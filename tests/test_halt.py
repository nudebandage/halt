import os
import shutil
import tempfile

import pytest

from halt import insert
from halt import load_column
from halt import load_row
from halt import delete
from halt import update
from halt import objectify
from halt import HaltException

from test_util import *

class TestHalt():

    def setup_class(cls):
        cls.tdir = tempfile.mkdtemp()

    def teardown_class(cls):
        shutil.rmtree(cls.tdir)

    def setup_method(self, func):
        '''create fresh database for each test method'''
        db = os.path.join(self.tdir, func.__name__+'.db')
        try:
            os.remove(db)
        except FileNotFoundError:
            pass
        dbcreate(db)
        self.db = db

    def test_insert(self):
        data = {'Name': 'bob', 'Password': 'password'}
        rowid = insert(self.db, 'Test', data, mash=False, commit=True, con=False)
        assert type(rowid) == int
        assert ([('bob', 'password', None)] == get_all_data(self.db))

    def test_insert_only_mash(self):
        data = {'random': 15}
        insert(self.db, 'Test', data, mash=True, commit=True, con=False)
        assert ([(None, None, '{"random": 15}')] == get_all_data(self.db))

    def test_insert_with_mash_and_columns(self):
        data = {'Name': 'bob', 'random': 15}
        insert(self.db, 'Test', data, mash=True, commit=True, con=False)
        assert ([('bob', None, '{"random": 15}')] == get_all_data(self.db))

    def test_load_column(self):
        data = {'Name': 'bob', 'Password': 'pass', 'random': 15}
        insert(self.db, 'Test', data, mash=True)
        assert 'bob' == load_column(self.db, 'Test', ('Name',))[0][0]
        assert ('bob', 'pass') == load_column(self.db,
                                             'Test', ('Name', 'Password'))[0]

    def test_load_row(self):
        data = {'Name': 'bob', 'Password': 'pass', 'random': 15}
        insert(self.db, 'Test', data, mash=True)
        assert [('bob', 'pass', {'random':15})] == load_row(self.db, 'Test', headers=False)
        should = [{'MashConfig': {'random': 15}, 'Password': 'pass', 'Name': 'bob'}]
        assert should == load_row(self.db, 'Test')

    def test_delete(self):
        data = {'Name': 'bob', 'Password': 'pass', 'random': 15}
        insert(self.db, 'Test', data, mash=True)
        delete(self.db, 'Test', "where Name == 'bob'")
        assert not get_all_data(self.db)

    def test_update_columns(self):
        data = {'Name': 'bob', 'Password': 'pass', 'random': 15}
        insert(self.db, 'Test', data, mash=True)

        new_data = {'Name': 'tom', 'random2': 15}
        update(self.db, 'Test', new_data, mash=False, cond="where Name == 'bob'")
        assert [('tom', 'pass', '{"random": 15}')] == get_all_data(self.db)

    @pytest.mark.here
    def test_update_only_mash(self):
        # First test when NOTHING in the MashConfig column
        data = {'Name': 'bob', 'Password': 'pass'}
        insert(self.db, 'Test', data, mash=False)

        new_data = {'r': 1, 'r2': 2}
        update(self.db, 'Test', new_data, mash=True, cond="where Name == 'bob'")
        results = get_all_data(self.db)
        assert results[0][:2] == ('bob', 'pass')
        dict_cmp({"r": 1, "r2": 2}, objectify(results[0][2]))

        # Now test with something existing in the mashconfig column
        new_data = {'r': 10, 'r3': 30}
        update(self.db, 'Test', new_data, mash=True, cond="where Name == 'bob'")
        results = get_all_data(self.db)
        assert results[0][:2] == ('bob', 'pass')
        dict_cmp({"r": 10, "r2": 2, "r3": 30}, objectify(results[0][2]))

    @pytest.mark.here
    def test_update_with_mash_and_columns(self):
        # First test when NOTHING in the MashConfig column
        data = {'Name': 'bob', 'Password': 'pass'}
        insert(self.db, 'Test', data, mash=False)

        new_data = {'Name': 'tom', 'r': 1, 'r2': 2}
        update(self.db, 'Test', new_data, mash=True, cond="where Name == 'bob'")
        results = get_all_data(self.db)
        assert results[0][:2] == ('tom', 'pass')
        dict_cmp({"r": 1, "r2": 2}, objectify(results[0][2]))

        # Now test with something existing in the mashconfig column
        new_data = {'Name': 'peter', 'r': 10, 'r3': 30}
        update(self.db, 'Test', new_data, mash=True, cond="where Name == 'tom'")
        results = get_all_data(self.db)
        assert results[0][:2] == ('peter', 'pass')
        dict_cmp({"r": 10, "r2": 2, "r3": 30}, objectify(results[0][2]))

