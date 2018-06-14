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
System tray menu:

![2018-06-12 9 37 24](https://user-images.githubusercontent.com/1452602/41293869-126d75f6-6e89-11e8-86a3-a1854d9c6abc.png)

Show [whistle](https://github.com/avwo/whistle) dashboard page in built-in browser:

![2018-06-10 12 45 22](https://user-images.githubusercontent.com/1452602/41194011-ba955c06-6c47-11e8-9419-3795d344de15.png)

## Prerequisites
(If only you want to use the integrated whistle extension,) Node.js is needed.

Install Node.js with [Homebrew](https://brew.sh/):

```bash
brew install node
# or:
# brew install node@8
```

Or download installer from <https://nodejs.org/en/>

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

Remember to backup config before manual upgrade.

## Customization

1. Open `Extension Folder`

2. Enter/Create specific `Extension Directroy`

3. Modify/Create `extension.json`

   *bin:* Main binary of extensions.

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
   brew install python
   git clone https://github.com/deepjia/v2net.git
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python setup.py py2app
   ```