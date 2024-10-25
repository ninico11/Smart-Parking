import requests
from dotenv import load_dotenv
import os

port = os.environ.get("GATEWAY_PORT", "5000")


def reserve_parking_lot(user_id, parking_lot_id, start_time, end_time):
    url = f"http://localhost:{port}/parking/api/parking/reservation"
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
