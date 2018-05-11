import os
import re
import subprocess
from time import sleep
import pprint


#mountData = """Export list for nas03:
#/volume1/multimedia 192.168.1.0/24
#/volume1/sales 192.168.1.0/24
#/volume2/users 192.168.1.0/24"""

def nfsResolver():
        masterData ={}
        index =0
        hostname_val = "hostname -i"
        for hostname_val in run_command(hostname_val):
            masterData['HostName'] = hostname_val.strip()

        cmd = "showmount -e %s"%(hostname_val)
        for mountData in run_command(cmd):
            #print"<<" + mountData +">>"
            matchObj = re.match(r'(\/[a-z,0-9]+)+\s+((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\/\d{1,4})*(\*)*)*', mountData, re.M|re.I)
            if matchObj:
                index +=1
                sharePathList = re.split("\s+", mountData.strip(), flags=re.UNICODE)
               # sharePathList = mountData.strip().split(' ')
                #print sharePathList
                masterData['Share_Path' + str(index)] = sharePathList[0].strip()
                masterData['ShareAccess'+ str(index)] = sharePathList[1:]
        return masterData



def ftpResolver():
        cmd = "sudo cat /etc/vsftpd/vsftpd.conf |grep -e ^\s*[^#]"
        # for values in run_command(cmd):
            #values


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


if __name__=='__main__':
        pprint.pprint(nfsResolver())
        #ftpResolver()
