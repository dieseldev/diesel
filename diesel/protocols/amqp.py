from diesel import Client, bytes, up
from struct import pack, unpack, calcsize

FRAME_METHOD = 1
FRAME_HEADER = 2
FRAME_BODY = 3

class BinaryFeed(object):
    def __init__(self, data):
        self.data = data
        self.mark = 0

    def get(self, fmt):
        sz = calcsize(fmt)
        vals = unpack(fmt, self.data[self.mark:self.mark+sz])
        self.mark += sz
        return vals[0] if len(vals) == 1 else vals

class AMQPMethod(object):
    def __init__(self, cls, method):
        self.cls = cls
        self.method = method

    def __str__(self):
        return '%s.%s' % (self.cls, self.method)

def get_field_table(feed):
    def g():
        table_length = feed.get('>I')
        keep = feed.mark
        while feed.mark - keep < table_length:
            fname_size = feed.get('>B')
            fname, field_type = feed.get('>%sss' % fname_size)
            if field_type == 'S':
                string_size = feed.get('>I')
                value = feed.get('>%ss' % string_size)
            elif field_type == 'I':
                value = feed.get('>i')
            elif field_type == 'D':
                value = None
            elif field_type == 'T':
                value = feed.get('>Q')
            elif field_type == 'F':
                value = get_field_table(feed)
            
            yield fname, value
    return dict(g())

class AMQPClient(Client):
    def get_frame(self):
        frame_header = yield bytes(7)
        typ, chan, size = unpack('>BHI', frame_header)

        payload = yield bytes(size)
        
        assert (yield bytes(1)) == '\xce' # frame-end

        if typ == FRAME_METHOD:
            yield up(self.handle_method(payload))

        elif typ == FRAME_HEADER:
            yield up(self.handle_content_header(payload))

        elif typ == FRAME_BODY:
            yield up(self.handle_content_body(payload))

    def handle_method(self, data):
        feed = BinaryFeed(data)
        class_id, method_id = feed.get('>HH')
        print class_id, method_id
        vmaj, vmin = feed.get('>BB')
        fields = get_field_table(feed)
        security = feed.get('>%ss' % feed.get('>I'))
        locales = feed.get('>%ss' % feed.get('>I'))
        
        return AMQPMethod(class_id, method_id)

    def on_connect(self):
        yield pack('>4sBBBB', "AMQP", 1, 1, 9, 1) # protocol header
        method = yield self.get_frame()
        print method
