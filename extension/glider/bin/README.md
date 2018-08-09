# [glider](https://github.com/nadoo/glider)

[![Build Status](https://img.shields.io/travis/nadoo/glider.svg?style=flat-square)](https://travis-ci.org/nadoo/glider)
[![Go Report Card](https://goreportcard.com/badge/github.com/nadoo/glider?style=flat-square)](https://goreportcard.com/report/github.com/nadoo/glider)
[![GitHub tag](https://img.shields.io/github/tag/nadoo/glider.svg?style=flat-square)](https://github.com/nadoo/glider/releases)
[![GitHub release](https://img.shields.io/github/release/nadoo/glider.svg?style=flat-square)](https://github.com/nadoo/glider/releases)

glider is a forward proxy with multiple protocols support, and also a dns forwarding server with ipset management features(like dnsmasq).

we can set up local listeners as proxy servers, and forward requests to internet via forwarders.

```bash
                |Forwarder ----------------->|
   Listener --> |                            | Internet
                |Forwarder --> Forwarder->...|
```

## Features

Listen (local proxy server):

- Socks5 proxy(tcp&udp)
- Http proxy(tcp)
- SS proxy(tcp&udp)
- Linux transparent proxy(iptables redirect)
- TCP tunnel
- UDP tunnel
- UDP over TCP tunnel

Forward (local proxy client/upstream proxy server):

- Socks5 proxy(tcp&udp)
- Http proxy(tcp)
- SS proxy(tcp&udp&uot)
- SSR proxy(tcp)
- VMess proxy(tcp)
- TLS, use it together with above proxy protocols(tcp)
- Websocket, use it together with above proxy protocols(tcp)

DNS Forwarding Server (udp2tcp):

- Listen on UDP and forward dns requests to remote dns server in TCP via forwarders
- Specify different upstream dns server based on destinations(in rule file)
- Tunnel mode: forward to a fixed upstream dns server
- Add resolved IPs to proxy rules
- Add resolved IPs to ipset
- DNS cache
- Custom dns record

IPSet Management:

- Add ip/cidrs from rule files on startup
- Add resolved ips for domains from rule files by dns forwarding server

General:

- Http and socks5 on the same port
- Forward chain
- HA or RR strategy for multiple forwarders
- Periodical proxy checking
- Rule proxy based on destinations: [Config Examples](config/examples)

TODO:

- [ ] IPv6 support in ipset manager
- [ ] Transparent UDP proxy (iptables tproxy)
- [ ] Performance tuning
- [ ] TUN/TAP device support
- [ ] SSH tunnel support (maybe)

## Install

Binary:

- [https://github.com/nadoo/glider/releases](https://github.com/nadoo/glider/releases)

Go Get (requires **Go 1.10+** ):

```bash
go get -u github.com/nadoo/glider
```

ArchLinux:

```bash
sudo pacman -S glider
```

## Run

command line:

```bash
glider -listen :8443 -verbose
```

config file:

```bash
glider -config CONFIGPATH
```

command line with config file:

```bash
glider -config CONFIGPATH -listen :8080 -verbose
```

## Usage

```bash
glider v0.6.6 usage:
  -checkduration int
        proxy check interval(seconds) (default 30)
  -checkwebsite string
        proxy check HTTP(NOT HTTPS) website address, format: HOST[:PORT], default port: 80 (default "www.apple.com")
  -config string
        config file path
  -dns string
        dns forwarder server listen address
  -dnsmaxttl int
        maximum TTL value for entries in the CACHE(seconds) (default 1800)
  -dnsminttl int
        minimum TTL value for entries in the CACHE(seconds)
  -dnsrecord value
        custom dns record, format: domain/ip
  -dnsserver value
        remote dns server
  -dnstimeout int
        timeout value used in multiple dnsservers switch(seconds) (default 3)
  -forward value
        forward url, format: SCHEME://[USER|METHOD:PASSWORD@][HOST]:PORT?PARAMS[,SCHEME://[USER|METHOD:PASSWORD@][HOST]:PORT?PARAMS]
  -ipset string
        ipset name
  -listen value
        listen url, format: SCHEME://[USER|METHOD:PASSWORD@][HOST]:PORT?PARAMS
  -rulefile value
        rule file path
  -rules-dir string
        rule file folder
  -strategy string
        forward strategy, default: rr (default "rr")
  -verbose
        verbose mode

Available Schemes:
  mixed: serve as a http/socks5 proxy on the same port. (default)
  ss: ss proxy
  socks5: socks5 proxy
  http: http proxy
  ssr: ssr proxy
  vmess: vmess proxy
  tls: tls transport
  ws: websocket transport
  redir: redirect proxy. (used on linux as a transparent proxy with iptables redirect rules)
  tcptun: tcp tunnel
  udptun: udp tunnel
  uottun: udp over tcp tunnel

Available schemes for different modes:
  listen: mixed ss socks5 http redir tcptun udptun uottun
  forward: ss socks5 http ssr vmess tls ws

SS scheme:
  ss://method:pass@host:port

Available methods for ss:
  AEAD_AES_128_GCM AEAD_AES_192_GCM AEAD_AES_256_GCM AEAD_CHACHA20_POLY1305 AES-128-CFB AES-128-CTR AES-192-CFB AES-192-CTR AES-256-CFB AES-256-CTR CHACHA20-IETF XCHACHA20
  NOTE: chacha20-ietf-poly1305 = AEAD_CHACHA20_POLY1305

SSR scheme:
  ssr://method:pass@host:port?protocol=xxx&protocol_param=yyy&obfs=zzz&obfs_param=xyz

VMess scheme:
  vmess://[security:]uuid@host:port?alterID=num

Available securities for vmess:
  none, aes-128-gcm, chacha20-poly1305

TLS scheme:
  tls://host:port[?skipVerify=true]

TLS with a specified proxy protocol:
  tls://host:port[?skipVerify=true],scheme://
  tls://host:port[?skipVerify=true],http://[user:pass@]
  tls://host:port[?skipVerify=true],socks5://[user:pass@]
  tls://host:port[?skipVerify=true],vmess://[security:]uuid@?alterID=num

Websocket scheme:
  ws://host:port[/path]

Websocket with a specified proxy protocol:
  ws://host:port[/path],scheme://
  ws://host:port[/path],http://[user:pass@]
  ws://host:port[/path],socks5://[user:pass@]
  ws://host:port[/path],vmess://[security:]uuid@?alterID=num

TLS and Websocket with a specified proxy protocol:
  tls://host:port[?skipVerify=true],ws://[@/path],scheme://
  tls://host:port[?skipVerify=true],ws://[@/path],http://[user:pass@]
  tls://host:port[?skipVerify=true],ws://[@/path],socks5://[user:pass@]
  tls://host:port[?skipVerify=true],ws://[@/path],vmess://[security:]uuid@?alterID=num

DNS forwarding server:
  dns=:53
  dnsserver=8.8.8.8:53
  dnsserver=1.1.1.1:53
  dnsrecord=www.example.com/1.2.3.4
  dnsrecord=www.example.com/2606:2800:220:1:248:1893:25c8:1946

Available forward strategies:
  rr: Round Robin mode
  ha: High Availability mode

Config file format(see `glider.conf.example` as an example):
  # COMMENT LINE
  KEY=VALUE
  KEY=VALUE
  # KEY equals to command line flag name: listen forward strategy...

Examples:
  glider -config glider.conf
    -run glider with specified config file.

  glider -config glider.conf -rulefile office.rule -rulefile home.rule
    -run glider with specified global config file and rule config files.

  glider -listen :8443
    -listen on :8443, serve as http/socks5 proxy on the same port.

  glider -listen ss://AEAD_CHACHA20_POLY1305:pass@:8443
    -listen on 0.0.0.0:8443 as a ss server.

  glider -listen socks5://:1080 -verbose
    -listen on :1080 as a socks5 proxy server, in verbose mode.

  glider -listen http://:8080 -forward socks5://127.0.0.1:1080
    -listen on :8080 as a http proxy server, forward all requests via socks5 server.

  glider -listen redir://:1081 -forward ss://method:pass@1.1.1.1:8443
    -listen on :1081 as a transparent redirect server, forward all requests via remote ss server.

  glider -listen redir://:1081 -forward "ssr://method:pass@1.1.1.1:8444?protocol=a&protocol_param=b&obfs=c&obfs_param=d"
    -listen on :1081 as a transparent redirect server, forward all requests via remote ssr server.

  glider -listen redir://:1081 -forward "tls://1.1.1.1:443,vmess://security:uuid@?alterID=10"
    -listen on :1081 as a transparent redirect server, forward all requests via remote tls+vmess server.

  glider -listen redir://:1081 -forward "ws://1.1.1.1:80,vmess://security:uuid@?alterID=10"
    -listen on :1081 as a transparent redirect server, forward all requests via remote ws+vmess server.

  glider -listen tcptun://:80=2.2.2.2:80 -forward ss://method:pass@1.1.1.1:8443
    -listen on :80 and forward all requests to 2.2.2.2:80 via remote ss server.

  glider -listen udptun://:53=8.8.8.8:53 -forward ss://method:pass@1.1.1.1:8443
    -listen on :53 and forward all udp requests to 8.8.8.8:53 via remote ss server.

  glider -listen uottun://:53=8.8.8.8:53 -forward ss://method:pass@1.1.1.1:8443
    -listen on :53 and forward all udp requests via udp over tcp tunnel.

  glider -listen socks5://:1080 -listen http://:8080 -forward ss://method:pass@1.1.1.1:8443
    -listen on :1080 as socks5 server, :8080 as http proxy server, forward all requests via remote ss server.

  glider -listen redir://:1081 -dns=:53 -dnsserver=8.8.8.8:53 -forward ss://method:pass@server1:port1,ss://method:pass@server2:port2
    -listen on :1081 as transparent redirect server, :53 as dns server, use forward chain: server1 -> server2.

  glider -listen socks5://:1080 -forward ss://method:pass@server1:port1 -forward ss://method:pass@server2:port2 -strategy rr
    -listen on :1080 as socks5 server, forward requests via server1 and server2 in round robin mode.

  glider -verbose -dns=:53 -dnsserver=8.8.8.8:53 -dnsrecord=www.example.com/1.2.3.4
    -listen on :53 as dns server, forward dns requests to 8.8.8.8:53, return 1.2.3.4 when resolving www.example.com.
```

## Advanced Usage

- [ConfigFile](config)
  - [glider.conf.example](config/glider.conf.example)
  - [office.rule.example](config/rules.d/office.rule.example)
- [Examples](config/examples)
  - [transparent proxy with dnsmasq](config/examples/8.transparent_proxy_with_dnsmasq)
  - [transparent proxy without dnsmasq](config/examples/9.transparent_proxy_without_dnsmasq)

## Service

- systemd: [https://github.com/nadoo/glider/blob/master/systemd/](https://github.com/nadoo/glider/blob/master/systemd/)

## Links

- [go-ss2](https://github.com/shadowsocks/go-shadowsocks2): ss protocol support
- [conflag](https://github.com/nadoo/conflag): command line and config file parse support
- [ArchLinux](https://www.archlinux.org/packages/community/x86_64/glider): a great linux distribution with glider pre-built package
