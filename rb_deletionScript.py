import os
import argparse
import pysftp
import shutil



def connection_module(serverlist, userName, userPassword, filePath):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    for server in serverlist:
        srv = pysftp.Connection(server, username= userName, password= userPassword , cnopts=cnopts,
                                default_path= filePath)
        for attr in srv.listdir_attr():
            matchfile = re.match(r'(.*) (rb_.*)$', str(attr), re.M)
            if matchfile:
                print matchfile.group(2)
                fileName=(matchfile.group(2)).strip()
                shutil.rmtree(filePath/fileName)

                #srv.get(matchfile.group(2), preserve_mtime = True)




if __name__==__main__:
    # cpmmand line parser
    parser = argparse.ArgumentParser(description="rb_deletionScript")

    parser.add_argument('-sf', '--serverfile', action='store', default='servers.txt',
                        help='Indicate relative path to an input file that contains all the servers to connect.\nBy default, servers.txt is used')
    parser.add_argument('-sp', '--srcfilepath', action='store', nargs='+',
                        help='Indicate relative path to files contain filepath need to be downloaded')
    parser.add_argument('-u', '--user', nargs='+',
                        help='Input a user ID')
    parser.add_argument('-p', '--password', nargs=1,
                        help='Input a user ID password')

    args = parser.parse_args()

    serverlist = []
    serverFilePath = os.path.join('.', args.serverfile)
    if args.serverfile is not None and os.path.exists(serverFilePath):
        with open(serverFilePath) as serverFile:
            servers = serverFile.readlines()
        serverlist += [x.strip() for x in servers]

    if len(serverlist) is 0:
        parser.error('Server does not exist')
    print serverlist, args.user, args.password, args.srcfilepath
    connection_module(serverlist, args.user, args.password, args.srcfilepath)
