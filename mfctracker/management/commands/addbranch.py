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
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from mfctracker.models import Branch

class Command(BaseCommand):
    help = 'Adds new branch'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', required=True, help='branch name')
        parser.add_argument('-p', '--path', required=True, help='branch path')
        parser.add_argument('-b', '--branch-point', type=str, default=None, help='branch point revision')
        parser.add_argument('-t', '--trunk', dest='trunk', action='store_true', help='flag this branch as trunk')

    def handle(self, *args, **options):
        branchpoint = options['branch_point']
        name = options['name']
        path = options['path'].strip('/')
        trunk = options['trunk']
        trunk_branch = None
        try:
            trunk_branch = Branch.trunk()
        except ObjectDoesNotExist:
            pass

        if trunk and trunk_branch:
            raise CommandError('Trunk branch already exists: {}'.format(trunk_branch.name))

        repo = Repo(settings.GIT_REPO)

        if not branchpoint:
            try:
                branchcommit = repo.merge_base('remotes/origin/' + trunk_branch.path, 'remotes/origin/' + path)
                if len(branchcommit) != 1:
                    raise Exception("merge_base yielded more than one commit")
                branchpoint = branchcommit[0].hexsha
            except Exception as e:
                raise CommandError('Failed to get branch point for branch {}: {}'.format(path, e))

        branch = Branch.create(name, path)
        branch.branch_commit = branchpoint
        branch.is_trunk = trunk
        commit = repo.commit(branchpoint)
        branch.last_commit = commit.parents[0].hexsha
        branch.branch_date = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)

        try:
            branch.save()
            self.stdout.write(self.style.SUCCESS('Branch {} created with path {}, branch point: {}'.format(name, path, branchpoint)))
        except Exception as e:
            raise CommandError('Error adding new branch: {}'.format(e.message))
