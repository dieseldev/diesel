from .http import HttpServer, HttpHeaders
from diesel.util.queue import Queue
from diesel import fork, until, receive, first, ConnectionClosed, send
from simplejson import dumps, loads, JSONDecodeError
import cgi, hashlib
from struct import pack, unpack
from base64 import b64encode
from array import array

class WebSocketDisconnect(object): pass
class WebSocketData(dict): pass

server_handshake_hybi = \
'''HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: %s\r'''

class WebSocketServer(HttpServer):
    '''Very simple Web Socket server.
    '''

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, web_handler, web_socket_handler, ws_location):
        self.web_handler = web_handler
        self.web_socket_handler = web_socket_handler
        self.ws_location = ws_location
        HttpServer.__init__(self, self.do_upgrade)

    def do_upgrade(self, req):
        if req.headers.get_one('Upgrade') != 'websocket' and req.headers.get_one('Upgrade') != 'WebSocket':
            return self.web_handler(req)

        hybi = False

        # do upgrade response
        org = req.headers.get_one('Origin')
        if 'Sec-WebSocket-Key' in req.headers:
            assert req.headers.get_one('Sec-WebSocket-Version') in ['8', '13'], \
                   "We currently only support Websockets version 8 and 13 (ver=%s)" % \
                   req.headers.get_one('Sec-WebSocket-Version')

            protocol = (req.headers.get_one('Sec-WebSocket-Protocol')
                        if 'Sec-WebSocket-Protocol' in req.headers else None)
            key = req.headers.get_one('Sec-WebSocket-Key')
            accept = b64encode(hashlib.sha1(key + self.GUID).digest())
            send(server_handshake_hybi % accept)
            if protocol:
                send("Sec-WebSocket-Protocol: %s\r" % protocol)
            send("\r\n\r\n")
            hybi = True

        elif 'Sec-WebSocket-Key1' in req.headers:
            protocol = (req.headers.get_one('Sec-WebSocket-Protocol')
                        if 'Sec-WebSocket-Protocol' in req.headers else None)
            key1 = req.headers.get_one('Sec-WebSocket-Key1')
            key2 = req.headers.get_one('Sec-WebSocket-Key2')
            key3 = receive(8)
            num1 = int(''.join(c for c in key1 if c in '0123456789'))
            num2 = int(''.join(c for c in key2 if c in '0123456789'))
            assert num1 % key1.count(' ') == 0
            assert num2 % key2.count(' ') == 0
            final = pack('!II8s', num1 / key1.count(' '), num2 / key2.count(' '), key3)
            secure_response = hashlib.md5(final).digest()
            send(
'''HTTP/1.1 101 Web Socket Protocol Handshake\r
Upgrade: WebSocket\r
Connection: Upgrade\r
Sec-WebSocket-Origin: %s\r
Sec-WebSocket-Location: %s\r
'''% (org, self.ws_location))
            if protocol:
                send("Sec-WebSocket-Protocol: %s\r\n" % (protocol,))
            send("\r\n")
            send(secure_response)

        else:
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

        def wrap(req, inq, outq):
            self.web_socket_handler(req, inq, outq)
            outq.put(WebSocketDisconnect())

        fork(wrap, req, inq, outq)

        while True:
            try:
                if hybi:
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
                else:
                    typ, val = first(receive=1, waits=[outq])
                    if typ == 'receive':
                        assert val == '\x00'
                        val = until('\xff')[:-1]
                        if val == '':
                            inq.put(WebSocketDisconnect())
                        else:
                            try:
                                data = loads(val)
                                inq.put(data)
                            except JSONDecodeError:
                                pass
                    elif typ == outq:
                        if type(val) is WebSocketDisconnect:
                            send('\x00\xff')
                            break
                        else:
                            data = dumps(dict(val))
                            send('\x00%s\xff' % data)


            except ConnectionClosed:
                inq.put(WebSocketDisconnect())
                raise ConnectionClosed("remote disconnected")
