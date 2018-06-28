var tape = require('tape');
var net = require('net');
var http = require('http');
var https = require('https');
var sni = require('./');

tape('http', t => {
  t.plan(1);

  var tcpServer = net.createServer(socket => {
    socket.once('data', data => {
      t.equal(sni(data), null);
      socket.destroy();
      tcpServer.close();
    });
  });

  tcpServer.listen('9000', () => {
    http.request({
      hostname: 'localhost',
      port: '9000',
    })
      .on('error', () => {})
      .end();
  });
});

tape('https', t => {
  t.plan(1);

  var tcpServer = net.createServer(socket => {
    socket.once('data', data => {
      t.equal(sni(data), 'localhost');
      socket.destroy();
      tcpServer.close();
    });
  });

  tcpServer.listen('9000', () => {
    https.request({
      hostname: 'localhost',
      port: '9000',
    })
      .on('error', () => {})
      .end();
  });
});