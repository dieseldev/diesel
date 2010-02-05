try:
    import ssl
except ImportError:
    ssl = None

class SecureWrapper(object):
    def __init__(self):
        assert ssl is not None, "SSL module not available"

    def wrap(self, sock):
        raise NotImplementedError
        yield 0

class TLSv1ServiceWrapper(SecureWrapper):
    def __init__(self, key_file, cert_file):
        SecureWrapper.__init__(self)
        self.key_file = key_file
        self.cert_file = cert_file

    def wrap(self, sock):
        return ssl.wrap_socket(sock, server_side=True,
        certfile=self.cert_file, keyfile=self.key_file,
        ssl_version = ssl.PROTOCOL_TLSv1,
        do_handshake_on_connect=False)

class TLSv1ClientWrapper(SecureWrapper):
    def __init__(self):
        SecureWrapper.__init__(self)

    def wrap(self, sock):
        return ssl.wrap_socket(sock, ssl_version = ssl.PROTOCOL_TLSv1,
        do_handshake_on_connect=False)

def ssl_async_handshake(sock, hub, next):
    def shake():
        try:
            sock.do_handshake()
        except ssl.SSLError, err:
            if err.args[0] == ssl.SSL_ERROR_WANT_READ:
                hub.disable_write(sock)
            elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                hub.enable_write(sock)
            else:
                hub.unregister(sock)
                raise
        else:
            hub.unregister(sock)
            next()
    hub.register(sock, shake, shake, shake)
    shake()
