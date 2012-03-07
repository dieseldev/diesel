import uuid

import diesel
from diesel.protocols.mongodb import *

from diesel.util.queue import Fanout

class MongoDbHarness(object):
    def setup(self):
        self.client = MongoClient()
        self.client.drop_database('dieseltest')
        self.db = self.client.dieseltest

    def filt(self, d):
        del d['_id']
        return d

class TestMongoDB(MongoDbHarness):
    def test_empty(self):
        assert self.db.cempty.find().all() == []
        assert self.db.cempty.find().one() == None

    # INSERT
    def test_insert(self):
        d = {'one' : 'two'}
        assert self.db.ionly.insert({'one' : 'two'})['err'] == None

    def test_insert_many(self):
        d1 = {'one' : 'two'}
        d2 = {'three' : 'four'}
        inp = [d1, d2]
        inp.sort()
        assert self.db.imult.insert(inp)['err'] == None
        all = self.db.imult.find().all()
        map(self.filt, all)
        all.sort()
        assert all == inp

    # UPDATE
    def test_update_basic(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up1.insert(d)['err'] == None
        assert self.filt(self.db.up1.find().one()) == d
        assert self.db.up1.update({'one' : 'two'},
                {'three' : 'five'})['err'] == None
        new = self.filt(self.db.up1.find().one())
        assert 'one' not in new
        assert new['three'] == 'five'

    def test_update_set(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up2.insert(d)['err'] == None
        assert self.filt(self.db.up2.find().one()) == d
        assert self.db.up2.update({'one' : 'two'},
                {'$set' : {'three' : 'five'}})['err'] == None
        new = self.filt(self.db.up2.find().one())
        assert new['one'] == 'two'
        assert new['three'] == 'five'

    def test_update_not_multi(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up3.insert(d)['err'] == None
        assert self.db.up3.insert(d)['err'] == None
        assert self.db.up3.update({'one' : 'two'},
                {'$set' : {'three' : 'five'}})['err'] == None

        threes = set()
        for r in self.db.up3.find():
            threes.add(r['three'])
        assert threes == set(['four', 'five'])

    def test_update_multi(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up4.insert(d)['err'] == None
        assert self.db.up4.insert(d)['err'] == None
        assert self.db.up4.update({'one' : 'two'},
                {'$set' : {'three' : 'five'}},
                multi=True)['err'] == None

        threes = set()
        for r in self.db.up4.find():
            threes.add(r['three'])
        assert threes == set(['five'])

    def test_update_miss(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up5.insert(d)['err'] == None
        snap = self.db.up5.find().all()
        assert self.db.up5.update({'one' : 'nottwo'},
                {'$set' : {'three' : 'five'}},
                multi=True)['err'] == None

        assert snap == self.db.up5.find().all()

    def test_update_all(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up6.insert(d)['err'] == None
        assert self.db.up6.insert(d)['err'] == None
        assert self.db.up6.update({},
                {'$set' : {'three' : 'five'}},
                multi=True)['err'] == None

        for r in self.db.up6.find().all():
            assert r['three'] == 'five'

    def test_update_upsert(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.up7.insert(d)['err'] == None
        assert self.db.up7.insert(d)['err'] == None
        assert len(self.db.up7.find().all()) == 2
        assert self.db.up7.update({'not' : 'there'},
                {'this is' : 'good'}, upsert=True)['err'] == None

        assert len(self.db.up7.find().all()) == 3

    # DELETE
    def test_delete_miss(self):
        d = {'one' : 'two'}
        assert self.db.del1.insert({'one' : 'two'})['err'] == None
        assert len(self.db.del1.find().all()) == 1
        assert self.db.del1.delete({'not' : 'me'})['err'] == None
        assert len(self.db.del1.find().all()) == 1

    def test_delete_target(self):
        d = {'one' : 'two'}
        assert self.db.del2.insert({'one' : 'two'})['err'] == None
        assert self.db.del2.insert({'three' : 'four'})['err'] == None
        assert len(self.db.del2.find().all()) == 2
        assert self.db.del2.delete({'one' : 'two'})['err'] == None
        assert len(self.db.del2.find().all()) == 1

    def test_delete_all(self):
        d = {'one' : 'two'}
        assert self.db.del3.insert({'one' : 'two'})['err'] == None
        assert self.db.del3.insert({'three' : 'four'})['err'] == None
        assert len(self.db.del3.find().all()) == 2
        assert self.db.del3.delete({})['err'] == None
        assert len(self.db.del3.find().all()) == 0

    # QUERY
    def test_query_basic(self):
        d = {'one' : 'two'}
        assert self.db.onerec.insert(d)['err'] == None
        assert map(self.filt, self.db.onerec.find().all()) == [d]
        assert self.filt(self.db.onerec.find().one()) == d

        x = 0
        for r in self.db.onerec.find():
            assert self.filt(r) == d
            x += 1
        assert x == 1

    def test_query_one(self):
        d1 = {'one' : 'two'}
        d2 = {'three' : 'four'}
        inp = [d1, d2]
        assert self.db.q0.insert(inp)['err'] == None
        assert len(self.db.q0.find().all()) == 2
        assert len(self.db.q0.find({'one' : 'two'}).all()) == 1

    def test_query_miss(self):
        d = {'one' : 'two'}
        assert self.db.q1.insert(d)['err'] == None
        assert self.db.q1.find({'one' : 'nope'}).all() == []

    def test_query_subfields(self):
        d = {'one' : 'two', 'three' : 'four'}
        assert self.db.q2.insert(d)['err'] == None
        assert map(self.filt,
                self.db.q2.find({'one' : 'two'}, ['three']).all()) \
                == [{'three' : 'four'}]

    def test_deterministic_order_when_static(self):
        for x in xrange(500):
            self.db.q3.insert({'x' : x})

        snap = self.db.q3.find().all()

        for x in xrange(100):
            assert snap == self.db.q3.find().all()

    def test_skip(self):
        for x in xrange(500):
            self.db.q4.insert({'x' : x})

        snap = self.db.q4.find().all()

        with_skip = self.db.q4.find(skip=250).all()

        assert snap[250:] == with_skip

    def test_limit(self):
        for x in xrange(500):
            self.db.q5.insert({'x' : x})

        snap = self.db.q5.find().all()

        with_skip = self.db.q5.find(limit=150).all()

        assert snap[:150] == with_skip

    def test_skip_limit(self):
        for x in xrange(500):
            self.db.q6.insert({'x' : x})

        snap = self.db.q6.find().all()

        with_skip = self.db.q6.find(skip=300, limit=150).all()

        assert snap[300:300+150] == with_skip

    # CURSOR PROPERTIES
    def test_cursor_count(self):
        for x in xrange(500):
            self.db.c1.insert({'x' : x})

        c = self.db.c1.find()
        assert c.count() == 500
        assert len(c.all()) == 500

        c = self.db.c1.find(skip=100, limit=150)
        assert c.count() == 150
        assert len(c.all()) == 150

    def test_cursor_sort(self):
        for x in xrange(500):
            self.db.c2.insert({'x' : x})

        snap = self.db.c2.find().sort('x', 1).all()

        print snap
        assert map(lambda d: d['x'], snap) == range(500)

        snap = self.db.c2.find().sort('x', -1).all()
        assert map(lambda d: d['x'], snap) == range(499, -1, -1)
