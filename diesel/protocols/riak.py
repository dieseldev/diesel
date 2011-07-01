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

class RiakClient(diesel.Client):
    def __init__(self, host='127.0.0.1', port=8087, **kw):
        diesel.Client.__init__(self, host, port, **kw)

    @diesel.call
    def get(self, bucket, key):
        pb = riak_pb2.RpbGetReq(bucket=bucket, key=key)
        self._send(pb)
        return self._receive()


    @diesel.call
    def put(self, bucket, key, value):
        content = riak_pb2.RpbContent(value=value)
        pb = riak_pb2.RpbPutReq(bucket=bucket, key=key, content=content)
        self._send(pb)
        return self._receive()

    @diesel.call
    def info(self):
        message_code = 7
        total_size = 1
        fmt = "!iB"
        diesel.send(struct.pack(fmt, total_size, message_code))
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
        #import pdb;pdb.set_trace()
        if response_size:
            raw_response = diesel.receive(response_size)
            message_code, = struct.unpack('B',raw_response[0])
            response = raw_response[1:]
            pb = MESSAGE_CODE_TO_PB[message_code]()
            pb.ParseFromString(response)
            return pb

if __name__ == '__main__':
    def test_client():
        c = RiakClient()
        c.put('testing', 'foo', '1')
        resp = c.get('testing', 'foo')
        print resp
        diesel.quickstop()
    diesel.quickstart(test_client)
