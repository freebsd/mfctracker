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
