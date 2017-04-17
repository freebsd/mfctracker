from datetime import date
import re

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.views.decorators.http import require_POST, require_http_methods

from .models import Branch, Commit, CommitNote
from .utils import get_mfc_requirements

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

def parse_filters(trunk_path, filters):
    result = None
    for s in filters.split():
        s = s.strip()
        if not s:
            continue
        committer = ''
        path = ''
        committer_q = None
        path_q = None

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
    branches = Branch.maintenance().order_by('-branch_revision', '-name')
    query = trunk.commits.filter(revision__gt=current_branch.branch_revision)

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
    context['branches'] = branches
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

def mfchelper(request, branch_id):
    current_branch = get_object_or_404(Branch, pk=branch_id)
    trunk_branch = Branch.trunk()
    template = loader.get_template('mfctracker/mfc.html')
    revisions = request.session.get('basket', [])
    revisions.sort()
    commits = Commit.objects.filter(revision__in=revisions).order_by("revision")
    commit_msg = None
    alerts = []
    if len(revisions) > 0:
        str_revisions = commit_msg_revisions(revisions)
        commit_msg = 'MFC ' + str_revisions
        if len(revisions) == 1:
            commit_msg += ':'
        commit_msg += '\n'
        mfc_re = re.compile('^MFC\s+after:.*\n?', re.IGNORECASE | re.MULTILINE)
        for commit in commits:
            if len(revisions) > 1:
                commit_msg = commit_msg + '\nr' + str(commit.revision)
                if not request.user.is_anonymous():
                    if request.user.username != commit.author:
                        commit_msg += ' by {}'.format(commit.author)
                commit_msg += ':'
            # Remove ^MFC.*after:.*$
            msg = commit.msg
            msg = mfc_re.sub('', msg)
            commit_msg = commit_msg + '\n' + msg
            commit_msg = commit_msg.strip() + '\n'

            mfc_with = get_mfc_requirements(msg)
            missing = mfc_with - set(revisions)
            if len(missing) > 0:
                missing_list = ', '.join([str(x) for x in missing])
                plural = 'commits' if len(missing) > 1 else 'commit'
                alerts.append('Revision {} should be MFCed with following {}: {}'.format(commit.revision, plural, missing_list))

    context = {}
    merge_revisions = svn_revisions_arg(revisions)
    commit_command = 'svn merge '
    commit_command += ' '.join(merge_revisions)
    commit_command += ' ^' + trunk_branch.path + '/'
    path = current_branch.path.strip('/')
    commit_command += ' ' + path

    context['commit_msg'] = commit_msg
    context['commit_command'] = commit_command
    context['empty'] = len(revisions) == 0
    if len(alerts):
        context['alerts'] = alerts

    return HttpResponse(template.render(context, request))

# MFC basket API
def basket(request):
    current_basket = request.session.get('basket', [])
    return JsonResponse({'basket': current_basket})

@require_POST
def addrevision(request):
    current_basket = request.session.get('basket', [])
    revision = request.POST.get('revision', None)
    if not revision:
        return HttpResponseBadRequest()
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    if not revision in current_basket:
        current_basket.append(revision)
        request.session['basket'] = current_basket

    return JsonResponse({'basket': current_basket})

@require_POST
def delrevision(request):
    current_basket = request.session.get('basket', [])
    revision = request.POST.get('revision', None)
    if not revision:
        return HttpResponseBadRequest()
    try:
        revision = int(revision)
    except ValueError:
        return HttpResponseBadRequest()

    if revision in current_basket:
        current_basket.remove(revision)
        request.session['basket'] = current_basket

    return JsonResponse({'basket': current_basket})

@require_POST
def clearbasket(request):
    current_basket = []
    request.session['basket'] = current_basket

    return JsonResponse({'basket': current_basket})

@require_http_methods(["POST", "DELETE"])
def comment_commit(request, revision):
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
