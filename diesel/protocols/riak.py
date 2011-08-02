"""Riak protocol buffers client.

Provides a couple interfaces to working with a Riak database. 

The first is a lower-level Client object. It has methods for interacting with
the server, buckets, keys and values. The methods are more verbose and return
dense dictionaries of data.

The other interface is via Buckets. These use a Client to allow you to work
with keys and values in the context of a Riak bucket. They offer a simpler API
and hooks for conflict resolution and custom loading/dumping of values.

"""
import struct

import diesel
from diesel.util.queue import Queue, QueueEmpty
from diesel.util.event import Event

try:
    import riak_proto as riak_pb2 # fastproto-enabled
except ImportError:
    import sys
    sys.stderr.write("Warning: must use fastproto protocol buffers library.\n")
    sys.stderr.write("See diesel/tools/riak_fastproto.")
    raise SystemExit(1)

from contextlib import contextmanager

# The commented-out message codes and types below are for requests and/or
# responses that don't have a body.

MESSAGE_CODES = [
(0, riak_pb2.RpbErrorResp),
#(1, riak_pb2.RpbPingReq),
#(2, riak_pb2.RpbPingResp),
#(3, riak_pb2.RpbGetClientIdReq),
(4, riak_pb2.RpbGetClientIdResp),
(5, riak_pb2.RpbSetClientIdReq),
#(6, riak_pb2.RpbSetClientIdResp),
#(7, riak_pb2.RpbGetServerInfoReq),
(8, riak_pb2.RpbGetServerInfoResp),
(9, riak_pb2.RpbGetReq ),
(10, riak_pb2.RpbGetResp),
(11, riak_pb2.RpbPutReq ),
(12, riak_pb2.RpbPutResp),
(13, riak_pb2.RpbDelReq ),
#(14, riak_pb2.RpbDelResp),
#(15, riak_pb2.RpbListBucketsReq),
(16, riak_pb2.RpbListBucketsResp),
(17, riak_pb2.RpbListKeysReq),
(18, riak_pb2.RpbListKeysResp),
(19, riak_pb2.RpbGetBucketReq),
(20, riak_pb2.RpbGetBucketResp),
(21, riak_pb2.RpbSetBucketReq),
#(22, riak_pb2.RpbSetBucketResp),
(23, riak_pb2.RpbMapRedReq),
(24, riak_pb2.RpbMapRedResp),
]

resolutions_in_progress = {}

class ResolvedLookup(Event):
    def __init__(self, resolver):
        Event.__init__(self)
        self.error = None
        self.value = None
        self.resolver = resolver

@contextmanager
def in_resolution(bucket, key, entity):
    e = ResolvedLookup(entity)
    resolutions_in_progress[(bucket, key)] = e
    try:
        yield e
    except:
        a = resolutions_in_progress.pop((bucket, key))
        a.error = True
        a.set()
        raise
    else:
        del resolutions_in_progress[(bucket, key)]

PB_TO_MESSAGE_CODE = dict((cls, code) for code, cls in MESSAGE_CODES)
MESSAGE_CODE_TO_PB = dict(MESSAGE_CODES)

class BucketSubrequestException(Exception):
    def __init__(self, s, sub_exceptions):
        Exception.__init__(s)
        self.sub_exceptions = sub_exceptions

