#!/usr/bin/env python

import urllib2
import subprocess
from subprocess import call

def is_connected_to_internet():
    try:
        f = urllib2.urlopen("http://www.google.com", timeout=1)
        f.close()
        return True
    except urllib2.URLError as err:
        pass
    return False


def run_shell(commands, show_output=False):
    if show_output:
        print "RUN: `%s` ---" % ' '.join(commands)

    proc = subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    (out, err) = proc.communicate()

    if show_output:
        print out


def main():
    # if no connection then try to restart wlan
    if is_connected_to_internet() == False:
        run_shell(["ifdown", "wlan0"], True)
        run_shell(["ifup", "wlan0"], True)


if __name__ == "__main__":
    main()
