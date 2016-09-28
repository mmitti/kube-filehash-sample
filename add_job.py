import etcd
import os
import sys
#ETCD_PORT=2379
#ETCD_SUFIX=/test
#ETCD_SRV=192.168.137.21
if __name__ == '__main__':
    method = sys.argv[1]
    job = sys.argv[2]
    root = sys.argv[3]

    suf = os.environ["ETCD_SUFIX"]

    client = etcd.Client(host=os.environ["ETCD_SRV"], port=int(os.environ["ETCD_PORT"]))
    max_id = 0
    r = client.read(suf+"/req", sorted=True, waitIndex=10)
    for j in r.children:
        if j.key == suf+"/req":
            continue
        id = int(j.key.split('/')[-1])
        max_id = max(max_id, id)

    client.write(suf+"/req/"+str(max_id+1)+"/job", job)
    client.write(suf+"/req/"+str(max_id+1)+"/method", method)
    client.write(suf+"/req/"+str(max_id+1)+"/root", root)
    print("DONE ID:", max_id+1)
