#  Copyright (c) 2016-2017 Oleksandr Tymoshenko <gonzo@bluezbox.com>
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#  SUCH DAMAGE.
import re

def get_mfc_requirements(msg):
    """ Get set of revisions required to be merged with commit """
    requirements = set()
    lines = msg.split('\n')
    for line in lines:
        if re.match('^\s*x-mfc-with\s*:', line, flags=re.IGNORECASE):
            pos = line.find(':')
            line = line[pos+1:]
            revisions = re.split('[, ]+', line.strip())
            for rev in revisions:
                if rev.startswith('r'):
                    rev = rev[1:]
                try:
                    r = int(rev)
                    requirements.add(r)
                except ValueError:
                    pass # Just ignore garbage in field

    return requirements

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


def mergeinfo_ranges_to_set(mergeinfo_ranges):
    """Convert compact ranges representation to python set object"""
    result = set()
    for r in mergeinfo_ranges:
        if type(r) == int:
            result.add(r)
        else:
            result |= set(range(r[0], r[1]+1))
    return result

