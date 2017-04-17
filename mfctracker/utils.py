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
