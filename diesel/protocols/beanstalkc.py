"""
Beanstalkd client implementation stolen from
https://github.com/earl/beanstalkc.git v0.2.0 and lightly adapted for diesel.
"""

__license__ = '''
Copyright (C) 2008, 2009 Andreas Bolka
Copyright (C) 2010, 2011 Michael Schurter

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import diesel
import yaml


BEANSTALK_PORT = 11300
DEFAULT_PRIORITY = 2**31
DEFAULT_TTR = 120


class BeanstalkcException(Exception): pass
class UnexpectedResponse(BeanstalkcException): pass
class CommandFailed(BeanstalkcException): pass
class DeadlineSoon(BeanstalkcException): pass


class BeanstalkClient(diesel.Client):
    def __init__(self, host='localhost', port=BEANSTALK_PORT):
        diesel.Client.__init__(self, host, port)

    def close(self):
        """Gracefully close beanstalk connection"""
        try:
            diesel.send('quit\r\n')
            diesel.Client.close(self)
        except diesel.ConnectionClosed:
            pass

    def _interact(self, command, expected_ok, expected_err=None):
        """Send a command and wait for a response"""
        if expected_err is None:
            expected_err = []
        diesel.send(command)
        status, results = self._read_response()
        if status in expected_ok:
            return results
        elif status in expected_err:
            raise CommandFailed(command.split()[0], status, results)
        else:
            raise UnexpectedResponse(command.split()[0], status, results)

    def _read_response(self):
        line = diesel.until_eol()
        # TODO Check for EOF? (line = Falsey)
        response = line.split()
        return response[0], response[1:]

    def _read_body(self, size):
        return diesel.receive(size + 2) # size + len('\r\n')

    def _interact_value(self, command, expected_ok, expected_err=None):
        return self._interact(command, expected_ok, expected_err)[0]

    def _interact_job(self, command, expected_ok, expected_err, reserved=True):
        jid, size = self._interact(command, expected_ok, expected_err)
        body = self._read_body(int(size))
        return Job(self, int(jid), body, reserved)

    def _interact_yaml(self, command, expected_ok, expected_err=None):
        size, = self._interact(command, expected_ok, expected_err)
        body = self._read_body(int(size))
        return yaml.load(body)

    def _interact_peek(self, command):
        try:
            return self._interact_job(command, ['FOUND'], ['NOT_FOUND'], False)
        except CommandFailed, (_, status, results):
            return None

    # -- public interface --

    @diesel.call
    def put(self, body, priority=DEFAULT_PRIORITY, delay=0, ttr=DEFAULT_TTR):
        assert isinstance(body, str), 'Job body must be a str instance'
        jid = self._interact_value(
                'put %d %d %d %d\r\n%s\r\n' %
                    (priority, delay, ttr, len(body), body),
                ['INSERTED', 'BURIED'], ['JOB_TOO_BIG'])
        return int(jid)

    @diesel.call
    def reserve(self, timeout=None):
        if timeout is not None:
            command = 'reserve-with-timeout %d\r\n' % timeout
        else:
            command = 'reserve\r\n'
        try:
            return self._interact_job(command,
                                      ['RESERVED'],
                                      ['DEADLINE_SOON', 'TIMED_OUT'])
        except CommandFailed, (_, status, results):
            if status == 'TIMED_OUT':
                return None
            elif status == 'DEADLINE_SOON':
                raise DeadlineSoon(results)

    @diesel.call
    def kick(self, bound=1):
        return int(self._interact_value('kick %d\r\n' % bound, ['KICKED']))

    @diesel.call
    def peek(self, jid):
        return self._interact_peek('peek %d\r\n' % jid)

    @diesel.call
    def peek_ready(self):
        return self._interact_peek('peek-ready\r\n')

    @diesel.call
    def peek_delayed(self):
        return self._interact_peek('peek-delayed\r\n')

    @diesel.call
    def peek_buried(self):
        return self._interact_peek('peek-buried\r\n')

    @diesel.call
    def tubes(self):
        return self._interact_yaml('list-tubes\r\n', ['OK'])

    @diesel.call
    def using(self):
        return self._interact_value('list-tube-used\r\n', ['USING'])

    @diesel.call
    def use(self, name):
        return self._interact_value('use %s\r\n' % name, ['USING'])

    @diesel.call
    def watching(self):
        return self._interact_yaml('list-tubes-watched\r\n', ['OK'])

    @diesel.call
    def watch(self, name):
        return int(self._interact_value('watch %s\r\n' % name, ['WATCHING']))

    @diesel.call
    def ignore(self, name):
        try:
            return int(self._interact_value('ignore %s\r\n' % name,
                                            ['WATCHING'],
                                            ['NOT_IGNORED']))
        except CommandFailed:
            return 1

    @diesel.call
    def stats(self):
        return self._interact_yaml('stats\r\n', ['OK'])

    @diesel.call
    def stats_tube(self, name):
        return self._interact_yaml('stats-tube %s\r\n' % name,
                                  ['OK'],
                                  ['NOT_FOUND'])

    @diesel.call
    def pause_tube(self, name, delay):
        self._interact('pause-tube %s %d\r\n' %(name, delay),
                       ['PAUSED'],
                       ['NOT_FOUND'])

    # -- job interactors --

    @diesel.call
    def delete(self, jid):
        self._interact('delete %d\r\n' % jid, ['DELETED'], ['NOT_FOUND'])

    @diesel.call
    def release(self, jid, priority=DEFAULT_PRIORITY, delay=0):
        self._interact('release %d %d %d\r\n' % (jid, priority, delay),
                       ['RELEASED', 'BURIED'],
                       ['NOT_FOUND'])

    @diesel.call
    def bury(self, jid, priority=DEFAULT_PRIORITY):
        self._interact('bury %d %d\r\n' % (jid, priority),
                       ['BURIED'],
                       ['NOT_FOUND'])

    @diesel.call
    def touch(self, jid):
        self._interact('touch %d\r\n' % jid, ['TOUCHED'], ['NOT_FOUND'])

    @diesel.call
    def stats_job(self, jid):
        return self._interact_yaml('stats-job %d\r\n' % jid,
                                   ['OK'],
                                   ['NOT_FOUND'])



class Job(object):
    """Copied from beanstalkc.py v0.2.0"""
    def __init__(self, conn, jid, body, reserved=True):
        self.conn = conn
        self.jid = jid
        self.body = body
        self.reserved = reserved

    def _priority(self):
        stats = self.stats()
        if isinstance(stats, dict):
            return stats['pri']
        return DEFAULT_PRIORITY

    # -- public interface --

    def delete(self):
        self.conn.delete(self.jid)
        self.reserved = False

    def release(self, priority=None, delay=0):
        if self.reserved:
            self.conn.release(self.jid, priority or self._priority(), delay)
            self.reserved = False

    def bury(self, priority=None):
        if self.reserved:
            self.conn.bury(self.jid, priority or self._priority())
            self.reserved = False

    def touch(self):
        if self.reserved:
            self.conn.touch(self.jid)

    def stats(self):
        return self.conn.stats_job(self.jid)
