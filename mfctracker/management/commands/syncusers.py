from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

from mfctracker.models import Commit

class Command(BaseCommand):
    help = 'Create users for every known committer'

    def handle(self, *args, **options):
        committers = set(Commit.objects.values_list('author', flat=True).distinct())
        for committer in committers:
            try:
                user = User.objects.get(username=committer)
            except User.DoesNotExist:
                email = '{}@freebsd.org'.format(committer)
                password = get_random_string(length=32)
                self.stdout.write('User does not exist, adding: {}'.format(committer, password))
                User.objects.create_user(committer, email, password)
