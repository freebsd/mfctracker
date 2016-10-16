import urllib
from datetime import date

from django import template

register = template.Library()

@register.filter
def mfc_state(commit, branch):
    if commit.merged_to.filter(pk=branch.pk).exists():
        return "done"

    if commit.mfc_after is None:
        return "no"

    if commit.mfc_after <= date.today():
        return "ready"

    return "wait"
