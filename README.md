# MFCTracker

## Overview

This project is a web tool for tracking MFC (merges to stable branches) state of Subversion commits. For now it's supposed to be used by FreeBSD developers but can easily be adopted to any Sunbversion repository with organization simmilar to FreeBSD's one.

## Stack

MFCTracker stack consists of Django, Python2, PostgreSQL. Production deployment is built using Nginx, uWSGI, and supervisord. The stack is generally OS-agnostic but automation scripts assume FreeBSD. Python2 was chosen because uWSGI on FreeBSD is built with Python2 support and I didn't want to generate custom packages for this project. 

## Development VM

Development VM can be created using vagrant tool. Run `vagrant up` to start VM, then `vagrant ssh` to log in. The project sources are located in `/app` directory which is mounted over NFS from host machine. To populate database run `sh scripts/setup.sh` in that directory followed by `python manage.py importcommits` command.

To start web app run `python manage.py runserver 0:8000`, web UI should be available at http://localhost:8000

## Server Setup

MFCTracker uses Ansible for initial setup and deployment automation. To setup a server install vanilla FreeBSD 11 and run following commands:

```sh
sudo pkg install git ansible
git clone https://github.com/gonzoua/mfctracker.git
ansible-playbook -i localhost, mfctracker/playbooks/setup.yml
```

Setup playbook will create mfctracker user, prepare directory layout, install all production requirements, PostgreSQL, creates database and user. After it's finished open `/usr/local/etc/mfctracker.env`, change value of the `SECRET_KEY` and optionally change mailer URL and LDAP config. Machine is ready for intial deployment.

Keep clone of mfctracker repo to get latest versions of playbooks before performing update.

## Initial Deployment

For initial deployment run following command:
```sh
ansible-playbook -i localhost, mfctracker/playbooks/deploy.yml
```

Once it's finished you should have one directory name like `20170425-221356-master-ebab7a0` in `/usr/local/mfctracker/`, and symlink `latest` pointing to that directory. Now you have working mfctracker setup but without any useful data.

Now we need to create branches and import all commits. To create branches run
```sh
mfctracker-manage addbranch --trunk --name HEAD --path /head --branch-point 256281 # this is STABLE-10 branchpoint
mfctracker-manage addbranch --name STABLE-10 --path /stable/10
mfctracker-manage addbranch --name STABLE-11 --path /stable/11
```

To import commits run (this command may take some time to finish)
```sh
/usr/local/mfctracker/latest/app/scripts/sync.sh
```

Once it's done mfctracker will sync commits every 7 minutes (there is cron job created for user `mfctracker` to do this)


### Update Deployment

Get latest version of playbooks by syncing to the latest version of MFCTracker repo (see step _Server Setup_):
```
cd mfctracker
git pull
```

Run deployment playbook
```sh
ansible-playbook -i localhost, playbooks/deploy.yml
```
It will perform exactly the same action as for initial performance, the only difference you don't have to edit anything. Once this step is done you should have latest version of MFCTracker up and running.
