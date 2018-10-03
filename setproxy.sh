#!/bin/bash

services=$(networksetup -listnetworkserviceorder | grep 'Hardware Port')
#while [ -z "$currentservice" ]; do
while read line; do
    sname=$(echo $line | sed -E "s/.*Port: ([^,]*).*/\1/")
    sdev=$(echo $line | sed -E "s/.*Device: ([a-z]*[0-9])\)/\1/")
    if [ -n "$sdev" ]; then
        if ifconfig $sdev 2>&1| grep 'status: active' > /dev/null
        then
            currentservice="$sname"
            case "$1" in
                pacon)
                    networksetup -setautoproxyurl "$currentservice" $2
                    ;;
                pacoff)
                    networksetup -setautoproxystate "$currentservice" off
                    ;;
                httpon)
                    networksetup -setwebproxy "$currentservice" 127.0.0.1 $2
                    networksetup -setsecurewebproxy "$currentservice" 127.0.0.1 $2
                    ;;
                httpoff)
                    networksetup -setwebproxystate "$currentservice" off
                    networksetup -setsecurewebproxystate "$currentservice" off
                    ;;
                socks5on)
                    networksetup -setsocksfirewallproxy "$currentservice" 127.0.0.1 $2
                    ;;
                socks5off)
                    networksetup -setsocksfirewallproxystate "$currentservice" off
                    ;;
                ?)
                    networksetup -setproxybypassdomains "$currentservice" $*
            esac     
            exit 0
        fi
    fi
done <<< "$(echo "$services")"
#sleep 5
#done
