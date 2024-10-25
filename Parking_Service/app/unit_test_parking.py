import pytest
from flask import Flask
from .parking_apis import parking_blueprint  # Import your blueprint
import mongomock
from datetime import datetime

# Initialize the Flask app for testing
@pytest.fixture
def client():
    app = Flask(__name__)
    
    # Use a mock MongoDB client with mongomock
    mock_client = mongomock.MongoClient()
    db = mock_client['parking_db']

    # Inject mock collections into the blueprint
    parking_blueprint.parking_collection = db['parking_lots']
    parking_blueprint.reservations_collection = db['reservations']

    # Register the blueprint
    app.register_blueprint(parking_blueprint)

    # Yield the Flask test client for requests
    with app.test_client() as client:
        yield client

# Test service status endpoint
def test_parking_service_status(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.get_json()['status'] == "Parking Lots Management Service is running"

# Test adding parking lots
def test_add_parking_lots(client):
    response = client.post('/api/parking/lots/add', json={
        'location': 'Downtown',
        'nr_of_lots': 2
    })
    assert response.status_code == 201
    assert "new parking lots added in Downtown" in response.get_json()['message']

# Test retrieving all parking lots
def test_get_parking_lots(client):
    # Add mock data first
    client.post('/api/parking/lots/add', json={
        'location': 'Downtown',
        'nr_of_lots': 1
    })

    response = client.get('/api/parking/lots')
    assert response.status_code == 200

# Test getting a specific parking lot
def test_get_parking_lot(client):
    # Add mock data and retrieve it
    add_response = client.post('/api/parking/lots/add', json={
        'location': 'Uptown',
        'nr_of_lots': 1
    })
    response = client.get('/api/parking/lots')
    lots = response.get_json()  # List of parking lots
    
    # Search for the lot with the given name
    for lot in lots:
        if lot['name'] == 'Uptown Lot 1':
            lot_id = lot['id']

    response = client.get(f'/api/parking/lots/{lot_id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == 'Uptown Lot 1'

# Test making a reservation
def test_make_reservation(client):
    lot_id = client.get('/api/parking/lots').get_json()[0]['id']
    print(f"Lot ID: {lot_id}")  # Debugging
    payload = {
        'parking_lot_id': str(lot_id),  # Ensure it's in string format
        'user_id': 1,
        'start_time': '2024-10-20 10:00:00',
        'end_time': '2024-10-20 12:00:00'
    }
    response = client.post('/api/parking/reservation', json = payload)
    print(payload)

    assert response.status_code == 201


# Test canceling a reservation
def test_cancel_reservation(client):
    # Add parking lot and reservation
    client.post('/api/parking/lots/add', json={
        'location': 'Downtown',
        'nr_of_lots': 1
    })
    lot_id = client.get('/api/parking/lots').get_json()[0]['id']
    reservation_response = client.post('/api/parking/reservation', json={
        'parking_lot_id': lot_id,
        'user_id': 'user_123',
        'start_time': '2024-10-20 10:00:00',
        'end_time': '2024-10-20 12:00:00'
    })

    reservation_id = client.get('/api/parking/reservations').get_json()[0]['reservation_id']
    cancel_response = client.post('/api/parking/reservations/cancel', json={
        'reservation_id': reservation_id
    })
    assert cancel_response.status_code == 200
    assert cancel_response.get_json()['message'] == "Reservation canceled successfully"

# Test updating parking lot status
def test_update_parking_lot_status(client):
    # Add mock data
    client.post('/api/parking/lots/add', json={
        'location': 'Midtown',
        'nr_of_lots': 1
    })
    lot_id = client.get('/api/parking/lots').get_json()[0]['id']

    response = client.post('/api/parking/lots/update', json={
        'parking_lot_id': lot_id,
        'status': 'occupied'
    })
    assert response.status_code == 200
    assert response.get_json()['message'] == "Parking lot status updated successfully"
