from django.http import HttpResponse
from django.template import loader

from .models import Branch, Commit

def index(request):
    template = loader.get_template('mfctracker/index.html')
    head = Branch.head()
    commits = head.commit_set.order_by('-revision')[:10]
    context = {'commits': commits}
    return HttpResponse(template.render(context, request))
