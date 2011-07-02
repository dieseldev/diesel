"""Riak protocol buffers client.

"""
import struct

import diesel

from diesel.protocols import riak_pb2


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

PB_TO_MESSAGE_CODE = dict((cls, code) for code, cls in MESSAGE_CODES)
MESSAGE_CODE_TO_PB = dict(MESSAGE_CODES)

def object_resolver(resolution_function):
    def resolve_all(response):
        res = response['content'].pop(0)
        while response['content']:
            other = response['content'].pop(0)
            other['value'] = resolution_function(
                res['last_mod'], res['value'],
                other['last_mod'], other['value'],
            )
            res = other
        return res['value']
    return resolve_all

class Bucket(object):
    def __init__(self, name, client, resolver=None):
        self.name = name
        self.client = client
        self._resolver = object_resolver(resolver)

    def get(self, key):
        # XXX problem here is that we don't return the vector clock
        # for subsequent puts of the returned value.
        response = self.client.get(self.name, key)
        if response:
            return self._handle_response(key, response)

    def put(self, key, value, **params):
        response = self.client.put(self.name, key, value, **params)
        if response:
            return self._handle_response(key, response)

    def delete(self, key):
        self.client.delete(self.name, key)

    def _handle_response(self, key, response):
        if len(response['content']) == 1:
            return response['content'][0]['value']
        else:
            return self._resolve(key, response)

    def _resolve(self, key, response):
        resolved_value = self._resolver(response)
        params = dict(vclock=response['vclock'], return_body=True)
        return self.put(key, resolved_value, **params)


class RiakClient(diesel.Client):
    def __init__(self, host='127.0.0.1', port=8087, **kw):
        diesel.Client.__init__(self, host, port, **kw)

    @diesel.call
    def get(self, bucket, key):
        """Get the value of key from bucket.
        
        Returns a dictionary with a list of the content for the key
        and the vector clock (vclock) for the key.
        
        """
        request = riak_pb2.RpbGetReq(bucket=bucket, key=key)
        self._send(request)
        response = self._receive()
        if response:
            return to_dict(response)

    @diesel.call
    def put(self, bucket, key, value, **params):
        """Puts the value to the key in the bucket.

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
            return to_dict(response)

    @diesel.call
    def delete(self, bucket, key):
        request = riak_pb2.RpbDelReq(bucket=bucket, key=key)
        self._send(request)
        return self._receive()

    @diesel.call
    def info(self):
        message_code = 7
        total_size = 1
        fmt = "!iB"
        diesel.send(struct.pack(fmt, total_size, message_code))
        return self._receive()

    @diesel.call
    def set_bucket_props(self, bucket, props):
        request = riak_pb2.RpbSetBucketReq(bucket=bucket)
        for name, value in props.iteritems():
            setattr(request.props, name, value)
        self._send(request)
        return self._receive()

    def _send(self, pb):
        message_code = PB_TO_MESSAGE_CODE[pb.__class__]
        message = pb.SerializeToString()
        message_size = len(message)
        total_size = message_size + 1 # plus 1 mc byte
        fmt = "!iB%ds" % message_size
        diesel.send(struct.pack(fmt, total_size, message_code, message))

    def _receive(self):
        response_size, = struct.unpack('!i', diesel.receive(4))
        raw_response = diesel.receive(response_size)
        message_code, = struct.unpack('B',raw_response[0])
        response = raw_response[1:]
        if response:
            pb = MESSAGE_CODE_TO_PB[message_code]()
            pb.ParseFromString(response)
            return pb

def to_dict(pb):
    out = {}
    for descriptor, value in pb.ListFields():
        try:
            value.MergeFrom
            value = [to_dict(v) for v in iter(value)]
        except (AttributeError, TypeError):
            pass
        out[descriptor.name] = value
    return out

if __name__ == '__main__':
    def test_client():
        c = RiakClient()
        c.delete('testing', 'bar')
        c.delete('testing', 'foo')
        c.get('testing', 'foo')
        assert c.put('testing', 'foo', '1', return_body=True)
        assert c.get('testing', 'foo')

        c.set_bucket_props('testing', {'allow_mult':True})
        assert c.put('testing', 'bar', 'hi', return_body=True)
        assert c.put('testing', 'bar', 'bye', return_body=True)
        assert len(c.get('testing', 'bar')['content']) > 1

        def resolve_longest(t1, v1, t2, v2):
            if len(v1) > len(v2):
                return v1
            return v2

        b = Bucket('testing', c, resolve_longest)
        resolved = b.get('bar')
        assert resolved == 'bye', resolved
        assert len(c.get('testing', 'bar')['content']) == 1
        assert not b.put('lala', 'g'*1024)
        assert b.get('lala') == 'g'*1024
        b.delete('lala')
        assert not b.get('lala')

        diesel.quickstop()
    diesel.quickstart(test_client)
