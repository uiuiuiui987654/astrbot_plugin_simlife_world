/* Time-of-day and weather for Room3D (bedroom-3d.js).
   Everything here is driven by an environment object (same shape as SceneStudio.environment):
     {hour:0-24, band:'dawn'|'day'|'dusk'|'night', weather:'clear'|'cloudy'|'rain'|'storm'|'snow'|'fog'|'wind', dark, signature}
   Public API (via window.Room3D):
     Room3D.makeEnvironment({hour, weather})      -> env object
     Room3D.setEnvironment(envOrPartial)          -> re-light every mounted room without rebuilding it
     engine.setEnvironment(envOrPartial)          -> one room
     Room3D.registerEffect(name, factory)         -> reserved hook for future effects:
        factory(rig) -> {apply(env, state), update(dt, time) -> bool needsAnimation, dispose()}
   state passed to effects: {sunDir, light (0..1), lamps (0..1), cover, wet, snow, wind, flash}. */
(function(root){
  'use strict';
  var PI=Math.PI,WEATHERS=['clear','cloudy','rain','storm','snow','fog','wind'],extraEffects={};
  // ---------------------------------------------------------------- keyframes
  // hour, sun colour, sun intensity, hemi sky, hemi ground, hemi intensity, exposure, background top/bottom, lamps on (0..1)
  var KEYS=[
    [0,'#8fa4d6',.32,'#7f90c0','#3e3a52',.78,1.12,'#2a3048','#3d4560',1],
    [5,'#8fa4d6',.32,'#7f90c0','#3e3a52',.78,1.12,'#2a3048','#3d4560',1],
    [6.1,'#ffad7a',1.05,'#d9c3d3','#8a8088',1.25,1.16,'#cdbfcc','#e9d9cf',.55],
    [7.5,'#ffe1bd',2.2,'#fbeedd','#a6ad94',1.72,1.2,'#e3e5dc','#e8e2d6',.05],
    [12,'#fff4dc',2.7,'#fff6e2','#a8ae98',1.95,1.2,'#e7e9df','#e5e4da',0],
    [16,'#ffe6c4',2.45,'#fff0da','#a9a890',1.85,1.2,'#ebe6da','#e7e1d4',0],
    [17.6,'#ffa774',1.65,'#f1c6b2','#8f8379',1.4,1.18,'#e6c6b9','#e4d3c6',.6],
    [18.8,'#c9a3c4',.8,'#a59ec4','#5a526a',1.0,1.14,'#5d5c7c','#7b7290',.9],
    [19.6,'#9fb2e0',.38,'#8a96c4','#433f58',.82,1.12,'#2f364f','#40475f',1],
    [24,'#8fa4d6',.32,'#7f90c0','#3e3a52',.78,1.12,'#2a3048','#3d4560',1]];
  var SKY=[[0,'#0f1c36','#2a3a5e'],[5,'#13213d','#33405f'],[6.1,'#7b8eaa','#efb5a0'],[7.5,'#86bcd0','#f3e2c4'],[12,'#74b6cc','#dcebe4'],[16,'#7fb6c8','#efe3c6'],[17.6,'#7d7da4','#f2b18c'],[18.8,'#3d4a75','#c98f8a'],[19.6,'#16233f','#38466a'],[24,'#0f1c36','#2a3a5e']];
  // sun factor, hemi factor, shadow strength, desaturation, extra lamps, cloud cover, wind, wet, snow
  var WX={clear:[1,1,1,0,0,.12,.15,0,0],cloudy:[.36,1.02,.35,.35,.15,.85,.3,0,0],rain:[.18,.86,.2,.5,.35,.95,.45,1,0],storm:[.07,.64,.1,.62,.55,1,1,1,0],snow:[.55,1.12,.5,.25,.1,.8,.25,0,1],fog:[.3,.96,.25,.55,.2,.7,.1,.35,0],wind:[.9,1,.9,.05,0,.35,1,0,0]};
  function bandOf(h){return h<5||h>=19?'night':h<8?'dawn':h<16.5?'day':'dusk';}
  function makeEnvironment(o){o=o||{};var h=o.hour==null?new Date().getHours()+new Date().getMinutes()/60:((Number(o.hour)%24)+24)%24,w=WEATHERS.indexOf(o.weather)>=0?o.weather:'clear',band=bandOf(h);
    var names={clear:'晴朗',cloudy:'多云',rain:'小雨',storm:'雷雨',snow:'下雪',fog:'有雾',wind:'大风'};
    var pal={night:['#101e38','#425373','#98b8de'],dawn:['#7b8eaa','#efb5a0','#ffe3ba'],day:['#78b8cc','#e0e9cc','#fff2c2'],dusk:['#7d7da4','#f2b18c','#ffd297']}[band];
    return {hour:h,band:band,weather:w,condition:o.condition||names[w],sky:pal,dark:band==='night',signature:band+'|'+w+'|'+(o.condition||names[w])};}
  function lerpKeys(T,keys,h,fields){var a=keys[0],b=keys[keys.length-1];for(var i=0;i<keys.length-1;i++)if(h>=keys[i][0]&&h<=keys[i+1][0]){a=keys[i];b=keys[i+1];break;}var t=b[0]===a[0]?0:(h-a[0])/(b[0]-a[0]);t=t*t*(3-2*t);
    return fields.map(function(f,j){var x=a[j+1],y=b[j+1];return f==='c'?new T.Color(x).lerp(new T.Color(y),t):x+(y-x)*t;});}
  function hourOf(env){if(env.hour!=null&&!isNaN(env.hour))return env.hour;return {night:22,dawn:6.8,day:12,dusk:17.8}[env.band]||12;}
  // ---------------------------------------------------------------- painters
  function paintSky(T,c,w,h,env,wx){
    var hr=hourOf(env),cols=lerpKeys(T,SKY,hr,['c','c']),grey=new T.Color(env.band==='night'?'#18222d':'#9aa7ad'),grey2=new T.Color(env.band==='night'?'#2a3640':'#cdd4d1');
    cols[0].lerp(grey,wx[3]);cols[1].lerp(grey2,wx[3]);var g=c.createLinearGradient(0,0,0,h);g.addColorStop(0,'#'+cols[0].getHexString());g.addColorStop(1,'#'+cols[1].getHexString());c.fillStyle=g;c.fillRect(0,0,w,h);
    var night=hr<5.6||hr>19.2,cover=wx[5];
    if(night&&cover<.9){c.fillStyle='rgba(255,248,221,'+(1-cover)*.9+')';for(var s=0;s<70;s++)c.fillRect((s*97+13)%w,(s*53)%(h*.55),s%7?1.2:2,s%7?1.2:2);
      var mx=w*(.2+.6*(((hr+24-19)%24)/10)),my=h*(.42-.25*Math.sin(PI*((hr+24-19)%24)/10));c.fillStyle='rgba(241,230,188,'+(1-cover*.8)+')';c.beginPath();c.arc(mx,my,15,0,PI*2);c.fill();c.fillStyle='#'+cols[0].clone().lerp(cols[1],my/h).getHexString();c.beginPath();c.arc(mx+6,my-4,13,0,PI*2);c.fill();}
    if(!night&&cover<.9){var p=(hr-6)/12,sx=w*(.08+.84*p),sy=h*(.82-.62*Math.sin(PI*Math.max(0,Math.min(1,p))));var glow=c.createRadialGradient(sx,sy,0,sx,sy,90);var warm=hr<8||hr>16.5?'255,190,130':'255,240,200';glow.addColorStop(0,'rgba('+warm+','+(.9-cover*.7)+')');glow.addColorStop(1,'rgba('+warm+',0)');c.fillStyle=glow;c.fillRect(0,0,w,h);c.fillStyle='rgba(255,246,214,'+(1-cover)+')';c.beginPath();c.arc(sx,sy,22,0,PI*2);c.fill();}
    var light=Math.max(.18,Math.min(1,lerpKeys(T,KEYS,hr,['c','n'])[1]/2.7*(1-wx[3]*.5)+.15)),base=['#94b3a1','#6b958a','#48776d'],dark=new T.Color('#1a2731');
    base.forEach(function(col,i){var cc=new T.Color(col).lerp(dark,1-light);if(wx[8])cc.lerp(new T.Color('#eef2f4'),.75-i*.18);c.fillStyle='#'+cc.getHexString();c.beginPath();c.moveTo(0,h);for(var j=0;j<=12;j++)c.lineTo(j*w/12,h*(.6+i*.11)+Math.sin(j*1.6+i)*h*.09);c.lineTo(w,h);c.fill();
      if(!wx[8]){c.fillStyle='#'+cc.clone().multiplyScalar(.8).getHexString();for(var k=0;k<14;k++){var tx=(k*71+i*37)%w,ty=h*(.62+i*.11)+Math.sin(tx/w*12*1.6/1+i)*0;c.beginPath();c.moveTo(tx,h*(.66+i*.11));c.lineTo(tx+6,h*(.6+i*.11));c.lineTo(tx+12,h*(.66+i*.11));c.fill();}}});
    if(wx[8]){c.fillStyle='rgba(255,255,255,.18)';c.fillRect(0,0,w,h);}
    if(env.weather==='fog'){var fg=c.createLinearGradient(0,h*.3,0,h);fg.addColorStop(0,'rgba(220,226,224,.25)');fg.addColorStop(1,'rgba(225,230,228,.8)');c.fillStyle=fg;c.fillRect(0,0,w,h);}
  }
  function paintClouds(T,c,w,h,env,wx,lightCol){
    c.clearRect(0,0,w,h);var nightF=env.band==='night'?.55:1,cover=wx[5],n=Math.round(4+cover*26),dark=env.weather==='storm'?.55:env.weather==='rain'?.35:env.weather==='snow'?.12:0,col=new T.Color('#ffffff').lerp(new T.Color('#5b636c'),dark).multiply(lightCol);
    var rgb=Math.round(col.r*255)+','+Math.round(col.g*255)+','+Math.round(col.b*255);
    for(var i=0;i<n;i++){var cx=(i*173.3)%w,cy=h*(.08+((i*37)%34)/100),r=24+((i*29)%40)*(.6+cover);for(var k=-1;k<=1;k++){var x=cx+k*w;for(var b=0;b<5;b++){var bx=x+(b-2)*r*.55,by=cy+Math.sin(b*1.7+i)*r*.18,gr=c.createRadialGradient(bx,by,0,bx,by,r*(.7+.1*b%3));gr.addColorStop(0,'rgba('+rgb+','+(.5+cover*.4)*nightF+')');gr.addColorStop(1,'rgba('+rgb+',0)');c.fillStyle=gr;c.fillRect(bx-r,by-r,r*2,r*2);}}}
    if(env.weather==='fog'){c.fillStyle='rgba(232,236,234,.55)';c.fillRect(0,0,w,h);}
  }
  // ---------------------------------------------------------------- controller
  function create(rig){
    var T=rig.T,k=rig.kit,scene=rig.scene,state={},env=null,wx=WX.clear,time=0,flash=0,nextFlash=3,effects=[],reduced=!!(root.matchMedia&&root.matchMedia('(prefers-reduced-motion: reduce)').matches);
    var dynamic=[],owned=[];function own(o){owned.push(o);return o;}
    // background gradient
    var bgCanvas=document.createElement('canvas');bgCanvas.width=4;bgCanvas.height=256;var bgTex=own(new T.CanvasTexture(bgCanvas));bgTex.colorSpace=T.SRGBColorSpace;scene.background=bgTex;
    // sky + clouds (shared by every window)
    var skyCanvas=rig.skyTex.image,cloudCanvas=document.createElement('canvas');cloudCanvas.width=1024;cloudCanvas.height=256;var cloudTex=own(new T.CanvasTexture(cloudCanvas));cloudTex.colorSpace=T.SRGBColorSpace;cloudTex.wrapS=T.RepeatWrapping;
    var cloudMat=own(new T.MeshBasicMaterial({map:cloudTex,transparent:true,depthWrite:false}));
    var dropsTex=k.canvasTexture(function(c,w,h){c.clearRect(0,0,w,h);for(var i=0;i<140;i++){var x=(i*67.3)%w,y=(i*131.7)%h,r=1.5+(i%5);c.fillStyle='rgba(235,245,250,.45)';c.beginPath();c.ellipse(x,y,r*.8,r,0,0,PI*2);c.fill();c.fillStyle='rgba(255,255,255,.7)';c.fillRect(x-r*.3,y-r*.5,1.2,1.2);if(i%6===0){c.strokeStyle='rgba(235,245,250,.3)';c.lineWidth=1.4;c.beginPath();c.moveTo(x,y);c.lineTo(x+Math.sin(i)*3,y-18-i%20);c.stroke();}}},256,256,[1,1]);
    var dropsMat=own(new T.MeshBasicMaterial({map:dropsTex,transparent:true,depthWrite:false,opacity:.9}));
    var frostTex=k.canvasTexture(function(c,w,h){var g=c.createRadialGradient(w/2,h/2,w*.22,w/2,h/2,w*.62);g.addColorStop(0,'rgba(255,255,255,0)');g.addColorStop(1,'rgba(245,250,255,.85)');c.fillStyle=g;c.fillRect(0,0,w,h);c.strokeStyle='rgba(255,255,255,.55)';for(var i=0;i<60;i++){var a=i*2.4,x=w/2+Math.cos(a)*w*.48,y=h/2+Math.sin(a)*h*.48;c.beginPath();c.moveTo(x,y);c.lineTo(x-Math.cos(a)*14,y-Math.sin(a)*14);c.stroke();}},256,256);
    var frostMat=own(new T.MeshBasicMaterial({map:frostTex,transparent:true,depthWrite:false}));
    // per-window layers: clouds, raindrops, frost, outside particles, light shaft, dust
    scene.updateMatrixWorld(true);
    var windows=(k.windows||[]).filter(function(wd){return !wd.facade;}).map(function(wd){
      var g=wd.wall,cx=(wd.u0+wd.u1)/2,cy=(wd.y0+wd.y1)/2,w=wd.u1-wd.u0,h=wd.y1-wd.y0,t=wd.t;
      var cl=k.mesh(k.keep(new T.PlaneGeometry(w+.04,h+.04)),cloudMat,g,cx,cy,-t-.009,false);cl.raycast=noop;
      var dr=k.mesh(k.keep(new T.PlaneGeometry(w,h)),dropsMat,g,cx,cy,-t/2+.006,false);dr.raycast=noop;dr.visible=false;
      var fr=k.mesh(k.keep(new T.PlaneGeometry(w,h)),frostMat,g,cx,cy,-t/2+.007,false);fr.raycast=noop;fr.visible=false;
      var box={x0:wd.u0-.1,x1:wd.u1+.1,y0:Math.max(0,wd.y0-.3),y1:Math.min(rig.H-.06,wd.y1+.35),z0:-t-.9,z1:-t-.05};
      return {wd:wd,g:g,clouds:cl,drops:dr,frost:fr,box:box,rain:null,snow:null,shaft:null,dust:null};});
    // ----- particles
    function noop(){}
    function spot(box){for(var n=0;n<12;n++){var x=box.x0+Math.random()*(box.x1-box.x0),z=box.z0+Math.random()*(box.z1-box.z0);if(!box.spawn||box.spawn(x,z))return [x,z];}return [x,z];}
    function floorAt(box,x,z){return box.floor?box.floor(x,z):box.y0;}
    function rainSystem(parent,box,count){var pos=new Float32Array(count*6),sp=new Float32Array(count),fl=new Float32Array(count);for(var i=0;i<count;i++){reset(i,true);}function reset(i,any){var q=spot(box),x=q[0],z=q[1],f=floorAt(box,x,z),y=any?f+Math.random()*(box.y1-f):box.y1+Math.random()*.4;fl[i]=f;pos[i*6]=x;pos[i*6+1]=y;pos[i*6+2]=z;pos[i*6+3]=x;pos[i*6+4]=y-.16;pos[i*6+5]=z;sp[i]=5.5+Math.random()*2.5;}
      var geo=k.keep(new T.BufferGeometry());geo.setAttribute('position',new T.BufferAttribute(pos,3));var mat=own(new T.LineBasicMaterial({color:'#d6e3ea',transparent:true,opacity:.55,depthWrite:false}));var obj=new T.LineSegments(geo,mat);obj.frustumCulled=false;obj.raycast=noop;parent.add(obj);
      return {obj:obj,update:function(dt,slant,len){for(var i=0;i<count;i++){var d=sp[i]*dt;pos[i*6+1]-=d;pos[i*6]+=slant*d;pos[i*6+4]=pos[i*6+1]-len;pos[i*6+3]=pos[i*6]-slant*len;pos[i*6+5]=pos[i*6+2];if(pos[i*6+4]<fl[i]||pos[i*6]>box.x1+.5)reset(i,false);}geo.attributes.position.needsUpdate=true;}};}
    var flakeTex=k.canvasTexture(function(c,w,h){var g=c.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.5,'rgba(255,255,255,.8)');g.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=g;c.fillRect(0,0,w,h);},32,32);
    function snowSystem(parent,box,count,size){var pos=new Float32Array(count*3),ph=new Float32Array(count),sp=new Float32Array(count),fl=new Float32Array(count);for(var i=0;i<count;i++){var q=spot(box);pos[i*3]=q[0];pos[i*3+2]=q[1];fl[i]=floorAt(box,q[0],q[1]);pos[i*3+1]=fl[i]+Math.random()*(box.y1-fl[i]);ph[i]=Math.random()*6.28;sp[i]=.35+Math.random()*.4;}
      var geo=k.keep(new T.BufferGeometry());geo.setAttribute('position',new T.BufferAttribute(pos,3));var mat=own(new T.PointsMaterial({map:flakeTex,size:size||.045,transparent:true,depthWrite:false,color:'#ffffff'}));var obj=new T.Points(geo,mat);obj.frustumCulled=false;obj.raycast=noop;parent.add(obj);
      return {obj:obj,update:function(dt,drift,tm){for(var i=0;i<count;i++){pos[i*3+1]-=sp[i]*dt;pos[i*3]+=(Math.sin(tm*1.3+ph[i])*.25+drift)*dt;if(pos[i*3+1]<fl[i]){var q=spot(box);pos[i*3]=q[0];pos[i*3+2]=q[1];fl[i]=floorAt(box,q[0],q[1]);pos[i*3+1]=box.y1;}if(pos[i*3]>box.x1)pos[i*3]=box.x0;}geo.attributes.position.needsUpdate=true;}};}
    function dustSystem(parent,box,count){var s=snowSystem(parent,box,count,.012);s.obj.material.opacity=.55;s.obj.material.blending=T.AdditiveBlending;s.obj.material.color.set('#fff2cf');return {obj:s.obj,update:function(dt,tm){var p=s.obj.geometry.attributes.position.array;for(var i=0;i<count;i++){p[i*3+1]+=Math.sin(tm*.5+i)*.004;p[i*3]+=Math.cos(tm*.3+i*1.7)*.002;p[i*3+2]+=Math.sin(tm*.4+i*.7)*.002;}s.obj.geometry.attributes.position.needsUpdate=true;}};}
    // outdoor volume
    var gY=rig.groundY||0,outdoorBox=rig.rainArea?{x0:rig.rainArea.x0,x1:rig.rainArea.x1,z0:rig.rainArea.z0,z1:rig.rainArea.z1,y0:rig.rainArea.y||0,y1:6,floor:function(){return rig.rainArea.y||0;}}:rig.outdoor?{x0:0,x1:rig.W+6,y0:gY,y1:4.2,z0:0,z1:rig.D+6,
      spawn:function(x,z){if(rig.awning&&x<rig.W&&z<1.05)return false;var ow=rig.kit&&rig.kit.outdoorWorld;if(ow&&ow.covered&&x>-.15&&x<rig.W+.15&&z>-.15&&z<rig.D+.15)return false;return true;},
      floor:function(x,z){return x<=rig.W&&z<=rig.D?0:gY;}}:null,outRain=null,outSnow=null;
    // ----- surfaces: snow cover, snow caps, wet floor
    var snowTex=k.canvasTexture(function(c,w,h){c.clearRect(0,0,w,h);for(var i=0;i<900;i++){var x=(i*97.1)%w,y=(i*57.7)%h,r=6+(i%7)*3;var g=c.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,'rgba(250,252,255,.9)');g.addColorStop(1,'rgba(250,252,255,0)');c.fillStyle=g;c.fillRect(x-r,y-r,2*r,2*r);}},256,256,[2,2]);
    var snowMat=own(new T.MeshStandardMaterial({map:snowTex,transparent:true,roughness:.9,depthWrite:false,color:'#ffffff'})),snowCover=null;
    if(rig.outdoor&&!rig.sheltered){snowCover=k.mesh(k.keep(new T.PlaneGeometry(rig.W,rig.D)),snowMat,scene,rig.W/2,.008,rig.D/2,false);snowCover.rotation.x=-PI/2;snowCover.raycast=noop;snowCover.visible=false;snowCover.receiveShadow=true;}
    var capMat=k.material('#fbfdff',.85),caps=(k.snowCaps||[]).map(function(cp){var m=k.box(cp.parent,cp.x,cp.y,cp.z,cp.w,.025,cp.d,capMat,.01);m.visible=false;m.raycast=noop;return m;});
    var floorBase=rig.floorMat?{rough:rig.floorMat.roughness,color:rig.floorMat.color.clone()}:null;
    // ----- light shafts (back-wall windows only)
    function shaftGeometry(wd,dir){var g=wd.wall,pts=[[wd.u0+.02,wd.y0],[wd.u1-.02,wd.y0],[wd.u1-.02,wd.y1],[wd.u0+.02,wd.y1]].map(function(p){return g.localToWorld(new T.Vector3(p[0],p[1],.01));});
      var reach=Math.min(4.2,rig.D*1.1),ends=pts.map(function(P){var s=Math.min(P.y/Math.max(.12,dir.y),reach);if(dir.x>1e-3)s=Math.min(s,(P.x-.02)/dir.x);if(dir.x<-1e-3)s=Math.min(s,(rig.W-.02-P.x)/-dir.x);if(dir.z<-1e-3)s=Math.min(s,(rig.D-.02-P.z)/-dir.z);return P.clone().addScaledVector(dir,-Math.max(0,s));});
      var v=[],c=[];function quad(a,b,cc,d,ca,cb){[a,b,cc,a,cc,d].forEach(function(p,i){v.push(p.x,p.y,p.z);var col=[ca,cb,cb,ca,cb,ca][i];c.push(col,col,col);});}
      for(var i=0;i<4;i++){var j=(i+1)%4;quad(pts[i],pts[j],ends[j],ends[i],1,0);}
      
      var geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(v,3));geo.setAttribute('color',new T.Float32BufferAttribute(c,3));return {geo:geo,box:new T.Box3().setFromPoints(pts.concat(ends))};}
    var shaftMat=own(new T.MeshBasicMaterial({vertexColors:true,transparent:true,blending:T.AdditiveBlending,depthWrite:false,side:T.DoubleSide,opacity:.1,color:'#fff0cc'}));
    // ----- sway targets
    var sway=(k.swayers||[]).map(function(s,i){return {obj:s.obj,kind:s.kind,phase:i*1.37,rx:s.obj.rotation.x,rz:s.obj.rotation.z};});
    // ----------------------------------------------------------------- apply
    function apply(next){
      next=next||{};env=Object.assign({},env||{},next);if(next.hour!=null&&!next.band)env.band=bandOf(env.hour);if(!env.band)env.band=bandOf(hourOf(env));env.dark=env.band==='night';if(!next.signature)env.signature=env.band+'|'+env.weather+'|'+(next.condition||env.condition||'');if(WEATHERS.indexOf(env.weather)<0)env.weather='clear';wx=WX[env.weather];var hr=hourOf(env),night=env.band==='night';
      var key=lerpKeys(T,KEYS,hr,['c','n','c','c','n','n','c','c','n']);var dark=rig.dark;
      var desat=new T.Color('#c9ccce');
      // sun / moon direction: always from behind the north wall, sweeping east→west through the day
      var p=night?(((hr+24-19.6)%24)/9.4):(hr-5.6)/14,az=(-.9+1.8*Math.max(0,Math.min(1,p))),el=night?.75:Math.max(.16,Math.sin(PI*Math.max(0,Math.min(1,p)))*.95);
      var dir=new T.Vector3(Math.sin(az)*Math.cos(el),Math.sin(el),(rig.outdoor?1:-1)*Math.cos(az)*Math.cos(el)).normalize();state.sunDir=dir;
      rig.sun.position.copy(rig.center).addScaledVector(dir,14);rig.sun.target.position.copy(rig.center);rig.sun.target.updateMatrixWorld();
      rig.sun.color.copy(key[0]).lerp(desat,wx[3]*.6);rig.sun.intensity=key[1]*wx[0]*(dark?.3:1)*(rig.outdoor?1.12:1);
      if(rig.sun.shadow&&'intensity' in rig.sun.shadow)rig.sun.shadow.intensity=Math.max(.15,wx[2]);
      rig.hemi.color.copy(key[2]).lerp(desat,wx[3]*.5);rig.hemi.groundColor.copy(key[3]);rig.hemi.intensity=key[4]*wx[1]*(dark?.55:1)*(rig.outdoor?1.15:1);
      rig.fill.intensity=(night?.25:.75)*wx[1]*(dark?.5:1);
      rig.renderer.toneMappingExposure=key[5]*(1-wx[3]*.04);
      var lamps=Math.min(1,key[8]+wx[4]*(night?0:1));if(dark)lamps=Math.max(lamps,.7);state.lamps=lamps;
      (rig.lits||[]).forEach(function(l){l.mat.emissiveIntensity=l.day+(l.night-l.day)*lamps;});(rig.lights||[]).forEach(function(l){l.light.intensity=l.day+(l.night-l.day)*lamps;});
      // background
      var top=key[6].clone().lerp(desat,wx[3]*.5),bot=key[7].clone().lerp(desat,wx[3]*.4);if(rig.outdoor&&!night){top.lerp(new T.Color('#cfe0e6'),.35);}
      var bc=bgCanvas.getContext('2d'),gr=bc.createLinearGradient(0,0,0,256);gr.addColorStop(0,'#'+top.getHexString());gr.addColorStop(1,'#'+bot.getHexString());bc.fillStyle=gr;bc.fillRect(0,0,4,256);bgTex.needsUpdate=true;
      // sky + clouds
      paintSky(T,skyCanvas.getContext('2d'),skyCanvas.width,skyCanvas.height,Object.assign({},env,{hour:hr}),wx);rig.skyTex.needsUpdate=true;
      var lightCol=key[2].clone().lerp(new T.Color('#ffffff'),night?0:.5);if(night)lightCol.multiplyScalar(.45);paintClouds(T,cloudCanvas.getContext('2d'),1024,256,env,wx,lightCol);cloudTex.needsUpdate=true;
      // weather layers
      var rainy=env.weather==='rain'||env.weather==='storm',snowy=env.weather==='snow';
      windows.forEach(function(w){w.drops.visible=rainy;w.frost.visible=snowy||(env.weather==='fog'&&night);
        if(rainy&&!w.rain)w.rain=rainSystem(w.g,w.box,env.weather==='storm'?240:150);if(w.rain)w.rain.obj.visible=rainy;
        if(snowy&&!w.snow)w.snow=snowSystem(w.g,w.box,110);if(w.snow)w.snow.obj.visible=snowy;});
      if(outdoorBox){if(rainy&&!outRain)outRain=rainSystem(scene,outdoorBox,env.weather==='storm'?1900:1300);if(outRain)outRain.obj.visible=rainy;if(snowy&&!outSnow)outSnow=snowSystem(scene,outdoorBox,1100,.055);if(outSnow)outSnow.obj.visible=snowy;}
      if(snowCover)snowCover.visible=snowy;caps.forEach(function(c){c.visible=snowy;});
      if(rig.floorMat&&rig.outdoor&&floorBase){var wet=wx[7];rig.floorMat.roughness=floorBase.rough*(1-.72*wet);rig.floorMat.color.copy(floorBase.color).multiplyScalar(1-.22*wet);rig.floorMat.envMapIntensity=.25+wet*.9;rig.floorMat.needsUpdate=true;}
      scene.fog=env.weather==='fog'&&rig.outdoor?new T.FogExp2(night?'#3a4250':'#d6dcd9',.06):env.weather==='fog'?new T.Fog(night?'#3a4250':'#dfe3e0',14,40):null;
      // light shafts + dust: clear-ish daylight, or a faint moonbeam
      var beam=wx[5]<.6&&!rig.outdoor&&!dark?(night?.025:hr<8||hr>16.5?.065:.055)*(1-wx[5]):0,beamCol=night?'#9fb4e8':hr<8||hr>16.5?'#ffc890':'#fff2d2';
      shaftMat.opacity=beam;shaftMat.color.set(beamCol);
      windows.forEach(function(w){if(w.wd.door||w.wd.side!=='back'){return;}if(w.shaft){w.shaft.geometry.dispose();w.g.parent&&scene.remove(w.shaft);w.shaft=null;}
        if(beam>0&&dir.y>.1){var sg=shaftGeometry(w.wd,dir);w.shaft=new T.Mesh(sg.geo,shaftMat);w.shaft.raycast=noop;w.shaft.renderOrder=5;scene.add(w.shaft);w.shaftBox=sg.box;w.shaftWall=w.g;
          if(!night&&!w.dust){var b=sg.box;w.dust=dustSystem(scene,{x0:b.min.x,x1:b.max.x,y0:.2,y1:Math.min(2.4,b.max.y),z0:Math.max(.05,b.min.z),z1:Math.min(rig.D,b.max.z)},70);}}
        if(w.dust)w.dust.obj.visible=beam>0&&!night;});
      state.light=Math.min(1,key[1]/2.7);state.cover=wx[5];state.wet=wx[7];state.snow=wx[8];state.wind=wx[6];
      effects.forEach(function(e){if(e.apply)e.apply(env,state);});
      return env;
    }
    function syncShaftVisibility(){windows.forEach(function(w){if(w.shaft)w.shaft.visible=w.g.visible;if(w.dust)w.dust.obj.visible=w.g.visible&&shaftMat.opacity>0&&env.band!=='night';});}
    // ----------------------------------------------------------------- animate
    function animated(){if(reduced||!env)return false;return true;}
    // Frame budget: particles need smooth motion; calm weather only drifts clouds and sways plants.
    function fps(){if(!env)return 0;var w=env.weather;return w==='rain'||w==='storm'||w==='snow'?60:w==='wind'?30:14;}
    function update(dt){
      if(!env)return false;time+=dt;var wind=wx[6],slant=wind*.35;
      cloudTex.offset.x=(cloudTex.offset.x+dt*(.004+wind*.02))%1;
      var rl=env.weather==='storm'?.22:.16;
      windows.forEach(function(w){if(w.rain&&w.rain.obj.visible)w.rain.update(dt,slant,rl);if(w.snow&&w.snow.obj.visible)w.snow.update(dt,wind*.4,time);if(w.dust&&w.dust.obj.visible)w.dust.update(dt,time);});
      if(outRain&&outRain.obj.visible)outRain.update(dt,slant,rl);if(outSnow&&outSnow.obj.visible)outSnow.update(dt,wind*.5,time);
      if(env.weather==='rain'||env.weather==='storm')dropsTex.offset.y=(dropsTex.offset.y+dt*.03)%1;
      var amp=(rig.outdoor?.05:.012)+wind*(rig.outdoor?.12:.05);
      sway.forEach(function(s){var a=Math.sin(time*(s.kind==='chime'?2.2:s.kind==='tree'?.9:1.4)+s.phase)*amp*(s.kind==='tree'?.3:1)*(s.kind==='curtain'?(wind>.4?1:.25):1)+Math.sin(time*3.1+s.phase*2)*amp*.25;if(s.kind==='curtain')s.obj.rotation.x=s.rx+Math.abs(a)*.8;else{s.obj.rotation.z=s.rz+a;s.obj.rotation.x=s.rx+a*.5;}});
      // lightning
      if(env.weather==='storm'){nextFlash-=dt;if(nextFlash<=0){flash=1;nextFlash=3.5+Math.random()*6;}}
      if(flash>0){flash=Math.max(0,flash-dt*5);var f=flash>.6||(flash<.4&&flash>.25)?1:0;rig.flashLight.intensity=f*(rig.outdoor?4:2.4);if(rig.skyMat)rig.skyMat.color.setScalar(1+f*1.8);}else{rig.flashLight.intensity=0;if(rig.skyMat)rig.skyMat.color.setScalar(1);}
      state.flash=flash;effects.forEach(function(e){if(e.update)e.update(dt,time,state);});
      syncShaftVisibility();
      return true;
    }
    function dispose(){effects.forEach(function(e){if(e.dispose)e.dispose();});windows.forEach(function(w){if(w.shaft)w.shaft.geometry.dispose();});owned.forEach(function(o){if(o.dispose)o.dispose();});}
    Object.keys(extraEffects).forEach(function(name){try{var e=extraEffects[name](rig);if(e)effects.push(e);}catch(err){console.warn('Room3D effect failed:',name,err);}});
    return {apply:apply,update:update,animated:animated,fps:fps,dispose:dispose,syncVisibility:syncShaftVisibility,get environment(){return env;},get state(){return state;}};
  }
  function skyColors(T,env){var hr=hourOf(env),wx=WX[env.weather]||WX.clear,c=lerpKeys(T,SKY,hr,['c','c']),night=env.band==='night';c[0].lerp(new T.Color(night?'#18222d':'#9aa7ad'),wx[3]);c[1].lerp(new T.Color(night?'#2a3640':'#cdd4d1'),wx[3]);return c;}
  root.Room3DAtmosphere={create:create,skyColors:skyColors,paintClouds:paintClouds,lerpKeys:lerpKeys,KEYS:KEYS,WX:WX,hourOf:hourOf,makeEnvironment:makeEnvironment,paintSky:paintSky,weathers:WEATHERS.slice(),bandOf:bandOf,registerEffect:function(name,factory){if(typeof factory==='function')extraEffects[name]=factory;else delete extraEffects[name];},effects:extraEffects};
})(window);
