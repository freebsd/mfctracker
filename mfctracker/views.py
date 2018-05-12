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
from datetime import date
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST, require_http_methods

from .models import Branch, Commit, CommitNote

def svn_range_to_arg(start, end):
    if start == end:
        return '-c r{}'.format(start)
    else:
        return '-r {}:{}'.format(start - 1, end)

def parse_extended_filters(trunk_path, filters):
    result = None
    for s in filters.split('\n'):
        s = s.strip()
        if not s:
            continue
        if not s.startswith('/'):
            s = '/' + s
        path = trunk_path + s
        q = Q(changes__path__startswith=path)
        if result is None:
            result = q
        else:
            result = result | q
    return result

def parse_single_filter(trunk_path, s):
    committer = ''
    path = ''
    committer_q = None
    path_q = None

    m = re.match('^r?(\d+)(?:-r?(\d+))?$', s)
    if m:
        rev_from = m.group(1)
        rev_to = m.group(2)
        if rev_to is None:
            q = Q(revision=rev_from)
        else:
            q = Q(revision__range=[rev_from, rev_to])
        return q

    if s.find('@') >= 0:
        committer, path = s.split('@', 1)
    else:
        committer = s

    if committer:
        committer_q = Q(author=committer)

    if path:
        if not path.startswith('/'):
            path = '/' + path
        path = trunk_path + path
        path_q = Q(changes__path__startswith=path)
    if path_q and committer_q:
        q = path_q & committer_q
    elif path_q:
        q = path_q
    elif committer_q:
        q = committer_q
    return q

def parse_filters(trunk_path, filters):
    result = None
    pattern = re.compile("[\s,]+")
    for s in pattern.split(filters):
        s = s.strip()
        if not s:
            continue
        q = parse_single_filter(trunk_path, s)
        if result is None:
            result = q
        else:
            result = result | q

    return result

def svn_revisions_arg(revisions):
    args = []

    if len(revisions) == 0:
        return args

    range_start = revisions[0]
    range_end = revisions[0]

    i = 1
    while i < len(revisions):
        if revisions[i] - 1 == range_end:
            range_end = revisions[i]
        else:
            args.append(svn_range_to_arg(range_start, range_end))
            range_start = range_end = revisions[i]
        i += 1

    args.append(svn_range_to_arg(range_start, range_end))
    return args

def commit_msg_revisions(revisions):
    result = []

    if len(revisions) == 0:
        return result

    range_start = revisions[0]
    range_end = revisions[0]

    i = 1
    while i < len(revisions):
        if revisions[i] - 1 == range_end:
            range_end = revisions[i]
        else:
            if range_start == range_end:
                result.append('r{}'.format(range_start))
            else:
                result.append('r{}-r{}'.format(range_start, range_end))
            range_start = range_end = revisions[i]
        i += 1

    if range_start == range_end:
        result.append('r{}'.format(range_start))
    else:
        result.append('r{}-r{}'.format(range_start, range_end))
    return ', '.join(result)

def parse_x_mfc_with_alerts(commits, current_branch):
    alerts = {}
    revisions = [commit.revision for commit in commits]
    for commit in commits:
        # Remove ^MFC.*after:.*$
        msg = commit.msg
        mfc_with = set(commit.mfc_with.all().values_list('revision', flat=True))
        merged = set(current_branch.merges.filter(revision__in=mfc_with).values_list('revision', flat=True))
        missing = mfc_with - set(revisions) - merged
        if len(missing) > 0:
            missing_list = ', '.join([str(x) for x in missing])
            plural = 'commits are' if len(missing) > 1 else 'commit is'
            alerts[commit.revision] = 'Following {} marked as X-MFC-With by revision {}: {}'.format(plural, commit.revision, missing_list)
    return alerts

def mfc_commit_message(revisions, user, summarized=False):
    commits = Commit.objects.filter(revision__in=revisions).order_by("revision")
    commit_msg = None
    if len(revisions) > 0:
        str_revisions = commit_msg_revisions(revisions)
        commit_msg = 'MFC ' + str_revisions
        if len(revisions) == 1:
            if not user.is_anonymous():
                if user.username != commits[0].author:
                    commit_msg += ' by {}'.format(commits[0].author)
            commit_msg += ':'
        commit_msg += '\n'
        mfc_re = re.compile('^MFC\s+after:.*\n?', re.IGNORECASE | re.MULTILINE)
        for commit in commits:
            if summarized:
                commit_msg = commit_msg + '\nr' + str(commit.revision) + ': '
                msg = commit.msg.strip()
                lines = msg.split('\n')
                if len(lines) > 0:
                    # Add summary string 
                    commit_msg = commit_msg + lines[0]
            else:
                if len(revisions) > 1:
                    commit_msg = commit_msg + '\nr' + str(commit.revision)
                    if not user.is_anonymous():
                        if user.username != commit.author:
                            commit_msg += ' by {}'.format(commit.author)
                    commit_msg += ':'
                # Remove ^MFC.*after:.*$
                msg = commit.msg
                msg = mfc_re.sub('', msg)
                commit_msg = commit_msg + '\n' + msg
                commit_msg = commit_msg.strip() + '\n'
    return commit_msg

