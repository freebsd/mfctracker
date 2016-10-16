from datetime import date

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, get_object_or_404

from .models import Branch, Commit

def index(request):
    default_pk = request.session.get('branch', None)
    if default_pk is None:
        branches = Branch.objects.filter(~Q(name='HEAD')).order_by('-branch_revision', '-name')
        default_pk = branches[0].pk
    return redirect('branch', branch_id=default_pk)

def setfilter(request, branch_id):
    author = request.GET.get('author', None)
    filter_waiting = request.GET.get('filter_waiting', None)
    filter_ready = request.GET.get('filter_ready', None)
    request.session['author'] = author
    request.session['filter_waiting'] = filter_waiting is not None
    request.session['filter_ready'] = filter_ready is not None

    return redirect('branch', branch_id=branch_id)

def branch(request, branch_id):
    current_branch = get_object_or_404(Branch, pk=branch_id)
    request.session['branch'] = branch_id

    template = loader.get_template('mfctracker/index.html')
    head = Branch.head()
    branches = Branch.objects.filter(~Q(name='HEAD')).order_by('-branch_revision', '-name')
    query = head.commit_set.filter(revision__gt=current_branch.branch_revision)

    author = request.session.get('author', None)
    filter_waiting = request.session.get('filter_waiting', False)
    filter_ready = request.session.get('filter_ready', False)

    if author:
        query = query.filter(author=author)
    else:
        author = ''

    q = Q()
    if filter_ready:
        q  = q | Q(mfc_after__lte=date.today())
    if filter_waiting:
        q = q | Q(mfc_after__gt=date.today())

    if filter_waiting or filter_ready:
       q = q & ~Q(merged_to__pk__contains=current_branch.pk)

    query = query.filter(q)

    all_commits = query.order_by('-revision')
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
    context['author'] = author

    if filter_waiting:
        context['waiting_checked'] = 'checked'
        context['waiting_active'] = 'active'

    if filter_ready:
        context['ready_checked'] = 'checked'
        context['ready_active'] = 'active'

    return HttpResponse(template.render(context, request))
