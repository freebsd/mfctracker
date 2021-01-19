psql -c "drop database if exists mfctracker;" template1
psql -c "create database mfctracker;" template1
python manage.py migrate
python manage.py addbranch --trunk --name HEAD --path main --branch-point 3ade9440198973efee3e6ae9636e1b147c72140b
python manage.py addbranch --name STABLE-12 --path stable/12

# Further import:
# git clone --config remote.origin.fetch='+refs/notes/*:refs/notes/*' https://git.freebsd.org/src.git ~/src
# python manage.py importcommits --branch HEAD
# python manage.py importcommits --branch STABLE-12
# python manage.py syncsvn
