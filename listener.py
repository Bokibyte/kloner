from http.server import HTTPServer, BaseHTTPRequestHandler

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        print("\n[+] RECEIVED POST DATA:")
        print(post_data.decode('utf-8', errors='ignore'))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received successfully!")

    def do_GET(self):
        print(f"\n[+] RECEIVED GET REQUEST for: {self.path}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"GET request received!")

if __name__ == '__main__':
    server_address = ('', 8080) # Listens on port 8080 across all interfaces
    httpd = HTTPServer(server_address, RequestHandler)
    print("[*] Local receiver running on port 8080...")
    httpd.serve_forever()