class Bucket(object):
    """A Bucket of keys/values in a Riak database.

    Buckets are intended to be cheap, non-shared objects for easily performing
    common key/value operations with Riak.

    Buckets should not be shared amongst concurrent consumers. Each consumer
    should have its own Bucket instance. This is due to the way vector clocks
    are tracked on the Bucket instances.

    """
    def __init__(self, name, client=None, make_client_context=None, resolver=None):
        """Return a new Bucket for the named bucket, using the given client.

        If your bucket allows sibling content (conflicts) you should supply a
        conflict resolver function or subclass and override ``resolve``. It
        should take four arguments and return a resolved value. Here is an
        example::

            def resolve_random(timestamp_1, value_1, timestamp_2, value_2):
                '''The worlds worst resolver function!'''
                return random.choice([value_1, value_2])

        """
        assert client is not None or make_client_context is not None,\
        "Must specify either client or make_client_context"
        assert not (client is not None and make_client_context is not None),\
        "Cannot specify both client and make_client_context"
        self.name = name
        if make_client_context:
            self.make_client_context = make_client_context
            self.used_client_context = True
        else:
            @contextmanager
            def noop_cm():
                yield client
            self.make_client_context = noop_cm
            self.used_client_context = False
        self._vclocks = {}
        if resolver:
            self.resolve = resolver
        self.client_id = None

    def for_client(self, client_id):
        self.client_id = client_id
        return self

    def get(self, key):
        """Get the value for key from the bucket.
        
        Records the vector clock for the value for future modification
        using ``put`` with this same Bucket instance.
        
        """
        with self.make_client_context() as client:
            if self.client_id:
                client.set_client_id(self.client_id)
            response = client.get(self.name, key)
        if response:
            return self._handle_response(key, response, resave=False)

    def _subrequest(self, inq, outq):
        while True:
            try:
                key = inq.get(waiting=False)
            except QueueEmpty:
                break
            else:
                try:
                    res = self.get(key)
                except Exception, e:
                    outq.put((key, False, e))
                else:
                    outq.put((key, True, res))

    def get_many(self, keys, concurrency_limit=100, no_failures=False):
        assert self.used_client_context,\
        "Cannot fetch in parallel without a pooled make_client_context!"
        inq = Queue()
        outq = Queue()
        for k in keys:
            inq.put(k)

        for x in xrange(min(len(keys), concurrency_limit)):
            diesel.fork(self._subrequest, inq, outq)

        failure = False
        okay, err = [], []
        for k in keys:
            (key, success, val) = outq.get()
            if success:
                okay.append((key, val))
            else:
                err.append((key, val))

        if no_failures:
            raise BucketSubrequestException(
            "Error in parallel subrequests", err)
        return okay, err

    def put(self, key, value, safe=True, **params):
        """Puts the given key/value into the bucket.

        If safe==True the response will be read back and conflict resolution
        might take place as well if the put triggers multiple sibling values
        for the key.

        Extra params are passed to the ``Client.put`` method.
        """
        if safe:
            params['return_body'] = True
            if 'vclock' not in params and key in self._vclocks:
                params['vclock'] = self._vclocks.pop(key)
        with self.make_client_context() as client:
            if self.client_id:
                client.set_client_id(self.client_id)
            response = client.put(self.name, key, self.dumps(value), **params)
        if response:
            return self._handle_response(key, response)

    def delete(self, key):
        """Deletes all values for the given key from the bucket."""
        with self.make_client_context() as client:
            if self.client_id:
                client.set_client_id(self.client_id)
            client.delete(self.name, key)

    def keys(self):
        """Get all the keys for a given bucket, is an iterator."""
        with self.make_client_context() as client:
            if self.client_id:
                client.set_client_id(self.client_id)
            return client.keys(self.name)

    def _handle_response(self, key, response, resave=True):
        # Returns responses for non-conflicting content. Resolves conflicts
        # if there are multiple values for a key.
        resave = resave and self.track_siblings(key, len(response['content']))
        if len(response['content']) == 1:
            self._vclocks[key] = response['vclock']
            return self.loads(response['content'][0]['value'])
        else:
            res = (self.name, key)
            if res in resolutions_in_progress:
                ev = resolutions_in_progress[res]
                if ev.resolver == self:
                    # recursing on put() with > 1 response
                    return self._resolve(key, response, resave=resave)
                ev.wait()
                if not ev.error:
                    return ev.value
                else:
                    return self._handle_response(key, response, resave=resave)
            with in_resolution(*(res + (self,))) as ev:
                result = self._resolve(key, response, resave=resave)
                ev.value = result
                ev.set()
            return result

    def _resolve(self, key, response, resave=True):
        # Performs conflict resolution for the given key and response. If all
        # goes well a new harmonized value for the key will be put up to the
        # bucket. If things go wrong, expect ... exceptions. :-|
        res = response['content'].pop(0)
        while response['content']:
            other = response['content'].pop(0)
            other['value'] = self.dumps(
                self.resolve(
                    res['last_mod'], 
                    self.loads(res['value']),
                    other['last_mod'], 
                    self.loads(other['value']),
                )
            )
            res = other
        resolved_value = self.loads(res['value'])
        params = dict(vclock=response['vclock'], return_body=True)
        if resave:
            return self.put(key, resolved_value, **params)
        else:
            return resolved_value

    def resolve(self, timestamp1, value1, timestamp2, value2):
        """Subclass to support custom conflict resolution."""
        msg = "Pass in a resolver or override this method."
        raise NotImplementedError(msg)

    def loads(self, raw_value):
        """Subclass to support loading rich values."""
        return raw_value

    def dumps(self, rich_value):
        """Subclass to support dumping rich values."""
        return rich_value

    def track_siblings(self, key, siblings):
        return True


class RiakErrorResp(Exception):
    def __init__(self, error_resp):
        Exception.__init__(self, error_resp.errmsg, error_resp.errcode)
        self.errmsg = error_resp.errmsg
        self.errcode = error_resp.errcode

    def __repr__(self):
        return "RiakErrorResp: %s" % (self.errmsg)

