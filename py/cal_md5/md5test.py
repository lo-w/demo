# import os
# import ctypes
from datetime import datetime

# libc = ctypes.CDLL(None, use_errno=True)
# def readahead(fno, offset, count):
#     code = libc.readahead(
#         ctypes.c_int(fno),
#         ctypes.c_longlong(offset),
#         ctypes.c_size_t(count)
#     )
#     if code != 0:
#         print(ctypes.get_errno())

# filename= "/mnt/c/Users/lo/Downloads/霸王别姬.1080p.国粤双语.BD中英双字/霸王别姬.1080p.国粤双语.BD中英双字[66影视www.66Ys.Co].mp4"
filename= "/home/lo/.repo/work/py/bawang.mp4"

import hashlib
fh = hashlib.md5()

# import xxhash
# fh = xxhash.xxh128()

offset = 2**18

start = datetime.now()
print(start)

# f = os.open(filename, os.O_RDONLY)
# for i in range(0, 5000):
#     # readahead(fd, i * offset, offset)
#     chunk = os.pread(f, offset, i * offset)
#     fh.update(chunk)

# with os.open(filename, os.O_RDONLY) as f:
#     for chunk in iter(lambda: os.read(f, offset), b''):
#         fh.update(chunk)

# f = libc.fopen(filename, "rb")
# print(type(f))
# read()
# chunk = f.read(offset)
# i = 0
# while chunk:
#     # i += 1
#     # readahead(f.fileno(), i * offset, offset)
#     fh.update(chunk)
#     chunk = f.read(offset)

with open(filename,'rb') as f:
    for chunk in iter(lambda: f.read(offset), b''):
        fh.update(chunk)

print(fh.hexdigest())
end = datetime.now()

print(end)
print(end - start)


