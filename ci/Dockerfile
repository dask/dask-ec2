FROM ubuntu:14.04

RUN apt-get update && apt-get install -y curl openssh-server python-dev libffi-dev libssl-dev

RUN mkdir /var/run/sshd
RUN echo 'root:root' |chpasswd
RUN sed -ri 's/^PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config

RUN mkdir -p /root/.ssh
ADD vagrant.pub /root/.ssh/authorized_keys

EXPOSE 22

CMD    ["/usr/sbin/sshd", "-D"]
