"""A WebSocket protocol implementation for diesel.

Implements much of RFC 6455 (http://tools.ietf.org/html/rfc6455) and enough
of hybi-00 to support Safari 5.0.1+.

Not implemented:
    * PING/PONG.
    * Extension support.

"""
from .http import HttpServer, Response
from diesel.util.queue import Queue
from diesel import fork, until, receive, first, ConnectionClosed, send
from simplejson import dumps, loads, JSONDecodeError
import hashlib
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
        """Creates a WebSocket server.

        The `web_handler` is used for non-WebSocket HTTP requests. It should
        be a callable that accepts a `Request` and returns a `Response`.

        The `web_socket_handler` will be called with three arguments: a
        `Request` instance, an input `Queue` and an output `Queue`. The input
        queue is where messages from the client will be received. Anything
        put in the output queue will be sent on to the client.

        All values passed to and from the queues MUST be dictionaries, or
        something that is JSON serializable. The one special case is the
        WebSocketDisconnect object that can arrive on the input queue if
        the client is closing the connection.

        """
        self.web_handler = web_handler
        self.web_socket_handler = web_socket_handler
        HttpServer.__init__(self, self.do_upgrade)

    def do_upgrade(self, req):
        """Handles the WebSocket handshake.

        Processes the `Request` instance `req` and returns a `Response`.

        Adds the WebSocket messaging protocol handler
        (`WebSocketServer.websocket_protocol`) to the `Response` object as
        `new_protocol`. That gets called by the underlying HttpServer when it
        sees a 101 Switching Protocols response.

        """
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

            protocol = req.headers.get('Sec-WebSocket-Protocol', None)
            key = req.headers.get('Sec-WebSocket-Key')
            accept = b64encode(hashlib.sha1(key + self.GUID).digest())
            headers = {
                'Upgrade' : 'websocket',
                'Connection' : 'Upgrade',
                'Sec-WebSocket-Accept' : accept,
                }
        elif 'Sec-WebSocket-Key1' in req.headers:
            protocol = req.headers.get('Sec-WebSocket-Protocol', None)
            key1 = req.headers.get('Sec-WebSocket-Key1')
            key2 = req.headers.get('Sec-WebSocket-Key2')
            headers = {
                'Upgrade': 'WebSocket',
                'Connection': 'Upgrade',
                'Sec-WebSocket-Origin': org,
                'Sec-WebSocket-Location': req.url.replace('http', 'ws', 1),
            }
            key3 = req.data
            assert len(key3) == 8, len(key3)
            num1 = int(''.join(c for c in key1 if c in '0123456789'))
            num2 = int(''.join(c for c in key2 if c in '0123456789'))
            assert num1 % key1.count(' ') == 0
            assert num2 % key2.count(' ') == 0
            final = pack('!II8s', num1 / key1.count(' '), num2 / key2.count(' '), key3)
            handshake_finish = hashlib.md5(final).digest()
        else:
            assert 0, "Unsupported WebSocket handshake."
        req.rfc_handshake = not bool(handshake_finish)

        if protocol:
            headers['Sec-WebSocket-Protocol'] = protocol

        resp = Response(
                response='' if not handshake_finish else handshake_finish,
                status=101,
                headers=headers,
                )
        resp.new_protocol = self.websocket_protocol

        return resp

    def websocket_protocol(self, req):
        """Runs the WebSocket protocol after the handshake is complete.

        Creates two `Queue` instances for incoming and outgoing messages and
        passes them to the `web_socket_handler` that was supplied to the
        `WebSocketServer` constructor.

        """
        inq = Queue()
        outq = Queue()

        def wrap(req, inq, outq):
            self.web_socket_handler(req, inq, outq)
            outq.put(WebSocketDisconnect())

        handler_loop = fork(wrap, req, inq, outq)

        if req.rfc_handshake:
            handle_frames = self.handle_rfc_6455_frames
        else:
            handle_frames = self.handle_non_rfc_frames

        try:
            handle_frames(inq, outq)
        except ConnectionClosed:
            if handler_loop.running:
                inq.put(WebSocketDisconnect())
            raise

    def handle_rfc_6455_frames(self, inq, outq):
        disconnecting = False
        while True:
            typ, val = first(receive=2, waits=[outq])
            if typ == 'receive':
                b1, b2 = unpack(">BB", val)

                opcode = b1 & 0x0f
                fin = (b1 & 0x80) >> 7
                has_mask = (b2 & 0x80) >> 7

                assert has_mask == 1, "Frames must be masked"

                if opcode == 8:
                    inq.put(WebSocketDisconnect())
                    if disconnecting:
                        break
                    disconnecting = True
                assert opcode in [1,8], "Currently only opcodes 1 & 8 are supported (opcode=%s)" % opcode
                length = b2 & 0x7f
                if length == 126:
                    length = unpack('>H', receive(2))[0]
                elif length == 127:
                    length = unpack('>L', receive(8))[0]

                mask = unpack('>BBBB', receive(4))
                if length:
                    payload = array('B', receive(length))
                    if disconnecting:
                        continue
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
                    if disconnecting:
                        break
                    disconnecting = True
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

    def handle_non_rfc_frames(self, inq, outq):
        while True:
            typ, val = first(receive=1, waits=[outq])
            if typ == 'receive':
                assert val == '\x00'
                val = until('\xff')[:-1]
                if val == '':
                    inq.put(WebSocketDisconnect())
                    break
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
