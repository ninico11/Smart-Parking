import requests

def reserve_parking_lot(user_id, parking_lot_id, start_time, end_time):
    url = "http://localhost:8000/api/parking/reservation"
    data = {
        "user_id": user_id,
        "parking_lot_id": parking_lot_id,
        "start_time": start_time,
        "end_time": end_time
    }
    print(data)
    response = requests.post(url, json=data)
    print(response)
    return response.json()
