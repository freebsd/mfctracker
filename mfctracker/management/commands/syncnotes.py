import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

from mfctracker.models import Commit, CommitNote

class Command(BaseCommand):
    help = 'Create users for every known committer'

    def handle(self, *args, **options):
        x_mfc_commits = Commit.objects.filter(msg__icontains='x-mfc-')
        for commit in x_mfc_commits:
            lines = commit.msg.split('\n')
            notes = []
            for line in lines:
                if re.match('^\s*x-mfc[^:]*:', line, flags=re.IGNORECASE):
                    notes.append(line)
            if len(notes) == 0:
                continue
            note_text = "\n".join(notes)
            user = User.objects.get(username=commit.author)
            # Do not add auto note if there is already one
            if user.notes.filter(commit=commit).count() > 0:
                continue
            commit_note = CommitNote.create(commit, user, note_text)
            commit_note.save()

