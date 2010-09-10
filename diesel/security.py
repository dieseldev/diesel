from OpenSSL import SSL
import traceback

def ssl_async_handshake(sock, hub, next):
    def shake():
        try:
            sock.do_handshake()
        except SSL.WantReadError:
            hub.disable_write(sock)
        except SSL.WantWriteError:
            hub.enable_write(sock)
        except SSL.WantX509LookupError:
            pass
        except SSL.ZeroReturnError:
            hub.unregister(sock) # and ignore
        except SSL.SysCallError:
            hub.unregister(sock) # and ignore
        except:
            hub.unregister(sock)
            sys.stderr.write("Unknown Error on connect():\n%s"
            % traceback.format_exc())
        else:
            hub.unregister(sock)
            next()
    hub.register(sock, shake, shake, shake)
    shake()
