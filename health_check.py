from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'status': 'ok', 'service': 'chat-server'}
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    port = 8080
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Health check server on port {port}")
    server.serve_forever()