class RiakClient(diesel.Client):
    """A client for the Riak distributed key/value database.
    
    Instances can be used stand-alone or passed to a Bucket constructor
    (which has a simpler API).
    
    """
    def __init__(self, host='127.0.0.1', port=8087, **kw):
        """Creates a new Riak Client connection object."""
        diesel.Client.__init__(self, host, port, **kw)

    @diesel.call
    def get(self, bucket, key):
        """Get the value of key from named bucket.
        
        Returns a dictionary with a list of the content for the key
        and the vector clock (vclock) for the key.
        
        """
        request = riak_pb2.RpbGetReq(bucket=bucket, key=key)
        self._send(request)
        response = self._receive()
        if response:
            return _to_dict(response)

    @diesel.call
    def put(self, bucket, key, value, **params):
        """Puts the value to the key in the named bucket.

        If an ``extra_content`` dictionary parameter is present, its content
        is merged into the RpbContent object.

        All other parameters are merged into the RpbPutReq object.

        """
        dict_content={'value':value}
        if 'extra_content' in params:
            dict_content.update(params.pop('extra_content'))
        content = riak_pb2.RpbContent(**dict_content)
        request = riak_pb2.RpbPutReq(
            bucket=bucket,
            key=key,
            content=content,
        )
        for name, value in params.iteritems():
            setattr(request, name, value)
        self._send(request)
        response = self._receive()
        if response:
            return _to_dict(response)

    @diesel.call
    def delete(self, bucket, key):
        """Deletes the given key from the named bucket, including all values."""
        request = riak_pb2.RpbDelReq(bucket=bucket, key=key)
        self._send(request)
        return self._receive()

    @diesel.call
    def keys(self, bucket):
        """Gets the keys for the given bucket, is an iterator"""
        request = riak_pb2.RpbListKeysReq(bucket=bucket)
        self._send(request)

        response = riak_pb2.RpbListKeysResp(done=False) #Do/while?
        while not response.done:
            response = self._receive()
            for key in response.keys:
                yield key

    @diesel.call
    def info(self):
        # No protocol buffer object to build or send.
        message_code = 7
        total_size = 1
        fmt = "!iB"
        diesel.send(struct.pack(fmt, total_size, message_code))
        return self._receive()

    @diesel.call
    def set_bucket_props(self, bucket, props):
        """Sets some properties on the named bucket.
        
        ``props`` should be a dictionary of properties supported by the
        RpbBucketProps protocol buffer.
        
        """
        request = riak_pb2.RpbSetBucketReq(bucket=bucket)
        bucket_props = riak_pb2.RpbBucketProps()
        for name, value in props.iteritems():
            setattr(bucket_props, name, value)
        request.props = bucket_props
        self._send(request)
        return self._receive()

    @diesel.call
    def set_client_id(self, client_id):
        """Sets the remote client id for this connection.

        This is crazy-important to do if your bucket allows sibling documents
        and you are reusing connections. In general, client ids should map to
        actors within your system.

        """
        request = riak_pb2.RpbSetClientIdReq(client_id=client_id)
        self._send(request)
        return self._receive()

    @diesel.call
    def _send(self, pb):
        # Send a protocol buffer on the wire as a request.
        message_code = PB_TO_MESSAGE_CODE[pb.__class__]
        message = pb.SerializeToString()
        message_size = len(message)
        total_size = message_size + 1 # plus 1 mc byte
        fmt = "!iB%ds" % message_size
        diesel.send(struct.pack(fmt, total_size, message_code, message))

    @diesel.call
    def _receive(self):
        # Receive a protocol buffer from the wire as a response.
        response_size, = struct.unpack('!i', diesel.receive(4))
        raw_response = diesel.receive(response_size)
        message_code, = struct.unpack('B',raw_response[0])
        response = raw_response[1:]
        if response:
            pb = MESSAGE_CODE_TO_PB[message_code]()
            pb.ParseFromString(response)
            if message_code == 0:
                # RpbErrorResp - raise an exception
                raise RiakErrorResp(pb)
            return pb

def _to_dict(pb):
    # Takes a protocol buffer (pb) and transforms it into a dict of more
    # common Python types.
    out = {}
    if hasattr(pb, 'ListFields'):
        fields = [d.name for (d, _) in pb.ListFields()]
    else:
        fields = [f for f in dir(pb) if f[0].islower()]
    for name in fields:
        value = getattr(pb, name)
        # Perform a couple sniff tests to see if a value is:
        # a) A protocol buffer
        # b) An iterable protocol buffer
        # c) Neither
        # Handles all of those situations.
        try:
            if type(value) == tuple:
                value = [_to_dict(v) for v in iter(value)]
            else:
                value.ParseFromString
                try:
                    value = [_to_dict(v) for v in iter(value)]
                except TypeError:
                    value = _to_dict(v)
        except AttributeError:
            pass
        out[name] = value
    return out


