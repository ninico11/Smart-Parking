from app import create_app, socketio
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Get the server port from environment variables, default to 8080
    server_port = os.environ.get('USER_SERVICE_PORT', '8080')

    # Run the app with SocketIO integration (disable reloader in debug mode)
    socketio.run(app, host='0.0.0.0', port=int(server_port), debug=True, use_reloader=False)
