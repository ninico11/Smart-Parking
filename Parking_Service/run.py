from app import create_app
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

app = create_app()

if __name__ == '__main__':
    server_port = os.environ.get('PARKING_SERVICE_PORT', '8001')
    app.run(port=server_port, host='0.0.0.0', debug=True)