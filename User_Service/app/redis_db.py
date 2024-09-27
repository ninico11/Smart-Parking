from dotenv import load_dotenv 
import os 
import json
import redis

from datetime import datetime

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to a string in ISO format
        return super().default(obj)
 
load_dotenv() 
client = redis.Redis(host=os.environ.get("", "localhost"), port=6379, db=0)
# client.flushdb
def save_user_session(user_id, user_data):
    user_data_json = json.dumps(user_data, ensure_ascii=False, cls=DateTimeEncoder)
    # Save the serialized JSON data to Redis
    client.hset(user_id, 'user_data', user_data_json)
    client.expire(user_id, 3600)
        
def delete_user_session(user_id):
    if client.hexists(user_id, 'user_data'):
        client.hdel(user_id, 'user_data')

def get_user_session(user_id):
    try:
        if client.hexists(user_id, 'user_data'):
            user_data_json = client.hget(user_id, 'user_data')
            user_data = json.loads(user_data_json)
            return user_data
        else:
            return "This user don't exit"

        
    except Exception as e:
        print(e)
        return None
    

