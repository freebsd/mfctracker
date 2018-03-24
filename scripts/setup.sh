psql -c "drop database if exists mfctracker;" template1
psql -c "create database mfctracker;" template1
python manage.py migrate
python manage.py addbranch --trunk --name HEAD --path /head --branch-point 256281
python manage.py addbranch --name STABLE-10 --path /stable/10
python manage.py addbranch --name STABLE-11 --path /stable/11

