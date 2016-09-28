import urllib.request
import json
import os
import etcd
import sys
import os.path
import time
#API=http://192.168.137.20:8080/
#NAMESPACE=default
#HOSTNAME=etcd-hab77
#ETCD_PORT=2379
#ETCD_SUFIX=/test
#CONF_PATH=/dat/conf.json
#DL_PATH=/dat/tmp
#S3_FIN=/dat/s3fin
#HASH_FIN=/dat/hashfin
suf = ""

# 現在未処理の仕事を取得する
# 見つかればreq/id/jobカウントをデクリメントしjobカウントが0であればreq/idを削除する
def enter_job(client):
    exec_id = None
    method = None
    job = 0
    root = ""
    # /req内のIDを列挙
    r = client.read(suf+"/req", sorted=True, waitIndex=10)
    for j in r.children:
        # /reqも含まれるので無視
        if j.key == suf+"/req":
            continue
        id = j.key.split('/')[-1]
        job = int(client.read(suf+"/req/"+id+"/job").value)
        # jobカウントが0より大きければデクリメントして採用する
        if job > 0:
            job -= 1
            client.write(suf+"/req/"+id+"/job", job)
            exec_id = id
            method = client.read(suf+"/req/"+id+"/method").value
            root = client.read(suf+"/req/"+id+"/root").value
        # デクリメント後も含めて0以下であればreqを削除
        if job <= 0:
            client.delete(suf+"/req/"+id, recursive=True)
        if exec_id is not None:
            break
    return (exec_id, method, root, job)

def last_wip_jobid(client, id):
    max_id = 0
    try:
        r = client.read(suf+"/wip/"+str(id))
        for j in r.children:
            if j.key == suf+"/wip/"+str(id):
                continue
            wid = int(j.key.split('/')[-1])
            max_id = max(max_id, wid)
    except:
        return 0
    return max_id

def get_wip_end_range(client, id, jid):
    try:
        return int(client.read(suf+"/wip/"+str(id)+"/"+str(jid)+"/range/end").value)
    except:
        return -1

def create_wip(client, id, remain_job_count):
    last_id = last_wip_jobid(client, id)
    jobid = last_id + 1
    div_count = remain_job_count + 1
    range_start = get_wip_end_range(client, id, last_id) + 1
    range_end = int((0xFF - range_start) / div_count) + range_start

    client.write(suf+"/wip/"+str(id)+"/"+str(jobid)+"/host", os.environ["HOSTNAME"])
    client.write(suf+"/wip/"+str(id)+"/"+str(jobid)+"/last_filename", "")
    client.write(suf+"/wip/"+str(id)+"/"+str(jobid)+"/range/start", range_start)
    client.write(suf+"/wip/"+str(id)+"/"+str(jobid)+"/range/end", range_end)
    return (jobid, range_start, range_end)


if __name__ == '__main__':
    with urllib.request.urlopen(os.environ["API"]+"api/v1/namespaces/"\
        +os.environ["NAMESPACE"]+"/pods/"+os.environ["HOSTNAME"]) as res:
        j = res.read().decode('utf-8')
        data = json.loads(j)
    nodeIP = data['status']['hostIP']
    suf = os.environ["ETCD_SUFIX"]

    client = etcd.Client(host=nodeIP, port=int(os.environ["ETCD_PORT"]))

    lock = etcd.Lock(client, 'file_hash')
    lock.acquire(timeout=30)

    exec_id, method, root, job = enter_job(client)
    if exec_id is None:
        lock.release()
        time.sleep(5)
        print("None Job")
        sys.exit(0)
    jobid, range_start, range_end = create_wip(client, exec_id, job)

    lock.release()

    print("START JOB ID:", jobid)
    print("ID:",exec_id)
    print("METHOD:",method)
    print("remain JOB Count:", job)
    print("RANGE ", range_start, "-", range_end)

    dat = {}
    dat['etcd_ip'] = nodeIP
    dat['etcd_suffix'] = suf
    dat['etcd_port'] = int(os.environ["ETCD_PORT"])
    dat['req_id'] = exec_id
    dat['job_id'] = jobid
    dat['range_start'] = range_start
    dat['range_end'] = range_end
    dat['method'] = method
    dat['root'] = root
    dat['s3_key'] = client.read(suf+"/conf/s3_key").value
    dat['s3_secret'] = client.read(suf+"/conf/s3_secret").value
    dat['s3_bucket'] = client.read(suf+"/conf/s3_bucket").value
    dat['mysql_host'] = client.read(suf+"/conf/mysql_host").value
    dat['mysql_name'] = client.read(suf+"/conf/mysql_name").value
    dat['mysql_pass'] = client.read(suf+"/conf/mysql_pass").value
    dat['mysql_user'] = client.read(suf+"/conf/mysql_user").value
    try:
        os.makedirs(os.environ["DL_PATH"])
    except:
        print("Exisits")

    f = open(os.environ["CONF_PATH"], 'w')
    f.write(json.dumps(dat))
    f.close()

    print("WAIT")
    while not os.path.exists(os.environ["S3_FIN"]) \
        or not os.path.exists(os.environ["HASH_FIN"]):
        time.sleep(10)

    client.write(suf+"/done/"+str(exec_id)+"/"+str(jobid)+"/host", os.environ["HOSTNAME"])


    os.remove(os.environ["CONF_PATH"])
    os.remove(os.environ["S3_FIN"])
    os.remove(os.environ["HASH_FIN"])
