from subprocess import Popen, PIPE


def gen_riak_protobufs():
    protoc = Popen(
        [
            "protoc", 
            "--proto_path=tools/",
            "--python_out=diesel/protocols", 
            "tools/riak.proto",
        ], 
    )

    protoc.communicate()

if __name__ == '__main__':
    gen_riak_protobufs()
