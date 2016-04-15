import urllib2
import os.path
import threading
import Queue
import sys
import os
import time

SAVEPATH = "."


downloaded_sz = 0
total_sz = 0
lock = threading.Lock()


def worker_progress():
    print ('worker, total_sz = ' + str(total_sz));
    while downloaded_sz != total_sz:
        print ('downloaded size: ' + str(downloaded_sz), 'total size: ' + str(total_sz), str(float(downloaded_sz) / total_sz * 100) + '%')
        sys.stdout.flush()
        time.sleep(1)


# This is executed by each worker_download Thread
def throw_bytes(sz):
     global downloaded_sz
     lock.acquire(True)
     downloaded_sz += sz
     lock.release()
    

def worker_download(downloadurl, savefile, from_, to):
    print ('worker, from: ' +  str(from_) + ', to: ' + str(to))
    size = to - from_
    print ('size: ' + str(size))

    req = urllib2.Request(downloadurl) 
    header_range = 'bytes=' + str(from_) + '-' + str(to - 1)
    req.add_header('Range', header_range)
    print('header range: ' + header_range)

    netfo = urllib2.urlopen(req)
    print('worker connected') 
    sys.stdout.flush()

    localfo = open(savefile, "rb+")
    localfo.seek(from_)
    print('seek to position ' + str(from_))

    BUF_SZ = 4096
    while size > 0:
        rd_sz = min(BUF_SZ, size)
        buf = netfo.read(rd_sz)
        localfo.write(buf)
        throw_bytes(len(buf))
        size -= len(buf)

    netfo.close()
    localfo.close()
    print('worker finished')
    sys.stdout.flush()


def head_response(downloadurl, **headers):
    request = urllib2.Request(downloadurl, headers = headers)
    request.get_method = lambda: 'HEAD'
    r = urllib2.urlopen(request)
    return r

def get_remote_filesize(downloadurl):
    netfo = head_response(downloadurl)
    return netfo.info().getheader('Content-Length')


def is_partial_supp(downloadurl):
    fo = head_response(downloadurl, Range = 'bytes=3-5')
    return fo.getcode() == 206


#downloadurl = raw_input("Download Url: \n")
#downloadurl = "http://de.apachehaus.com/downloads/httpd-2.4.18-x64-vc11-r3.zip?"
#downloadurl = "http://dlsw.baidu.com/sw-search-sp/soft/ca/13442/Thunder_dl_7.9.43.5054.1456898740.exe?"

#downloadurl = "http://tenet.dl.sourceforge.net/project/mingw-w64/mingw-w64/mingw-w64-release/mingw-w64-v4.0.6.zip?"


downloadurl="https://atlas.hashicorp.com/laravel/boxes/homestead/versions/0.4.2/providers/virtualbox.box?"



print('download from: ' + downloadurl)

savefile = os.path.join(SAVEPATH, os.path.basename(downloadurl)[:-1])
print('save to: ' + savefile)


N_THREADS = 20

# check if partial content is supported
if not is_partial_supp(downloadurl):
#    print('partial content is not supported, do you want to change N_THREADS to only one?')
#    sys.stdout.flush()
#    answer = raw_input('')
#    if answer == 'yes':
    print('partial content is not supported, switching to single thread...')
    sys.stdout.flush()
    N_THREADS = 1
#    else:
#        print 'quiting ...'
#        exit(0)

    


print('number of threads: ' + str(N_THREADS))

filesize = int(get_remote_filesize(downloadurl))
total_sz = filesize

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


thread_progress = threading.Thread(target=worker_progress)
thread_progress.start()
threads.append(thread_progress)



for thread in threads:
    thread.join();


print "all over"
