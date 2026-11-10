  // ---------------------------------------------------------------- public: spec + build
  var cache={};
  function supports(key,view){return view==='indoor'?!!INTERIOR_OF[key]:!!STREET[key];}
  var JDIMS={walk:[20,12],cycle:[20,12],bus:[12,8],car:[10,8],rail:[14,8]};
  function spec(key,view,mode){
    if(view==='indoor'){var I=IN[INTERIOR_OF[key]];if(!I)return null;return {W:I.W,D:I.D,H:I.H||3.2,outdoor:!!I.outdoor,dark:!!I.dark,theme:I.theme,floor:I.floor,walls:I.walls,anchor:I.anchor,camera:I.camera||null,interior:true};}
    var dims={cafe:[20,16],bookstore:[18,15],museum:[22,16],cinema:[20,15],mall:[26,17],office:[22,16],street:[20,18],food:[20,15],supermarket:[24,17],grocery:[16,13],market:[20,16],nightmarket:[20,16],station:[26,17],airport:[34,24],hotel:[22,16],travel:[22,17],temple:[20,20],onsen:[18,16],harbor:[26,20],mountain:[22,18],izakaya:[18,14],transit:[22,16],generic:[24,18],park:[22,18],beach:[24,20],botanical:[22,17],riverside:[24,18],lakeside:[24,18],campsite:[22,18],amusement:[26,19],flower_shop:[18,14],bakery:[18,14],library:[24,18]}[key]||[20,16];if(key==='transit'&&JDIMS[mode])dims=JDIMS[mode];
    return {W:dims[0],D:dims[1],H:3,outdoor:true,dark:false,theme:{wall:'#ede4d2',side:'#b8c5a5',floor:'#c8af8c'},floor:'none',walls:null,interior:false};}
  function build(k,ctx){
    var key=ctx.key,view=ctx.view;
    if(view==='indoor'){var I=IN[INTERIOR_OF[key]];if(I.outdoor){var w=stageIndoorOutdoor(k,ctx);}I.build(k,I,ctx);finishWorld(k);return {anchor:I.anchor,camera:I.camera};}
    var r=STREET[key](k,ctx);if(!(key==='transit'&&JOURNEY[ctx.mode])){streetLife(k,ctx);groundDetail(k);}finishWorld(k);return r;
  }
  function groundDetail(k){var trees=(k._trees||[]).filter(function(t){return t.y===0&&t.kind!=='palm'&&t.kind!=='bamboo';});if(!trees.length)return;var gr=k._ground,hard=/paving|cobble|tile|deck|asphalt/.test(gr),T=k.T;
    if(hard){var gt=cachedTex(k,'tree_grate',function(c,w,h){c.fillStyle='#3e3a36';c.fillRect(0,0,w,h);c.strokeStyle='#5b5650';c.lineWidth=3;for(var r=14;r<w/2;r+=9){c.beginPath();c.arc(w/2,h/2,r,0,PI*2);c.stroke();}c.lineWidth=4;for(var a=0;a<8;a++){c.beginPath();c.moveTo(w/2+Math.cos(a*PI/4)*14,h/2+Math.sin(a*PI/4)*14);c.lineTo(w/2+Math.cos(a*PI/4)*w,h/2+Math.sin(a*PI/4)*w);c.stroke();}c.fillStyle='#6b5a49';c.beginPath();c.arc(w/2,h/2,13,0,PI*2);c.fill();c.strokeStyle='#8f8a82';c.lineWidth=6;c.strokeRect(3,3,w-6,h-6);},128,128);
      var gm=k.material('#ffffff',.6,{map:gt,metalness:.3,polygonOffset:true,polygonOffsetFactor:-1});trees.forEach(function(t){var pl=k.mesh(k.keep(new T.PlaneGeometry(1.3,1.3)),gm,null,t.x,.006,t.z,false);pl.rotation.x=-PI/2;pl.raycast=noop;pl.receiveShadow=true;});return;}
    if(!/grass|dirt|gravel/.test(gr))return;var n=trees.length*22,geo=k.keep(new T.ConeGeometry(.04,.18,4)),inst=new T.InstancedMesh(geo,k.mat('#ffffff',.9),n),m4=new T.Matrix4(),q=new T.Quaternion(),e=new T.Euler(),v=new T.Vector3(),sc=new T.Vector3(),c=new T.Color(),cols=['#8fb27d','#a3c08a','#7fa56f','#b5c98f'],r=rng(trees.length*131+7),i=0;
    trees.forEach(function(t){for(var j=0;j<22;j++){var a=r()*PI*2,d=.35+r()*1.1;e.set((r()-.5)*.5,r()*PI,(r()-.5)*.5);q.setFromEuler(e);var s2=.6+r()*.9;sc.set(s2,s2*(.7+r()*.8),s2);v.set(t.x+Math.cos(a)*d,.09*sc.y,t.z+Math.sin(a)*d);m4.compose(v,q,sc);inst.setMatrixAt(i,m4);inst.setColorAt(i,c.set(cols[Math.floor(r()*4)]));i++;}});
    inst.castShadow=false;inst.receiveShadow=true;inst.raycast=noop;inst.instanceMatrix.needsUpdate=true;k.scene.add(inst);
    trees.forEach(function(t,ti){if(ti%2===0)P.flowers(k,t.x-1,t.x+1,t.z+.4,t.z+1.2,7,.001);});}
  function streetLife(k,ctx){var road=(k._roads||[])[0],W=ctx.W,wetEnv=k.env&&/rain|storm/.test(k.env.weather||''),umb=['#7fa59b','#c8786a','#5f7e9b','#e3c27a'];
    if(road){
      // every vehicle on the carriageway drives: one lane each way, equal speed per lane and spaced by body length so nothing overlaps
      var x0=-18,x1=W+18,span=x1-x0,RS=.82,lanes=[{z:road[0]+(road[1]-road[0])*.25,dir:-1,v:-5.2,cars:[]},{z:road[0]+(road[1]-road[0])*.75,dir:1,v:6.4,cars:[]}],cols=['#a9bcc9','#e8c3b9','#e9e2d2','#c9d6b8','#5f7e9b','#c8786a','#3b3b46'],kinds=['sedan','suv','hatch','taxi','van','pickup','truck','sedan','sports','jeep','wagon','suv'];
      k.scene.children.slice().forEach(function(c){var u=c.userData||{};if(u.vehicle&&c.position.z>road[0]-.6&&c.position.z<road[1]+.6){var ln=Math.abs(c.position.z-lanes[0].z)<Math.abs(c.position.z-lanes[1].z)?lanes[0]:lanes[1];ln.cars.push(c);}});
      lanes.forEach(function(ln,li){var want=li?4:3,need=function(a,b){return (a.userData.len+b.userData.len)*RS/2+2.4;};
        ln.cars.sort(function(a,b){return a.position.x-b.position.x;});for(var i=1;i<ln.cars.length;i++){var pa=ln.cars[i-1],pb=ln.cars[i];if(pb.position.x-pa.position.x<need(pa,pb))pb.position.x=pa.position.x+need(pa,pb);}
        var n=0;while(ln.cars.length<want&&n++<12){var xs=ln.cars.map(function(c){return c.position.x;}).sort(function(a,b){return a-b;}),best=null,gap=0;if(!xs.length){best=x0+span*(.2+li*.3);}else for(var j=0;j<xs.length;j++){var a=xs[j],b=j+1<xs.length?xs[j+1]:xs[0]+span,g=b-a;if(g>gap){gap=g;best=a+g/2;}}
          if(xs.length&&gap<13)break;var kind=kinds[(ln.cars.length*3+li*2+Math.round(W))%kinds.length],cx=best>x1?best-span:best,car=P.vehicle(k,kind,cx,ln.z,ln.dir*PI/2,cols[(ln.cars.length*2+li*3)%cols.length]);ln.cars.push(car);}
        ln.cars.forEach(function(c){c.position.z=ln.z;c.rotation.y=ln.dir*PI/2;c.scale.setScalar(RS);c.userData.propId=c.userData.propId==='bus'?'bus':'moving_car';scroller(k,c,ln.v,x0,x1);});});
      var mh=k.mat('#4c4f52',.6,.4);[[W*.3,road[0]+(road[1]-road[0])*.5],[W*.78,road[0]+(road[1]-road[0])*.3]].forEach(function(q){var m=k.cylB(null,q[0],-.001,q[1],.32,.32,.012,mh);m.receiveShadow=true;m.raycast=noop;});
}}
  function stageIndoorOutdoor(k,ctx){return stage(k,{W:ctx.W,D:ctx.D,ground:'tile',gscale:1,outer:'grass',horizon:'hills'});}
  // ---------------------------------------------------------------- animated bits (registered as a Room3D effect)
  function destinationEffect(rig){
    var k=rig.kit;if(!k||!k.destination)return null;var t=0,env=null,night=false,wet=0,cBase=null;
    return {apply:function(e,st){env=e;night=e.band==='night';wet=st&&st.wet||(e.weather==='rain'||e.weather==='storm'?1:0);var lm=st&&st.lamps!=null?st.lamps:(night?1:0);if(k._poolMat){k._poolMat.opacity=.6*Math.min(1,lm*1.4);k._poolMat.visible=lm>.02;}[['_beamMat',.55],['_headGlowMat',.9],['_tailGlowMat',.7]].forEach(function(b){var m=k[b[0]];if(m){m.opacity=b[1]*Math.min(1,lm*1.3);m.visible=lm>.02;}});},update:function(dt){t+=dt;
      (k._dwater||[]).forEach(function(w,i){w.tex.offset.x=(w.tex.offset.x+dt*.012*(i%2?1:-1))%1;w.tex.offset.y=(w.tex.offset.y+dt*.006)%1;});
      (k._dspin||[]).forEach(function(s){s.obj.rotation[s.axis]+=dt*s.speed;if(s.axis==='z')s.obj.children.forEach(function(c){if(c.userData.cab)c.rotation.z=-s.obj.rotation.z;});});
      (k._dsteam||[]).forEach(function(s){var p=(t*.4+s.ph)%1;s.obj.position.y=s.base+p*.5;s.obj.material.opacity=.3*(1-p);s.obj.scale.copy(s.s0).multiplyScalar(.8+p*.8);});
      (k._dflames||[]).forEach(function(f,i){f.scale.set(1+Math.sin(t*13+i)*.08,1+Math.sin(t*9+i*2)*.15,1+Math.cos(t*11+i)*.08);});(k._dfireLights||[]).forEach(function(l,i){l.intensity=(night?3.5:.8)*(1+Math.sin(t*15+i)*.12+Math.sin(t*7)*.08);});
      (k._dscroll||[]).forEach(function(s){var x=s.obj.position.x+s.v*dt,L=s.x1-s.x0;if(x<s.x0)x+=L;else if(x>s.x1)x-=L;s.obj.position.x=x;var wh=s.obj.userData.wheels;if(wh){var a=Math.abs(s.v*dt)/(s.obj.userData.wheelR*(s.obj.scale.x||1));for(var wi=0;wi<wh.length;wi++)wh[wi].rotation.x+=a;}});
      (k._dtscroll||[]).forEach(function(s){s.tex.offset.x=(s.tex.offset.x-s.v*dt/s.size)%1;});
      (k._dpeople||[]).forEach(function(p){if(!p.walk)return;var a=Math.sin(t*6.2+p.ph)*.45;p.legs[0].rotation.x=a;p.legs[1].rotation.x=-a;if(!p.umb)p.arms[0].rotation.x=-a*.7;p.arms[1].rotation.x=p.umb?-.5:a*.7;});
      (k._dwheels||[]).forEach(function(w){w.obj.rotation[w.axis||'z']-=w.speed*dt;});
      (k._dbob||[]).forEach(function(b){b.obj.position.y=(b.y0||0)+Math.sin(t*b.f+(b.ph||0))*b.amp+Math.sin(t*b.f*.37+1)*b.amp*.6;});
      (k._drainGlass||[]).forEach(function(r){r.obj.visible=wet>.25;if(wet>.25)r.tex.offset.y=(r.tex.offset.y+dt*.04)%1;});
      if(k.character&&k.pose&&k.pose.bob){if(cBase==null)cBase=k.character.position.y;var b=k.pose.bob,y=cBase;if(b==='walk')y+=Math.abs(Math.sin(t*5.6))*.045;else if(b==='ride')y+=Math.sin(t*3.1)*.012;else y+=(k._dbob&&k._dbob[0]?k._dbob[0].obj.position.y:0);k.character.position.y=y;}
      (k._dfoam||[]).forEach(function(f){var p=(t*.12+f.ph)%1;f.obj.position.z=f.base+p*1.6;f.obj.material.opacity=.55*(1-p);});
      return true;},dispose:function(){}};
  }
  // the house's own 1F garage room reuses this interior at the room's size (no world/sky staging)
  function garageRoom(k,ctx){IN.garage.build(k,IN.garage,Object.assign({home:true},ctx||{}));}
  root.Destination3DModels={supports:supports,spec:spec,build:build,garageRoom:garageRoom,streets:Object.keys(STREET),interiors:Object.keys(INTERIOR_OF),props:P,building:building};
  if(root.Room3DAtmosphere)root.Room3DAtmosphere.registerEffect('destination-life',destinationEffect);
})(window);
