# sni

Get the Server Name Indication of a raw TLS stream (without Node's TLS module)

## Installation
```
npm install sni
```

## Usage
```js
var sni = require("sni")
  , net = require("net");

net.createServer(function(socket) {
    socket.once("data", function(data) { // Listen on the HELLO packet
        console.log(sni(data)); // www.example.com or null if no servername was found
    });
}).listen(443); // Listen on the HTTPS port
```

## Benchmark
1,000,000 rounds took me 157 ms.
Test it for yourself with `npm run bench`.

## Why?
Because I wanted to route my HTTPS streams without actually encoding them with
Node's TLS module.

## Note
It is recommended that you attempt to determine if your data actually _is_ a TLS client hello before attempting to extract the SNI. A library to do just such a thing can be found [here](https://github.com/jessetane/is-tls-client-hello).

## License
MIT