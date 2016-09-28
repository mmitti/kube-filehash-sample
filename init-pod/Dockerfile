FROM fedora:latest
MAINTAINER mmitti <dev@mail.mmitti.info>
RUN dnf install -y python-pip gcc redhat-rpm-config python3-devel
RUN pip3 install python-etcd
COPY init.py /
ENTRYPOINT python3 -u /init.py