def _get_basket(request):
    if request.user.is_authenticated():
        basket = list(request.user.profile.mfc_basket)
    else:
        basket = request.session.get('basket', [])
    return basket

def _set_basket(request, basket):
    if request.user.is_authenticated():
        request.user.profile.mfc_basket = basket
        request.user.profile.save()
    else:
        request.session['basket'] = basket

def index(request):
    default_pk = request.session.get('branch', None)
    if default_pk is None:
        branches = Branch.maintenance().order_by('-branch_revision', '-name')
        default_pk = branches[0].pk
    return redirect('branch', branch_id=default_pk)

def setfilter(request, branch_id):
    filters = request.POST.get('filters', None)
    filter_waiting = request.POST.get('filter_waiting', None)
    filter_ready = request.POST.get('filter_ready', None)
    filter_other = request.POST.get('filter_other', None)
    # extended_filters = request.POST.get('extended_filters', None)

    request.session['filters'] = filters
    request.session['filter_waiting'] = filter_waiting is not None
    request.session['filter_ready'] = filter_ready is not None
    request.session['filter_other'] = filter_other is not None
    # request.session['extended_filters'] = extended_filters

    return redirect('branch', branch_id=branch_id)

def branch(request, branch_id):
    current_branch = get_object_or_404(Branch, pk=branch_id)
    request.session['branch'] = branch_id

    template = loader.get_template('mfctracker/index.html')
    trunk = Branch.trunk()
    query = trunk.commits.filter(revision__gt=current_branch.branch_revision)
    if not request.user.is_anonymous():
       query = query.exclude(userprofile=request.user.profile)

    filters = request.session.get('filters', None)
    filter_waiting = request.session.get('filter_waiting', False)
    filter_ready = request.session.get('filter_ready', False)
    filter_other = request.session.get('filter_other', False)
    # extended_filters = request.session.get('extended_filters', '')

    # if extended_filters:
    #     q = q & parse_extended_filters(trunk.path, extended_filters)

    if filters:
        parsed_q = parse_filters(trunk.path, filters)
        if parsed_q:
            query = query.filter(parsed_q)
    else:
        filters = ''

    q = Q()

    if filter_ready:
        q  = q | Q(mfc_after__lte=date.today())

    if filter_waiting:
        q = q | Q(mfc_after__gt=date.today())

    if filter_other:
        q = q | Q(mfc_after__isnull=True)

    if filter_waiting or filter_ready or filter_other:
       q = q & ~Q(merged_to__pk__contains=current_branch.pk)

    # if extended_filters:
    #     q = q & parse_extended_filters(trunk.path, extended_filters)
    query = query.filter(q)

    all_commits = query.order_by('-revision').distinct('revision')
    paginator = Paginator(all_commits, 15)

    page = request.GET.get('page')
    if page is None:
        page = request.session.get('page', None)

    try:
        commits = paginator.page(page)
        request.session['page'] = page
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        commits = paginator.page(1)
        request.session['page'] = 1
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        commits = paginator.page(paginator.num_pages)
        request.session['page'] = paginator.num_pages

    context = {}
    context['commits'] = commits
    context['current_branch'] = current_branch
    context['filters'] = filters
    # context['extended_filters'] = extended_filters

    if filter_waiting:
        context['waiting_checked'] = 'checked'
        context['waiting_active'] = 'active'

    if filter_ready:
        context['ready_checked'] = 'checked'
        context['ready_active'] = 'active'

    if filter_other:
        context['other_checked'] = 'checked'
        context['other_active'] = 'active'

    return HttpResponse(template.render(context, request))


def mfcbasket(request, branch_id):
    current_branch = get_object_or_404(Branch, pk=branch_id)
    trunk_branch = Branch.trunk()
    template = loader.get_template('mfctracker/mfcbasket.html')
    revisions = _get_basket(request)
    revisions.sort()
    commits = Commit.objects.filter(revision__in=revisions).order_by("-revision")
    if request.user.is_authenticated:
        share_uri = reverse('mfcshare', kwargs={
            'username': request.user.username,
            'token': request.user.profile.share_token,
            'branch_id': current_branch.pk,
        })
        share_url = request.build_absolute_uri(share_uri)
    else:
        share_url = ''
    context = {}
    context['commits'] = commits
    context['share_url'] = share_url
    context['summarized'] = request.session.get('summarized', False)
    context['alerts'] = parse_x_mfc_with_alerts(commits, current_branch)
    context['current_branch'] = current_branch
    return HttpResponse(template.render(context, request))


def mfcshare(request, branch_id, username, token):
    current_branch = get_object_or_404(Branch, pk=branch_id)
    trunk_branch = Branch.trunk()
    user = get_object_or_404(User, username=username, profile__share_token=token)
    template = loader.get_template('mfctracker/mfcshare.html')
    revisions = user.profile.mfc_basket
    revisions.sort()
    commits = Commit.objects.filter(revision__in=revisions).order_by("revision")
    context = {}
    context['commits'] = commits
    context['username'] = username
    context['current_branch'] = current_branch
    return HttpResponse(template.render(context, request))

