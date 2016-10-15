import svn.remote
import json

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from mfctracker.models import Commit, Branch

def mergeinfo_ranges_to_set(mergeinfo_ranges):
    """Convert compact ranges representation to python set object"""
    result = set()
    for r in mergeinfo_ranges:
        if type(r) == int:
            result.add(r)
        else:
            result |= set(range(r[0], r[1]+1))
    return result

def parse_mergeinfo_prop(mergeinfo_str):
    """Parse svn:mergeinfo property and return dictionary
       where branch pathes are keys and values are compact
       representations of merged commits: array of numbers
       and tuples with <first, last> values
    """
        
    lines = mergeinfo_str.split('\n')
    mergeinfo = {}

    for  line in lines:
        if not line:
            next
        branch_path, merged_part = line.split(':')
        revisions = merged_part.split(',')
        merged = []
        for r in revisions:
            if r.find('-') > 0:
                start, stop = r.split('-')
                merged.append((int(start), int(stop),))
            else:
                merged.append(int(r))
        mergeinfo[branch_path] = merged

    return mergeinfo

class Command(BaseCommand):
    help = 'Import new commits from SVN repo'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--start-revision', type=int,
            default=-1, help='revision to start import from')
        parser.add_argument('-b', '--branch', type=str,
            default=None, help='name of the branch')
        parser.add_argument('-l', '--limit', type=int,
            default=None, help='maximum number of commits passsed to svn log command')

    def handle(self, *args, **options):
        revision = options['start_revision']
        branch = options['branch']

        if branch is None:
            branches = list(Branch.objects.all())
        else:
            branches = [ Branch.objects.get(name=branch) ]

        r = svn.remote.RemoteClient(settings.SVN_BASE_URL)


        for b in branches:
            revision = max(revision, b.branch_revision)
            self.stdout.write('Importing commits for branch %s, starting with r%d' % (b.name, revision))
            log_entries = reversed(list(r.log_default(rel_filepath=b.path, revision_from=revision)))
            branch_commits = 0
            last_revision = 0
            for entry in log_entries:
                commit = Commit.create(entry.revision, entry.author, entry.date, entry.msg)
                commit.branch = b
                commit.save()
                branch_commits += 1
                last_revision = entry.revision

            if branch_commits:
                self.stdout.write('Imported {} commits, last revision is {}'.format(branch_commits, last_revision))
                b.last_revision = last_revision
            else:
                self.stdout.write('No commits to import')

            props = r.properties(b.path)
            mergeinfo_prop = props.get('svn:mergeinfo', None)
            mergeinfo = {}
            if mergeinfo_prop is not None:
                mergeinfo = parse_mergeinfo_prop(props['svn:mergeinfo'])
            b.mergeinfo = mergeinfo
            b.save()

        # Sync mergeinfo and commit records
        known_pathes = list(Branch.objects.values_list('path', flat=True)) 
        for b in branches:
            old_merged_revisions = list(b.merges.values_list('revision', flat=True))
            new_merged_revisions = set()
            for path in known_pathes:
                if path == b.path:
                    continue
                if not path in b.mergeinfo.keys():
                    continue
                new_merged_revisions |= mergeinfo_ranges_to_set(b.mergeinfo[path])
            update_revisions = new_merged_revisions.difference(old_merged_revisions)
            new_merged_commits = 0
            for commit in Commit.objects.filter(revision__in=update_revisions):
                commit.merged_to.add(b)
                commit.save()
                new_merged_commits += 1
            self.stdout.write('{} commits marked as merged to {}'.format(new_merged_commits, b.name))
