from http.server import BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    server_version = 'Elasticsearch/7.10.2'
    sys_version = ''
print(Handler(None, None, None).version_string())
