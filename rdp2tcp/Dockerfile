FROM ubuntu:22.04

ENV WORKDIR=/opt/.work \
STARTUP=/start \
DISPLAY=:99

RUN apt update && \
### get related pkgs
apt install -y wget xvfb freerdp2-x11 xdotool ca-certificates openssl iptables && \
WGET_ARGS="--no-check-certificate --no-cache --no-cookies" && \
### get rdp2tcp client(compile from local)
### https://github.com/V-E-O/rdp2tcp/blob/master/INSTALL
RDP2TCP_CLIENT='https://raw.githubusercontent.com/lo-w/demo/refs/heads/main/rdp2tcp/client' && \
wget $WGET_ARGS -q $RDP2TCP_CLIENT -P $WORKDIR && \
### get rdp2tcp start bash
RDP2TCP_START='https://raw.githubusercontent.com/lo-w/demo/refs/heads/main/rdp2tcp/rdp2tcp.sh' && \
wget $WGET_ARGS -q $RDP2TCP_START  -P $WORKDIR && \
### add start up script
echo '#!/bin/bash -e' > $STARTUP && \
echo '### START RDP2TCP...' >> $STARTUP && \
echo 'echo "RDP2TCP starting..."' >> $STARTUP && \
echo '$WORKDIR/rdp2tcp.sh &' >> $STARTUP && \
echo 'tail -f /dev/null' >> $STARTUP && \
echo 'wait' >> $STARTUP && \
chmod +x $STARTUP

ENTRYPOINT ["sh", "-c", "$STARTUP"]
