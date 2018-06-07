# pipestream
pipestream用于管理stream拼接串，无需按顺序依次pipe stream，且可以通过回调的方式动态插入stream，通过pipestream拼接的stream串可以作为一个对象传递。

# Installation
	$ npm install pipestream

#Example

- `pipeStream.xxx(dest, pipeOpts)` 如果设置了`pipeOpts = {end: false}`，上一个流执行结束后不会触发当前dest的end事件，但会触发dest的ending事件
- `pipeStream.pipe`一定要在最后调用，因为执行完pipeStream.pipe，再执行 `prepend, addHead`, `add`, `addTail`, `append` 对当前的stream串不起作用。
	
		var PipeStream = require('pipestream');
		var Transform = require('stream').Transform;
		
		/**测试prepend, addHead, add, addTail, append方法**/
		
		var pipeStream = new PipeStream();
		
		//1. //pipeStream.wrapStream(process.stdin); //PipeStream.wrap(process.stdin);
		pipeStream.wrapStream(process.stdout, true); //PipeStream.wrap(process.stdout, true);
		//2. //process.stdin.pipe(pipeStream);
		//3. //pipeStream.dest(process.stdout);
		
		var prepend = new Transform();
		prepend._transform = function(chunk, encoding, cb) {
			console.log('---------prepend-------');
			cb(null, chunk);
		};
		
		var addHead = new Transform();
		addHead._transform = function(chunk, encoding, cb) {
			console.log('---------addHead-------');
			cb(null, chunk);
		};
		
		var add = new Transform();
		add._transform = function(chunk, encoding, cb) {
			console.log('---------add-------');
			cb(null, chunk);
		};
		
		var addTail = new Transform();
		addTail._transform = function(chunk, encoding, cb) {
			console.log('---------addTail-------');
			cb(null, chunk);
		};
		
		var append = new Transform();
		append._transform = function(chunk, encoding, cb) {
			console.log('---------append-------');
			cb(null, chunk);
		};
		
		pipeStream.add(add/*, pipeOpts*/);
		pipeStream.addTail(addTail/*, pipeOpts*/);
		pipeStream.addHead(addHead/*, pipeOpts*/);
		pipeStream.prepend(prepend/*, pipeOpts*/);
		pipeStream.append(append/*, pipeOpts*/);
		
		//动态往stream串前面插入stream对象，放在头部最后一个
		pipeStream.addHead(function(src, next) {
			var dest = new Transform();
			dest._transform = function(chunk, encoding, cb) {
				console.log('---------async addHead-------');
				cb(null, chunk);
			};
			
			setTimeout(function() {
				next(src.pipe(dest));
			}, 1000);
		});
		
		//动态往stream串插入stream对象
		pipeStream.add(function(src, next) {
			var dest = new Transform();
			dest._transform = function(chunk, encoding, cb) {
				console.log('---------async add-------');
				cb(null, chunk);
			};
			
			setTimeout(function() {
				next(src.pipe(dest));
			}, 2000);
		});
		
		//动态往stream串尾部插入stream对象，放在尾部第一个
		pipeStream.addTail(function(src, next) {
			var dest = new Transform();
			dest._transform = function(chunk, encoding, cb) {
				console.log('---------async addTail-------');
				cb(null, chunk);
			};
			
			setTimeout(function() {
				next(src.pipe(dest));
			}, 3000);
		});
		
		//动态往stream串尾部插入stream对象，放在尾部最后一个
		pipeStream.append(function(src, next) {
			var dest = new Transform();
			dest._transform = function(chunk, encoding, cb) {
				console.log('---------async append-------');
				cb(null, chunk);
			};
			
			setTimeout(function() {
				next(src.pipe(dest));
			}, 4000);
		});
		
		//动态往stream串前面插入stream对象，放在头部第一个
		pipeStream.prepend(function(src, next) {
			var dest = new Transform();
			dest._transform = function(chunk, encoding, cb) {
				console.log('---------async prepend-------');
				cb(null, chunk);
			};
			
			setTimeout(function() {
				next(src.pipe(dest));
			}, 5000);
		});
		
		//1. //process.stdin.pipe(process.stdout);
		process.stdout.src(process.stdin);
		//2. //pipeStream.pipe(process.stdout);
		//3. //pipeStream.src(process.stdin);
		
		//process.stdin.pipe(pipeStream).pipe(process.stdout);


#API Reference

1. `PipeStream(options)` 跟正常的stream的options参数唯一区别是PipeStream多了一个pipeError的属性，用来标示是否整个pipeStream里面的stream串出现异常时把异常都传递给pipeStream.pipe(dest)里面的dest对象处理。
2. `pipeStreamObj.prepend(dest, pipeOpts)` 把dest放到stream串头部第一个位置，dest可以为一个回调方法，pipeStream会自动执行该回调方法，其上一个stream及执行下一步的回调，具体使用见Example
3. `pipeStreamObj.addHead(dest, pipeOpts)` 把dest放到stream串头部最后一个位置，dest同prepend方法
4. `pipeStreamObj.add(dest, pipeOpts)`、 `pipeStreamObj.insert(dest, pipeOpts, index)` 把dest放到stream串中间最后一个位置，dest同prepend方法
5. `pipeStreamObj.addTail(dest, pipeOpts)` 把dest放到stream串尾部第一个位置，dest同prepend方法
6. `pipeStreamObj.append(dest, pipeOpts)` 把dest放到stream串尾部最后一个位置，dest同prepend方法
7. `pipeStreamObj.pipe(dest, pipeOpts)` 同stream.pipe，执行这个方法后stream串将创建完毕，无法再往该stream串插入stream对象。
8. `pipeStreamObj.dest(dest, pipeOpts)` 相当于`pipeStreamObj.pipe`，这个要与`pipeStreamObj.src`一起使用，用于从dest-->src的顺序pipe stream
9. `pipeStreamObj.src(src, pipeOpts)` 相当于`src.pipe(pipeStreamObj, pipeOpts)`，执行该方法后，不能再调用prepend、append、add、addHead、addTail方法
10. pipe(pipeStreamObj, pipeOpts)`，这个与pipeStreamObj.dest一起使用，执行这个方法后stream串将创建完毕，无法再往该stream串插入stream对象。。
10. `PipeStream.Transform`  pipeStreamObj.add(`new PipeStream.Transform()`)相当于pipeStreamObj.add(`new require('stream').PassThrough({objectMode: 1}), {end: false}`)，且在执行PipeStream.Transform.prototype._transform(chunk, encoding, cb)方法时，如果传过来的chunk为null，则表示这是最后一个回调，执行该回调后流将结束，无需再监听end事件。
11. `pipeStreamObj.wrapStream(stream, dest, pipeOpts)` `PipeStream.wrap(stream, dest, options)` 把stream转成pipeStream，dest表示为用于被pipe的stream，看示例。
12. `PipeStream.pipe(stream, pipeOpts)` 默认设置{end: false}，且会加入ending事件。

		


