import os
import re

def nfsResolver():
	hostname = os.system('hostname')
	mountData = os.system('showmount -e hostname')
	matchObj = re.match(r'(.*):(\s(\/[a-z,0-9]+)+\s((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})*(\/\d{1,4})*))*')
	sharePath = matchObj.group(2)
	
def ftpResolver():
	os.system()

def


def printRepot():



if __name__ == __main__:
