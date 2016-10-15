from django.core.management.base import BaseCommand, CommandError
from mfctracker.models import Branch

class Command(BaseCommand):
    help = 'Adds new branch'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', required=True, help='branch name')
        parser.add_argument('-p', '--path', required=True, help='branch path')

    def handle(self, *args, **options):
        name = options['name']
        path = options['path'].strip('/')
        path = '/' + path
        branch = Branch.create(name, path)
        try:
            branch.save()
            self.stdout.write(self.style.SUCCESS('Branch %s created with path %s' %  (name, path)))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Error adding new branch: %s' % e.message))

