from django.core.management.base import BaseCommand, CommandError
from mfctracker.models import Branch

class Command(BaseCommand):
    help = 'Delete branch by name'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', required=True, help='branch name')

    def handle(self, *args, **options):
        name = options['name']

        try:
            branch = Branch.objects.get(name=name)
            branch.delete()
            self.stdout.write(self.style.SUCCESS('Branch %s was deleted' %  (name)))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Error deleteing branch %s: %s' % (name, e.message)))
