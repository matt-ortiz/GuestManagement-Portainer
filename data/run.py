import os
from gevent.pywsgi import WSGIServer
from app import create_app

app = create_app()

def find_free_port(start_port=5000, max_attempts=100):
    """Try to find a free port starting from start_port"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', port))
            s.close()
            return port
        except OSError:
            continue
    raise OSError(f"Could not find a free port after {max_attempts} attempts")

if __name__ == '__main__':
    # Only use this for development
    app.run(host='0.0.0.0', port=8000)