# node-pac
[![node version](https://img.shields.io/badge/node.js-%3E=_0.10-green.svg?style=flat-square)](http://nodejs.org/download/)
[![build status](https://img.shields.io/travis/imweb/node-pac.svg?style=flat-square)](https://travis-ci.org/imweb/node-pac)
[![Test coverage](https://codecov.io/gh/imweb/node-pac/branch/master/graph/badge.svg?style=flat-square)](https://codecov.io/gh/imweb/node-pac)
[![David deps](https://img.shields.io/david/imweb/node-pac.svg?style=flat-square)](https://david-dm.org/imweb/node-pac)
[![License](https://img.shields.io/npm/l/node-pac.svg?style=flat-square)](https://www.npmjs.com/package/node-pac)

Node版pac脚本解析器。

# 安装

	npm install --save node-pac

# 用法

	var Pac = require('node-pac');
	var pac = new Pac('https://raw.githubusercontent.com/imweb/node-pac/master/test/scripts/normal.pac');

	pac.FindProxyForURL('http://9v.cn/index.html', function(err, res)　{
		console.log(err, res);
	});

# API
1. `Pac`: 构造函数，可以通过`new Pac(options)`或`Pac(options)`两种方式生成Pac对象，其中： options为pac文件内容、本地的pac文件路径、或者http[s]链接，或者为以下对象：

		｛
			url: 'pac文件内容、本地的pac文件路径、或者http[s]链接',
			timeout: 'url为http[s]链接时才生效，设置请求的超时时间，默认5000ms',
			cacheTime: '缓存pac脚本的时间，在缓存时间内，node-pac不会重新拉起pac脚本'
			//默认为30s，超过这个时间用户再请求时会重新拉取脚本
			//也可以通过下面的pac.forceUpdate()强制刷新

		｝

2. `pac.FindProxyForURL(url, cb)`或者 `pac.findProxyForURL(url, cb)`: 通过请求url异步获取该请求的代理设置，cb的参数及返回值如下

		function cb(err, res){
			//err: 解析出错时的错误对象
			//res: 解析成功返回的代理设置，如：PROXY 127.0.0.1:8080; 
			//或 SOCKS 127.0.0.1:1080;
		}

	PS: 如果解析过程出错，按实际情况给出提示，或者直接默认为`DIRECT;`

3. `pac.FindWhistleProxyForURL(url, cb)`或者 `pac.findWhistleProxyForURL(url, cb)`: 通过请求url异步获取该请求的[whistle](https://github.com/avwo/whistle)代理设置，cb的参数及返回值如下

		function cb(err, res){
			//err: 解析出错时的错误对象
			//res: 解析成功返回的代理设置，如：proxy://127.0.0.1:8080 
			//或 socks://127.0.0.1:1080
		}

4. `pac.update()`: 重新获取本地或远程的pac脚本并刷新pac对象内部解析脚本，如果获取失败继续使用上一个缓存的内容，一般node-pac会自动更新，无需手动调用该方法，除非程序能确切获取脚本更新的事件或确实需要强制更新才需使用该方法。

5. `pac.forceUpdate()`: 强制重新获取本地或远程的pac脚本并刷新pac对象内部解析脚本，如果获取失败调用`pac.FindProxyForURL(url, cb)`时会把错误传给cb，一般node-pac会自动更新，无需手动调用该方法，除非程序能确切获取脚本更新的事件或确实需要强制更新才需使用该方法。

# License
[MIT](https://github.com/imweb/node-pac/blob/master/LICENSE)