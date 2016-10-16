from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template import loader

from .models import Branch, Commit

def index(request):
    template = loader.get_template('mfctracker/index.html')
    head = Branch.head()
    all_commits = head.commit_set.order_by('-revision')
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

    context = {'commits': commits }
    return HttpResponse(template.render(context, request))
