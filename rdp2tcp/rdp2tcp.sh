#!/bin/bash -e

if [[ -z $RHOST || -z $RUSER || -z $RPASS || -z $RDP2TCP || -z $REMOTE ]]; then
    echo "missing needed params..."
    exit 1
fi

# $(ping -w 1 -qc 1 $RHOST 2>&1 >/dev/null)
# if [[ $? != 0 ]];then
#     echo "$RHOST unreachable..." 
#     exit 1
# fi

rm -f /tmp/.X*-lock
Xvfb $DISPLAY -pixdepths 1 -screen 0 200x100x24 &> /dev/null &
sleep 1

# start freerdp
echo "start    freerdp service..."
if [[ -z $DOMAIN ]]; then
    xfreerdp /cert:tofu /smart-sizing:35x30 -themes -wallpaper +compression /compression-level:2 /rdp2tcp:$WORKDIR/client /v:"$RHOST" /u:"$RUSER" /p:"$RPASS" &> /dev/null &
else
    xfreerdp /cert:tofu /smart-sizing:35x30 -themes -wallpaper +compression /compression-level:2 /rdp2tcp:$WORKDIR/client /v:"$RHOST" /u:"$RUSER" /p:"$RPASS" /d:"$DOMAIN" &> /dev/null &
fi

# check freerdp
for i in {1..10}; do
    freerdp_window=$(xdotool search --class FreeRDP | head -n 1);
    [[ -n $freerdp_window ]] && break
    sleep 1;
done

if [[ -z $freerdp_window ]]; then
    echo "xfreerdp started failed..."
    exit 1
fi

# press enter to login window
xdotool key --window $freerdp_window Return &> /dev/null

# register rdp2tcp tunnel
echo "register rdp2tcp tunnel ..."
sleep 1
exec 3<>/dev/tcp/127.0.0.1/8477
echo -e "$RDP2TCP" >&3
REPLY=$(cat <&3)
# close connection
exec 3>&-
exec 3<&-

if [[ $(echo $REPLY | awk '/registered/{print $NF}') != "registered" ]]; then
    echo "rdp2tcp register failed..."
    exit 1
fi

# start remote process
echo "start    remote  service..."
IFS=':' read -r -a r_list <<< $REMOTE
sleep 1
xdotool key  --window $freerdp_window Super+r &> /dev/null
xdotool type --window $freerdp_window "${r_list[0]}" &> /dev/null
xdotool key  --window $freerdp_window "shift+semicolon" &> /dev/null
xdotool type --window $freerdp_window "${r_list[1]}" &> /dev/null
xdotool key  --window $freerdp_window Return &> /dev/null

sleep 3
xdotool key  --window $freerdp_window Super+Down &> /dev/null
