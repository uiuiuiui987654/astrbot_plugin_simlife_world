/* 3D outing destinations for Room3D (bedroom-3d.js, "destination" mode).
   Every place has a street view (outdoor) and, where GarageDestinations has one, an interior.
   Scenes follow the art direction already written in DestinationArt.descriptions /
   GarageDestinations: same buildings, same props, now as real geometry.
   Coordinates are metres: x ∈ [0,W] left→right, z ∈ [0,D] back→front (camera side), y up.
   Everything that could become clickable later is tagged with kit.prop(...) (see Room3D.onPropClick). */
(function(root){
  'use strict';
  var PI=Math.PI;
  function rng(seed){var s=Math.abs(seed|0)%2147483646||1;return function(){s=(s*16807)%2147483647;return (s-1)/2147483646;};}
  function noop(){}
  // ---------------------------------------------------------------- textures
  function cachedTex(k,key,paint,w,h){k._dtex=k._dtex||{};if(!k._dtex[key])k._dtex[key]=k.canvasTexture(paint,w||256,h||256,[1,1]);return k._dtex[key];}
  function tiled(k,key,paint,rx,ry,w,h){var t=k.trackTexture(cachedTex(k,key,paint,w,h).clone());t.wrapS=t.wrapT=k.T.RepeatWrapping;t.repeat.set(rx,ry);t.needsUpdate=true;return t;}
  var PAINT={
    paving:function(c,w,h){c.fillStyle='#b9b0a0';c.fillRect(0,0,w,h);for(var i=0;i<4;i++)for(var j=0;j<4;j++){c.fillStyle=['#d8cfbf','#d0c6b4','#ddd5c6','#cfc8ba'][(i*3+j)%4];c.fillRect(i*w/4+2,j*h/4+2,w/4-4,h/4-4);}},
    cobble:function(c,w,h){c.fillStyle='#7d7468';c.fillRect(0,0,w,h);var r=rng(3);for(var j=0;j<10;j++)for(var i=0;i<10;i++){c.fillStyle=['#a99c8a','#b6a994','#9c907f','#c0b4a0'][(i+j*3)%4];c.beginPath();c.ellipse(i*w/10+w/20+(j%2)*w/20,j*h/10+h/20,w/23+r()*2,h/24+r()*2,r(),0,PI*2);c.fill();}},
    asphalt:function(c,w,h){c.fillStyle='#5d6066';c.fillRect(0,0,w,h);for(var i=0;i<1800;i++){c.fillStyle=i%2?'#686b71':'#55585e';c.fillRect((i*73)%w,(i*151)%h,2,2);}},
    sand:function(c,w,h){c.fillStyle='#e6d3a8';c.fillRect(0,0,w,h);for(var i=0;i<2600;i++){c.fillStyle=['#dcc79a','#efdfb8','#d6c08f'][i%3];c.fillRect((i*73)%w,(i*151)%h,2,2);}},
    grass:function(c,w,h){c.fillStyle='#93a87c';c.fillRect(0,0,w,h);for(var i=0;i<5000;i++){c.fillStyle=['#86a070','#9fb486','#7c9668','#a7b98d'][i%4];c.fillRect((i*73.1)%w,(i*151.7)%h,2,3+(i%3));}},
    gravel:function(c,w,h){c.fillStyle='#d6cfc2';c.fillRect(0,0,w,h);for(var i=0;i<3500;i++){c.fillStyle=['#c4bcae','#e3ddd2','#b8b0a2'][i%3];c.beginPath();c.arc((i*73)%w,(i*151)%h,1.5,0,PI*2);c.fill();}},
    dirt:function(c,w,h){c.fillStyle='#a48b6a';c.fillRect(0,0,w,h);for(var i=0;i<2600;i++){c.fillStyle=['#977f60','#b39a78','#8d7658'][i%3];c.fillRect((i*73)%w,(i*151)%h,3,2);}},
    deck:function(c,w,h){c.fillStyle='#7b6550';c.fillRect(0,0,w,h);for(var j=0;j<8;j++){c.fillStyle=['#b39d83','#a8927a','#bca78c','#ae977d'][j%4];c.fillRect(0,j*h/8+2,w,h/8-4);}},
    water:function(c,w,h){c.fillStyle='#ffffff';c.fillRect(0,0,w,h);c.strokeStyle='rgba(120,150,170,.35)';c.lineWidth=2;for(var j=0;j<14;j++){c.beginPath();for(var x=0;x<=w;x+=8)c.lineTo(x,j*h/14+Math.sin(x/w*PI*4+j)*4);c.stroke();}},
    tile:function(c,w,h){c.fillStyle='#cfcac0';c.fillRect(0,0,w,h);for(var i=0;i<4;i++)for(var j=0;j<4;j++){c.fillStyle=['#efece6','#e8e4dc','#f3f1ec'][(i+j)%3];c.fillRect(i*w/4+2,j*h/4+2,w/4-4,h/4-4);}}
  };
  function groundMat(k,kind,rx,ry,color,rough){return k.material(color||'#ffffff',rough==null?.9:rough,{map:tiled(k,'g_'+kind,PAINT[kind],rx,ry)});}
  function flat(k,p,x0,x1,z0,z1,y,m){var pl=k.mesh(k.keep(new k.T.PlaneGeometry(x1-x0,z1-z0)),m,p,(x0+x1)/2,y||0,(z0+z1)/2,false);pl.rotation.x=-PI/2;pl.raycast=noop;return pl;}
  function signTex(k,text,o){o=o||{};return k.canvasTexture(function(c,w,h){c.fillStyle=o.bg||'#f6efe2';c.fillRect(0,0,w,h);if(o.border!==false){c.strokeStyle=o.fg||'#5b4a3c';c.lineWidth=h*.06;c.strokeRect(h*.06,h*.06,w-h*.12,h-h*.12);}c.fillStyle=o.fg||'#5b4a3c';var fs=Math.round(h*(o.size||.52));c.font=(o.bold===false?'':'bold ')+fs+'px sans-serif';while(fs>10&&c.measureText(text).width>w*.86){fs-=2;c.font=(o.bold===false?'':'bold ')+fs+'px sans-serif';}c.textAlign='center';c.textBaseline='middle';c.fillText(text,w/2,h*.54);},o.tw||Math.max(256,Math.round(96*(o.aspect||2.7))),o.th||96);}
  function signBoard(k,p,x,y,z,w,h,text,o){o=o||{};var t=signTex(k,text,{bg:o.bg,fg:o.fg,size:o.size,border:o.border,bold:o.bold,aspect:w/h}),m=o.glow?k.material('#ffffff',.6,{map:t,emissive:'#ffffff',emissiveMap:t,emissiveIntensity:.12,lit:[.12,.9]}):k.material('#ffffff',.6,{map:t});var b=k.box(p,x,y,z,w,h,.04,k.mat(o.bg||'#f6efe2',.6),.01);var face=k.mesh(k.keep(new k.T.PlaneGeometry(w-.004,h-.004)),m,b,0,0,.0215,false);face.receiveShadow=true;face.userData.sign=text;if(o.ry)b.rotation.y=o.ry;return b;}
  function litWin(k){return root.Room3DModels.interiorMaterial(k);}
