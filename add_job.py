import etcd
import os
import sys
#ETCD_PORT=2379
#ETCD_PREFIX=/test
#ETCD_SRV=192.168.137.21
if __name__ == '__main__':
    method = sys.argv[1]
    job = sys.argv[2]
    root = sys.argv[3]

    pre = os.environ["ETCD_PREFIX"]

    client = etcd.Client(host=os.environ["ETCD_SRV"], port=int(os.environ["ETCD_PORT"]))
    max_id = 0
    r = client.read(pre+"/req", sorted=True, waitIndex=10)
    for j in r.children:
        if j.key == pre+"/req":
            continue
        id = int(j.key.split('/')[-1])
        max_id = max(max_id, id)

    client.write(pre+"/req/"+str(max_id+1)+"/job", job)
    client.write(pre+"/req/"+str(max_id+1)+"/method", method)
    client.write(pre+"/req/"+str(max_id+1)+"/root", root)
    print("DONE ID:", max_id+1)
