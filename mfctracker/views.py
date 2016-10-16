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

def branch(request, branch_id):
    current_branch = get_object_or_404(Branch, pk=branch_id)
    request.session['branch'] = branch_id

    template = loader.get_template('mfctracker/index.html')
    head = Branch.head()
    branches = Branch.objects.filter(~Q(name='HEAD')).order_by('-branch_revision', '-name')
    query = head.commit_set.filter(revision__gt=current_branch.branch_revision)

    author = request.GET.get('author', None)
    if author is None:
        author = request.session.get('author', None)
    else:
        request.session['author'] = author

    if author:
        query = query.filter(author=author)
    else:
        author = ''

    all_commits = query.order_by('-revision')
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
    context['branches'] = branches
    context['current_branch'] = current_branch
    context['author'] = author

    return HttpResponse(template.render(context, request))
