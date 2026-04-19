from flask import Flask
import werkzeug.serving
werkzeug.serving.WSGIRequestHandler.version_string = lambda self: 'App-webs/'
app = Flask(__name__)
@app.route('/')
def home(): return 'ok'
if __name__ == '__main__':
    import threading
    threading.Thread(target=app.run, kwargs={'port': 5555}, daemon=True).start()
    import time, requests
    time.sleep(1)
    print(requests.get('http://127.0.0.1:5555').headers)
