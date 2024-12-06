from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db, socketio
from .models import User, Notification, Reservation
from app.parking_request import reserve_parking_lot
from app.redis_db import get_user_session, save_user_session
from flask_socketio import emit, join_room, leave_room

from prometheus_flask_exporter import Counter

import logging

logging.basicConfig(level=logging.INFO)

user_blueprint = Blueprint('user_apis', __name__)

request_counter = Counter(
    'app_requests_total', 'Total number of requests', ['method', 'endpoint']
)

@user_blueprint.route('/api/status', methods=['GET'])
def user_service_status():
    request_counter.labels(method='GET', endpoint='/status').inc()
    try:
        # If needed, you can add more checks here, such as database connection status
        logging.info("Status controlled.")
        return jsonify({"status": "User Management Service is running"}), 200
    except Exception as e:
        logging.error("Status error.")
        return jsonify({"status": "User Management Service is down", "error": str(e)}), 500

@user_blueprint.route('/api/users', methods=['GET'])
def get_users():
    request_counter.labels(method='GET', endpoint='/api/users').inc()
    logging.info("Fetching all users.")
    users = User.query.all()
    
    return jsonify([{
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "address": user.address,
        "profile_pic_url": user.profile_pic_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    } for user in users]), 200

# Signup route
@user_blueprint.route('/api/users/auth/signup', methods=['POST'])
def signup():
    request_counter.labels(method='POST', endpoint='/api/users/auth/signup').inc()
    data = request.get_json()

    # Avoid logging sensitive data like passwords
    logging.debug(f"Signup Request Data (excluding password): { {k: v for k, v in data.items() if k != 'password'} }")
    
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    address = data.get('address')
    
    if User.query.filter_by(email=email).first():
        logging.warning(f"Attempted signup with existing email: {email}")
        return jsonify({"error": "User with this email already exists"}), 400
    
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, full_name=full_name, address=address)
    
    db.session.add(new_user)
    db.session.commit()
    logging.info(f"User created successfully with email: {email}")
    
    return jsonify({"message": "User created successfully"}), 201

