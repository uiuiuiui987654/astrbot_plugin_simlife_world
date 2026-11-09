/* Room 3D renderer for every room of the house (WebGL / three.js).
   - Furniture coordinates remain owned by RoomModel (plan units, 50 units = 1 m).
   - Furniture/fixture/decor geometry lives in room-3d-models.js (root.Room3DModels).
   - Kept under the historic name Bedroom3D so app.js camera/click integration keeps working.

   Clickable props (reserved interface, not wired yet):
   every non-item object (fixtures and decor) is tagged as a "prop" with userData {propId, propName}.
     Room3D.onPropClick = function(info){ ... }   // info: {room, id, name, object, host}
     engine.pickProp(event) -> {id, name, object} | null
     engine.props -> {propId: THREE.Group}
   While Room3D.onPropClick is null, clicking a prop does nothing (current behaviour).

   Time of day / weather (room-3d-atmosphere.js):
     Room3D.setEnvironment({hour:21.5, weather:'rain'})   // every mounted room, no rebuild
     engine.setEnvironment(env) / engine.environment
     Room3D.makeEnvironment({hour, weather}) and Room3D.registerEffect(name, factory) for future effects.
   The "环境" toolbar button opens a local preview of any time/weather (does not touch app state). */
(function(root){
  'use strict';
  var scriptURL=document.currentScript.src,libraryURL=new URL('vendor/three.module.js',scriptURL).href;
  var library,active=new Map(),views={},pending=false,SCALE=1/50;
  var ROOMS={客厅:[300,220],浴室:[180,220],厨房:[260,220],餐厅:[330,240],健身室:[240,240],阳台:[170,240],玄关:[780,120],卧室:[300,220],衣帽间:[180,220],书房:[260,220],画室:[330,240],影音室:[240,240],露台:[170,240],楼梯厅:[780,120],车库:[440,400]};
  var MIRRORED=/浴室|阳台|衣帽间|玄关|露台/,OUTDOOR=/阳台|露台/,CORRIDOR=/玄关|楼梯厅/;
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function floorOf(room){return root.SceneStudio&&root.SceneStudio.floorFor?root.SceneStudio.floorFor(room):1;}
  function supports(room){return !!(ROOMS[room]&&root.RoomModel&&root.Room3DModels);}
  function homeView(room,fit){return {theta:CORRIDOR.test(room)?0:OUTDOOR.test(room)?.62:MIRRORED.test(room)?.52:-.52,phi:CORRIDOR.test(room)?1.08:OUTDOOR.test(room)?.98:1.02,distance:fit};}
  function markup(now,items,env,look,room){
    room=room||'卧室';
    var local=items.filter(function(i){return i.room===room;}),config={room:room,items:local,env:env,look:look||{},activity:now&&now.activity||'自由时间'};
    var fallback=root.SceneStudio?root.SceneStudio.room(room,now,items,env,look):'';
    var badge=root.SceneStudio?root.SceneStudio.badge(env):'';
    return '<div class="bedroom-3d room-3d" data-room="'+esc(room)+'" data-config="'+esc(JSON.stringify(config))+'"><div class="bedroom-3d-fallback">'+fallback+'</div><div class="bedroom-3d-viewport" tabindex="0" role="region" aria-label="'+esc(room)+'3D：拖动旋转，右键或 Shift 拖动平移，滚轮缩放，方向键旋转"></div><div class="room-label">'+esc(room)+' · 3D<small>'+floorOf(room)+'F · '+esc(config.activity)+'</small></div>'+badge+'<div class="appearance-badge">'+esc(config.look.name||'白紫日常装')+'</div><div class="bedroom-3d-hint">拖动旋转 · 右键平移 · 滚轮缩放 · 点击家具</div><div class="bedroom-3d-status" role="status">正在布置 3D '+esc(room)+'…</div><div class="bedroom-3d-toolbar" role="group" aria-label="'+esc(room)+'3D控制"><button type="button" data-bed3d="items" aria-expanded="false">家具</button><button type="button" data-bed3d="out" aria-label="缩小">−</button><button type="button" data-bed3d="in" aria-label="放大">＋</button><button type="button" data-bed3d="reset">复位</button><button type="button" data-bed3d="expand" aria-label="全屏查看">放大</button><button type="button" data-bed3d="env" aria-expanded="false">环境</button><button type="button" data-bed3d="plan">平面</button></div><div class="room-3d-env" hidden><label>时间 <output>--:--</output><input type="range" min="0" max="23.75" step="0.25" data-env="hour"></label><label>天气 <select data-env="weather"><option value="clear">晴朗</option><option value="cloudy">多云</option><option value="rain">小雨</option><option value="storm">雷雨</option><option value="snow">下雪</option><option value="fog">有雾</option><option value="wind">大风</option></select></label><button type="button" data-env="live">跟随当前</button></div><div class="bedroom-3d-items" hidden>'+local.map(function(i){return '<button type="button" class="furniture-hit" data-id="'+esc(i.id)+'">'+esc(i.name||i.id)+'</button>';}).join('')+'</div><div class="bedroom-3d-tooltip"></div></div>';
  }
  // Outing destinations (street view / interior) — models in destination-3d.js.
  function supportsDestination(key,view){return !!(root.Destination3DModels&&root.Destination3DModels.supports(key,view||'outdoor'));}
  function markupDestination(o){
    var config={dest:{key:o.key,view:o.view||'outdoor',mode:o.mode||''},items:[],env:o.env,look:o.look||{},activity:''};
    var badge=root.SceneStudio?root.SceneStudio.badge(o.env):'';
    var envPanel='<div class="room-3d-env" hidden><label>时间 <output>--:--</output><input type="range" min="0" max="23.75" step="0.25" data-env="hour"></label><label>天气 <select data-env="weather"><option value="clear">晴朗</option><option value="cloudy">多云</option><option value="rain">小雨</option><option value="storm">雷雨</option><option value="snow">下雪</option><option value="fog">有雾</option><option value="wind">大风</option></select></label><button type="button" data-env="live">跟随当前</button></div>';
    return '<div class="bedroom-3d room-3d dest-3d" data-dest="'+esc(o.key)+'" data-view="'+esc(config.dest.view)+'" data-config="'+esc(JSON.stringify(config))+'"><div class="bedroom-3d-fallback">'+(o.fallback||'')+'</div><div class="bedroom-3d-viewport" tabindex="0" role="region" aria-label="外出场景3D：拖动旋转，右键或 Shift 拖动平移，滚轮缩放"></div>'+(o.labelHtml||'')+badge+'<div class="bedroom-3d-hint">拖动旋转 · 右键平移 · 滚轮缩放</div><div class="bedroom-3d-status" role="status">正在布置 3D 场景…</div><div class="bedroom-3d-toolbar" role="group" aria-label="场景3D控制"><button type="button" data-bed3d="out" aria-label="缩小">−</button><button type="button" data-bed3d="in" aria-label="放大">＋</button><button type="button" data-bed3d="reset">复位</button><button type="button" data-bed3d="expand" aria-label="全屏查看">放大</button><button type="button" data-bed3d="env" aria-expanded="false">环境</button><button type="button" data-bed3d="plan">平面</button></div>'+envPanel+'<div class="bedroom-3d-items" hidden></div><div class="bedroom-3d-tooltip"></div></div>';
  }
  // Room interior bounds (plan units) derived from every planned piece, so walls hug the furniture.
  function bounds(room){
    var M=root.RoomModel,models=root.Room3DModels,size=ROOMS[room],rects=[];
    (models.roomItems[room]||[]).forEach(function(id){var p=M.plan[id];if(p)rects.push(p);});
    (M.fixtures[room]||[]).forEach(function(f){rects.push([f.x,f.y,f.w,f.d]);});
    if(M.rugs[room])rects.push(M.rugs[room]);
    var a=M.anchors[room];if(a)rects.push([a[0]-8,a[1]-8,16,16]);
    var minX=Math.min.apply(null,rects.map(function(r){return r[0];})),minY=Math.min.apply(null,rects.map(function(r){return r[1];}));
    var maxX=Math.max.apply(null,rects.map(function(r){return r[0]+r[2];})),maxY=Math.max.apply(null,rects.map(function(r){return r[1]+r[3];}));
    var corridor=CORRIDOR.test(room);
    return {OX:Math.min(12,minX-2),OZ:corridor?minY-2:Math.min(35,minY-2),RX:Math.max(size[0]-12,maxX+2),RZ:corridor?Math.max(size[1]+(((models.rooms[room]||{}).extraDepth)||0),maxY+2):Math.max(size[1]-10,maxY+2)};
  }
  async function mount(host){
    host.dataset.wired='true';
    var fallback=function(message){host.dataset.ready='false';host.classList.add('show-plan');host.querySelector('.bedroom-3d-status').textContent=message;host.querySelector('.bedroom-3d-toolbar').hidden=true;};
    try{
      library=library||import(libraryURL);var T=await library;if(!host.isConnected)return;
      var cfg=JSON.parse(host.dataset.config),room=cfg.room||'卧室',env=cfg.env,night=env.dark,viewport=host.querySelector('.bedroom-3d-viewport'),MODELS=root.Room3DModels,RM=root.RoomModel;
      var DEST=cfg.dest?root.Destination3DModels:null,dspec=DEST?DEST.spec(cfg.dest.key,cfg.dest.view,cfg.dest.mode):null,destAnchor=null,built=null;if(cfg.dest&&!dspec)throw new Error('destination not supported');if(DEST)room='dest:'+cfg.dest.key+':'+cfg.dest.view+(cfg.dest.mode?':'+cfg.dest.mode:'');
      if(!DEST&&!supports(room))throw new Error('room not supported: '+room);
      var outdoor=DEST?dspec.outdoor:OUTDOOR.test(room),corridor=!DEST&&CORRIDOR.test(room),cfgRoom=DEST?{floor:dspec.floor,dark:dspec.dark,height:dspec.H}:(MODELS.rooms[room]||{}),theme=DEST?dspec.theme:MODELS.theme(room);
      var renderer=new T.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
      renderer.setPixelRatio(Math.min(root.devicePixelRatio||1,1.6));renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=night?1.15:1.2;
      viewport.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-hidden','true');
      var scene=new T.Scene();scene.background=new T.Color(night?'#343c50':outdoor?'#dfe6dc':'#e5e4da');if(env.hour==null&&root.Room3DAtmosphere)env=Object.assign({},env,{hour:{night:22,dawn:6.8,day:12,dusk:17.8}[env.band]});
      var Bd=DEST?{OX:0,OZ:0,RX:dspec.W/SCALE,RZ:dspec.D/SCALE}:bounds(room),W=(Bd.RX-Bd.OX)*SCALE,D=(Bd.RZ-Bd.OZ)*SCALE,H=cfgRoom.height||2.64,scale=SCALE;
      var X=function(v){return (v-Bd.OX)*scale;},Z=function(v){return (v-Bd.OZ)*scale;};
      var fit=Math.max(3.2,.5*Math.hypot(W,D,1.6)/Math.sin(T.MathUtils.degToRad(19.5))*.9);
      if(corridor)fit=Math.min(fit,9.5);if(outdoor&&!DEST)fit*=1.18;if(DEST&&!dspec.interior)fit=Math.max(13,Math.hypot(W,D)*.8);
      var HOME=DEST?Object.assign({theta:dspec.interior?-.52:-.28,phi:dspec.interior?1.02:1.16,distance:fit},dspec.camera||{}):homeView(room,fit),freshView=!views[room],view=views[room]||(views[room]=Object.assign({},HOME)),orbit=Object.assign({},view);
      var camera=new T.PerspectiveCamera(39,1,.2,200),homeTarget=DEST?new T.Vector3(W/2,dspec.interior?.8:2.2,dspec.interior?D/2:D*.5):new T.Vector3(corridor?Math.min(W/2,X((RM.anchors[room]||[0])[0])):W/2,.72,D/2),target=homeTarget.clone(),ray=new T.Raycaster(),pointer=new T.Vector2();
      var textures=[],materials=[],geometries=[],meshes=[],itemGroups={},propGroups={},mirrors=[],lights=[],dead=false,frame=0,character,walls={};
      var state={host:host,room:room,renderer:renderer,scene:scene,camera:camera,groups:itemGroups,props:propGroups,orbit:orbit,target:target,render:render,dispose:dispose,project:project,pick:pick,pickProp:pickProp,size:{W:W,D:D,H:H}};active.set(host,state);
      // ---------- kit: helpers shared with the model builders ----------
      var matCache={},geoCache={};
      var lits=[],lampLights=[];
      function material(color,roughness,extra){var lit=extra&&extra.lit;if(lit){extra=Object.assign({},extra);delete extra.lit;}var m=new T.MeshStandardMaterial(Object.assign({color:color,roughness:roughness==null?.78:roughness},extra));materials.push(m);if(lit)lits.push({mat:m,day:lit[0],night:lit[1]});return m;}
      function mat(color,roughness,metal){var key=color+'|'+roughness+'|'+metal;return matCache[key]||(matCache[key]=material(color,roughness,metal?{metalness:metal}:undefined));}
      function canvasTexture(paint,w,h,repeat){var canvas=document.createElement('canvas');canvas.width=w||512;canvas.height=h||512;paint(canvas.getContext('2d'),canvas.width,canvas.height);var t=new T.CanvasTexture(canvas);t.colorSpace=T.SRGBColorSpace;t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());if(repeat){t.wrapS=t.wrapT=T.RepeatWrapping;t.repeat.set(repeat[0],repeat[1]);}textures.push(t);return t;}
      function keep(g){geometries.push(g);return g;}
      function rawBox(w,h,d,r){
        if(!r)return new T.BoxGeometry(w,h,d);
        r=Math.min(r,w*.24,h*.24,d*.24);var x=-w/2+r,y=-h/2+r,ww=w-2*r,hh=h-2*r,cr=Math.min(r,ww*.24,hh*.24),shape=new T.Shape();
        shape.moveTo(x+cr,y);shape.lineTo(x+ww-cr,y);shape.quadraticCurveTo(x+ww,y,x+ww,y+cr);shape.lineTo(x+ww,y+hh-cr);shape.quadraticCurveTo(x+ww,y+hh,x+ww-cr,y+hh);shape.lineTo(x+cr,y+hh);shape.quadraticCurveTo(x,y+hh,x,y+hh-cr);shape.lineTo(x,y+cr);shape.quadraticCurveTo(x,y,x+cr,y);
        var g=new T.ExtrudeGeometry(shape,{depth:Math.max(.0001,d-2*r),bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:r,bevelThickness:r,curveSegments:4});g.translate(0,0,-(d-2*r)/2);g.computeVertexNormals();
        var pos=g.attributes.position,norm=g.attributes.normal,uv=g.attributes.uv;
        for(var i=0;i<pos.count;i++){var ax=Math.abs(norm.getX(i)),ay=Math.abs(norm.getY(i)),az=Math.abs(norm.getZ(i));if(ay>=ax&&ay>=az)uv.setXY(i,pos.getX(i)/w+.5,pos.getZ(i)/d+.5);else if(az>=ax)uv.setXY(i,pos.getX(i)/w+.5,pos.getY(i)/h+.5);else uv.setXY(i,pos.getZ(i)/d+.5,pos.getY(i)/h+.5);}
        uv.needsUpdate=true;return g;
      }
      function cached(key,make){return geoCache[key]||(geoCache[key]=keep(make()));}
      function boxGeometry(w,h,d,r){return cached('b'+w.toFixed(3)+','+h.toFixed(3)+','+d.toFixed(3)+','+(r||0).toFixed(3),function(){return rawBox(w,h,d,r);});}
      function mesh(g,m,parent,x,y,z,shadow){var a=new T.Mesh(g,m);a.position.set(x||0,y||0,z||0);a.castShadow=shadow!==false;a.receiveShadow=true;(parent||scene).add(a);meshes.push(a);return a;}
      function box(p,x,y,z,w,h,d,m,r){return mesh(boxGeometry(w,h,d,r),m,p,x,y,z);}
      function bx(p,x,y0,z,w,h,d,m,r){return box(p,x,y0+h/2,z,w,h,d,m,r);}
      function sph(p,x,y,z,sx,sy,sz,m){var big=Math.max(sx,sy==null?sx:sy,sz==null?sx:sz)>.06,g=cached(big?'sh':'sl',function(){return big?new T.SphereGeometry(1,22,16):new T.SphereGeometry(1,10,8);});var a=mesh(g,m,p,x,y,z);a.scale.set(sx,sy==null?sx:sy,sz==null?sx:sz);return a;}
      function cyl(p,x,y,z,r1,r2,h,m,open,seg){return mesh(cached('c'+[r1,r2,h,!!open,seg||0].join(','),function(){return new T.CylinderGeometry(r1,r2,h,seg||(Math.max(r1,r2)>.08?28:14),1,!!open);}),m,p,x,y,z);}
      function cylB(p,x,y0,z,r1,r2,h,m,open,seg){return cyl(p,x,y0+h/2,z,r1,r2,h,m,open,seg);}
      function tor(p,x,y,z,r,t,m,arc){return mesh(cached('t'+[r,t,arc||0].join(','),function(){return new T.TorusGeometry(r,t,8,32,arc||Math.PI*2);}),m,p,x,y,z);}
      function group(p,x,y,z){var g=new T.Group();if(x!=null)g.position.set(x,y||0,z||0);(p||scene).add(g);return g;}
      function legs(p,L,Dd,h,inset,m,r){var k=inset==null?.08:inset;[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){cylB(p,q[0]*(L/2-k),0,q[1]*(Dd/2-k),r||.024,(r||.024)*.75,h,m||kit.darkWood);});}
      function batch(parent,m){var parts=[];return {box:function(x,y,z,w,h,d,r){var g=rawBox(w,h,d,r);g.translate(x,y,z);parts.push(g);return this;},done:function(){
        if(!parts.length)return null;var acc={position:[],normal:[],uv:[]};parts.forEach(function(g){var n=g.index?g.toNonIndexed():g;['position','normal','uv'].forEach(function(k){var a=n.attributes[k].array;for(var i=0;i<a.length;i++)acc[k].push(a[i]);});if(n!==g)n.dispose();g.dispose();});
        var out=new T.BufferGeometry();out.setAttribute('position',new T.Float32BufferAttribute(acc.position,3));out.setAttribute('normal',new T.Float32BufferAttribute(acc.normal,3));out.setAttribute('uv',new T.Float32BufferAttribute(acc.uv,2));out.computeBoundingSphere();return mesh(keep(out),m,parent,0,0,0);}};}
      function pillow(w,h,d){return cached('p'+[w,h,d].join(','),function(){var g=new T.BoxGeometry(w,h,d,14,4,10),p=g.attributes.position;for(var i=0;i<p.count;i++){var nx=p.getX(i)/(w/2),nz=p.getZ(i)/(d/2),edge=Math.max(Math.abs(nx),Math.abs(nz)),t=1-Math.pow(edge,2.6)*.8;p.setY(i,p.getY(i)*t);p.setX(i,p.getX(i)*(1-.07*nz*nz));p.setZ(i,p.getZ(i)*(1-.07*nx*nx));}g.computeVertexNormals();return g;});}
      function drape(w,l,hangX,hangZ,r,puff){
        return cached('d'+[w,l,hangX,hangZ,r,puff].join(','),function(){
          var a=r*Math.PI/2,tw=w+2*(a+hangX),tl=l+(hangZ?a+hangZ:0),g=new T.PlaneGeometry(tw,tl,Math.max(2,Math.round(tw*26)),Math.max(2,Math.round(tl*22)));g.rotateX(-Math.PI/2);var p=g.attributes.position;
          function fold(c,half,hang){var e=Math.abs(c)-half;if(e<=0||!hang)return [c,0];var s=c<0?-1:1;if(e<a){var t=e/r;return [s*(half+r*Math.sin(t)),r-r*Math.cos(t)];}return [s*(half+r),r+(e-a)];}
          for(var i=0;i<p.count;i++){var x=p.getX(i),z=p.getZ(i)+tl/2-l/2,fx=fold(x,w/2,hangX),fz=hangZ?fold(z,l/2,hangZ):[z,0],dx=fx[1],dz=z>0?fz[1]:0,nx=fx[0],nz=z>0?fz[0]:z;
            if(dx>r)nx+=(nx<0?-1:1)*Math.sin(z*21+1.3)*.011*Math.min(1,(dx-r)/.08);if(dz>r)nz+=Math.sin(x*19)*.011*Math.min(1,(dz-r)/.08);
            var y=-Math.max(dx,dz);if(!dx&&!dz)y+=(puff||0)*(1-Math.pow(2*x/w,4))*(1-Math.pow(Math.max(0,2*z/l),6));p.setXYZ(i,nx,y,nz);}
          g.computeVertexNormals();return g;});
      }
      function emissive(color,day,nightI,extra){return material(color,.5,Object.assign({emissive:color,emissiveIntensity:day,lit:[day,nightI]},extra));}
      function pointLight(p,x,y,z,color,dayI,nightI,dist){var l=new T.PointLight(color,dayI,dist||4,2);l.position.set(x,y,z);(p||scene).add(l);lights.push(l);lampLights.push({light:l,day:dayI,night:nightI});return l;}
      function mirror(m){m.castShadow=false;mirrors.push(m);return m;}
      // Reserved: tag any object as a prop so it can be made clickable later via Room3D.onPropClick.
      function prop(p,id,name){var g=new T.Group();g.userData.propId=id;g.userData.propName=name||id;(p||scene).add(g);propGroups[id]=g;return g;}
      var kit={T:T,THREE:T,room:room,night:night,env:env,W:W,D:D,H:H,scale:scale,X:X,Z:Z,material:material,mat:mat,canvasTexture:canvasTexture,keep:keep,mesh:mesh,box:box,bx:bx,sph:sph,cyl:cyl,cylB:cylB,tor:tor,group:group,legs:legs,batch:batch,pillow:pillow,drape:drape,emissive:emissive,pointLight:pointLight,mirror:mirror,prop:prop,boxGeometry:boxGeometry,theme:theme,outdoor:outdoor,corridor:corridor,windows:[],swayers:[],snowCaps:[],scene:scene,trackMaterial:function(m){materials.push(m);return m;},trackTexture:function(t){textures.push(t);return t;}};
      MODELS.materials(kit);
      // ---------- floor ----------
      // Floor (with optional openings, e.g. the stairwell going down from 2F) and the slab under it.
      var floorMat;if(DEST&&dspec.outdoor){floorMat=material('#ffffff',.9);}else{
      var holes=(cfgRoom.floorHoles||[]).filter(function(id){return RM.plan[id]&&cfg.items.some(function(i){return i.id===id;});}).map(function(id){var p=RM.plan[id];return [X(p[0]),X(p[0]+p[2]),Z(p[1]),Z(p[1]+p[3])];});
      var floorRects=[[0,W,0,D]];holes.forEach(function(h){var next=[];floorRects.forEach(function(r){if(h[1]<=r[0]||h[0]>=r[1]||h[3]<=r[2]||h[2]>=r[3]){next.push(r);return;}var x0=Math.max(r[0],h[0]),x1=Math.min(r[1],h[1]);if(h[2]>r[2])next.push([x0,x1,r[2],h[2]]);if(h[3]<r[3])next.push([x0,x1,h[3],r[3]]);if(h[0]>r[0])next.push([r[0],h[0],r[2],r[3]]);if(h[1]<r[1])next.push([h[1],r[1],r[2],r[3]]);});floorRects=next.filter(function(r){return r[1]-r[0]>.005&&r[3]-r[2]>.005;});});
      var slabMat=mat(outdoor?'#a9a08f':'#bba58d',.9);floorRects.forEach(function(r){var e=.08,x0=r[0]===0?-e:r[0],x1=r[1]===W?W+e:r[1],z0=r[2]===0?-e:r[2],z1=r[3]===D?D+e:r[3];bx(null,(x0+x1)/2,-.226,(z0+z1)/2,x1-x0,.22,z1-z0,slabMat,holes.length?0:.04);});
      var floorTex=MODELS.floorTexture(kit,cfgRoom.floor||'wood'),fsize=floorTex.userData.size||2.2,floorMat=material('#ffffff',cfgRoom.floor==='tile'?.4:cfgRoom.floor==='carpet'?1:.72,{map:floorTex}),floor=null;
      floorRects.forEach(function(r){var geo=keep(new T.PlaneGeometry(r[1]-r[0],r[3]-r[2])),uv=geo.attributes.uv,pos=geo.attributes.position;for(var i=0;i<uv.count;i++)uv.setXY(i,(pos.getX(i)+(r[0]+r[1])/2)/fsize,(-pos.getY(i)+(r[2]+r[3])/2)/fsize*-1+0);uv.needsUpdate=true;var f=mesh(geo,floorMat,null,(r[0]+r[1])/2,0,(r[2]+r[3])/2,false);f.rotation.x=-Math.PI/2;if(!floor)floor=f;});
      floorTex.repeat.set(1,1);}
      // ---------- walls (4 cutaway walls; the ones between camera and room hide) ----------
      var sky=MODELS.skyTexture(kit);
      function wallFrame(side){var g=new T.Group();scene.add(g);g.userData.side=side;
        if(side==='right'){g.position.set(W,0,0);g.rotation.y=-Math.PI/2;}else if(side==='left'){g.position.set(0,0,D);g.rotation.y=Math.PI/2;}else if(side==='front'){g.position.set(W,0,D);g.rotation.y=Math.PI;}
        g.userData.length=side==='back'||side==='front'?W:D;walls[side]=g;return g;}
      // Converts a world point on a wall into the wall's local "u" coordinate.
      function wallU(side,x,z){return side==='back'?x:side==='right'?z:side==='left'?D-z:W-x;}
      kit.walls=walls;kit.wallU=wallU;kit.sky=sky;
      var wallSpecs=DEST?(dspec.walls||{}):MODELS.walls(kit,cfgRoom,{plan:RM.plan,X:X,Z:Z,W:W,D:D,outdoor:outdoor,corridor:corridor});
      ['back','right','left','front'].forEach(function(side){var spec=wallSpecs[side];if(!spec)return;var g=wallFrame(side);MODELS.buildWall(kit,g,g.userData.length,spec,side);});
      // ---------- rug ----------
      var rug=RM.rugs[room];if(rug){bx(null,X(rug[0]+rug[2]/2),.003,Z(rug[1]+rug[3]/2),rug[2]*scale,.022,rug[3]*scale,MODELS.rugMaterial(kit,room),.008).castShadow=false;}
      // ---------- fixtures (non-item furniture: tagged as props) ----------
      function placeGroup(g,cx,cz,face,base){var pivot=new T.Group();pivot.position.set(cx,base||0,cz);pivot.rotation.y={S:0,E:Math.PI/2,W:-Math.PI/2,N:Math.PI}[face||'S']||0;g.add(pivot);return pivot;}
      function frameOf(p,face){var sideways=/E|W/.test(face);return {L:(sideways?p[3]:p[2])*scale,Dd:(sideways?p[2]:p[3])*scale};}
      var fixtureTop={};
      (RM.fixtures[room]||[]).forEach(function(f){
        var g=prop(null,f.id,MODELS.names[f.id]||f.id),fr=frameOf([f.x,f.y,f.w,f.d],f.facing),pivot=placeGroup(g,X(f.x+f.w/2),Z(f.y+f.d/2),f.facing,0);
        fixtureTop[f.id]=f.h*scale;
        (MODELS.fixtures[f.id]||MODELS.fixtures[f.type]||MODELS.fixtures.counter)(kit,pivot,{L:fr.L,Dd:fr.Dd,H:f.h*scale,face:f.facing,fixture:f});
      });
      // ---------- items ----------
      var owned=new Set(cfg.items.map(function(i){return i.id;}));
      function supportTop(mount){if(!mount||mount==='wall'||mount==='ceiling')return 0;if(fixtureTop[mount]!=null)return fixtureTop[mount];if(MODELS.surfaceTop[mount]!=null)return MODELS.surfaceTop[mount];return RM.plan[mount]?RM.meta({id:mount},MODELS.types[mount]||'table').height*scale:0;}
      cfg.items.forEach(function(item){
        var p=RM.plan[item.id],g=new T.Group();g.userData.itemId=item.id;scene.add(g);itemGroups[item.id]=g;
        if(item.custom_place && item.place && p){
          var cx=Math.max(.05,Math.min(.95,Number(item.place.x)||.5))*W;
          var cz=Math.max(.05,Math.min(.95,Number(item.place.y)||.5))*D;
          var cmeta=RM.meta(item,MODELS.types[item.id]||'box'),cfr=frameOf(p,cmeta.facing);
          var cpivot=placeGroup(g,cx,cz,item.place.facing||cmeta.facing);
          (MODELS.items[item.id]||MODELS.placeholder)(kit,cpivot,{L:cfr.L,Dd:cfr.Dd,H:cmeta.height*scale,face:item.place.facing||cmeta.facing,mount:'',base:0,item:item,plan:p,owned:owned,ceiling:H});
          return;
        }
        if(!p||item.slot_id){if(!item.place)return;var x=Math.max(.05,Math.min(.95,Number(item.place.x)||.5))*W,z=Math.max(.05,Math.min(.95,Number(item.place.y)||.5))*D;if(MODELS.goodsPlace)MODELS.goodsPlace(kit,g,item,{x:x,z:z,base:Math.max(0,(Number(item.place.z_cm)||0)/100)});else MODELS.placeholder(kit,placeGroup(g,x,z,'S',0),{L:.3,Dd:.25,H:.3,item:item});return;}
        var meta=RM.meta(item,MODELS.types[item.id]||'box'),fr=frameOf(p,meta.facing),mount=p[4]||'',pivot=placeGroup(g,X(p[0]+p[2]/2),Z(p[1]+p[3]/2),meta.facing,supportTop(mount));
        var s={L:fr.L,Dd:fr.Dd,H:meta.height*scale,face:meta.facing,mount:mount,base:pivot.position.y,item:item,plan:p,owned:owned,ceiling:H};
        (MODELS.items[item.id]||MODELS.placeholder)(kit,pivot,s);
      });
      if(MODELS.goodsSnap){scene.updateMatrixWorld(true);MODELS.goodsSnap(kit);}
      // ---------- room decor (props) ----------
      if(MODELS.decor[room])MODELS.decor[room](kit,{plan:RM.plan,fixtures:RM.fixtures[room]||[],X:X,Z:Z,W:W,D:D,H:H,walls:walls,wallU:wallU,owned:owned});
      // ---------- open-air rooms: the house, the garden and the sky around them ----------
      if(DEST){kit.destination=true;built=DEST.build(kit,{key:cfg.dest.key,view:cfg.dest.view,mode:cfg.dest.mode||'',W:W,D:D,H:H})||{};kit.pose=built.pose||null;destAnchor=built.anchor||null;if(kit.floorMat)floorMat=kit.floorMat;if(built.camera){Object.assign(HOME,built.camera);if(freshView){Object.assign(view,HOME);Object.assign(orbit,HOME);}}}
      else if(outdoor&&root.Room3DOutdoor){try{root.Room3DOutdoor.build(kit,{groundY:cfgRoom.ground==null?-.45:cfgRoom.ground,cfg:cfgRoom});}catch(err){console.warn('Room 3D outdoor world skipped',err);}}
      // ---------- lighting (values are driven by the atmosphere controller) ----------
      var hemi=new T.HemisphereLight('#fff4dc','#a6ad94',1.9);scene.add(hemi);
      var sun=new T.DirectionalLight('#fff1d4',2.6),span=Math.max(W,D)/2+2.2;scene.add(sun,sun.target);
      sun.castShadow=true;var res=Math.max(W,D)>9?2048:1536;sun.shadow.mapSize.set(res,res);Object.assign(sun.shadow.camera,{left:-span,right:span,top:span,bottom:-span,near:.5,far:40});sun.shadow.normalBias=.025;sun.shadow.bias=-.0003;
      var fill=new T.DirectionalLight('#e8e2ff',.75);fill.position.set(W/2-3,3.5,D+6);scene.add(fill);
      var flashLight=new T.DirectionalLight('#dfe8ff',0);flashLight.position.set(W/2,8,-4);scene.add(flashLight);
      if(!outdoor){var Lt=MODELS.lighting(kit,cfgRoom);if(Lt.ceiling){var cl=new T.PointLight('#ffd9a8',0,Math.max(W,D)*1.4,1.6);cl.position.set(W/2,H-.25,D/2);scene.add(cl);lights.push(cl);lampLights.push({light:cl,day:0,night:Lt.ceiling});}}
      // ---------- reflections: cube captures for mirrors, plus one for metal/glass/floor sheen ----------
      var cubeTargets=[],envTarget=null;
      function capture(pos,hide,rt){rt=rt||new T.WebGLCubeRenderTarget(256,{type:T.HalfFloatType});if(cubeTargets.indexOf(rt)<0)cubeTargets.push(rt);var cam=new T.CubeCamera(.05,60,rt);cam.position.copy(pos);if(hide)hide.visible=false;scene.add(cam);cam.update(renderer,scene);scene.remove(cam);if(hide)hide.visible=true;return rt;}
      var mirrorTargets=[];
      function captureAll(){
        try{scene.updateMatrixWorld(true);var wv={};Object.keys(walls).forEach(function(sd){wv[sd]=walls[sd].visible;walls[sd].visible=true;});
          envTarget=capture(new T.Vector3(W/2,1.3,D/2),null,envTarget);var envTex=envTarget.texture;
          kit.metals.forEach(function(m){if(m.envMap!==envTex){m.envMap=envTex;m.envMapIntensity=.9;m.needsUpdate=true;}});
          if(kit.glass.envMap!==envTex){kit.glass.envMap=envTex;kit.glass.envMapIntensity=.7;kit.glass.needsUpdate=true;}
          if(floorMat.envMap!==envTex){floorMat.envMap=envTex;floorMat.envMapIntensity=outdoor?.25:.18;floorMat.needsUpdate=true;}
          mirrors.slice(0,3).forEach(function(m,i){var pos=new T.Vector3(),n=new T.Vector3(0,0,1);m.getWorldPosition(pos);n.transformDirection(m.matrixWorld);pos.addScaledVector(n,.06);mirrorTargets[i]=capture(pos,m,mirrorTargets[i]);if(!m.userData.ownMaterial){m.material=m.material.clone();materials.push(m.material);m.userData.ownMaterial=true;}m.material.envMap=mirrorTargets[i].texture;m.material.needsUpdate=true;});
          Object.keys(wv).forEach(function(sd){walls[sd].visible=wv[sd];});
        }catch(err){console.warn('Room 3D reflections skipped',err);}
      }
      // ---------- atmosphere: time of day + weather ----------
      var ATM=root.Room3DAtmosphere,atmosphere=null;
      if(ATM){atmosphere=ATM.create({T:T,kit:kit,scene:scene,renderer:renderer,sun:sun,hemi:hemi,fill:fill,flashLight:flashLight,center:new T.Vector3(W/2,0,D/2),lits:lits,lights:lampLights,floorMat:floorMat,outdoor:outdoor,awning:!!cfgRoom.awning,groundY:cfgRoom.ground==null?0:cfgRoom.ground,rainArea:DEST&&outdoor?(built&&built.rainArea||{x0:-3,x1:W+3,z0:-2,z1:D+3}):null,sheltered:!!(built&&built.sheltered),dark:!!cfgRoom.dark,W:W,D:D,H:H,skyTex:sky,skyMat:kit.skyMat,room:room,host:host});atmosphere.apply(env);}
      else{sun.position.set(W*.3-1.4,5.6,-3.4);sun.target.position.set(W*.45,0,D*.55);}
      captureAll();
      host.dataset.weather=env.weather;host.dataset.band=env.band;
      // ---------- character billboard ----------
      var look=cfg.look,loader=new T.TextureLoader(),src=look.src||'assets/character_daily.png',anchor=RM.anchors[room]||[(Bd.OX+Bd.RX)/2,(Bd.OZ+Bd.RZ)/2],CX=destAnchor?destAnchor[0]:X(anchor[0]),CZ=destAnchor?destAnchor[1]:Z(anchor[1]);
      if(look.none){host.dataset.textureReady='true';}else loader.load(src,function(t){if(dead){t.dispose();return;}textures.push(t);t.colorSpace=T.SRGBColorSpace;var m=new T.MeshBasicMaterial({map:t,transparent:true,alphaTest:.08,side:T.DoubleSide,depthWrite:true,toneMapped:false});materials.push(m);var geo=keep(new T.PlaneGeometry(1.6*t.image.width/t.image.height,1.6));var pose=built&&built.pose||{};if(pose.clipY!=null){renderer.localClippingEnabled=true;m.clippingPlanes=[new T.Plane(new T.Vector3(0,1,0),-pose.clipY)];}character=mesh(geo,m,scene,CX,.81+(pose.dy||0),CZ,false);kit.character=character;character.userData.character=true;host.dataset.appearance=look.key||'daily';host.dataset.textureReady='true';render();},undefined,function(){host.dataset.textureReady='error';});
      var shadow=sph(null,CX,.05,CZ,.2,.006,.13,material('#4a4252',1,{transparent:true,opacity:.2,depthWrite:false}));shadow.castShadow=false;if(built&&built.pose&&built.pose.hideShadow)shadow.visible=false;if(look.none)shadow.visible=false;
      // ---------- camera / render ----------
      function updateCamera(){
        orbit.phi=T.MathUtils.clamp(orbit.phi,.3,1.36);orbit.distance=T.MathUtils.clamp(orbit.distance,Math.max(2.2,fit*.35),fit*2.2);
        camera.position.set(target.x+orbit.distance*Math.sin(orbit.phi)*Math.sin(orbit.theta),target.y+orbit.distance*Math.cos(orbit.phi),target.z+orbit.distance*Math.sin(orbit.phi)*Math.cos(orbit.theta));camera.lookAt(target);
        var c=camera.position,vis={back:c.z>-.1,front:c.z<D+.1,left:c.x>-.1,right:c.x<W+.1};Object.keys(walls).forEach(function(sd){walls[sd].visible=walls[sd].userData.alwaysVisible||vis[sd];});
        if(atmosphere)atmosphere.syncVisibility();if(character)character.rotation.y=Math.atan2(c.x-character.position.x,c.z-character.position.z);Object.assign(view,orbit);
      }
      function draw(){updateCamera();renderer.render(scene,camera);host.dataset.frames=String((Number(host.dataset.frames)||0)+1);}
      function render(){if(dead||frame||looping)return;frame=requestAnimationFrame(function(){frame=0;if(dead||host.classList.contains('show-plan'))return;draw();});startLoop();}
      // Continuous animation (rain, snow, clouds, sway, lightning) only while visible on screen.
      var looping=false,onScreen=true,last=0,loopFrame=0;
      function canLoop(){return !dead&&atmosphere&&atmosphere.animated()&&onScreen&&!document.hidden&&!host.classList.contains('show-plan');}
      function startLoop(){if(looping||!canLoop())return;looping=true;last=performance.now();loopFrame=requestAnimationFrame(tick);}
      function tick(now){if(!canLoop()){looping=false;return;}loopFrame=requestAnimationFrame(tick);var budget=1000/(atmosphere.fps()||14);if(now-last<budget-2)return;var dt=Math.min(.1,(now-last)/1000);last=now;atmosphere.update(dt);draw();}
      var io=root.IntersectionObserver?new IntersectionObserver(function(es){onScreen=es[0].isIntersecting;if(onScreen)startLoop();}):null;if(io)io.observe(host);
      function onVis(){if(!document.hidden)startLoop();}document.addEventListener('visibilitychange',onVis);
      var recaptureTimer=0;
      function setEnvironment(next){if(dead||!atmosphere)return null;var e=atmosphere.apply(next);host.dataset.weather=e.weather;host.dataset.band=e.band;host.dataset.environment=e.signature||'';syncPanel();clearTimeout(recaptureTimer);recaptureTimer=setTimeout(function(){if(!dead){captureAll();render();}},350);render();return e;}
      state.setEnvironment=setEnvironment;Object.defineProperty(state,'environment',{get:function(){return atmosphere?atmosphere.environment:env;}});state.atmosphere=atmosphere;
      function resize(){if(dead)return;var r=viewport.getBoundingClientRect();if(r.width<1||r.height<1)return;renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.fov=T.MathUtils.radToDeg(2*Math.atan(Math.tan(T.MathUtils.degToRad(39/2))*Math.max(1,1.36/camera.aspect)));camera.updateProjectionMatrix();render();}
      var observer=new ResizeObserver(resize);observer.observe(viewport);
      function hits(event){var r=viewport.getBoundingClientRect();pointer.set((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);return ray.intersectObjects(scene.children,true);}
      function owner(obj){var a=obj,hidden=false,id=null,propG=null;while(a){if(!a.visible)hidden=true;if(!id&&a.userData.itemId)id=a.userData.itemId;if(!propG&&a.userData.propId)propG=a;a=a.parent;}return {hidden:hidden,id:id,prop:propG};}
      function blocking(obj){return !(obj.material&&obj.material.transparent&&obj.material.opacity<.3);}
      // Returns an owned item id, 'character', or null (contract used by app.js).
      function pick(event){var list=hits(event);for(var k=0;k<list.length;k++){var obj=list[k].object;if(!obj.visible)continue;var o=owner(obj);if(o.hidden)continue;if(o.id)return o.id;if(obj.userData.character)return 'character';if(!blocking(obj))continue;return null;}return null;}
      // Reserved interface: nearest visible prop under the pointer (fixtures / decor), or null.
      function pickProp(event){var list=hits(event);for(var k=0;k<list.length;k++){var obj=list[k].object;if(!obj.visible)continue;var o=owner(obj);if(o.hidden)continue;if(o.id||obj.userData.character)return null;if(o.prop)return {id:o.prop.userData.propId,name:o.prop.userData.propName,object:o.prop};if(!blocking(obj))continue;return null;}return null;}
      function project(id){var g=itemGroups[id]||propGroups[id];if(!g)return null;scene.updateMatrixWorld(true);var center=new T.Box3().setFromObject(g).getCenter(new T.Vector3());center.project(camera);var r=viewport.getBoundingClientRect();return {x:r.left+(center.x+1)*r.width/2,y:r.top+(1-center.y)*r.height/2};}
      function propHandler(){var R=root.Room3D;return R&&typeof R.onPropClick==='function'?R.onPropClick:null;}
      // ---------- interaction ----------
      var drag=null,suppress=false,tip=host.querySelector('.bedroom-3d-tooltip'),itemDrag=null,floorPlane=new T.Plane(new T.Vector3(0,1,0),0);
      function itemDragEnabled(){var R=root.Room3D;return R&&R.dragEnabled?R:null;}
      function pointOnFloor(e){var r=viewport.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);var p=new T.Vector3();return ray.ray.intersectPlane(floorPlane,p)?p:null;}
      function surfaceAt(x,z,excludeId){
        var down=new T.Raycaster(new T.Vector3(x,1.8,z),new T.Vector3(0,-1,0)),list=down.intersectObjects(scene.children,true);
        for(var i=0;i<list.length;i++){var hit=list[i],obj=hit.object;if(!obj.visible||hit.point.y<=.04||hit.point.y>1.3)continue;var o=owner(obj);if(o.hidden||o.id===excludeId||obj.userData.character)continue;if(!o.id&&!o.prop)continue;return {y:hit.point.y,id:o.id||(o.prop&&o.prop.userData.propId)||''};}
        return {y:0,id:''};
      }
      function itemDragStart(e,id){
        if(!itemDragEnabled()||!id||id==='character'||!itemGroups[id])return false;
        var item=cfg.items.find(function(entry){return String(entry.id)===String(id);});
        if(!item)return false;
        var g=itemGroups[id],pivot=g.children[0]||g;
        itemDrag={id:id,item:item,pointer:e.pointerId,pivot:pivot,startX:e.clientX,startY:e.clientY,moved:false,surfaceId:''};
        suppress=false;e.preventDefault();e.stopPropagation();try{viewport.setPointerCapture(e.pointerId);}catch(err){}
        return true;
      }
      function itemDragMove(e){
        if(!itemDrag)return false;
        var dx=e.clientX-itemDrag.startX,dy=e.clientY-itemDrag.startY;
        if(Math.hypot(dx,dy)>4)itemDrag.moved=true;
        if(itemDrag.moved){
          var p=pointOnFloor(e);if(!p)return true;
          var x=T.MathUtils.clamp(p.x,.05*W,.95*W),z=T.MathUtils.clamp(p.z,.05*D,.95*D);
          itemDrag.pivot.position.x=x;itemDrag.pivot.position.z=z;itemDrag.pivot.position.y=0;
          itemDrag.surfaceId='';
          if(itemDrag.item.placed&&root.GoodsSize&&root.GoodsSize.smallEnoughForSurface&&root.GoodsSize.smallEnoughForSurface(itemDrag.item)){
            var s=surfaceAt(x,z,itemDrag.id);itemDrag.pivot.position.y=s.y;itemDrag.surfaceId=s.id;
          }
          tip.style.display='none';render();
        }
        e.preventDefault();e.stopPropagation();return true;
      }
      function itemDragEnd(e){
        if(!itemDrag)return false;
        var d=itemDrag;itemDrag=null;
        if(viewport.hasPointerCapture(e.pointerId))viewport.releasePointerCapture(e.pointerId);
        suppress=d.moved;
        if(d.moved){
          var info={room:room,id:d.id,item:d.item,
            x:T.MathUtils.clamp(d.pivot.position.x/W,.05,.95),
            y:T.MathUtils.clamp(d.pivot.position.z/D,.05,.95),
            z_cm:Math.max(0,d.pivot.position.y)*100,
            surface_id:d.surfaceId||''};
          var R=root.Room3D;if(R&&typeof R.onItemDrop==='function'){try{R.onItemDrop(info);}catch(err){console.warn('Room 3D item drop handler skipped',err);}}
        }
        return true;
      }
      function clampTarget(){target.x=T.MathUtils.clamp(target.x,0,W);target.z=T.MathUtils.clamp(target.z,0,D);}
      viewport.addEventListener('contextmenu',function(e){e.preventDefault();});
      viewport.addEventListener('pointerdown',function(e){
        if(e.button===0&&itemDragEnabled()){var picked=pick(e);if(picked&&picked!=='character'&&itemDragStart(e,picked))return;}
        if(e.button!==0&&e.button!==2)return;drag={id:e.pointerId,x:e.clientX,y:e.clientY,theta:orbit.theta,phi:orbit.phi,pan:e.button===2||e.shiftKey,tx:target.x,tz:target.z,moved:false};suppress=false;viewport.setPointerCapture(e.pointerId);});
      viewport.addEventListener('pointermove',function(e){
        if(itemDragMove(e))return;
        if(drag){var dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>4)drag.moved=true;if(drag.moved){
          if(drag.pan){var k=orbit.distance*.0016,s=Math.sin(orbit.theta),c=Math.cos(orbit.theta);target.x=drag.tx-c*dx*k-s*dy*k;target.z=drag.tz+s*dx*k-c*dy*k;clampTarget();}
          else{orbit.theta=drag.theta-dx*.008;orbit.phi=drag.phi-dy*.006;}
          tip.style.display='none';render();}return;}
        var id=pick(e),item=cfg.items.find(function(i){return i.id===id;}),pr=!item&&propHandler()?pickProp(e):null,propItem=pr?cfg.items.find(function(i){return String(i.id)===String(pr.id);}):null,label=item?(item.name||id):propItem?propItem.name:pr?pr.name:'';if(pr||item)label='点击互动 · '+label;
        viewport.style.cursor=label?'pointer':'grab';tip.style.display=label?'block':'none';
        if(label){tip.textContent=label;tip.style.left=Math.min(host.clientWidth-130,e.clientX-host.getBoundingClientRect().left+12)+'px';tip.style.top=Math.max(75,e.clientY-host.getBoundingClientRect().top-25)+'px';}});
      function release(e){if(itemDragEnd(e))return;if(!drag)return;suppress=drag.moved;drag=null;if(viewport.hasPointerCapture(e.pointerId))viewport.releasePointerCapture(e.pointerId);}
      viewport.addEventListener('pointerup',release);viewport.addEventListener('pointercancel',release);viewport.addEventListener('pointerleave',function(){tip.style.display='none';});
      // Capture before the application's photo handler; forward a semantic furniture click.
      host.addEventListener('click',function(e){if(!viewport.contains(e.target))return;e.preventDefault();e.stopPropagation();if(suppress){suppress=false;return;}
        var id=pick(e);if(id&&id!=='character'){var btn=Array.from(host.querySelectorAll('.bedroom-3d-items .furniture-hit')).find(function(b){return b.dataset.id===id;});if(btn)btn.click();return;}
        if(!id){var handler=propHandler();if(handler){var pr=pickProp(e);if(pr)handler({room:room,id:pr.id,name:pr.name,object:pr.object,host:host});}}},true);
      viewport.addEventListener('wheel',function(e){e.preventDefault();orbit.distance*=Math.exp(e.deltaY*.001);render();},{passive:false});
      viewport.addEventListener('keydown',function(e){var used=true;switch(e.key){case 'ArrowLeft':orbit.theta-=.12;break;case 'ArrowRight':orbit.theta+=.12;break;case 'ArrowUp':orbit.phi-=.08;break;case 'ArrowDown':orbit.phi+=.08;break;case '+':case '=':orbit.distance*=.9;break;case '-':orbit.distance*=1.1;break;case 'Home':reset();break;default:used=false;}if(used){e.preventDefault();render();}});
      function reset(){Object.assign(orbit,HOME);target.copy(homeTarget);render();}
      host.querySelector('.bedroom-3d-toolbar').addEventListener('click',function(e){var b=e.target.closest('[data-bed3d]');if(!b)return;e.stopPropagation();switch(b.dataset.bed3d){case 'reset':reset();break;case 'in':orbit.distance*=.88;render();break;case 'out':orbit.distance/= .88;render();break;case 'items':var panel=host.querySelector('.bedroom-3d-items');panel.hidden=!panel.hidden;b.setAttribute('aria-expanded',String(!panel.hidden));break;case 'expand':if(host.classList.contains('expanded')){host.classList.remove('expanded');updateExpansion();}else if(document.fullscreenElement===host){document.exitFullscreen();}else if(host.requestFullscreen){host.requestFullscreen().catch(function(){host.classList.add('expanded');updateExpansion();});}else{host.classList.add('expanded');updateExpansion();}break;case 'env':var ep=host.querySelector('.room-3d-env');ep.hidden=!ep.hidden;b.setAttribute('aria-expanded',String(!ep.hidden));syncPanel();break;case 'plan':host.classList.toggle('show-plan');b.textContent=host.classList.contains('show-plan')?'3D':'平面';render();break;}});
      // Environment preview panel (local only).
      var panel=host.querySelector('.room-3d-env'),liveEnv=Object.assign({},env);
      function fmt(h){var m=Math.round(h*60)%1440;return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');}
      function syncPanel(){if(!panel)return;var e=state.environment||env,h=e.hour!=null?e.hour:{night:22,dawn:6.8,day:12,dusk:17.8}[e.band];panel.querySelector('[data-env=hour]').value=h;panel.querySelector('output').textContent=fmt(h);panel.querySelector('[data-env=weather]').value=e.weather;}
      if(panel){['click','pointerdown','wheel','keydown'].forEach(function(t){panel.addEventListener(t,function(e){e.stopPropagation();});});
        panel.addEventListener('input',function(e){var t=e.target;if(t.dataset.env==='hour'){var h=Number(t.value);panel.querySelector('output').textContent=fmt(h);setEnvironment(ATM.makeEnvironment({hour:h,weather:state.environment.weather}));}});
        panel.addEventListener('change',function(e){var t=e.target;if(t.dataset.env==='weather')setEnvironment(ATM.makeEnvironment({hour:hourNow(),weather:t.value}));});
        panel.querySelector('[data-env=live]').addEventListener('click',function(){setEnvironment(liveEnv);});}
      function hourNow(){var e=state.environment||env;return e.hour!=null?e.hour:{night:22,dawn:6.8,day:12,dusk:17.8}[e.band];}
      function updateExpansion(){var expanded=document.fullscreenElement===host||host.classList.contains('expanded');host.querySelector('[data-bed3d=expand]').textContent=expanded?'还原':'放大';resize();}
      host.addEventListener('fullscreenchange',updateExpansion);
      host.addEventListener('keydown',function(e){if(e.key==='Escape'&&host.classList.contains('expanded')){host.classList.remove('expanded');updateExpansion();}});
      renderer.domElement.addEventListener('webglcontextlost',function(e){e.preventDefault();fallback('3D 暂不可用，已显示平面视图');});
      function dispose(){if(dead)return;dead=true;cancelAnimationFrame(frame);cancelAnimationFrame(loopFrame);clearTimeout(recaptureTimer);if(io)io.disconnect();document.removeEventListener('visibilitychange',onVis);if(atmosphere)atmosphere.dispose();if(observer)observer.disconnect();geometries.forEach(function(g){g.dispose();});materials.forEach(function(m){m.dispose();});textures.forEach(function(t){t.dispose();});cubeTargets.forEach(function(t){t.dispose();});scene.traverse(function(o){if(o.shadow)o.shadow.dispose();});renderer.dispose();renderer.forceContextLoss();active.delete(host);}
      state.reset=reset;state.resize=resize;host.dataset.ready='true';host.dataset.environment=env.signature;host.dataset.renderer='webgl';resize();
    }catch(error){var running=active.get(host);if(running)running.dispose();fallback('3D 暂不可用，已显示平面视图');console.warn('Room 3D unavailable:',error);}
  }
  function scan(){pending=false;active.forEach(function(state,el){if(!el.isConnected)state.dispose();});document.querySelectorAll('.bedroom-3d:not([data-wired])').forEach(mount);}
  new MutationObserver(function(){if(!pending){pending=true;queueMicrotask(scan);}}).observe(document.documentElement,{childList:true,subtree:true});
  var api={markup:markup,destinationMarkup:markupDestination,supportsDestination:supportsDestination,instances:active,supports:supports,rooms:Object.keys(ROOMS),onPropClick:null,dragEnabled:false,onItemDrop:null,
    setEnvironment:function(next){var out=[];active.forEach(function(s){if(s.setEnvironment)out.push(s.setEnvironment(next));});return out;},
    makeEnvironment:function(o){return root.Room3DAtmosphere?root.Room3DAtmosphere.makeEnvironment(o):null;},
    registerEffect:function(name,factory){if(root.Room3DAtmosphere)root.Room3DAtmosphere.registerEffect(name,factory);},
    weathers:['clear','cloudy','rain','storm','snow','fog','wind']};
  root.Room3D=api;root.Bedroom3D=api;
})(window);
