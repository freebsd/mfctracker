#  Copyright (c) 2016-2017 Oleksandr Tymoshenko <gonzo@bluezbox.com>
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
import svn.remote
import json
import parsedatetime
import time
import re
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

from mfctracker.models import Commit, Branch, Change
from mfctracker.utils import get_mfc_requirements, mergeinfo_ranges_to_set, parse_mergeinfo_prop

class Command(BaseCommand):
    help = 'Import new commits from SVN repo'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--start-revision', type=int,
            default=-1, help='revision to start import from')
        parser.add_argument('-b', '--branch', type=str,
            default=None, help='name of the branch')
        parser.add_argument('-l', '--limit', type=int,
            default=None, help='maximum number of commits passsed to svn log command')

    def handle(self, *args, **options):
        start_revision = options['start_revision']
        branch = options['branch']
        limit = options['limit']
        committers = {}

        if branch is None:
            branches = list(Branch.objects.all().order_by('-is_trunk'))
        else:
            branches = [ Branch.objects.get(name=branch) ]

        r = svn.remote.RemoteClient(settings.SVN_BASE_URL)

        for b in branches:
            branch_path = b.path
            branch_path = branch_path
            if start_revision < 0:
                revision = b.last_revision
            else:
                revision = start_revision
            # Do not go behind first commit to the branch
            revision = max(revision, b.branch_revision)
            self.stdout.write('Importing commits for branch %s, starting with r%d (last revision r%d)' % (b.name, revision, b.last_revision))
            log_entries = reversed(list(r.log_default(rel_filepath=b.path, revision_from=revision, limit=limit, changelist=True)))
            branch_commits = 0
            last_revision = 0
            mfc_with = {}
            for entry in log_entries:
                # Do not include last_revision in subsequent imports
                if entry.revision <= b.last_revision:
                    continue
                commit = Commit.create(entry.revision, entry.author, entry.date, entry.msg)
                commit.branch = b
                commit.mfc_after = self.parse_mfc_entry(entry.msg, entry.date)
                commit.save()
                for c in entry.changelist:
                    op = c[0]
                    path = c[1]
                    if not path.startswith(branch_path):
                        continue
                    change = Change.create(commit, op, path)
                    change.save()
                branch_commits += 1
                last_revision = max(last_revision, entry.revision)
                if b.is_trunk:
                    deps = get_mfc_requirements(entry.msg)
                    if len(deps) > 0:
                        mfc_with[entry.revision] = deps

                if not committers.has_key(entry.author):
                    try:
                        user = User.objects.get(username=entry.author)
                    except User.DoesNotExist:
                        email = '{}@{}'.format(entry.author, settings.SVN_EMAIL_DOMAIN)
                        password = get_random_string(length=32)
                        user = User.objects.create_user(entry.author, email, password)
                    committers[entry.author] = user

            for revision, deps in mfc_with.iteritems():
                commit = Commit.objects.get(revision=revision)
                for dep in deps:
                    try:
                        dep_commit = Commit.objects.get(revision=dep)
                        commit.mfc_with.add(dep_commit)
                    except Commit.DoesNotExist:
                        self.stdout.write(self.style.ERROR('r{} has r{} in X-MFC-With list but it does not exist'.format(entry.revision, revision)))

            if branch_commits:
                self.stdout.write('Imported {} commits, last revision is {}'.format(branch_commits, last_revision))
                b.last_revision = last_revision
            else:
                self.stdout.write('No commits to import')

            props = r.properties(b.path)
            mergeinfo_prop = props.get('svn:mergeinfo', None)
            mergeinfo = {}
            if mergeinfo_prop is not None:
                mergeinfo = parse_mergeinfo_prop(props['svn:mergeinfo'])
            b.mergeinfo = mergeinfo
            b.save()

        # Sync mergeinfo and commit records
        known_pathes = list(Branch.objects.values_list('path', flat=True)) 
        for b in branches:
            old_merged_revisions = list(b.merges.values_list('revision', flat=True))
            new_merged_revisions = set()
            for path in known_pathes:
                if path == b.path:
                    continue
                if not path in b.mergeinfo.keys():
                    continue
                new_merged_revisions |= mergeinfo_ranges_to_set(b.mergeinfo[path])
            update_revisions = new_merged_revisions.difference(old_merged_revisions)
            new_merged_commits = 0
            for commit in Commit.objects.filter(revision__in=update_revisions):
                commit.merged_to.add(b)
                commit.save()
                new_merged_commits += 1
            self.stdout.write('{} commits marked as merged to {}'.format(new_merged_commits, b.name))

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
