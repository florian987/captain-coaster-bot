FROM python:3.6.6-alpine3.8

RUN apt-get update && \
    apt-get -y install openssh-client

RUN mkdir $HOME/.ssh && chmod 600 $HOME/.ssh
COPY deploy_rsa /root/.ssh/id_rsa

ENTRYPOINT ["/usr/bin/python", "-u", "GitAutoDeploy.py", "--ssh-keyscan"]