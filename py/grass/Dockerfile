FROM alpine:3.19

### https://hub.docker.com/_/alpine
### https://pkgs.alpinelinux.org/packages
### https://pkgs.alpinelinux.org/packages?name=chromium&branch=v3.19&repo=&arch=&maintainer=
### https://chromedriver.storage.googleapis.com/index.html
### https://chromedriver.storage.googleapis.com/99.0.4844.51/chromedriver_linux64.zip
### https://pypi.org/project/chromedriver-binary/#history
ENV WORKDIR=/opt/.work \
EXTENSIONID='ilehaonighjijnmpnagapkhpcdbhclfg' \
STARTUP=/start

RUN apk update && \
### get chrome & driver
apk add --no-cache python3 py3-pip chromium chromium-chromedriver wget curl && \
### create virtual env
mkdir -p $WORKDIR/logs && python3 -m venv $WORKDIR && . $WORKDIR/bin/activate && \
### install python lib
pip install --no-cache-dir selenium flask && \
### get grass extention
CHROME_DRIVER_VERSION='123.0.6312.122' && \
GRASS_EXT='https://clients2.google.com/service/update2/crx?response=redirect&prodversion=CHROME_DRIVER_VERSION&acceptformat=crx2,crx3&x=id%3DEXTENSIONID%26uc&nacl_arch=x86-64' && \
wget --no-check-certificate --no-cache --no-cookies -q $(echo $GRASS_EXT | sed "s/CHROME_DRIVER_VERSION/$CHROME_DRIVER_VERSION/g;s/EXTENSIONID/$EXTENSIONID/g") -O $WORKDIR/grass.crx && \
### get grass script
GRASS_SCR='https://raw.githubusercontent.com/lo-w/demo/main/py/grass/grass.py' && \
wget --no-check-certificate --no-cache --no-cookies -q $GRASS_SCR -P $WORKDIR && \
### add cronjob
echo '*/5 * * * * RANDOM=$(date +%s%N | cut -b10-19) && sleep $(( $RANDOM % 150 )) && curl http://localhost:3000' >> /etc/crontabs/root && \
### add start up script
echo '#!/bin/sh -e' > $STARTUP && \
echo '### START CRONJOB...' >> $STARTUP && \
echo 'crond -l 2 -f > /dev/stdout 2> /dev/stderr &' >> $STARTUP && \
echo '### START GRASS...' >> $STARTUP && \
echo 'echo "GRASS starting..."' >> $STARTUP && \
echo '$WORKDIR/bin/python $WORKDIR/grass.py &' >> $STARTUP && \
echo 'wait -n' >> $STARTUP && \
echo 'exit $?' >> $STARTUP && \
chmod +x $STARTUP && rm -rf /var/cache/apk/*

# CMD ["$WORKDIR/bin/python", "$WORKDIR/grass.py"]
ENTRYPOINT ["sh", "-c", "$STARTUP"]
