  // ---------------------------------------------------------------- building grammar
  function roof(k,g,o,w,d,h){
    var T=k.T,m=k.mat(o.roofColor||'#8a6f62',.7),rise=o.rise==null?Math.min(w,d)*.35:o.rise,ov=o.overhang==null?.35:o.overhang,type=o.roof||'gable';
    if(type==='flat'){k.bx(g,0,h,0,w+.1,.18,d+.1,k.mat(o.trim||'#efe7d8',.8));var pm=k.mat(o.trim||'#efe7d8',.8);k.bx(g,0,h+.18,d/2-.05,w+.1,.35,.1,pm);k.bx(g,0,h+.18,-d/2+.05,w+.1,.35,.1,pm);k.bx(g,w/2-.05,h+.18,0,.1,.35,d,pm);k.bx(g,-w/2+.05,h+.18,0,.1,.35,d,pm);return h+.5;}
    if(type==='hip'||type==='pyramid'){var c=k.mesh(k.keep(new T.ConeGeometry(1,1,4,1)),m,g,0,h+rise/2,0);c.rotation.y=PI/4;c.scale.set((w/2+ov)*1.414,rise,(d/2+ov)*1.414);return h+rise;}
    if(type==='curved'){var cy=k.mesh(k.keep(new T.CylinderGeometry(1,1,1,32,1,false,0,PI)),m,g,0,h,0);cy.rotation.z=PI/2;cy.rotation.y=0;cy.scale.set(rise,w+ov*2,d/2+ov);cy.rotation.set(0,0,PI/2);cy.rotation.order='ZYX';cy.rotation.x=-PI/2;return h+rise;}
    if(type==='sawtooth'){var n=Math.max(2,Math.round(w/2.2)),sw=w/n,gm=k.glass;for(var i=0;i<n;i++){var x=-w/2+sw*(i+.5),s=k.box(g,x,h+rise/2,0,sw*1.02,.08,d,m);s.rotation.z=Math.atan2(rise,sw);s.scale.x=1/Math.cos(Math.atan2(rise,sw));var gl=k.box(g,x+sw/2-.02,h+rise/2,0,.04,rise,d-.1,gm);gl.castShadow=false;}return h+rise;}
    if(type==='pagoda'){for(var t2=0;t2<(o.tiers||2);t2++){var y=h+t2*rise*.9,sc=1-t2*.28;var cone=k.mesh(k.keep(new T.ConeGeometry(1,1,4,1,true)),m,g,0,y+rise*.25,0);cone.rotation.y=PI/4;cone.scale.set((w/2+ov+.6)*1.414*sc,rise*.5,(d/2+ov+.6)*1.414*sc);if(t2<(o.tiers||2)-1)k.bx(g,0,y+rise*.4,0,w*.55*sc,rise*.5,d*.55*sc,k.mat(o.color||'#d9c7a7',.85));}k.bx(g,0,h+(o.tiers||2)*rise*.9-.2,0,.15,.6,.15,k.mat('#c8a45f',.4,.5));return h+(o.tiers||2)*rise;}
    // gable (ridge along x by default; o.along==='z' turns the gable to the street)
    var alongX=o.along!=='z',span=alongX?d:w,len=(alongX?w:d)+ov*2,half=span/2+ov,slope=Math.atan2(rise,span/2),sl=Math.hypot(half,half*rise/(span/2));
    [-1,1].forEach(function(sd){var b=alongX?k.box(g,0,h+rise/2,sd*half/2,len,.14,sl,m,.02):k.box(g,sd*half/2,h+rise/2,0,sl,.14,len,m,.02);if(alongX)b.rotation.x=sd*slope;else b.rotation.z=-sd*slope;});
    var shape=new T.Shape();shape.moveTo(-span/2,0);shape.lineTo(span/2,0);shape.lineTo(0,rise);shape.lineTo(-span/2,0);var geo=k.keep(new T.ExtrudeGeometry(shape,{depth:.08,bevelEnabled:false})),wm=k.mat(o.color||'#e9dfcf',.9);
    [0,1].forEach(function(e){var tri=k.mesh(geo,wm,g,0,h,0);if(alongX){tri.rotation.y=PI/2;tri.position.set(e?w/2-.08:-w/2,h,0);}else{tri.position.set(0,h,e?d/2-.08:-d/2);}});
    if(o.gableWindow&&!alongX){var gw=k.cyl(g,0,h+rise*.42,d/2+.01,Math.min(.45,rise*.22),Math.min(.45,rise*.22),.04,litWin(k));gw.rotation.x=PI/2;k.tor(g,0,h+rise*.42,d/2+.03,Math.min(.45,rise*.22),.05,k.mat(o.trim||'#f6efe2',.7));}
    if(o.chimney)k.bx(g,w*.25,h+rise*.3,-d*.1,.5,rise*.9,.5,k.mat('#a5786a',.9));
    return h+rise;
  }
  function windowAt(k,g,x,y,z,w,h,o,ry){
    var wg=k.group(g,x,y,z);if(ry)wg.rotation.y=ry;var fm=k.mat(o.frame||'#f6efe2',.6);
    if(o.arch){var a=k.cyl(wg,0,h/2,.01,w/2,w/2,.02,litWin(k),false,20);a.rotation.x=PI/2;a.scale.z=1;k.box(wg,0,0,.01,w,h,.02,litWin(k)).castShadow=false;var t=k.tor(wg,0,h/2,.04,w/2+.03,.04,fm,PI);t.castShadow=false;}
    else k.box(wg,0,0,.01,w,h,.02,o.mat||litWin(k)).castShadow=false;
    var f=k.batch(wg,fm);f.box(-w/2-.03,0,.04,.06,h+.06,.06).box(w/2+.03,0,.04,.06,h+.06,.06).box(0,-h/2-.05,.07,w+.16,.06,.12);if(!o.arch)f.box(0,h/2+.03,.04,w+.12,.06,.06);if(o.mullion!==false){f.box(0,0,.04,.035,h,.035);if(h>.9)f.box(0,h*.15,.04,w,.035,.035);}f.done();
    if(o.shutters){var sm=k.mat(o.shutters,.8);[-1,1].forEach(function(s){k.box(wg,s*(w/2+.2),0,.04,.26,h,.03,sm,.01).castShadow=false;});}
    if(o.box){k.bx(wg,0,-h/2-.22,.18,w+.1,.16,.2,k.mat('#a7835f',.8),.02);for(var i=0;i<6;i++)k.sph(wg,-w/2+.1+i*(w-.2)/5,-h/2-.04,.18,.06,.05,.06,k.mat(['#e8857a','#f7e2a4','#f2c9d2','#ffffff'][i%4],.7));}
    return wg;
  }
  // o: {x,z,w,d,h,floors,color,trim,base, roof...,cols,winW,winH,arch,shutters,door:{w,h,color,arch,glass},sideCols,boxes,balcony,awning:{color,stripe},sign:{text,..},name,id}
  function aoSkirt(k,p,w,d,y){var t=cachedTex(k,'ao_skirt',function(c,cw,ch){c.clearRect(0,0,cw,ch);c.shadowColor='rgba(30,26,34,.55)';c.shadowBlur=26;c.fillStyle='rgba(30,26,34,.55)';c.fillRect(40,40,cw-80,ch-80);},256,256);
    var m=k._aoMat||(k._aoMat=k.material('#ffffff',1,{map:t,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2}));var pl=k.mesh(k.keep(new k.T.PlaneGeometry(w*1.32+.9,d*1.32+.9)),m,p,0,y||.008,0,false);pl.rotation.x=-PI/2;pl.raycast=noop;pl.castShadow=false;pl.renderOrder=1;pl.userData.decal=true;return pl;}
  function building(k,o){
    var g=k.prop(null,o.id||('bld_'+Math.round(o.x*10)+'_'+Math.round(o.z*10)),o.name||'建筑');g.position.set(o.x,0,o.z);if(o.ry)g.rotation.y=o.ry;
    var w=o.w,d=o.d,h=o.h,fl=o.floors||Math.max(1,Math.round(h/3)),fh=h/fl,wall=k.mat(o.color||'#e9dfcf',.9),trim=k.mat(o.trim||'#f6efe2',.75);
    k.bx(g,0,0,0,w,h,d,wall);k.bx(g,0,0,0,w+.06,.45,d+.06,k.mat(o.base||'#b9ad9a',.95));aoSkirt(k,g,w,d);
    if(h>3.5&&!o.noPipe){var pm=k._pipeMat||(k._pipeMat=k.mat('#8f9496',.5,.4)),px=(o.x*7%2>1?-1:1)*(w/2-.12);k.cylB(g,px,.1,d/2+.07,.045,.045,h-.25,pm);k.bx(g,px,h-.2,d/2+.02,.16,.1,.14,pm,.02);for(var bI=1;bI<fl;bI++)k.bx(g,px,bI*fh,d/2+.04,.07,.04,.07,pm);k.bx(g,px+(px>0?.06:-.06),.1,d/2+.12,.18,.05,.14,pm,.02);}
    if(o.roof==='flat'&&w>3){var ru=k.group(g,-w*.2,h+.25,-d*.15),um=k.mat('#d6d6d0',.6,.2);k.bx(ru,0,0,0,.9,.55,.6,um,.04);var fan=k.cyl(ru,0,.3,.31,.2,.2,.02,k.mat('#4c4f52',.6));fan.rotation.x=PI/2;k.cylB(g,w*.25,h+.25,d*.1,.12,.12,.5,um);k.cyl(g,w*.25,h+.82,d*.1,.18,.18,.06,um);}
    for(var f=1;f<fl;f++)k.bx(g,0,f*fh-.06,0,w+.05,.12,d+.05,trim);
    var top=roof(k,g,o,w,d,h);
    var cols=o.cols==null?Math.max(1,Math.floor(w/1.6)):o.cols,ww=o.winW||Math.min(1.0,w/cols*.55),wh=o.winH||Math.min(1.5,fh*.5);
    for(var fi=0;fi<fl;fi++){for(var c=0;c<cols;c++){var x=-w/2+w*(c+.5)/cols;if(fi===0&&o.door&&Math.abs(x-(o.door.x||0))<(o.door.w||1.2)/2+ww/2+.1)continue;if(fi===0&&o.groundFront)continue;
      windowAt(k,g,x,fi*fh+fh*.52,d/2,ww,fi===0&&o.tallGround?fh*.72:wh,{arch:o.arch&&(fi===0||o.archAll),shutters:o.shutters,box:o.boxes&&fi>0,frame:o.frame});}
      var sc=o.sideCols==null?Math.max(1,Math.floor(d/2.2)):o.sideCols;for(var s2=0;s2<sc;s2++)windowAt(k,g,w/2,fi*fh+fh*.52,-d/2+d*(s2+.5)/sc,ww*.9,wh,{shutters:o.shutters,frame:o.frame},PI/2);}
    if(o.door){var dw=o.door.w||1.2,dh=o.door.h||2.3,dx=o.door.x||0,dg=k.group(g,dx,0,d/2);var dm=o.door.glass?k.glass:k.mat(o.door.color||'#7d8f78',.55);k.bx(dg,0,.45,.03,dw,dh-.45,.06,o.door.glass?litWin(k):dm,.01);if(o.door.glass){var gp=k.bx(dg,0,.45,.07,dw,dh-.45,.01,k.glass);gp.castShadow=false;}var df=k.batch(dg,trim);df.box(-dw/2-.05,dh/2,.06,.1,dh,.1).box(dw/2+.05,dh/2,.06,.1,dh,.1).box(0,dh+.05,.06,dw+.2,.1,.1);if(o.door.glass||dw>1.4)df.box(0,dh/2+.2,.08,.04,dh-.5,.04);df.done();if(o.door.arch){var ar=k.tor(dg,0,dh,.06,dw/2+.05,.06,trim,PI);ar.castShadow=false;k.cyl(dg,0,dh,.03,dw/2,dw/2,.04,litWin(k),false,20).rotation.x=PI/2;}k.sph(dg,dw/2-.15,1.15,.1,.04,.04,.04,k.brass);k.bx(dg,0,0,.45,dw+.6,.18,.6,k.mat(o.base||'#b9ad9a',.95),.02);}
    if(o.awning){var aw=o.awning,ag=k.group(g,aw.x||0,aw.y||Math.min(2.75,fh*.92),d/2);var at=k.canvasTexture(function(cv,cw,ch){for(var i=0;i<12;i++){cv.fillStyle=i%2?(aw.stripe||'#f6efe2'):(aw.color||'#a8b89d');cv.fillRect(i*cw/12,0,cw/12,ch);}if(aw.scallop){cv.fillStyle='rgba(0,0,0,0)';}},256,64);var am=k.material('#ffffff',.85,{map:at,side:k.T.DoubleSide});var ab=k.box(ag,0,0,.6,aw.w||w*.9,.04,1.25,am,.01);ab.rotation.x=.35;if(aw.scallop){for(var sI=0;sI<Math.round((aw.w||w*.9)/.3);sI++){var sx=-(aw.w||w*.9)/2+.15+sI*.3,sp=k.cyl(ag,sx,-.24,1.18,.15,.15,.02,k.mat(sI%2?(aw.stripe||'#f6efe2'):(aw.color||'#a8b89d'),.85),false,16);sp.rotation.x=PI/2;sp.scale.set(1,1,1);}}}
    if(o.sign){var sg=o.sign;signBoard(k,g,sg.x||0,sg.y||Math.min(h-.4,fh*.95+.35),d/2+.08,sg.w||Math.min(3.2,w*.6),sg.h||.6,sg.text,sg);}
    if(o.balcony){for(var b=1;b<fl;b++){var by=b*fh,bm=k.mat(o.balconyColor||'#8d6e57',.8);k.bx(g,0,by,d/2+.45,w*.92,.1,.9,bm);var rl=k.batch(g,bm);for(var x2=-w*.46;x2<=w*.46;x2+=.18)rl.box(x2,by+.5,d/2+.88,.04,.8,.04);rl.box(0,by+.92,d/2+.88,w*.92,.06,.08);rl.done();}}
    g.userData.top=top;return g;
  }
