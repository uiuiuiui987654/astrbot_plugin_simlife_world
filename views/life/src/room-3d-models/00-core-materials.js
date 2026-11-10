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
