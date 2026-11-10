  // ------------------------------------------------------------------ walls
  function walls(k,cfg,ctx){
    var X=ctx.X,out={},th=k.theme;
    function holesFromPlan(list,kind){return (list||[]).map(function(w){return {u0:X(w[0]),u1:X(w[1]),y0:kind==='door'?0:w[2],y1:kind==='door'?2.12:w[3],type:kind==='door'?(w[2]||'door'):'window'};});}
    var backHoles=holesFromPlan(cfg.windows,'window').concat(holesFromPlan(cfg.doors,'door'));
    var O=((root.RoomModel||{}).openings||{})[k.room],side={};
    if(O){var Z=ctx.Z,W=ctx.W,D=ctx.D;
      var hole=function(o,u0,u1){var win=o[2]==='win';return {u0:u0,u1:u1,y0:win?(o[3]||1.0):0,y1:win?(o[4]||2.3):(o[2]==='glass'?2.15:2.12),type:win?'window':o[2]};};
      side.back=(O.N||[]).map(function(o){return hole(o,X(o[0]),X(o[1]));});
      side.front=(O.S||[]).map(function(o){return hole(o,W-X(o[1]),W-X(o[0]));});
      side.left=(O.W||[]).map(function(o){return hole(o,D-Z(o[1]),D-Z(o[0]));});
      side.right=(O.E||[]).map(function(o){return hole(o,Z(o[0]),Z(o[1]));});
      backHoles=side.back;}
    if(cfg.outdoor){
      out.back={kind:'facade',holes:backHoles};
      out.left={kind:'facade',holes:O?side.left:(cfg.leftOpenings||[]).map(function(o){return {u0:ctx.D-o[1],u1:ctx.D-o[0],y0:o[2],y1:o[3],type:o[4]};})};
      out.right={kind:'rail'};out.front={kind:'rail'};
      return out;
    }
    var wains=cfg.wainscot||(k.room==='影音室'?'none':'panel');
    out.back={kind:'wall',holes:backHoles,wainscot:wains,curtain:cfg.curtain};
    out.right={kind:'wall',holes:O?side.right:[],wainscot:wains,curtain:cfg.curtain};out.left={kind:'wall',holes:O?side.left:[],wainscot:wains,curtain:cfg.curtain};
    var frontHoles=[];if(O)frontHoles=side.front;else if(!ctx.corridor){var du=ctx.W*.42;frontHoles.push({u0:ctx.W-du-.9,u1:ctx.W-du,y0:0,y1:2.1,type:'door'});}
    out.front={kind:'wall',holes:frontHoles,wainscot:wains};
    return out;
  }
  function spans(len,holes,y,a,b){var segs=[[a==null?0:a,b==null?len:b]];holes.forEach(function(h){if(y<h.y0-.001||y>h.y1+.001)return;var next=[];segs.forEach(function(s){if(h.u1<=s[0]||h.u0>=s[1]){next.push(s);return;}if(h.u0-.04>s[0])next.push([s[0],h.u0-.04]);if(h.u1+.04<s[1])next.push([h.u1+.04,s[1]]);});segs=next;});return segs.filter(function(s){return s[1]-s[0]>.02;});}
  function curtains(k,g,h,color){
    var T=k.T,mat=k.fabric(color,true);if(!k._curtainGeo){var geo=new T.PlaneGeometry(.34,1,18,16),pos=geo.attributes.position;for(var i=0;i<pos.count;i++){pos.setZ(i,Math.sin(pos.getX(i)*110)*.025);pos.setX(i,pos.getX(i)*(1-.18*Math.sin((pos.getY(i)+.5)*PI)));}geo.computeVertexNormals();k._curtainGeo=k.keep(geo);}
    var ch=Math.min(2.5,h.y1+.08)-Math.max(.25,h.y0-.4);
    [h.u0-.36,h.u1+.02].forEach(function(x){var top=Math.max(.25,h.y0-.4)+ch,pv=k.group(g,x+.17,top,.14);var c=k.mesh(k._curtainGeo,mat,pv,0,-ch/2,0);c.scale.y=ch;k.swayers.push({obj:pv,kind:'curtain'});k.tor(g,x+.17,h.y0+.12,.15,.07,.008,k.brass).scale.set(1,.35,1);});
    var rod=k.cyl(g,(h.u0+h.u1)/2,h.y1+.1,.15,.012,.012,h.u1-h.u0+.9,k.brass);rod.rotation.z=PI/2;k.sph(g,h.u0-.45,h.y1+.1,.15,.035,.035,.035,k.brass);k.sph(g,h.u1+.45,h.y1+.1,.15,.035,.035,.035,k.brass);
  }
  function interiorMaterial(k){if(k._interiorMat)return k._interiorMat;var t=k.canvasTexture(function(c,w,h){c.fillStyle='#d9c7ae';c.fillRect(0,0,w,h);c.fillStyle='#c4ad90';c.fillRect(0,h*.68,w,h*.32);c.fillStyle='#e9dcc8';c.fillRect(w*.08,h*.18,w*.22,h*.3);c.fillStyle='#b9a7b9';c.fillRect(0,0,w*.16,h);c.fillRect(w*.84,0,w*.16,h);var g=c.createRadialGradient(w*.6,h*.35,0,w*.6,h*.35,w*.5);g.addColorStop(0,'rgba(255,236,190,.9)');g.addColorStop(1,'rgba(255,236,190,0)');c.fillStyle=g;c.fillRect(0,0,w,h);c.fillStyle='#8d7a66';c.fillRect(w*.45,h*.55,w*.3,h*.16);},128,128);
    k._interiorMat=k.material('#8f8478',.6,{map:t,emissive:'#ffffff',emissiveMap:t,emissiveIntensity:.05,lit:[.05,.85]});return k._interiorMat;}
  function windowUnit(k,g,h,t,spec,facade,side){k.windows.push({wall:g,u0:h.u0,u1:h.u1,y0:h.y0,y1:h.y1,t:t,side:side,facade:!!facade});
    var sky=k.mesh(k.cachedPlane?k.cachedPlane:k.keep(new k.T.PlaneGeometry(1,1)),facade?interiorMaterial(k):k.skyMat,g,(h.u0+h.u1)/2,(h.y0+h.y1)/2,-t-.012,false);sky.scale.set(h.u1-h.u0+.04,h.y1-h.y0+.04,1);
    var w=h.u1-h.u0,cx=(h.u0+h.u1)/2,cy=(h.y0+h.y1)/2,frame=k.batch(g,facade?k.paint:k.cream);
    var pane=k.box(g,cx,cy,-t/2,w,h.y1-h.y0,.006,k.glass);pane.castShadow=false;
    frame.box(h.u0-.04,cy,0,.08,h.y1-h.y0+.08,.14,.01).box(h.u1+.04,cy,0,.08,h.y1-h.y0+.08,.14,.01).box(cx,h.y1+.04,0,w+.16,.08,.14,.01);
    var n=Math.max(1,Math.round(w/.85));for(var i=1;i<n;i++)frame.box(h.u0+w*i/n,cy,-t/2,.04,h.y1-h.y0,.06);frame.box(cx,h.y0+(h.y1-h.y0)*.64,-t/2,w,.035,.06);frame.done();
    k.bx(g,cx,h.y0-.045,.05,w+.26,.05,.22,facade?k.paint:k.wood,.015);k.bx(g,cx,h.y0-.13,0,w+.1,.09,.06,k.cream,.01);
    if(spec.curtain)curtains(k,g,h,spec.curtain);
  }
  function doorUnit(k,g,h,t,type,side){if(type==='glass')k.windows.push({wall:g,u0:h.u0,u1:h.u1,y0:.12,y1:h.y1-.06,t:t,side:side,door:true,facade:!!k.outdoor});
    var w=h.u1-h.u0,cx=(h.u0+h.u1)/2,frame=k.batch(g,type==='glass'?k.paint:k.cream);
    frame.box(h.u0-.04,h.y1/2,0,.08,h.y1+.04,.16,.008).box(h.u1+.04,h.y1/2,0,.08,h.y1+.04,.16,.008).box(cx,h.y1+.04,0,w+.16,.08,.16,.008);frame.done();
    if(type==='glass'){var sky=k.mesh(k.keep(new k.T.PlaneGeometry(w,h.y1)),k.outdoor?interiorMaterial(k):k.skyMat,g,cx,h.y1/2,-t-.012,false);var f=k.batch(g,k.paint);var sash=k.doorSash||(k.doorSash=k.material('#f4efe4',.45)),hw=w/2;[-1,1].forEach(function(sd){var lx=cx+sd*hw/2;f.box(lx-hw/2+.035,h.y1/2,-t/2,.07,h.y1,.06).box(lx+hw/2-.035,h.y1/2,-t/2,.07,h.y1,.06).box(lx,h.y1-.04,-t/2,hw,.08,.06).box(lx,.06,-t/2,hw,.12,.06).box(lx,.52,-t/2,hw,.06,.06).box(lx,1.35,-t/2,hw-.1,.03,.045).box(lx,(h.y1+.55)/2,-t/2,.03,h.y1-.62,.045);k.bx(g,lx,.12,-t/2,hw-.12,.38,.035,sash,.01);k.bx(g,lx,.18,-t/2+.025,hw-.24,.26,.01,k.mat('#e9e2d4',.5),.004);k.box(g,lx-sd*(hw/2-.1),1.0,-t/2+.045,.02,.2,.03,k.brass,.006);k.box(g,lx-sd*(hw/2-.1),1.0,-t/2-.045,.02,.2,.03,k.brass,.006);});f.done();k.box(g,cx,(h.y1+.55)/2,-t/2,w,h.y1-.6,.006,k.glass).castShadow=false;return;}
    var leaf=type==='entry'?k.material('#7d8f78',.55):(k.doorLeaf||(k.doorLeaf=k.material('#b08a63',.6)));k.bx(g,cx,0,-t/2,w,h.y1,.05,leaf,.01);
    var p=k.batch(g,type==='entry'?k.material('#8fa189',.55):(k.doorPanel||(k.doorPanel=k.material('#c29d75',.55))));p.box(cx,1.48,-t/2+.03,w-.24,.7,.012,.004).box(cx,.55,-t/2+.03,w-.24,.8,.012,.004);p.done();
    k.sph(g,h.u1-.12,1.0,-t/2+.06,.03,.03,.03,k.brass);k.bx(g,h.u1-.12,.99,-t/2+.03,.05,.02,.04,k.brass,.006);
  }
  function buildWall(k,g,len,spec,side){
    var t=.1,H=k.H,T=k.T,th=k.theme;
    if(!k.skyMat){k.skyMat=new T.MeshBasicMaterial({map:k.sky,toneMapped:true});}
    if(spec.kind==='rail'){g.userData.alwaysVisible=true;
      var post=k.batch(g,k.paint),glassH=.95;for(var u=0;u<=len+.001;u+=Math.max(.6,len/Math.ceil(len/1.1)))post.box(u,glassH/2+.03,-.04,.06,glassH+.06,.06,.01);post.box(len/2,glassH+.08,-.04,len+.06,.05,.09,.01).box(len/2,.03,-.04,len,.06,.08);post.done();k.snowCaps.push({parent:g,x:len/2,y:glassH+.118,z:-.04,w:len+.06,d:.1});
      var gp=k.box(g,len/2,glassH/2+.05,-.04,len,glassH-.1,.012,k.glass);gp.castShadow=false;
      // floor edge planter strip
      k.bx(g,len/2,0,-.12,len,.04,.12,k.material('#9c8a73',.9),.01);
      return;
    }
    var holes=spec.holes||[],wallMat=spec.kind==='facade'?k.material('#ede4d2',.92):k.material(th.wall,.92);
    var a=side==='back'||side==='front'?-t:0,b=side==='back'||side==='front'?len+t:len,pieces=k.batch(g,wallMat),cuts=[a];
    holes.slice().sort(function(p,q){return p.u0-q.u0;}).forEach(function(h){pieces.box((cuts[cuts.length-1]+h.u0)/2,H/2,-t/2,h.u0-cuts[cuts.length-1],H,t);if(h.y0>0)pieces.box((h.u0+h.u1)/2,h.y0/2,-t/2,h.u1-h.u0,h.y0,t);pieces.box((h.u0+h.u1)/2,(h.y1+H)/2,-t/2,h.u1-h.u0,H-h.y1,t);cuts.push(h.u1);});
    pieces.box((cuts[cuts.length-1]+b)/2,H/2,-t/2,b-cuts[cuts.length-1],H,t);pieces.done();
    if(spec.kind==='facade'){
      var trim=k.batch(g,k.material('#c9bba3',.85));trim.box(len/2,.12,.01,len+.2,.24,.03).box(len/2,H-.05,.02,len+.2,.1,.06);for(var y=.4;y<H-.2;y+=.18)spans(len,holes,y).forEach(function(s){trim.box((s[0]+s[1])/2,y,.002,s[1]-s[0],.012,.008);});trim.done();
      if(spec.awning){var aw=k.box(g,len/2,H-.02,.5,len+.2,.04,1.0,k.material('#d7cbb3',.8),.01);aw.rotation.x=.14;k.bx(g,len/2,H-.2,.98,len+.2,.1,.05,k.material('#a9bba1',.85),.01);}
    }else if(spec.wainscot==='tile'){
      var tileTex=k.tileWall||(k.tileWall=k.canvasTexture(function(c,w,h){c.fillStyle='#c9d3c9';c.fillRect(0,0,w,h);for(var i=0;i<4;i++)for(var j=0;j<8;j++){c.fillStyle=['#f1f4ee','#e9efe7','#f4f6f1'][(i+j)%3];c.fillRect(i*w/4+2+(j%2)*w/8,j*h/8+2,w/4-4,h/8-4);}},256,256,[1,1]));
      spans(len,holes,.6,0,len).forEach(function(s){var m=k.material('#ffffff',.25,{map:tileTex.clone()});m.map.wrapS=m.map.wrapT=T.RepeatWrapping;m.map.repeat.set((s[1]-s[0])/.6,2);m.map.needsUpdate=true;k.box(g,(s[0]+s[1])/2,.62,.01,s[1]-s[0],1.24,.02,m).castShadow=false;});
      var tt=k.batch(g,k.cream);spans(len,holes,1.24,0,len).forEach(function(s){tt.box((s[0]+s[1])/2,1.25,.02,s[1]-s[0],.03,.04,.004);});spans(len,holes,.04,0,len).forEach(function(s){tt.box((s[0]+s[1])/2,.04,.02,s[1]-s[0],.08,.03);});tt.done();
    }else if(spec.wainscot==='panel'){
      var panel=k.material(th.side,.85),pb=k.batch(g,panel);spans(len,holes,.3,0,len).forEach(function(s){pb.box((s[0]+s[1])/2,.32,.017,s[1]-s[0],.64,.035);});pb.done();
      var tr=k.batch(g,k.cream);[.07,.64].forEach(function(y){spans(len,holes,y,0,len).forEach(function(s){tr.box((s[0]+s[1])/2,y,.04,s[1]-s[0],y<.1?.12:.035,.075,.004);});});
      spans(len,holes,2.6,0,len).forEach(function(s){tr.box((s[0]+s[1])/2,2.58,.04,s[1]-s[0],.035,.075,.004);tr.box((s[0]+s[1])/2,2.62,.03,s[1]-s[0],.04,.06,.004);});
      spans(len,holes,.3,0,len).forEach(function(s){for(var px=s[0]+.08;px+.66<s[1];px+=.75){tr.box(px+.03,.32,.045,.016,.40,.018);tr.box(px+.63,.32,.045,.016,.40,.018);tr.box(px+.33,.12,.045,.61,.016,.018);tr.box(px+.33,.52,.045,.61,.016,.018);}});tr.done();
    }else{var base=k.batch(g,k.material('#3a3446',.7));spans(len,holes,.05,0,len).forEach(function(s){base.box((s[0]+s[1])/2,.05,.02,s[1]-s[0],.1,.03);});base.done();}
    if(!k._aoTex)k._aoTex=k.canvasTexture(function(c,w,h){var gr=c.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#ffffff');gr.addColorStop(.35,'#737373');gr.addColorStop(1,'#000000');c.fillStyle=gr;c.fillRect(0,0,w,h);},4,64);
    if(!k._aoMat)k._aoMat=k.material('#2a2230',1,{transparent:true,alphaMap:k._aoTex,opacity:k.room==='影音室'?.4:.22,depthWrite:false});
    var ao=k.mesh(k.keep(new T.PlaneGeometry(b-a,.42)),k._aoMat,g,(a+b)/2,.004,.21,false);ao.rotation.x=-PI/2;ao.raycast=function(){};ao.receiveShadow=false;
    holes.forEach(function(h){if(h.type==='window')windowUnit(k,g,h,t,spec,spec.kind==='facade',side);else doorUnit(k,g,h,t,h.type,side);});
  }
  function shade(hex,f){var n=parseInt(hex.slice(1),16),r=(n>>16)&255,g=(n>>8)&255,b=n&255;r=Math.round(r*f*.92);g=Math.round(g*f*.9);b=Math.round(Math.min(255,b*f*1.02));return '#'+((1<<24)+(r<<16)+(g<<8)+b).toString(16).slice(1);}
  // ------------------------------------------------------------------ shared pieces
  function cabinet(k,g,L,D,H,o){
    o=o||{};var body=o.body||k.wood,front=o.front||k.wood,plinth=o.legs?0:.08;
    if(o.legs)k.legs(g,L,D,o.legs,.07);else k.bx(g,0,0,-.02,L-.04,plinth,D-.06,k.darkWood);
    var y0=o.legs||plinth,top=o.top||k.cream;k.bx(g,0,y0,0,L,H-y0-.035,D,body,.02);k.bx(g,0,H-.035,.005,L+.02,.035,D+.02,top,.01);
    var gaps=o.gaps||[],n=Math.max(1,Math.round(L/(o.door||.55))),dw=L/n;
    for(var i=0;i<n;i++){var cx=-L/2+dw*(i+.5),blocked=gaps.some(function(r){return cx+dw/2>r[0]+.01&&cx-dw/2<r[1]-.01;});if(blocked)continue;
      if(o.drawers){var rows=o.drawers,dh=(H-y0-.06)/rows;for(var r=0;r<rows;r++){k.bx(g,cx,y0+.02+r*dh,D/2+.008,dw-.025,dh-.025,.016,front,.006);k.bx(g,cx,y0+.02+r*dh+dh*.55,D/2+.022,.12,.016,.014,k.brass,.004);}}
      else{k.bx(g,cx,y0+.02,D/2+.008,dw-.025,H-y0-.08,.016,front,.006);k.bx(g,cx+(i%2?-1:1)*(dw/2-.07),y0+(H-y0)*.62,D/2+.024,.016,.14,.016,k.brass,.004);}}
  }
  function seatSofa(k,g,L,D,o){
    o=o||{};var f=k.fabric(o.color||'#b9c6ad'),f2=k.fabric(o.cushion||o.color||'#c9d3bc'),arm=o.arm||.16,seats=o.seats||3,seatY=o.seatY||.3,backH=o.back||.48;
    k.legs(g,L,D,.1,.1,k.darkWood,.022);k.bx(g,0,.1,0,L,.2,D,f,.05);
    k.bx(g,0,.1,-D/2+.11,L,seatY+backH-.1,.22,f,.06);
    [-1,1].forEach(function(s){k.bx(g,s*(L/2-arm/2),.1,0,arm,seatY+.16,D,f,.06);});
    var cw=(L-2*arm)/seats;for(var i=0;i<seats;i++){var x=-L/2+arm+cw*(i+.5);k.mesh(k.pillow(cw-.02,.16,D-.3),f2,g,x,seatY+.05,.07);var b=k.mesh(k.pillow(cw-.05,.18,backH*.95),f2,g,x,seatY+backH*.5+.04,-D/2+.3);b.rotation.x=1.3;if(o.recliner){k.cylB(g,x+cw/2-.01,seatY+.16,D/2-.25,.035,.035,.02,k.black);}}
    (o.throws||['#c8abc2','#f5e8cd']).forEach(function(c,i){var p=k.mesh(k.pillow(.4,.13,.4),k.fabric(c),g,(i?1:-1)*(L/2-arm-.25),seatY+.27,-D/2+.42);p.rotation.x=1.05;p.rotation.z=(i?-1:1)*.12;});
  }
  function chair(k,g,L,D,o){
    o=o||{};var seatH=o.seat||.45,m=o.wood||k.wood;k.legs(g,L*.82,D*.82,seatH-.04,.03,m,.018);k.bx(g,0,seatH-.04,0,L*.86,.04,D*.86,m,.01);
    k.mesh(k.pillow(L*.8,.06,D*.78),k.fabric(o.color||'#c9d3bc'),g,0,seatH+.02,.0);
    if(o.back!==false){[-1,1].forEach(function(s){k.bx(g,s*(L*.41-.02),seatH,-D*.41+.02,.03,.42,.03,m,.006);});k.bx(g,0,seatH+.3,-D*.41+.02,L*.82,.12,.025,m,.008);k.bx(g,0,seatH+.12,-D*.41+.02,L*.74,.05,.02,m,.006);}
  }
  function plant(k,g,x,z,size,o){
    o=o||{};var s=size||1,pot=o.pot||k.mat('#e9e0d1',.55);k.cylB(g,x,0,z,.17*s,.13*s,.34*s,pot);k.cylB(g,x,.33*s,z,.15*s,.15*s,.02,k.soil);
    var lg=k.group(g,x,.34*s,z);k.swayers.push({obj:lg,kind:'plant'});for(var i=0;i<(o.leaves||11);i++){var ang=i*2.4,len=(.32+(i%3)*.1)*s,L=k.sph(lg,Math.cos(ang)*.07*s,.02*s+len*.45,Math.sin(ang)*.07*s,.06*s,len*.5,.018*s,i%2?k.leaf:k.leafDark);L.rotation.set(Math.sin(ang)*.55,ang,Math.cos(ang)*.55);}
  }
  function frameArt(k,g,w,h,paint,o){o=o||{};var t=k.canvasTexture(paint,192,Math.round(192*h/w));k.box(g,0,0,.022,w,h,.04,o.frame||k.brass,.008);k.box(g,0,0,.044,w-.07,h-.07,.005,k.material('#ffffff',.9,{map:t})).castShadow=false;}
  function wallProp(k,side,id,name,u,y,off){var w=k.walls[side];if(!w)return null;var g=k.prop(w,id,name);g.position.set(u,y,off||0);return g;}
  function floorProp(k,id,name,x,z,rot){var g=k.prop(null,id,name);g.position.set(x,0,z);g.rotation.y=rot||0;return g;}
  function pendant(k,id,name,x,z,drop,o){o=o||{};var g=floorProp(k,id,name||'吊灯',x,z),y=k.H-(drop||.7);k.cylB(g,0,y+.2,0,.004,.004,k.H-y-.2,k.black);var shadeM=k.material(o.color||'#f2e3c2',.7,{side:k.T.DoubleSide,emissive:'#ffd395',emissiveIntensity:.08,lit:[.08,.6]});k.cylB(g,0,y,0,o.top||.07,o.r||.22,.2,shadeM,true);k.sph(g,0,y+.04,0,.05,.05,.05,k.emissive('#fff2d0',.3,2));k.pointLight(g,0,y-.05,0,'#ffd7a0',.0,o.power||2.4,o.dist||5);return g;}
  function art(seed,colors){return function(c,w,h){c.fillStyle=colors[0];c.fillRect(0,0,w,h);for(var i=0;i<5;i++){c.fillStyle=colors[1+i%(colors.length-1)];c.beginPath();var x=(Math.sin(seed*3+i*2.1)*.35+.5)*w,y=(Math.cos(seed*5+i*1.3)*.3+.5)*h;c.ellipse(x,y,w*(.12+.06*(i%3)),h*(.08+.05*((i+seed)%3)),i,0,PI*2);c.fill();}c.fillStyle=colors[colors.length-1]+'99';c.fillRect(0,h*.72,w,h*.28);};}