# Signin route
@user_blueprint.route('/api/users/auth/signin', methods=['POST'])
def signin():
    request_counter.labels(method='POST', endpoint='/api/users/auth/signin').inc()
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        logging.warning(f"Failed login attempt for email: {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.address:
        logging.warning(f"User {email} attempted login without address")
        return jsonify({"error": "Please add your address to receive notifications"}), 403

    # Generate access token
    access_token = create_access_token(identity=user.id)
    logging.info(f"User {email} signed in successfully.")

    # Save user session
    user_data = {
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "address": user.address,
        "profile_pic_url": user.profile_pic_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    save_user_session(user.id, user_data)

    # Automatically join WebSocket room for the user's address
    socketio.emit('join_region', {'region': user.address}, room=user.id)

    return jsonify({"access_token": access_token}), 200

# Signout route (invalidating the token can be managed using JWT blacklisting or other logic)
@user_blueprint.route('/api/users/auth/signout', methods=['POST'])
@jwt_required()
def signout():
    request_counter.labels(method='POST', endpoint='/api/users/auth/signout').inc()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    logging.info(f"User {user.email} signed out.")
    
    return jsonify({"message": "User signed out successfully"}), 200


# Fetch user profile
@user_blueprint.route('/api/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    # request_counter.labels(method='GET', endpoint='/api/users/profile').inc()
    try:   
        logging.info(f"Start profile")
        user_id = get_jwt_identity()
        logging.info(f"User ID: {user_id}")
        user = get_user_session(user_id)
        logging.info(f"Fetching profile for user ID: {user_id}")
        
        return jsonify({
            "email": user['email'],
            "full_name": user['full_name'],
            "phone_number": user['phone_number'],
            "address": user['address'],
            "profile_pic_url": user['profile_pic_url'],
            "created_at": user['created_at'],
            "updated_at": user['updated_at']
        }), 200
    except Exception as e:
        logging.error("Profile error.")
        logging.error(f"Error: {e}")
        return jsonify({"status": "User Management Service is down", "error": str(e)}), 500
    
# Update user profile
@user_blueprint.route('/api/users/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    request_counter.labels(method='PUT', endpoint='/api/users/profile/update').inc()
    user_id = get_jwt_identity()
    data = request.get_json()
    try:
        update_data = data["update_data"]
        user = User.query.get_or_404(user_id)
        user.full_name = update_data.get('full_name', user.full_name)
        user.phone_number = update_data.get('phone_number', user.phone_number)
        user.profile_pic_url = update_data.get('profile_pic_url', user.profile_pic_url)
        user.address = update_data.get('address', user.address)
        db.session.commit()
        logging.info(f"User profile updated for ID: {user_id}")
        user_data = {
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "address": user.address,
            "profile_pic_url": user.profile_pic_url,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        save_user_session(user.id, user_data)

        logging.info(f"Profile update completed successfully for user ID: {user_id}")
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        logging.error(f"Profile update failed for user ID: {user_id}, Error: {str(e)}")
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500

# Fetch user notifications
@user_blueprint.route('/api/users/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id).all()
    
    return jsonify([
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at
        } for n in notifications
    ]), 200

# Mark notifications as read
@user_blueprint.route('/api/users/notifications/mark-as-read', methods=['POST'])
@jwt_required()
def mark_notifications_as_read():
    user_id = get_jwt_identity()
    data = request.get_json()
    notification_ids = data.get('notification_ids', [])
    
    Notification.query.filter(Notification.user_id == user_id, Notification.id.in_(notification_ids)).update(
        {'is_read': True}, synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({"message": "Notifications marked as read"}), 200

# WebSocket notifications - This would be handled separately in the websocket logic file

# Reserve parking lot for the user
@user_blueprint.route('/api/users/reserve', methods=['POST'])
@jwt_required()
def user_reserve_parking():
    user_id = get_jwt_identity()
    data = request.get_json()
    parking_lot_id = data.get('parking_lot_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not parking_lot_id or not start_time or not end_time:
        logging.warning(f"User ID {user_id} provided incomplete reservation data.")
        return jsonify({"error": "Missing required fields"}), 400

    try:
        reservation_response = reserve_parking_lot(user_id, parking_lot_id, start_time, end_time)
    except Exception as e:
        logging.error(f"Error communicating with parking service: {str(e)}")
        return jsonify({"error": "Error communicating with parking service"}), 500

    if 'error' in reservation_response:
        logging.error(f"Reservation error for user ID {user_id}: {reservation_response['error']}")
        return jsonify({"error": reservation_response['error']}), 400

    # Store the reservation in the User Management Service's database
    new_reservation = Reservation(
        user_id=user_id,
        parking_lot_id=parking_lot_id,
        start_time=start_time,
        end_time=end_time,
        status='reserved'
    )

    db.session.add(new_reservation)
    db.session.commit()
    logging.info(f"Reservation successful for user ID {user_id} in parking lot {parking_lot_id}")

    return jsonify({
        "message": "Reservation successful",
        "reservation": reservation_response
    }), 201


# Fetch user reservations
@user_blueprint.route('/api/users/reservations', methods=['GET'])
@jwt_required()
def get_reservations():
    user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(user_id=user_id).all()
    
    return jsonify([
        {
            "id": r.id,
            "parking_lot_id": r.parking_lot_id,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "status": r.status
        } for r in reservations
    ]), 200
    
@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection."""
    emit('connected', {'message': 'WebSocket connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logging.info('Client disconnected')

@socketio.on('join_region')
def join_region(data):
    """Join a specific region room."""
    region = data.get('region')
    if region:
        join_room(region)
        emit('joined_region', {'message': f'Joined region {region}'}, room=region)

@socketio.on('leave_region')
def leave_region(data):
    """Leave a specific region room."""
    region = data.get('region')
    if region:
        leave_room(region)
        emit('left_region', {'message': f'Left region {region}'}, room=region)

@user_blueprint.route('/api/users/notification/<region>', methods=['POST'])
def send_notification(region):
    """Send notification to users in the specified region."""
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Broadcast the message to the WebSocket room for the region
    socketio.emit('notification', {'message': message}, room=region)

    return jsonify({'message': 'Notification sent successfully'}), 200
