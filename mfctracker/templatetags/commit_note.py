import urllib
from datetime import date

from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.filter
def commit_note(commit, user):
    if user.is_anonymous():
        return None

    try:
        note = commit.notes.get(user=user)
        return note
    except ObjectDoesNotExist:
        return None
