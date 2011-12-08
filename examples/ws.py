from diesel.protocols.http import http_response, HttpHeaders
from diesel.protocols.websockets import WebSocketServer, WebSocketData as WSD
from diesel import Service, Application, sleep
from diesel.util.queue import QueueTimeout

LOCATION = "ws://localhost:8091/"

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

def web_handler(req):
    heads = HttpHeaders()
    heads.add('Content-Length', len(content))
    heads.add('Content-Type', 'text/html')

    return http_response(req, 200, heads, content)

import time

def socket_handler(req, inq, outq):
    message = "hello, there!"
    while True:
        try:
            v = inq.get(timeout=0.5)
        except QueueTimeout:
            pass
        else:
            message = v['message']

        outq.put(WSD(message=message, time=time.time()))

a = Application()
a.add_service(Service(WebSocketServer(web_handler, socket_handler, LOCATION), 8091))
a.run()