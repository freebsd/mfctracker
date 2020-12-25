#  Copyright (c) 2016-2019 Oleksandr Tymoshenko <gonzo@bluezbox.com>
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#  SUCH DAMAGE.
from git import Repo
from git.exc import GitCommandError
import json
import parsedatetime
import time
import re
from datetime import date, datetime, timezone
from collections import deque

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max
from django.utils.crypto import get_random_string

from mfctracker.models import Commit, Branch, Change
from mfctracker.utils import get_mfc_requirements, get_cherry_picked_commits

class Command(BaseCommand):
    help = 'Import new commits from SVN repo'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--start-revision', type=str,
            default='', help='revision to start import from')
        parser.add_argument('-b', '--branch', type=str,
            default=None, help='name of the branch')
        parser.add_argument('-l', '--limit', type=int,
            default=None, help='maximum number of commits passsed to git log command')

    def handle(self, *args, **options):
        start_revision = options['start_revision']
        branch = options['branch']
        limit = options['limit']
        committers = {}

        if branch is None:
            branches = list(Branch.objects.all().order_by('-is_trunk'))
        else:
            branches = [ Branch.objects.get(name=branch) ]

        repo = Repo(settings.GIT_REPO)

        for b in branches:
            commits = b.commits.all()
            counter = commits.aggregate(Max('commit_counter'))['commit_counter__max']
            if counter is None:
                counter = 1
            else:
                counter = counter + 1
            branch_ref = 'remotes/origin/' + b.path
            if not start_revision:
                revision = b.last_commit
            else:
                revision = start_revision
            self.stdout.write('Importing commits for branch %s, starting with %s (last revision %s)' % (b.name, revision, b.last_commit))
            log_entries = repo.iter_commits(branch_ref)
            branch_commits = 0
            last_commit = ''
            mfc_with = {}
            mfced = set()
            # track back to the last commit

            new_entries = deque([], limit)
            for entry in log_entries:
                if entry.hexsha == b.last_commit:
                    break
                new_entries.appendleft(entry)

            for entry in new_entries:
                committed_date = datetime.fromtimestamp(entry.committed_date, tz=timezone.utc)
                revision = None
                try:
                    notes = repo.git.notes('show', entry.hexsha)
                    m = re.match('.*revision=(\d+).*', notes)
                    if m:
                        revision = m.group(1)
                except GitCommandError:
                    pass
                author = entry.committer.email
                if author.find('@') >= 0:
                    author = author.split("@")[0]

                commit = Commit.create(entry.hexsha, author, committed_date, entry.message)
                commit.branch = b
                commit.svn_revision = revision
                commit.mfc_after = self.parse_mfc_entry(entry.message, committed_date);
                commit.commit_counter = counter
                counter += 1
                commit.save()

                if b.is_trunk:
                    changes = []
                    for path in entry.stats.files:
                        change = Change(path=path, commit=commit)
                        changes.append(change)
                    Change.objects.bulk_create(changes)

                branch_commits += 1
                last_commit = entry.hexsha
                if b.is_trunk:
                    deps = get_mfc_requirements(entry.message)
                    if len(deps) > 0:
                        mfc_with[entry.hexsha] = deps
                else:
                    picked = get_cherry_picked_commits(entry.message)
                    mfced = mfced.union(picked)

                if not entry.author in committers:
                    try:
                        user = User.objects.get(username=entry.author)
                    except User.DoesNotExist:
                        email = '{}@{}'.format(entry.author, settings.SVN_EMAIL_DOMAIN)
                        password = get_random_string(length=32)
                        user = User.objects.create_user(entry.author, email, password)
                    committers[entry.author] = user

            for sha in mfced:
                try:
                    commit = Commit.objects.get(sha=sha)
                    commit.merged_to.add(b)
                    commit.save()
                except Commit.DoesNotExist:
                    self.stdout.write(self.style.ERROR('{} merked as merged but does not exist'.format(sha)))

            for sha, deps in mfc_with.items():
                commit = Commit.objects.get(sha=sha)
                for dep in deps:
                    try:
                        rev = int(dep)
                        dep_commit = Commit.objects.get(svn_revision=rev)
                        commit.mfc_with.add(dep_commit)
                        continue
                    except Commit.DoesNotExist:
                        self.stdout.write(self.style.ERROR('{} has r{} in X-MFC-With list but it does not exist'.format(sha, dep)))
                        continue
                    except ValueError:
                        pass

                    dep_commits = Commit.objects.filter(sha__startswith=dep)
                    if dep_commits.count() == 0:
                        self.stdout.write(self.style.ERROR('{} has {} in X-MFC-With list but it does not exist'.format(sha, dep)))
                    elif dep_commits.count() > 1:
                        self.stdout.write(self.style.ERROR('{} has {} in X-MFC-With list but it is ambiguous'.format(sha, dep)))
                    else:
                        commit.mfc_with.add(dep_commits[0])

            if branch_commits:
                self.stdout.write('Imported {} commits, last revision is {}'.format(branch_commits, last_commit))
                b.last_commit = last_commit
            else:
                self.stdout.write('No commits to import')

            b.save()

    def parse_mfc_entry(self, msg, commit_date):
        lines = msg.split('\n')
        for line in lines:
            if re.match('^\s*mfc\s+after\s*:', line, flags=re.IGNORECASE):
                calendar = parsedatetime.Calendar()
                mfc_after_st, parsed = calendar.parse(line, commit_date)
                if parsed:
                    mfc_after = date.fromtimestamp(time.mktime(mfc_after_st))
                    return mfc_after
                else:
                    self.stdout.write(self.style.ERROR(u'Failed to parse MFC line: \'' + line + u'\''))

        return None
