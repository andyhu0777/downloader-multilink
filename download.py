import urllib2
import os.path
import threading
import Queue
import sys

SAVEPATH = "."


def worker_download(downloadurl, savefile, from_, to):
    print ('worker, from: ' +  str(from_) + ', to: ' + str(to))
    size = to - from_
    print ('size: ' + str(size))

    req = urllib2.Request(downloadurl)
    req.add_header('Range', 'bytes=' + str(from_) + '-' + str(to - 1))
    netfo = urllib2.urlopen(req)
    print('worker connected') 
    sys.stdout.flush()
    localfo = open(savefile, "rb+")
    localfo.seek(from_)
    buf = '' 
    while True:
        BUF_SZ = 4096
        buf = netfo.read(min(BUF_SZ, size))
        size -= len(buf)
        print('size remaining: ' + str(size))
        sys.stdout.flush()
        localfo.write(buf)
        if size <= 0:
            break;
    netfo.close()
    localfo.close()
    print('worker finished')
    sys.stdout.flush()


def get_remote_filesize(downloadurl):
    netfo = urllib2.urlopen(downloadurl)
    return netfo.info().getheader('Content-Length')


#downloadurl = raw_input("Download Url: \n")
downloadurl = "http://de.apachehaus.com/downloads/httpd-2.4.18-x64-vc11-r3.zip?"
print('download from: ' + downloadurl)

savefile = os.path.join(SAVEPATH, os.path.basename(downloadurl)[:-1])
print('save to: ' + savefile)


N_THREADS = 20

print('number of threads: ' + str(N_THREADS))

#filesize = int(get_remote_filesize(downloadurl))

filesize = 9253683

with open(savefile, 'wb') as fo:
    fo.seek(filesize - 1)
    fo.write('\0')
print ('filesize: '+ str(os.stat(savefile).st_size))

filesizeeach = filesize // N_THREADS

if filesize % N_THREADS != 0:
    filesizeeach += 1
    lastfilesize = filesizeeach - (N_THREADS - filesize % N_THREADS)
else:
    lastfilesize = filesizeeach

print('filesize each: ' + str(filesizeeach))
print('lastfilesize: ' + str(lastfilesize));

sys.stdout.flush()

threads = []

for i in range(N_THREADS):
    from_ = i * filesizeeach
    to = i * filesizeeach + filesizeeach
    if i == N_THREADS - 1:
        to = i * filesizeeach + lastfilesize
    thread = threading.Thread(target=worker_download, args=(downloadurl, savefile, from_, to))
    thread.start()
    threads.append(thread)



for thread in threads:
    thread.join();


print "all over"
