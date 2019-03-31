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
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

from mfctracker.models import Commit, UserProfile

class Command(BaseCommand):
    help = 'Create users for every known committer'

    def handle(self, *args, **options):
        committers = set(Commit.objects.values_list('author', flat=True).distinct())
        for committer in committers:
            try:
                user = User.objects.get(username=committer)
                if user.profile is None:
                    profile = UserProfile.objects.create(share_token=get_random_string(length=8), user=user)
                    profile.save()
            except User.DoesNotExist:
                email = '{}@{}'.format(committer, settings.SVN_EMAIL_DOMAIN)
                password = get_random_string(length=32)
                self.stdout.write('User does not exist, adding: {}'.format(committer, password))
                User.objects.create_user(committer, email, password)
