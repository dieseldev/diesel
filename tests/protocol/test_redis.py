import diesel
from diesel.protocols.redis import *

class RedisHarness(object):
    def setup(self):
        self.client = RedisClient()
        self.client.select(11)
        self.client.flushdb()

class TestRedis(RedisHarness):
    def test_basic(self):
        r = self.client
        assert r.get('newdb') == None
        r.set('newdb', '1')

        r.set('foo3', 'bar')
        assert r.exists('foo3')
        r.delete('foo3')
        assert not r.exists('foo3')

        for x in range(5000):
            r.set('foo', 'bar')

        assert r.get('foo') == 'bar'
        assert r.get('foo2') == None

        assert r.exists('foo') == True
        assert r.exists('foo2') == False

        assert r.type('foo') == 'string'
        assert r.type('foo2') == 'none'
        assert r.keys('fo*') == set(['foo'])
        assert r.keys('bo*') == set()

        assert r.randomkey()

        r.rename('foo', 'bar')
        assert r.get('foo') == None
        assert r.get('bar') == 'bar'

        r.rename('bar', 'foo')
        assert r.get('foo') == 'bar'
        assert r.get('bar') == None
        assert r.dbsize()

        assert r.ttl('foo') == None

        r.setex("gonesoon", 3, "whatever")
        assert 0 < r.ttl("gonesoon") <= 3.0

        r.set("phrase", "to be or ")
        r.append("phrase", "not to be")
        assert r.get("phrase") == "to be or not to be"
        assert r.substr('phrase', 3, 11) == 'be or not'

        r.set("one", "two")
        assert r.mget(["one", "foo"]) == ['two', 'bar']
        r.mset({"one" : "three", "foo":  "four"})
        assert r.mget(["one", "foo"]) == ['three', 'four']

    def test_incr(self):
        r = self.client
        assert r.incr("counter") == 1
        assert r.get('counter') == '1'
        assert r.incr("counter") == 2
        assert r.get('counter') == '2'
        assert r.incrby("counter", 2) == 4
        assert r.get('counter') == '4'

    def test_decr(self):
        r = self.client
        r.set('counter', '4')
        assert r.decr("counter") == 3
        assert r.decr("counter") == 2
        assert r.decrby("counter", 2) == 0

    def test_lists(self):
        r = self.client
        r.rpush("ml", 5)
        r.lpush("ml", 1)
        assert r.lrange("ml", 0, 500) == ['1', '5']
        assert r.llen("ml") == 2

        r.ltrim("ml", 1, 3)

        assert r.lrange("ml", 0, 500) == ['5']

        r.lset("ml", 0, 'nifty!')
        assert r.lrange("ml", 0, 500) == ['nifty!']
        assert r.lindex("ml", 0) == 'nifty!'

        r.lrem("ml", 'nifty!')

        assert r.lrange("ml", 0, 500) == []

        r.rpush("ml", 'yes!')
        r.rpush("ml", 'no!')
        assert r.lrange("ml", 0, 500) == ["yes!", "no!"]

        assert r.lpop("ml") == 'yes!'
        assert r.rpop("ml") == 'no!'

        t = time.time()
        r.blpop(['ml'], 3)
        delt = time.time() - t
        assert 2.5 < delt < 10

        r.rpush("ml", 'yes!')
        r.rpush("ml", 'no!')
        assert r.blpop(['ml'], 3) == ('ml', 'yes!')
        assert r.blpop(['ml'], 3) == ('ml', 'no!')

        r.rpush("ml", 'yes!')
        r.rpush("ml", 'no!')
        r.rpush("ml2", 'one!')
        r.rpush("ml2", 'two!')

        r.rpoplpush("ml", "ml2")
        assert r.lrange("ml", 0, 500) == ['yes!']
        assert r.lrange("ml2", 0, 500) == ['no!', 'one!', 'two!']

    def test_sets(self):
        r = self.client
        r.sadd("s1", "one")
        r.sadd("s1", "two")
        r.sadd("s1", "three")

        assert r.smembers("s1") == set(["one", "two", "three"])

        r.srem("s1", "three")

        assert r.smembers("s1") == set(["one", "two"])

        r.smove("s1", "s2", "one")
        assert r.spop("s2") == 'one'
        assert r.scard("s1") == 1

        assert r.sismember("s1", "two") == True
        assert r.sismember("s1", "one") == False

        r.sadd("s1", "four")
        r.sadd("s2", "four")

        assert r.sinter(["s1", "s2"]) == set(['four'])
        r.sinterstore("s3", ["s1", "s2"])
        assert r.smembers('s3') == r.sinter(["s1", "s2"])
        assert r.sunion(["s1", "s2"]) == set(['two', 'four'])
        r.sunionstore("s3", ["s1", "s2"])
        assert r.smembers('s3') == r.sunion(["s1", "s2"])

        assert r.srandmember("s3") in r.smembers("s3")

    def test_zsets(self):
        r = self.client
        r.zadd("z1", 10, "ten")
        r.zadd("z1", 1, "one")
        r.zadd("z1", 2, "two")
        r.zadd("z1", 0, "zero")


        assert r.zrange("z1", 0, -1) == ['zero', 'one', 'two', 'ten']
        r.zrem("z1", "two")
        assert r.zrange("z1", 0, -1) == ['zero', 'one', 'ten']
        assert r.zrevrange("z1", 0, -1) == list(reversed(r.zrange("z1", 0, -1)))

        r.zrem("z1", (r.zrange("z1", 0, 0))[0]) # remove 'zero'?
        assert r.zrange("z1", 0, -1) == ['one', 'ten']
        assert r.zcard("z1") == 2

        assert r.zscore("z1", "one") == 1.0

        r.zincrby("z1", -2, "one")

        assert r.zscore("z1", "one") == -1.0

        r.zadd("z1", 2, "two")
        r.zadd("z1", 3, "three")
        assert r.zrangebyscore("z1", -5, 15) == ['one', 'two', 'three', 'ten']
        assert r.zrangebyscore("z1", 2, 15) == ['two', 'three', 'ten']
        assert r.zrangebyscore("z1", 2, 15, 1, 50) == ['three', 'ten']
        assert r.zrangebyscore("z1", 2, 15, 1, 1) == ['three']
        assert r.zrangebyscore("z1", 2, 15, 1, 50, with_scores=True) == [('three', 3.0), ('ten', 10.0)]

        assert r.zcount("z1", 2, 15) == 3

        assert r.zremrangebyrank('z1', 1, 1)
        assert r.zrangebyscore("z1", -5, 15) == ['one', 'three', 'ten']
        assert r.zremrangebyscore('z1', 2, 4)
        assert r.zrangebyscore("z1", -5, 15) == ['one', 'ten']

    def test_hashes(self):
        r = self.client
        r.hset("h1", "bahbah", "black sheep")
        assert r.hget("h1", "bahbah") == "black sheep"

        r.hmset("h1", {"foo" : "bar", "baz" : "bosh"})
        assert r.hmget("h1", ["foo", "bahbah", "baz"]) == {'foo' : 'bar', 'baz' : 'bosh', 'bahbah' : 'black sheep'}

        assert r.hincrby("h1", "count", 3) == 3
        assert r.hincrby("h1", "count", 4) == 7

        assert r.hmget("h1", ["foo", "count"]) == {'foo' : 'bar', 'count' : '7'}

        assert r.hexists("h1", "bahbah") == True
        assert r.hexists("h1", "nope") == False

        r.hdel("h1", "bahbah")
        assert r.hexists("h1", "bahbah") == False
        assert r.hlen("h1") == 3

        assert r.hkeys("h1") == set(['foo', 'baz', 'count'])
        assert set(r.hvals("h1")) == set(['bar', 'bosh', '7'])
        assert r.hgetall("h1") == {'foo' : 'bar', 'baz' : 'bosh', 'count' : '7'}

    def test_transactions(self):
        r = self.client
        r.set('t2', 1)
        # Try a successful transaction.
        with r.transaction() as t:
            t.incr('t1')
            t.incr('t2')
        assert r.get('t1') == '1'
        assert r.get('t2') == '2'

        # Try a failing transaction.
        try:
            with r.transaction() as t:
                t.incr('t1')
                t.icnr('t2') # typo!
        except AttributeError:
            # t1 should not get incremented since the transaction body
            # raised an exception.
            assert r.get('t1') == '1'
            assert t.aborted
        else:
            assert 0, "DID NOT RAISE"

        # Try watching keys in a transaction.
        r.set('w1', 'watch me')
        transaction = r.transaction(watch=['w1'])
        w1 = r.get('w1')
        with transaction:
            transaction.set('w2', w1 + ' if you can!')
        assert transaction.value == ['OK']
        assert r.get('w2') == 'watch me if you can!'

        # Try changing watched keys.
        r.set('w1', 'watch me')
        transaction = r.transaction(watch=['w1'])
        r.set('w1', 'changed!')
        w1 = r.get('w1')
        try:
            with transaction:
                transaction.set('w2', w1 + ' if you can!')
        except RedisTransactionError:
            assert transaction.aborted
        else:
            assert 0, "DID NOT RAISE"
