from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import os

# MongoDB setup (you need to configure this with your actual MongoDB connection string)
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
client = MongoClient(mongo_uri)
db = client['parking_db']
parking_collection = db['parking_lots']
reservations_collection = db['reservations']

parking_blueprint = Blueprint('parking_apis', __name__)

@parking_blueprint.route('/status', methods=['GET'])
def parking_service_status():
    try:
        # Optionally check MongoDB connection here to ensure the service is operational
        db_stats = parking_collection.database.command("ping")
        return jsonify({
            "status": "Parking Lots Management Service is running",
            "database": "MongoDB connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "Parking Lots Management Service is down",
            "error": str(e)
        }), 500

# Retrieve the list of available parking lots with their status
@parking_blueprint.route('/api/parking/lots', methods=['GET'])
def get_parking_lots():
    parking_lots = list(parking_collection.find({}, {'_id': 1, 'name': 1, 'status': 1, 'location': 1}))
    return jsonify([{
        'id': str(parking_lot['_id']),
        'name': parking_lot['name'],
        'status': parking_lot['status'],
        'location': parking_lot['location']
    } for parking_lot in parking_lots]), 200

# Retrieve detailed information about a specific parking lot
@parking_blueprint.route('/api/parking/lots/<lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    parking_lot = parking_collection.find_one({'_id': ObjectId(lot_id)})
    if not parking_lot:
        return jsonify({"error": "Parking lot not found"}), 404
    
    return jsonify({
        'id': str(parking_lot['_id']),
        'name': parking_lot['name'],
        'status': parking_lot['status'],
        'location': parking_lot['location'],
    }), 200

# Add new parking lots based on location and number of lots
@parking_blueprint.route('/api/parking/lots/add', methods=['POST'])
def add_parking_lots():
    data = request.get_json()
    location = data.get('location')
    nr_of_lots = data.get('nr_of_lots')

    if not location or not isinstance(nr_of_lots, int) or nr_of_lots <= 0:
        return jsonify({"error": "Invalid data"}), 400

    # Add the specified number of parking lots at the given location
    parking_lots = []
    for i in range(nr_of_lots):
        parking_lot = {
            'name': f"{location} Lot {i + 1}",
            'location': location,
            'status': 'available',
            'created_at': datetime.datetime.utcnow()
        }
        parking_lots.append(parking_lot)

    # Insert the new parking lots into the database
    parking_collection.insert_many(parking_lots)

    return jsonify({"message": f"{nr_of_lots} new parking lots added in {location}"}), 201

# Make a parking reservation
@parking_blueprint.route('/api/parking/reservation', methods=['POST'])
def make_reservation():
    data = request.get_json()
    print('here')
    print(data)
    parking_lot_id = data.get('parking_lot_id')
    user_id = data.get('user_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    # Convert time strings to datetime objects
    try:
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    parking_lot = parking_collection.find_one({'_id': ObjectId(parking_lot_id)})
    if not parking_lot:
        return jsonify({"error": "Parking lot not found"}), 404

    # Check if the parking lot is available
    if parking_lot['status'] != 'available':
        return jsonify({"error": "Parking lot is not available"}), 201

    # Create the reservation
    reservation = {
        'user_id': user_id,
        'parking_lot_id': ObjectId(parking_lot_id),
        'start_time': start_time,
        'end_time': end_time,
        'status': 'reserved',
        'created_at': datetime.datetime.utcnow()
    }

    reservations_collection.insert_one(reservation)

    # Update parking lot status to reserved
    parking_collection.update_one({'_id': ObjectId(parking_lot_id)}, {'$set': {'status': 'reserved'}})

    return jsonify({"message": "Reservation made successfully"}), 201

# Cancel a parking reservation
@parking_blueprint.route('/api/parking/reservations/cancel', methods=['POST'])
def cancel_reservation():
    data = request.get_json()
    reservation_id = data.get('reservation_id')

    reservation = reservations_collection.find_one({'_id': ObjectId(reservation_id)})
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404

    # Update the reservation status
    reservations_collection.update_one({'_id': ObjectId(reservation_id)}, {'$set': {'status': 'canceled'}})

    # Update parking lot status to available
    parking_collection.update_one({'_id': ObjectId(reservation['parking_lot_id'])}, {'$set': {'status': 'available'}})

    return jsonify({"message": "Reservation canceled successfully"}), 200

# Update parking lot status based on sensor data or manual entry
@parking_blueprint.route('/api/parking/lots/update', methods=['POST'])
def update_parking_lot():
    data = request.get_json()
    parking_lot_id = data.get('parking_lot_id')
    status = data.get('status')

    if status not in ['available', 'reserved', 'occupied']:
        return jsonify({"error": "Invalid status"}), 400

    parking_lot = parking_collection.find_one({'_id': ObjectId(parking_lot_id)})
    if not parking_lot:
        return jsonify({"error": "Parking lot not found"}), 404

    parking_collection.update_one({'_id': ObjectId(parking_lot_id)}, {'$set': {'status': status}})

    return jsonify({"message": "Parking lot status updated successfully"}), 200

@parking_blueprint.route('/api/parking/reservations', methods=['GET'])
def get_reservations():
    user_id = request.args.get('user_id')
    parking_lot_id = request.args.get('parking_lot_id')
    
    query = {}
    if user_id:
        query['user_id'] = user_id
    if parking_lot_id:
        query['parking_lot_id'] = ObjectId(parking_lot_id)
    
    reservations = list(reservations_collection.find(query))
    
    if not reservations:
        return jsonify({"error": "No reservations found"}), 404
    
    return jsonify([{
        'reservation_id': str(reservation['_id']),
        'user_id': reservation['user_id'],
        'parking_lot_id': str(reservation['parking_lot_id']),
        'start_time': reservation['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': reservation['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
        'status': reservation['status'],
        'created_at': reservation['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    } for reservation in reservations]), 200
