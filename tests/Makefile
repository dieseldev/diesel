WV=./wvtestrun ./wvtest.py
default: test-basic

test-basic:
	$(WV) diesel_test_basic_*.py

test-short:
	$(WV) `ls diesel_test_basic_*.py | grep -v _fork`
