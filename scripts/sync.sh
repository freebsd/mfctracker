#!/bin/sh

lockfile=/var/tmp/mfctracker.sync.lock

if ( set -o noclobber; echo "$$" > "$lockfile") 2> /dev/null; then

    trap 'rm -f "$lockfile"; exit $?' INT TERM EXIT
    /usr/local/bin/mfctracker-manage importcommits $*

    # clean up after yourself, and release your trap
    rm -f "$lockfile"
    trap - INT TERM EXIT
else
        echo "Lock exists: $lockfile owned by $(cat $lockfile)"
fi
