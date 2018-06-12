# V2Net
[![Build Status](https://travis-ci.org/deepjia/v2net.svg?branch=master)](https://travis-ci.org/deepjia/v2net)

## Introduction
V2Net is a network assistant tool for macOS.

Some popular network tools are integrated, with the ability of adding new extensions without coding:

* Proxy:
[ss-libev](https://github.com/shadowsocks/shadowsocks-libev)
[v2ray](https://www.v2ray.com)
[gost](https://github.com/ginuerzh/gost/tree/2.6)
* Bypass:
[privoxy](https://www.privoxy.org)
[gost](https://github.com/ginuerzh/gost/tree/2.6)
* Capture:
[whistle](https://github.com/avwo/whistle)

This is an alpha version.

## Snapshot
![2018-06-12 9 37 24](https://user-images.githubusercontent.com/1452602/41293869-126d75f6-6e89-11e8-86a3-a1854d9c6abc.png)

![2018-06-10 12 45 22](https://user-images.githubusercontent.com/1452602/41194011-ba955c06-6c47-11e8-9419-3795d344de15.png)

## Prerequisites
To use the integrated whistle extension, Node.js is needed.

Install Node.js with [homebrew](https://brew.sh/):

```bash
brew install node
# or:
# brew install node@8
```

Or download installer from <https://nodejs.org/en/>

## Install
Download latest release:

<https://github.com/deepjia/v2net/releases>

Unpack and drag `V2Net.app` to `Application` folder.

## Usage
Example of profile.ini
```ini
[General]
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local, ::ffff:0:0:0:0/1, ::ffff:128:0:0:0/1
# proxy/bypass/capture: extensions selected last time
proxy = ✈️Beijing
bypass = 🚄Privoxy
capture =
# system: whether V2Net is set as system proxy last time
system = false
Port = 8014
InnerPortProxy = 8114
InnerPortBypass = 8214

[Proxy]
# The order of values is defined in "keys" field of extension.json in extension folders
# name = extension_name, *values
✈️Beijing = ss, server_ip, 12345, chacha20-ietf-poly1305, password, 60, true
🇨🇳Shenzhen = vmess, example.org, 443, /ws, uuid
🇨🇳Hangzhou = gost, ss, chacha20:password@server_ip, 12345
🇯🇵Tokyo = gost, socks5, server_ip, 12345
🇺🇸Denver = gost, http, server_ip, 12345

[Bypass]
# Same as proxy, privoxy preferred
🚄Privoxy = privoxy, , 127.0.0.1, , privoxy.txt
#🚄Gost = gost, , 127.0.0.1, , gost.txt

[Capture]
# Same as proxy
🛠️Whistle = whistle

```