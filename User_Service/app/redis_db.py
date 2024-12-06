from rediscluster import RedisCluster
import os
import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    
# Update the Redis connection settings for the cluster
redis_cluster_nodes = [
    {"host": "ud-redis-node-1", "port": 6379},
    {"host": "ud-redis-node-2", "port": 6379},
    {"host": "ud-redis-node-3", "port": 6379},
    {"host": "ud-redis-node-4", "port": 6379},
    {"host": "ud-redis-node-5", "port": 6379},
    {"host": "ud-redis-node-6", "port": 6379},
]

client = RedisCluster(startup_nodes=redis_cluster_nodes, decode_responses=True)

def save_user_session(user_id, user_data):
    user_data_json = json.dumps(user_data, ensure_ascii=False, cls=DateTimeEncoder)
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
            return "This user doesn't exist"
    except Exception as e:
        print(e)
        return None