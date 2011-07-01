#!/usr/bin/env python
"""Auto-generated unit tests."""

import unittest


import riak_proto





class Test_riak_proto(unittest.TestCase):
  
  def testRpbErrorResp_Basics(self):
    pb = riak_proto.RpbErrorResp()
    
    
    pb.errmsg = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.errmsg)
    
    
    
    pb.errcode = 2
    self.assertEquals(2, pb.errcode)
    
    

    pb2 = riak_proto.RpbErrorResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.errmsg, pb2.errmsg)
    
    self.assertEquals(pb.errcode, pb2.errcode)
    
  
  def testRpbGetClientIdResp_Basics(self):
    pb = riak_proto.RpbGetClientIdResp()
    
    
    pb.client_id = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.client_id)
    
    

    pb2 = riak_proto.RpbGetClientIdResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.client_id, pb2.client_id)
    
  
  def testRpbSetClientIdReq_Basics(self):
    pb = riak_proto.RpbSetClientIdReq()
    
    
    pb.client_id = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.client_id)
    
    

    pb2 = riak_proto.RpbSetClientIdReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.client_id, pb2.client_id)
    
  
  def testRpbGetServerInfoResp_Basics(self):
    pb = riak_proto.RpbGetServerInfoResp()
    
    
    pb.node = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.node)
    
    
    
    pb.server_version = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.server_version)
    
    

    pb2 = riak_proto.RpbGetServerInfoResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.node, pb2.node)
    
    self.assertEquals(pb.server_version, pb2.server_version)
    
  
  def testRpbGetReq_Basics(self):
    pb = riak_proto.RpbGetReq()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    
    
    pb.key = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.key)
    
    
    
    pb.r = 3
    self.assertEquals(3, pb.r)
    
    
    
    pb.pr = 4
    self.assertEquals(4, pb.pr)
    
    
    
    pb.basic_quorum = True
    self.assertEquals(True, pb.basic_quorum)
    
    
    
    pb.notfound_ok = True
    self.assertEquals(True, pb.notfound_ok)
    
    
    
    pb.if_modified = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.if_modified)
    
    
    
    pb.head = True
    self.assertEquals(True, pb.head)
    
    
    
    pb.deletedvclock = True
    self.assertEquals(True, pb.deletedvclock)
    
    

    pb2 = riak_proto.RpbGetReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
    self.assertEquals(pb.key, pb2.key)
    
    self.assertEquals(pb.r, pb2.r)
    
    self.assertEquals(pb.pr, pb2.pr)
    
    self.assertEquals(pb.basic_quorum, pb2.basic_quorum)
    
    self.assertEquals(pb.notfound_ok, pb2.notfound_ok)
    
    self.assertEquals(pb.if_modified, pb2.if_modified)
    
    self.assertEquals(pb.head, pb2.head)
    
    self.assertEquals(pb.deletedvclock, pb2.deletedvclock)
    
  
  def testRpbGetResp_Basics(self):
    pb = riak_proto.RpbGetResp()
    
    
    
    
    pb.vclock = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.vclock)
    
    
    
    pb.unchanged = True
    self.assertEquals(True, pb.unchanged)
    
    

    pb2 = riak_proto.RpbGetResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.content, pb2.content)
    
    self.assertEquals(pb.vclock, pb2.vclock)
    
    self.assertEquals(pb.unchanged, pb2.unchanged)
    
  
  def testRpbPutReq_Basics(self):
    pb = riak_proto.RpbPutReq()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    
    
    pb.key = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.key)
    
    
    
    pb.vclock = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.vclock)
    
    
    
    
    
    pb.w = 5
    self.assertEquals(5, pb.w)
    
    
    
    pb.dw = 6
    self.assertEquals(6, pb.dw)
    
    
    
    pb.return_body = True
    self.assertEquals(True, pb.return_body)
    
    
    
    pb.pw = 8
    self.assertEquals(8, pb.pw)
    
    
    
    pb.if_not_modified = True
    self.assertEquals(True, pb.if_not_modified)
    
    
    
    pb.if_none_match = True
    self.assertEquals(True, pb.if_none_match)
    
    
    
    pb.return_head = True
    self.assertEquals(True, pb.return_head)
    
    

    pb2 = riak_proto.RpbPutReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
    self.assertEquals(pb.key, pb2.key)
    
    self.assertEquals(pb.vclock, pb2.vclock)
    
    self.assertEquals(pb.content, pb2.content)
    
    self.assertEquals(pb.w, pb2.w)
    
    self.assertEquals(pb.dw, pb2.dw)
    
    self.assertEquals(pb.return_body, pb2.return_body)
    
    self.assertEquals(pb.pw, pb2.pw)
    
    self.assertEquals(pb.if_not_modified, pb2.if_not_modified)
    
    self.assertEquals(pb.if_none_match, pb2.if_none_match)
    
    self.assertEquals(pb.return_head, pb2.return_head)
    
  
  def testRpbPutResp_Basics(self):
    pb = riak_proto.RpbPutResp()
    
    
    
    
    pb.vclock = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.vclock)
    
    
    
    pb.key = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.key)
    
    

    pb2 = riak_proto.RpbPutResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.content, pb2.content)
    
    self.assertEquals(pb.vclock, pb2.vclock)
    
    self.assertEquals(pb.key, pb2.key)
    
  
  def testRpbDelReq_Basics(self):
    pb = riak_proto.RpbDelReq()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    
    
    pb.key = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.key)
    
    
    
    pb.rw = 3
    self.assertEquals(3, pb.rw)
    
    
    
    pb.vclock = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.vclock)
    
    
    
    pb.r = 5
    self.assertEquals(5, pb.r)
    
    
    
    pb.w = 6
    self.assertEquals(6, pb.w)
    
    
    
    pb.pr = 7
    self.assertEquals(7, pb.pr)
    
    
    
    pb.pw = 8
    self.assertEquals(8, pb.pw)
    
    
    
    pb.dw = 9
    self.assertEquals(9, pb.dw)
    
    

    pb2 = riak_proto.RpbDelReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
    self.assertEquals(pb.key, pb2.key)
    
    self.assertEquals(pb.rw, pb2.rw)
    
    self.assertEquals(pb.vclock, pb2.vclock)
    
    self.assertEquals(pb.r, pb2.r)
    
    self.assertEquals(pb.w, pb2.w)
    
    self.assertEquals(pb.pr, pb2.pr)
    
    self.assertEquals(pb.pw, pb2.pw)
    
    self.assertEquals(pb.dw, pb2.dw)
    
  
  def testRpbListBucketsResp_Basics(self):
    pb = riak_proto.RpbListBucketsResp()
    
    
    pb.buckets = (b'\x00\x01\x02',)
    self.assertEquals((b'\x00\x01\x02',), pb.buckets)
    
    

    pb2 = riak_proto.RpbListBucketsResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.buckets, pb2.buckets)
    
  
  def testRpbListKeysReq_Basics(self):
    pb = riak_proto.RpbListKeysReq()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    

    pb2 = riak_proto.RpbListKeysReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
  
  def testRpbListKeysResp_Basics(self):
    pb = riak_proto.RpbListKeysResp()
    
    
    pb.keys = (b'\x00\x01\x02',)
    self.assertEquals((b'\x00\x01\x02',), pb.keys)
    
    
    
    pb.done = True
    self.assertEquals(True, pb.done)
    
    

    pb2 = riak_proto.RpbListKeysResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.keys, pb2.keys)
    
    self.assertEquals(pb.done, pb2.done)
    
  
  def testRpbGetBucketReq_Basics(self):
    pb = riak_proto.RpbGetBucketReq()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    

    pb2 = riak_proto.RpbGetBucketReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
  
  def testRpbGetBucketResp_Basics(self):
    pb = riak_proto.RpbGetBucketResp()
    
    
    

    pb2 = riak_proto.RpbGetBucketResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.props, pb2.props)
    
  
  def testRpbSetBucketReq_Basics(self):
    pb = riak_proto.RpbSetBucketReq()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    
    
    

    pb2 = riak_proto.RpbSetBucketReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
    self.assertEquals(pb.props, pb2.props)
    
  
  def testRpbMapRedReq_Basics(self):
    pb = riak_proto.RpbMapRedReq()
    
    
    pb.request = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.request)
    
    
    
    pb.content_type = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.content_type)
    
    

    pb2 = riak_proto.RpbMapRedReq()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.request, pb2.request)
    
    self.assertEquals(pb.content_type, pb2.content_type)
    
  
  def testRpbMapRedResp_Basics(self):
    pb = riak_proto.RpbMapRedResp()
    
    
    pb.phase = 1
    self.assertEquals(1, pb.phase)
    
    
    
    pb.response = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.response)
    
    
    
    pb.done = True
    self.assertEquals(True, pb.done)
    
    

    pb2 = riak_proto.RpbMapRedResp()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.phase, pb2.phase)
    
    self.assertEquals(pb.response, pb2.response)
    
    self.assertEquals(pb.done, pb2.done)
    
  
  def testRpbContent_Basics(self):
    pb = riak_proto.RpbContent()
    
    
    pb.value = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.value)
    
    
    
    pb.content_type = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.content_type)
    
    
    
    pb.charset = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.charset)
    
    
    
    pb.content_encoding = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.content_encoding)
    
    
    
    pb.vtag = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.vtag)
    
    
    
    
    
    pb.last_mod = 7
    self.assertEquals(7, pb.last_mod)
    
    
    
    pb.last_mod_usecs = 8
    self.assertEquals(8, pb.last_mod_usecs)
    
    
    
    

    pb2 = riak_proto.RpbContent()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.value, pb2.value)
    
    self.assertEquals(pb.content_type, pb2.content_type)
    
    self.assertEquals(pb.charset, pb2.charset)
    
    self.assertEquals(pb.content_encoding, pb2.content_encoding)
    
    self.assertEquals(pb.vtag, pb2.vtag)
    
    self.assertEquals(pb.links, pb2.links)
    
    self.assertEquals(pb.last_mod, pb2.last_mod)
    
    self.assertEquals(pb.last_mod_usecs, pb2.last_mod_usecs)
    
    self.assertEquals(pb.usermeta, pb2.usermeta)
    
  
  def testRpbPair_Basics(self):
    pb = riak_proto.RpbPair()
    
    
    pb.key = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.key)
    
    
    
    pb.value = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.value)
    
    

    pb2 = riak_proto.RpbPair()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.key, pb2.key)
    
    self.assertEquals(pb.value, pb2.value)
    
  
  def testRpbLink_Basics(self):
    pb = riak_proto.RpbLink()
    
    
    pb.bucket = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.bucket)
    
    
    
    pb.key = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.key)
    
    
    
    pb.tag = b'\x00\x01\x02'
    self.assertEquals(b'\x00\x01\x02', pb.tag)
    
    

    pb2 = riak_proto.RpbLink()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.bucket, pb2.bucket)
    
    self.assertEquals(pb.key, pb2.key)
    
    self.assertEquals(pb.tag, pb2.tag)
    
  
  def testRpbBucketProps_Basics(self):
    pb = riak_proto.RpbBucketProps()
    
    
    pb.n_val = 1
    self.assertEquals(1, pb.n_val)
    
    
    
    pb.allow_mult = True
    self.assertEquals(True, pb.allow_mult)
    
    

    pb2 = riak_proto.RpbBucketProps()
    pb2.ParseFromString(pb.SerializeToString())

    
    self.assertEquals(pb.n_val, pb2.n_val)
    
    self.assertEquals(pb.allow_mult, pb2.allow_mult)
    
  



def suite():
  suite = unittest.TestSuite()
  
  suite.addTests(unittest.makeSuite(Test_riak_proto))
  
  return suite