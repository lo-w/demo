# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/ewuxren/.miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/ewuxren/.miniconda3/etc/profile.d/conda.sh" ]; then
        . "/home/ewuxren/.miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/ewuxren/.miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

alias ce="conda env list"
alias ca="conda activate"
alias cda="conda deactivate"

# cmder config
if [[ -f ~/.64adminrc ]]; then source ~/.64adminrc;fi
if [[ "$PWD" =~ (cmder(_mini)?|"$USER"|[wW]indows|[sS]ystem32)$ ]]; then cd;fi
if [[ ! -f /etc/resolv.conf ]]; then echo -e "nameserver 193.181.14.10\nnameserver 193.181.14.11\nnameserver 193.181.14.12" | sudo tee /etc/resolv.conf 2&> /dev/null;fi

# subsystem mkdir config
umask 022

# user alias
#if [[ ! -f ~/.ssh/config ]]; then touch ~/.ssh/config; fi
while read ssh_name
do
    alias $ssh_name="ssh -q $ssh_name"
done < <(awk '/^[h|H]ost/{print $2}' ~/.ssh/config)

(ps aux | pgrep dockerd &> /dev/null)
if [[ $? != 0 ]]; then
    sudo service docker start &> /dev/null
fi

function pf()
{
    # port forwarding
    SOCKET5_COMMAND="ssh -CfnNqT $1"
    if [[ "$1" == "eo" ]]; then
        SOCKET5_COMMAND="ssh -CfnNqT -D 20006 eo4767"
    fi
    SOCKET5_EXIST=$(ps aux | pgrep "$SOCKET5_COMMAND")
    if [[ -z "$SOCKET5_EXIST" ]]; then
        $SOCKET5_COMMAND -o ConnectTimeout=2;
        if [[ $? != 0 ]];then
            echo "$1 NOT OK";
        fi
    fi
}

function tun2socks()
{
    (ip a s tun0 &> /dev/null)
    if [[ $? != 0 ]]; then
        sudo ip tuntap add mode tun dev tun0
        sudo ip link set dev tun0 up
        sudo ip route add 10.196.44.0/22 dev tun0
    fi
}
tun2socks

function se()
{
    (ps aux | pgrep ssh &> /dev/null)
    if [[ $? == 0 ]]; then
        #kill $(ps aux | grep ssh | grep -v grep | awk -F' ' '{print $2}')
	#kill $(ps aux | pgrep ssh | awk -F' ' '{print $2}')
        kill $(ps aux | awk -F' ' '/ssh/{if ($11!="awk") print $2}')
    fi
    pf seli

    (ps aux | pgrep tun2proxy &> /dev/null)
    if [[ $? != 0 ]]; then
        (tun2proxy --tun tun0 --proxy "SOCKS5://127.0.0.1:20002" &> /dev/null &)
    fi

}

export J11_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export CLASSPATH=$:CLASSPATH:$JAVA_HOME/lib/
export PATH=$PATH:$JAVA_HOME/bin
export NODE_PATH=/usr/lib/node_modules
export GOPATH=$HOME/.gopath
#export GOPROXY="http://www-proxy.ericsson.se:8080"
export PATH=$PATH:$GOPATH/bin

#export http_proxy="http://www-proxy.ericsson.se:8080"
#export https_proxy="http://www-proxy.ericsson.se:8080"
