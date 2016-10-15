from django.db import models
import jsonfield

class Branch(models.Model):
    """Branch info"""
    name = models.CharField(max_length=30, unique=True)
    path = models.CharField(max_length=128, unique=True)
    mergeinfo = jsonfield.JSONField(default={})
    # Last imported revision
    last_revision = models.IntegerField(default=1)
    # Branchpoint
    branch_revision = models.IntegerField(default=1)

    @classmethod
    def create(cls, name, path):
        obj = cls(name=name, path=path)
        return obj

    @classmethod
    def head(cls):
        return cls.objects.get(name='HEAD')

class Commit(models.Model):
    """Single commit info"""
    revision = models.IntegerField(primary_key=True)
    author = models.CharField(max_length=30)
    date = models.DateTimeField()
    mfc_after = models.DateTimeField(blank=True, null=True)
    msg = models.TextField() 
    merged_to = models.ManyToManyField(Branch, blank=True, related_name='merges')
    branch = models.ForeignKey(Branch, null=True, on_delete=models.SET_NULL)

    @classmethod
    def create(cls, revision, author, date, msg):
        commit = cls(revision=revision, author=author, date=date, msg=msg)
        return commit
