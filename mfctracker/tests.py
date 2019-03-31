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
from datetime import datetime
import pytest

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from .utils import get_mfc_requirements, parse_mergeinfo_prop, mergeinfo_ranges_to_set
from .models import Commit, CommitNote

@pytest.fixture()
def valid_user(request):
    user = User.objects.create_user(username='gonzo', password='password', email='gonzo@freebsd.org')
    return user

@pytest.fixture()
def commit(request, valid_user):
    commit = Commit.create(1024, valid_user.username, datetime.now(), 'commit message')
    commit.save()
    return commit

@pytest.fixture()
def note(request, valid_user, commit):
    note = CommitNote.create(commit, valid_user, 'text')
    note.save()
    return note

@pytest.fixture()
def loggedin_client(request, valid_user):
    client = Client()
    if not client.login(username='gonzo', password='password'):
        raise AssertionError('Login failed')
    return client

class TestUtils(TestCase):

    def test_mfc_requirements(self):
        requirements = get_mfc_requirements('x-mfc-with: r1, r2,r3 , 4,5')
        self.assertEqual(requirements, set(xrange(1,6)))

    def test_mergeinfo_parser(self):
        mergeinfo = parse_mergeinfo_prop('/repo:1-3,4*,5')
        revisions = mergeinfo_ranges_to_set(mergeinfo['/repo'])
        self.assertEqual(revisions, set(xrange(1,6)))

@pytest.mark.django_db()
class TestComments():

    def test_not_authorized_post(self):
        client = Client()
        response = client.post(reverse('comment_commit', kwargs={'revision': '1'}))
        assert response.status_code == 403

    def test_not_authorized_delete(self):
        client = Client()
        response = client.delete(reverse('comment_commit', kwargs={'revision': '1'}))
        assert response.status_code == 403

    def test_no_commit_post(self, loggedin_client):
        response = loggedin_client.post(reverse('comment_commit', kwargs={'revision': '1'}))
        assert response.status_code == 404

    def test_no_commit_delete(self, loggedin_client):
        response = loggedin_client.delete(reverse('comment_commit', kwargs={'revision': '1'}))
        assert response.status_code == 404

    def test_no_commit_delete(self, loggedin_client):
        response = loggedin_client.delete(reverse('comment_commit', kwargs={'revision': '1'}))
        assert response.status_code == 404

    def test_create_comment(self, loggedin_client, commit):
        assert commit.notes.count() == 0
        response = loggedin_client.post(reverse('comment_commit', kwargs={'revision': commit.revision}),
            {'text': 'comment'})
        assert response.status_code == 204
        assert commit.notes.first().text == 'comment'

    def test_update_comment(self, loggedin_client, commit, note):
        assert commit.notes.count() == 1
        assert commit.notes.first().text == note.text
        response = loggedin_client.post(reverse('comment_commit', kwargs={'revision': commit.revision}),
            {'text': 'comment'})
        assert response.status_code == 204
        assert commit.notes.first().text == 'comment'
        assert commit.notes.first().text != note.text

    def test_delete_comment(self, loggedin_client, commit, note):
        assert commit.notes.count() == 1
        response = loggedin_client.delete(reverse('comment_commit', kwargs={'revision': commit.revision}))
        assert response.status_code == 204
        assert commit.notes.count() == 0

    def test_add_do_not_merge(self, loggedin_client, valid_user, commit):
        assert valid_user.profile.do_not_merge.count() == 0
        response = loggedin_client.post(reverse('add_do_not_merge', kwargs={'revision': commit.revision}))
        assert response.status_code == 204
        assert valid_user.profile.do_not_merge.count() == 1

    def test_del_do_not_merge(self, loggedin_client, valid_user, commit):
        valid_user.profile.do_not_merge.add(commit)
        valid_user.profile.save()
        assert valid_user.profile.do_not_merge.count() == 1
        response = loggedin_client.post(reverse('del_do_not_merge', kwargs={'revision': commit.revision}))
        assert response.status_code == 204
        assert valid_user.profile.do_not_merge.count() == 0

    def test_del_do_not_merge_no_commit(self, loggedin_client, valid_user, commit):
        assert valid_user.profile.do_not_merge.count() == 0
        response = loggedin_client.post(reverse('del_do_not_merge', kwargs={'revision': commit.revision}))
        assert response.status_code == 204
        assert valid_user.profile.do_not_merge.count() == 0
