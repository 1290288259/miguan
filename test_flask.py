from flask import Flask, Response
app = Flask(__name__)
@app.after_request
def add_server(response):
    response.headers['Server'] = 'App-webs/'
    return response
@app.route('/')
def home(): return 'ok'
if __name__ == '__main__':
    import threading
    threading.Thread(target=app.run, kwargs={'port': 5555}, daemon=True).start()
    import time, requests
    time.sleep(1)
    print(requests.get('http://127.0.0.1:5555').headers)
