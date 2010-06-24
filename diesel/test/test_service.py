from diesel.tests import DieselTest
from diesel import Loop, sleep, Service, until_eol, until, count, send
import thread, socket, time
from uuid import uuid4

class TestEchoService(DieselTest):
    def test_basic_echo(self):
        PORT = 51372 
        NUM = 5
        app, touch, acc = self.prepare_test()
        def handle_echo(conn):
            said = until_eol()
            send( 'YS:' + said )
            touch()

        def b_client():
            time.sleep(0.5)
            r = uuid4().hex
            s = socket.socket()
            s.connect(('localhost', PORT))
            s.sendall(r + '\r\n')
            back = s.recv(65536)
            cl = s.recv(500)
            acc[r] = back, cl

        for x in xrange(NUM):
            thread.start_new_thread(b_client, ())
        app.add_service(Service(handle_echo, PORT))
        self.run_test(NUM)

        for key, (back, cl) in acc.iteritems():
            assert back == 'YS:%s\r\n' % key
            assert cl == ''

    def test_back_and_forth(self):
        PORT = 51372 
        NUM = 5
        app, touch, acc = self.prepare_test()
        def handle_echo(conn):
            said = until_eol()
            out = 'YS:' + said

            send( out )
            for c in out:
                send( c )

            touch()

        def b_client():
            time.sleep(0.5)
            r = uuid4().hex
            s = socket.socket()
            s.connect(('localhost', PORT))
            s.sendall(r + '\r\n')
            time.sleep(0.2)
            back = s.recv(65536)
            cl = s.recv(500)
            acc[r] = back, cl

        for x in xrange(NUM):
            thread.start_new_thread(b_client, ())
        app.add_service(Service(handle_echo, PORT))
        self.run_test(NUM)

        for key, (back, cl) in acc.iteritems():
            assert back == ('YS:%s\r\n' % key) * 2
            assert cl == ''

    def test_byte_boundaries(self):
        PORT = 51372 
        NUM = 5
        app, touch, acc = self.prepare_test()
        def handle_echo(conn):
            size = int((until('|'))[:-1])
            said = count(size)
            out = 'YS:' + said

            send( out )

            touch()

        def b_client():
            time.sleep(0.5)
            r = uuid4().bytes
            s = socket.socket()
            s.connect(('localhost', PORT))
            s.send('%s|' % len(r))
            s.sendall(r)
            time.sleep(0.2)
            back = s.recv(65536)
            cl = s.recv(500)
            acc[r] = back, cl

        for x in xrange(NUM):
            thread.start_new_thread(b_client, ())
        app.add_service(Service(handle_echo, PORT))
        self.run_test(NUM)

        for key, (back, cl) in acc.iteritems():
            assert back == ('YS:%s\r\n' % key) * 2
            assert cl == ''
