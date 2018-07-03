# V2Net
[![Build Status](https://travis-ci.org/deepjia/v2net.svg?branch=master)](https://travis-ci.org/deepjia/v2net)

**⚠️ IMPORTANT ⚠️**

I changed names & prerequisites of some extensions in version 0.3.0 (alpha).

Please review your `profile.ini` and satisfy the prerequisites before upgrading.

## Introduction
V2Net is a network assistant tool for macOS.

It focuses on extendability, with all extensions working in a way of proxy chains. 

Some popular network tools are integrated, with the ability of adding new extensions without programming:

* Proxy:
[glider](https://github.com/nadoo/glider)
[gost](https://github.com/ginuerzh/gost/tree/2.6)
[v2ray](https://www.v2ray.com)
[ss-libev](https://github.com/shadowsocks/shadowsocks-libev)
* Bypass:
[glider](https://github.com/nadoo/glider)
[gost](https://github.com/ginuerzh/gost/tree/2.6)
[privoxy](https://www.privoxy.org)
* Capture:
[whistle](https://github.com/avwo/whistle)

This is an **alpha** version.


## Snapshot
System tray menu:

![2018-06-12 9 37 24](https://user-images.githubusercontent.com/1452602/41293869-126d75f6-6e89-11e8-86a3-a1854d9c6abc.png)

Show [whistle](https://github.com/avwo/whistle) dashboard page in built-in browser (removed in 0.4.0, use Safari instead):

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

### ss-libev
Install with [Homebrew](https://brew.sh/):

```bash
brew install shadowsocks-libev
```

Or just use the **glider** extension instead, which is **recommended**.

### v2ray
Install with [Homebrew](https://brew.sh/):

```bash
brew install v2ray/v2ray/v2ray-core
```


## Installation
Download latest release:

<https://github.com/deepjia/v2net/releases>

Unpack and drag `V2Net.app` to `Application` folder.

## Usage
Example of `profile.ini`

```ini
[General]
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local, ::ffff:0:0:0:0/1, ::ffff:128:0:0:0/1
# proxy/bypass/capture: extensions selected last time
proxy =
bypass =
capture =
# system: whether V2Net is set as system proxy last time
system = false
Port = 8014
InnerPortProxy = 8114
InnerPortBypass = 8214

[Proxy]
# The order of values is defined in "keys" field of extension.json in extension folders
# name = extension_name, *values
🇨🇳Eg.ProxyAndBypass(glider)(ss)GliderProxyAndBypass = glider, ss, AEAD_CHACHA20_POLY1305:password@server_ip, 12345, glider.txt
🇨🇳Eg.Proxy(glider)(ss)ExampleProxy = glider, ss, AEAD_AES_256_GCM:password@server_ip, 12345
🇨🇳️Eg.Proxy(ss-libev)(ss)ExampleProxy = ss-libev, server_ip, 12345, chacha20-ietf-poly1305, password
🇨🇳Eg.Proxy(v2ray)(vmess-tls-ws)ExampleProxy = v2ray, example.org, 443, /ws, uuid
🇯🇵Eg.Proxy(gost)(socks5)ExampleProxy = gost, socks5, server_ip, 12345
🇺🇸Eg.Proxy(gost)(http)ExampleProxy = gost, http, server_ip, 8080
🇨🇳Eg.Proxy(gost)(https)ExampleProxy = gost, https, user:password@server_ip, 443

[Bypass]
# Same as proxy
🚄Eg.Bypass(glider)(auto)GliderBypass = glider, , 127.0.0.1, , glider.txt
🚄Eg.Bypass(gost)(auto)GostBypass = gost, , 127.0.0.1, , gost.txt
🚄Eg.Bypass(privoxy)(auto)PrivoxyBypass = privoxy, , 127.0.0.1, , privoxy.txt

[Capture]
# Same as proxy
🛠️Eg.Capture(glider)(auto)Whistle = whistle
# You can also put global proxies here
🛠️Eg.Capture(gost)(http)JMeter = gost, http, 127.0.0.1, 8888
🛠Eg.Capture(gost)(http)Charles = gost, http, 127.0.0.1, 8888
🛠️Eg.Capture(gost)(http)BurpSuite = gost, http, 127.0.0.1, 8080

```

Remember to backup config before manual upgrade.

## Customization

1. Open `Extension Folder`

2. Enter/Create specific `Extension Directroy`

3. Modify/Create `extension.json`

   *bin:* Main binary of extensions.

   *pre*: Preparation command.
   
   *args*: Arguments for binary to start with.

   *url*: Dashboard url for capture extension.

   *exitargs*: Arguments for binary to quit with.(If left blank, binary process  will be stopped when stopping the extension)

   *keys*: Keys to render by [jinja2](http://jinja.pocoo.org), whose values are in `profile.ini`

   *http*: Whether the extension serve as a http proxy.

   *socks5*: Whether the extension serve as a socks5 proxy

   *render*: Render the template files in `Extension Directroy`

   *default*: Default vaules to render.

   ```json
   {
     "bin": "./extension/myext/bin/mybinary",
     "args": "-p {{ ExtensionPort }} -c ./extension/myext/myconfig.ini",
     "url": "http://127.0.0.1:{{ ExtensionPort }}",
     "exitargs": "",
     "keys": ["ServerProtocol", "ServerAddress", "SeverPort", "ServerPassword"],
     "http": false,
     "socks5": true,
     "render": {"mytemplate.jinja": "myconfig.ini"},
     "default": {"ServerAddress":"example.com"}
   }
   ```

   [jinja2](http://jinja.pocoo.org) is used as render engine, which render {{ *key* }} as *values* from the `profile.ini` as well as from *default* values, which also supports logic causes like {{*% if  %*}} {{*% endif %*}}.

   Specially:

      - {{ *ExtensionPort* }} will always be rendered as the proper value depending on your settings in `profile.ini`
      - If an extension is running as a secondary proxy, {{ *ServerPort* }} and {{ *ServerProtocol* }} will be automatically rendered as `http` or `socks5` when left blank.


## Build

```bash
brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/f2a764ef944b1080be64bd88dca9a1d80130c558/Formula/python.rb
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
- [ ] Version check
- [ ] Change profile location
- [ ] Proxy group with connection test