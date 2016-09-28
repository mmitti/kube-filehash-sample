import json
import os
from boto.s3 import connection, key
import threading
import time
import os.path

path = ""

key = ""
secret = ""
bucket_name = ""
root_dir = ""
file_list = []
range_start = 0x00
range_end = 0xFF

#CONF_PATH=/dat/conf.json
#DL_PATH=/dat/tmp
#S3_FIN=/dat/s3fin

def run():
    fetched_count = 0
    file_count = len(os.listdir(path))
    for n in file_list[:]:
        if(file_count + fetched_count >= 10):
            break
        k = bucket.get_key(n)
        name = k.name.split('/')[-1]
        print(name)
        f = open(path+name+".part", "wb")
        f.write(k.read())
        f.close()
        os.rename(path+name+".part", path+name)
        fetched_count = fetched_count + 1
        file_list.remove(n)

    print("FETCHED:",fetched_count)

def init():
    for k in bucket.list(prefix=root_dir):
        try:
            i = int(k.name.split('/')[-1][0:2], 16)
            if range_start <= i and i <= range_end:
                file_list.append(k.name)
                print(k.name)
        except:
            print("ERR:", k.name)


if __name__ == '__main__':
    conf = None
    while conf is None:
        if os.path.exists(os.environ["S3_FIN"]):
            print("FINISH WAIT")
            time.sleep(10)
            continue
        try:
            f = open(os.environ["CONF_PATH"], 'r')
            conf = json.loads(f.read())
            f.close()
        except:
            print("INIT WAIT")
            time.sleep(10)

    key = conf['s3_key']
    secret = conf['s3_secret']
    bucket_name = conf['s3_bucket']
    root_dir = conf['root']
    path = os.environ["DL_PATH"]
    range_start = conf['range_start']
    range_end = conf['range_end']

    conn = connection.S3Connection(key, secret)
    bucket = conn.get_bucket(bucket_name)

    init()

    while len(file_list) > 0:
        time.sleep(10)
        run()

    f = open(os.environ["S3_FIN"], 'w')
    f.write("DONE")
    f.close()
    print("DONE!")
