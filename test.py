import zlib
filename='/home/vaibhavbehre/gentoo_root.img'
def adler32sum(filename, blocksize=65536):
    checksum = zlib.adler32("")
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            checksum = zlib.adler32(block, checksum)
    return checksum & 0xffffffff
print adler32sum(filename)
