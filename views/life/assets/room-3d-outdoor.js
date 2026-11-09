/* Outdoor world for Room3D open-air rooms (阳台 / 露台).
   build(kit, ctx) is called by the engine while the scene is assembled; it adds
     - the house the room belongs to (L-shaped massing, plinth, storey bands, roofs, lit windows),
     - the garden around it (lawn, patio, path, trees, hedges, pond, lamps, flowers, bench),
     - the distance (neighbour houses, hill ring) and a sky dome (gradient, sun, moon, stars, clouds).
   A Room3D effect ('outdoor-world') then drives everything that depends on time and weather:
     sky colours, sun/moon, stars, cloud drift, base haze, wet / snowy ground and trees,
     birds, butterflies, fireflies, wind-blown leaves, rain ripples and puddles.
   Everything that could become clickable later is tagged with kit.prop(...). */
(function(root){
  'use strict';
  var PI=Math.PI;
  function rng(seed){var s=seed|0||1;return function(){s=(s*16807)%2147483647;return (s-1)/2147483646;};}
  function noop(){}
  // Child group whose children are expressed in world coordinates, but hide/show with `parent`.
  function worldAnchor(T,parent){var a=new T.Group();a.quaternion.copy(parent.quaternion).invert();a.position.copy(parent.position).negate().applyQuaternion(a.quaternion);parent.add(a);return a;}
  function wbox(k,p,x0,x1,y0,y1,z0,z1,m,r,shadow){var b=k.box(p,(x0+x1)/2,(y0+y1)/2,(z0+z1)/2,Math.abs(x1-x0),Math.abs(y1-y0),Math.abs(z1-z0),m,r);if(shadow===false)b.castShadow=false;return b;}
  // ---------------------------------------------------------------- house massing
  function interiorMaterial(k){if(root.Room3DModels&&root.Room3DModels.interiorMaterial)return root.Room3DModels.interiorMaterial(k);if(k._interiorMat)return k._interiorMat;var T=k.T,t=k.canvasTexture(function(c,w,h){c.fillStyle='#d9c7ae';c.fillRect(0,0,w,h);c.fillStyle='#c4ad90';c.fillRect(0,h*.68,w,h*.32);c.fillStyle='#e9dcc8';c.fillRect(w*.08,h*.18,w*.22,h*.3);c.fillStyle='#b9a7b9';c.fillRect(0,0,w*.16,h);c.fillRect(w*.84,0,w*.16,h);var g=c.createRadialGradient(w*.6,h*.35,0,w*.6,h*.35,w*.5);g.addColorStop(0,'rgba(255,236,190,.9)');g.addColorStop(1,'rgba(255,236,190,0)');c.fillStyle=g;c.fillRect(0,0,w,h);c.fillStyle='#8d7a66';c.fillRect(w*.45,h*.55,w*.3,h*.16);},128,128);
    k._interiorMat=k.material('#8f8478',.6,{map:t,emissive:'#ffffff',emissiveMap:t,emissiveIntensity:.05,lit:[.05,.85]});return k._interiorMat;}
  function massWindow(k,p,x,y,z,w,h,normal,frameMat){
    var g=k.group(p,x,y,z);g.rotation.y={'+z':0,'+x':PI/2,'-x':-PI/2,'-z':PI}[normal]||0;
    k.box(g,0,0,.004,w,h,.01,interiorMaterial(k),0).castShadow=false;var gl=k.box(g,0,0,.03,w,h,.006,k.glass);gl.castShadow=false;
    var f=k.batch(g,frameMat);f.box(-w/2-.04,0,.05,.08,h+.08,.08).box(w/2+.04,0,.05,.08,h+.08,.08).box(0,h/2+.04,.05,w+.16,.08,.08).box(0,0,.05,.04,h,.04).box(0,-h/2-.05,.08,w+.2,.06,.16);f.done();
    if(!arguments[9]){var sh=k.material('#8aa092',.8);[-1,1].forEach(function(sd){k.box(g,sd*(w/2+.2),0,.06,.22,h+.06,.03,sh,.01).castShadow=false;});}return g;}
  function gableRoof(k,p,x0,x1,z0,z1,top,rise,alongX,mat,trim){
    var T=k.T,ov=.45,span=alongX?(z1-z0):(x1-x0),half=span/2+ov,len=(alongX?(x1-x0):(z1-z0))+ov*2,slope=Math.atan2(rise,span/2),sl=Math.hypot(half,rise*half/(span/2));
    var cx=(x0+x1)/2,cz=(z0+z1)/2;
    [-1,1].forEach(function(sd){var m=alongX?k.box(p,cx,top+rise/2,cz+sd*half/2,len,.14,sl,mat,.02):k.box(p,cx+sd*half/2,top+rise/2,cz,sl,.14,len,mat,.02);if(alongX)m.rotation.x=sd*slope;else m.rotation.z=-sd*slope;m.castShadow=false;});
    var shape=new T.Shape();shape.moveTo(-span/2,0);shape.lineTo(span/2,0);shape.lineTo(0,rise);shape.lineTo(-span/2,0);
    var geo=k.keep(new T.ExtrudeGeometry(shape,{depth:.1,bevelEnabled:false}));
    [0,1].forEach(function(e){var tri=k.mesh(geo,k._houseWall,p,0,top,0);tri.castShadow=false;if(alongX){tri.rotation.y=PI/2;tri.position.set(e?x1-.1:x0,top,cz);}else{tri.position.set(cx,top,e?z1-.1:z0);}});
    var ridge=alongX?k.box(p,cx,top+rise+.04,cz,len,.1,.16,trim,.02):k.box(p,cx,top+rise+.04,cz,.16,.1,len,trim,.02);ridge.castShadow=false;
  }
  // The balcony (1F) and the terrace (2F) share one footprint: each view draws the other level's
  // doors and windows (from RoomModel.openings) on the house faces, plus that level's deck and railing.
  function otherLevel(k,back,left,W,D,H,g,terrace,frame,trim,stone){
    var other=terrace?'阳台':'露台',O=((root.RoomModel||{}).openings||{})[other]||{},yF=terrace?-3.2:3.2,glassDoor=function(p,c,wd,normal,face){var gd=massWindow(k,p,normal==='+z'?c:face,yF+1.07,normal==='+z'?face:c,wd-.08,2.06,normal,frame,true);var kick=k.box(gd,0,-.8,.04,wd-.1,.36,.02,frame);kick.castShadow=false;return gd;};
    (O.N||[]).forEach(function(o){var a=k.X(o[0]),b=k.X(o[1]),c=(a+b)/2;if(o[2]==='win')massWindow(k,back,c,yF+((o[3]||1)+(o[4]||2.25))/2,-.09,b-a-.1,(o[4]||2.25)-(o[3]||1)-.1,'+z',frame);else glassDoor(back,c,b-a,'+z',-.09);});
    (O.W||[]).forEach(function(o){var a=k.Z(o[0]),b=k.Z(o[1]),c=(a+b)/2;if(o[2]==='win')massWindow(k,left,-.09,yF+((o[3]||1)+(o[4]||2.25))/2,c,b-a-.1,(o[4]||2.25)-(o[3]||1)-.1,'+x',frame);else glassDoor(left,c,b-a,'+x',-.09);});
    var lv=k.group(null,0,0,0),deck=k.material(terrace?'#b89c7a':'#cbb48f',.85),rail=k.material('#f6f1e6',.6);
    // floor slab of that level with its edge fascia, glass railing on the open sides and a planter strip
    k.bx(lv,W/2,yF-.22,D/2,W+.1,.22,D+.1,stone,.02);k.bx(lv,W/2,yF,D/2,W,.02,D,deck,.005);
    var pb=k.batch(lv,rail),runs=[[0,D,W,D,'x'],[W,0,W,D,'z']];runs.forEach(function(r){var len=r[4]==='x'?r[2]-r[0]:r[3]-r[1],n=Math.max(2,Math.ceil(len/1.1));for(var i=0;i<=n;i++){var u=i*len/n;pb.box(r[4]==='x'?r[0]+u:r[0]-.04,yF+.52,r[4]==='x'?r[1]-.04:r[1]+u,.06,1.0,.06);}
      if(r[4]==='x')pb.box(W/2,yF+1.05,D-.04,W+.06,.05,.09);else pb.box(W-.04,yF+1.05,D/2,.09,.05,D+.06);
      var gp=k.box(lv,r[4]==='x'?W/2:W-.04,yF+.52,r[4]==='x'?D-.04:D/2,r[4]==='x'?W:.012,.86,r[4]==='x'?.012:D,k.glass);gp.castShadow=false;});pb.done();
    var pl=k.material('#9c8a73',.9),leaf=k.material('#8fa982',.85);k.bx(lv,W/2,yF,D-.2,W-.3,.22,.24,pl,.01);for(var j=0;j<6;j++)k.sph(lv,.5+j*(W-1)/5,yF+.3,D-.2,.16,.13,.14,leaf);
    if(terrace){k.bx(lv,W/2,-.215,D/2,W+.1,.2,D+.1,stone,.02);var post=k.cylB(lv,W-.06,yF,D-.06,.07,.07,3.0,rail);}
    else{k.cylB(lv,W-.06,0,D-.06,.07,.07,yF-.22,rail);k._upperLevel=lv;
      // like the cut-away ceilings indoors, the terrace above is only drawn for eye-level views so it never hides the balcony
      var sc=k.scene,prev=sc.onBeforeRender;sc.onBeforeRender=function(r,s2,cam){if(prev)prev.apply(this,arguments);lv.visible=cam.position.y<yF-.1;};}
    lv.traverse(function(o){o.raycast=noop;});return lv;
  }
  // The 1F garage wing from the home plan (车库 west of the 餐厅, its doors on the 餐厅's south line; balcony-local y -160..240).
  // The stylised house block reaches x=-14 here, so the wing is placed flush against it rather than at its plan x.
  function garageWing(k,g,terrace,wall,trim,stone,frame){
    var T=k.T,x1=-14.05,x0=x1-8.8,z0=k.Z(-160),z1=k.Z(240),y0=terrace?-3.2:0,h=3.0,cx=(x0+x1)/2,cz=(z0+z1)/2,w=x1-x0,d=z1-z0,gw=k.prop(null,'garage_wing','车库');
    var siding=k.material('#e6e0d2',.9),door=k.material('#ecebe6',.5,{metalness:.15}),dark=k.material('#3a3d42',.6),glassM=k.material('#5d7280',.1,{metalness:.4}),base=gw;
    k.bx(base,cx,(g+y0)/2,cz,w+.1,y0-g,d+.1,stone,.02);[[cx,z0+.06,w,.12],[cx,z1-.06,w,.12]].forEach(function(q){k.bx(base,q[0],y0+.18,q[1],q[2],.36,q[3],siding,.01);});[[x0+.06,cz],[x1-.06,cz]].forEach(function(q){k.bx(base,q[0],y0+.18,q[1],.12,.36,d,siding,.01);});
    // like the cut-away room walls: the wing's walls and roof hide while it stands between the camera and the balcony
    gw=k.group(base,0,0,0);var box=new T.Box3(new T.Vector3(x0-.2,g,z0-.2),new T.Vector3(x1+.2,y0+h+.6,z1+.2)),ray=new T.Ray(),tgt=new T.Vector3(k.W/2,1.0,k.D/2),hit=new T.Vector3(),sc=k.scene,prev=sc.onBeforeRender;
    sc.onBeforeRender=function(r,s2,cam){if(prev)prev.apply(this,arguments);ray.origin.copy(cam.position);ray.direction.copy(tgt).sub(cam.position);var len=ray.direction.length();ray.direction.normalize();var p=ray.intersectBox(box,hit);gw.visible=!(p&&p.distanceTo(cam.position)<len);};
    k.bx(gw,cx,y0+h/2,cz,w,h,d,siding,.02);
    k.bx(gw,cx,y0+h+.06,cz,w+.12,.12,d+.12,trim,.01);k.bx(gw,cx,y0+h+.1,cz,w-.3,.04,d-.3,k.material('#9da09a',.95),.0);
    [[cx,z0+.06,w+.12,.12],[cx,z1-.06,w+.12,.12]].forEach(function(q){k.bx(gw,q[0],y0+h+.25,q[1],q[2],.3,q[3],trim,.01);});[[x0+.06,cz],[x1-.06,cz]].forEach(function(q){k.bx(gw,q[0],y0+h+.25,q[1],.12,.3,d,trim,.01);});
    k.box(gw,x0+w*.41,y0+h+.2,z0+d*.44,2.2,.14,1.5,glassM,.02);k.bx(gw,x0+1.2,y0+h+.12,z0+1.0,1.1,.6,.75,k.material('#d9dbd6',.5),.03);
    // three sectional roll-up doors facing the street, each with a lamp, plus a side door and windows
    [90,220,350].forEach(function(bx){var x=x0+bx*.02,dg=k.group(gw,x,y0,z1+.01);
      for(var p=0;p<5;p++){k.bx(dg,0,.05+p*.46,.02,2.3,.44,.04,door,.01);k.box(dg,0,.27+p*.46,.045,2.24,.012,.004,k.material('#d1d0ca',.5));if(p===3)for(var wn=0;wn<4;wn++)k.box(dg,-.8+wn*.53,1.65,.048,.38,.16,.01,glassM);}
      var fr=k.batch(dg,trim);fr.box(-1.22,1.2,.04,.12,2.4,.08).box(1.22,1.2,.04,.12,2.4,.08).box(0,2.44,.04,2.56,.12,.08);fr.done();
      k.bx(dg,0,2.62,.08,.16,.22,.1,k.emissive('#ffd9a0',.25,1.6),.03);k.pointLight(dg,0,2.5,.5,'#ffd29a',0,1.0,4);});
    var sd=k.group(gw,x0-.01,y0,z0+1.4);sd.rotation.y=-PI/2;k.bx(sd,0,0,.02,.9,2.1,.05,k.material('#7d8f78',.55),.01);k.sph(sd,.3,1.0,.06,.03,.03,.03,k.brass);
    [z0+3.4,z0+5.2].forEach(function(z){var wg=k.group(gw,x0-.01,y0+1.5,z);wg.rotation.y=-PI/2;k.bx(wg,0,0,.02,1.1,.7,.05,trim,.01);k.box(wg,0,0,.05,.96,.56,.01,glassM);});
    k.cylB(gw,x0-.08,g,z1-.2,.045,.045,y0+h-g,k.material('#c9c2b6',.5)).castShadow=false;
    // concrete driveway from the doors down to the street, with expansion joints and a curb cut
    var RZ=z1+11,dl=RZ-1-z1,cm=k.material('#b9b8b2',.85),jm=k.material('#8f8e88',.9),dw=k.bx(base,cx,g+.012,z1+dl/2,w-.4,.02,dl,cm,0);dw.castShadow=false;
    for(var j=1.6;j<dl;j+=1.6)k.box(base,cx,g+.024,z1+j,w-.4,.004,.03,jm).castShadow=false;k.box(base,cx,g+.024,z1+dl/2,.03,.004,dl,jm).castShadow=false;
    street(k,g,RZ,cx,w);return base;}
  // The street in front of the house: sidewalk, curb, asphalt with a dashed centre line, and the front walk from the entry door.
  function street(k,g,RZ,dcx,dw){
    var st=k.prop(null,'street','马路'),side=k.material('#d4ccbb',.9),curb=k.material('#bdb6a8',.85),asph=k.material('#6d7275',.95),paint=k.material('#efe2b4',.7),x0=-60,x1=k.W+60,cx=(x0+x1)/2,L=x1-x0;
    function flat(m,x,z,w,d,y){var b=k.box(st,x,g+(y||.01),z,w,.02,d,m,0);b.castShadow=false;b.receiveShadow=true;return b;}
    flat(side,cx,RZ-.5,L,1.0,.02);flat(curb,cx,RZ+.03,L,.14,.05);flat(asph,cx,RZ+3.1,L,6.0,.008);
    for(var x=x0+1;x<x1-2;x+=4)flat(paint,x+1,RZ+3.1,2.0,.14,.02);
    flat(paint,cx,RZ+.35,L,.08,.02);flat(paint,cx,RZ+5.85,L,.08,.02);
    flat(curb,dcx,RZ-.5,dw,1.0,.026);
    flat(k.material('#d8cdb4',.85),-5.9,(k.D+4.8+RZ-1)/2,1.2,RZ-1-(k.D+4.8),.012);
    st.traverse(function(o){o.raycast=noop;});return st;}
  function buildHouse(k,ctx,W,D,H,g,top,terrace){
    var T=k.T,back=worldAnchor(T,k.walls.back),left=worldAnchor(T,k.walls.left);
    var wall=k._houseWall=k.material('#ede4d2',.92),stone=k.material('#b9ad9a',.95),trim=k.material('#f6efe2',.8),roof=k._roofMat=k.material('#7f8a8f',.7),frame=k.material('#f6f1e6',.6);
    // north block (behind the back wall) and west block (behind the left wall)
    wbox(k,back,-14,W,g,top,-11,-.1,wall,0,false);wbox(k,left,-14,-.1,g,top,-.1,D+3,wall,0,false);
    wbox(k,back,-14.05,W+.05,g,g+.55,-11.05,-.1,stone,0,false);wbox(k,left,-14.05,-.1,g,g+.55,-.1,D+3.05,stone,0,false);
    var bandY=terrace?-.2:3.05;wbox(k,back,-14.06,W+.06,bandY,bandY+.16,-11.06,-.1,trim,0,false);wbox(k,left,-14.06,-.1,bandY,bandY+.16,-.1,D+3.06,trim,0,false);
    wbox(k,back,W-.02,W+.08,g,top,-.2,-.05,trim,0,false);wbox(k,back,W-.02,W+.08,g,top,-11.1,-10.95,trim,0,false);wbox(k,left,-.24,-.04,g,top,D+2.92,D+3.08,trim,0,false);
    wbox(k,back,-14.2,W+.2,top,top+.12,-11.2,-.1,trim,0,false);wbox(k,left,-14.2,-.1,top,top+.12,-.1,D+3.2,trim,0,false);
    gableRoof(k,back,-14,W,-11,-.1,top+.12,2.1,true,roof,trim);gableRoof(k,left,-14,-.1,-.1,D+3,top+.12,2.1,false,roof,trim);
    // horizontal siding on the big visible faces
    var sid=k.canvasTexture(function(c,w,h){c.fillStyle='#ede4d2';c.fillRect(0,0,w,h);var gr=c.createLinearGradient(0,0,0,h);gr.addColorStop(0,'rgba(255,255,255,.35)');gr.addColorStop(.85,'rgba(0,0,0,0)');gr.addColorStop(1,'rgba(120,100,80,.35)');c.fillStyle=gr;c.fillRect(0,0,w,h);},16,32);
    function siding(p,x,y,z,w,h,ry){var m=k.material('#ffffff',.92,{map:k.trackTexture(sid.clone())});m.map.wrapS=m.map.wrapT=T.RepeatWrapping;m.map.repeat.set(1,h/.2);m.map.needsUpdate=true;var pl=k.mesh(k.keep(new T.PlaneGeometry(w,h)),m,p,x,y,z,false);pl.rotation.y=ry;pl.raycast=noop;return pl;}
    var sb=g+.56;siding(back,W+.012,(sb+top)/2,-5.55,10.9,top-sb,PI/2);siding(back,W/2,(H+top)/2+.06,-.095,W,top-H-.12,0);if(sb<-.25)siding(back,W/2,(sb-.2)/2,-.095,W,-.2-sb,0);
    siding(left,-.095,(H+top)/2+.06,D/2,D,top-H-.12,PI/2);siding(left,-.095,(sb+top)/2,D+1.5,3,top-sb,PI/2);if(sb<-.02)siding(left,-.095,sb/2,D/2,D,-sb,PI/2);siding(left,-7,(sb+top)/2,D+3.006,13.8,top-sb,0);
    // downpipe at the east corner
    k.cylB(back,W+.12,g,-.35,.045,.045,top-g,k.material('#c9c2b6',.5)).castShadow=false;
    // lit windows on the visible faces
    var lv=terrace?[1.55,-1.65]:[1.6,4.7];
    lv.forEach(function(y){[-2.6,-7.2].forEach(function(z){massWindow(k,back,W+.01,y,z,1.0,1.25,'+x',frame);});[D+1.6].forEach(function(z){if(y>H+.3||y<0||terrace)massWindow(k,left,-.09,y,z,.9,1.2,'+x',frame);});[-3.4,-8.6].forEach(function(x){massWindow(k,left,x,y,D+3.01,1.0,1.25,'+z',frame);});});
    otherLevel(k,back,left,W,D,H,g,terrace,frame,trim,stone);
    garageWing(k,g,terrace,wall,trim,stone,frame);
    // front door on the west block's south face
    var dg=k.group(left,-5.9,g+.55,D+3.01);k.bx(dg,0,0,.03,1.0,2.15,.06,k.material('#7d8f78',.55),.01);var df=k.batch(dg,frame);df.box(-.54,1.08,.05,.08,2.2,.08).box(.54,1.08,.05,.08,2.2,.08).box(0,2.2,.05,1.16,.08,.08);df.done();k.sph(dg,.36,1.05,.08,.03,.03,.03,k.brass);
    var awn=k.box(dg,0,2.42,.45,1.6,.06,.9,trim,.01);awn.rotation.x=.12;var lamp=k.box(dg,.75,1.85,.08,.12,.2,.1,k.emissive('#ffd9a0',.25,1.8),.02);k.pointLight(dg,.75,1.7,.4,'#ffd29a',0,1.4,4);
    k.bx(dg,0,-.55,.4,1.5,.18,.7,stone,.01);k.bx(dg,0,-.37,.25,1.3,.18,.4,stone,.01);
    return {back:back,left:left,wall:wall,trim:trim,stone:stone};
  }
  // ---------------------------------------------------------------- room shell additions
  function buildRoomEdges(k,ctx,house,W,D,H,g,terrace){
    var T=k.T,stone=house.stone,trim=house.trim;
    if(terrace){
      // slab fascia, supporting columns and the covered 1F balcony underneath
      wbox(k,null,-.02,W+.08,-.42,-.02,D-.02,D+.08,trim,.01);wbox(k,null,W-.02,W+.08,-.42,-.02,-.05,D+.08,trim,.01);
      wbox(k,null,0,W,-.44,-.2,0,D,k.material('#e8e0d0',.9),0,false);
      [[W-.15,D-.15],[W-.15,.15]].forEach(function(q){wbox(k,null,q[0]-.13,q[0]+.13,g,-.42,q[1]-.13,q[1]+.13,house.wall,.02);wbox(k,null,q[0]-.16,q[0]+.16,g,g+.25,q[1]-.16,q[1]+.16,stone,.02);});
      wbox(k,null,0,W,g,g+.45,0,D,stone,0,false);var f1=k.material('#b39d83',.8);wbox(k,null,0,W-.05,g+.45,g+.47,0,D-.05,f1,0,false);
      var rail=k.batch(null,k.paint),ry=g+.47;for(var x=.1;x<W;x+=.55)rail.box(x,ry+.5,D-.12,.05,1.0,.05);for(var z=.1;z<D;z+=.55)rail.box(W-.12,ry+.5,z,.05,1.0,.05);rail.box(W/2,ry+1.02,D-.12,W,.05,.08).box(W-.12,ry+1.02,D/2,.08,.05,D);rail.done();
    }else{
      wbox(k,null,-.02,W+.06,g,-.2,-.02,D+.06,stone,.02);wbox(k,null,-.04,W+.08,-.24,-.18,-.04,D+.08,trim,.01);
      // eave over the back of the balcony with recessed lights
      var ev=house.back;wbox(k,ev,-.1,W+.2,H+.1,H+.24,-.1,1.15,k.material('#f3ece0',.8),.01);wbox(k,ev,-.1,W+.2,H+.1,H+.3,1.1,1.18,trim,.01);
      for(var i=0;i<3;i++){var sp=k.cyl(ev,W*(i+.5)/3,H+.095,.6,.06,.06,.01,k.emissive('#fff0cf',.2,1.6));sp.castShadow=false;}
      k.pointLight(ev,W/2,H-.05,.6,'#ffe0b0',0,1.6,4);
    }
  }
  // ---------------------------------------------------------------- garden
  function tree(k,x,y,z,h,rnd,mats,world){var t=k.prop(null,'tree_'+world.trees.length,'树');t.position.set(x,y,z);k.cylB(t,0,0,0,.13*h/4,.09*h/4,h*.55,mats.bark);
    var c=k.group(t,0,h*.5,0);k.swayers.push({obj:c,kind:'tree'});for(var i=0;i<4;i++){var a=i*1.9+rnd()*1.2,r=(.7+rnd()*.5)*h/4;k.sph(c,Math.cos(a)*r*.6,h*.18+i*.18*h/4+rnd()*.3,Math.sin(a)*r*.6,r,r*.85,r,i%2?mats.leaf:mats.leaf2);}
    k.sph(c,0,h*.38,0,.9*h/4,.8*h/4,.9*h/4,mats.leaf);world.trees.push(t);return t;}
  function buildGarden(k,ctx,house,W,D,g,terrace){
    var T=k.T,rnd=rng(terrace?11:5),world={trees:[],flowers:null,lamps:[]};
    var grassTex=k.canvasTexture(function(c,w,h){c.fillStyle='#93a87c';c.fillRect(0,0,w,h);for(var i=0;i<5000;i++){c.fillStyle=['#86a070','#9fb486','#7c9668','#a7b98d'][i%4];c.fillRect((i*73.1)%w,(i*151.7)%h,2,3+(i%3));}},256,256,[40,40]);
    var grass=world.grassMat=k.material('#ffffff',.95,{map:grassTex});var ground=k.mesh(k.keep(new T.CircleGeometry(70,48)),grass,null,W/2,g-.005,D/2,false);ground.rotation.x=-PI/2;ground.raycast=noop;world.ground=ground;
    var paveTex=k.canvasTexture(function(c,w,h){c.fillStyle='#bfb6a6';c.fillRect(0,0,w,h);for(var i=0;i<4;i++)for(var j=0;j<4;j++){c.fillStyle=['#d6cdbd','#cfc5b3','#dcd4c6'][(i+j*2)%3];c.fillRect(i*w/4+2,j*h/4+2,w/4-4,h/4-4);}},256,256,[1,1]);
    var pave=world.paveMat=k.material('#ffffff',.85,{map:paveTex});
    [[W,W+1.6,-11,D+3],[-14,W+1.6,D+3,D+4.8],[-14,W,D,D+3]].forEach(function(r,i){if(i===2&&!terrace)return;var m=k.material('#ffffff',.85,{map:k.trackTexture(paveTex.clone())});m.map.wrapS=m.map.wrapT=T.RepeatWrapping;m.map.repeat.set((r[1]-r[0])/1.2,(r[3]-r[2])/1.2);m.map.needsUpdate=true;var p=k.mesh(k.keep(new T.PlaneGeometry(r[1]-r[0],r[3]-r[2])),m,null,(r[0]+r[1])/2,g+.006,(r[2]+r[3])/2,false);p.rotation.x=-PI/2;p.raycast=noop;});
    // stepping-stone path
    var stoneM=k.material('#cfc6b6',.85),path=k.prop(null,'garden_path','小径');for(var i=0;i<9;i++){var t=i/8,px=W+2.6+t*6.5+Math.sin(t*3)*.8,pz=D+4.8+t*3.5,s=k.cylB(path,px,g,pz,.32,.34,.05,stoneM);s.scale.set(1,1,.75);s.rotation.y=t*2;}
    var mats={bark:k.material('#7a6352',.9),leaf:k.material('#7f9f74',.85),leaf2:k.material('#6b8f6a',.85)};world.foliage=[mats.leaf,mats.leaf2];
    var th=terrace?6.2:4.6;[[W+4.2,-6.5,1.1],[W+7,-2.6,.9],[W+11.5,D+2.5,1],[W+9.5,-9.5,.85],[W+13,D+10,.95],[-3.5,D+7.8,1.05],[W+13,-6,1.2],[-8,D+9.5,1]].forEach(function(q){tree(k,q[0],g,q[1],th*q[2],rnd,mats,world);});
    // hedges
    var hedgeM=k.material('#728f6c',.9);world.foliage.push(hedgeM);var hedges=k.prop(null,'hedges','树篱');
    function shrub(p,x,z,s,m){for(var i=0;i<5;i++){var a=i*1.3+rnd(),rr=s*(.45+rnd()*.25);k.sph(p,x+Math.cos(a)*s*.35,g+rr*.8+(i===4?s*.25:0),z+Math.sin(a)*s*.35,rr,rr*.85,rr,m);}}
    [[W+3.1,-10.5,-1.4],[W+3.1,1.4,D+2.6]].forEach(function(r){for(var zz=r[1];zz<=r[2];zz+=.75)shrub(hedges,r[0]+Math.sin(zz*3)*.06,zz,.75,hedgeM);});for(var xx=-12;xx<=-1;xx+=.75)if(Math.abs(xx+5.9)>.9)shrub(hedges,xx,D+6,.75,hedgeM);
    // flower beds along the house (instanced blossoms)
    var beds=[[W+1.7,W+2.65,-10.2,-.9],[W+1.7,W+2.65,-.7,D+2.7],[W+5.1,W+7.1,D+1.5,D+4.3]],fb=k.prop(null,'flower_beds','花圃'),soil=k.material('#6b5443',.95),edge=k.material('#c9bfae',.85);
    beds.forEach(function(b){var cx=(b[0]+b[1])/2,cz=(b[2]+b[3])/2,w=b[1]-b[0],d=b[3]-b[2];k.box(fb,cx,g+.05,cz,w,.1,d,soil,.02).receiveShadow=true;[[cx,b[2],w+.12,.08],[cx,b[3],w+.12,.08]].forEach(function(q){k.box(fb,q[0],g+.07,q[1],q[2],.14,q[3],edge,.02);});[[b[0],cz],[b[1],cz]].forEach(function(q){k.box(fb,q[0],g+.07,q[1],.08,.14,d,edge,.02);});});
    var N=260,bloomGeo=k.keep(new T.SphereGeometry(1,8,6)),inst=new T.InstancedMesh(bloomGeo,k.material('#ffffff',.7),N),stems=new T.InstancedMesh(k.keep(new T.CylinderGeometry(.006,.008,1,4)),k.material('#6f9465',.8),N),leaves=new T.InstancedMesh(k.keep(new T.SphereGeometry(1,7,5)),k.material('#7f9f74',.85),N),m4=new T.Matrix4(),q=new T.Quaternion(),col=new T.Color(),cols=['#f2c9d2','#f7e2a4','#ffffff','#c8abc2','#e8857a','#b7c9e8'];
    for(var b=0;b<N;b++){var bd=beds[b%3],x=bd[0]+.12+rnd()*(bd[1]-bd[0]-.24),z=bd[2]+.12+rnd()*(bd[3]-bd[2]-.24),hgt=.16+rnd()*.2,base=g+.1,sc=.035+rnd()*.03;
      m4.compose(new T.Vector3(x,base+hgt,z),q,new T.Vector3(sc,sc*.7,sc));inst.setMatrixAt(b,m4);inst.setColorAt(b,col.set(cols[b%cols.length]));
      m4.compose(new T.Vector3(x,base+hgt/2,z),q,new T.Vector3(1,hgt,1));stems.setMatrixAt(b,m4);
      var ls=.06+rnd()*.05;m4.compose(new T.Vector3(x+(rnd()-.5)*.08,base+.03,z+(rnd()-.5)*.08),q,new T.Vector3(ls,ls*.55,ls));leaves.setMatrixAt(b,m4);}
    [inst,stems,leaves].forEach(function(m){m.instanceMatrix.needsUpdate=true;m.castShadow=false;m.receiveShadow=true;m.raycast=noop;fb.add(m);});world.flowers=inst;
    var bushM=k.material('#86a37c',.9);world.foliage.push(bushM);[[W+2.2,-7.5],[W+2.2,-3.6],[W+5.6,D+1.4],[W+7.6,D+3.6]].forEach(function(q){shrub(fb,q[0],q[1],.65,bushM);});
    // pond with stone rim and lily pads
    var pond=k.prop(null,'pond','池塘'),px=W+6.6,pz=D+5.6;var water=world.water=k.material('#5f8a8f',.06,{metalness:.25});k.metals.push(water);var wp=k.cylB(pond,px,g+.01,pz,1.4,1.4,.02,water);wp.scale.set(1,1,.7);wp.castShadow=false;
    var rim=k.tor(pond,px,g+.04,pz,1.42,.12,stoneM);rim.rotation.x=PI/2;rim.scale.set(1,.7,1);for(var l=0;l<5;l++){var lp=k.cylB(pond,px+Math.cos(l*1.4)*.7,g+.035,pz+Math.sin(l*1.4)*.4,.14,.14,.005,k.material('#6f9a64',.7));lp.castShadow=false;}world.pond=wp;
    // bench and lamp posts
    var bench=k.prop(null,'garden_bench','长椅');bench.position.set(W+5.2,g,D+3.2);bench.rotation.y=-.9;k.legs(bench,1.3,.45,.42,.08,k.material('#4c4f52',.4,.6),.02);var bw=k.batch(bench,k.walnut);for(var i2=0;i2<4;i2++)bw.box(0,.44,-.18+i2*.12,1.36,.035,.09,.006);for(var j=0;j<3;j++)bw.box(0,.62+j*.11,-.24,1.36,.08,.03,.006);bw.done();
    [[W+2.5,D+4.4],[W+7.8,D+8.4],[W+2.4,-3.9]].forEach(function(q,i){var lp=k.prop(null,'garden_lamp_'+i,'庭院灯');lp.position.set(q[0],g,q[1]);k.cylB(lp,0,0,0,.08,.1,.12,k.black);k.cylB(lp,0,.12,0,.035,.035,1.1,k.black);k.bx(lp,0,1.2,0,.18,.24,.18,k.emissive('#ffe2b0',.2,2.2),.03);k.cylB(lp,0,1.44,0,.14,.04,.08,k.black);if(i===0)k.pointLight(lp,0,1.3,0,'#ffd8a0',0,2.2,6);world.lamps.push(lp);});
    // distance: neighbour houses + hill ring
    var nb=[[W+24,-16,'#e4d6c4','#8a7a72'],[W+30,D+26,'#dfe3d6','#7d8a8c'],[W+16,-30,'#eadfd0','#93827a'],[-8,D+30,'#e0dccd','#7f8a8f']];world.far=[];
    nb.forEach(function(n,i){var hg=k.prop(null,'neighbour_'+i,'邻居家');hg.position.set(n[0],g,n[1]);hg.rotation.y=i*.7;var wm=k.material(n[2],.9),rm=k.material(n[3],.8);world.far.push(wm,rm);k.bx(hg,0,0,0,7,5,6,wm).castShadow=false;var r1=k.box(hg,0,5.9,-1.6,7.6,.2,3.8,rm);r1.rotation.x=.48;var r2=k.box(hg,0,5.9,1.6,7.6,.2,3.8,rm);r2.rotation.x=-.48;r1.castShadow=r2.castShadow=false;
      for(var w=0;w<3;w++)for(var f=0;f<2;f++){var win=k.box(hg,-2.4+w*2.4,1.4+f*2.2,3.01,.9,1.0,.02,interiorMaterial(k));win.castShadow=false;}});
    var hillTex=k.canvasTexture(function(c,w,h){c.clearRect(0,0,w,h);[['#8fae9c',.45],['#6f9384',.62],['#557a6e',.78]].forEach(function(l,i){c.fillStyle=l[0];c.beginPath();c.moveTo(0,h);for(var x=0;x<=w;x+=8)c.lineTo(x,h*l[1]-Math.sin(x/w*PI*(6+i*3)+i)*h*.12-Math.sin(x/w*PI*17+i*2)*h*.04);c.lineTo(w,h);c.fill();if(i===2){for(var t=0;t<w;t+=9){var hh=h*(.05+((t*13)%7)/100);c.beginPath();c.moveTo(t,h*l[1]+4);c.lineTo(t+4.5,h*l[1]-hh);c.lineTo(t+9,h*l[1]+4);c.fill();}}});},2048,256);
    hillTex.wrapS=T.RepeatWrapping;hillTex.repeat.set(2,1);var hillMat=world.hillMat=new T.MeshBasicMaterial({map:hillTex,transparent:true,side:T.BackSide,depthWrite:false,fog:true});k.trackMaterial(hillMat);
    var hills=k.mesh(k.keep(new T.CylinderGeometry(58,58,16,64,1,true)),hillMat,null,W/2,g+6.5,D/2,false);hills.raycast=noop;hills.receiveShadow=false;hills.renderOrder=-1;
    return world;
  }
  // ---------------------------------------------------------------- sky dome
  function buildSky(k,W,D,g){
    var T=k.T,sky={};var c=document.createElement('canvas');c.width=8;c.height=256;var tex=new T.CanvasTexture(c);tex.colorSpace=T.SRGBColorSpace;k.trackTexture(tex);sky.canvas=c;sky.tex=tex;
    var dm=new T.MeshBasicMaterial({map:tex,side:T.BackSide,depthWrite:false,fog:false});k.trackMaterial(dm);var dome=k.mesh(k.keep(new T.SphereGeometry(95,32,16)),dm,null,W/2,g,D/2,false);dome.raycast=noop;dome.renderOrder=-3;dome.receiveShadow=false;
    var cc=document.createElement('canvas');cc.width=1024;cc.height=256;var ct=new T.CanvasTexture(cc);ct.colorSpace=T.SRGBColorSpace;ct.wrapS=T.RepeatWrapping;ct.repeat.set(3,1);k.trackTexture(ct);sky.cloudCanvas=cc;sky.cloudTex=ct;
    var cm=new T.MeshBasicMaterial({map:ct,transparent:true,side:T.BackSide,depthWrite:false,fog:false});k.trackMaterial(cm);var cd=k.mesh(k.keep(new T.SphereGeometry(85,32,10,0,PI*2,0,PI*.46)),cm,null,W/2,g+2,D/2,false);cd.raycast=noop;cd.renderOrder=-2;cd.receiveShadow=false;sky.cloudMat=cm;
    function sprite(paint,size){var t=k.canvasTexture(paint,128,128),m=new T.SpriteMaterial({map:t,transparent:true,depthWrite:false,fog:false});k.trackMaterial(m);var s=new T.Sprite(m);s.scale.set(size,size,1);s.renderOrder=-2;s.raycast=noop;k.scene.add(s);return s;}
    sky.sun=sprite(function(c,w,h){var g2=c.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);g2.addColorStop(0,'rgba(255,250,230,1)');g2.addColorStop(.18,'rgba(255,240,200,1)');g2.addColorStop(.3,'rgba(255,220,160,.45)');g2.addColorStop(1,'rgba(255,210,150,0)');c.fillStyle=g2;c.fillRect(0,0,w,h);},16);
    sky.moon=sprite(function(c,w,h){var g2=c.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);g2.addColorStop(0,'rgba(240,236,210,.35)');g2.addColorStop(1,'rgba(240,236,210,0)');c.fillStyle=g2;c.fillRect(0,0,w,h);c.fillStyle='#f3edd2';c.beginPath();c.arc(w/2,h/2,w*.16,0,PI*2);c.fill();c.fillStyle='rgba(200,196,170,.5)';[[.46,.46,.03],[.54,.55,.025],[.5,.4,.02]].forEach(function(q){c.beginPath();c.arc(w*q[0],h*q[1],w*q[2],0,PI*2);c.fill();});},9);
    var n=500,pos=new Float32Array(n*3),r=rng(9);for(var i=0;i<n;i++){var th=r()*PI*2,ph=Math.acos(.15+r()*.85);pos[i*3]=W/2+Math.sin(ph)*Math.cos(th)*88;pos[i*3+1]=g+Math.cos(ph)*88;pos[i*3+2]=D/2+Math.sin(ph)*Math.sin(th)*88;}
    var sg=k.keep(new T.BufferGeometry());sg.setAttribute('position',new T.BufferAttribute(pos,3));var smat=new T.PointsMaterial({color:'#fff8e0',size:1.6,sizeAttenuation:false,transparent:true,depthWrite:false,fog:false});k.trackMaterial(smat);sky.stars=new T.Points(sg,smat);sky.stars.raycast=noop;sky.stars.renderOrder=-2;k.scene.add(sky.stars);
    return sky;
  }
  // ---------------------------------------------------------------- room decor additions
  function decorate(k,ctx,W,D,H,terrace){
    // wall sconce on the façade
    var sc=k.walls.back?k.prop(k.walls.back,'facade_sconce','壁灯'):null;if(sc){sc.position.set(terrace?W*.86:W*.92,1.95,0);k.bx(sc,0,-.12,.03,.1,.24,.06,k.black,.01);k.box(sc,0,0,.1,.12,.18,.12,k.emissive('#ffdca8',.2,2),.03);k.box(sc,0,.12,.1,.16,.03,.16,k.black,.01);k.pointLight(sc,0,0,.3,'#ffd6a0',0,1.5,3.5);}
    // planter boxes on the railings (props)
    ['right','front'].forEach(function(side,si){var w=k.walls[side];if(!w)return;var len=w.userData.length;for(var i=0;i<(len>3?2:1);i++){var u=len*(i+1)/((len>3?2:1)+1);var p=k.prop(w,'rail_planter_'+side+'_'+i,'栏杆花箱');p.position.set(u,.98,.08);k.bx(p,0,0,0,.62,.16,.18,k.material('#b9a586',.85),.02);for(var f=0;f<7;f++){k.sph(p,-.25+f*.083,.2+(f%2)*.04,(f%3-1)*.04,.04,.035,.04,k.mat(['#f2c9d2','#ffffff','#e8857a','#f7e2a4','#c8abc2'][(f+si)%5],.7));k.sph(p,-.25+f*.083,.16,0,.05,.03,.05,f%2?k.leaf:k.leafDark);}}});
    // doormat inside the façade door + step-free threshold
    (k.windows||[]).forEach(function(wd){if(!wd.door||!wd.facade)return;var dm=k.prop(wd.wall,'doormat_'+wd.side,'门垫');dm.position.set((wd.u0+wd.u1)/2,.003,.36);k.bx(dm,0,0,0,(wd.u1-wd.u0)*.9,.014,.5,k.material('#ffffff',.95,{map:k.tex.basket}),.006).castShadow=false;k.bx(wd.wall,(wd.u0+wd.u1)/2,0,-.05,wd.u1-wd.u0+.04,.025,.16,k.material('#b9ad9a',.6),.004);});
    if(terrace){
      var rug=k.prop(null,'terrace_rug','户外地毯');var rt=k.canvasTexture(function(c,w,h){c.fillStyle='#e9e0cc';c.fillRect(0,0,w,h);c.fillStyle='#a8b89d';for(var i=0;i<w;i+=32)c.fillRect(i,0,14,h);c.strokeStyle='#d9c9a6';c.lineWidth=6;c.strokeRect(8,8,w-16,h-16);},256,128);k.bx(rug,W/2,.004,1.75,1.9,.012,1.0,k.material('#ffffff',.95,{map:rt}),.004).castShadow=false;
      var lw=k.walls.left;if(lw){var ivy=k.prop(lw,'ivy','爬藤');ivy.position.set(lw.userData.length-.62,0,.025);var it=k.canvasTexture(function(c,w,h){c.clearRect(0,0,w,h);var r=rng(4);c.strokeStyle='#5f7a52';c.lineWidth=3;for(var s=0;s<6;s++){c.beginPath();var x=w*(.15+s*.13);c.moveTo(x,h);for(var y=h;y>h*(.15+r()*.3);y-=12){x+=Math.sin(y*.05+s)*4;c.lineTo(x,y);}c.stroke();}for(var i=0;i<520;i++){var x2=w*(.1+r()*.8),y2=h*(.1+r()*.9)*(.6+.4*(1-Math.abs(x2/w-.5)));c.fillStyle=['#6f9a5f','#86ad70','#5d8550','#9cbd84'][i%4];c.beginPath();c.ellipse(x2,y2,7,5,r()*PI,0,PI*2);c.fill();}},256,512);
        var im=k.material('#ffffff',.85,{map:it,transparent:true,alphaTest:.3,side:k.T.DoubleSide});var ip=k.mesh(k.keep(new k.T.PlaneGeometry(1.2,2.3)),im,ivy,0,1.15,0,false);ip.castShadow=true;}
    }else{
      // ceiling-hung laundry rack under the eave
      var lr=k.prop(null,'laundry_rack','晾衣架');lr.position.set(W*.55,0,.72);var bar=k.cyl(lr,0,2.3,0,.012,.012,1.6,k.chrome);bar.rotation.z=PI/2;[-.7,.7].forEach(function(x){k.cylB(lr,x,2.3,0,.006,.006,H+.1-2.3,k.chrome);});
      var cl=['#f5e8cd','#c8abc2','#a8b89d','#e9d7d0','#f2efe8'];for(var i=0;i<5;i++){var hg=k.group(lr,-.56+i*.28,2.28,0);k.swayers.push({obj:hg,kind:'plant'});k.tor(hg,0,-.03,0,.05,.004,k.chrome,PI).rotation.y=PI/2;var len=.42+(i%3)*.14;k.bx(hg,0,-.06-len,0,.025,len,.34,k.fabric(cl[i],true),.01);}
    }
  }
  // ---------------------------------------------------------------- build entry
  function build(k,ctx){
    var W=k.W,D=k.D,H=k.H,terrace=k.room==='露台',g=ctx.groundY,top=terrace?3.2:6.4;
    var house=buildHouse(k,ctx,W,D,H,g,top,terrace);buildRoomEdges(k,ctx,house,W,D,H,g,terrace);var world=buildGarden(k,ctx,house,W,D,g,terrace);world.sky=buildSky(k,W,D,g);decorate(k,ctx,W,D,H,terrace);
    world.terrace=terrace;world.covered=!terrace;world.upper=k._upperLevel||null;world.groundY=g;world.roof=k._roofMat;world.W=W;world.D=D;world.plantSpots=[];
    var P=root.RoomModel.plan;['flower_bed','plants'].forEach(function(id){var p=P[id];if(p&&(root.Room3DModels.roomItems[k.room]||[]).indexOf(id)>=0)world.plantSpots.push([k.X(p[0]+p[2]/2),k.Z(p[1]+p[3]/2)]);});
    world.plantSpots.push([W+.9,D+1.2],[W+5.8,D+2.8]);
    k.outdoorWorld=world;return world;
  }
  // ---------------------------------------------------------------- time & weather driven effect
  function outdoorEffect(rig){
    var k=rig.kit,world=k&&k.outdoorWorld;if(!rig.outdoor||!world)return null;
    var T=rig.T,A=root.Room3DAtmosphere,scene=rig.scene,W=world.W,D=world.D,g=world.groundY,sky=world.sky,env=null,t=0,owned=[];
    function own(o){owned.push(o);return o;}
    var base={grass:world.grassMat.color.clone(),grassRough:world.grassMat.roughness,foliage:world.foliage.map(function(m){return m.color.clone();}),water:world.water?world.water.color.clone():null,far:world.far.map(function(m){return m.color.clone();}),roof:world.roof?world.roof.color.clone():null};
    // ---- birds
    var birds=[],birdMat=own(new T.MeshBasicMaterial({color:'#3d4148',side:T.DoubleSide,fog:true}));var wingGeo=own(new T.PlaneGeometry(.34,.1));wingGeo.translate(.17,0,0);
    for(var i=0;i<6;i++){var b=new T.Group(),l=new T.Mesh(wingGeo,birdMat),r=new T.Mesh(wingGeo,birdMat);r.rotation.y=PI;b.add(l,r);b.userData={l:l,r:r,rad:7+i*1.4,h:10+(i%3)*1.8,sp:.22+i*.035,ph:i*1.1,cx:world.lifeArea?(world.lifeArea.x0+world.lifeArea.x1)/2+(i%2)*3-1.5:W+6+(i%2)*3,cz:world.lifeArea?world.lifeArea.z0-4-(i%3)*2:-6-(i%3)*2};b.traverse(function(o){o.raycast=noop;});scene.add(b);birds.push(b);}
    // ---- butterflies
    var bfs=[],bfCols=['#f2c9d2','#f7e2a4','#b7c9e8'];bfCols.forEach(function(c,i){var m=own(new T.MeshBasicMaterial({color:c,side:T.DoubleSide}));var gg=own(new T.CircleGeometry(.05,8));gg.translate(.05,0,0);var b=new T.Group(),l=new T.Mesh(gg,m),r=new T.Mesh(gg,m);r.rotation.y=PI;b.add(l,r);var spot=world.plantSpots[i%world.plantSpots.length];b.userData={l:l,r:r,spot:spot,ph:i*2.1,base:(spot[0]<=W&&spot[1]<=D)?0:g};b.traverse(function(o){o.raycast=noop;});scene.add(b);bfs.push(b);});
    // ---- fireflies
    var FF=46,fpos=new Float32Array(FF*3),fcol=new Float32Array(FF*3),fseed=[],r=rng(21),la=world.lifeArea;for(var f=0;f<FF;f++){var inRoom=!la&&f<10,x=la?la.x0+r()*(la.x1-la.x0):inRoom?.2+r()*(W-.4):W+.6+r()*8,z=la?la.z0+r()*(la.z1-la.z0):inRoom?.4+r()*(D-.6):-4+r()*(D+9),y=(la?la.y:inRoom?0:g)+.25+r()*1.3;fpos[f*3]=x;fpos[f*3+1]=y;fpos[f*3+2]=z;fseed.push([x,y,z,r()*10,.6+r()*1.4]);}
    var fg=own(new T.BufferGeometry());fg.setAttribute('position',new T.BufferAttribute(fpos,3));fg.setAttribute('color',new T.BufferAttribute(fcol,3));
    var ftex=k.canvasTexture(function(c,w,h){var gr=c.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);gr.addColorStop(0,'rgba(255,255,255,1)');gr.addColorStop(.3,'rgba(255,255,255,.6)');gr.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=gr;c.fillRect(0,0,w,h);},32,32);
    var fm=own(new T.PointsMaterial({size:.12,map:ftex,vertexColors:true,transparent:true,blending:T.AdditiveBlending,depthWrite:false}));var flies=new T.Points(fg,fm);flies.raycast=noop;flies.frustumCulled=false;scene.add(flies);
    // ---- wind-blown leaves
    var LN=60,leafGeo=own(new T.PlaneGeometry(.07,.045)),leafMat=own(new T.MeshStandardMaterial({color:'#b69a5a',side:T.DoubleSide,roughness:.8})),leaves=new T.InstancedMesh(leafGeo,leafMat,LN),lseed=[],m4=new T.Matrix4(),q=new T.Quaternion(),e=new T.Euler(),v=new T.Vector3(),one=new T.Vector3(1,1,1),lc=new T.Color();
    for(var li=0;li<LN;li++){lseed.push({x:-3+r()*(W+12),y:g+r()*5,z:-3+r()*(D+10),s:r()*6,v:.6+r()});leaves.setColorAt(li,lc.set(['#b69a5a','#9fb07a','#c98f5f','#d7b56d'][li%4]));}
    leaves.raycast=noop;leaves.castShadow=false;leaves.frustumCulled=false;scene.add(leaves);
    // ---- rain ripples (on exposed deck + ground) and puddles
    var RN=110,ringGeo=own(new T.RingGeometry(.7,1,24));ringGeo.rotateX(-PI/2);var ringMat=own(new T.MeshBasicMaterial({color:'#cfe0ea',transparent:true,blending:T.AdditiveBlending,depthWrite:false,opacity:.16})),rings=new T.InstancedMesh(ringGeo,ringMat,RN),rseed=[];
    for(var ri=0;ri<RN;ri++){var onDeck=ri<45&&!world.covered,rx,rz;if(onDeck){rx=.1+r()*(W-.2);rz=(rig.awning?1.2:.1)+r()*(D-(rig.awning?1.3:.2));}else{rx=W+.3+r()*7;rz=-3+r()*(D+8);}rseed.push({x:rx,z:rz,y:(onDeck?0:g)+.012,p:r(),sp:1.2+r()*.8});rings.setColorAt(ri,lc.set('#ffffff'));}
    rings.raycast=noop;rings.castShadow=false;rings.frustumCulled=false;scene.add(rings);
    var puddleMat=own(new T.MeshStandardMaterial({color:'#6b7680',roughness:.04,metalness:.4,transparent:true,opacity:.55,depthWrite:false})),puddles=new T.Group();scene.add(puddles);
    [[W*.35,D*.75,.5,.3,0],[W*.7,D*.5,.35,.22,0],[W+1.6,D+2,.9,.5,g],[W+4,-1,.7,.4,g],[W+3.2,D+4.2,.6,.35,g]].forEach(function(p2){if(!world.terrace&&p2[4]===0&&(world.covered||rig.awning&&p2[1]<1.2))return;var m=new T.Mesh(own(new T.CircleGeometry(1,24)),puddleMat);m.rotation.x=-PI/2;m.scale.set(p2[2],p2[3],1);m.position.set(p2[0],p2[4]+.009,p2[1]);m.raycast=noop;m.receiveShadow=true;puddles.add(m);});
    if(puddleMat&&k.metals)k.metals.push(puddleMat);
    var flags={birds:false,bfs:false,flies:false,leaves:false,rain:false};
    function apply(next,state){
      env=next;var hr=A.hourOf(env),night=env.band==='night',w=env.weather,wx=A.WX[w]||A.WX.clear,cover=wx[5];
      // dome gradient: zenith → horizon (+ warm band at dawn/dusk)
      var cols=A.skyColors(T,env),c=sky.canvas.getContext('2d'),gr=c.createLinearGradient(0,0,0,256);var zen='#'+cols[0].getHexString(),hor='#'+cols[1].getHexString();
      gr.addColorStop(0,zen);gr.addColorStop(.42,'#'+cols[0].clone().lerp(cols[1],.6).getHexString());gr.addColorStop(.5,hor);gr.addColorStop(1,hor);c.fillStyle=gr;c.fillRect(0,0,8,256);sky.tex.needsUpdate=true;
      // sun / moon
      var dir=state.sunDir.clone(),centre=new T.Vector3(W/2,g,D/2);sky.sun.position.copy(centre).addScaledVector(dir,80);sky.moon.position.copy(centre).addScaledVector(dir,80);
      sky.sun.visible=!night&&cover<.9;sky.sun.material.opacity=1-cover*.8;var warm=hr<8||hr>16.5;sky.sun.material.color.set(warm?'#ffc890':'#ffffff');sky.sun.scale.setScalar(warm?20:15);
      sky.moon.visible=night&&cover<.95;sky.moon.material.opacity=1-cover*.7;
      sky.stars.visible=night;sky.stars.material.opacity=Math.max(0,1-cover*1.1);
      // clouds on the dome
      var lightCol=cols[1].clone().lerp(new T.Color('#ffffff'),night?.1:.6);if(night)lightCol.multiplyScalar(.5);A.paintClouds(T,sky.cloudCanvas.getContext('2d'),1024,256,env,wx,lightCol);sky.cloudTex.needsUpdate=true;sky.cloudMat.opacity=.55+cover*.45;
      // distance tint + haze
      var lv=Math.max(.25,Math.min(1,state.light*1.2+(night?.15:.2)));world.hillMat.color.setScalar(lv).lerp(new T.Color(hor),.25+cover*.25);
      world.far.forEach(function(m,i){m.color.copy(base.far[i]).multiplyScalar(.5+lv*.5);});
      if(w!=='fog')scene.fog=new T.FogExp2('#'+cols[1].clone().lerp(new T.Color(night?'#2a3346':'#e6e8e2'),.35).getHexString(),night?.022:.016);
      // ground: wet / snow
      var snow=w==='snow',wet=wx[7];world.grassMat.color.copy(base.grass).multiplyScalar(1-.18*wet);if(snow)world.grassMat.color.lerp(new T.Color('#f4f7fa'),.85);world.grassMat.roughness=base.grassRough*(1-.4*wet);
      world.foliage.forEach(function(m,i){m.color.copy(base.foliage[i]);if(snow)m.color.lerp(new T.Color('#eef2f4'),.5);});
      if(world.water){world.water.color.copy(base.water);if(snow)world.water.color.lerp(new T.Color('#dfe8ec'),.8);world.water.roughness=snow?.5:.06;}(world.waters||[]).forEach(function(wt){if(!wt.base)wt.base=wt.mat.color.clone();wt.mat.color.copy(wt.base);if(snow)wt.mat.color.lerp(new T.Color('#dfe8ec'),.6);});
      if(world.flowers)world.flowers.visible=!snow;if(world.roof){world.roof.color.copy(base.roof);if(snow)world.roof.color.lerp(new T.Color('#f2f5f8'),.8);world.roof.roughness=.7-.35*wet;}
      // life
      flags.birds=!night&&(w==='clear'||w==='cloudy'||w==='wind')&&hr>6&&hr<19;flags.bfs=!night&&(w==='clear'||w==='cloudy')&&hr>8&&hr<17.5;flags.flies=night&&(w==='clear'||w==='cloudy'||w==='wind');flags.leaves=w==='wind'||w==='storm';flags.rain=w==='rain'||w==='storm';
      birds.forEach(function(b){b.visible=flags.birds;});bfs.forEach(function(b){b.visible=flags.bfs;});flies.visible=flags.flies;leaves.visible=flags.leaves;rings.visible=flags.rain&&!rig.sheltered;puddles.visible=wet>.5&&!rig.sheltered;
      if(!flags.leaves)leaves.count=0;else leaves.count=LN;
    }
    function update(dt,time){
      t+=dt;if(!env)return false;var wx=A.WX[env.weather]||A.WX.clear,wind=wx[6];
      sky.cloudTex.offset.x=(sky.cloudTex.offset.x+dt*(.002+wind*.008))%1;
      if(flags.birds)birds.forEach(function(b){var u=b.userData,a=t*u.sp+u.ph;b.position.set(u.cx+Math.cos(a)*u.rad,g+u.h+Math.sin(a*2)*.4,u.cz+Math.sin(a)*u.rad);b.rotation.y=-a;var f=Math.sin(t*9+u.ph)*.7;u.l.rotation.x=f;u.r.rotation.x=-f;});
      if(flags.bfs)bfs.forEach(function(b){var u=b.userData,s=u.spot;b.position.set(s[0]+Math.sin(t*.7+u.ph)*.6+Math.sin(t*2.3+u.ph)*.12,u.base+.55+Math.sin(t*1.3+u.ph)*.22,s[1]+Math.cos(t*.5+u.ph*2)*.5);b.rotation.y=t*.7+u.ph;var f=Math.sin(t*22+u.ph)*1.1;u.l.rotation.y=f;u.r.rotation.y=PI-f;});
      if(flags.flies){var p=fg.attributes.position.array,c=fg.attributes.color.array;for(var i=0;i<FF;i++){var s=fseed[i];p[i*3]=s[0]+Math.sin(t*.4*s[4]+s[3])*.5;p[i*3+1]=s[1]+Math.sin(t*.7*s[4]+s[3]*2)*.25;p[i*3+2]=s[2]+Math.cos(t*.35*s[4]+s[3])*.5;var bl=Math.max(0,Math.sin(t*s[4]*1.6+s[3]));bl=bl*bl;c[i*3]=1*bl;c[i*3+1]=.95*bl;c[i*3+2]=.45*bl;}fg.attributes.position.needsUpdate=true;fg.attributes.color.needsUpdate=true;}
      if(flags.leaves){for(var j=0;j<LN;j++){var L=lseed[j];L.x+=dt*(1.2+wind*2.2)*L.v;L.y-=dt*.35*L.v;L.z+=Math.sin(t+L.s)*dt*.6;if(L.x>W+12||L.y<g){L.x=-3;L.y=g+1+Math.random()*4.5;L.z=-3+Math.random()*(D+10);}e.set(t*3*L.v+L.s,t*2+L.s,t*4*L.v);q.setFromEuler(e);v.set(L.x,L.y,L.z);m4.compose(v,q,one);leaves.setMatrixAt(j,m4);}leaves.instanceMatrix.needsUpdate=true;}
      if(flags.rain){for(var k2=0;k2<rseed.length;k2++){var R=rseed[k2],ph=(t*R.sp+R.p)%1;var sc=.015+ph*.085;v.set(R.x,R.y,R.z);m4.compose(v,q.identity(),new T.Vector3(sc,1,sc));rings.setMatrixAt(k2,m4);rings.setColorAt(k2,lc.setScalar(1-ph));if(ph<dt*R.sp*1.5){R.x=(R.y>0?.1+Math.random()*(W-.2):W+.3+Math.random()*7);R.z=R.y>0?(rig.awning?1.2:.1)+Math.random()*(D-(rig.awning?1.3:.2)):-3+Math.random()*(D+8);}}rings.instanceMatrix.needsUpdate=true;if(rings.instanceColor)rings.instanceColor.needsUpdate=true;}
      return true;
    }
    function dispose(){owned.forEach(function(o){if(o&&o.dispose)o.dispose();});[birds,bfs].forEach(function(list){list.forEach(function(b){scene.remove(b);});});scene.remove(flies);scene.remove(leaves);scene.remove(rings);scene.remove(puddles);}
    return {apply:apply,update:update,dispose:dispose};
  }
  root.Room3DOutdoor={build:build,effect:outdoorEffect,buildSky:buildSky};
  if(root.Room3DAtmosphere)root.Room3DAtmosphere.registerEffect('outdoor-world',outdoorEffect);
})(window);
