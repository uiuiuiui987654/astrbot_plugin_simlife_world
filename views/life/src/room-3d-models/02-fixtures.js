  // ------------------------------------------------------------------ fixtures (props)
  var fixtures={
    counter:function(k,g,s){cabinet(k,g,s.L,s.Dd,s.H,{door:.5});},
    ledge:function(k,g,s){k.bx(g,0,0,0,s.L,s.H,s.Dd,k.mat('#e8e2d6',.4),.015);},
    bench:function(k,g,s){k.legs(g,s.L,s.Dd,s.H-.06,.05,k.darkWood,.02);k.bx(g,0,s.H-.07,0,s.L,.04,s.Dd,k.walnut,.01);k.mesh(k.pillow(s.L-.04,.06,s.Dd-.03),k.fabric('#c8abc2'),k.group(g),0,s.H-.01,0);},
    chair:function(k,g,s){chair(k,g,s.L,s.Dd,{seat:s.H*.98});},
    nightstand:function(k,g,s){var L=s.L,D=s.Dd,h=s.H;k.legs(g,L,D,.09,.07);k.bx(g,0,.09,0,L,h-.11,D,k.wood,.02);k.bx(g,0,h-.03,0,L+.03,.04,D+.03,k.cream,.01);[.21,.42].forEach(function(y){k.box(g,0,y,D/2+.012,L-.07,.18,.035,k.wood,.012);k.sph(g,0,y,D/2+.04,.02,.02,.016,k.brass);});},
    record_console:function(k,g,s){var L=s.L,D=s.Dd,H=s.H;k.legs(g,L,D,.16,.06);k.bx(g,0,.16,0,L,H-.16,D,k.walnut,.02);k.bx(g,0,.2,D/2-.12,L-.08,H-.28,.25,k.black);var cols=['#c8786a','#5f7e9b','#e3c27a','#7d9a74','#a86d8b','#e9e1d1','#3b3b46'];for(var i=0;i<16;i++)k.bx(g,-L/2+.08+i*(L-.16)/16,.2,D/2-.13,.018,.26+(i%3)*.01,.22,k.mat(cols[i%cols.length],.7));k.bx(g,0,H-.03,0,L+.02,.03,D+.02,k.walnut,.008);},
    aquarium_console:function(k,g,s){cabinet(k,g,s.L,s.Dd,s.H,{body:k.walnut,front:k.walnut,door:.4,top:k.black});},
    media_console:function(k,g,s){var L=s.L,D=s.Dd,H=s.H;k.legs(g,L,D,.12,.08,k.darkWood,.02);k.bx(g,0,.12,0,L,H-.12,D,k.wood,.02);for(var i=0;i<3;i++){var x=-L/2+L/6+i*L/3;k.bx(g,x,.15,D/2+.006,L/3-.03,H-.2,.012,k.cane,.004);k.sph(g,x+(L/6-.06)*(i===1?1:i?-1:1),.15+(H-.2)/2,D/2+.02,.015,.015,.012,k.brass);}},
    piano_bench:function(k,g,s){k.legs(g,s.L,s.Dd,s.H-.06,.04,k.blackGloss,.02);k.bx(g,0,s.H-.07,0,s.L,.05,s.Dd,k.blackGloss,.01);k.mesh(k.pillow(s.L-.04,.05,s.Dd-.02),k.fabric('#8a6f7c'),g,0,s.H-.005,0);},
    vanity_counter:function(k,g,s){var L=s.L,D=s.Dd,H=s.H,stone=k.mat('#f1ede4',.25);cabinet(k,g,L,D,H,{front:k.lightWood,top:stone,door:.4});
      k.cylB(g,0,H,.03,.22,.2,.08,k.porcelain).scale.set(1,1,.75);k.cylB(g,0,H+.075,.03,.19,.19,.008,k.mat('#d6e3e2',.1)).scale.set(1,1,.72);
      k.cylB(g,0,H,-D/2+.1,.016,.016,.22,k.chrome);var sp=k.cyl(g,0,H+.22,-D/2+.16,.012,.012,.12,k.chrome);sp.rotation.x=PI/2;
      var fr=k.group(g,0,H+.62,-D/2+.02);k.box(fr,0,0,0,.86,.72,.03,k.lightWood,.02);k.mirror(k.box(fr,0,0,.017,.76,.62,.004,k.material('#ffffff',.04,{metalness:1})));
      k.cylB(g,.35,H,-.05,.03,.03,.12,k.mat('#c7dccd',.3));k.cylB(g,.35,H+.12,-.05,.008,.008,.03,k.chrome);},
    bath_ledge:function(k,g,s){k.bx(g,0,0,0,s.L,s.H,s.Dd,k.mat('#e8e2d6',.35),.015);},
    kitchen_north:function(k,g,s){kitchenRun(k,g,s,true);},
    kitchen_right:function(k,g,s){kitchenRun(k,g,s,false);},
    sink:function(k,g,s){var L=s.L,D=s.Dd,H=s.H;k.bx(g,0,H-.03,0,L-.04,.035,D-.04,k.steel,.01);k.bx(g,0,H-.02,0,L-.14,.03,D-.12,k.mat('#8e9598',.3,.6),.01);k.cylB(g,0,H,-D/2+.05,.018,.018,.32,k.chrome);var arc=k.tor(g,0,H+.32,-D/2+.13,.08,.012,k.chrome,PI);arc.rotation.y=PI/2;k.cylB(g,.1,H,-D/2+.05,.012,.012,.08,k.chrome);},
    weights_rack:function(k,g,s){var L=s.L,D=s.Dd,H=s.H,m=k.mat('#3c3f44',.5,.4);[-1,1].forEach(function(x){[-1,1].forEach(function(z){k.bx(g,x*(L/2-.03),0,z*(D/2-.04),.04,H,.04,m,.008);});});k.bx(g,0,H-.03,0,L,.03,D,m,.006);var t=k.box(g,0,H*.5,0,L-.04,.03,D-.06,m,.006);t.rotation.x=.18;k.bx(g,0,.02,0,L,.03,D,m);},
    clothes:function(k,g,s){clothesRail(k,g,s);},
    desk_chair:function(k,g,s){officeChair(k,g,s,'#6f8a80');},
    art_chair:function(k,g,s){var H=Math.min(s.H,.46);k.cylB(g,0,0,0,.2,.22,.03,k.darkWood);k.cylB(g,0,0,0,.025,.025,H-.04,k.chrome);k.cylB(g,0,H*.4,0,.16,.16,.012,k.chrome,true);k.cylB(g,0,H-.05,0,.19,.18,.05,k.walnut);var bk=k.box(g,0,H+.22,-.17,.34,.24,.03,k.walnut,.01);bk.rotation.x=.12;[-1,1].forEach(function(sd){k.bx(g,sd*.14,H-.02,-.16,.025,.24,.025,k.chrome);});},
    art_workbench:function(k,g,s){var L=s.L,D=s.Dd,H=s.H;k.legs(g,L,D,H-.04,.06,k.wood,.03);k.bx(g,0,H-.04,0,L,.04,D,k.lightWood,.01);k.bx(g,-L/2+.3,H-.3,0,.5,.22,D-.1,k.wood,.01);k.bx(g,-L/2+.3,H-.2,D/2-.04,.44,.08,.012,k.cream,.004);k.bx(g,L*.25,H,-.05,.5,.003,.36,k.mat('#f6f1e6',.9));for(var i=0;i<5;i++){var p=k.cylB(g,L*.05+i*.03,H,D*.25,.006,.006,.16,k.mat(['#c8786a','#5f7e9b','#e3c27a','#7d9a74','#a86d8b'][i],.5));p.rotation.z=(i-2)*.12;}},
    popcorn_console:function(k,g,s){cabinet(k,g,s.L,s.Dd,s.H,{body:k.mat('#6a4f6c',.6),front:k.mat('#7e6280',.55),top:k.walnut,door:.36});},
    hall_shelf:function(k,g,s){var L=s.L,D=s.Dd,H=s.H;k.legs(g,L,D,H-.04,.04,k.darkWood,.018);k.bx(g,0,H-.04,0,L,.04,D,k.wood,.01);k.bx(g,0,.18,0,L-.06,.025,D-.06,k.wood,.006);k.bx(g,0,.205,0,L*.5,.12,D*.6,k.basket,.02);}
  };
  // 1F 玄关: the flight UP to the 2F 楼梯厅 (same plan rect as the 2F stairwell). Rises west -> east against the north wall,
  // closed underneath with a panelled side, wood treads, a wall rail and a newel + handrail + balusters on the open south side.
  fixtures.stair_flight=function(k,g,s){var L=s.L,D=s.Dd,Ht=Math.max(2.6,(k.H||3)),n=16,rise=Ht/n,run=L/n,x0=-L/2,z0=-D/2,zs=D/2;
    var body=k.batch(g,k.cream),tr=k.batch(g,k.wood);
    for(var i=0;i<n;i++){var x=x0+i*run,top=(i+1)*rise;body.box(x+run/2,top/2,0,run,top,D);tr.box(x+run/2+.01,top+.012,.01,run+.03,.024,D+.02,.004);}
    body.done();tr.done();
    // panelled stringer on the open side
    var T=k.T,sh=new T.Shape();sh.moveTo(x0,0);for(var j=0;j<n;j++){sh.lineTo(x0+j*run,(j+1)*rise);sh.lineTo(x0+(j+1)*run,(j+1)*rise);}sh.lineTo(-x0,0);sh.lineTo(x0,0);
    var sm=k.mesh(k.keep(new T.ExtrudeGeometry(sh,{depth:.03,bevelEnabled:false})),k.mat('#efe6d6',.8),g,0,0,zs+.001);sm.castShadow=true;
    for(var p=1;p<4;p++){var px=x0+p*L/4;k.box(g,px,p*Ht/8,zs+.035,.03,p*Ht/4-.2,.01,k.mat('#c9b49a',.8));}
    // balusters + sloped handrail + newel post
    var slope=Math.atan2(Ht,L),hl=Math.hypot(L,Ht),ry=.92,bb=k.batch(g,k.walnut);
    for(var b=0;b<n;b++){var bx=x0+(b+.5)*run,by=(b+1)*rise;bb.box(bx,by+ry/2,zs-.05,.035,ry,.035);}bb.done();
    var hr=k.box(g,0,Ht/2+ry+.02,zs-.05,hl,.06,.08,k.walnut,.02);hr.rotation.z=slope;
    k.box(g,x0+.06,(rise+ry+.15)/2,zs-.05,.1,rise+ry+.15,.1,k.walnut,.02);k.sph(g,x0+.06,rise+ry+.17,zs-.05,.065,.065,.065,k.walnut);
    var wr=k.box(g,0,Ht/2+.9,z0+.04,hl,.04,.04,k.brass,.01);wr.rotation.z=slope;
    // landing light at the top of the flight
    var lp=k.box(g,-x0-.4,Ht-.25,z0+.03,.22,.08,.04,k.emissive('#fff0cf',.3,1.4),.02);lp.castShadow=false;};
  fixtures.basin=fixtures.vanity_counter;fixtures.kitchen_sink=fixtures.sink;fixtures.clothes_rail=fixtures.clothes;
  fixtures.kitchen_chair=function(k,g,s){chair(k,g,s.L,s.Dd,{seat:.45,color:'#e3d6b4'});};
  ['dining_chair_l1','dining_chair_l2','dining_chair_r1','dining_chair_r2'].forEach(function(id){fixtures[id]=function(k,g,s){chair(k,g,s.L,s.Dd,{seat:.46,color:'#b6c4a1',wood:k.walnut});};});
  function insetRanges(k,f){var M=root.RoomModel,cx=f.x+f.w/2,cz=f.y+f.d/2,out=[];Object.keys(M.plan).forEach(function(id){var p=M.plan[id];if(p[4]!==f.id||!/oven|dishwasher/.test(id))return;var a,b;if(f.facing==='W'){a=(p[1]-cz)/50;b=(p[1]+p[3]-cz)/50;}else if(f.facing==='E'){a=-(p[1]+p[3]-cz)/50;b=-(p[1]-cz)/50;}else{a=(p[0]-cx)/50;b=(p[0]+p[2]-cx)/50;}out.push([a,b]);});return out;}
  function kitchenRun(k,g,s,north){
    var f=s.fixture,L=s.L,D=s.Dd,H=s.H,gaps=insetRanges(k,f),door=k.mat('#e6ead9',.55),stone=k.mat('#efebe2',.3);
    cabinet(k,g,L,D,H,{body:door,front:k.mat('#d9e0c9',.6),top:stone,gaps:gaps,door:.5});
    // backsplash + upper cabinets (kept clear of the window and the hob)
    var win=(rooms[k.room]||{}).windows||[],clear=[];if(north)win.forEach(function(w){clear.push([(w[0]-(f.x+f.w/2))/50-.1,(w[1]-(f.x+f.w/2))/50+.1]);});else gaps.forEach(function(r,i){if(i===0)clear.push([r[0]-.05,r[1]+.05]);});
    k.bx(g,0,H,-D/2+.01,L,.5,.02,k.mat('#f4f1e9',.3),.004);
    var ux=[],segs=spans(L,clear.map(function(c){return {u0:c[0]+L/2,u1:c[1]+L/2,y0:0,y1:3};}),1,0,L);segs.forEach(function(sg){var a=sg[0]-L/2,b=sg[1]-L/2;if(b-a<.3)return;k.bx(g,(a+b)/2,1.48,-D/2+.18,b-a,.7,.34,door,.015);var n=Math.max(1,Math.round((b-a)/.5));for(var i=0;i<n;i++){var x=a+(b-a)*(i+.5)/n;k.bx(g,x,1.5,-D/2+.355,(b-a)/n-.02,.66,.012,k.mat('#d9e0c9',.6),.005);k.bx(g,x,1.56,-D/2+.37,.12,.014,.014,k.brass,.004);}});
    if(!north&&gaps.length){var r=gaps[0],cx=(r[0]+r[1])/2;k.bx(g,cx,1.6,-D/2+.22,r[1]-r[0]+.06,.12,.42,k.steel,.01);var hood=k.cylB(g,cx,1.72,-D/2+.16,.12,.2,.5,k.steel,false,4);hood.rotation.y=PI/4;}
  }
  function clothesRail(k,g,s){
    var L=s.L,D=s.Dd,H=s.H,m=k.brass;[-1,1].forEach(function(x){k.cylB(g,x*(L/2-.03),0,0,.018,.018,H,m);k.bx(g,x*(L/2-.03),0,0,.06,.03,D,k.darkWood,.008);});
    var bar=k.cyl(g,0,H-.06,0,.014,.014,L-.04,m);bar.rotation.z=PI/2;k.bx(g,0,.14,0,L-.1,.025,D-.06,k.wood,.006);
    var cols=['#f5e8cd','#c8abc2','#a8b89d','#e9d7d0','#7d8fa8','#f2efe8','#d7b98d','#b8a1c9','#91a68b'];
    for(var i=0;i<9;i++){var x=-L/2+.18+i*(L-.36)/8,len=.62+((i*7)%4)*.12;k.tor(g,x,H-.1,0,.05,.004,k.chrome,PI).rotation.set(0,PI/2,0);k.bx(g,x,H-.12-len,0,.05,len,.4,k.fabric(cols[i]),.02);}
    for(var j=0;j<3;j++){k.bx(g,-L/2+.3+j*.4,.165,-.06,.1,.06,.22,k.mat(['#e9d7d0','#7d6a5a','#f4f0e8'][j],.5),.02);k.bx(g,-L/2+.42+j*.4,.165,-.06,.1,.06,.22,k.mat(['#e9d7d0','#7d6a5a','#f4f0e8'][j],.5),.02);}
  }
  function officeChair(k,g,s,color){
    var H=Math.min(s.H,.47),f=k.fabric(color);for(var i=0;i<5;i++){var a=i*PI*2/5,leg=k.box(g,Math.sin(a)*.14,.05,Math.cos(a)*.14,.04,.03,.3,k.black,.008);leg.rotation.y=a;k.sph(g,Math.sin(a)*.28,.03,Math.cos(a)*.28,.03,.03,.03,k.black);}
    k.cylB(g,0,.05,0,.028,.028,H-.12,k.chrome);k.mesh(k.pillow(.5,.09,.48),f,g,0,H-.02,0);k.bx(g,0,H-.09,0,.42,.04,.4,k.black,.01);
    k.bx(g,0,H+.02,-.24,.06,.18,.03,k.black,.008);var back=k.mesh(k.pillow(.46,.07,.5),f,g,0,H+.36,-.26);back.rotation.x=1.45;
    [-1,1].forEach(function(x){k.bx(g,x*.26,H,-.02,.03,.18,.03,k.black,.008);k.bx(g,x*.26,H+.18,-.02,.06,.03,.28,k.black,.01);});
  }
