# V2Net
[![Build Status](https://travis-ci.org/deepjia/v2net.svg?branch=master)](https://travis-ci.org/deepjia/v2net)

**⚠️ IMPORTANT ⚠️**

You need to backup profiles before upgrade, if you have a version lower than 0.4.6.

Some settings had been moved from `profile.ini` to `setting.ini` since version 0.5.0 (alpha).


## Introduction
V2Net is a network assistant tool for macOS.

It focuses on extendability, with all extensions working in a way of proxy chains. 

Some popular network tools are integrated, with the ability of adding new extensions without programming:

* Proxy:
[gost](https://github.com/ginuerzh/gost/tree/2.6)
[glider](https://github.com/nadoo/glider)
[v2ray](https://www.v2ray.com)
[ss-libev](https://github.com/shadowsocks/shadowsocks-libev)
* Bypass:
[gost](https://github.com/ginuerzh/gost/tree/2.6)
[glider](https://github.com/nadoo/glider)
[privoxy](https://www.privoxy.org)
* Capture:
[whistle](https://github.com/avwo/whistle)
[mitmproxy/mitmweb](https://mitmproxy.org)
[charles](https://www.charlesproxy.com/)

This is an **alpha** version.


## Snapshot
System tray menu:

![wx20180718-174131](https://user-images.githubusercontent.com/1452602/42873567-e3bd8f76-8ab1-11e8-9bd4-891c7c7d11d0.png)

Choose [mitmproxy](https://mitmproxy.org) CLI tool:

![wx20180718-174810](https://user-images.githubusercontent.com/1452602/42874086-d101982c-8ab2-11e8-96d1-0c774a4a259c.png)

Show [whistle](https://github.com/avwo/whistle) dashboard page in built-in browser (**removed since 0.4.0**, show in Safari instead):

![2018-06-10 12 45 22](https://user-images.githubusercontent.com/1452602/41194011-ba955c06-6c47-11e8-9419-3795d344de15.png)

## Prerequisites
Install prerequisites if only you need the related extension.
### whistle
Node.js and whistle are needed.

Install with [Homebrew](https://brew.sh/):

```bash
brew install node
npm install -g whistle
```

### v2ray
Install with [Homebrew](https://brew.sh/):

```bash
brew install v2ray/v2ray/v2ray-core
```
Currently only vmess+ws+tls support, but you can customize to support more.
For vmess only, **glider** is also a choice.

### ss-libev
Install with [Homebrew](https://brew.sh/):

```bash
brew install shadowsocks-libev
```

Or just use the **gost** (for non-AEAD encryption) or **glider** (for AEAD encryption) extension instead, which are **recommended**.

### privoxy
Install with [Homebrew](https://brew.sh/):

```bash
brew install privoxy
```

Or just use the **gost** or **glider** extension instead, which are **recommended**.

### mitmproxy/mitmweb
Python3 and mitmproxy are needed.

Install mitmproxy with [Homebrew](https://brew.sh/), which will automatically install/upgrade python3:

```bash
brew install mitmproxy
```
Since mitmproxy depends on python3, it will not work if you want to use an older version of python3 from Homebrew, like me. Then you need to download from [official site](https://snapshots.mitmproxy.org/4.0.3/mitmproxy-4.0.3-osx.tar.gz), unpack and move/link binaries to `/usr/local/bin`.

Instead, install whistle which is **recommended**.

### charles
Buy and install [charles](https://www.charlesproxy.com/).

## Installation
Download latest release:

<https://github.com/deepjia/v2net/releases>

Unpack and drag `V2Net.app` to `Application` folder.

Open `Application` folder, right click on `V2Net.app`, hold `option` key, click `Open`.

## Usage
(Optional) Click `Edit Setting File`, set `custom-path` to store config files. In this way, your config can sync with iCloud Drive/Dropbox, etc.

Example of `setting.ini`:

```ini
[Global]
custom-path =
# PATH in env
env-path = /usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
# proxy/bypass/capture: extensions selected last time, will be filled automatically
proxy =
bypass =
capture =
# system: whether V2Net is set as system proxy last time, will be filled automatically
system = false
# Port settings
port = 8014
port-proxy = 8114
port-bypass = 8214

```

Click `Open Profile Folder`, and edit your profiles.

Example of `profile.ini`:

```ini
[General]
loglevel = INFO
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local, ::ffff:0:0:0:0/1, ::ffff:128:0:0:0/1

[Proxy]
# The order of values is defined in "keys" field of extension.json in extension folders
# name = extension_name, *values
# For gost and glider, you can combine proxy and bypass:
🇨🇳Eg.ProxyAndBypass(glider)(ss)ExampleProxy = glider, ss, AEAD_CHACHA20_POLY1305:password@server_ip, 12345, glider.txt
🇯🇵Eg.ProxyAndBypass(gost)(ss)ExampleProxy = gost, ss, chacha20:password@server_ip, 12345, gost.txt
🇨🇳Eg.ProxyAndBypass(glider)(vmess)ExampleProxy = glider, vmess, [security:]uuid@server_ip, 12345?alterID=num, glider.txt
# gost and glider support RFC protocols:
🇯🇵Eg.Proxy(gost)(socks5)ExampleProxy = gost, socks5, server_ip, 12345
🇺🇸Eg.Proxy(gost)(http)ExampleProxy = gost, http, server_ip, 8080
🇨🇳Eg.Proxy(gost)(https)ExampleProxy = gost, https, user:password@server_ip, 443
# for ss protocol, gost may have better stablity than glider, but do not support AEAD
# gost support:
#    aes-128-cfb, aes-192-cfb, aes-256-cfb, bf-cfb, cast5-cfb, des-cfb, rc4-md5, rc4-md5-6, chacha20, salsa20, rc4, table
# glider support:
#    AEAD_AES_128_GCM AEAD_AES_192_GCM AEAD_AES_256_GCM AEAD_CHACHA20_POLY1305 AES-128-CFB AES-128-CTR AES-192-CFB AES-192-CTR AES-256-CFB AES-256-CTR CHACHA20-IETF XCHACHA20
🇯🇵Eg.Proxy(gost)(ss)ExampleProxy = gost, ss, chacha20:password@server_ip, 12345, gost.txt
🇨🇳Eg.Proxy(glider)(ss)ExampleProxy = glider, ss, AEAD_AES_256_GCM:password@server_ip, 12345
# Other extensions need prerequisites:
🇨🇳️Eg.Proxy(ss-libev)(ss)ExampleProxy = ss-libev, server_ip, 12345, chacha20-ietf-poly1305, password
🇨🇳Eg.Proxy(v2ray)(vmess-tls-ws)ExampleProxy = v2ray, example.org, 443, /ws, ID, alterID

[Bypass]
# Same as proxy, gost and glider are preferred:
🚄Eg.Bypass(glider)(auto)GliderBypass = glider, , 127.0.0.1, , glider.txt
🚄Eg.Bypass(gost)(auto)GostBypass = gost, , 127.0.0.1, , gost.txt
🚄Eg.Bypass(privoxy)(auto)PrivoxyBypass = privoxy, , 127.0.0.1, , privoxy.txt

[Capture]
# Same as proxy, whistle recommended:
🛠️Eg.Capture(whistle)(auto)Whistle = whistle
🛠️Eg.Capture(mitmweb)(auto)mitmproxy = mitmproxy
🛠️Eg.Capture(mitmweb)(auto)mitmweb = mitmweb
🛠️Eg.Capture(whistle)(auto)WhistleCustomRule = whistle, whistle.txt
# You can also put global proxies here:
🛠️Eg.Capture(gost)(http)JMeter = gost, http, 127.0.0.1, 8888
🛠Eg.Capture(gost)(http)Charles = gost, http, 127.0.0.1, 8888
🛠️Eg.Capture(gost)(http)BurpSuite = gost, http, 127.0.0.1, 8080

```

## Customization

1. Open `Extension Folder`

2. Enter/Create specific `Extension Directroy`

3. Modify/Create `extension.json`

   *bin:* Main binary of extensions.

   *pre*: Preparation command.
   
   *args*: Arguments for binary to start with.

   *exitargs*: Arguments for binary to quit with.(If left blank, binary process  will be stopped when stopping the extension)

   *url*: Dashboard url for capture extension.

   *keys*: Keys to render by [jinja2](http://jinja.pocoo.org), whose values are in `profile.ini`

   *http*: Whether the extension serve as a http proxy.

   *socks5*: Whether the extension serve as a socks5 proxy

   *render*: Render the template files in `Extension Directroy`

   *default*: Default vaules to render.

   ```json
   {
     "bin": "{{ ExtensionDir }}/bin/mybinary",
     "args": "-p {{ ExtensionPort }} -c '{{ TempDir }}/myconfig.ini'",
     "exitargs": "",
     "url": "http://127.0.0.1:{{ ExtensionPort }}",
     "keys": ["ServerProtocol", "ServerAddress", "SeverPort", "ServerPassword"],
     "http": false,
     "socks5": true,
     "render": {"{{ ExtensionDir }}/mytemplate.jinja": "{{ TempDir }}/myconfig.ini"},
     "default": {"ServerAddress":"example.com"}
   }
   ```

   [jinja2](http://jinja.pocoo.org) is used as render engine, which render {{ *key* }} as *values* from the `profile.ini` as well as from *default* values, which also supports logic causes like {*% if  %*} {*% endif %*}.

   Specially:

      - {{ *ExtensionPort* }} will always be rendered as the proper value depending on your settings in `profile.ini`
      - {{ *ExtensionDir* }} and {{ *TempDir* }} are reserved.
      - If an extension is running as a secondary proxy, {{ *ServerPort* }} and {{ *ServerProtocol* }} will be automatically rendered as `http` or `socks5` when left blank.


## Build

```bash
# PyInstaller & py2app do not support python 3.7
brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb
brew switch brew switch python 3.6.5_1
git clone https://github.com/deepjia/v2net.git
cd v2net
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller v2net.spec
# You can also use py2app
# pip install py2app
# python setup.py py2app
```

## Todos
- [ ] Performance tuning
- [ ] Proxy group with connection test