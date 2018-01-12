import os
import argparse
import pysftp
import zlib




def connection_module(serverlist, userName, password):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    for server in serverlist:
        srv = pysftp.Connection('192.168.190.129', username='root', password='redhat', cnopts=cnopts,
                                default_path='/d/d3')
        for attr in srv.listdir_attr():
            print(attr)
            matchfile = re.match(r'(.*) (pb.*)$', str(attr), re.M)
            if matchfile:
                print matchfile.group(2)
                srv.get(matchfile.group(2), preserve_mtime = True)





def adler32sum(filename, blocksize=65536):
    checksum = zlib.adler32("")
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            checksum = zlib.adler32(block, checksum)
    return checksum & 0xffffffff
print adler32sum(filename)


def disk_usage(path):
    """Return disk usage statistics
    Returned valus is about the given path.
        a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    percentagefree=float(free)/total
    return percentagefree

if __name__==__main__:
    # cpmmand line parser
    parser = argparse.ArgumentParser(description="backupScript")
    parser.add_argument('-s', '--server', nargs='+',
                        help='Input server(s) to connect. Addition to servers in serverfile. ')
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

    if args.server is not None:
        serverlist += args.server

    if len(serverlist) is 0:
        parser.error('Server does not exist')

    connection_module(serverlist, args.user, args.password)


