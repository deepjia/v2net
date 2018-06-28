var sni = require('./')
  , net = require('net');

net.createServer(function(socket) {
  socket.once('data', function(data) {
    if (sni(data) === null) {
      throw new Error('Invalid protocol')
    }
    var start = Date.now();
    for(var i = 0; i < 1000000; i++)
      sni(data);
    console.log(Date.now() - start + ' ms');
  });
}).listen(9000);

console.log('open a tls connection to localhost:9000 to run the benchmark');