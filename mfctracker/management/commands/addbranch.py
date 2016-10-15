import svn.remote

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from mfctracker.models import Branch

class Command(BaseCommand):
    help = 'Adds new branch'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', required=True, help='branch name')
        parser.add_argument('-p', '--path', required=True, help='branch path')
        parser.add_argument('-b', '--branch-point', type=int, default=None, help='branch point revision')

    def handle(self, *args, **options):
        branchpoint = options['branch_point']
        name = options['name']
        path = options['path'].strip('/')
        path = '/' + path
        if not branchpoint:
            try:
                r = svn.remote.RemoteClient(settings.SVN_BASE_URL)
                entries = list(r.log_default(rel_filepath=path, limit=1, revision_from=0, revision_to='HEAD', stop_on_copy=True))
                if len(entries) != 1:
                    raise ValueError('Invalid number of entries ({}) returned for branch point query'.format(len(entries)))
                branchpoint = entries[0].revision
            except Exception as e:
                self.stdout.write(self.style.ERROR('Failed to get branch point for branch: %s' % e.message))

        branch = Branch.create(name, path)
        branch.branch_revision = branchpoint
        branch.last_revision = branchpoint - 1

        try:
            branch.save()
            self.stdout.write(self.style.SUCCESS('Branch {} created with path {}, branch point: {}'.format(name, path, branchpoint)))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Error adding new branch: %s' % e.message))
