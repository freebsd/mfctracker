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

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from mfctracker.models import Branch

class Command(BaseCommand):
    help = 'Adds new branch'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', required=True, help='branch name')
        parser.add_argument('-p', '--path', required=True, help='branch path')
        parser.add_argument('-b', '--branch-point', type=int, default=None, help='branch point revision')
        parser.add_argument('-t', '--trunk', dest='trunk', action='store_true', help='flag this branch as trunk')

    def handle(self, *args, **options):
        branchpoint = options['branch_point']
        name = options['name']
        path = options['path'].strip('/')
        path = '/' + path
        trunk = options['trunk']
        if trunk:
            try:
                trunk_branch = Branch.trunk()
                if trunk_branch.is_trunk:
                    raise CommandError('Trunk branch already exists: {}'.format(trunk_branch.name))
            except ObjectDoesNotExist:
                pass

        if not branchpoint:
            try:
                r = svn.remote.RemoteClient(settings.SVN_BASE_URL)
                entries = list(r.log_default(rel_filepath=path, limit=1, revision_from=0, revision_to='HEAD', stop_on_copy=True))
                if len(entries) != 1:
                    raise CommandError('Invalid number of entries ({}) returned for branch point query'.format(len(entries)))
                branchpoint = entries[0].revision
            except Exception as e:
                raise CommandError('Failed to get branch point for branch: {}'.format(e.message))

        branch = Branch.create(name, path)
        branch.branch_revision = branchpoint
        branch.is_trunk = trunk
        branch.last_revision = branchpoint - 1

        try:
            branch.save()
            self.stdout.write(self.style.SUCCESS('Branch {} created with path {}, branch point: {}'.format(name, path, branchpoint)))
        except Exception as e:
            raise CommandError('Error adding new branch: {}'.format(e.message))