# Testing Code Below
# ==================
# XXX hack - can't define it in __main__ below
class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

if __name__ == '__main__':
    import cPickle

    def test_client():
        c = RiakClient()
        c.set_client_id('testing-client')

        # Do some cleanup from a previous run.
        c.delete('testing', 'bar')
        c.delete('testing', 'foo')
        c.delete('testing', 'lala')
        c.delete('testing', 'baz')
        c.delete('testing', 'diff')
        c.delete('testing.pickles', 'here')
        c.delete('testing.pickles', 'there')

        assert not c.get('testing', 'foo')
        assert c.put('testing', 'foo', '1', return_body=True)
        assert c.get('testing', 'foo')

        # Create a conflict for the 'bar' key in 'testing'.
        assert not c.set_bucket_props('testing', {'allow_mult':True})
        b1 = c.put('testing', 'bar', 'hi', return_body=True)
        b2 = c.put('testing', 'bar', 'bye', return_body=True)
        assert len(c.get('testing', 'bar')['content']) > 1

        def resolve_longest(t1, v1, t2, v2):
            if len(v1) > len(v2):
                return v1
            return v2

        # Test that the conflict is resolved, this time using the Bucket
        # interface.
        b = Bucket('testing', c, resolver=resolve_longest)
        resolved = b.get('bar')
        assert resolved == 'bye', resolved
        assert len(c.get('testing', 'bar')['content']) == 1

        # put/get/delete with a Bucket
        assert b.put('lala', 'g'*1024)
        assert b.get('lala') == 'g'*1024
        b.delete('lala')
        assert not b.get('lala')

        # Multiple changes to a key using a Bucket should be a-ok.
        assert b.put('baz', 'zzzz')
        assert b.put('baz', 'ffff')
        assert b.put('baz', 'tttt')
        assert len(c.get('testing', 'baz')['content']) == 1
        assert b.get('baz') == 'tttt'

        # Custom Bucket.
        class PickleBucket(Bucket): # lol
            def loads(self, raw_value):
                return cPickle.loads(raw_value)

            def dumps(self, rich_value):
                return cPickle.dumps(rich_value)

            def resolve(self, t1, v1, t2, v2):
                # Returns the value with the smallest different between points.
                d1 = abs(v1.x - v1.y)
                d2 = abs(v2.x - v2.y)
                if d1 < d2:
                    return v1
                return v2

        assert not c.set_bucket_props('testing.pickles', {'allow_mult':True})
        p = PickleBucket('testing.pickles', c)
        assert p.put('here', Point(4,2))
        out = p.get('here')
        assert (4,2) == (out.x, out.y)
        assert isinstance(out, Point)

        # Resolve Point conflicts.
        p1 = PickleBucket('testing.pickles', c).for_client('c 1')
        p1.put('there', Point(4,12), safe=False)
        p2 = PickleBucket('testing.pickles', c).for_client('c 2')
        p2.put('there', Point(3,7), safe=False)
        p3 = PickleBucket('testing.pickles', c).for_client('c 3')
        p3.put('there', Point(90,99), safe=False)
        p4 = PickleBucket('testing.pickles', c).for_client('c 4')
        p4.put('there', Point(4,10), safe=False)
        p5 = PickleBucket('testing.pickles', c).for_client('c 5')
        p5.put('there', Point(1,9), safe=False)
        assert len(c.get('testing.pickles', 'there')['content']) == 5
        there = p5.get('there')
        assert (3,7) == (there.x, there.y), (there.x, there.y)
        assert isinstance(there, Point)

        # Doing stuff with different client ids but the same vector clock.
        c.set_client_id('diff 1')
        assert b.put('diff', '---')
        c.set_client_id('diff 2')
        assert b.put('diff', '+++')
        assert b.get('diff') == '+++'
        
        # Provoking an error
        try:
            # Tell Riak to require 10000 nodes to write this before success.
            c.put('testing', 'error!', 'oh noes!', w=10000)
        except RiakErrorResp, e:
            assert e.errcode == 1, e.errcode
            assert e.errmsg == '{n_val_violation,3}', e.errmsg
            assert repr(e) == "RiakErrorResp: {n_val_violation,3}", repr(e)
        except Exception, e:
            assert 0, "UNEXPECTED EXCEPTION: %r" % e
        else:
            assert 0, "DID NOT RAISE"
        diesel.quickstop()
    diesel.quickstart(test_client)

del Point
