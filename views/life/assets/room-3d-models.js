/* 由 views/life/src/room-3d-models/ 下的片段生成，请勿直接修改；改完片段后运行 python tools/build_frontend.py */
/* 3D models for Room3D (bedroom-3d.js). Every builder works in a local frame:
   origin = centre of the footprint at its support height, +x = width (L), +z = front (Dd), +y = up.
   The engine rotates the frame by the item's facing (RoomModel.facing) and places it on its support.
   Non-item objects are tagged with kit.prop(...) so they can later be made clickable (Room3D.onPropClick). */
(function(root){
  'use strict';
  var PI=Math.PI;
  var roomItems={
    车库:[],
    客厅:['sofa','tv','coffee_table','record_player','game_console','board_game','floor_lamp','yoga_mat','piano','aquarium'],
    浴室:['bathtub','shower','bath_salts','waterproof_speaker','face_mask','bath_towel'],
    厨房:['fridge','coffee_machine','pour_over','oven','toaster','dining_table','recipe_book','tea_set','rice_cooker','dishwasher'],
    餐厅:['dining_room_table','sideboard'],
    健身室:['treadmill','dumbbells','fitness_mirror'],
    阳台:['balcony_chair','plants','watering_can','wind_chime','telescope','blanket','washing_machine','iron'],
    玄关:['shoe_cabinet','umbrella','key_tray','vacuum','sewing_kit','delivery_box'],
    卧室:['bed','wardrobe','bedside_lamp','vanity_mirror','aroma_diffuser','plush','bedtime_book'],
    衣帽间:['dressing_mirror','accessory_cabinet'],
    书房:['bookshelf','desk','desk_lamp','monitor','keyboard','notebook','camera','headphones'],
    画室:['art_easel','paint_cart','digital_tablet'],
    影音室:['cinema_screen','cinema_sofa','popcorn_machine'],
    露台:['terrace_swing','flower_bed','bbq_grill'],
    楼梯厅:['stairs','storage_bench']
  };
  // Artwork types (same as SceneStudio layout) → RoomModel.height lookup.
  var types={bed:'bed',wardrobe:'cabinet',bedside_lamp:'lamp',desk_lamp:'lamp',vanity_mirror:'vanity',aroma_diffuser:'diffuser',plush:'bear',bedtime_book:'book',bathtub:'tub',shower:'shower',bath_salts:'jar',waterproof_speaker:'speaker',face_mask:'mask',bath_towel:'towel',bookshelf:'bookshelf',desk:'desk',monitor:'monitor',keyboard:'keyboard',notebook:'book',camera:'camera',headphones:'headphones',sofa:'sofa',tv:'monitor',coffee_table:'table',record_player:'record',game_console:'console',board_game:'board',floor_lamp:'floorlamp',yoga_mat:'mat',piano:'piano',aquarium:'aquarium',fridge:'fridge',coffee_machine:'coffee',pour_over:'pourover',oven:'oven',toaster:'toaster',dining_table:'dining',recipe_book:'book',tea_set:'tea',rice_cooker:'ricecooker',dishwasher:'dishwasher',balcony_chair:'rockingchair',plants:'plants',watering_can:'wateringcan',wind_chime:'chime',telescope:'telescope',blanket:'towel',washing_machine:'washer',iron:'iron',shoe_cabinet:'cabinet',umbrella:'umbrella',key_tray:'keys',vacuum:'vacuum',sewing_kit:'board',delivery_box:'box',treadmill:'treadmill',dumbbells:'weights',fitness_mirror:'mirror',art_easel:'easel',paint_cart:'paints',digital_tablet:'monitor',cinema_screen:'screen',cinema_sofa:'sofa',popcorn_machine:'popcorn',dressing_mirror:'mirror',accessory_cabinet:'jewelry',terrace_swing:'rockingchair',flower_bed:'plants',bbq_grill:'grill',stairs:'stairs',storage_bench:'cabinet',dining_room_table:'dining',sideboard:'cabinet'};
  var names={stair_flight:'楼梯',nightstand:'床头柜',record_console:'唱片柜',aquarium_console:'鱼缸柜',media_console:'电视柜',piano_bench:'琴凳',vanity_counter:'洗手台',bath_ledge:'浴缸置物台',kitchen_north:'橱柜台面',kitchen_right:'转角橱柜',kitchen_sink:'水槽',kitchen_chair:'餐椅',dining_chair_l1:'餐椅',dining_chair_l2:'餐椅',dining_chair_r1:'餐椅',dining_chair_r2:'餐椅',weights_rack:'哑铃架',clothes_rail:'挂衣架',desk_chair:'办公椅',art_workbench:'画桌',art_chair:'画凳',popcorn_console:'小吧台',hall_shelf:'玄关台',desk_lamp:'书房台灯'};
  // Height of the usable surface of items that carry other items.
  var surfaceTop={bed:.6,balcony_chair:.44,coffee_table:.46,dining_table:.76,washing_machine:.86,desk:.74,shoe_cabinet:.88};
  var palettes={'客厅':['#eee6d4','#aabda5','#c8ac85'],'卧室':['#f0e3df','#c9b9c6','#c7a88c'],'餐厅':['#eee1c6','#b6c4a1','#c8aa80'],'书房':['#e7e8d8','#a1b7ad','#bfa580'],'画室':['#f3e9d6','#ccd2b3','#d1b895'],'影音室':['#d8d0df','#918d9f','#aa968a'],'衣帽间':['#f0e6df','#c1b5b3','#c9af92'],'健身室':['#e2e9dd','#a8beb2','#bead94'],'浴室':['#e4eddf','#b4cec6','#dbe4d2'],'厨房':['#f0ead7','#b9c7aa','#d8ddc6'],'玄关':['#efe6d6','#bcc6ab','#c8ab86'],'楼梯厅':['#ede4d4','#bfb3a2','#c4a682'],'阳台':['#ebe3d3','#a9bba1','#b9a48a'],'露台':['#ebe3d3','#a9bba1','#b39d83'],'车库':['#e4e2da','#cfd2cc','#9a9c98']};
  function theme(room){var p=palettes[room]||['#eee5d1','#b8c5a5','#c8af8c'];return {wall:p[0],side:p[1],floor:p[2]};}
  // Window / door openings are given in plan x units along the north wall; y in metres.
  var rooms={
    车库:{floor:'concrete',windows:[],curtain:false},
    客厅:{windows:[[108,192,1.0,2.35]],curtain:'#cbb79c'},
    浴室:{floor:'tile',wainscot:'tile',windows:[[48,104,1.45,2.25]],curtain:false},
    厨房:{floor:'tile',wainscot:'tile',windows:[[96,168,1.36,2.3]],curtain:false},
    餐厅:{windows:[[126,236,1.0,2.35]],curtain:'#c9b98f'},
    健身室:{windows:[[84,170,1.0,2.35]],curtain:false},
    阳台:{floor:'deck',outdoor:true,windows:[[16,118,1.0,2.25]],doors:[],awning:false,ground:-.45,leftOpenings:[[1.5,2.42,0,2.15,'glass'],[.15,1.2,1.0,2.25,'window']]},
    玄关:{windows:[[262,330,1.1,2.25],[540,600,1.1,2.25]],doors:[[410,466,'entry'],[342,398]],curtain:false},
    卧室:{windows:[[50,131,1.32,2.46]],curtain:'#c5adc1'},
    衣帽间:{windows:[[62,118,1.36,2.3]],curtain:'#d3c1bd'},
    书房:{windows:[[110,192,1.1,2.35]],curtain:'#a9bcb3'},
    画室:{windows:[[104,252,.95,2.45]],curtain:false},
    影音室:{floor:'carpet',windows:[],curtain:false,dark:true},
    露台:{floor:'deck',outdoor:true,windows:[[24,150,1.0,2.25]],doors:[],ground:-3.65,leftOpenings:[[1.3,2.22,0,2.15,'glass'],[2.4,3.12,1.0,2.1,'window']]},
    楼梯厅:{windows:[[220,330,1.1,2.3]],doors:[[150,206],[650,706]],curtain:false,floorHoles:['stairs']}
  };
  // ------------------------------------------------------------------ materials
  function materials(k){
    var T=k.T;
    function tex(paint,w,h,rep){return k.canvasTexture(paint,w,h,rep);}
    k.tex={};
    k.tex.wood=tex(function(c,w,h){c.fillStyle='#c7aa85';c.fillRect(0,0,w,h);for(var i=0;i<100;i++){var y=i*h/100;c.strokeStyle=i%3?'#ae8d6630':'#f6e4bc55';c.lineWidth=.5+i%3*.3;c.beginPath();c.moveTo(0,y);c.bezierCurveTo(w*.3,y+Math.sin(i)*9,w*.68,y-8,w,y+3);c.stroke();}});
    k.tex.cloth=tex(function(c,w,h){c.fillStyle='#ffffff';c.fillRect(0,0,w,h);c.strokeStyle='#b7aeb425';c.lineWidth=.6;for(var i=0;i<w;i+=4){c.beginPath();c.moveTo(i,0);c.lineTo(i,h);c.moveTo(0,i);c.lineTo(w,i);c.stroke();}},256,256);
    k.tex.quilt=tex(function(c,w,h){c.fillStyle='#ffffff';c.fillRect(0,0,w,h);for(var i=0;i<w;i+=3){c.strokeStyle='#b9adb81c';c.beginPath();c.moveTo(i,0);c.lineTo(i,h);c.stroke();}c.strokeStyle='#8f7f9455';c.lineWidth=2;c.setLineDash([7,5]);for(var j=1;j<6;j++){c.beginPath();c.moveTo(j*w/6,0);c.lineTo(j*w/6,h);c.stroke();c.beginPath();c.moveTo(0,j*h/6);c.lineTo(w,j*h/6);c.stroke();}},512,512);
    k.tex.basket=tex(function(c,w,h){c.fillStyle='#c9a978';c.fillRect(0,0,w,h);for(var y=0;y<h;y+=8)for(var x=0;x<w;x+=16){c.fillStyle=((x/16+y/8)%2)?'#b48f5c':'#dcc092';c.fillRect(x+((y/8)%2)*8,y,12,6);}},128,128);
    k.tex.cane=tex(function(c,w,h){c.fillStyle='#e6d2ae';c.fillRect(0,0,w,h);c.strokeStyle='#b8996a';c.lineWidth=2;for(var i=-h;i<w;i+=10){c.beginPath();c.moveTo(i,0);c.lineTo(i+h,h);c.stroke();c.beginPath();c.moveTo(i+h,0);c.lineTo(i,h);c.stroke();}c.strokeStyle='#a98b5f';c.lineWidth=5;c.strokeRect(2,2,w-4,h-4);},128,256);
    k.tex.plaid=tex(function(c,w,h){c.fillStyle='#d9c9a6';c.fillRect(0,0,w,h);c.fillStyle='#a8b89d88';for(var i=0;i<w;i+=32){c.fillRect(i,0,10,h);c.fillRect(0,i,w,10);}c.fillStyle='#ffffff55';for(var j=0;j<w;j+=32){c.fillRect(j+16,0,2,h);c.fillRect(0,j+16,w,2);}},128,128);
    k.wood=k.material('#ffffff',.62,{map:k.tex.wood});k.lightWood=k.material('#f4e8d3',.62,{map:k.tex.wood});k.darkWood=k.mat('#9b7c5c',.6);k.walnut=k.material('#9a7558',.55,{map:k.tex.wood});
    k.cream=k.mat('#f6ead6',.8);k.white=k.material('#f7f1e8',.92,{map:k.tex.cloth});k.porcelain=k.mat('#fbfaf6',.18);k.paint=k.mat('#f3eee4',.55);
    k.lavender=k.material('#c2aebe',.96,{map:k.tex.cloth});k.sage=k.material('#a8b89d',.97,{map:k.tex.cloth,side:T.DoubleSide});
    k.brass=k.material('#c8ad7c',.3,{metalness:.8});k.chrome=k.material('#dde2e4',.18,{metalness:.9});k.steel=k.material('#b9bfc2',.32,{metalness:.75});k.black=k.mat('#2b2a2e',.45);k.blackGloss=k.mat('#1f1e22',.2);
    k.glass=k.material('#e3f0f0',.05,{transparent:true,opacity:.22,metalness:.1,depthWrite:false});
    k.metals=[k.brass,k.chrome,k.steel];
    k.basket=k.material('#ffffff',.9,{map:k.tex.basket});k.cane=k.material('#ffffff',.85,{map:k.tex.cane});
    var fab={};k.fabric=function(color,side){var key=color+(side?'2':'');return fab[key]||(fab[key]=k.material(color,.95,{map:k.tex.cloth,side:side?T.DoubleSide:T.FrontSide}));};
    k.leaf=k.material('#7f9f7d',.85,{side:T.DoubleSide});k.leafDark=k.material('#5f8063',.85,{side:T.DoubleSide});k.soil=k.mat('#6d5a48',1);
  }
  function floorTexture(k,kind){
    var t,th=k.theme;
    if(kind==='concrete')t=k.canvasTexture(function(c,w,h){c.fillStyle='#a3a5a1';c.fillRect(0,0,w,h);for(var i=0;i<2600;i++){c.fillStyle=['#9a9c98','#acaea9','#b3b4ae','#93958f'][i%4];c.fillRect((i*151)%w,(i*263+i*i%37)%h,2+i%3,2+i%2);}c.fillStyle='#ffffff10';c.fillRect(0,0,w,h*.5);c.strokeStyle='#7f817d';c.lineWidth=3;c.beginPath();c.moveTo(0,1);c.lineTo(w,1);c.moveTo(1,0);c.lineTo(1,h);c.stroke();},512,512,[1,1]);
    else if(kind==='tile')t=k.canvasTexture(function(c,w,h){c.fillStyle='#d5d9cf';c.fillRect(0,0,w,h);var n=4,s=w/n;for(var i=0;i<n;i++)for(var j=0;j<n;j++){c.fillStyle=['#eef0e8','#e6e9df','#f2f2ec','#e9ece3'][(i*3+j)%4];c.fillRect(i*s+3,j*s+3,s-6,s-6);}},512,512,[1,1]);
    else if(kind==='deck')t=k.canvasTexture(function(c,w,h){c.fillStyle='#6f6253';c.fillRect(0,0,w,h);var n=8,s=h/n;for(var j=0;j<n;j++){var off=(j*97)%w;for(var x=-off;x<w;x+=w*.75){c.fillStyle=['#b39d83','#a8927a','#bca78c','#ae977d'][(j+Math.round(x))%4];c.fillRect(x+2,j*s+3,w*.75-4,s-6);c.strokeStyle='#8e7a6340';for(var g=0;g<6;g++){c.beginPath();c.moveTo(x,j*s+6+g*(s-12)/6);c.lineTo(x+w*.75,j*s+8+g*(s-12)/6);c.stroke();}}}},512,512,[1,1]);
    else if(kind==='carpet')t=k.canvasTexture(function(c,w,h){c.fillStyle='#4f4762';c.fillRect(0,0,w,h);for(var i=0;i<6000;i++){c.fillStyle=i%2?'#5b5270':'#463f57';c.fillRect((i*73)%w,(i*151)%h,2,2);}},256,256,[1,1]);
    else t=k.canvasTexture(function(c,w,h){var rows=8,s=h/rows,base=['#faf3e7','#e9dfcd','#fff8ea','#eee7db'];c.fillStyle='#cdbfa9';c.fillRect(0,0,w,h);for(var j=0;j<rows;j++){var off=((j*.37)%1)*w/2.2;for(var x=-off,n=0;x<w;x+=w/2.2,n++){var col=base[(n+j*3)%4];c.fillStyle=col;c.fillRect(x+1.5,j*s+1.5,w/2.2-3,s-3);c.globalAlpha=.18;c.strokeStyle='#b79a76';for(var g=0;g<7;g++){c.beginPath();c.moveTo(x,j*s+4+g*(s-8)/7);c.bezierCurveTo(x+60,j*s+6+g*(s-8)/7+Math.sin(n+g)*3,x+140,j*s+2+g*(s-8)/7,x+w/2.2,j*s+5+g*(s-8)/7);c.stroke();}c.globalAlpha=1;}}var tint=th.floor;c.globalCompositeOperation='multiply';c.fillStyle=tint;c.globalAlpha=.85;c.fillRect(0,0,w,h);c.globalAlpha=1;c.globalCompositeOperation='source-over';},1024,1024,[1,1]);
    t.userData.size=kind==='tile'?1.2:kind==='deck'?1.6:2.2;return t;
  }
  function skyTexture(k){var env=k.env,night=k.night;return k.canvasTexture(function(c,w,h){var g=c.createLinearGradient(0,0,0,h);g.addColorStop(0,env.sky[0]);g.addColorStop(1,env.sky[1]);c.fillStyle=g;c.fillRect(0,0,w,h);c.fillStyle=night?'#f1e6bc':'#ffefbd';if(/clear|wind/.test(env.weather)){c.beginPath();c.arc(w*.75,h*.23,night?16:26,0,PI*2);c.fill();}if(night){c.fillStyle='#fff8dd';for(var s=0;s<50;s++)c.fillRect(s*97%w,s*53%(h*.5),1.5,1.5);}['#94b3a1','#6b958a','#48776d'].forEach(function(color,i){c.fillStyle=color;c.beginPath();c.moveTo(0,h);for(var j=0;j<=10;j++)c.lineTo(j*w/10,h*(.58+i*.11)+Math.sin(j*1.6+i)*h*.1);c.lineTo(w,h);c.fill();});if(/rain|storm|snow/.test(env.weather)){c.strokeStyle=env.weather==='snow'?'#ffffffcc':'#e5f0e3bb';for(var n=0;n<120;n++){var x=n*73%w,y=n*119%h;c.beginPath();c.moveTo(x,y);c.lineTo(x-(env.weather==='snow'?1:5),y+(env.weather==='snow'?3:18));c.stroke();}}},512,384);}
  function rugMaterial(k,room){
    var col={卧室:['#bcaebc','#e9dfe0'],客厅:['#d8cdb4','#a9b89d'],餐厅:['#cbbf9f','#f1e8d2'],书房:['#a9bab1','#e8eadf'],画室:['#d9c7a3','#f5ead3'],影音室:['#3e3650','#7a6e95'],健身室:['#6f8a80','#b5cabd']}[room]||['#cfc4ad','#f1e8d2'];
    var t=k.canvasTexture(function(c,w,h){c.fillStyle=col[0];c.fillRect(0,0,w,h);c.strokeStyle=col[1];c.lineWidth=3;c.strokeRect(14,14,w-28,h-28);c.lineWidth=1;c.strokeRect(22,22,w-44,h-44);if(room==='健身室'){c.strokeStyle=col[1]+'88';for(var y=30;y<h;y+=24){c.beginPath();c.moveTo(20,y);c.lineTo(w-20,y);c.stroke();}return;}for(var y2=38;y2<h-25;y2+=32)for(var x=38;x<w-25;x+=38){c.beginPath();c.moveTo(x,y2-5);c.lineTo(x+5,y2);c.lineTo(x,y2+5);c.lineTo(x-5,y2);c.closePath();c.stroke();}},512,384);
    return k.material('#ffffff',1,{map:t});
  }
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
  // ------------------------------------------------------------------ items
  var items={};
  // ---- bedroom
  items.bed=function(k,g,s){var L=s.L,D=s.Dd,mw=L-.08,BT=.6,back=-D/2,front=D/2,sheet=k.material('#fbf6ee',.95,{map:k.tex.cloth}),duvet=k.material('#cdb9cc',.95,{map:k.tex.quilt,side:k.T.DoubleSide});
    k.legs(g,L,D,.15,.1);k.box(g,0,.25,.04,L,.2,D-.08,k.wood,.04);k.box(g,0,.47,.05,mw,.22,D-.16,sheet,.07);k.box(g,0,.37,.05,mw+.008,.012,D-.15,k.cream,.004);
    k.box(g,0,.66,back+.05,L+.06,1.02,.1,k.wood,.04);k.box(g,0,.74,back+.11,L-.1,.62,.06,k.lavender,.03);
    for(var row=0;row<2;row++)for(var t=0;t<6;t++)k.sph(g,-mw*.42+t*mw*.168+(row?mw*.084:0),.62+row*.24,back+.142,.016,.016,.008,k.cream);
    [-1,1].forEach(function(sd){var pl=k.mesh(k.pillow(mw*.44,.17,.42),k.white,g,sd*mw*.235,BT+.06,back+.36);pl.rotation.x=.28;pl.rotation.y=sd*.04;});
    var cu=k.mesh(k.pillow(.42,.13,.34),k.lavender,g,.05,BT+.08,back+.6);cu.rotation.x=.55;cu.rotation.z=.06;
    var dl=front-(back+.72)-.02;k.mesh(k.drape(mw,dl,.17,.15,.05,.025),duvet,g,0,BT,back+.72+dl/2);
    var cuff=k.cyl(g,0,BT+.012,back+.72,.032,.032,mw+.07,sheet);cuff.rotation.z=PI/2;cuff.scale.set(1,1,.75);
    k.mesh(k.drape(mw+.02,.4,.2,0,.065,0),k.sage,g,0,BT+.035,front-.42);for(var st=0;st<9;st++)k.box(g,-mw/2+.15+st*(mw-.3)/8,BT+.04,front-.42,.012,.006,.36,k.cream,.002);};
  items.wardrobe=function(k,g,s){var L=s.L,D=s.Dd,fz=D/2;k.bx(g,0,0,-.01,L-.08,.12,D-.06,k.darkWood,.01);k.box(g,0,1.11,0,L,1.98,D,k.wood,.025);k.box(g,0,2.12,0,L+.06,.05,D+.05,k.cream,.012);k.box(g,0,2.165,0,L+.02,.04,D+.02,k.cream,.012);
    [-1,1].forEach(function(sd){var xx=sd*L*.247;k.box(g,xx,1.12,fz+.015,L*.475,1.86,.045,k.wood,.012);var fr=k.batch(g,k.cream);fr.box(xx,1.95,fz+.042,L*.41,.035,.012).box(xx,.29,fz+.042,L*.41,.035,.012).box(xx-L*.19,1.12,fz+.042,.035,1.66,.012).box(xx+L*.19,1.12,fz+.042,.035,1.66,.012).box(xx,1.36,fz+.042,L*.41,.025,.012);fr.done();
      var sl=k.batch(g,k.mat('#d2bb9c',.7));for(var r=0;r<7;r++){sl.box(xx-L*.15+r*L*.05,1.6,fz+.045,.012,.42,.008);sl.box(xx-L*.15+r*L*.05,.74,fz+.045,.012,.92,.008);}sl.done();k.sph(g,sd*.07,1.12,fz+.06,.022,.022,.018,k.brass);});
    k.box(g,-.38,2.32,0,.42,.26,.3,k.basket,.03);k.box(g,.12,2.29,0,.32,.2,.28,k.basket,.03);};
  items.bedside_lamp=function(k,g,s){k.cylB(g,0,0,0,.09,.11,.04,k.brass);k.sph(g,0,.12,0,.075,.09,.075,k.mat('#d9cbb9',.35));k.cylB(g,0,.2,0,.012,.012,.18,k.brass);
    var shadeM=k.material('#f4e4bd',.8,{emissive:'#ffd395',emissiveIntensity:.12,lit:[.12,.65],side:k.T.DoubleSide});k.cylB(g,0,.27,0,.11,.18,.22,shadeM,true);k.tor(g,0,.27,0,.18,.006,k.brass).rotation.x=PI/2;
    k.sph(g,0,.32,0,.04,.05,.04,k.emissive('#fff6df',.3,2)).castShadow=false;k.pointLight(g,0,.32,.05,'#ffcf8d',.25,3.2,4.5);};
  // Study desk lamp: balanced-arm architect lamp at the back-left of the desk, reaching toward the work area.
  items.desk_lamp=function(k,g,s){var T=k.T,V=function(x,y,z){return new T.Vector3(x,y,z);},body=k.material('#36574a',.38,{metalness:.45}),joint=k.mat('#22312b',.4,.5),steel=k.chrome,
      hd=V(.78,0,.62).normalize(),side=V(hd.z,0,-hd.x);
    // weighted base, brass ring, rocker switch
    k.cylB(g,0,0,0,.078,.084,.022,body);k.tor(g,0,.022,0,.07,.004,k.brass).rotation.x=Math.PI/2;k.cylB(g,0,.022,0,.03,.045,.014,body);
    k.bx(g,-.035,.03,-.035,.022,.008,.014,joint,.003);k.cylB(g,0,.036,0,.012,.012,.03,joint);
    // shoulder yoke + axle
    var J0=V(0,.07,0);[-1,1].forEach(function(sd){k.bx(g,side.x*sd*.018,.058,side.z*sd*.018,.006,.04,.03,body,.002).rotation.y=Math.atan2(hd.x,hd.z);});
    function axle(p){var c=k.cyl(g,p.x,p.y,p.z,.009,.009,.05,joint);c.quaternion.setFromUnitVectors(V(0,1,0),side);[-1,1].forEach(function(sd){k.sph(g,p.x+side.x*sd*.028,p.y,p.z+side.z*sd*.028,.012,.012,.012,steel);});}
    function arm(a,b,gap){[-1,1].forEach(function(sd){var o=side.clone().multiplyScalar(sd*gap);rod(k,g,[a.x+o.x,a.y,a.z+o.z],[b.x+o.x,b.y,b.z+o.z],.0048,body);});}
    function spring(a,b,off){var d=b.clone().sub(a),L=d.length(),u=d.clone().normalize(),n=side.clone().cross(u).normalize(),pts=[],turns=Math.round(L*90);for(var i=0;i<=turns*10;i++){var t=i/(turns*10),ang=t*turns*Math.PI*2,c=a.clone().add(d.clone().multiplyScalar(t)).add(n.clone().multiplyScalar(off));pts.push(c.add(side.clone().multiplyScalar(Math.cos(ang)*.006)).add(n.clone().multiplyScalar(Math.sin(ang)*.006)));}
      k.mesh(k.keep(new T.TubeGeometry(new T.CatmullRomCurve3(pts),turns*10,.0012,5,false)),steel,g,0,0,0);rod(k,g,a.clone().add(n.clone().multiplyScalar(off)).toArray(),a.clone().add(n.clone().multiplyScalar(off)).add(u.clone().multiplyScalar(-.03)).toArray(),.0015,steel);}
    axle(J0);
    var J1=J0.clone().add(hd.clone().multiplyScalar(.15)).add(V(0,.31,0));arm(J0,J1,.014);var sa=J0.clone().lerp(J1,.18),sb=J0.clone().lerp(J1,.62);spring(sa,sb,.018);spring(sa,sb,-.018);axle(J1);
    var J2=J1.clone().add(hd.clone().multiplyScalar(.3)).add(V(0,-.06,0));arm(J1,J2,.012);var sc=J1.clone().lerp(J2,.15),sd2=J1.clone().lerp(J2,.55);spring(sc,sd2,.016);axle(J2);
    // shade: aimed down and forward onto the desk
    var head=k.group(g,J2.x,J2.y,J2.z);head.quaternion.setFromUnitVectors(V(0,-1,0),hd.clone().multiplyScalar(.55).add(V(0,-1,0)).normalize());
    k.cylB(head,0,-.035,0,.016,.016,.035,joint);k.cylB(head,0,-.06,0,.034,.026,.028,body);
    k.cylB(head,0,-.175,0,.034,.082,.118,k.material('#36574a',.38,{metalness:.45,side:T.DoubleSide}),true,28);
    k.cylB(head,0,-.173,0,.031,.078,.112,k.material('#fff1d2',.6,{emissive:'#ffd595',emissiveIntensity:.08,lit:[.08,.9],side:T.BackSide}),true,28);
    k.tor(head,0,-.175,0,.082,.0035,k.brass).rotation.x=Math.PI/2;
    k.sph(head,0,-.13,0,.03,.034,.03,k.emissive('#fff6df',.25,2.2)).castShadow=false;
    k.pointLight(head,0,-.2,0,'#ffcf8d',.2,3,3.2);
    // power cord running off the back edge of the desk
    k.mesh(k.keep(new T.TubeGeometry(new T.CatmullRomCurve3([V(-.05,.012,-.06),V(-.07,.004,-.09),V(-.075,.0,-.1),V(-.078,-.04,-.104),V(-.08,-.6,-.11)]),24,.0028,6,false)),k.mat('#2b2a2e',.6),g,0,0,0);
  };
  items.aroma_diffuser=function(k,g,s){k.cylB(g,0,0,0,.07,.085,.04,k.darkWood);k.sph(g,0,.085,0,.085,.075,.085,k.material('#e8eee3',.25,{transparent:true,opacity:.9}));k.cylB(g,0,.15,0,.018,.022,.02,k.darkWood);var mist=k.material('#ffffff',1,{transparent:true,opacity:.22,depthWrite:false});[0,1,2].forEach(function(i){k.sph(g,Math.sin(i*2)*.015,.2+i*.05,0,.03+i*.012,.025+i*.01,.03+i*.012,mist).castShadow=false;});};
  items.bedtime_book=function(k,g,s){var L=s.L,D=s.Dd;k.bx(g,0,0,0,L,.02,D,k.mat('#7f9b8e',.7),.004);k.bx(g,.004,.02,0,L-.012,.016,D-.012,k.cream,.002);k.bx(g,0,.036,0,L,.012,D,k.mat('#9fb5a3',.7),.003);k.bx(g,.03,.03,D/2+.01,.012,.003,.06,k.mat('#c4877f'));};
  items.vanity_mirror=function(k,g,s){var L=s.L,D=s.Dd;k.legs(g,L,D,.13,.06);k.bx(g,0,.13,0,L,.6,D,k.wood,.02);k.bx(g,0,.725,0,L+.04,.04,D+.04,k.cream,.015);
    [-1,1].forEach(function(sd){for(var r=0;r<3;r++){var y=.25+r*.18;k.box(g,sd*L*.3,y,D/2+.01,L*.36,.16,.03,k.wood,.01);k.box(g,sd*L*.3,y,D/2+.035,.1,.02,.02,k.brass,.006);}});k.box(g,0,.6,D/2+.01,L*.2,.12,.03,k.wood,.01);
    var mh=.86,my=.77+mh/2,mz=-D/2+.12;k.box(g,0,my,mz,L*.62,mh,.06,k.wood,.03);k.box(g,0,my,mz,L*.62-.08,mh-.08,.07,k.brass,.008);k.mirror(k.box(g,0,my,mz+.04,L*.62-.13,mh-.13,.006,k.material('#ffffff',.04,{metalness:1})));
    k.cylB(g,L*.33,.745,D/2-.16,.035,.04,.06,k.mat('#d7b0bb',.5));k.cylB(g,L*.22,.745,D/2-.12,.025,.03,.08,k.material('#e8dfee',.2,{transparent:true,opacity:.85}));k.bx(g,-L*.3,.745,D/2-.2,.12,.02,.16,k.mat('#e5cfa0',.5),.006);
    var sx=0,sz=D/2+.3;[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){var leg=k.cylB(g,sx+q[0]*.1,0,sz+q[1]*.1,.016,.012,.4,k.darkWood);leg.rotation.set(q[1]*.1,0,-q[0]*.1);});k.cylB(g,sx,.38,sz,.2,.18,.08,k.lavender);k.sph(g,sx,.46,sz,.19,.035,.19,k.lavender);};
  items.plush=function(k,g,s){var y0=.07,fur=k.mat('#debf96',1),snout=k.mat('#f5e3c5'),eye=k.mat('#4b454c',.3),bow=k.mat('#b99ac3',.8);
    k.sph(g,0,y0+.12,0,.15,.17,.13,fur);k.sph(g,0,y0+.32,0,.14,.13,.12,fur);[-1,1].forEach(function(sd){k.sph(g,sd*.11,y0+.42,0,.055,.055,.04,fur);k.sph(g,sd*.11,y0+.42,.02,.03,.03,.02,snout);k.sph(g,sd*.055,y0+.34,.106,.014,.017,.009,eye);k.sph(g,sd*.14,y0+.12,.02,.055,.09,.055,fur);k.sph(g,sd*.08,y0-.01,.06,.07,.05,.09,fur);k.sph(g,sd*.04,y0+.21,.12,.035,.022,.02,bow);});
    k.sph(g,0,y0+.29,.115,.07,.05,.03,snout);k.sph(g,0,y0+.31,.145,.019,.014,.009,eye);k.sph(g,0,y0+.12,.12,.08,.09,.02,snout);};
  // ---- living room
  items.sofa=function(k,g,s){seatSofa(k,g,s.L,Math.min(s.Dd,1.0),{color:'#b9c6ad',cushion:'#c6d1ba'});};
  items.tv=function(k,g,s){var dark=k.mat('#2b2a2e',.4);k.bx(g,0,0,-.0,.5,.018,.22,dark,.006);k.bx(g,0,.018,-.01,.08,.08,.04,dark,.01);k.box(g,0,.56,0,1.58,.9,.035,k.blackGloss,.012);
    var scr=k.canvasTexture(function(c,w,h){var gr=c.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#27354a');gr.addColorStop(1,'#11161f');c.fillStyle=gr;c.fillRect(0,0,w,h);if(k.night){c.fillStyle='#e8c78d';c.beginPath();c.arc(w*.7,h*.35,18,0,PI*2);c.fill();c.fillStyle='#4f7a6c';c.beginPath();c.moveTo(0,h);c.lineTo(w*.3,h*.55);c.lineTo(w*.55,h*.8);c.lineTo(w*.8,h*.5);c.lineTo(w,h*.7);c.lineTo(w,h);c.fill();}},256,144);
    k.box(g,0,.56,.019,1.5,.84,.002,k.material('#ffffff',.15,{map:scr,emissive:'#ffffff',emissiveMap:scr,emissiveIntensity:.05,lit:[.05,.9]})).castShadow=false;};
  items.coffee_table=function(k,g,s){var L=s.L,D=s.Dd,H=.46;var top=k.cylB(g,0,H-.045,0,.5,.5,.045,k.wood);top.scale.set(L,1,D);var sh=k.cylB(g,0,.12,0,.5,.5,.02,k.wood);sh.scale.set(L*.8,1,D*.75);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){k.cylB(g,q[0]*L*.32,0,q[1]*D*.28,.022,.018,H-.04,k.darkWood);});k.bx(g,L*.22,H,-.05,.22,.04,.16,k.mat('#a8b89d',.6),.01);k.cylB(g,-L*.25,H,.05,.05,.06,.1,k.mat('#e9e1d1',.3));};
  items.record_player=function(k,g,s){var L=s.L,D=s.Dd;k.bx(g,0,0,0,L,.08,D,k.walnut,.012);k.cylB(g,-.06,.08,0,.16,.16,.015,k.chrome);k.cylB(g,-.06,.095,0,.15,.15,.004,k.blackGloss);k.cylB(g,-.06,.099,0,.05,.05,.002,k.mat('#c8786a',.6));
    k.cylB(g,.19,.08,-.13,.02,.02,.04,k.chrome);var arm=k.box(g,.14,.125,-.03,.012,.012,.24,k.chrome);arm.rotation.y=.35;k.bx(g,.2,.08,.15,.05,.01,.03,k.chrome);};
  items.game_console=function(k,g,s){k.bx(g,0,0,-.02,.22,.06,.3,k.mat('#f3f0ea',.4),.012);k.bx(g,0,.03,.131,.18,.004,.004,k.emissive('#7fb3e6',.4,1.4));var c=k.group(g,.0,0,.2);k.bx(c,0,0,0,.12,.025,.06,k.mat('#8f9eae',.5),.012);k.sph(c,-.055,.015,.01,.03,.02,.03,k.mat('#8f9eae',.5));k.sph(c,.055,.015,.01,.03,.02,.03,k.mat('#8f9eae',.5));c.rotation.y=.4;};
  items.board_game=function(k,g,s){var t=k.canvasTexture(function(c,w,h){for(var i=0;i<8;i++)for(var j=0;j<8;j++){c.fillStyle=(i+j)%2?'#e8dcc0':'#9d8467';c.fillRect(i*w/8,j*h/8,w/8,h/8);}},128,128);k.bx(g,0,0,0,.36,.014,.36,k.material('#ffffff',.6,{map:t}),.004);
    [[-.12,-.12,'#c8786a'],[.05,-.05,'#5f7e9b'],[.12,.1,'#c8786a'],[-.05,.12,'#5f7e9b'],[0,0,'#e3c27a']].forEach(function(p){k.cylB(g,p[0],.014,p[1],.016,.02,.035,k.mat(p[2],.4));k.sph(g,p[0],.06,p[1],.016,.016,.016,k.mat(p[2],.4));});k.bx(g,.26,0,.08,.14,.035,.2,k.mat('#c9b49a',.6),.006);};
  items.floor_lamp=function(k,g,s){k.cylB(g,0,0,0,.15,.17,.03,k.brass);k.cylB(g,0,.03,0,.012,.012,1.38,k.brass);var sm=k.material('#f4e4bd',.8,{emissive:'#ffd395',emissiveIntensity:.1,lit:[.1,.7],side:k.T.DoubleSide});k.cylB(g,0,1.34,0,.16,.24,.3,sm,true);k.sph(g,0,1.42,0,.05,.06,.05,k.emissive('#fff6df',.3,2)).castShadow=false;k.pointLight(g,0,1.42,0,'#ffd29a',.2,2.6,5);};
  items.yoga_mat=function(k,g,s){var L=s.L,D=s.Dd,m=k.mat('#a98fae',.85);k.bx(g,.12,0,0,L-.3,.008,D-.08,m,.003);var r=k.cyl(g,-L/2+.14,.08,0,.08,.08,D-.08,m);r.rotation.x=PI/2;k.cylB(g,-L/2+.14,.0,D/2-.04,.075,.075,.002,k.mat('#8e7493',.85)).rotation.x=PI/2;};
  items.piano=function(k,g,s){var L=s.L,D=s.Dd,H=1.24,pb=k.blackGloss,bz=-D/2;k.bx(g,0,0,bz+.21,L,H,.42,pb,.02);k.bx(g,0,H,bz+.21,L+.04,.03,.46,pb,.008);
    [-1,1].forEach(function(sd){k.bx(g,sd*(L/2-.04),0,bz+.5,.08,.76,.18,pb,.01);k.bx(g,sd*(L/2-.06),0,D/2-.06,.06,.06,.08,pb,.01);});
    var keys=k.canvasTexture(function(c,w,h){c.fillStyle='#f8f5ee';c.fillRect(0,0,w,h);var n=52;for(var i=0;i<n;i++){c.fillStyle='#d8d2c6';c.fillRect(i*w/n,0,1,h);}for(var j=0;j<n-1;j++){if([2,6].indexOf(j%7)>=0)continue;c.fillStyle='#1d1c1f';c.fillRect((j+.65)*w/n,0,w/n*.7,h*.62);}},1024,64);
    k.bx(g,0,.7,bz+.52,L-.16,.05,.22,pb,.006);k.bx(g,0,.75,bz+.53,L-.18,.022,.2,k.material('#ffffff',.3,{map:keys}),.002);k.bx(g,0,.77,bz+.43,L-.16,.06,.03,pb,.006);
    k.box(g,0,1.0,bz+.43,L*.6,.24,.02,pb,.006).rotation.x=-.2;k.bx(g,0,.95,bz+.38,.34,.24,.01,k.mat('#f6f1e6',.9)).rotation.x=-.2;
    [-.06,0,.06].forEach(function(x){k.bx(g,x,.06,bz+.44,.03,.012,.08,k.brass,.004);});k.cylB(g,L*.35,H+.03,bz+.2,.04,.05,.1,k.mat('#e9e1d1',.3));};
  items.aquarium=function(k,g,s){var L=s.L,D=s.Dd,H=.58,f=k.black;k.bx(g,0,0,0,L,.03,D,f,.006);k.bx(g,0,H-.04,0,L,.04,D,f,.006);
    var water=k.material('#7fc4c9',.1,{transparent:true,opacity:.32,depthWrite:false});k.bx(g,0,.03,0,L-.03,H-.1,D-.03,water).castShadow=false;k.bx(g,0,.03,0,L-.01,H-.07,D-.01,k.glass).castShadow=false;
    k.bx(g,0,.03,0,L-.04,.05,D-.04,k.mat('#e3d4b5',1));for(var i=0;i<9;i++){var x=-L/2+.1+i*(L-.2)/8,hh=.12+((i*5)%4)*.06;var w=k.cylB(g,x,.08,(i%3-1)*D*.25,.004,.02,hh,i%2?k.leaf:k.leafDark);w.rotation.z=Math.sin(i)*.15;}
    [[-.3,.32,.05,'#f08a4b'],[.2,.25,-.08,'#f2c14e'],[.4,.38,.1,'#e86f6f'],[-.05,.2,.0,'#7fb3e6']].forEach(function(fh){var b=k.sph(g,fh[0],fh[1],fh[2],.035,.022,.012,k.mat(fh[3],.4));k.sph(g,fh[0]-.04,fh[1],fh[2],.015,.016,.004,k.mat(fh[3],.4));b.castShadow=false;});
    k.sph(g,.5,.1,.08,.06,.04,.05,k.mat('#a7a39a',.9));k.pointLight(g,0,H-.06,0,'#9fd6e6',.1,1.2,2.2);};
  // ---- bathroom
  items.bathtub=function(k,g,s){var L=s.L,D=s.Dd,H=.58,wht=k.porcelain,t=.08;[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){k.sph(g,q[0]*(L/2-.15),.04,q[1]*(D/2-.12),.05,.05,.05,k.brass);});
    k.bx(g,0,.07,0,L,.12,D,wht,.06);k.bx(g,0,.07,-D/2+t/2,L,H-.07,t,wht,.03);k.bx(g,0,.07,D/2-t/2,L,H-.07,t,wht,.03);k.bx(g,-L/2+t/2,.07,0,t,H-.07,D,wht,.03);k.bx(g,L/2-t/2,.07,0,t,H-.07,D,wht,.03);
    k.bx(g,0,.19,0,L-2*t,.01,D-2*t,k.mat('#eef3f1',.2));k.bx(g,0,.2,0,L-2*t-.01,.24,D-2*t-.01,k.material('#a9d6d8',.05,{transparent:true,opacity:.45,depthWrite:false})).castShadow=false;
    for(var b=0;b<10;b++)k.sph(g,-L*.2+Math.sin(b*2.3)*L*.2,.45,Math.cos(b*1.7)*D*.2,.04+(b%3)*.015,.025,.04+(b%3)*.015,k.mat('#ffffff',.6)).castShadow=false;
    k.cylB(g,L/2-.08,H,0,.02,.02,.14,k.chrome);var sp=k.cyl(g,L/2-.14,H+.13,0,.014,.014,.14,k.chrome);sp.rotation.z=PI/2;};
  items.shower=function(k,g,s){var L=s.L,D=s.Dd;k.bx(g,0,0,0,L,.06,D,k.porcelain,.02);k.cylB(g,0,.06,0,.035,.035,.002,k.chrome);
    var gl=k.material('#dfeff0',.05,{transparent:true,opacity:.18,depthWrite:false,metalness:.1});k.bx(g,0,.06,D/2-.01,L,1.94,.012,gl).castShadow=false;k.bx(g,-L/2+.01,.06,0,.012,1.94,D,gl).castShadow=false;
    var fr=k.batch(g,k.chrome);fr.box(-L/2+.01,1.03,D/2-.01,.025,1.94,.025).box(0,2.0,D/2-.01,L,.025,.025).box(-L/2+.01,2.0,0,.025,.025,D);fr.done();
    k.cylB(g,L/2-.12,.6,-D/2+.04,.014,.014,1.45,k.chrome);var arm=k.cyl(g,L/2-.12,2.05,-D/2+.15,.012,.012,.22,k.chrome);arm.rotation.x=PI/2;k.cylB(g,L/2-.12,1.98,-D/2+.26,.1,.1,.02,k.chrome);k.cylB(g,L/2-.12,1.05,-D/2+.05,.04,.04,.08,k.chrome).rotation.x=PI/2;
    k.bx(g,L/2-.08,1.1,-.1,.1,.02,.2,k.chrome,.004);k.cylB(g,L/2-.08,1.12,-.15,.025,.025,.1,k.mat('#c9b6d5',.4));k.cylB(g,L/2-.08,1.12,-.06,.025,.025,.12,k.mat('#b5d0c4',.4));};
  items.bath_salts=function(k,g,s){k.cylB(g,0,0,0,.075,.075,.16,k.material('#eef6f4',.05,{transparent:true,opacity:.35}));k.cylB(g,0,.005,0,.068,.068,.1,k.mat('#e8b9c6',.9));k.cylB(g,0,.16,0,.08,.08,.03,k.lightWood);k.cylB(g,.1,0,.03,.015,.02,.06,k.mat('#f4f0e8',.5));};
  items.waterproof_speaker=function(k,g,s){k.cylB(g,0,0,0,.06,.06,.16,k.mat('#7fa6a1',.6));k.cylB(g,0,.03,0,.062,.062,.1,k.mat('#5c7f7a',.9));k.tor(g,0,.18,0,.03,.006,k.black).rotation.x=PI/2;};
  items.face_mask=function(k,g,s){var p=k.bx(g,-.05,0,0,.16,.008,.22,k.mat('#f2c9d2',.5),.004);p.rotation.y=.2;k.cylB(g,.1,0,.02,.045,.045,.06,k.mat('#ffffff',.3));k.cylB(g,.1,.06,.02,.047,.047,.02,k.mat('#c8abc2',.4));};
  items.bath_towel=function(k,g,s){var L=s.L,D=s.Dd,x=L/2-.05,bar=k.cyl(g,x,1.15,0,.012,.012,D-.04,k.chrome);bar.rotation.x=PI/2;[-1,1].forEach(function(z){k.bx(g,x+.03,1.13,z*(D/2-.03),.03,.04,.02,k.chrome);});
    var t=k.material('#e9d7d0',.98,{map:k.tex.cloth});k.bx(g,x-.02,.72,0,.03,.44,D-.14,t,.01);k.bx(g,x+.02,.72,0,.03,.44,D-.14,t,.01);k.bx(g,x,1.15,0,.07,.03,D-.14,t,.012);k.bx(g,x-.02,.78,0,.035,.03,D-.14,k.mat('#c8abc2',.95));};
  // ---- kitchen
  items.fridge=function(k,g,s){var L=s.L,D=s.Dd,H=1.92,b=k.mat('#e4e8dc',.35);k.bx(g,0,0,0,L,H,D-.04,b,.04);k.bx(g,0,.03,D/2-.02,L-.02,1.18,.04,b,.02);k.bx(g,0,1.23,D/2-.02,L-.02,.66,.04,b,.02);
    [.7,1.45].forEach(function(y,i){k.bx(g,L/2-.08,y,D/2+.02,.025,i?.3:.5,.03,k.brass,.008);});[['#c8786a',.2,1.5],['#e3c27a',-.1,1.38],['#7d9a74',.05,.9]].forEach(function(m){k.bx(g,m[1],m[2],D/2+.002,.06,.06,.01,k.mat(m[0],.5),.004);});k.bx(g,-.1,.95,D/2+.002,.14,.18,.004,k.mat('#fbf8f0',.9));};
  items.coffee_machine=function(k,g,s){var b=k.mat('#ebe4d6',.35);k.bx(g,0,0,-.06,.32,.38,.24,b,.03);k.bx(g,0,0,.06,.32,.04,.18,k.steel,.01);k.bx(g,0,.24,.07,.3,.14,.16,b,.02);k.cylB(g,0,.17,.1,.04,.035,.07,k.chrome);var h=k.box(g,0,.2,.2,.02,.02,.12,k.black,.006);k.cylB(g,0,.04,.1,.035,.03,.07,k.porcelain);k.cylB(g,.11,.32,.15,.02,.02,.02,k.brass).rotation.x=PI/2;k.cylB(g,-.11,.32,.15,.02,.02,.02,k.brass).rotation.x=PI/2;};
  items.pour_over=function(k,g,s){k.cylB(g,-.04,0,0,.065,.055,.15,k.material('#eef6f4',.05,{transparent:true,opacity:.4}));k.cylB(g,-.04,0,0,.055,.05,.07,k.mat('#5b3a2a',.4));k.cylB(g,-.04,.15,0,.08,.03,.09,k.mat('#f1ebe0',.25));
    var kt=k.group(g,.09,0,.0);k.cylB(kt,0,0,0,.06,.07,.13,k.steel);k.cylB(kt,0,.13,0,.03,.05,.03,k.steel);var sp=k.cyl(kt,-.07,.1,0,.006,.009,.14,k.steel);sp.rotation.z=.9;k.tor(kt,.07,.08,0,.04,.006,k.black,PI).rotation.z=-PI/2;};
  items.toaster=function(k,g,s){var b=k.mat('#b8d0c3',.35);k.bx(g,0,0,0,.3,.2,.17,b,.05);[-.04,.04].forEach(function(z){k.bx(g,0,.19,z,.22,.012,.025,k.black);k.bx(g,0,.17,z,.18,.07,.012,k.mat('#d9b27c',.8),.01);});k.bx(g,.16,.08,0,.02,.02,.04,k.chrome,.005);};
  items.recipe_book=function(k,g,s){var st=k.group(g,0,0,0);k.bx(st,0,0,.05,.32,.02,.1,k.wood,.004);var b=k.group(st,0,.12,-.0);b.rotation.x=-.35;[-1,1].forEach(function(sd){var p=k.box(b,sd*.08,0,0,.16,.22,.012,k.mat('#fbf6ea',.9),.003);p.rotation.y=sd*-.12;});k.box(b,0,0,-.012,.34,.24,.01,k.mat('#c8786a',.6),.003);};
  items.oven=function(k,g,s){var L=s.L,D=s.Dd,f=D/2+.006,top=0,b=-s.base;k.bx(g,0,b+.1,f,L-.04,.72,.012,k.steel,.006);k.bx(g,0,b+.22,f+.007,L-.2,.4,.004,k.material('#20262a',.1,{metalness:.3}));var hd=k.cyl(g,0,b+.72,f+.04,.012,.012,L-.2,k.chrome);hd.rotation.z=PI/2;
    k.bx(g,0,b+.76,f+.005,L-.04,.06,.008,k.black);for(var i=0;i<4;i++)k.cyl(g,-L*.3+i*L*.2,b+.79,f+.015,.015,.015,.015,k.chrome).rotation.x=PI/2;
    k.bx(g,0,top,0,L-.1,.008,D-.14,k.blackGloss,.004);[[-.17,-.14],[.17,-.14],[-.17,.14],[.17,.14]].forEach(function(q){k.tor(g,q[0]*L*1.4,top+.01,q[1]*D*1.2,.075,.004,k.mat('#6e6a69',.5)).rotation.x=PI/2;});};
  items.dishwasher=function(k,g,s){var L=s.L,D=s.Dd,f=D/2+.006,b=-s.base;k.bx(g,0,b+.1,f,L-.04,.74,.012,k.steel,.006);k.bx(g,0,b+.78,f+.002,L-.04,.05,.008,k.black);var hd=k.cyl(g,0,b+.72,f+.035,.01,.01,L-.24,k.chrome);hd.rotation.z=PI/2;k.bx(g,L*.3,b+.79,f+.007,.06,.012,.002,k.emissive('#8fd6a8',.4,1.2));};
  items.rice_cooker=function(k,g,s){k.cylB(g,0,0,0,.14,.13,.18,k.mat('#f4f0e8',.35));k.sph(g,0,.18,0,.13,.05,.13,k.mat('#f4f0e8',.35));k.bx(g,0,.2,0,.12,.03,.03,k.mat('#c8abc2',.5),.01);k.bx(g,0,.07,.13,.06,.04,.02,k.emissive('#e6b67f',.4,1),.006);};
  items.dining_table=function(k,g,s){diningTable(k,g,s.L,s.Dd,{});};
  items.tea_set=function(k,g,s){k.bx(g,0,0,0,.5,.015,.28,k.walnut,.006);var tp=k.mat('#f5f1e8',.2);k.sph(g,-.1,.08,0,.08,.07,.08,tp);k.cylB(g,-.1,.14,0,.03,.04,.02,tp);k.sph(g,-.1,.17,0,.012,.012,.012,k.brass);var sp=k.cyl(g,-.02,.08,0,.01,.016,.1,tp);sp.rotation.z=-.9;k.tor(g,-.2,.08,0,.04,.008,tp,PI*1.2).rotation.z=PI/2;
    [.08,.17].forEach(function(x){k.cylB(g,x,.015,.04,.03,.025,.05,tp);k.cylB(g,x,.015,.04,.045,.045,.004,tp);});};
  function diningTable(k,g,L,D,o){var H=.76,m=o.wood||k.wood;k.bx(g,0,H-.045,0,L,.045,D,m,.012);k.bx(g,0,H-.11,0,L-.12,.07,D-.12,m,.006);[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){k.bx(g,q[0]*(L/2-.08),0,q[1]*(D/2-.08),.06,H-.05,.06,m,.01);});if(o.runner){k.bx(g,0,H,0,.34,.004,D+.06,k.fabric('#a8b89d'),.002);}}
  // ---- dining room
  items.dining_room_table=function(k,g,s){var L=s.L,D=s.Dd,H=.76;diningTable(k,g,L,D,{runner:true,wood:k.walnut});var pl=k.porcelain;[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){var x=q[0]*L*.23,z=q[1]*(D/2-.18);k.cylB(g,x,H,z,.12,.11,.012,pl);k.cylB(g,x,H+.012,z,.085,.08,.01,k.mat('#e9eee0',.3));k.cylB(g,x+.17,H,z-.05*q[1],.03,.025,.12,k.glass);[-1,1].forEach(function(sd){k.bx(g,x+sd*.16,H,z,.012,.004,.16,k.chrome);});});
    k.cylB(g,0,H,0,.06,.05,.18,k.mat('#d9cfe0',.2));for(var i=0;i<7;i++){var a=i*.9,st=k.cylB(g,Math.sin(a)*.03,H+.18,Math.cos(a)*.03,.003,.003,.16,k.leafDark);st.rotation.set(Math.cos(a)*.3,0,Math.sin(a)*.3);k.sph(g,Math.sin(a)*.08,H+.34+(i%3)*.03,Math.cos(a)*.08,.035,.03,.035,k.mat(['#f2c9d2','#f5e8cd','#c8abc2'][i%3],.8));}};
  items.sideboard=function(k,g,s){var L=s.L,D=s.Dd,H=.86;k.legs(g,L,D,.16,.07);k.bx(g,0,.16,0,L,H-.2,D,k.walnut,.02);k.bx(g,0,H-.04,0,L+.02,.04,D+.02,k.walnut,.01);for(var i=0;i<3;i++){var x=-L/2+L/6+i*L/3;k.bx(g,x,.2,D/2+.006,L/3-.03,H-.3,.012,k.cane,.004);k.sph(g,x,.2+(H-.3)/2,D/2+.025,.015,.015,.012,k.brass);}
    k.cylB(g,-L*.32,H,0,.07,.05,.3,k.mat('#c9d7cc',.2));for(var j=0;j<3;j++){var st=k.cylB(g,-L*.32+(j-1)*.02,H+.28,0,.003,.003,.22,k.leafDark);st.rotation.z=(j-1)*.3;}var fr=k.group(g,L*.25,H+.2,-D/2+.06);fr.rotation.x=-.12;frameArt(k,fr,.36,.42,art(3,['#f3ead9','#c8abc2','#a8b89d','#e3c27a']));k.bx(g,L*.02,H,0,.24,.06,.16,k.mat('#a9bcb3',.6),.006);k.bx(g,L*.02,H+.06,0,.22,.05,.15,k.mat('#e9d7d0',.6),.006);};
  // ---- gym
  items.treadmill=function(k,g,s){var L=s.L,D=s.Dd,dk=k.mat('#3a3d42',.5),gr=k.mat('#b8bec2',.4,.4);k.bx(g,0,0,-.05,L*.82,.16,D-.2,dk,.04);k.bx(g,0,.16,-.08,L*.58,.012,D-.5,k.mat('#232528',.9));[-1,1].forEach(function(sd){k.bx(g,sd*L*.35,.16,-.08,L*.1,.02,D-.5,gr,.006);});
    [-1,1].forEach(function(sd){var p=k.box(g,sd*L*.36,.72,D/2-.3,.06,1.2,.07,gr,.012);p.rotation.x=-.18;var h=k.cyl(g,sd*L*.36,1.12,D/2-.5,.018,.018,.42,k.black);h.rotation.x=PI/2;});
    var con=k.box(g,0,1.32,D/2-.18,L*.8,.1,.34,dk,.03);con.rotation.x=.55;var scr=k.box(g,0,1.36,D/2-.2,L*.36,.012,.18,k.emissive('#7fd0e6',.3,1.4),.004);scr.rotation.x=.55;k.cylB(g,L*.3,1.28,D/2-.22,.03,.03,.16,k.mat('#7fb3e6',.3));};
  items.dumbbells=function(k,g,s){var cols=['#c8786a','#7d9a74','#5f7e9b'];for(var i=0;i<3;i++)for(var j=0;j<2;j++){var x=-.18+i*.18,z=(j-.5)*.12,c=k.mat(cols[i],.5),h=k.cyl(g,x,.05,z,.012,.012,.15,k.chrome);h.rotation.z=PI/2;[-1,1].forEach(function(sd){var w=k.cyl(g,x+sd*.065,.05,z,.04-i*.005,.04-i*.005,.04,c,false,6);w.rotation.z=PI/2;});}};
  items.fitness_mirror=function(k,g,s){var L=s.L,D=s.Dd,w=L-.2,h=1.86;k.box(g,0,.06+h/2,-D/2+.04,w+.06,h+.06,.04,k.black,.01);k.mirror(k.box(g,0,.06+h/2,-D/2+.065,w,h,.006,k.material('#ffffff',.04,{metalness:1})));k.bx(g,0,0,-D/2+.06,w+.06,.06,.08,k.black,.01);};
  // ---- balcony
  items.balcony_chair=function(k,g,s){var w=k.walnut;[-1,1].forEach(function(sd){var rg=k.group(g,sd*.28,1.0,0);rg.rotation.y=PI/2;var r=k.tor(rg,0,0,0,1.0,.018,w,1.0);r.rotation.z=-PI/2-.5;k.bx(g,sd*.28,.04,-.25,.03,.42,.03,w,.006);k.bx(g,sd*.28,.04,.2,.03,.4,.03,w,.006);k.bx(g,sd*.29,.62,-.03,.05,.03,.56,w,.01);k.bx(g,sd*.29,.42,.22,.03,.22,.03,w,.006);});
    k.bx(g,0,.4,0,.6,.04,.52,w,.01);var back=k.group(g,0,.42,-.26);back.rotation.x=-.22;for(var i=0;i<5;i++)k.bx(back,-.24+i*.12,0,0,.07,.62,.025,w,.008);k.bx(back,0,.6,0,.62,.06,.03,w,.01);
    k.mesh(k.pillow(.52,.08,.46),k.fabric('#d9c9a6'),g,0,.46,.02);var bp=k.mesh(k.pillow(.48,.07,.42),k.fabric('#a8b89d'),g,0,.72,-.24);bp.rotation.x=1.35;};
  items.blanket=function(k,g,s){var m=k.material('#ffffff',.95,{map:k.tex.plaid,side:k.T.DoubleSide});k.mesh(k.drape(.46,.24,0,.3,.035,.01),m,g,0,.1,.0);};
  items.plants=function(k,g,s){var L=s.L,D=s.Dd,box=k.mat('#b9a586',.85);k.bx(g,0,0,0,L,.36,D,box,.03);k.bx(g,0,.34,0,L-.06,.02,D-.06,k.soil);var n=Math.round(L/.22);for(var i=0;i<n;i++){var x=-L/2+.11+i*(L-.22)/(n-1),kind=i%3;if(kind===0){for(var j=0;j<6;j++){var a=j*1.1,l=k.sph(g,x+Math.cos(a)*.04,.48+(j%2)*.06,Math.sin(a)*.04,.035,.13,.012,j%2?k.leaf:k.leafDark);l.rotation.set(Math.sin(a)*.6,a,Math.cos(a)*.6);}}else if(kind===1){k.sph(g,x,.48,0,.11,.1,.1,k.leafDark);for(var f=0;f<5;f++)k.sph(g,x+Math.sin(f*1.3)*.08,.55+(f%2)*.03,Math.cos(f*1.3)*.07,.025,.025,.025,k.mat(['#f2c9d2','#f7e2a4','#ffffff'][f%3],.7));}else{k.cylB(g,x,.35,0,.008,.008,.3,k.leafDark);k.sph(g,x,.7,0,.09,.12,.09,k.leaf);}}};
  items.watering_can=function(k,g,s){var m=k.mat('#9db8b0',.4,.3);k.cylB(g,0,0,0,.1,.11,.2,m);var sp=k.cyl(g,.15,.14,0,.012,.02,.24,m);sp.rotation.z=-1.0;k.cylB(g,.25,.21,0,.03,.02,.03,m).rotation.z=-1.0;var h=k.tor(g,-.02,.2,0,.09,.012,m,PI);h.rotation.z=.2;};
  items.wind_chime=function(k,g,s){var top=s.ceiling-.08,piv=k.group(g,0,top-.25,0);k.swayers.push({obj:piv,kind:'chime'});g=piv;top=.25;k.cylB(g,0,top-.25,0,.004,.004,.33,k.black);k.cylB(g,0,top-.27,0,.08,.08,.02,k.lightWood);for(var i=0;i<6;i++){var a=i*PI/3,len=.18+i*.035;k.cylB(g,Math.cos(a)*.06,top-.3-len,Math.sin(a)*.06,.008,.008,len,k.brass);}k.cylB(g,0,top-.62,0,.003,.003,.14,k.black);k.bx(g,0,top-.72,0,.06,.09,.004,k.mat('#c8abc2',.6));};
  items.telescope=function(k,g,s){var m=k.mat('#f3f0ea',.35),dk=k.black;for(var i=0;i<3;i++){var a=i*PI*2/3,l=k.box(g,Math.sin(a)*.2,.48,Math.cos(a)*.2,.025,1.0,.025,k.darkWood,.006);l.rotation.set(Math.cos(a)*-.38,0,Math.sin(a)*.38);}k.sph(g,0,.98,0,.05,.05,.05,dk);
    var tube=k.group(g,0,1.08,0);tube.rotation.x=-.6;k.cyl(tube,0,0,.08,.07,.07,.9,m).rotation.x=PI/2;k.cyl(tube,0,0,.55,.08,.08,.06,dk).rotation.x=PI/2;k.cyl(tube,0,.09,-.1,.015,.015,.22,dk).rotation.x=PI/2;k.cyl(tube,0,0,-.4,.025,.02,.1,dk).rotation.x=PI/2;};
  items.washing_machine=function(k,g,s){var L=s.L,D=s.Dd,H=.86,b=k.mat('#f5f3ee',.35);k.bx(g,0,0,0,L,H,D,b,.03);k.bx(g,0,H-.13,D/2+.004,L-.04,.11,.008,k.mat('#e7e4dc',.4));k.cyl(g,L*.25,H-.075,D/2+.012,.03,.03,.015,k.chrome).rotation.x=PI/2;k.bx(g,-L*.2,H-.09,D/2+.01,.18,.05,.004,k.emissive('#a7d3d6',.3,1));
    var door=k.tor(g,0,.4,D/2+.02,.2,.035,k.chrome);k.cyl(g,0,.4,D/2+.018,.19,.19,.02,k.material('#9fb7c4',.05,{transparent:true,opacity:.55})).rotation.x=PI/2;k.cyl(g,0,.4,D/2-.01,.16,.16,.01,k.mat('#c8abc2',.9)).rotation.x=PI/2;};
  items.iron=function(k,g,s){var b=k.group(g,0,0,0);b.rotation.y=.3;k.bx(b,0,0,0,.12,.03,.24,k.chrome,.01);k.bx(b,0,.03,-.01,.1,.06,.2,k.mat('#9ec2cf',.35),.03);var h=k.tor(b,0,.1,-.02,.07,.014,k.mat('#9ec2cf',.35),PI);h.rotation.y=PI/2;k.bx(g,-.08,0,.0,.32,.004,.3,k.material('#ffffff',.95,{map:k.tex.plaid}),.002);};
  // ---- entry
  items.shoe_cabinet=function(k,g,s){var L=s.L,D=s.Dd,H=.88;k.legs(g,L,D,.12,.06);k.bx(g,0,.12,0,L,H-.16,D,k.wood,.02);k.bx(g,0,H-.04,0,L+.02,.04,D+.02,k.cream,.01);var n=3;for(var i=0;i<n;i++){var x=-L/2+L/(2*n)+i*L/n,sl=k.batch(g,k.lightWood);sl.box(x,.16+(H-.24)/2,D/2+.008,L/n-.03,H-.24,.012,.004);for(var r=0;r<7;r++)sl.box(x,.2+r*.085,D/2+.018,L/n-.06,.02,.01,.002);sl.done();k.sph(g,x+L/(2*n)-.07,.5,D/2+.03,.015,.015,.012,k.brass);}
    };
  items.umbrella=function(k,g,s){k.cylB(g,0,0,0,.12,.11,.45,k.mat('#c9d7cc',.3));k.cylB(g,0,.44,0,.122,.122,.02,k.mat('#b3c4b8',.3));[['#c8abc2',-.03,.2],['#7d9a74',.04,-.15]].forEach(function(u){var gr=k.group(g,u[1],.06,u[1]);gr.rotation.set(u[2]*.4,0,u[2]*.5);k.cylB(gr,0,0,0,.025,.06,.7,k.mat(u[0],.6));k.cylB(gr,0,.7,0,.008,.008,.12,k.darkWood);k.tor(gr,.03,.82,0,.03,.008,k.darkWood,PI).rotation.z=0;});};
  items.key_tray=function(k,g,s){k.cylB(g,0,0,0,.14,.13,.025,k.wood).scale.set(1.2,1,.85);k.tor(g,-.03,.03,0,.025,.005,k.brass).rotation.x=PI/2;k.bx(g,.02,.025,.0,.06,.006,.015,k.brass,.002);k.tor(g,.05,.03,.04,.02,.004,k.chrome).rotation.x=PI/2;k.bx(g,.08,.026,.04,.05,.006,.012,k.chrome,.002);k.bx(g,-.08,.025,.03,.04,.012,.03,k.mat('#c8786a',.5),.004);};
  items.vacuum=function(k,g,s){var m=k.mat('#ebe7df',.35),acc=k.mat('#9db8b0',.4);k.bx(g,0,0,0,.36,.04,.3,m,.015);k.bx(g,0,.04,-.11,.3,.6,.06,m,.02);k.bx(g,0,.04,.04,.28,.04,.1,k.mat('#4a4c50',.6),.02);k.cylB(g,0,.06,0,.014,.014,.95,k.chrome);k.cylB(g,0,.4,.04,.06,.06,.22,acc);k.bx(g,0,1.0,0,.04,.12,.06,k.black,.01);k.bx(g,0,.6,-.08,.06,.012,.004,k.emissive('#8fd6a8',.4,1));};
  items.sewing_kit=function(k,g,s){k.bx(g,0,0,0,.3,.1,.2,k.basket,.02);k.bx(g,0,.1,-.05,.3,.012,.12,k.mat('#c8abc2',.6),.004).rotation.x=-.5;['#c8786a','#7fb3e6','#e3c27a','#7d9a74'].forEach(function(c,i){k.cylB(g,-.1+i*.065,.1,.03,.018,.018,.05,k.mat(c,.6));});k.sph(g,.2,.03,.05,.04,.03,.04,k.mat('#d97b7b',.8));};
  items.delivery_box=function(k,g,s){var L=s.L*.86,D=s.Dd*.86,H=.46,c=k.mat('#c9a97c',.9);k.bx(g,0,0,0,L,H,D,c,.01);k.bx(g,0,H,0,.07,.003,D+.01,k.mat('#e8dcc0',.4));k.bx(g,0,H*.5,D/2+.002,.07,H,.003,k.mat('#e8dcc0',.4));k.bx(g,L*.22,H+.001,-.08,.18,.002,.12,k.mat('#fbf8f0',.9));k.bx(g,L*.6,0,.0,.3,.22,.24,c,.01);};
  // ---- dressing room
  items.dressing_mirror=function(k,g,s){var L=s.L,D=s.Dd,w=Math.min(1.0,L-.2),h=1.8,z=-D/2+.05,sh=k.T;var fr=k.group(g,0,.08+h/2,z);fr.rotation.x=-.08;k.box(fr,0,0,0,w+.08,h+.08,.05,k.brass,.02);k.mirror(k.box(fr,0,0,.028,w,h,.006,k.material('#ffffff',.04,{metalness:1})));k.bx(g,0,0,z+.05,w+.1,.08,.12,k.brass,.01);};
  items.accessory_cabinet=function(k,g,s){var L=s.L,D=s.Dd,H=1.06;k.legs(g,L,D,.1,.06);k.bx(g,0,.1,0,L,H-.24,D,k.lightWood,.02);for(var r=0;r<4;r++)for(var c=0;c<3;c++){var x=-L/3+c*L/3,y=.14+r*.17;k.bx(g,x,y,D/2+.006,L/3-.03,.15,.012,k.lightWood,.005);k.bx(g,x,y+.075,D/2+.02,.08,.014,.012,k.brass,.004);}
    k.bx(g,0,H-.14,0,L,.02,D,k.lightWood,.004);k.bx(g,0,H-.12,0,L-.04,.02,D-.04,k.fabric('#8a6f7c'));var gl=k.bx(g,0,H-.1,0,L,.1,D,k.glass);gl.castShadow=false;var fr=k.batch(g,k.brass);fr.box(0,H,D/2,L,.012,.012).box(0,H,-D/2,L,.012,.012).box(L/2,H,0,.012,.012,D).box(-L/2,H,0,.012,.012,D);fr.done();
    [['#f2e3c2',-.5],['#c9d7e6',-.2],['#e8b9c6',.15],['#f5e8cd',.45]].forEach(function(j,i){k.tor(g,j[1]*L*.8,H-.09,(i%2-.5)*.15,.035,.008,k.material(j[0],.2,{metalness:.6})).rotation.x=PI/2;k.sph(g,j[1]*L*.8+.07,H-.09,(i%2-.5)*.15+.05,.015,.015,.015,k.mat(j[0],.1));});};
  // ---- study
  items.bookshelf=function(k,g,s){var L=s.L,D=s.Dd,H=2.16,m=k.wood;[-1,1].forEach(function(sd){k.bx(g,sd*(L/2-.02),0,0,.04,H,D,m,.008);});k.bx(g,0,0,-D/2+.01,L,H,.02,k.lightWood);var shelves=6;for(var i=0;i<=shelves;i++)k.bx(g,0,i*(H-.04)/shelves,0,L-.04,.03,D,m,.006);
    var cols=['#c8786a','#5f7e9b','#e3c27a','#7d9a74','#a86d8b','#e9e1d1','#3b3b46','#b8a1c9'],bats=cols.map(function(c){return k.batch(g,k.mat(c,.7));});
    for(var sh=0;sh<shelves;sh++){var x=-L/2+.05,y=sh*(H-.04)/shelves+.03,n=0;while(x<L/2-.08){var bw=.025+((sh*7+n*13)%5)*.008,bh=.2+((sh*3+n*5)%5)*.025;if(n%11===7){x+=.12;n++;continue;}bats[(sh*3+n)%cols.length].box(x+bw/2,y+bh/2,.02,bw,bh,D-.08,.003);x+=bw+.004;n++;}}
    bats.forEach(function(b){b.done();});k.sph(g,L*.3,(H-.04)/shelves*3+.12,.02,.07,.07,.07,k.mat('#e9e1d1',.3));};
  items.desk=function(k,g,s){var L=s.L,D=s.Dd,H=.74;k.bx(g,0,H-.035,0,L,.035,D,k.wood,.012);[-1,1].forEach(function(sd){var fr=k.batch(g,k.walnut);fr.box(sd*(L/2-.06),(H-.04)/2,-D/2+.08,.05,H-.04,.05).box(sd*(L/2-.06),(H-.04)/2,D/2-.08,.05,H-.04,.05).box(sd*(L/2-.06),.06,0,.05,.05,D-.16);fr.done();});
    k.bx(g,L*.3,H-.3,.0,.5,.25,D-.2,k.wood,.012);k.bx(g,L*.3,H-.2,D/2-.1,.44,.08,.012,k.cream,.004);k.bx(g,0,H-.1,-D/2+.07,L-.2,.06,.02,k.walnut);
    };
  items.monitor=function(k,g,s){var dark=k.mat('#2b2a2e',.4);k.bx(g,0,0,0,.24,.012,.16,dark,.005);k.bx(g,0,.012,-.03,.04,.24,.03,dark,.008);k.box(g,0,.42,0,.72,.42,.025,k.blackGloss,.01);
    var t=k.canvasTexture(function(c,w,h){c.fillStyle='#1e2430';c.fillRect(0,0,w,h);var cols=['#7fb3e6','#e3c27a','#c8abc2','#8fd6a8','#e9e1d1'];for(var i=0;i<18;i++){c.fillStyle=cols[i%5];c.fillRect(14+(i%4)*10,10+i*7,40+((i*37)%120),3);}c.fillStyle='#2c3444';c.fillRect(w*.68,0,w*.32,h);},256,160);
    k.box(g,0,.42,.0135,.68,.38,.002,k.material('#ffffff',.2,{map:t,emissive:'#ffffff',emissiveMap:t,emissiveIntensity:.25,lit:[.25,.9]})).castShadow=false;};
  items.keyboard=function(k,g,s){var t=k.canvasTexture(function(c,w,h){c.fillStyle='#f4f1ea';c.fillRect(0,0,w,h);c.fillStyle='#dcd6ca';for(var r=0;r<5;r++)for(var i=0;i<15;i++)c.fillRect(4+i*16.5,4+r*11,14,9);},256,64);k.bx(g,0,0,0,.44,.018,.14,k.material('#ffffff',.5,{map:t}),.006);k.bx(g,.32,0,0,.06,.02,.1,k.mat('#f4f1ea',.4),.02);};
  items.notebook=function(k,g,s){[-1,1].forEach(function(sd){var p=k.bx(g,sd*.1,0,0,.2,.012,.27,k.mat('#fbf8f0',.9),.003);p.rotation.z=sd*-.03;});k.bx(g,0,0,0,.42,.006,.29,k.mat('#7d9a74',.7),.003);var pen=k.cyl(g,.12,.02,.02,.006,.006,.15,k.mat('#5f7e9b',.4));pen.rotation.set(PI/2,0,.6);};
  items.camera=function(k,g,s){k.bx(g,0,0,0,.16,.1,.07,k.mat('#2f2f33',.5),.015);k.bx(g,0,.03,0,.165,.05,.072,k.mat('#c8b28c',.8),.006);k.cyl(g,.0,.05,.06,.035,.035,.06,k.black).rotation.x=PI/2;k.cyl(g,0,.05,.092,.026,.026,.004,k.material('#7f9fb9',.05,{metalness:.5})).rotation.x=PI/2;k.cylB(g,-.05,.1,0,.012,.012,.012,k.chrome);};
  items.headphones=function(k,g,s){var m=k.mat('#e9e1d1',.45);k.bx(g,0,0,0,.12,.012,.12,k.walnut,.004);k.cylB(g,0,0,0,.01,.01,.22,k.walnut);var band=k.tor(g,0,.2,0,.09,.014,m,PI);band.rotation.y=PI/2;[-1,1].forEach(function(sd){k.cyl(g,0,.2,sd*.09,.045,.045,.035,m).rotation.x=PI/2;});};
  // ---- art studio
  items.art_easel=function(k,g,s){var w=k.wood;[-1,1].forEach(function(sd){var l=k.box(g,sd*.28,.8,.1,.035,1.66,.035,w,.006);l.rotation.z=sd*-.12;l.rotation.x=-.08;});var b=k.box(g,0,.78,-.32,.035,1.6,.035,w,.006);b.rotation.x=.38;k.bx(g,0,.7,.16,.7,.03,.08,w,.006);
    var t=k.canvasTexture(art(7,['#f3ead9','#94b3a1','#c8abc2','#e3c27a','#6b958a']),256,200);k.box(g,0,1.1,.13,.8,.62,.03,k.mat('#f8f4ea',.9),.004);k.box(g,0,1.1,.146,.76,.58,.002,k.material('#ffffff',.85,{map:t})).castShadow=false;k.bx(g,0,1.4,.13,.06,.04,.05,w,.006);};
  items.paint_cart=function(k,g,s){var m=k.mat('#9db8b0',.4,.2);[-1,1].forEach(function(x){[-1,1].forEach(function(z){k.cylB(g,x*.3,.04,z*.26,.012,.012,.86,m);k.sph(g,x*.3,.03,z*.26,.03,.03,.03,k.black);});});for(var i=0;i<3;i++){var y=.12+i*.33;k.bx(g,0,y,0,.62,.012,.54,m,.006);var e=k.batch(g,m);e.box(0,y+.04,.27,.62,.07,.012).box(0,y+.04,-.27,.62,.07,.012).box(.31,y+.04,0,.012,.07,.54).box(-.31,y+.04,0,.012,.07,.54);e.done();}
    ['#c8786a','#5f7e9b','#e3c27a','#7d9a74','#a86d8b','#e9e1d1'].forEach(function(c,i){k.cylB(g,-.22+i*.085,.79,-.1+(i%2)*.18,.035,.035,.08,k.mat(c,.4));});k.cylB(g,.18,.46,.05,.05,.045,.12,k.porcelain);for(var b=0;b<5;b++){var br=k.cylB(g,.18+(b-2)*.012,.5,.05,.004,.006,.22,k.wood);br.rotation.z=(b-2)*.08;}k.bx(g,-.1,.13,0,.3,.04,.22,k.mat('#f4f0e8',.9),.004);};
  items.digital_tablet=function(k,g,s){var dark=k.mat('#2b2a2e',.4);var st=k.group(g,0,0,0);k.bx(st,0,0,.05,.5,.02,.3,dark,.01);var p=k.group(st,0,.14,0);p.rotation.x=-1.05;k.box(p,0,0,0,.62,.4,.025,k.blackGloss,.015);var t=k.canvasTexture(art(11,['#f3ead9','#c8abc2','#a8b89d','#e3c27a','#7fb3e6']),256,170);k.box(p,0,0,.0135,.56,.34,.002,k.material('#ffffff',.2,{map:t,emissive:'#ffffff',emissiveMap:t,emissiveIntensity:.2,lit:[.2,.8]})).castShadow=false;var pen=k.cyl(g,.32,.02,.1,.006,.006,.16,k.black);pen.rotation.set(PI/2,0,.4);};
  // ---- cinema
  items.cinema_screen=function(k,g,s){var L=s.L,D=s.Dd,w=L-.06,h=Math.min(1.85,w*.5),y=.6+h/2;k.box(g,0,y,-D/2+.04,w+.12,h+.12,.06,k.black,.01);var t=k.canvasTexture(function(c,W,Hh){var gr=c.createLinearGradient(0,0,0,Hh);gr.addColorStop(0,'#2b3f6b');gr.addColorStop(.6,'#e9a87c');gr.addColorStop(1,'#3b2f45');c.fillStyle=gr;c.fillRect(0,0,W,Hh);c.fillStyle='#fff1c9';c.beginPath();c.arc(W*.5,Hh*.62,30,0,PI*2);c.fill();c.fillStyle='#2a2238';c.beginPath();c.moveTo(0,Hh);for(var i=0;i<=12;i++)c.lineTo(i*W/12,Hh*.7+Math.sin(i*1.7)*14);c.lineTo(W,Hh);c.fill();},512,256);
    k.box(g,0,y,-D/2+.075,w,h,.004,k.material('#ffffff',.6,{map:t,emissive:'#ffffff',emissiveMap:t,emissiveIntensity:.45,lit:[.45,.85]})).castShadow=false;k.pointLight(g,0,y,.6,'#f0b98f',.5,1.4,5);[-1,1].forEach(function(sd){k.bx(g,sd*(w/2+.32),0,-D/2+.2,.3,1.1,.3,k.mat('#2f2b38',.6),.02);k.cyl(g,sd*(w/2+.32),.8,-D/2+.355,.09,.09,.01,k.black).rotation.x=PI/2;k.cyl(g,sd*(w/2+.32),.4,-D/2+.355,.07,.07,.01,k.black).rotation.x=PI/2;});};
  items.cinema_sofa=function(k,g,s){seatSofa(k,g,s.L,s.Dd,{color:'#6a5f86',cushion:'#776b93',seats:3,recliner:true,throws:['#c8abc2','#e3c27a'],back:.54,arm:.2});};
  items.popcorn_machine=function(k,g,s){var red=k.mat('#c65b55',.45);k.bx(g,0,0,0,.46,.1,.4,red,.02);var gl=k.material('#f2f6f2',.05,{transparent:true,opacity:.25,depthWrite:false});k.bx(g,0,.1,0,.44,.42,.38,gl).castShadow=false;var fr=k.batch(g,red);[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){fr.box(q[0]*.215,.31,q[1]*.185,.02,.42,.02);});fr.done();
    k.bx(g,0,.1,0,.42,.12,.36,k.mat('#f7e3a4',.9),.01);for(var i=0;i<14;i++)k.sph(g,-.17+(i%7)*.055,.24,-.1+Math.floor(i/7)*.15,.025,.022,.025,k.mat('#fbf1d0',.9));k.bx(g,0,.52,0,.48,.06,.42,red,.02);k.cylB(g,0,.58,0,.12,.02,.12,red);k.sph(g,0,.42,0,.08,.05,.08,k.steel);k.pointLight(g,0,.45,0,'#ffd18a',0,.8,1.5);};
  // ---- terrace
    items.terrace_swing=items.balcony_chair;
  items.flower_bed=function(k,g,s){var L=s.L,D=s.Dd,wd=k.mat('#a58c6c',.85);k.bx(g,0,0,0,L,.38,D,wd,.02);var pl=k.batch(g,k.mat('#8f7759',.85));for(var i=0;i<L/.15;i++)pl.box(-L/2+.075+i*.15,.19,D/2+.002,.005,.38,.004);pl.done();k.bx(g,0,.36,0,L-.05,.03,D-.05,k.soil);
    var cols=['#f2c9d2','#f7e2a4','#ffffff','#c8abc2','#e8857a'];for(var j=0;j<Math.round(L/.11);j++){var x=-L/2+.06+j*.11,z=((j*7)%5-2)*D*.08,h=.12+((j*3)%4)*.05;k.cylB(g,x,.38,z,.005,.005,h,k.leafDark);k.sph(g,x,.39+h,z,.04,.035,.04,k.mat(cols[j%cols.length],.7));k.sph(g,x+.03,.4,z+.02,.05,.025,.03,j%2?k.leaf:k.leafDark);}};
  items.bbq_grill=function(k,g,s){var blk=k.mat('#2f3134',.45);for(var i=0;i<3;i++){var a=i*PI*2/3,l=k.box(g,Math.sin(a)*.15,.3,Math.cos(a)*.15,.03,.62,.03,blk,.006);l.rotation.set(Math.cos(a)*.18,0,-Math.sin(a)*.18);}
    var bowl=k.sph(g,0,.66,0,.3,.22,.3,blk);var lid=k.sph(g,0,.68,0,.3,.2,.3,k.mat('#3b3e42',.35,.3));lid.scale.y=.18;k.cylB(g,0,.84,0,.02,.02,.05,k.chrome);k.cyl(g,0,.66,.31,.015,.015,.12,k.chrome).rotation.z=PI/2;k.bx(g,.38,.6,0,.3,.02,.3,k.walnut,.006);k.cyl(g,-.2,.06,-.2,.06,.06,.03,blk).rotation.z=PI/2;};
  // ---- stair hall
  items.stairs=function(k,g,s){
    // A flight going DOWN to 1F. Only the upper part of the stairwell is modelled; below that the
    // opening fades into the darker floor beneath, so the cut-away room does not grow a 3 m box.
    var T=k.T,L=s.L,D=s.Dd,n=16,rise=.18,run=D/n,depth=1.3,shown=Math.floor(depth/rise)-0;
    var grad=k._stairGrad||(k._stairGrad=k.canvasTexture(function(c,w,h){var gr=c.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#e3d9c8');gr.addColorStop(.55,'#9d907f');gr.addColorStop(1,'#2f2a26');c.fillStyle=gr;c.fillRect(0,0,w,h);},4,64));
    var inner=k.material('#ffffff',.95,{map:grad}),outer=k.mat('#bba58d',.9);
    function plane(w,h,x,y,z,ry,m){var p=k.mesh(k.keep(new T.PlaneGeometry(w,h)),m,g,x,y,z,false);p.rotation.y=ry;return p;}
    var yc=-depth/2;
    plane(D,depth,-L/2,yc,0,PI/2,inner);plane(D,depth,L/2,yc,0,-PI/2,inner);plane(L,depth,0,yc,D/2,PI,inner);plane(L,depth,0,yc,-D/2,0,inner);
    plane(D+.02,depth-.2,-L/2-.03,yc-.1,0,-PI/2,outer);plane(D+.02,depth-.2,L/2+.03,yc-.1,0,PI/2,outer);plane(L+.06,depth-.2,0,yc-.1,D/2+.03,0,outer);plane(L+.06,depth-.2,0,yc-.1,-D/2-.03,PI,outer);
    var rb=k.batch(g,k.cream),tb=k.batch(g,k.wood);for(var i=0;i<shown;i++){var top=-(i+1)*rise,z0=-D/2+i*run,bot=Math.max(-depth,top-rise*1.4);rb.box(0,(top+bot)/2,z0+run/2,L,top-bot,run);tb.box(0,top+.015,z0+run/2-.01,L+.02,.03,run+.03,.004);}rb.done();tb.done();
    var capZ=-D/2+shown*run,cap=k.box(g,0,-depth+.01,(capZ+D/2)/2,L,.02,D/2-capZ,k.mat('#2f2a26',1));cap.castShadow=false;
    // trim round the opening + balustrade on the open side and the far end (the corridor-side entry stays open)
    var trim=k.batch(g,k.cream);trim.box(-L/2-.04,-.04,0,.08,.08,D+.16).box(0,-.04,D/2+.04,L+.16,.08,.08).box(L/2+.04,-.04,0,.08,.08,D+.16);trim.done();
    var rail=k.batch(g,k.darkWood);for(var z=-D/2+.05;z<=D/2+.01;z+=.12)rail.box(-L/2-.04,.45,z,.025,.86,.025);for(var x=-L/2+.08;x<L/2;x+=.12)rail.box(x,.45,D/2+.04,.025,.86,.025);rail.done();
    [-1,1].forEach(function(e){k.bx(g,-L/2-.04,0,e*(D/2+.02),.07,1.0,.07,k.walnut,.01);});k.bx(g,L/2+.02,0,D/2+.04,.07,1.0,.07,k.walnut,.01);
    var hr=k.cyl(g,-L/2-.04,.95,0,.03,.03,D+.1,k.walnut);hr.rotation.x=PI/2;var he=k.cyl(g,0,.95,D/2+.04,.03,.03,L+.1,k.walnut);he.rotation.z=PI/2;
    // wall-side handrail following the flight down into the opening
    var fl=shown*run,drop=shown*rise,len=Math.hypot(fl,drop),ang=Math.atan2(drop,fl),wr=k.cyl(g,L/2-.05,.9-drop/2,-D/2+fl/2,.02,.02,len,k.walnut);wr.rotation.x=PI/2+ang;k.bx(g,L/2-.05,0,-D/2+.04,.05,.92,.05,k.walnut,.01);
    // small sign so the direction reads at a glance
    var sg=k.group(g,-L/2-.08,1.0,-D/2+.25);sg.rotation.y=-PI/2;var st=k.canvasTexture(function(c,w,h){c.fillStyle='#f6efe2';c.fillRect(0,0,w,h);c.fillStyle='#6b5a49';c.font='bold 40px sans-serif';c.textAlign='center';c.fillText('1F ↓',w/2,h*.68);},128,64);k.box(sg,0,.08,0,.24,.12,.015,k.material('#ffffff',.8,{map:st}),.004);
  };
  items.storage_bench=function(k,g,s){var L=s.L,D=s.Dd,H=.46;k.bx(g,0,0,0,L,H-.04,D,k.wood,.02);k.bx(g,0,H-.04,0,L+.02,.04,D+.02,k.walnut,.01);var n=4;for(var i=0;i<n;i++){var x=-L/2+L/(2*n)+i*L/n;k.bx(g,x,.04,D/2-.01,L/n-.06,H-.14,.02,k.mat('#5a4f44',.9));k.bx(g,x,.05,D/2-.18,L/n-.1,.26,.32,k.basket,.03);}
    k.mesh(k.pillow(L-.06,.08,D-.04),k.fabric('#a8b89d'),g,0,H+.03,0);[-1,1].forEach(function(sd){var p=k.mesh(k.pillow(.4,.12,.36),k.fabric(sd<0?'#f5e8cd':'#c8abc2'),g,sd*(L/2-.3),H+.2,-D/2+.12);p.rotation.x=1.25;});};
  function placeholder(k,g,s){k.bx(g,0,0,0,Math.max(.2,Math.min(.5,(s.L||.3)*.8)),Math.max(.2,Math.min(.6,s.H||.3)),Math.max(.2,Math.min(.5,(s.Dd||.3)*.8)),k.sage,.035);}
  // ------------------------------------------------------------------ decor (non-item props)
  var decor={
    // 1F garage: the house's own garage room; contents shared with the garage interior builder (cars, bays, workbench...)
    车库:function(k,c){var D3=root.Destination3DModels;if(D3&&D3.garageRoom){var garage=root.SimLifeGarage||{};D3.garageRoom(k,{W:c.W,D:c.D,H:c.H,doorZ:c.Z(98),doorSide:'right',mode:garage.mode||'',vehicles:garage.vehicles||[]});}},
    卧室:function(k,c){var ns=c.fixtures[0];if(ns){var g=wallProp(k,'back','clock','时钟',c.X(ns.x+ns.w/2),1.86);if(g)clock(k,g);}
      var wd=c.plan.wardrobe,vm=c.plan.vanity_mirror,az=c.Z(vm[1]+vm[3]/2),pic=wallProp(k,'right','moon_art','月亮挂画',c.wallU('right',c.W,az),2.03);if(pic)frameArt(k,pic,.42,.4,function(cx,w,h){cx.fillStyle='#f4ead9';cx.fillRect(0,0,w,h);cx.fillStyle='#beacc6';cx.beginPath();cx.arc(w*.54,h*.42,w*.27,0,PI*2);cx.fill();cx.fillStyle='#f4ead9';cx.beginPath();cx.arc(w*.68,h*.34,w*.25,0,PI*2);cx.fill();});
      var bed=c.plan.bed,sl=floorProp(k,'slippers','拖鞋',c.X(bed[0]+bed[2])+.22,c.Z(bed[1]+bed[3])-.55,.2),pink=k.mat('#e9c9cf',.9);[-.06,.06].forEach(function(x,i){var s1=k.bx(sl,x,.04,i*.05,.1,.04,.25,pink,.018);k.bx(sl,x,.05,i*.05+.05,.09,.03,.12,k.mat('#fbf3ee',1),.012);});
      },
    客厅:function(k,c){var g=wallProp(k,'back','wall_art','装饰画',c.X(238),1.75);if(g){frameArt(k,g,.7,.5,art(1,['#f3ead9','#a8b89d','#e3c27a','#94b3a1']));}
      var g2=wallProp(k,'left','gallery','照片墙',k.D*.55,1.7);if(g2){[[-.4,.1,.36,.46],[.05,.18,.4,.3],[.05,-.17,.4,.3],[.45,.0,.3,.4]].forEach(function(f,i){var s=k.group(g2,f[0],f[1],0);frameArt(k,s,f[2],f[3],art(i+2,['#f4ecdc','#c8abc2','#7d9a74','#e3c27a']),{frame:i%2?k.darkWood:k.brass});});}
      pendant(k,'ceiling_lamp','吊灯',c.X(144),c.Z(132),.75,{r:.3});},
    浴室:function(k,c){var m=floorProp(k,'bath_mat','浴室地垫',c.X(70),c.Z(104)+.2);k.bx(m,0,0,0,.8,.012,.5,k.fabric('#b4cec6'),.006);
      var sh=wallProp(k,'back','towel_hook','挂钩',c.X(150),1.6);if(sh){k.bx(sh,0,0,.02,.3,.05,.04,k.lightWood,.01);[-.08,.08].forEach(function(x){k.sph(sh,x,-.02,.06,.015,.015,.015,k.chrome);});}},
    厨房:function(k,c){pendant(k,'pendant_1','吊灯',c.X(50),c.Z(172),.8,{r:.16,color:'#d9e0c9'});pendant(k,'pendant_2','吊灯',k.W*.5,k.D*.5,.8,{r:.16,color:'#d9e0c9'});
      var shelf=wallProp(k,'left','spice_shelf','调料架',k.D*.5,1.45);if(shelf){k.bx(shelf,0,0,.1,.7,.03,.18,k.wood,.006);['#c8786a','#e3c27a','#7d9a74','#a86d8b','#e9e1d1'].forEach(function(cl,i){k.cylB(shelf,-.28+i*.14,.03,.1,.03,.03,.12,k.mat(cl,.3));});}
      },
    餐厅:function(k,c){var t=c.plan.dining_room_table;pendant(k,'chandelier','吊灯',c.X(t[0]+t[2]/2),c.Z(t[1]+t[3]/2),.9,{r:.32,color:'#e8d9b5',power:3.2});var g=wallProp(k,'right','dining_art','装饰画',k.D*.45,1.6);if(g)frameArt(k,g,.8,.6,art(5,['#f1e7d3','#c8786a','#e3c27a','#7d9a74']));},
    健身室:function(k,c){var g=wallProp(k,'back','gym_clock','时钟',c.X(50),1.95);if(g)clock(k,g);var b=floorProp(k,'water_bottle','水壶',c.X(110),c.Z(170));k.cylB(b,0,0,0,.04,.04,.24,k.mat('#7fb3e6',.3));k.cylB(b,0,.24,0,.03,.03,.04,k.black);var bl=floorProp(k,'gym_ball','健身球',c.X(205),c.Z(200));k.sph(bl,0,.32,0,.32,.32,.32,k.mat('#c8abc2',.6));},
    阳台:function(k,c){var l=floorProp(k,'lantern','提灯',c.W-.3,c.D-.35);k.cylB(l,0,0,0,.08,.08,.02,k.brass);k.bx(l,0,.02,0,.14,.22,.14,k.glass);k.cylB(l,0,.05,0,.03,.03,.12,k.emissive('#ffe0a0',.3,2));k.cylB(l,0,.24,0,.09,.03,.05,k.brass);k.tor(l,0,.3,0,.03,.005,k.brass);plant(k,floorProp(k,'plant2','绿植',c.W-.3,c.D-.75),0,0,.8);k.pointLight(l,0,.16,0,'#ffd18a',0,1.2,2.5);},
    玄关:function(k,c){var mat=floorProp(k,'doormat','门垫',c.X(395),k.D-.5);k.bx(mat,0,0,0,1.3,.015,.75,k.material('#ffffff',.95,{map:k.tex.basket}),.006);
      var rn=floorProp(k,'runner','走廊地毯',c.X(250),k.D*.56);k.bx(rn,0,0,0,5.4,.012,1.15,k.fabric('#c9b18e'),.006);k.box(rn,0,.013,0,5.2,.004,.95,k.fabric('#e3d3b3'),.004).castShadow=false;
      var hooks=wallProp(k,'back','coat_hooks','挂衣钩',c.X(38),1.62);if(hooks){k.bx(hooks,0,0,.02,1.0,.08,.03,k.wood,.008);['#c8abc2','#7d8fa8','#d7b98d'].forEach(function(cl,i){var x=-.3+i*.3;k.sph(hooks,x,0,.06,.02,.02,.03,k.brass);k.bx(hooks,x,-.75,.08,.36,.72,.06,k.fabric(cl),.03);});}
      var mir=wallProp(k,'back','hall_mirror','穿衣镜',c.X(330),1.5);if(mir){k.box(mir,0,0,.02,.5,.8,.03,k.brass,.02);k.mirror(k.box(mir,0,0,.037,.44,.74,.004,k.material('#ffffff',.04,{metalness:1})));}
      [c.X(150),c.X(400),c.X(660)].forEach(function(x,i){pendant(k,'hall_light_'+i,'廊灯',x,k.D*.66,.5,{r:.14});});},
    衣帽间:function(k,c){var r=floorProp(k,'round_rug','圆地毯',c.X(100),c.Z(150));k.cylB(r,0,0,0,.7,.7,.012,k.fabric('#e9d7d0'));var o=floorProp(k,'ottoman','软凳',c.X(100),c.Z(150));k.cylB(o,0,0,0,.24,.24,.36,k.fabric('#c8abc2'));k.sph(o,0,.36,0,.23,.05,.23,k.fabric('#c8abc2'));pendant(k,'pendant','吊灯',c.X(100),c.Z(120),.7,{r:.2});},
    书房:function(k,c){var b=wallProp(k,'back','pinboard','软木板',c.X(222),1.55);if(b){k.box(b,0,0,.015,.6,.45,.03,k.mat('#c6a27a',1),.008);['#f7e2a4','#f2c9d2','#c9e1d6','#ffffff'].forEach(function(cl,i){var n=k.box(b,-.18+i*.12,(i%2)*.1-.03,.034,.1,.1,.002,k.mat(cl,.9));n.rotation.z=(i-1.5)*.1;});}
      var sh=wallProp(k,'right','wall_shelf','壁架',k.D*.35,1.6);if(sh){k.bx(sh,0,0,.12,.9,.03,.22,k.wood,.006);k.bx(sh,.15,.03,.12,.2,.2,.16,k.mat('#7d9a74',.7),.006);}
      },
    画室:function(k,c){[[c.X(60),1.65,.5,.6,13],[c.X(290),1.7,.6,.45,17]].forEach(function(p,i){var g=wallProp(k,'back','canvas_'+i,'画作',p[0],p[1]);if(g)frameArt(k,g,p[2],p[3],art(p[4],['#f3ead9','#94b3a1','#e8857a','#e3c27a','#5f7e9b']),{frame:k.lightWood});});
      var g2=wallProp(k,'right','canvas_r','画作',k.D*.4,1.5);if(g2)frameArt(k,g2,.9,.7,art(19,['#efe6d2','#c8abc2','#7fb3e6','#a8b89d']),{frame:k.lightWood});
      for(var i=0;i<3;i++){var cv=floorProp(k,'canvas_stack_'+i,'画布',k.W-.22-i*.05,c.D*.66,0);var t=k.box(cv,-.04,.38,0,.03,.7-i*.1,.55-i*.08,k.mat('#f8f4ea',.9),.004);t.rotation.z=-.12;var fr=k.box(cv,-.065,.38,0,.012,.7-i*.1,.55-i*.08,k.mat('#c9b08a',.8),.002);fr.rotation.z=-.12;}
      },
    影音室:function(k,c){['left','right'].forEach(function(side){var w=k.walls[side];if(!w)return;var g=k.prop(w,'acoustic_'+side,'吸音板');var O=((root.RoomModel||{}).openings||{})[k.room]||{},holes=(O[side==='right'?'E':'W']||[]).map(function(o){return side==='right'?[c.Z(o[0]),c.Z(o[1])]:[k.D-c.Z(o[1]),k.D-c.Z(o[0])];}),free=function(u,h){return !holes.some(function(r){return u+h>r[0]-.08&&u-h<r[1]+.08;});};for(var i=0;i<4;i++)for(var j=0;j<2;j++){var pu=.5+i*((k.D-1)/3.2);if(free(pu,.3))k.bx(g,pu,.9+j*.75,.03,.6,.62,.05,k.fabric(j?'#5b5270':'#6a5f86'),.02);}var sc=k.prop(w,'sconce_'+side,'壁灯');[k.D*.3,k.D*.7].filter(function(u){return free(u,.1);}).forEach(function(u){k.box(sc,u,2.1,.06,.16,.08,.1,k.emissive('#ffcf8d',.4,1.6),.03);k.pointLight(sc,u,2.0,.25,'#ffcf8d',.2,1.1,2.5);});});
      },
    露台:function(k,c){var g=k.prop(null,'string_lights','串灯');var bulbs=k.emissive('#fff0c0',.25,2.2);for(var i=0;i<12;i++){var x=.2+i*(k.W-.4)/11,y=2.2-Math.sin(i/11*PI)*.25;k.sph(g,x,y,k.D-.12,.03,.04,.03,bulbs).castShadow=false;}[.12,k.W-.12].forEach(function(x){k.cylB(g,x,0,k.D-.12,.03,.03,2.3,k.walnut);});for(var w=0;w<11;w++){var xa=.2+w*(k.W-.4)/11,xb=.2+(w+1)*(k.W-.4)/11,ya=2.2-Math.sin(w/11*PI)*.25,yb=2.2-Math.sin((w+1)/11*PI)*.25,seg=k.cyl(g,(xa+xb)/2,(ya+yb)/2+.03,k.D-.12,.003,.003,Math.hypot(xb-xa,yb-ya),k.black);seg.rotation.z=PI/2+Math.atan2(yb-ya,xb-xa);}
      plant(k,floorProp(k,'tree','盆栽树',k.W-.32,c.Z(170)),0,0,1.8,{leaves:16});var l=floorProp(k,'lantern','提灯',.3,k.D-.35);k.cylB(l,0,0,0,.09,.09,.02,k.black);k.bx(l,0,.02,0,.16,.26,.16,k.glass);k.cylB(l,0,.06,0,.035,.035,.14,k.emissive('#ffe0a0',.3,2));k.cylB(l,0,.28,0,.1,.04,.06,k.black);},
    楼梯厅:function(k,c){var g=wallProp(k,'back','hall_art','装饰画',c.X(322),1.6);if(g)frameArt(k,g,.9,.6,art(23,['#f1e7d3','#94b3a1','#c8abc2','#e3c27a']));var rn=floorProp(k,'runner','走廊地毯',c.X(290),k.D*.6);k.bx(rn,0,0,0,5.6,.012,1.15,k.fabric('#b6c4a1'),.006);k.box(rn,0,.013,0,5.4,.004,.95,k.fabric('#cfd8bd'),.004).castShadow=false;
      [c.X(130),c.X(400),c.X(720)].forEach(function(x,i){pendant(k,'hall_light_'+i,'廊灯',x,k.D*.66,.55,{r:.14});});}
  };
  function clock(k,g){var t=k.canvasTexture(function(c,w,h){c.fillStyle='#fbf5ea';c.fillRect(0,0,w,h);c.translate(w/2,h/2);c.fillStyle='#8e7a92';for(var i=0;i<12;i++){c.save();c.rotate(i*PI/6);c.fillRect(-2,-w*.42,4,i%3?10:18);c.restore();}c.strokeStyle='#5e5361';c.lineCap='round';c.lineWidth=6;c.beginPath();c.moveTo(0,0);c.lineTo(w*.18,-w*.12);c.stroke();c.lineWidth=4;c.beginPath();c.moveTo(0,0);c.lineTo(-w*.05,-w*.32);c.stroke();},256,256);
    k.tor(g,0,0,.05,.16,.022,k.brass);k.mesh(k.keep(new k.T.CircleGeometry(.16,40)),k.material('#ffffff',.7,{map:t}),g,0,0,.045,false);}
  function lighting(k,cfg){var n=k.night,out=k.outdoor;if(cfg.dark)return {sky:n?'#6f6a8f':'#bdb8d6',ground:'#3d3650',hemi:n?.7:1.1,sun:'#fff1d4',sunI:n?.2:.8,fill:n?.15:.35,ceiling:0};
    return {sky:n?'#a7b9df':'#fff4dc',ground:n?'#575069':'#a6ad94',hemi:n?.95:(out?2.3:1.9),sun:n?'#b4c8ef':k.env.band==='dusk'?'#ffd4a3':'#fff1d4',sunI:n?.6:(out?3.0:2.6),fill:n?.25:.75,ceiling:k.corridor?1.2:2.2};}
  // ---------------------------------------------------------------- installable shop goods (furniture slots, see FURNITURE-SLOTS.md)
  // Each builder draws in a pivot whose origin is the slot point on its supporting surface, front facing +z.
  function lathe(k,pts,seg){return k.keep(new k.T.LatheGeometry(pts.map(function(p){return new k.T.Vector2(p[0],p[1]);}),seg||24));}
  function rod(k,g,a,b,r,m){var T=k.T,A=new T.Vector3(a[0],a[1],a[2]),B=new T.Vector3(b[0],b[1],b[2]),d=B.clone().sub(A),c=k.cyl(g,(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2,r,r,d.length(),m,false,8);c.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return c;}
  var goodsModels={
    pillow:function(k,g,s){var c=s.color||'#c8b4cf',f=k.fabric(c),pv=k.group(g,0,.21,0);pv.rotation.x=1.2;k.mesh(k.pillow(.42,.17,.42),f,pv,0,0,0);k.sph(pv,0,.072,0,.022,.012,.022,k.fabric(s.trim||'#efe3c8'));k.sph(pv,0,-.072,0,.022,.012,.022,k.fabric(s.trim||'#efe3c8'));[[-1,-1],[1,-1],[-1,1],[1,1]].forEach(function(q){k.sph(pv,q[0]*.2,0,q[1]*.2,.022,.012,.022,f);});},
    cushion_cover:function(k,g,s){goodsModels.pillow(k,g,{color:'#a8b89d',trim:'#f6efe2'});},
    thin_blanket:function(k,g){var m=k.fabric('#c8b6cf');k.bx(g,0,0,0,.5,.06,.36,m,.03);k.bx(g,0,.06,-.02,.48,.05,.3,k.fabric('#d8cade'),.025);var d=k.box(g,0,-.08,.2,.5,.2,.02,m,.01);d.rotation.x=-.2;for(var i=0;i<6;i++)k.box(g,-.22+i*.088,-.19,.23,.008,.04,.008,k.fabric('#a995b3'));},
    plush_bear:function(k,g){var f=k.fabric('#d6b08a'),l=k.fabric('#f2e2c8');k.sph(g,0,.13,0,.13,.14,.11,f);k.sph(g,0,.31,0,.1,.1,.09,f);[-1,1].forEach(function(sd){k.sph(g,sd*.075,.39,0,.035,.035,.025,f);k.sph(g,sd*.13,.14,.03,.045,.06,.045,f);k.sph(g,sd*.07,.03,.07,.05,.04,.06,f);k.sph(g,sd*.035,.33,.083,.012,.012,.008,k.black);});k.sph(g,0,.29,.08,.04,.03,.025,l);k.sph(g,0,.3,.103,.012,.009,.008,k.black);k.box(g,0,.22,.075,.12,.03,.02,k.fabric('#e3a9a4'),.01);},
    diffuser:function(k,g){k.mesh(lathe(k,[[0,0],[.05,0],[.055,.08],[.03,.12],[.015,.13],[0,.13]]),k.material('#cfe3e6',.05,{transparent:true,opacity:.6}),g,0,0,0);k.cylB(g,0,0,0,.048,.048,.05,k.material('#e3c48a',.3,{transparent:true,opacity:.7}));for(var i=0;i<5;i++){var st=k.cyl(g,(i-2)*.008,.22,0,.002,.002,.2,k.mat('#3d3428',.7));st.rotation.z=(i-2)*.12;}},
    lamp:function(k,g){k.cylB(g,0,0,0,.14,.16,.03,k.black);k.cylB(g,0,.03,0,.012,.012,1.32,k.brass);k.mesh(lathe(k,[[.12,0],[.18,0],[.12,.24],[.09,.24]],28),k.material('#f3e3c3',.8,{side:k.T.DoubleSide,emissive:'#f3d6a0',emissiveIntensity:.15,lit:[.15,.9]}),g,0,1.18,0);k.sph(g,0,1.24,0,.045,.045,.045,k.emissive('#fff2d0',.3,1.6));k.pointLight(g,0,1.2,0,'#ffd9a0',0,1.1,4);},
    night_light:function(k,g){k.cylB(g,0,0,0,.05,.055,.03,k.mat('#f3eee6',.5));k.cylB(g,0,.03,0,.02,.02,.05,k.mat('#f3eee6',.5));k.mesh(lathe(k,[[0,0],[.07,0],[.07,.02],[.05,.06],[0,.075]],24),k.emissive('#fbe7b0',.25,1.5),g,0,.07,0);k.pointLight(g,0,.12,0,'#ffd9a0',0,.5,2);},
    candle:function(k,g,s){var m=k.material(s&&s.glass||'#e3d2b8',.1,{transparent:true,opacity:.75});k.cylB(g,0,0,0,.05,.05,.09,m);k.cylB(g,0,.005,0,.045,.045,.06,k.mat('#f6efe2',.7));k.cyl(g,0,.075,0,.002,.002,.012,k.black);k.sph(g,0,.09,0,.008,.016,.008,k.emissive('#ffcf7a',.6,2));k.pointLight(g,0,.12,0,'#ffc77a',0,.45,1.6);},
    scented_candle:function(k,g){goodsModels.candle(k,g,{glass:'#c9b4cf'});k.box(g,0,.045,.051,.05,.03,.002,k.mat('#f6efe2',.6));},
    perfume:function(k,g){k.box(g,0,.055,0,.07,.1,.04,k.material('#f3d6dc',.05,{transparent:true,opacity:.75}),.012);k.cylB(g,0,.105,0,.012,.012,.02,k.brass);k.box(g,0,.135,0,.035,.03,.035,k.brass,.008);k.box(g,0,.05,.021,.04,.03,.002,k.mat('#fbf8f1',.6));},
    music_box:function(k,g){var w=k.walnut||k.mat('#8a6a4b',.6);k.bx(g,0,0,0,.18,.08,.12,w,.01);var lid=k.group(g,0,.08,-.06);lid.rotation.x=-1.1;k.bx(lid,0,0,.06,.18,.015,.12,w,.006);k.box(lid,0,.016,.06,.15,.002,.09,k.material('#d8e3e8',.05,{metalness:.9}));k.cylB(g,.02,.08,.0,.03,.03,.01,k.mat('#c8786a',.5));k.cylB(g,.02,.09,0,.004,.004,.05,k.brass);k.sph(g,.02,.15,0,.012,.02,.012,k.mat('#f3eee6',.5));k.cyl(g,.1,.04,0,.006,.006,.03,k.brass).rotation.z=Math.PI/2;},
    music_box_gift:function(k,g){goodsModels.music_box(k,g);k.box(g,0,.04,.061,.02,.08,.002,k.mat('#e86a7a',.6));},
    vase:function(k,g){k.mesh(lathe(k,[[0,0],[.06,0],[.09,.08],[.07,.2],[.04,.24],[.05,.27],[0,.27]],28),k.mat('#9cbcd0',.35),g,0,0,0);[[0,-.1],[.05,.25],[-.05,-.3]].forEach(function(q){var st=k.cyl(g,q[0]*.6,.36,0,.003,.003,.22,k.mat('#6f9468',.7));st.rotation.z=q[1];k.sph(g,q[0]*1.6,.47,0,.03,.025,.03,k.mat(q[0]?'#f3d6dc':'#f6efe2',.7));});},
    flowers:function(k,g){k.mesh(lathe(k,[[0,0],[.07,0],[.08,.14],[.06,.18],[0,.18]],24),k.material('#dfeef0',.05,{transparent:true,opacity:.55}),g,0,0,0);var cols=['#e8a3a8','#f3d36b','#f6efe2','#c8b6cf','#e86a5a'];for(var i=0;i<9;i++){var a=i*2.4,r=i?.045+.02*(i%2):0,st=k.cyl(g,Math.cos(a)*r*.5,.25,Math.sin(a)*r*.5,.003,.003,.18,k.mat('#6f9468',.7));st.rotation.set(Math.sin(a)*.25,0,Math.cos(a)*.25);k.sph(g,Math.cos(a)*r*1.6,.35+(i%3)*.02,Math.sin(a)*r*1.6,.035,.03,.035,k.mat(cols[i%5],.7));}for(var j=0;j<4;j++)k.sph(g,Math.cos(j*1.6)*.07,.3,Math.sin(j*1.6)*.07,.04,.015,.025,k.mat('#8fae84',.8));},
    bouquet:function(k,g){goodsModels.flowers(k,g);k.box(g,0,.13,.075,.1,.03,.004,k.mat('#e3a9a4',.6));},
    plant:function(k,g){k.mesh(lathe(k,[[0,0],[.11,0],[.15,.28],[.16,.3],[0,.3]],24),k.mat('#d9a37e',.8),g,0,0,0);k.cylB(g,0,.27,0,.145,.145,.02,k.mat('#5e4a3a',.95));for(var i=0;i<9;i++){var lf=k.sph(g,Math.cos(i*.7)*.07,.45+(i%3)*.12,Math.sin(i*.7)*.07,.07,.13,.025,k.mat(i%2?'#8fae84':'#6f9468',.8));lf.rotation.set(Math.sin(i)*.5,i*.7,Math.cos(i)*.4);}},
    plant_pot:function(k,g){k.mesh(lathe(k,[[0,0],[.12,0],[.15,.24],[.17,.26],[.16,.27],[0,.27]],28),k.mat('#ece5d8',.4),g,0,0,0);k.cylB(g,0,.24,0,.15,.15,.02,k.mat('#5e4a3a',.95));for(var i=0;i<5;i++){var a=i*1.25;k.sph(g,Math.cos(a)*.05,.33+(i%2)*.04,Math.sin(a)*.05,.05,.05,.05,k.mat('#a5c39a',.8));}},
    rug:function(k,g){var m=k.material('#d8c3a5',.95);k.box(g,0,.004,0,1.0,.008,.7,m,.004).castShadow=false;k.box(g,0,.0085,0,.86,.002,.56,k.material('#b9a283',.95)).castShadow=false;k.box(g,0,.009,0,.7,.002,.4,k.material('#e8d9bf',.95)).castShadow=false;},
    bath_mat:function(k,g){k.box(g,0,.006,0,.7,.012,.45,k.material('#b7d6d0',1),.006).castShadow=false;for(var i=0;i<7;i++)k.box(g,-.3+i*.1,.0125,0,.04,.002,.4,k.material('#d5ebe6',1)).castShadow=false;},
    towel:function(k,g){goodsModels.bath_mat(k,g);var t=k.fabric('#f0c9cf');k.bx(g,.15,.012,-.05,.3,.05,.2,t,.02);k.bx(g,.15,.062,-.05,.28,.045,.18,k.fabric('#9cbcd0'),.02);},
    storage_box:function(k,g){var c=k.material('#dfe6ea',.3,{transparent:true,opacity:.78}),lid=k.mat('#9cbcd0',.5),dk=k.mat('#7d9aab',.5);
      k.bx(g,0,0,0,.4,.012,.3,c,.004);[-1,1].forEach(function(sd){k.box(g,sd*.2,.145,0,.012,.27,.3,c);k.box(g,0,.145,sd*.15,.4,.27,.012,c);k.box(g,sd*.207,.24,0,.006,.035,.1,dk,.003);k.bx(g,sd*.212,.27,0,.016,.05,.05,lid,.004);});
      k.bx(g,0,.28,0,.43,.035,.33,lid,.012);k.bx(g,0,.315,0,.36,.008,.26,k.mat('#b4cedc',.5),.004);k.box(g,0,.17,.157,.12,.06,.002,k.mat('#fbf8f1',.6));
      [['#c8b6cf',.02],['#a8b89d',.08],['#e3a9a4',.14]].forEach(function(q){k.bx(g,0,q[1]-.008,0,.34,.055,.24,k.fabric(q[0]),.02);});},
    storage_basket:function(k,g){var w=k.mat('#c9a57c',.9);k.mesh(lathe(k,[[0,0],[.18,0],[.2,.26],[.21,.27],[0,.27]],24),w,g,0,0,0);for(var i=0;i<4;i++)k.tor(g,0,.05+i*.06,0,.185+i*.006,.006,k.mat('#a98560',.9)).rotation.x=Math.PI/2;[-1,1].forEach(function(sd){var h=k.tor(g,sd*.2,.27,0,.04,.008,k.mat('#a98560',.9),Math.PI);h.rotation.y=Math.PI/2;});k.sph(g,0,.27,0,.12,.05,.1,k.fabric('#a8b89d'));},
    humidifier:function(k,g){k.mesh(lathe(k,[[0,0],[.1,0],[.11,.06],[.09,.3],[.04,.34],[0,.34]],28),k.mat('#f3eee6',.4),g,0,0,0);k.cylB(g,0,.08,0,.104,.104,.16,k.material('#cfe3e6',.05,{transparent:true,opacity:.55}));k.cylB(g,0,.34,0,.015,.015,.02,k.mat('#c9d0d4',.4));k.box(g,0,.04,.1,.04,.012,.004,k.emissive('#7fd18e',.6,1.2));for(var i=0;i<3;i++){var m=k.sph(g,(i-1)*.02,.42+i*.06,0,.04+i*.015,.03+i*.01,.04+i*.015,k.material('#ffffff',.9,{transparent:true,opacity:.25-i*.06,depthWrite:false}));m.castShadow=false;}},
    guitar:function(k,g){var T=k.T,spruce=k.mat('#e2b679',.42),side=k.mat('#8f5a34',.5),dark=k.mat('#2a2420',.5),neckM=k.mat('#6e4a30',.55),fret=k.mat('#d9d4cc',.25,.8),stand=k.mat('#2b2b2e',.45,.3),pad=k.mat('#3a3a3d',.9);
      // A-frame stand: two splayed front legs + one rear leg meeting at a hub, cradle arms in front, padded back rest.
      rod(k,g,[-.15,0,.12],[0,.36,-.1],.011,stand);rod(k,g,[.15,0,.12],[0,.36,-.1],.011,stand);rod(k,g,[0,0,-.26],[0,.36,-.1],.011,stand);
      [-1,1].forEach(function(sd){rod(k,g,[sd*.02,.13,-.02],[sd*.1,.11,.09],.009,stand);rod(k,g,[sd*.1,.11,.09],[sd*.11,.16,.11],.009,stand);k.sph(g,sd*.11,.165,.112,.016,.016,.016,pad);k.sph(g,sd*.15,.006,.12,.018,.008,.018,pad);});
      rod(k,g,[0,.11,-.02],[0,.13,-.02],.012,stand);k.sph(g,0,.006,-.26,.018,.008,.018,pad);var rest=k.cyl(g,0,.37,-.1,.022,.022,.09,pad);rest.rotation.z=Math.PI/2;
      // Guitar leans back ~12deg; its local y runs bottom->headstock, +z is the soundboard.
      var gt=k.group(g,0,.135,.075);gt.rotation.x=-.21;
      var sh=new T.Shape(),pts=[],N=40;for(var i=0;i<=N;i++){var y=i/N*.5,w1=y<.38?Math.sqrt(Math.max(0,.0361-(y-.19)*(y-.19))):0,w2=y>.24?Math.sqrt(Math.max(0,.0196-(y-.36)*(y-.36))):0,w=Math.max(w1,w2,y>.22&&y<.33?.118:0);pts.push([w,y]);}
      pts.forEach(function(q,i){if(i)sh.lineTo(q[0],q[1]);else sh.moveTo(q[0],q[1]);});for(var r=pts.length-1;r>=0;r--)sh.lineTo(-pts[r][0],pts[r][1]);
      var bodyG=k.keep(new T.ExtrudeGeometry(sh,{depth:.085,bevelEnabled:true,bevelThickness:.006,bevelSize:.006,bevelSegments:2,curveSegments:4}));bodyG.translate(0,0,-.0425);
      k.mesh(bodyG,[spruce,side],gt,0,0,0);
      var back=k.mesh(k.keep(new T.ShapeGeometry(sh)),side,gt,0,0,-.049);back.rotation.y=Math.PI;back.scale.x=-1;
      k.mesh(k.keep(new T.CircleGeometry(.04,28)),dark,gt,0,.33,.0495);var ros=k.tor(gt,0,.33,.049,.047,.004,k.mat('#5b3b26',.5));
      k.bx(gt,0,.105,.049,.13,.012,.012,k.mat('#3b2a1e',.5),.004);k.bx(gt,0,.112,.058,.075,.004,.004,k.mat('#f1ead8',.4));
      var pg=k.mesh(k.keep(new T.CircleGeometry(.045,20,0,Math.PI*.9)),k.mat('#4a2e20',.4),gt,.045,.27,.0496);pg.rotation.z=-1.1;
      k.bx(gt,0,.49,.03,.05,.42,.025,neckM,.008);k.box(gt,0,.7,.044,.048,.42,.004,k.mat('#33241a',.5));for(var f=0;f<12;f++)k.box(gt,0,.505+f*.032*(1-f*.03),.0465,.048,.002,.002,fret);
      [.6,.66,.72].forEach(function(y){k.sph(gt,0,y,.0465,.004,.004,.002,k.mat('#efe9da',.4));});
      var head=k.group(gt,0,.92,.03);head.rotation.x=-.18;k.bx(head,0,0,0,.075,.16,.02,neckM,.01);k.box(head,0,.08,.011,.075,.16,.002,dark);
      for(var t=0;t<3;t++)[-1,1].forEach(function(sd){var pe=k.cyl(head,sd*.05,.04+t*.045,0,.004,.004,.03,k.chrome);pe.rotation.z=Math.PI/2;k.box(head,sd*.068,.04+t*.045,0,.01,.016,.006,k.mat('#efe9da',.4),.003);});
      k.box(gt,0,.92,.046,.05,.004,.006,k.mat('#f1ead8',.4));
      for(var c=0;c<6;c++){var x=-.018+c*.0072;rod(k,gt,[x*1.6,.112,.061],[x,.92,.05],.0007+(5-c)*.00012,k.mat('#d9d4cc',.3,.8));}
    },
    model_kit:function(k,g){var w=k.mat('#e9ecef',.5),b=k.mat('#7fb3e6',.5),r=k.mat('#c8564a',.5);k.cylB(g,0,0,0,.06,.07,.015,k.black);k.bx(g,-.025,.015,0,.025,.07,.03,w,.005);k.bx(g,.025,.015,0,.025,.07,.03,w,.005);k.bx(g,0,.085,0,.08,.08,.05,b,.01);k.bx(g,0,.165,0,.05,.045,.045,w,.01);k.box(g,0,.19,.024,.035,.012,.002,k.emissive('#7fd1e8',.5,1.2));[-1,1].forEach(function(sd){k.bx(g,sd*.055,.09,0,.022,.065,.025,r,.005);});k.cyl(g,.02,.23,0,.003,.003,.04,k.black);},
    journal:function(k,g){k.bx(g,0,0,0,.15,.022,.21,k.mat('#a8b89d',.7),.005);k.bx(g,.003,.002,0,.14,.018,.2,k.mat('#f6efe2',.7));k.box(g,.05,.011,0,.012,.024,.212,k.mat('#c8786a',.6));k.cyl(g,-.078,.012,-.04,.004,.004,.025,k.brass).rotation.x=Math.PI/2;},
    sketchbook:function(k,g){k.bx(g,0,0,0,.24,.018,.17,k.mat('#5f6f66',.7),.004);for(var i=0;i<9;i++)k.tor(g,-.115,.01,-.07+i*.018,.008,.0018,k.chrome).rotation.y=Math.PI/2;var p=k.cyl(g,.04,.025,.11,.004,.004,.16,k.mat('#e8c27a',.6));p.rotation.set(Math.PI/2,0,.4);},
    washi_tape:function(k,g){['#e3a9a4','#9cbcd0','#f3d36b'].forEach(function(c,i){var t=k.tor(g,-.06+i*.06,.02,(i%2)*.03,.025,.012,k.mat(c,.6));t.rotation.x=Math.PI/2;});},
    instant_film:function(k,g){k.bx(g,0,0,0,.1,.03,.08,k.mat('#2f3438',.5),.006);for(var i=0;i<3;i++){var ph=k.box(g,.06+i*.035,.004+i*.002,.04-i*.01,.054,.003,.066,k.mat('#fbfaf5',.6),.002);ph.rotation.y=.3-i*.25;k.box(ph,0,.002,-.006,.046,.001,.045,k.mat(['#9cc1c9','#e3c4c0','#c8d6b4'][i],.6));}},
    guitar_strings:function(k,g){k.bx(g,0,0,0,.12,.008,.12,k.mat('#3d4a55',.5),.004);k.tor(g,0,.012,0,.035,.002,k.brass).rotation.x=Math.PI/2;k.tor(g,0,.012,0,.025,.0015,k.mat('#d9c08a',.3,.6)).rotation.x=Math.PI/2;},
    paint_set:function(k,g){k.cylB(g,-.05,0,0,.035,.03,.1,k.mat('#f6efe2',.6));['#c8564a','#5f7e9b','#e8c27a','#7d8f78'].forEach(function(c,i){var b=k.cyl(g,-.05+(i-1.5)*.01,.15,0,.004,.004,.14,k.mat('#b08a63',.6));b.rotation.z=(i-1.5)*.12;k.sph(g,-.05+(i-1.5)*.02,.22,0,.007,.012,.007,k.mat(c,.6));});var pal=k.mesh(k.keep(new k.T.CircleGeometry(.09,24)),k.mat('#e8d6b4',.6),g,.07,.004,.02);pal.rotation.x=-Math.PI/2;['#c8564a','#5f7e9b','#e8c27a','#7d8f78','#f3eee6'].forEach(function(c,i){k.sph(g,.07+Math.cos(i*1.2)*.05,.008,.02+Math.sin(i*1.2)*.05,.014,.005,.014,k.mat(c,.5));});},
    paint:function(k,g){k.bx(g,0,0,0,.2,.018,.09,k.mat('#3d4a55',.4,.4),.004);var lid=k.box(g,0,.05,-.045,.2,.09,.004,k.mat('#3d4a55',.4,.4));lid.rotation.x=-.3;for(var i=0;i<12;i++)k.bx(g,-.085+(i%6)*.034,.018,-.02+Math.floor(i/6)*.04,.026,.004,.03,k.mat(['#c8564a','#e8857a','#f2c14e','#7d8f78','#5f7e9b','#a86d8b'][i%6],.6));},
    puzzle:function(k,g){var c=['#9cbcd0','#e3a9a4','#f3d36b','#a8b89d','#c8b6cf'];k.bx(g,0,0,0,.4,.006,.3,k.mat('#efe6d3',.8));for(var i=0;i<8;i++)for(var j=0;j<6;j++)if((i*7+j*3)%9)k.bx(g,-.175+i*.05,.006,-.125+j*.05,.046,.004,.046,k.mat(c[(i+j*2)%5],.7));k.bx(g,.28,0,.05,.18,.05,.14,k.mat('#5f7e9b',.6),.006);},
    puzzle_500:function(k,g){goodsModels.puzzle(k,g);},
    board_game:function(k,g){k.bx(g,0,0,0,.4,.008,.4,k.mat('#f6efe2',.6),.004);for(var i=0;i<4;i++)k.box(g,0,.009,0,.36-i*.08,.002,.36-i*.08,k.mat(['#9cbcd0','#e3a9a4','#a8b89d','#f3d36b'][i],.6));['#c8564a','#5f7e9b','#f2c14e'].forEach(function(c,i){k.cylB(g,-.12+i*.12,.01,.1,.015,.02,.04,k.mat(c,.5));k.sph(g,-.12+i*.12,.06,.1,.014,.014,.014,k.mat(c,.5));});k.bx(g,.14,.01,-.12,.04,.04,.04,k.mat('#fbfaf5',.4),.008);},
    yarn:function(k,g){var w=k.mat('#c9a57c',.9);k.mesh(lathe(k,[[0,0],[.12,0],[.15,.1],[.15,.11],[0,.11]],24),w,g,0,0,0);['#c8b6cf','#9cbcd0','#e3a9a4'].forEach(function(c,i){k.sph(g,-.05+i*.05,.13+(i%2)*.02,(i%2)*.03,.055,.055,.055,k.fabric(c));});var n=k.cyl(g,.06,.2,0,.004,.004,.24,k.mat('#b08a63',.6));n.rotation.z=.6;},
    tablecloth:function(k,g){var c=k.fabric('#f2ede1',true);k.box(g,0,.003,0,.8,.006,.5,c).castShadow=false;[-1,1].forEach(function(sd){var d=k.box(g,0,-.07,sd*.25,.8,.14,.006,c);d.castShadow=false;});for(var i=0;i<5;i++)k.box(g,-.32+i*.16,.007,0,.03,.002,.5,k.mat('#e3a9a4',.8)).castShadow=false;}
  };
  // ---- second wave: tech, wearables and keepsakes (hang = drawn downward from the hook point)
  var HANG={tshirt:1,hoodie:1,skirt:1,long_skirt:1,jeans:1,pajamas:1,cardigan:1,coat:1,trench_coat:1,scarf:1,cap:1,beret:1};
  function hanger(k,g){var w=k.walnut||k.mat('#8a6a4b',.6);k.tor(g,0,.012,.07,.016,.003,k.chrome,Math.PI*1.3).rotation.z=-.3;rod(k,g,[0,0,.07],[0,-.035,.07],.003,k.chrome);rod(k,g,[0,-.035,.07],[-.2,-.075,.07],.009,w);rod(k,g,[0,-.035,.07],[.2,-.075,.07],.009,w);k.sph(g,-.2,-.075,.07,.01,.01,.01,w);k.sph(g,.2,-.075,.07,.01,.01,.01,w);}
  function peg(k,g){var w=k.walnut||k.mat('#8a6a4b',.6);var c=k.cyl(g,0,0,.03,.008,.01,.06,w);c.rotation.x=Math.PI/2;k.sph(g,0,.004,.062,.014,.014,.012,w);}
  function shirt(k,g,col,len,sleeve,opts){opts=opts||{};var f=k.fabric(col);k.box(g,0,-.075-len/2,.07,.42,len,.05,f,.02);[-1,1].forEach(function(sd){var s=k.box(g,sd*.25,-.13-sleeve/2,.07,.12,sleeve,.045,f,.03);s.rotation.z=sd*.32;});if(opts.hood){k.sph(g,0,-.1,.04,.13,.07,.035,f);k.sph(g,0,-.085,.09,.06,.025,.012,k.fabric('#93a68a'));[-1,1].forEach(function(sd){k.cyl(g,sd*.03,-.15,.098,.003,.003,.1,k.fabric('#f2ede1'));});}if(opts.placket){k.box(g,0,-.07-len/2,.096,.012,len-.02,.004,k.fabric(opts.placket));for(var i=0;i<4;i++)k.sph(g,.025,-.15-i*len/5,.1,.009,.009,.004,k.brass);}if(opts.belt){k.box(g,0,-.07-len*.42,.097,.44,.04,.006,k.fabric(opts.belt));}if(opts.pocket)k.box(g,0,-.07-len*.68,.097,.22,.1,.004,k.fabric(opts.pocket));}
  var goodsModels2={
    tshirt:function(k,g){hanger(k,g);shirt(k,g,'#f2ede1',.5,.16,{pocket:'#e3d6c0'});},
    hoodie:function(k,g){hanger(k,g);shirt(k,g,'#a8b89d',.55,.4,{hood:true,pocket:'#93a68a'});},
    cardigan:function(k,g){hanger(k,g);shirt(k,g,'#c8b6cf',.55,.42,{placket:'#b19fbd'});},
    coat:function(k,g){hanger(k,g);shirt(k,g,'#9cb3c9',.72,.5,{placket:'#86a0b8'});},
    trench_coat:function(k,g){hanger(k,g);shirt(k,g,'#d4b98a',.95,.55,{placket:'#c2a574',belt:'#b8996a'});},
    pajamas:function(k,g){hanger(k,g);shirt(k,g,'#c9d6e8',.42,.38,{placket:'#f6efe2'});[-1,1].forEach(function(sd){k.box(k.group(g,0,0,0),sd*.1,-.62,.04,.16,.42,.04,k.fabric('#c9d6e8'),.02);});},
    skirt:function(k,g){hanger(k,g);k.box(g,0,-.12,.07,.36,.02,.03,k.chrome);k.mesh(lathe(k,[[.15,0],[.28,-.48],[0,-.48]],24),k.fabric('#e3a9a4',true),g,0,-.13,.07).scale.set(1,1,.25);},
    long_skirt:function(k,g){hanger(k,g);k.box(g,0,-.12,.07,.36,.02,.03,k.chrome);k.mesh(lathe(k,[[.14,0],[.3,-.85],[0,-.85]],24),k.fabric('#9cb3c9',true),g,0,-.13,.07).scale.set(1,1,.25);},
    jeans:function(k,g){hanger(k,g);var j=k.fabric('#6f8fb3');k.box(g,0,-.16,.07,.36,.06,.04,j,.01);[-1,1].forEach(function(sd){var l=k.box(g,sd*.085,-.55,.07,.16,.78,.045,j,.02);l.rotation.z=-sd*.03;});k.box(g,0,-.2,.094,.36,.006,.004,k.fabric('#c9d6e4'));},
    scarf:function(k,g){peg(k,g);var f=k.fabric('#c8786a');[-1,1].forEach(function(sd){k.box(g,sd*.07,-.32,.07,.13,.62,.025,f,.02);for(var i=0;i<5;i++)k.box(g,sd*.07-.05+i*.025,-.66,.07,.006,.06,.006,f);});k.box(g,0,-.03,.06,.24,.08,.05,f,.03);[-.2,-.4].forEach(function(y){[-1,1].forEach(function(sd){k.box(g,sd*.07,y,.084,.13,.02,.002,k.fabric('#f2ede1'));});});},
    cap:function(k,g){peg(k,g);var c=k.fabric('#5f7e9b'),cr=k.group(g,0,-.1,.075);k.sph(cr,0,0,0,.095,.09,.06,c);k.sph(cr,0,.088,0,.014,.008,.012,k.fabric('#4d6a86'));for(var i=0;i<3;i++){var sm=k.box(cr,(i-1)*.045,0,.056,.003,.17,.003,k.fabric('#4d6a86'));sm.rotation.z=(i-1)*.45;}var b=k.box(cr,0,-.1,.04,.15,.012,.1,k.fabric('#4d6a86'),.004);b.rotation.x=-.9;k.box(cr,0,.03,.058,.035,.02,.002,k.fabric('#f2ede1'));},
    beret:function(k,g){peg(k,g);var c=k.fabric('#c8786a'),b=k.group(g,0,-.11,.07);b.rotation.z=.18;k.sph(b,0,0,0,.13,.12,.035,c);k.tor(b,0,-.0,-.01,.085,.012,k.fabric('#a85c52'));k.cyl(b,0,.122,0,.006,.004,.025,k.fabric('#a85c52'));},
    sneakers:function(k,g,s){var col=s&&s.color||'#f2ede1',sole=k.mat('#fbfaf5',.7);[-1,1].forEach(function(sd){var sh=k.group(g,sd*.075,0,sd*.02);sh.rotation.y=sd*.08;k.bx(sh,0,0,0,.1,.03,.27,sole,.012);k.box(sh,0,.06,-.03,.095,.07,.2,k.fabric(col),.03);k.box(sh,0,.05,.09,.09,.045,.08,k.fabric(col),.03);for(var i=0;i<3;i++)k.box(sh,0,.098-i*.008,.0+i*.03,.05,.004,.008,k.mat('#f6f6f2',.6));k.box(sh,0,.04,-.135,.07,.06,.012,k.fabric(s&&s.trim||'#9bb3a8'),.004);});},
    canvas_shoes:function(k,g){goodsModels2.sneakers(k,g,{color:'#9cb3c9',trim:'#f2ede1'});},
    indoor_slippers:function(k,g){var sole=k.mat('#e6efe1',.9),top=k.fabric('#c8d6c2');[-1,1].forEach(function(sd){var sh=k.group(g,sd*.075,0,0);sh.rotation.y=sd*.06;k.bx(sh,0,0,0,.095,.022,.25,sole,.01);k.bx(sh,0,.022,0,.088,.006,.24,k.fabric('#f4efe4'),.003);k.sph(sh,0,.03,.055,.05,.034,.065,top);k.box(sh,0,.024,.055,.1,.012,.12,top,.005);});},
    bracelet:function(k,g){k.bx(g,0,0,0,.16,.012,.1,k.mat('#efe6d3',.6),.01);var r=k.tor(g,0,.02,0,.035,.006,k.mat('#e2b65e',.3,.7));r.rotation.x=Math.PI/2;for(var i=0;i<8;i++){var a=i/8*Math.PI*2;k.sph(g,Math.cos(a)*.035,.02,Math.sin(a)*.035,.008,.008,.008,k.mat(['#c8b6cf','#9cbcd0','#f3d6dc'][i%3],.3));}},
    bracelet_gift:function(k,g){goodsModels2.bracelet(k,g);k.bx(g,.05,.012,.02,.04,.03,.04,k.mat('#e86a7a',.6),.006);},
    earrings:function(k,g){k.bx(g,0,0,0,.12,.012,.08,k.mat('#efe6d3',.6),.01);[-1,1].forEach(function(sd){k.tor(g,sd*.025,.03,0,.012,.002,k.mat('#e2b65e',.3,.7));k.sph(g,sd*.025,.012,0,.008,.012,.008,k.mat('#9cbcd0',.2));});},
    necklace:function(k,g){var b=k.mat('#efe6d3',.5);k.cylB(g,0,0,0,.04,.05,.02,b);k.cylB(g,0,.02,0,.01,.012,.14,b);var bust=k.sph(g,0,.18,0,.06,.07,.035,k.mat('#3b3b46',.6));var c=k.tor(g,0,.17,.03,.045,.002,k.mat('#e2b65e',.3,.7),Math.PI);c.rotation.z=Math.PI;k.sph(g,0,.125,.04,.008,.012,.006,k.mat('#9cbcd0',.2));},
    smart_watch:function(k,g){k.bx(g,0,0,0,.06,.06,.04,k.mat('#efe6d3',.6),.01);var w=k.group(g,0,.07,0);k.bx(w,0,0,0,.035,.04,.012,k.mat('#2f3438',.4),.006);k.box(w,0,.02,.007,.026,.03,.002,k.material('#1c2a33',.3,{emissive:'#7fd18e',emissiveIntensity:.3,lit:[.3,.8]}));k.box(w,0,-.035,0,.02,.03,.008,k.mat('#3d454c',.6));},
    handwritten_card:function(k,g){var a=k.box(g,0,.05,-.02,.12,.1,.003,k.mat('#f2ede1',.7));a.rotation.x=-.35;var b=k.box(g,0,.05,.02,.12,.1,.003,k.mat('#fbfaf5',.7));b.rotation.x=.35;k.box(g,0,.06,.04,.04,.03,.002,k.mat('#e86a7a',.6)).rotation.x=.35;},
    headphones:function(k,g){k.cylB(g,0,0,0,.05,.06,.02,k.walnut||k.mat('#8a6a4b',.6));k.cylB(g,0,.02,0,.008,.008,.22,k.walnut||k.mat('#8a6a4b',.6));var hb=k.tor(g,0,.2,0,.075,.012,k.mat('#3b3d42',.5),Math.PI);[-1,1].forEach(function(sd){var cup=k.cyl(g,sd*.08,.18,0,.04,.04,.03,k.mat('#c8b6cf',.5));cup.rotation.z=Math.PI/2;});},
    camera:function(k,g){k.bx(g,0,0,0,.13,.08,.06,k.mat('#3b3d42',.5),.01);k.bx(g,-.03,.08,0,.03,.015,.03,k.mat('#3b3d42',.5));var l=k.cyl(g,.01,.04,.045,.028,.03,.04,k.mat('#2b2e33',.4));l.rotation.x=Math.PI/2;k.cyl(g,.01,.04,.066,.02,.02,.004,k.material('#5b7d9a',.1,{metalness:.6})).rotation.x=Math.PI/2;k.box(g,.045,.085,0,.02,.01,.02,k.mat('#c8564a',.5));},
    keyboard:function(k,g){k.bx(g,0,0,0,.36,.02,.12,k.mat('#e9ecef',.5),.006);var kb=k.batch(g,k.mat('#c9ced4',.5));for(var r=0;r<4;r++)for(var c=0;c<14;c++)kb.box(-.16+c*.0245,.026,-.042+r*.027,.02,.008,.021);kb.done();k.box(g,-.16,.03,-.042,.02,.01,.021,k.mat('#e8857a',.5));},
    wireless_mouse:function(k,g){var m=k.sph(g,0,.012,0,.03,.022,.05,k.mat('#e9ecef',.4));k.box(g,0,.03,-.02,.002,.006,.03,k.mat('#3b3d42',.5));k.bx(g,0,0,0,.14,.003,.12,k.mat('#3b4a55',.8));},
    game_pad:function(k,g){var c=k.group(g,0,.02,0);k.box(c,0,0,0,.14,.03,.06,k.mat('#5c6670',.5),.015);[-1,1].forEach(function(sd){k.sph(c,sd*.06,-.002,.025,.03,.02,.04,k.mat('#5c6670',.5));});k.sph(c,-.03,.017,0,.01,.006,.01,k.mat('#3d454c',.5));[['#e8857a',.045,-.01],['#7fb3e6',.055,.0],['#f3d36b',.035,0],['#91ac8b',.045,.01]].forEach(function(b){k.sph(c,b[1],.017,b[2],.005,.004,.005,k.mat(b[0],.4));});},
    console:function(k,g){k.bx(g,0,0,0,.26,.05,.18,k.mat('#e9ecef',.4),.01);k.box(g,0,.026,.0,.24,.002,.16,k.mat('#d7dce0',.5));k.box(g,.1,.025,.091,.02,.006,.002,k.emissive('#7fb3e6',.5,1.2));goodsModels2.game_pad(k,k.group(g,-.03,.05,.0));},
    speaker:function(k,g){k.cylB(g,0,0,0,.05,.05,.17,k.fabric('#7d8f78'));k.cylB(g,0,.17,0,.051,.051,.012,k.mat('#3b3d42',.5));k.box(g,0,.12,.05,.02,.02,.002,k.emissive('#7fd18e',.4,1));},
    tablet:function(k,g){k.bx(g,0,0,-.02,.1,.01,.08,k.mat('#c9ced4',.4,.4),.004);var t=k.group(g,0,.01,0);t.rotation.x=-.3;k.bx(t,0,0,0,.22,.16,.012,k.mat('#2f3438',.4),.01);k.box(t,0,.08,.0065,.2,.14,.002,k.material('#1c2a33',.3,{emissive:'#88a49c',emissiveIntensity:.35,lit:[.35,.8]}));},
    powerbank:function(k,g){k.bx(g,0,0,0,.07,.022,.13,k.mat('#e9ecef',.4),.008);for(var i=0;i<4;i++)k.box(g,-.02+i*.013,.023,.05,.007,.002,.004,k.emissive('#7fd18e',.4,1));},
    hard_drive:function(k,g){k.bx(g,0,0,0,.09,.02,.12,k.mat('#3d4a55',.4,.3),.008);k.box(g,0,.021,.04,.006,.002,.006,k.emissive('#7fb3e6',.5,1.2));},
    charging_pad:function(k,g){k.cylB(g,0,0,0,.05,.05,.01,k.mat('#3d454c',.5));k.bx(g,0,.01,0,.07,.008,.14,k.mat('#e9ecef',.4),.008);k.box(g,0,.019,0,.06,.001,.12,k.material('#1c2a33',.3,{emissive:'#88a49c',emissiveIntensity:.2,lit:[.2,.5]}));},
    webcam:function(k,g){[-1,0,1].forEach(function(i){var l=k.cyl(g,i*.02,.05,i?0:-.02,.003,.003,.1,k.black);l.rotation.z=i*.3;if(!i)l.rotation.x=.3;});var h=k.group(g,0,.11,0);k.sph(h,0,0,0,.035,.035,.03,k.mat('#e9ecef',.4));k.cyl(h,0,0,.028,.016,.016,.006,k.mat('#2b2e33',.4)).rotation.x=Math.PI/2;},
    monitor_arm:function(k,g){var d=k.mat('#3b3d42',.4,.4);k.bx(g,0,0,0,.08,.04,.08,d,.01);k.cylB(g,0,.04,0,.012,.012,.3,d);var a=k.box(g,.1,.34,0,.22,.025,.025,d,.008);a.rotation.z=.25;var m=k.group(g,.22,.38,.02);k.bx(m,0,0,0,.28,.18,.015,k.mat('#2f3438',.4),.008);k.box(m,0,.09,.008,.26,.16,.002,k.material('#1c2a33',.3,{emissive:'#7d9aab',emissiveIntensity:.3,lit:[.3,.8]}));},
    earbuds:function(k,g){k.bx(g,0,0,0,.06,.035,.045,k.mat('#f5f5f0',.3),.016);var lid=k.group(g,0,.035,-.022);lid.rotation.x=-1.0;k.bx(lid,0,0,.022,.06,.012,.045,k.mat('#f5f5f0',.3),.01);[-1,1].forEach(function(sd){k.sph(g,sd*.013,.04,.0,.009,.01,.009,k.mat('#ffffff',.3));});}
  };
  Object.keys(goodsModels2).forEach(function(id){goodsModels[id]=goodsModels2[id];});
  // Curtains hang on the window nearest the slot; other goods use the slot's facing.
  function goodsId(item){return String(item&&(item.possession_id||item.goods_id||item.id)||'');}
  function placedGoods(k,g,s){var id=goodsId(s.item);var b=goodsModels[id];if(b){b(k,g,s);return true;}return false;}
  function curtainSet(k,g,width,height,color){var rod=k.cyl(g,0,height,.0,.012,.012,width+.2,k.brass);rod.rotation.z=Math.PI/2;[-1,1].forEach(function(sd){var pn=k.group(g,sd*(width/2-.12),height-.02,0);for(var i=0;i<5;i++){k.box(pn,-.1+i*.05,-height/2+.01,(i%2)*.025,.06,height-.04,.025,k.fabric(color,true),.012);}k.tor(pn,0,-height*.55,.02,.11,.012,k.fabric('#d9c9a6'),Math.PI*2);});}
  function goodsPlace(k,g,item,o){var T=k.T,pl=item.place||{},id=goodsId(item);
    if(id==='curtain'){var O=((root.RoomModel||{}).openings||{})[k.room]||{},wins=(O.N||[]).filter(function(w){return w[2]==='win';}),best=null;wins.forEach(function(w){var c=(k.X(w[0])+k.X(w[1]))/2;if(!best||Math.abs(c-o.x)<Math.abs(best.c-o.x))best={c:c,w:k.X(w[1])-k.X(w[0]),top:w[4]||2.3};});
      var cg=new T.Group();cg.position.set(best?best.c:o.x,0,.13);g.add(cg);curtainSet(k,cg,best?best.w+.3:1.2,Math.min(k.H-.1,(best?best.top:2.2)+.15),'#cdbfa3');return cg;}
    var pivot=new T.Group();pivot.position.set(o.x,o.base,o.z);pivot.rotation.y={S:0,E:Math.PI/2,W:-Math.PI/2,N:Math.PI}[pl.facing||'S']||0;g.add(pivot);
    // Freely placed (no slot) clothes get their own coat stand; small goods rest on the furniture top under them.
    var holder=pivot;if(HANG[id]&&o.base<.5){coatStand(k,pivot);holder=k.group(pivot,0,1.52,-.06);}
    if(!placedGoods(k,holder,{item:item}))placeholder(k,holder,{L:.3,Dd:.25,H:.3,item:item});
    if(o.base>.05&&!HANG[id])(k._goodsSnap||(k._goodsSnap=[])).push({pivot:pivot,g:g,base:o.base});
    else if(!item.slot_id&&!HANG[id]&&!FLOOR_GOODS[id])(k._goodsSnap||(k._goodsSnap=[])).push({pivot:pivot,g:g,base:0,free:true});return pivot;}
  var FLOOR_GOODS={rug:1,bath_mat:1,lamp:1,plant:1,plant_pot:1,humidifier:1,guitar:1,storage_box:1,storage_basket:1,yarn:1,sneakers:1,canvas_shoes:1,indoor_slippers:1,thin_blanket:1,tablecloth:1,towel:1};
  function coatStand(k,g){var w=k.walnut||k.mat('#8a6a4b',.6);[0,1,2,3].forEach(function(i){var a=i*Math.PI/2+.4,l=k.box(g,Math.cos(a)*.12,.03,Math.sin(a)*.12,.26,.025,.035,w,.01);l.rotation.y=-a;});k.cylB(g,0,0,0,.025,.03,1.62,w);k.sph(g,0,1.64,0,.035,.03,.035,w);
    [0,1,2,3].forEach(function(i){var a=i*Math.PI/2,h=k.cyl(g,Math.cos(a)*.06,1.55,Math.sin(a)*.06,.008,.008,.12,k.brass);h.rotation.set(Math.sin(a)*.9,0,-Math.cos(a)*.9);k.sph(g,Math.cos(a)*.11,1.59,Math.sin(a)*.11,.012,.012,.012,k.brass);});}
  // Surface goods sit on whatever furniture top is under the slot point (slot heights are approximate).
  function goodsSnap(k){var list=k._goodsSnap||[];if(!list.length)return;var T=k.T,ray=new T.Raycaster(),down=new T.Vector3(0,-1,0),targets=[];
    k.scene.traverse(function(o){if(o.isMesh&&o.visible&&!(o.userData&&o.userData.character)&&o.geometry&&o.geometry.type!=='PlaneGeometry')targets.push(o);});
    list.forEach(function(s){var own=[];s.g.traverse(function(o){own.push(o);});var p=s.pivot.getWorldPosition(new T.Vector3());ray.set(new T.Vector3(p.x,s.free?1.4:s.base+.45,p.z),down);ray.far=s.free?1.4:1.0;
      var hit=ray.intersectObjects(targets.filter(function(t){return own.indexOf(t)<0;}),false).find(function(h){return s.free?h.point.y>-.02&&h.point.y<1.3:(h.point.y>s.base-.4&&h.point.y<s.base+.4);});if(hit)s.pivot.position.y=hit.point.y+.002;});
    k._goodsSnap=[];}
  root.Room3DModels={interiorMaterial:interiorMaterial,roomItems:roomItems,types:types,names:names,surfaceTop:surfaceTop,theme:theme,rooms:rooms,materials:materials,floorTexture:floorTexture,skyTexture:skyTexture,rugMaterial:rugMaterial,walls:walls,buildWall:buildWall,fixtures:fixtures,items:items,decor:decor,placeholder:placeholder,lighting:lighting,goods:goodsModels,goodsPlace:goodsPlace,goodsSnap:goodsSnap};
})(window);
