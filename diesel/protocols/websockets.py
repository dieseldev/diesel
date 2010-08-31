from .http import HttpServer, HttpHeaders
from diesel.util.queue import Queue
from diesel import fork, until, receive, first, ConnectionClosed, send
from simplejson import dumps, loads
import cgi

class WebSocketDisconnect(object): pass
class WebSocketData(dict): pass

class WebSocketServer(HttpServer):
    '''Very simple Web Socket server.
    '''
    def __init__(self, web_handler, web_socket_handler, ws_location):
        self.web_handler = web_handler
        self.web_socket_handler = web_socket_handler
        self.ws_location = ws_location
        HttpServer.__init__(self, self.do_upgrade)

    def do_upgrade(self, req):
        if req.headers.get_one('Upgrade') != 'WebSocket':
            return self.web_handler(req)

        # do upgrade response
        org = req.headers.get_one('Origin')

        send(
'''HTTP/1.1 101 Web Socket Protocol Handshake\r
Upgrade: WebSocket\r
Connection: Upgrade\r
WebSocket-Origin: %s\r
WebSocket-Location: %s\r
WebSocket-Protocol: diesel-generic\r
\r
''' % (org, self.ws_location))
        
        inq = Queue()
        outq = Queue()

        def wrap(inq, outq):
            self.web_socket_handler(inq, outq)
            outq.put(WebSocketDisconnect())

        fork(wrap, inq, outq)
                                    
        while True:
            try:
                typ, val = first(receive=1, waits=[outq.wait_id])
                if typ == 'receive':
                    assert val == '\x00'
                    val = until('\xff')[:-1]
                    if val == '':
                        inq.put(WebSocketDisconnect())
                    else:
                        data = dict((k, v[0]) if len(v) == 1 else (k, v) for k, v in cgi.parse_qs(val).iteritems())
                        inq.put(WebSocketData(data))
                else:
                    try:
                        v = outq.get(waiting=False)
                    except QueueEmpty:
                        pass
                    else:
                        if type(v) is WebSocketDisconnect:
                            send('\x00\xff')
                            break
                        else:
                            data = dumps(dict(v))
                            send('\x00%s\xff' % data)

            except ConnectionClosed:
                inq.put(WebSocketDisconnect())
                raise ConnectionClosed("remote disconnected")
