FROM alpine:edge

ENV WORKDIR=/opt/.work \
    STARTUP=/start

RUN apk update && \
apk add --no-cache ca-certificates wget && \
mkdir -p $WORKDIR/gaga $WORKDIR/meson $WORKDIR/openvpn /etc/openvpn/ && \
### GAGA
GAGA_URL='https://assets.coreservice.io/public/package/65/gaganode_pro/0.0.300/gaganode_pro-0_0_300.tar.gz' && \
wget --no-check-certificate --no-cache --no-cookies $GAGA_URL -q -O- | tar -zxf- --strip-components=1 -C $WORKDIR/gaga/ && \
### MESON
MESON_URL='https://staticassets.meson.network/public/meson_cdn/v3.1.20/meson_cdn-linux-amd64.tar.gz' && \
wget --no-check-certificate --no-cache --no-cookies $MESON_URL -q -O- | tar -zxf- --strip-components=1 -C $WORKDIR/meson/ && \
### DOWNLOAD PROXY FILE
PROTON_URL='https://raw.githubusercontent.com/ProtonVPN/scripts/master/update-resolv-conf.sh' && \
wget --no-check-certificate --no-cache --no-cookies $PROTON_URL -q -O /etc/openvpn/update-resolv-conf && \
### START ENTRYPOINT FILE
echo '#!/bin/sh -e' > $STARTUP && \
echo '### CHECK PROXY...' >> $STARTUP && \
echo 'if [ -z $PROTON ]; then' >> $STARTUP && \
echo '    echo "not using proxy..."' >> $STARTUP && \
echo 'else' >> $STARTUP && \
echo '    echo "install proxy..."' >> $STARTUP && \
echo '    apk update' >> $STARTUP && \
echo '    apk add openvpn openresolv bash' >> $STARTUP && \
echo '    sed -i "s/^auth-user-pass$/auth-user-pass \/opt\/.work\/openvpn\/pass.txt/g" $WORKDIR/openvpn/protonvpn.ovpn' >> $STARTUP && \
echo '    openvpn $WORKDIR/openvpn/protonvpn.ovpn &> /dev/null &' >> $STARTUP && \
echo '    sleep 10' >> $STARTUP && \
echo 'fi' >> $STARTUP && \
echo '### START GAGA...' >> $STARTUP && \
echo 'if [ -z $TOKENG ]; then' >> $STARTUP && \
echo '    echo "GAGA TOKEN not exists..."' >> $STARTUP && \
echo 'else' >> $STARTUP && \
echo '    echo "GAGA TOKEN replace..."' >> $STARTUP && \
echo '    sed -i "s/token = '\'''\''/token = '\''$TOKENG'\''/g;s/INFO/ERROR/g" $WORKDIR/gaga/root_conf/default.toml' >> $STARTUP && \
echo '    echo "GAGA starting..."' >> $STARTUP && \
echo '    $WORKDIR/gaga/gaganode &' >> $STARTUP && \
echo 'fi' >> $STARTUP && \
echo '### START MESON...' >> $STARTUP && \
echo 'if [ -z $TOKENM ]; then' >> $STARTUP && \
echo '    echo "MESON TOKEN not exists..."' >> $STARTUP && \
echo 'else' >> $STARTUP && \
echo '    echo "MESON TOKEN replace..."' >> $STARTUP && \
echo '    $WORKDIR/meson/meson_cdn config set --token=$TOKENM --https_port=$PORT --cache.size=$SIZE --log.level=ERROR' >> $STARTUP && \
echo '    echo "MESON starting..."' >> $STARTUP && \
echo '    $WORKDIR/meson/meson_cdn &' >> $STARTUP && \
echo 'fi' >> $STARTUP && \
echo 'wait -n' >> $STARTUP && \
echo 'exit $?' >> $STARTUP && \
chmod +x $STARTUP /etc/openvpn/update-resolv-conf && \
rm -rf /var/cache/apk/*

ENTRYPOINT ["sh", "-c", "$STARTUP"]
