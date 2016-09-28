import json
import os
import threading
import pymysql.cursors
import hashlib
from socket import gethostname
import os.path
import sys
import etcd
import time

path = ""
db_host = ""
db_user = ""
db_pass = ""
db_name = ""
table_name = "FileHash"
hash_method = "MD5"

#CONF_PATH=/dat/conf.json
#DL_PATH=/dat/tmp
#S3_FIN=/dat/s3fin
#HASH_FIN=/dat/hashfin

def db_write(host_name, file_name, file_hash):
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        db=db_name,
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor)
    with conn.cursor() as cur:
        sql = "INSERT INTO FileHash (HostName, FileName, HashMethod, Hash, Date) VALUES (%s, %s, %s, %s, NOW())"
        cur.execute(sql, (host_name, file_name, hash_method, file_hash))
        conn.commit()
    conn.close()

def get_hash(file_name):
    method = hashlib.md5()
    if hash_method == "SHA1":
        method = hashlib.sha1()
    elif hash_method == "SHA224":
        method = hashlib.sha224()
    elif hash_method == "SHA256":
        method =  hashlib.sha256()
    elif hash_method == "SHA384":
        method =  hashlib.sha384()
    elif hash_method == "SHA512":
        method =  hashlib.sha512()

    with open(path + file_name, 'rb') as f:
        for chunk in iter(lambda: f.read(2048 * method.block_size), b''):
            method.update(chunk)

    return method.hexdigest()


def run():
    count = 0
    rm_files = []
    for f in os.listdir(path):
        if f.endswith(".part"):
            continue
        print(f)
        db_write(gethostname(), f, get_hash(f))
        count += 1
        rm_files.append(f)
    if count != 0:
        print("WRITE:", count)
    for f in rm_files:
        os.remove(path+f)

    if count == 0 and os.path.exists(os.environ["S3_FIN"]):
        print("DONE!")
        f = open(os.environ["HASH_FIN"], 'w')
        f.write("DONE")
        f.close()
        sys.exit(0)
    t=threading.Timer(10,run)
    t.start()

if __name__ == '__main__':
    conf = None
    while conf is None:
        if os.path.exists(os.environ["HASH_FIN"]):
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

    path = os.environ["DL_PATH"]

    db_host = conf['mysql_host']
    db_user = conf['mysql_user']
    db_pass = conf['mysql_pass']
    db_name = conf['mysql_name']
    hash_method = conf['method']

    t=threading.Thread(target=run)
    t.start()
