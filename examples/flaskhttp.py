from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, world!"

if __name__ == '__main__':
    from diesel.protocols.wsgi import WSGIApplication
    WSGIApplication(app, port=7080).run()
