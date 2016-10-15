from django.core.management.base import BaseCommand, CommandError
from mfctracker.models import Branch

class Command(BaseCommand):
    help = 'List all branches'

    def handle(self, *args, **options):
        self.stdout.write('{:<12} {}'.format('Name', 'Path'))
        self.stdout.write('-' * 16)
        for branch in Branch.objects.all():
            self.stdout.write('{:<12} {}'.format(branch.name, branch.path))
