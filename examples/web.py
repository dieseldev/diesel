from diesel.web import DieselFlask, request

app = DieselFlask(__name__)

@app.route("/")
def hello():
    name = request.args.get('name', 'world')
    return "hello, %s!" % name

@app.route("/err")
def err():
    a = b
    return "never happens.."

if __name__ == '__main__':
    import diesel
    def t():
        while True:
            diesel.sleep(1)
            print("also looping..")
    app.diesel_app.add_loop(diesel.Loop(t))
    app.run(debug=True)
