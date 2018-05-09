import os
import re
import subprocess
from time import sleep


#mountData = """Export list for nas03:
#/volume1/multimedia 192.168.1.0/24
#/volume1/sales 192.168.1.0/24
#/volume2/users 192.168.1.0/24"""

def nfsResolver():
        masterData ={}
        hostname_val = "hostname -i"
        for hostname_val in run_command(hostname_val):
            masterData['HostName'] = hostname_val

        cmd = "showmount -e %s"%(hostname_val)
        for mountData in run_command(cmd):
            print"<<" + mountData +">>"
            matchObj = re.match(r'^(\/[a-z,0-9]+)+\s((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\/\d{1,4})*)*\n', mountData,re.M)
            if matchObj:
                 print matchObj.group(1)
                 print matchObj.group(2)
#       modifiedData = str(mountData).split(':')
        #print modifiedData
        #matchObj = re.match(r'(.*):(\s(\/[a-z,0-9]+)+\s((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})*(\/\d{1,4})*))*')
        #sharePath = matchObj.group(2)

def ftpResolver():
        os.system()
        return 0

def run_command(command):
        p = subprocess.Popen(command, stdout = subprocess.PIPE,
                                        stderr = subprocess.PIPE, shell=True)
        for line in iter(p.stdout.readline,b''):
            if line:
                yield line
        while p.poll() is None:
            sleep(.1)
        err = p.stderr.read()
        if p.returncode !=0:
            print"Error: " + str(err)




def printRepot():
        return 0




if __name__ == '__main__':

if __name__=='__main__':
	nfsResolver()
