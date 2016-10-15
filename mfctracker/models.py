from django.db import models

class Branch(models.Model):
    """Branch info"""
    name = models.CharField(max_length=30, unique=True)
    path = models.CharField(max_length=128, unique=True)

class Commit(models.Model):
    """Single commit info"""
    revision = models.IntegerField(unique=True)
    author = models.CharField(max_length=30)
    date = models.DateTimeField()
    mfc_after = models.DateTimeField(blank=True, null=True)
    msg = models.TextField() 
    mfced_commits = models.ManyToManyField('self', blank=True)
    branch = models.ForeignKey(Branch, null=True, on_delete=models.SET_NULL)
