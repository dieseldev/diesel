from .http import HttpServer, Response
from diesel.util.queue import Queue
from diesel import fork, until, receive, first, ConnectionClosed, send
from simplejson import dumps, loads, JSONDecodeError
import cgi, hashlib
from struct import pack, unpack
from base64 import b64encode
from array import array

class WebSocketDisconnect(object): pass
class WebSocketData(dict): pass

class WebSocketServer(HttpServer):
    '''Very simple Web Socket server.
    '''

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, web_handler, web_socket_handler):
        self.web_handler = web_handler
        self.web_socket_handler = web_socket_handler
        HttpServer.__init__(self, self.do_upgrade)

    def do_upgrade(self, req):
        if req.headers.get('Upgrade', '').lower() != 'websocket':
            return self.web_handler(req)

        headers = {}

        # do upgrade response
        org = req.headers.get('Origin')
        handshake_finish = None
        if 'Sec-WebSocket-Key' in req.headers:
            assert req.headers.get('Sec-WebSocket-Version') in ['8', '13'], \
                   "We currently only support Websockets version 8 and 13 (ver=%s)" % \
                   req.headers.get('Sec-WebSocket-Version')

            protocol = (req.headers.get('Sec-WebSocket-Protocol')
                        if 'Sec-WebSocket-Protocol' in req.headers else None)
            key = req.headers.get('Sec-WebSocket-Key')
            accept = b64encode(hashlib.sha1(key + self.GUID).digest())
            headers = {
                'Upgrade' : 'websocket',
                'Connection' : 'Upgrade',
                'Sec-WebSocket-Accept' : accept,
                }
            if protocol:
                headers["Sec-WebSocket-Protocol"] = protocol
        else:
            assert 0, "Only RFC 6455 WebSockets are supported"

        resp = Response(
                response='',
                status=101,
                headers=headers
                )

        self.send_response(resp)

        if handshake_finish:
            send(handshake_finish)

        inq = Queue()
        outq = Queue()

        def wrap(req, inq, outq):
            self.web_socket_handler(req, inq, outq)
            outq.put(WebSocketDisconnect())

        fork(wrap, req._get_current_object(), inq, outq)

        while True:
            try:
                typ, val = first(receive=2, waits=[outq])
                if typ == 'receive':
                    b1, b2 = unpack(">BB", val)

                    opcode = b1 & 0x0f
                    fin = (b1 & 0x80) >> 7
                    has_mask = (b2 & 0x80) >> 7

                    assert has_mask == 1, "Frames must be masked"

                    if opcode == 8:
                        inq.put(WebSocketDisconnect())
                    else:
                        assert opcode == 1, "Currently only opcode 1 is supported (opcode=%s)" % opcode
                        length = b2 & 0x7f
                        if length == 126:
                            length = unpack('>H', receive(2))[0]
                        elif length == 127:
                            length = unpack('>L', receive(8))[0]

                        mask = unpack('>BBBB', receive(4))
                        payload = array('B', receive(length))
                        for i in xrange(len(payload)):
                            payload[i] ^= mask[i % 4]

                        try:
                            data = loads(payload.tostring())
                            inq.put(data)
                        except JSONDecodeError:
                            pass
                elif typ == outq:
                    if type(val) is WebSocketDisconnect:
                        b1 = 0x80 | (8 & 0x0f) # FIN + opcode
                        send(pack('>BB', b1, 0))
                        break
                    else:
                        payload = dumps(val)

                        b1 = 0x80 | (1 & 0x0f) # FIN + opcode

                        payload_len = len(payload)
                        if payload_len <= 125:
                            header = pack('>BB', b1, payload_len)
                        elif payload_len > 125 and payload_len < 65536:
                            header = pack('>BBH', b1, 126, payload_len)
                        elif payload_len >= 65536:
                            header = pack('>BBQ', b1, 127, payload_len)

                    send(header + payload)

            except ConnectionClosed:
                inq.put(WebSocketDisconnect())
                raise ConnectionClosed("remote disconnected")
