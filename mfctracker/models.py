from django.db import models
import jsonfield

class Branch(models.Model):
    """Branch info"""
    name = models.CharField(max_length=30, unique=True)
    path = models.CharField(max_length=128, unique=True)
    is_trunk = models.BooleanField(default=False)
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
    def trunk(cls):
        return cls.objects.get(is_trunk=True)

    @classmethod
    def maintenance(cls):
        return cls.objects.filter(is_trunk=False)

class Commit(models.Model):
    """Single commit info"""
    revision = models.IntegerField(primary_key=True)
    author = models.CharField(max_length=30)
    date = models.DateTimeField()
    mfc_after = models.DateField(blank=True, null=True)
    msg = models.TextField() 
    merged_to = models.ManyToManyField(Branch, blank=True, related_name='merges')
    branch = models.ForeignKey(Branch, null=True, on_delete=models.SET_NULL, related_name='commits')

    @classmethod
    def create(cls, revision, author, date, msg):
        commit = cls(revision=revision, author=author, date=date, msg=msg)
        return commit

    @property
    def summary(self):
        msg = self.msg.strip()
        eol = msg.find('\n')
        if eol >= 0:
            return  msg[0:eol]
        return msg

class Change(models.Model):
    path = models.CharField(max_length=1024)
    operation = models.CharField(max_length=8)
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='changes')

    @classmethod
    def create(cls, commit, operation, path):
        commit = cls(path=path, operation=operation, commit=commit)
        return commit
