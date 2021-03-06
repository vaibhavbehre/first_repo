import sys
import os
from subprocess import Popen, PIPE, STDOUT
from time import sleep
from os import waitpid, execv, read, write
 #Ports are handled in ~/.ssh/config since we use OpenSSH
COMMAND="uname -a"
ssh = subprocess.Popen(['ssh', 'uname@hostname',  COMMAND],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
result = ssh.stdout.readlines()
if result == []:
    error = ssh.stderr.readlines()
    print >>sys.stderr, "ERROR: %s" % error
else:
    print result
