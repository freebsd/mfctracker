from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponse
from django.template import loader

from .models import Branch, Commit

def index(request):
    template = loader.get_template('mfctracker/index.html')
    head = Branch.head()
    branches = Branch.objects.filter(~Q(name='HEAD')).order_by('-branch_revision', '-name')
    query = head.commit_set
    author = request.GET.get('author', None)
    if author:
        query = query.filter(author=author)

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

    context = {'commits': commits, 'branches': branches, 'current_branch': head }
    return HttpResponse(template.render(context, request))
