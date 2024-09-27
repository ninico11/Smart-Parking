from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8000')
    app.run(port=server_port, host='0.0.0.0', debug=True)