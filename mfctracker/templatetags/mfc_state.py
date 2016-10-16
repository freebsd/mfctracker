import urllib

from django import template

register = template.Library()

@register.filter
def mfc_state(commit, branch):
    if commit.merged_to.filter(pk=branch.pk).exists():
        return "done"

    # TODO: check mfc_after field here

    return "no"
