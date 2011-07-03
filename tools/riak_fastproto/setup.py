try:
  from setuptools import setup, Extension
except ImportError:
  from distutils.core import setup, Extension

setup(name="proto_wrapper",
      version="1.0",
      packages=[
        
      ],
      package_dir={
        
      },
      ext_modules=[
        
          Extension("riak_proto", ["riak.cc", "riak.pb.cc"], libraries=['protobuf']),
        
      ],
      test_suite="test.suite")