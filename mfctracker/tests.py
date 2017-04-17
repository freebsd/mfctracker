from datetime import datetime
import pytest

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from .utils import get_mfc_requirements
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
