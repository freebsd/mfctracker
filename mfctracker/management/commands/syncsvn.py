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
import svn.remote
import json
import parsedatetime
import time
import re
from datetime import date, datetime, timedelta
from collections import deque

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

from mfctracker.models import Commit, Branch, Change
from mfctracker.utils import get_mfc_requirements, mergeinfo_ranges_to_set, parse_mergeinfo_prop

class Command(BaseCommand):
    help = 'Import new commits from SVN repo'

    def handle(self, *args, **options):
        r = svn.remote.RemoteClient(settings.SVN_BASE_URL)
        b = Branch.objects.get(name='STABLE-12')
        props = r.properties(b.path)
        mergeinfo_prop = props.get('svn:mergeinfo', None)
        mergeinfo = parse_mergeinfo_prop(props['svn:mergeinfo'])
        update_revisions = mergeinfo_ranges_to_set(mergeinfo['/head'])
        for commit in Commit.objects.filter(svn_revision__in=update_revisions):
            print (commit.svn_revision)
            commit.merged_to.add(b)
            commit.save()

        return None
