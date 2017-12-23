import os
import socket
import socks
import requests
import threading
import time
import queue
import logging
import argparse





"""
url='http://2.bp.blogspot.com/-P0bE2S6NY8g/T4jOqvfILPI/AAAAAAAAOGw/C-3eg-KfepM/s1600/IMG_5598.JPG'


try:
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 2080)
    #socks.set_default_proxy(socks.SOCKS5, "104.224.167.103", 443)
    socket.socket = socks.socksocket
    content = requests.get(url, timeout=180).text
except Exception as e:
    print(str(e))


 
import threading, time, random
count = 0
class Downloader(threading.Thread):
    def __init__(self, queue, lock=None, threadName=None):
        super(Counter, self).__init__(name = threadName)   
        self.lock = lock
        self.queus = queue
    
    def run(self):
        global count
        self.lock.acquire()
        for i in xrange(10000):
            count = count + 1
        self.lock.release()
lock = threading.Lock()
for i in range(5): 
    Counter(lock, "thread-" + str(i)).start()
time.sleep(2)	#确保线程都执行完毕
print count

"""
DIR = os.getcwd()
logging.basicConfig(filename=os.path.join(DIR,'logger.log'), level=logging.INFO)


class Downloader(threading.Thread):
    def __init__(self, q, dir_name, lock=None, threadName=None):
        super(Downloader, self).__init__(name=threadName)
        
        self.lock = lock
        self.queue = q
        self.thread_stop = False
        self.dir_name = dir_name
        self.retry_lst = {}

    def download(self, url):
        try:
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 2080)
            #socks.set_default_proxy(socks.SOCKS5, "104.224.167.103", 443)
            socket.socket = socks.socksocket
            r = requests.get(url, stream=True, timeout=10) 
            #raise Exception("抛出一个异常") 
            return r
        except Exception as e:
            print(str(e))
            logging.error("download error,request get:{}".format(url))
            return None

    def run(self):
        while not self.thread_stop:
            #print('------------------is_sigint_up:{}'.format(is_sigint_up))
            #print("thread {} : waiting for task".format(int(self.ident)))  
            try:  
                url=self.queue.get(block=True, timeout=20)#接收消息
                print("[BEGIN] thread: {} ;task url:{}".format(int(self.ident), url))
            except queue.Empty:  
                print("Nothing to do!i will go home!")  
                self.thread_stop=True  
                break 

            filename = url.strip().split('/')[-1]
            r = self.download(url)
            if r:
                try:
                    with open(os.path.join(DIR, self.dir_name,filename),'wb') as fd:
                        for chunk in r.iter_content():
                            fd.write(chunk)
                    print("[DONE] thread:{};taskurl:{} done; left:{}".format(int(self.ident), url,self.queue.qsize()))
                    logging.info("[DONE] thread:{};taskurl:{} done; left:{}".format(int(self.ident), url,self.queue.qsize()))                    
                except Exception as e:               
                    print(str(e))
                    #删掉没下载完成的图片
                    os.remove(os.path.join(DIR, self.dir_name,filename))
                    #重新放入queue,维护一个下载次数列表，最多失败三次
                    retry_num = self.retry_lst.get(url, 0)
                    if retry_num < 3:
                        self.queue.put(url)
                        retry_num += 1
                        self.retry_lst[url] = retry_num   
                        print("[RETRY] thread {} : task url:{}, retry_num:{}".format(int(self.ident), url, retry_num)) 
                        logging.info("[RETRY] thread {} : task url:{}, retry_num:{}".format(int(self.ident), url, retry_num))
                    else:
                        logging.error("download error,write chunk:{}".format(url))

            self.queue.task_done()#完成一个任务  

    def stop(self):  
        self.thread_stop = True  

 
def Boss(q,links):
    for link in links:
        q.put(link, block=True, timeout=None)

#   with open('D:\\download\\bing_test_all.txt', 'r') as f:
#       for line in f:
#           q.put(line.strip(), block=True, timeout=None)
            #print("queue size:{}".format(q.qsize()))

 
def main():
    p = argparse.ArgumentParser(prog='aioget',
                            description='''
                            Downloads concurrently a list of files''')
    p.add_argument("urls", help="Download links", nargs='*')
    p.add_argument("-f",
                   "--from_file",
                   metavar='FILE',
                   type=str,
                   help="Reads urls from a file")
    args = p.parse_args()

    if args.from_file:
        with open(os.path.join(DIR, args.from_file), 'r') as fh:
            c = fh.readlines()
            links = [elem.strip() for elem in c]

            dir_name = args.from_file +'_download'
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)


    q=queue.Queue()
    thread_boss=threading.Thread(target = Boss, args = (q,links,), name = 'thread-boss')
    thread_boss.start()
    
    thread_lst = []
    for i in range(5): 
        thread = Downloader(q=q, dir_name=dir_name)
        thread_lst.append(thread)
    
    for t in thread_lst: 
        t.start()
        print("{} running".format(t))
  
    thread_boss.join()
    q.join()
  

if __name__=='__main__':
    main()