def mfchelper(request, branch_id, summarized = False):
    request.session['summarized'] = summarized
    current_branch = get_object_or_404(Branch, pk=branch_id)
    trunk_branch = Branch.trunk()
    template = loader.get_template('mfctracker/mfc.html')
    revisions = _get_basket(request)
    revisions.sort()
    commits = Commit.objects.filter(revision__in=revisions).order_by("revision")
    commit_msg = mfc_commit_message(revisions, request.user, summarized)
    context = {}
    merge_revisions = svn_revisions_arg(revisions)
    commit_command = 'svn merge '
    commit_command += ' '.join(merge_revisions)
    commit_command += ' ^' + trunk_branch.path + '/'
    path = current_branch.path.strip('/')
    commit_command += ' ' + path

    context['commit_msg'] = commit_msg
    context['commit_command'] = commit_command
    context['current_branch'] = current_branch
    context['empty'] = len(revisions) == 0
    context['nextformat'] = not summarized
    context['alerts'] = parse_x_mfc_with_alerts(commits, current_branch)

    return HttpResponse(template.render(context, request))

# MFC basket API
def basket(request):
    current_basket = _get_basket(request)
    return JsonResponse({'basket': current_basket})

@require_POST
def addrevision(request):
    current_basket = _get_basket(request)
    revision = request.POST.get('revision', None)
    if not revision:
        return HttpResponseBadRequest()
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    if not revision in current_basket:
        current_basket.append(revision)
    _set_basket(request, current_basket)

    return JsonResponse({'basket': current_basket})

@require_POST
def delrevision(request):
    current_basket = _get_basket(request)
    revision = request.POST.get('revision', None)
    if not revision:
        return HttpResponseBadRequest()
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    if revision in current_basket:
        current_basket.remove(revision)
    _set_basket(request, current_basket)

    return JsonResponse({'basket': current_basket})

@require_POST
def clearbasket(request):
    current_basket = []
    _set_basket(request, current_basket)

    return JsonResponse({'basket': current_basket})

@require_http_methods(["POST", "DELETE"])
def comment_commit(request, revision):
    # can't use login_required because it's API call
    # @login_required redirects to login page with 302 result code
    if not request.user.is_authenticated():
        raise PermissionDenied

    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    commit = get_object_or_404(Commit, revision=revision)
    if request.method == 'DELETE':
        # Delete comment if text wasn't passed
        try:
            comment = CommitNote.objects.get(commit=commit, user=request.user)
            comment.delete()
        except CommitNote.DoesNotExist:
            pass
    elif request.method == 'POST':
        # Delete comment if text wasn't passed
        note, created = CommitNote.objects.get_or_create(commit=commit, user=request.user)
        note.text = request.POST.get('text', '')
        note.save()

    return HttpResponse(status=204)


@require_http_methods(["POST"])
def fix_commit_dependencies(request, revision):
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    commit = get_object_or_404(Commit, revision=revision)
    mfc_with = set(commit.mfc_with.all().values_list('revision', flat=True))
    current_basket = _get_basket(request)

    for dependency in mfc_with:
        if not dependency in current_basket:
            current_basket.append(dependency)

    _set_basket(request, current_basket)

    return HttpResponse(status=204)


@require_http_methods(["POST"])
@login_required
def generate_new_token(request, branch_id):
    request.user.profile.share_token = get_random_string(length=8)
    request.user.profile.save()
    share_uri = reverse('mfcshare', kwargs={
        'username': request.user.username,
        'token': request.user.profile.share_token,
        'branch_id': branch_id
    })
    share_url = request.build_absolute_uri(share_uri)
    return JsonResponse({'url': share_url})

def get_version(request):
    try:
        from mfctracker import VERSION
        version = VERSION
    except ImportError:
        version = 'development'
    return JsonResponse({'version': version})


@require_POST
def add_do_not_merge(request, revision):
    if request.user.is_anonymous():
        return HttpResponseBadRequest()

    if not revision:
        return HttpResponseBadRequest()
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    commit = get_object_or_404(Commit, revision=revision)
    request.user.profile.do_not_merge.add(commit)
    request.user.profile.save()

    return HttpResponse(status=204)

@require_POST
def del_do_not_merge(request, revision):
    if request.user.is_anonymous():
        return HttpResponseBadRequest()

    if not revision:
        return HttpResponseBadRequest()
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    commit = get_object_or_404(Commit, revision=revision)

    commit = get_object_or_404(Commit, revision=revision)
    request.user.profile.do_not_merge.remove(commit)
    request.user.profile.save()

    return HttpResponse(status=204)


def never_mfc(request):
    if request.user.is_anonymous():
        return HttpResponseBadRequest()

    template = loader.get_template('mfctracker/nevermfc.html')

    all_commits = request.user.profile.do_not_merge.order_by("-revision")
    paginator = Paginator(all_commits, 15)

    page = request.GET.get('page')
    try:
        commits = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        commits = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        commits = paginator.page(paginator.num_pages)

    context = {}
    context['commits'] = commits
    return HttpResponse(template.render(context, request))
