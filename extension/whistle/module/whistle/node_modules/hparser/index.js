var util = require('./lib/util');
var parse = require('./lib/parse');;

exports.getRawHeaderNames = util.getRawHeaderNames;
exports.formatHeaders = util.formatHeaders;
exports.toMultipart = util.toMultipart;
exports.toMultiparts = util.toMultiparts;
exports.parse = parse;
exports.getRawHeaders = parse.getRawHeaders;
exports.MultipartParser = require('./lib/multipart-parser');
