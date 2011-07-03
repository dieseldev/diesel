from subprocess import Popen, PIPE
import os

def gen_riak_protobufs():
    if not os.path.exists('riak_fastproto'):
        os.mkdir('riak_fastproto')
    protoc = Popen(
        [
            "protoc", 
            "--proto_path=.",
            "--fastpython_out=riak_fastproto", 
            "--cpp_out=riak_fastproto", 
            "riak.proto",
        ], 
    )

    protoc.communicate()

if __name__ == '__main__':
    gen_riak_protobufs()
