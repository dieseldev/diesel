import time

from diesel import Service, Application, sleep
from diesel.web import DieselFlask
from diesel.util.queue import QueueTimeout

app = DieselFlask(__name__)

LOCATION = "ws://172.16.26.128:8080/ws"

content = '''
<html>
<head>
<script>

var chatter = new WebSocket("%s");

chatter.onopen = function (evt) {
}

chatter.onmessage = function (evt) {
    var p = document.getElementById("the-p");
    p.innerHTML = evt.data;
}

function push () {
    var i = document.getElementById("the-i");
    chatter.send(JSON.stringify({
        message: i.value
    }));
}

</script>

</head>
<body>

<h1>Hello dude!</h1>

<p id="the-p">
</p>

<input type="text" size="40" id="the-i" /> <input type="button" value="Update Message" onclick="push(); return false" />

</body>
</html>
''' % LOCATION

@app.route("/")
def web_handler():
    return content

@app.route("/ws")
@app.websocket
def socket_handler(req, inq, outq):
    message = "hello, there!"
    while True:
        try:
            v = inq.get(timeout=0.5)
        except QueueTimeout:
            pass
        else:
            message = v['message']

        outq.put(dict(message=message, time=time.time()))

app.run()
