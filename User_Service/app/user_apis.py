from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db
from .models import User, Notification, Reservation
from app.parking_request import reserve_parking_lot
from app.redis_db import get_user_session, save_user_session

user_blueprint = Blueprint('user_apis', __name__)

@user_blueprint.route('/api/users/status', methods=['GET'])
def user_service_status():
    try:
        # If needed, you can add more checks here, such as database connection status
        return jsonify({"status": "User Management Service is running"}), 200
    except Exception as e:
        return jsonify({"status": "User Management Service is down", "error": str(e)}), 500

@user_blueprint.route('/api/users', methods=['GET'])
def get_users():
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
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User with this email already exists"}), 400
    
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, full_name=full_name)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully"}), 201

# Signin route
@user_blueprint.route('/api/users/auth/signin', methods=['POST'])
def signin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user.id)
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
    return jsonify({"access_token": access_token}), 200

# Signout route (invalidating the token can be managed using JWT blacklisting or other logic)
@user_blueprint.route('/api/users/auth/signout', methods=['POST'])
@jwt_required()
def signout():
    # Implement token revocation logic here if needed
    return jsonify({"message": "User signed out successfully"}), 200

# Fetch user profile
@user_blueprint.route('/api/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = get_user_session(user_id)
    
    return jsonify({
        "email": user['email'],
        "full_name": user['full_name'],
        "phone_number": user['phone_number'],
        "address": user['address'],
        "profile_pic_url": user['profile_pic_url'],
        "created_at": user['created_at'],
        "updated_at": user['updated_at']
    }), 200

# Update user profile
@user_blueprint.route('/api/users/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    
    user.full_name = data.get('full_name', user.full_name)
    user.phone_number = data.get('phone_number', user.phone_number)
    user.address = data.get('address', user.address)
    user.preferences = data.get('preferences', user.preferences)
    
    db.session.commit()
    
    return jsonify({"message": "Profile updated successfully"}), 200

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
        return jsonify({"error": "Missing required fields"}), 400

    # Call the Parking Service to make the reservation
    try:
        reservation_response = reserve_parking_lot(user_id, parking_lot_id, start_time, end_time)
    except Exception as e:
        return jsonify({"error": "Error communicating with parking service"}), 500

    if 'error' in reservation_response:
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
