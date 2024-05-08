FROM alpine:edge

ENV WORKDIR=/opt/.work \
    STARTUP=/start

RUN apk update && \
apk add --no-cache ca-certificates wget && \
mkdir -p $WORKDIR && \
### GAGA
GAGA_URL='https://assets.coreservice.io/public/package/65/gaganode_pro/0.0.300/gaganode_pro-0_0_300.tar.gz' && \
wget --no-check-certificate --no-cache --no-cookies $GAGA_URL -q -O- | tar -zxf- --strip-components=1 -C $WORKDIR/ && \
### START ENTRYPOINT FILE
echo '#!/bin/sh -e' > $STARTUP && \
echo '### START GAGA...' >> $STARTUP && \
echo 'if [ -z $TOKEN ]; then' >> $STARTUP && \
echo '    echo "GAGA TOKEN not exists..."' >> $STARTUP && \
echo 'else' >> $STARTUP && \
echo '    echo "GAGA TOKEN replace..."' >> $STARTUP && \
echo '    sed -i "s/token = '\'''\''/token = '\''$TOKEN'\''/g;s/INFO/ERROR/g" $WORKDIR/root_conf/default.toml' >> $STARTUP && \
echo '    echo "GAGA starting..."' >> $STARTUP && \
echo '    $WORKDIR/gaganode &' >> $STARTUP && \
echo 'fi' >> $STARTUP && \
echo 'wait -n' >> $STARTUP && \
echo 'exit $?' >> $STARTUP && \
chmod +x $STARTUP && \
rm -rf /var/cache/apk/*

ENTRYPOINT ["sh", "-c", "$STARTUP"]
