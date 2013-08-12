!function(){require.config({paths:{jquery:"//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min","jquery-ui":"//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min",datatables:"//ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min",d3:"//cdnjs.cloudflare.com/ajax/libs/d3/3.2.2/d3.v3"},shim:{d3:{exports:"d3"}}})}.call(this),function(){define("utils",["d3"],function(t){var e,n,i;return e=function(){function t(t,e){this._func=t,this._period=null!=e?e:1e3,this._id=null,this._running=!1}return t.prototype.func=function(t){return null!=t?(this._func=t,this.running()&&this.reset(),this):this._func},t.prototype.period=function(t){return null!=t?(this._period=t,this.running()&&this.reset(),this):this._period},t.prototype.running=function(t){return null!=t?(this._running=t,null!=this._id&&(clearInterval(this._id),this._id=null),t&&(this._id=setInterval(this.func(),this.period())),this):this._running},t.prototype.reset=function(){return this.running(!1),this.running(!0)},t}(),{definitions:window.definitions,describe:function(t,e){var n,i;for(n in e)i=e[n],t=t.attr(n,i);return t},mergeObj:function(t,e){var n,i;null==t&&(t={});for(n in e)i=e[n],null!=i&&(t[n]=i);return t},isEmpty:function(t){var e,n;for(e in t)if(n=t[e],t.hasOwnProperty(e))return!1;return!0},mash:function(t){var e,n,i,r;for(e={},i=0,r=t.length;r>i;i++)n=t[i],e[n[0]]=n[1];return e},loadJSON:n=function(e,i,r){return null==r&&(r=3),r>0?t.json(definitions.webRoot+e,function(t,s){return null==t&&s.success?i(s.data):(null!=t&&console.log(t),null!=s&&console.log(s.error),setTimeout(function(){return n(e,i,r-1)},10))}):void 0},loadUnwrappedJSON:i=function(e,n,r){return null==r&&(r=3),r>0?t.json(definitions.webRoot+e,function(t,s){return null!=t?(null!=t&&console.log(t),setTimeout(function(){return i(e,n,r-1)},10)):n(s)}):void 0},property:function(t){var e,n,i;return n=void 0,e="function"==typeof t||null==t.get?function(t){return t}:t.get,i="function"==typeof t?t:null!=t.set?t.set:function(){throw new Error("property is read-only")},function(t){return null!=t?(n=i.call(this,t,n),this):e.call(this,n)}},degrees:function(t){return 180*(t/Math.PI)},radians:function(t){return Math.PI/180*t},IntervalFunc:e}})}.call(this),function(){var t={}.hasOwnProperty,e=function(e,n){function i(){this.constructor=e}for(var r in n)t.call(n,r)&&(e[r]=n[r]);return i.prototype=n.prototype,e.prototype=new i,e.__super__=n.prototype,e},n=[].indexOf||function(t){for(var e=0,n=this.length;n>e;e++)if(e in this&&this[e]===t)return e;return-1};define("plots",["utils","d3","jquery"],function(t,i){var r,s,o,a,l,u,c,h,p,f,d;return h=t.mash,c=t.describe,p=t.mergeObj,f=t.property,d=0,u={top:40,right:70,bottom:50,left:60},a=function(){function t(t,e,n){var r;this.rootSelector=null!=t?t:"body",this.margin=null!=e?e:u,this.dimensions=null!=n?n:["x","y"],this.root=i.select(this.rootSelector),this.size={x:this.root.attr("width"),y:this.root.attr("height")},this.canvasSize={x:this.size.x-this.margin.left-this.margin.right,y:this.size.y-this.margin.top-this.margin.bottom},this._scales=h(function(){var t,e,n,s;for(n=this.dimensions,s=[],t=0,e=n.length;e>t;t++)r=n[t],s.push([r,i.scale.linear()]);return s}.call(this)),this._title="",this._prepared=!1}return t.prototype.select=function(t){return i.select(""+this.rootSelector+" "+t)},t.prototype.scales=function(t,e){var n,i;if(null==e&&(e={x:[0,this.canvasSize.x],y:[this.canvasSize.y,0]}),null!=t)return p(this._scales,t),this.declareDirty(),this;for(n in e)i=e[n],this._scales[n].range(i);return this._scales},t.prototype.title=function(t){return null!=t?(this._title=t,this._prepared&&this.select(".title").text(t),this):this._title},t.prototype.limits=function(t){var e,n;if(null!=t){for(e in t)n=t[e],this._scales[e].domain(n);return this.declareDirty(),this}return h(function(){var t,n,i,r;for(i=this.dimensions,r=[],t=0,n=i.length;n>t;t++)e=i[t],r.push([e,this._scales[e].domain()]);return r}.call(this))},t.prototype.maps=function(){var t;return h(function(){var e,n,i,r;for(i=this.dimensions,r=[],e=0,n=i.length;n>e;e++)t=i[e],r.push([t,this._scales[t].copy()]);return r}.call(this))},t.prototype.clear=function(){return this._prepared?(this.canvas.remove(),this._prepared=!1,this.prepare()):void 0},t.prototype.prepare=function(){return this._prepared?!1:(this._prepareCanvas(),this._prepareCanvasClipPath(),this._prepareTitle(),this._prepared=!0)},t.prototype.declareDirty=function(){return this.clear(),this.prepare(),this},t.prototype._prepareCanvas=function(){return this.canvas=c(this.root.append("g"),{"class":"canvas",transform:"translate("+this.margin.left+", "+this.margin.top+")"}),this.svgDefs=this.canvas.append("defs")},t.prototype._prepareCanvasClipPath=function(){return this.canvasClipId="canvas-clip-"+(d+=1),this._canvasClip=this.canvas.append("clipPath").attr("id",this.canvasClipId),c(this._canvasClip.append("rect"),{x:0,y:0,width:this.canvasSize.x,height:this.canvasSize.y})},t.prototype._prepareTitle=function(){var t;return t=20,c(this.canvas.append("text").text(this._title),{x:this.canvasSize.x/2,y:-this.margin.top+1.1*t,"text-anchor":"middle","font-size":""+t,"class":"title axis-label"})},t}(),r=function(t){function n(t,e){var i;null==t&&(t="body"),null==e&&(e=["x","y"]),n.__super__.constructor.call(this,t,null,e),this._axisLabels=h(function(){var t,e,n,r;for(n=this.dimensions,r=[],t=0,e=n.length;e>t;t++)i=n[t],r.push([i,i]);return r}.call(this)),this._ticks=h(function(){var t,e,n,r;for(n=this.dimensions,r=[],t=0,e=n.length;e>t;t++)i=n[t],r.push([i,null]);return r}.call(this)),this._showGrid=!0}return e(n,t),n.prototype.select=function(t){return i.select(""+this.rootSelector+" "+t)},n.prototype.axisLabels=function(t){var e,n,i;if(null!=t){if(p(this._axisLabels,t),this._prepared){i=this._axisLabels;for(e in i)n=i[e],this.select("."+e+".axis-label").text(n)}return this}return this._axisLabels},n.prototype.ticks=function(t){return null!=t?(p(this._ticks,t),this.declareDirty(),this):this._ticks},n.prototype.showGrid=function(t){return null!=t?(this._showGrid=t,this.declareDirty(),this):this._showGrid},n.prototype.prepare=function(){return n.__super__.prepare.call(this)?(this._prepareGrid(),this._prepareAxes(),this._prepareAxisLabels()):void 0},n.prototype._prepareGrid=function(){var t;if(this._showGrid)return t=this._makeAxes(),t.x.tickSize(-this.canvasSize.y,0,0).tickFormat(""),t.y.tickSize(-this.canvasSize.x,0,0).tickFormat(""),c(this.canvas.append("g"),{"class":"x grid",transform:"translate(0, "+this.canvasSize.y+")"}).call(t.x),c(this.canvas.append("g"),{"class":"y grid"}).call(t.y)},n.prototype._prepareAxisLabels=function(){var t,e;return t=15,c(this.canvas.append("text").text(this._axisLabels.x),{x:this.canvasSize.x/2,y:this.canvasSize.y+this.margin.bottom-1.1*t,"text-anchor":"middle","font-size":""+t,"class":"x axis-label"}),e=this.canvas.append("g").attr("transform","rotate(-90)"),c(e.append("text").text(this._axisLabels.y),{x:-this.canvasSize.y/2,y:1.1*t-this.margin.left,"text-anchor":"middle","font-size":""+t,"class":"y axis-label"})},n.prototype._prepareAxes=function(){var t;return t=this._makeAxes(),c(this.canvas.append("g"),{"class":"x axis",transform:"translate(0, "+this.canvasSize.y+")"}).call(t.x),c(this.canvas.append("g"),{"class":"y axis"}).call(t.y)},n.prototype._makeAxes=function(t){var e,n,r,s,o,a,l;for(null==t&&(t={x:"bottom",y:"left"}),e={},s=this.scales(),l=this.dimensions,o=0,a=l.length;a>o;o++)r=l[o],n=i.svg.axis().scale(s[r]).orient(t[r]),null!=this._ticks[r]&&n.ticks.apply(n,this._ticks[r]),e[r]=n;return e},n}(a),l=function(t){function n(t,e){null==e&&(e=["x","y","z"]),n.__super__.constructor.call(this,t,e),this._zBarWidth=30,this.canvasSize.x-=this._zBarWidth,this._zColor={lower:i.rgb(0,0,0),upper:i.rgb(255,0,0)}}return e(n,t),n.prototype.zColor=function(t){return null!=t?(p(this._zColor(t)),this.declareDirty(),this):this._zColor},n.prototype.scales=function(t,e){var i,r;if(null==e&&(e={z:[this.canvasSize.y,0]}),null!=t)return n.__super__.scales.call(this,t);t=n.__super__.scales.call(this);for(i in e)r=e[i],t[i].range(r);return t},n.prototype.maps=function(){var t,e,r,s;return r=n.__super__.maps.call(this),e=this.canvasSize.y,s=this.zColor(),t=i.interpolateRgb(s.lower,s.upper),{x:r.x,y:r.y,z:function(n){return t(1-r.z(n)/e)}}},n.prototype.prepare=function(){return n.__super__.prepare.call(this)?(this._prepareZGradient(),this._prepareZColorBar(),this._prepareZAxis(),this._prepareZLabel()):void 0},n.prototype._prepareZGradient=function(){var t;return t=this.zColor(),this._zGradient=c(this.svgDefs.append("linearGradient"),{id:"zGradient",x1:"0%",y1:"100%",x2:"0%",y2:"0%"}),c(this._zGradient.append("stop"),{offset:"0%","stop-color":t.lower,"stop-opacity":1}),c(this._zGradient.append("stop"),{offset:"100%","stop-color":t.upper,"stop-opacity":1})},n.prototype._prepareZColorBar=function(){var t;return t=10,this._zColorBar=c(this.canvas.append("rect"),{x:this.canvasSize.x+t,y:0,width:this._zBarWidth-t,height:this.canvasSize.y,fill:"url(#"+this._zGradient.attr("id")+")"})},n.prototype._prepareZAxis=function(){return c(this.canvas.append("g"),{"class":"z axis",transform:"translate("+(this.canvasSize.x+this._zBarWidth)+", 0)"}).call(this._makeAxes({z:"right"}).z)},n.prototype._prepareZLabel=function(){var t,e;return t=15,e=this.canvas.append("g").attr("transform","rotate(-90)"),c(e.append("text").text(this.axisLabels().z),{x:-this.canvasSize.y/2,y:this.canvasSize.x+this._zBarWidth+this.margin.right,"text-anchor":"middle","font-size":""+t,"class":"z axis-label"})},n}(r),s=function(t){function n(t){n.__super__.constructor.call(this,t),this.bins([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]),this.useProbability(!0),this.limits({y:[0,1]})}return e(n,t),n.prototype.bins=function(t){return null!=t?(this._bins=t,this.declareDirty(),this):this._bins},n.prototype.useProbability=function(t){return null!=t?(this._useProbability=t,this.axisLabels({y:t?"Probability":"Frequency"}),this.declareDirty(),this):this._useProbability},n.prototype.plot=function(t){var e,n,r,s,o,a;return this.prepare(),a=this.scales(),s=a.x,o=a.y,n=i.layout.histogram(),null!=this.bins()&&n.bins(this.bins()),n.frequency(!this.useProbability()),e=n(t),this.canvas=i.select(this.rootSelector+">.canvas"),r=this.canvas.selectAll("rect.histogram-bar").data(e),c(r.enter().append("rect"),{"class":"histogram-bar",x:function(t){return Math.floor(s(t.x))},y:function(t){return o(t.y)},width:function(t){return Math.ceil(s(t.x+t.dx)-s(t.x))},height:function(t){return o(0)-o(t.y)},fill:"steelblue","shape-rendering":"crispEdge"}),r.exit().remove()},n}(r),o=function(t){function r(t,e){null==t&&(t="body"),null==e&&(e=["x","y","color","size"]),r.__super__.constructor.call(this,t,e),this.showLegend(!1),this.scales({color:i.scale.category20(),size:i.scale.ordinal()}),this.groups(["default"])}return e(r,t),r.prototype.showLegend=f(function(t){return this.declareDirty(),t}),r.prototype.groups=f(function(t){var e;return this.scales().color.domain(t),this.scales().size.domain(t).range(function(){var n,i,r;for(r=[],n=0,i=t.length;i>n;n++)e=t[n],r.push(5);return r}()),this.declareDirty(),t}),r.prototype.sizes=f({get:function(){var t,e,n;return n=this.scales().size.range(),t=this.groups(),h(function(){var i,r,s;for(s=[],e=i=0,r=t.length;r>=0?r>i:i>r;e=r>=0?++i:--i)s.push([t[e],n[e]]);return s}())},set:function(t){var e,n,i,r,s,o;for(i=this.scales().size.range(),e=this.groups(),n=s=0,o=e.length;o>=0?o>s:s>o;n=o>=0?++s:--s)r=t[e[n]],null!=r&&(i[n]=r);return this.scales().size.range(i),this.declareDirty()}}),r.prototype.colors=f({get:function(){var t,e,n;return n=this.scales().color.range(),t=this.groups(),h(function(){var i,r,s;for(s=[],e=i=0,r=t.length;r>=0?r>i:i>r;e=r>=0?++i:--i)s.push([t[e],n[e]]);return s}())},set:function(t){var e,n,i,r,s,o;for(r=this.scales().color.range(),n=this.groups(),i=s=0,o=n.length;o>=0?o>s:s>o;i=o>=0?++s:--s)e=t[n[i]],null!=e&&(r[i]=e);return this.scales().color.range(r),this.declareDirty()}}),r.prototype.prepare=function(){return r.__super__.prepare.call(this)?this._prepareLegend():void 0},r.prototype._prepareLegend=function(){var t,e,n,r,s,o,a=this;if(this.showLegend())return s=5,r={x:100,y:20},e=this.groups(),n=c(this.canvas.append("g").selectAll(".legend").data(i.zip(function(){o=[];for(var t=0,n=e.length;n>=0?n>t:t>n;n>=0?t++:t--)o.push(t);return o}.apply(this),e)).enter().append("g"),{"class":"legend",transform:function(t){return"translate("+(a.canvasSize.x-r.x)+", "+t[0]*(r.y+s)+")"}}),t=this.scales().color,c(n.append("rect"),{x:0,y:0,width:r.x,height:r.y,stroke:"none",fill:function(e){return t(e[1])}}),c(n.append("text").text(function(t){return t[1]}),{x:3,y:r.y-5,"text-anchor":"start","font-size":""+(r.y-8),"font-weight":"bold",fill:"white"})},r.prototype.plot=function(t){var e,r,s,o,a,l,u,h,p,f,d,g,y,_,v;for(this.prepare(),o=[],y=this.groups(),p=0,d=y.length;d>p;p++)if(s=y[p],!(n.call(t,s)<0))for(_=t[s],f=0,g=_.length;g>f;f++)a=_[f],o.push({group:s,point:a});return v=this.scales(),u=v.x,h=v.y,r=v.color,l=v.size,this.canvas=i.select(this.rootSelector+">.canvas"),e=this.canvas.selectAll("circle.scatter-point").data(o),c(e.enter().append("circle"),{"class":"scatter-point","clip-path":"url(#"+this.canvasClipId+")"}),c(e.transition().duration(500),{cx:function(t){return u(t.point[0])},cy:function(t){return h(t.point[1])},r:function(t){return l(t.group)},stroke:"none",fill:function(t){return r(t.group)}}),e.exit().remove()},r}(r),{SvgPlot:a,BasicPlot:r,ZColorPlot:l,Histogram:s,ScatterPlot:o}})}.call(this),function(){var t={}.hasOwnProperty,e=function(e,n){function i(){this.constructor=e}for(var r in n)t.call(n,r)&&(e[r]=n[r]);return i.prototype=n.prototype,e.prototype=new i,e.__super__=n.prototype,e};define("triggers/scroller",["utils","plots","d3"],function(t,n,i){var r,s,o;return o=t.describe,r=t.IntervalFunc,s=function(t){function n(t,e){this.store=t,n.__super__.constructor.call(this,e),this.windowSize(30),this._autoRefresh=new r,this._nouseScroll=new r,this._keyScroll=new r,this.axisLabels({x:"Time [s]",y:"Frequency [Hz]",z:"SNR"}),this.limits({x:[-this._windowSize,0]})}return e(n,t),n.prototype.windowSize=function(t){return null!=t?(this._windowSize=t,this.limits({x:[-t,0]}),this.declareDirty(),this):this._windowSize},n.prototype.scrollTo=function(t,e){var n,i,r,s,a,l,u,c,h,p;return null==e&&(e=null),this.prepare(),n=null!=this._lastTime?this._lastTime:t,null==e&&(e=1e3*(t-n)),this.axisLabels({x:"Time [s] since "+Math.round(t)}),c=this.windowSize(),s=[t-c,t],(h=this.store).indicateWindow.apply(h,s),a=function(t,e){return t.time_min-e},i=this.maps(),u=this.canvasSize.x/c,l=(p=this.store).getWindow.apply(p,s),r=this.canvas.selectAll("rect.value").data(l,function(t){return t.id}),o(r.enter().append("rect"),{"class":"value",x:function(t){return Math.round(i.x(a(t,n)))},y:function(t){return Math.round(i.y(t.freq_max))},width:function(t){return Math.ceil(u*(t.time_max-t.time_min))},height:function(t){var e;return e=i.y(t.freq_min)-i.y(t.freq_max),Math.ceil(Math.abs(e))},fill:function(t){return i.z(t.snr)},stroke:"none","clip-path":"url(#"+this.canvasClipId+")"}),r.exit().remove(),o(r.transition().duration(e).ease("linear"),{x:function(e){return Math.round(i.x(a(e,t)))}}),this._lastTime=t},n.prototype.autoRefresh=function(t,e){var n,i=this;return null==e&&(e=1e3),null!=t?(this._autoRefresh.running(!1),t&&(this._autoRefresh.period(e),n=this._lastTime,this._autoRefresh.func(function(){return n===i._lastTime&&i.scrollTo(i._lastTime,0),n=i._lastTime}),this._autoRefresh.running(!0)),this):this._autoRefresh.running()},n.prototype.mouseScroll=function(t,e,n,r){var s,o,a=this;return null==e&&(e=500),null==n&&(n=.05),null==r&&(r=100),null!=t?(this._mouseScroll.running(!1),t&&(this._mouseScroll.period=e,o={x:this.canvasSize.x/2,y:this.canvasSize.y/2},this.canvas.on("mouseover",function(){var t;return t=i.mouse(this),o.x=t[0],o.y=t[1],t}),s={left:r,right:this.canvasSize.x-r},this._mouseScroll.func(function(){var t;return t=a._lastTime,o.x<s.left&&(t-=n*(s.left-o.x)),o.x>s.right&&(t+=n*(o.x-s.right)),t!==a._lastTime?a.scrollTo(t,e):void 0}),this._mouseScroll.running(!0)),this):this._mouseScroll.running()},n.prototype.keyScroll=function(t,e,n,r,s){var o,a=this;return null==e&&(e=300),null==n&&(n=5),null==r&&(r=37),null==s&&(s=39),null!=t?(this._keyScroll.running(!1),t&&(this._keyScroll.period(e),o={left:!1,right:!1},i.select("body").on("keydown",function(){return i.event.keyCode===r&&(o.left=!0),i.event.keyCode===s?o.right=!0:void 0}),i.select("body").on("keyup",function(){return i.event.keyCode===r&&(o.left=!1),i.event.keyCode===s?o.right=!1:void 0}),this._keyScroll.func(function(){var t;return t=a._lastTime,o.left&&(t-=n),o.right&&(t+=n),t!==a._lastTime?a.scrollTo(t,e):void 0}),this._keyScroll.running(!0)),this):this._keyScroll.running()},n}(n.ZColorPlot),{TriggerScroller:s}})}.call(this),function(){define("triggers/store",["utils","d3"],function(t){var e,n,i,r,s,o;return r=t.definitions,s=t.loadJSON,n=t.IntervalFunc,o=0,e=function(){function t(t,e,n){this.channel=t,this.startTime=e,this.endTime=n,this.accessedTime=0,this.triggers=[],this.loaded=!1}return t.prototype.load=function(t){var e,n=this;return null==t&&(t=1e3),this.accessedTime=(new Date).getTime(),this.loaded?void 0:(e="/triggers/channel/"+this.channel.id+"/"+(""+this.startTime+"-"+this.endTime+"?limit="+t),s(e,function(t){var e,i,r,s;for(n.triggers=t.triggers,s=n.triggers,i=0,r=s.length;r>i;i++)e=s[i],e.id=o+=1;return n.loaded=!0}))},t}(),i=function(){function t(t,e,i){this.channel=t,this.timeChunk=null!=e?e:30,this.maxChunks=null!=i?i:50,this.chunks={},this._garbageCollecting=new n(this.garbageCollect,1e4)}return t.prototype.garbageCollecting=function(t,e){return null==e&&(e=1e4),null!=t?(this._garbageCollecting.period(e),this._garbageCollecting.running(t),this):this._garbageCollecting.running()},t.prototype.indicateWindow=function(t,n,i){var r,s,o,a,l,u;for(null==i&&(i=2),l=this._getChunkStarts(t,n,i),u=[],o=0,a=l.length;a>o;o++)s=l[o],null==this.chunks[s]&&(r=s+this.timeChunk,this.chunks[s]=new e(this.channel,s,r)),u.push(this.chunks[s].load());return u},t.prototype.getWindow=function(t,e,n){var i,r;return null==n&&(n=1),r=this._getChunkStarts(t,e,n),[].concat.apply([],function(){var t,e,n;for(n=[],t=0,e=r.length;e>t;t++)i=r[t],n.push(this.chunks[i].triggers);return n}.call(this))},t.prototype._getChunkStarts=function(t,e,n){var i,r,s,o,a;for(r=this.timeChunk*(Math.floor(t/this.timeChunk)-n),s=Math.ceil((e-t)/this.timeChunk)+2*n,s>=this.maxChunks&&console.log("Warning! window is too large: "+t+"-"+e),a=[],i=o=0;s>=0?s>o:o>s;i=s>=0?++o:--o)a.push(r+i*this.timeChunk);return a},t.prototype.garbageCollect=function(){var t,e,n,i,r,s,o,a,l,u,c;n=0,a=this.chunks;for(r in a)r=a[r],n+=1;if(i=n-this.maxChunks,i>0){l=this.chunks;for(r in l)t=l[r],e=t;for(e.sort(function(t,e){return t.accessedTime-e.accessedTime}),u=e.slice(0,i),c=[],s=0,o=u.length;o>s;s++)t=u[s],c.push(delete this.chunks[t.startTime]);return c}},t}(),{Chunk:e,TriggerStore:i}})}.call(this),function(){var t={}.hasOwnProperty,e=function(e,n){function i(){this.constructor=e}for(var r in n)t.call(n,r)&&(e[r]=n[r]);return i.prototype=n.prototype,e.prototype=new i,e.__super__=n.prototype,e};define("triggers/densities",["utils","plots","d3","jquery"],function(t,n,i,r){var s,o,a,l,u;return o=t.definitions,a=t.describe,l=t.loadJSON,u=function(t){return new Date(1e3*t)},s=function(t){function n(t,e){this.channel=e,n.__super__.constructor.call(this,t),this._scroller=null,this.axisLabels({x:"Time [s]",y:"Frequency [Hz]",z:"SNR Density"}),this.scales({x:i.time.scale(),y:i.scale.log().clamp(!0),z:i.scale.log().clamp(!0)}),this.ticks({x:[5],y:[5],z:[5]})}return e(n,t),n.prototype.scroller=function(t){return null!=t?(this._scroller=t,this):this._scroller},n.prototype.load=function(){var t,e=this;return t="/triggers/channel/"+this.channel.id+"/"+"densities",l(t,function(t){var n,i,r,s;return s=t.times,i=t.frequencies,n=t.densities,r=i[i.length-1],i.push(2*r),s.push(2*s[s.length-1]-s[s.length-2]),t=e._makeData(s,i,n),e._draw(s,i,t)})},n.prototype._makeData=function(t,e,n){var i,r,s,o,a,l,c,h,p,f,d,g,y,_,v;for(r=[],c=f=0,g=n.length;g>=0?g>f:f>g;c=g>=0?++f:--f)if(y=t.slice(c,+(c+1)+1||9e9),h=y[0],a=y[1],0!==h&&0!==a)for(_=[h,a].map(u),p=_[0],l=_[1],o=n[c],i=d=0,v=o.length;v>=0?v>d:d>v;i=v>=0?++d:--d)s=o[i],10>s||r.push({startDate:p,endDate:l,freqMin:e[i],freqMax:e[i+1],density:s});return r},n.prototype._draw=function(t,e,n){var s,o,l,c,h,p,f,d,g,y,_,v,m=this;for(this.prepare(),this.limits({x:[t[0],t[t.length-1]].map(u),y:i.extent(e),z:[10,1e4]}),h=this.maps(),f=r(this.root[0][0]),p={x:f.position().left+this.margin.left,y:f.position().top+this.margin.top},c=a(r("<canvas/>"),{id:"density-image",width:this.canvasSize.x,height:this.canvasSize.y}),c.css({position:"absolute",left:p.x,top:p.y}),c.appendTo(r("body")),s=c[0].getContext("2d"),_=0,v=n.length;v>_;_++)o=n[_],s.fillStyle=h.z(o.density),g=Math.round(h.x(o.startDate)),y=Math.round(h.y(o.freqMax)),d=Math.ceil(h.x(o.endDate)-h.x(o.startDate)),l=Math.ceil(h.y(o.freqMin)-h.y(o.freqMax)),s.fillRect(g,y,d,l);return c.click(function(t){var e;return g=t.pageX-p.x,e=Math.round(m.scales().x.invert(g)/1e3),null!=m._scroller?m._scroller.scrollTo(e,0):void 0})},n}(n.ZColorPlot),{DensityPlot:s}})}.call(this),function(){var t={}.hasOwnProperty,e=function(e,n){function i(){this.constructor=e}for(var r in n)t.call(n,r)&&(e[r]=n[r]);return i.prototype=n.prototype,e.prototype=new i,e.__super__=n.prototype,e};define("triggers/distributions",["utils","plots","d3","jquery"],function(t,n,i){var r,s,o,a,l;return s=t.definitions,o=t.describe,a=t.loadJSON,l=function(t){return new Date(1e3*t)},r=function(t){function n(t,e){this.channel=e,n.__super__.constructor.call(this,t),this.field("SNR"),this.clustered(!0)}return e(n,t),n.prototype.clustered=function(t){return null!=t?(this._clustered=t,this.declareDirty(),this):this._clustered},n.prototype.field=function(t){var e,n,r;if(null!=t){switch(this._field=t,t){case"SNR":this.axisLabels({x:"SNR"}),this.bins(function(){for(r=[],n=0;30>=n;n++)r.push(n);return r}.apply(this));break;case"Amplitude":this.axisLabels({x:"Amplitude"}),this.bins(function(){var t,n;for(n=[],e=t=0;100>=t;e=++t)n.push(e/100);return n}());break;case"Frequency":this.bins(function(){var t,n;for(n=[],e=t=0;100>=t;e=++t)n.push(Math.exp(.05*e-1));return n}()),this.scales({x:i.scale.log().clamp(!0)}),this.axisLabels({x:"Frequency"});break;default:throw new Error("Invalid field: "+t)}return this.limits({x:i.extent(this.bins())}),this.declareDirty(),this}return this._field},n.prototype.load=function(){var t,e,n=this;return t=function(){switch(this.field()){case"SNR":return"snr";case"Amplitude":return"amplitude";case"Frequency":return"freq"}}.call(this),e="/triggers/channel/"+this.channel.id+"/"+("field/"+t+"?clustered="+this.clustered()),a(e,function(t){var e;return e=t.values,n.plot(e)})},n}(n.Histogram),{TriggerDistributionPlot:r}})}.call(this),function(){define("triggers/main",["utils","triggers/scroller","triggers/store","triggers/densities","triggers/distributions","jquery","jquery-ui"],function(t,e,n,i,r,s){var o;return console.log("Starting"),o=t.definitions.channel,s(function(){var i,a,l,u;return u=s("#tabs").tabs(),l=new r.TriggerDistributionPlot("#snrs",o).field("SNR"),l.load(),a=new r.TriggerDistributionPlot("#freqs",o).field("Frequency"),a.load(),i=new r.TriggerDistributionPlot("#ampls",o).field("Amplitude"),i.load(),n=new n.TriggerStore(o),n.garbageCollecting(!0),n.indicateWindow(t.definitions.time_min),e=new e.TriggerScroller(n,"#clusters"),e.windowSize(120),e.scales({y:d3.scale.log().clamp(!0),z:d3.scale.log().clamp(!0)}),e.limits({y:[.1,100],z:[1,200]}),e.scrollTo(t.definitions.time_min),e.autoRefresh(!0),e.keyScroll(!0)})})}.call(this);