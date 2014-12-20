import cgi

from diesel import first
from diesel.web import DieselFlask
from diesel.protocols.websockets import WebSocketDisconnect
from diesel.util.queue import Fanout

app = DieselFlask(__name__)

content = '''
<html>
<head>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js" type="text/javascript"></script>
<script>

var chatter = new WebSocket("ws://" + document.location.host + "/ws");

chatter.onopen = function (evt) {
}

chatter.onmessage = function (evt) {
    var res = JSON.parse(evt.data);
    var p = $('#the-chat');
    var add = $('<div class="chat-message"><span class="nick">&lt;' + res.nick +
    '&gt;</span> ' + res.message + '</div>');
    p.append(add);
    if (p.children().length > 15)
        p.children().first().remove();
}

function push () {
    chatter.send(JSON.stringify({
        message: $('#the-message').val(),
        nick: $('#the-nick').val()
    }));
    $('#the-message').val('');
    $('#the-message').focus();
}

$(function() {
    $('#the-button').click(push);
    $('#the-message').keyup(function (evt) { if (evt.keyCode == 13) push(); });
});

</script>

<style>

body {
    width: 800px;
    margin: 25px auto;
}

#the-chat {
    margin: 15px 8px;
}

.chat-message {
    margin: 4px 0;
}


.nick {
    font-weight: bold;
    color: #555;
}

</style>

</head>
<body>

<h2>Diesel WebSocket Chat</h2>

<div style="font-size: 13px; font-weight: bold; margin-bottom: 10px">
Nick: <input type="text" size="10" id="the-nick" />&nbsp;&nbsp;
Message: <input type="text" size="60" id="the-message" />&nbsp;&nbsp;
<input type="button" value="Send" id="the-button"/>
</div>

<div id="the-chat">
</div>

</body>
</html>
'''


f = Fanout()

@app.route("/")
def web_handler():
    return content

@app.route("/ws")
@app.websocket
def socket_handler(req, inq, outq):
    with f.sub() as group:
        while True:
            q, v = first(waits=[inq, group])
            if q == group:
                outq.put(dict(message=v['message'], nick=v['nick']))
            elif isinstance(v, WebSocketDisconnect):
                return
            elif v.get('nick', '').strip() and v.get('message', '').strip():
                f.pub({
                    'nick' : cgi.escape(v['nick'].strip()),
                    'message' : cgi.escape(v['message'].strip()),
                    })

app.run()
