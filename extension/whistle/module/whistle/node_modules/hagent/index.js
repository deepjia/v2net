var getServer = require('./lib/get-server');
var ServerAgent = require('./lib/server-agent');

exports.getServer = getServer;
exports.serverAgent = new ServerAgent();
exports.serverAgent.ServerAgent = ServerAgent;
exports.create = getServer.create;
exports.agent = require('./lib/agent');