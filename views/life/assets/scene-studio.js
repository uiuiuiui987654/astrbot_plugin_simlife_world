/* Layered scene artwork. All furniture remains an individual accessible SVG group. */
(function (root) {
  'use strict';
  var S = {};
  var floors = {
    1: [['客厅',270,30,300,220,'#806754'],['浴室',590,30,180,220,'#6c9395'],['厨房',790,30,260,220,'#82927b'],['餐厅',270,270,330,240,'#8c7459'],['健身室',620,270,240,240,'#667c77'],['阳台',880,270,170,240,'#597c67'],['玄关',270,530,780,120,'#7f6e60'],['车库',30,530,440,400,'#6d7275']],
    2: [['卧室',270,30,300,220,'#8e788e'],['衣帽间',590,30,180,220,'#8d7f76'],['书房',790,30,260,220,'#637f85'],['画室',270,270,330,240,'#a18f76'],['影音室',620,270,240,240,'#645b7b'],['露台',880,270,170,240,'#567a69'],['楼梯厅',270,530,780,120,'#7d6d62']]
  };
  // The top-down preview uses a compact 240x240 garage beside the dining room.
  // The close-up keeps its larger drawing canvas so the garage artwork can breathe.
  var planFloors = {
    1: floors[1].map(function (r) {
      return r[0] === '车库'
        ? ['车库', 30, 270, 240, 240, r[5]]
        : r.slice();
    }),
    2: floors[2].map(function (r) { return r.slice(); })
  };
  // The plan is wider than the original 840 to fit the 1F garage wing on the east side (2F shows its roof).
  S.width = 1090; S.height = 860;
  // Garage bays (room plan units, nose north): A1 jeep, A2 the family car, A3 sports car. Shared by plan + close-up.
  S.garageBays = [{x:90,type:'jeep',paint:'#6f7f5c',label:'吉普'},{x:220,type:'sedan',paint:'#eef2ef',label:'白色小车',home:true},{x:350,type:'sports',paint:'#c8423a',label:'跑车'}];
  S.garageOut = function(type){
    var g=root.SimLifeGarage||{};
    var carType=String(type||'');
    var carId=carType==='jeep'?'car_jeep':carType==='sports'?'car_sports':'car_white';
    var vehicles=g.vehicles||[];
    if(vehicles.length){
      var found=vehicles.filter(function(v){return v&&v.id===carId;})[0];
      if(found)return /out/.test(String(found.status||''));
    }
    return /out/.test(g.mode||'');
  };
  S.rooms = function (floor) { return floors[floor].map(function(r) { return {name:r[0],x:r[1],y:r[2],w:r[3],h:r[4],fill:r[5]}; }); };
  S.planRooms = function (floor) { return planFloors[floor].map(function(r) { return {name:r[0],x:r[1],y:r[2],w:r[3],h:r[4],fill:r[5]}; }); };
  S.garagePlanRect = {x:30,y:270,w:240,h:240};
  // the garage close-up / 3D canvas (plan units); the top-down plan squeezes it into garagePlanRect
  var GW=440,GH=400;S.garageCanvas={w:GW,h:GH};
  S.floorFor = function(room) { return floors[2].some(function(r){return r[0]===room;}) ? 2 : 1; };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
  function rect(x,y,w,h,fill,r,extra) { return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(r||0)+'" fill="'+fill+'" '+(extra||'')+'/>'; }
  function line(x,y,a,b,c,w) { return '<path d="M'+x+' '+y+'L'+a+' '+b+'" fill="none" stroke="'+c+'" stroke-width="'+(w||1)+'"/>'; }
  function circle(x,y,r,c,extra) { return '<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+c+'" '+(extra||'')+'/>'; }
  function ellipse(x,y,a,b,c) { return '<ellipse cx="'+x+'" cy="'+y+'" rx="'+a+'" ry="'+b+'" fill="'+c+'"/>'; }
  function text(x,y,t,size,c,extra) { return '<text x="'+x+'" y="'+y+'" fill="'+(c||'#fff0db')+'" font-size="'+(size||12)+'" '+(extra||'')+'>'+esc(t)+'</text>'; }
  function path(d,c,extra) { return '<path d="'+d+'" fill="'+c+'" '+(extra||'')+'/>'; }
  S.environment = function(data,search) {
    data = data || {}; var p = new URLSearchParams(search || ''), t = p.get('time') || data.now_time;
    var hour = t && /^\d{1,2}:\d{2}/.test(t) ? Number(t.split(':')[0])+Number(t.split(':')[1])/60 : new Date().getHours()+new Date().getMinutes()/60;
    var band = hour < 5 || hour >= 19 ? 'night' : hour < 8 ? 'dawn' : hour < 16.5 ? 'day' : 'dusk';
    var condition = p.get('weather') || (data.weather || {}).condition || '晴朗';
    var kind = /雷|storm|thunder/i.test(condition) ? 'storm' : /雪|snow/i.test(condition) ? 'snow' : /雨|rain|drizzle/i.test(condition) ? 'rain' : /雾|霾|fog|mist/i.test(condition) ? 'fog' : /大风|wind/i.test(condition) ? 'wind' : /阴|多云|cloud|overcast/i.test(condition) ? 'cloudy' : 'clear';
    var palettes = {night:['#101e38','#425373','#98b8de'],dawn:['#7b8eaa','#efb5a0','#ffe3ba'],day:['#78b8cc','#e0e9cc','#fff2c2'],dusk:['#7d7da4','#f2b18c','#ffd297']};
    var sky = palettes[band].slice(); if (/rain|storm|fog|snow|cloudy/.test(kind)) sky = band==='night' ? ['#152432','#465d6b','#acc5d2'] : ['#718996','#b8c6c7','#d9e6de'];
    return {band:band,weather:kind,condition:condition,hour:hour,sky:sky,dark:band==='night',signature:band+'|'+kind+'|'+condition};
  };
  S.classes = function(e) { return ' time-'+e.band+' weather-'+e.weather; };
  S.badge = function(e) { return '<div class="environment-badge">'+esc({night:'夜晚',dawn:'晨光',day:'日间',dusk:'黄昏'}[e.band])+' · '+esc(e.condition)+'</div>'; };
  function defs(id,e) {
    function gradient(n,a,b) { return '<linearGradient id="'+id+n+'" x2="0.8" y2="1"><stop stop-color="'+a+'"/><stop offset="1" stop-color="'+b+'"/></linearGradient>'; }
    return '<defs>'+gradient('wood','#c5a482','#967353')+gradient('woodTop','#e4c8a3','#bb9770')+gradient('metal','#eef0dc','#91aaa0')+gradient('fabric','#d8c6d8','#aa91ad')+gradient('sage','#b6c9a7','#849e7b')+gradient('cream','#fff8e7','#dccdb3')+gradient('porcelain','#f2f7e9','#9bb7b6')+gradient('glass','#a0c6d0','#4c7385')+gradient('sky',e.sky[0],e.sky[1])+
      '<radialGradient id="'+id+'warm"><stop stop-color="#ffcf7f" stop-opacity=".62"/><stop offset="1" stop-color="#ffcf7f" stop-opacity="0"/></radialGradient>'+
      '<pattern id="'+id+'planks" width="66" height="22" patternUnits="userSpaceOnUse">'+rect(0,0,66,22,'#c4aa8a')+line(0,21,66,21,'#a68e71',.7)+line(33,0,33,21,'#b69d7e',.6)+path('M4 7Q17 5 29 8M39 16Q51 18 62 15','none','stroke="#d4ad7f" opacity=".27"')+'</pattern>'+
      '<pattern id="'+id+'tiles" width="22" height="22" patternUnits="userSpaceOnUse">'+rect(0,0,22,22,'#9eb9b1')+rect(1,1,20,20,'#d5e0ce',1)+path('M2 20L20 2','none','stroke="#f2edcf" stroke-opacity=".13"')+'</pattern>'+
      '<pattern id="'+id+'weave" width="4" height="4" patternUnits="userSpaceOnUse">'+path('M0 1H4M1 0V4','none','stroke="#fff5dd" stroke-opacity=".12" stroke-width=".5"')+'</pattern>'+
      '<pattern id="'+id+'grain" width="54" height="18" patternUnits="userSpaceOnUse">'+path('M0 4Q14 0 28 4T55 4M-4 12Q12 15 28 11T58 12M2 7Q15 3 25 7M30 15Q41 11 53 14','none','stroke="#6e5237" stroke-opacity=".22" stroke-width=".55"')+path('M1 5Q14 1 27 5M29 12Q41 8 54 11','none','stroke="#f1d3a4" stroke-opacity=".28" stroke-width=".65"')+'</pattern>'+
      '<filter id="'+id+'shadow" x="-30%" y="-30%" width="170%" height="180%"><feDropShadow dx="1" dy="4" stdDeviation="3" flood-color="#201820" flood-opacity=".35"/></filter></defs>';
  }
  S.materialDefs = defs;
  function plant(x,y,s) {
    return '<g transform="translate('+x+' '+y+') scale('+(s||1)+')">'+ellipse(0,19,14,5,'#233c3433')+rect(-7,7,14,15,'#b78664',3)+ellipse(0,7,7,3,'#dfb794')+line(0,9,0,-14,'#446f52',2)+ellipse(-7,-2,6,12,'#4f9267')+ellipse(7,-9,6,12,'#78ac79')+ellipse(0,-15,5,11,'#a1bd87')+line(-7,-10,-3,6,'#b9c894',.8)+'</g>';
  }
  function rug(x,y,w,h,c,id) { return rect(x,y,w,h,c,10)+rect(x+4,y+4,w-8,h-8,'none',8,'stroke="#eddbb1" stroke-opacity=".45"')+rect(x,y,w,h,'url(#'+id+'weave)',10); }
  function hit(item,body,transform,extra) {
    return '<g class="furniture-hit studio-item" role="button" tabindex="0" data-id="'+esc(item.id)+'" '+(extra||'')+' aria-label="'+esc(item.name)+'" transform="'+(transform||'')+'"><title>'+esc(item.name)+' · '+esc((item.actions||[]).slice(0,2).join(' / '))+'</title>'+body+'</g>';
  }
  // Artwork types are shared; plan footprints and close-up placement are independent.
  var layout = {
    bed:[30,45,142,112,'bed'],wardrobe:[202,26,66,112,'cabinet'],bedside_lamp:[177,54,27,30,'lamp'],vanity_mirror:[211,141,68,35,'vanity'],aroma_diffuser:[175,112,22,27,'diffuser'],plush:[43,155,22,25,'bear'],bedtime_book:[86,160,32,22,'book'],
    bathtub:[25,35,195,76,'tub'],shower:[238,32,36,66,'shower'],bath_salts:[21,118,24,26,'jar'],waterproof_speaker:[72,120,25,29,'speaker'],face_mask:[115,120,40,28,'mask'],bath_towel:[216,123,60,35,'towel'],
    bookshelf:[14,32,63,137,'bookshelf'],desk:[100,88,172,61,'desk'],desk_lamp:[226,92,20,24,'lamp'],monitor:[138,43,79,43,'monitor'],keyboard:[143,115,75,16,'keyboard'],notebook:[99,42,34,28,'book'],camera:[236,50,29,25,'camera'],headphones:[91,158,32,28,'headphones'],
    sofa:[22,56,73,116,'sofa'],tv:[240,56,30,100,'monitor'],coffee_table:[119,85,91,53,'table'],record_player:[139,30,58,35,'record'],game_console:[225,160,52,22,'console'],board_game:[128,148,37,30,'board'],floor_lamp:[96,34,30,32,'floorlamp'],yoga_mat:[20,177,84,18,'mat'],piano:[190,22,83,40,'piano'],aquarium:[21,25,64,28,'aquarium'],
    fridge:[18,73,54,104,'fridge'],coffee_machine:[94,31,35,35,'coffee'],pour_over:[140,34,24,28,'pourover'],oven:[209,90,62,57,'oven'],toaster:[173,34,35,26,'toaster'],dining_table:[91,102,112,67,'dining'],recipe_book:[222,35,38,26,'book'],tea_set:[110,174,68,23,'tea'],rice_cooker:[76,174,28,22,'ricecooker'],dishwasher:[222,155,50,36,'dishwasher'],
    balcony_chair:[49,86,95,53,'rockingchair'],plants:[18,32,113,34,'plants'],watering_can:[159,48,33,27,'wateringcan'],wind_chime:[227,28,27,36,'chime'],telescope:[174,125,82,46,'telescope'],blanket:[57,151,57,25,'towel'],washing_machine:[18,144,49,43,'washer'],iron:[128,170,35,20,'iron'],
    shoe_cabinet:[5,40,53,120,'cabinet'],umbrella:[65,72,25,80,'umbrella'],key_tray:[99,70,36,60,'keys'],vacuum:[151,50,38,105,'vacuum'],sewing_kit:[204,60,30,70,'board'],delivery_box:[247,38,43,117,'box'],
    treadmill:[26,40,135,102,'treadmill'],dumbbells:[188,116,73,32,'weights'],fitness_mirror:[199,36,58,64,'mirror'],
    art_easel:[31,38,94,106,'easel'],paint_cart:[163,48,61,77,'paints'],digital_tablet:[165,142,81,40,'monitor'],
    cinema_screen:[33,27,229,68,'screen'],cinema_sofa:[62,124,170,57,'sofa'],popcorn_machine:[246,122,34,49,'popcorn'],
    dressing_mirror:[33,33,62,111,'mirror'],accessory_cabinet:[153,40,115,108,'jewelry'],
    terrace_swing:[55,82,95,58,'rockingchair'],flower_bed:[28,157,137,33,'plants'],bbq_grill:[195,60,68,62,'grill'],
    stairs:[170,20,100,165,'stairs'],storage_bench:[21,51,105,105,'cabinet'],
    dining_room_table:[75,70,160,88,'dining'],sideboard:[25,25,75,34,'cabinet']
  };
  S.layout = layout;
  function object(type,w,h,id,e,front) {
    return root.FurnitureArt.draw(type,w,h,id,e,front);
  }
  // Windows sit on outside walls; each door is drawn once (on the south/east side of the pair) and swings into the room it serves.
  function scaleOpenings(op,sx,sy){var o={};Object.keys(op).forEach(function(s){var f=/[NS]/.test(s)?sx:sy;o[s]=op[s].map(function(q){var c=q.slice();c[0]=q[0]*f;c[1]=q[1]*f;return c;});});return o;}
  function planOpenings(r,op){
    var b=[];
    function win(x,y,w,h){b.push(rect(x,y,w,h,'#b6d7ce',2),w>h?line(x+w/2,y,x+w/2,y+h,'#d7ebdd',2):line(x,y+h/2,x+w,y+h/2,'#d7ebdd',2));}
    function door(x,y,w,h,kind,vertical){var col=kind==='glass'?'#bcd9d0':kind==='entry'?'#8fa189':'#cebb97';b.push(rect(x,y,w,h,col,1));
      var s=Math.min(24,vertical?h:w),stroke='stroke="'+(kind==='glass'?'#d6efe6':'#f2d9ae')+'" stroke-width="1" opacity=".7"';
      if(kind==='glass'){b.push(vertical?line(x+w/2,y,x+w/2,y+h,'#eef6ef',1):line(x,y+h/2,x+w,y+h/2,'#eef6ef',1));return;}
      if(vertical)b.push(path('M'+(x+2)+' '+y+'h-'+s+'q0 '+s+' '+s+' '+s,'none',stroke));
      else b.push(path('M'+x+' '+(y+2)+'v-'+s+'q'+s+' 0 '+s+' '+s,'none',stroke));}
    (op.N||[]).forEach(function(o){if(o[2]==='win')win(r.x+o[0],r.y+2,o[1]-o[0],7);});
    (op.W||[]).forEach(function(o){if(o[2]==='win')win(r.x+2,r.y+o[0],7,o[1]-o[0]);});
    (op.E||[]).forEach(function(o){if(o[2]==='win')win(r.x+r.w-9,r.y+o[0],7,o[1]-o[0]);else door(r.x+r.w-2,r.y+o[0],22,o[1]-o[0],o[2],true);});
    (op.S||[]).forEach(function(o){if(o[2]==='win')win(r.x+o[0],r.y+r.h-9,o[1]-o[0],7);else door(r.x+o[0],r.y+r.h-2,o[1]-o[0],/玄关/.test(r.name)?8:24,o[2],false);});
    return b.join('');
  }
  S.home = function(now,floor,items,e) {
    var id='map-', rooms=S.planRooms(floor), b=[defs(id,e)];
    var PW=S.width,PH=S.height;b.push(rect(10,14,PW-20,PH-24,'#526851',14,'opacity=".16"'),rect(12,10,PW-24,PH-24,'#d1c5a8',14),rect(15,13,PW-30,PH-30,'#f4ebd5',11),rect(22,22,PW-44,PH-44,'#a7b79f',7));
    b.push(yardArt(floor));
    if(floor===2)b.push(garageRoof(id));
    rooms.forEach(function(r){
      var outdoor=/阳台|露台/.test(r.name), tiled=/浴室|厨房/.test(r.name), op=((root.RoomModel||{}).openings||{})[r.name];
      var garage=r.name==='车库';
      // the garage openings are in its 440x400 close-up units; the plan shows it scaled into its 240x300 slot
      if(garage&&op)op=scaleOpenings(op,r.w/GW,r.h/GH);
      b.push('<g class="studio-room" data-room="'+r.name+'">',garage?rect(r.x,r.y,r.w,r.h,'#a3a5a1',3):rect(r.x,r.y,r.w,r.h,'url(#'+id+(tiled?'tiles':'planks')+')',3),rect(r.x,r.y,r.w,r.h,r.fill,3,'opacity=".12"'));
      b.push(garage?garagePlanScaled(r,id):'<g transform="translate('+r.x+' '+r.y+')">'+root.HouseInterior.floor(r.name,r.w,r.h)+'</g>');
      if(!outdoor)b.push(rect(r.x+1,r.y+1,r.w-2,r.h-2,'none',2,'stroke="#f9efd7" stroke-width="3"'),line(r.x+5,r.y+5,r.x+r.w-5,r.y+5,root.HouseInterior.theme(r.name).side,3));
      if(outdoor)b.push(rect(r.x,r.y,r.w,r.h,'#3b766c',3,'opacity=".22"'));
      if(outdoor) {
        // Replace the enclosing building edge with a slab and a transparent railing.
        b.push('<g class="open-air-boundary" data-room="'+r.name+'" data-covered="'+(r.name==='阳台')+'">',rect(r.x+r.w-3,r.y-1,22,r.h+2,'url(#'+id+'planks)'),rect(r.x+r.w-3,r.y-1,22,r.h+2,'#6b9c7b',0,'opacity=".18"'));
        b.push(path('M'+r.x+' '+(r.y+r.h)+'V'+r.y+'H'+(r.x+r.w+18)+'M'+r.x+' '+(r.y+r.h)+'H'+(r.x+r.w+18),'none','stroke="#b8bea3" stroke-width="2"'));
        b.push(rect(r.x+r.w+4,r.y+5,11,r.h-10,'#bedfd82a',1),line(r.x+r.w+13,r.y+3,r.x+r.w+13,r.y+r.h-3,'#bcd7ca',2));
        for(var railY=r.y+6;railY<r.y+r.h;railY+=29)b.push(line(r.x+r.w+3,railY,r.x+r.w+15,railY,'#cbd7bc',2),circle(r.x+r.w+13,railY,1.6,'#e7e3c9'));
        b.push('</g>');
      } else b.push(rect(r.x+2,r.y+2,r.w-4,r.h-4,'none',2,'stroke="#f5e2b6" stroke-opacity=".18" stroke-width="3"'));
      if(!/玄关|楼梯/.test(r.name)) {
        var mat=root.RoomModel.rugs[r.name];
        if(mat)b.push(rug(r.x+mat[0],r.y+mat[1],mat[2],mat[3],/卧室|影音/.test(r.name)?'#d7c8df88':'#efe4c699',id));
        // Window recess, curtain folds and projected daylight stay behind furniture.
        var nwin=op&&!outdoor?(op.N||[]).filter(function(o){return o[2]==='win';})[0]:null;
        if(nwin&&!e.dark&& !/rain|storm|fog/.test(e.weather))b.push(path('M'+(r.x+nwin[0])+' '+(r.y+10)+'l-25 '+r.h*.6+'h'+((nwin[1]-nwin[0])*1.4)+'l-10 -'+r.h*.6+'Z',e.band==='dusk'?'#ffcf8a':'#f7efd1','opacity=".16"'));

      }
      b.push('<g class="room-fixtures" pointer-events="none" transform="translate('+r.x+' '+r.y+')">'+root.InteriorLayout.planFixtures(r.name,id)+'</g>');
      var fixtureHits='';
      ((root.RoomModel||{}).fixtures&&root.RoomModel.fixtures[r.name]||[]).forEach(function(f){
        var fit=items.find(function(entry){return String(entry.id)===String(f.id);});
        if(!fit)return;
        var label=String(fit.name||f.id);
        fixtureHits+='<rect class="furniture-hit studio-fixture" data-id="'+esc(f.id)+'" x="'+(r.x+f.x)+'" y="'+(r.y+f.y)+'" width="'+f.w+'" height="'+f.d+'" fill="transparent" pointer-events="all" role="button" tabindex="0" aria-label="'+esc(label)+'"><title>'+esc(label)+'</title></rect>';
      });
      if(fixtureHits)b.push('<g class="fixture-hit-layer">'+fixtureHits+'</g>');
      b.push('</g>');
      var roomItems=items.filter(function(i){return i.room===r.name;});
      roomItems.sort(function(a,b){
        var ap=root.InteriorLayout.plan[a.id],bp=root.InteriorLayout.plan[b.id];
        return Number(!!(ap&&ap[4]))-Number(!!(bp&&bp[4]));
      });
      roomItems.forEach(function(item){
        var p=root.InteriorLayout.plan[item.id];
        if(!p||item.slot_id||item.custom_place){
          if(!item.place)return;
          var px=r.x+(Math.max(0.05,Math.min(0.95,Number(item.place.x)||0.5)))*r.w;
          var py=r.y+(Math.max(0.05,Math.min(0.95,Number(item.place.y)||0.5)))*r.h;
          // Placed goods show their own picture (installed slot goods larger for rugs, lamps, plants, curtains).
          var gsz={rug:40,bath_mat:32,towel:28,curtain:36,lamp:26,plant:24,plant_pot:22,guitar:26,storage_box:22,storage_basket:22,tablecloth:30}[String(item.possession_id||item.id)];
          if(gsz==null&&root.GoodsSize){var fp=GoodsSize.footprint(item);gsz=Math.max(14,Math.min(48,Math.max(fp[0],fp[1])*.35));}
          if(gsz==null)gsz=18;
          px=Math.max(r.x+gsz/2+2,Math.min(r.x+r.w-gsz/2-2,px));py=Math.max(r.y+gsz/2+2,Math.min(r.y+r.h-gsz/2-2,py));
          var gart=root.ItemArtwork?(root.ItemArtwork.draw(item)||''):'';
          if(gart)gart=gart.replace('<svg ','<svg x="'+(-gsz/2)+'" y="'+(-gsz/2)+'" width="'+gsz+'" height="'+gsz+'" ');
          b.push(hit(item,gart?'<ellipse cx="0" cy="'+(gsz*.36)+'" rx="'+(gsz*.36)+'" ry="'+(gsz*.12)+'" fill="#24382a22"/>'+gart:'<circle cx="0" cy="0" r="9" fill="#f7efd8" stroke="#7d8f73" stroke-width="1.2"/><text x="0" y="3.2" text-anchor="middle" font-size="9">📦</text>','translate('+px+' '+py+')'));
          return;
        }
        var type=(layout[item.id]||[])[4]||'box';
        b.push(hit(item,root.InteriorLayout.planArtwork(item,type,id,e),'translate('+(r.x+p[0])+' '+(r.y+p[1])+')',floor===2&&item.id==='stairs'?'data-stair-floor="1"':''));
      });
      if(e.dark) b.push('<g pointer-events="none">'+ellipse(r.x+r.w*.6,r.y+r.h*.5,r.w*.48,r.h*.45,'url(#'+id+'warm)')+'</g>');
      b.push('<g pointer-events="none">'+rect(r.x+7,r.y+6,Math.max(48,r.name.length*13+15),23,'#566c51e6',5)+text(r.x+15,r.y+22,r.name,12,'#f5e8cf','font-weight="600"')+'</g>');
      if(now&&now.kind==='home'&&now.room===r.name)b.push(rect(r.x-2,r.y-2,r.w+4,r.h+4,'none',5,'stroke="#8da37a" stroke-width="2.5" class="current-room-outline" pointer-events="none"'));
      if(outdoor)b.push(text(r.x+67,r.y+21,r.name==='阳台'?'开放 · 遮檐':'开放 · 无顶',7,'#d5dec7'));
      if(op)b.push('<g class="plan-openings" pointer-events="none">'+planOpenings(r,op)+'</g>');
    });
    b.push('<g pointer-events="none">'+text(34,PH-9,'VIRTUAL LIFE  /  '+floor+'F',8,'#d7caa9','letter-spacing="2"')+text(PW-185,PH-9,'光影随时间与天气变化',8,'#c0d1c5')+'</g>');
    return b.join('');
  };
  // 1F garage plan: concrete slab, bay lines, roll-up doors on the street side, workbench / shelving, plan-view cars.
  function garagePlan(r,id){var b=[],x=r.x,y=r.y;
    for(var i=0;i<60;i++)b.push(circle(x+((i*97)%r.w),y+((i*61+i*i)%r.h),.9+(i%3)*.4,i%2?'#8e908c':'#b5b7b1'));
    [25,155,285,415].forEach(function(bx){b.push(line(x+bx,y+70,x+bx,y+r.h-20,'#e3c24f',3));});
    b.push(rect(x+12,y+r.h-14,r.w-24,5,'#6d7275',1),rect(x+r.w/2-60,y+r.h-60,120,6,'#5d6164',2,'opacity=".6"'));
    S.garageBays.forEach(function(g){b.push(rect(x+g.x-58,y+r.h-9,116,9,'#d8d9d2',1,'stroke="#8b8e88" stroke-width="1"'),line(x+g.x-54,y+r.h-5,x+g.x+54,y+r.h-5,'#a6a9a3',1),text(x+g.x,y+r.h-24,'A'+(S.garageBays.indexOf(g)+1),11,'#e3c24f','text-anchor="middle" font-weight="700"'));
      b.push(rect(x+g.x-34,y+44,20,8,'#e3c24f',2),rect(x+g.x+14,y+44,20,8,'#e3c24f',2));});
    b.push(rect(x+70,y+12,62,26,'#b08a63',2,'stroke="#7e6247" stroke-width="1"'),rect(x+74,y+16,14,8,'#c8564a',1),rect(x+94,y+17,16,6,'#5f7e9b',1),rect(x+116,y+16,10,9,'#4a6b5a',1));
    b.push(rect(x+r.w-26,y+150,20,90,'#8f969b',2,'stroke="#6f767b" stroke-width="1"'));for(var s2=0;s2<4;s2++)b.push(rect(x+r.w-24,y+156+s2*21,16,14,['#c9a87a','#d6c3a0','#c8564a','#b99a6e'][s2],1.5));
    b.push(rect(x+r.w-26,y+262,20,34,'#c8564a',2,'stroke="#9a3f36" stroke-width="1"'),circle(x+r.w-16,y+r.h-40,6,'#26282b'),circle(x+r.w-16,y+r.h-40,3,'#55595d'));
    S.garageBays.forEach(function(g,i){var cx=x+g.x,cy=y+r.h-153,ky=r.ky||1;
      if(S.garageOut(g.home?'sedan':g.type)){b.push('<ellipse cx="'+cx+'" cy="'+(cy+40)+'" rx="22" ry="14" fill="#3c3a38" opacity=".3"/>',rect(cx-36,cy+10,8,80,'#2b2b2b',3,'opacity=".12"'),rect(cx+28,cy+10,8,80,'#2b2b2b',3,'opacity=".12"'),text(cx,cy+4,'车出门了',10,'#55595d','text-anchor="middle"'));return;}
      var art=root.VehicleArt&&root.VehicleArt.top?root.VehicleArt.top(g.type,g.paint):'';
      b.push('<g class="garage-car-hit" data-car="'+(g.home?'home':g.type)+'" role="button" tabindex="0" aria-label="'+esc(g.label)+'"><title>'+esc(g.label+(g.home?' · 点击打开车库':''))+'</title><g transform="translate('+(cx+47.3)+' '+(cy+107.5*ky)+') scale(-2.15 '+(-2.15*ky).toFixed(3)+')">'+art+'</g></g>');});
    b.push(line(x+2,y+60,x+2,y+r.h-10,'#c9c3b2',2));
    return b.join('');}
  function garagePlanScaled(r,id){
    // cars are counter-scaled so the non-uniform squeeze does not stretch them
    var base={x:0,y:0,w:GW,h:GH,ky:(r.w/GW)/(r.h/GH)};
    return '<g transform="translate('+r.x+' '+r.y+') scale('+(r.w/GW).toFixed(4)+' '+(r.h/GH).toFixed(4)+')">'+garagePlan(base,id)+'</g>';
  }
  // 2F: the garage below is a flat roof with gravel, parapet, skylight and an outdoor AC unit.
  // Site around the house: west side garden above the garage, front lawn with the path from the front door.
  function yardArt(floor){var b=['<g class="front-yard" pointer-events="none">'],PH=PH_(),PW=PW_();
    // street along the bottom edge: sidewalk, curb, asphalt with a dashed centre line
    var G=S.garagePlanRect,RY=PH-128,RB=PH-24,dwx=G.x+6,dww=G.w-12,gy=G.y+G.h,hx=G.x+G.w;
    b.push(rect(hx-4,660,PW-hx-18,RY-664,'#9fb497',4));
    for(var i=0;i<12;i++)b.push(circle(hx+20+((i*137)%(PW-hx-60)),676+((i*71)%Math.max(8,RY-700)),7+(i%3)*3,i%2?'#8aa483':'#93ac8b'));
    // small kitchen garden and trees on the strip above the garage
    b.push(rect(G.x+20,G.y-112,150,90,'#8a6d55',4));for(var r=0;r<4;r++)for(var c=0;c<6;c++)b.push(circle(G.x+34+c*24,G.y-96+r*20,6,r%2?'#8fbf6f':'#a7c97f'));
    [[G.x+60,G.y-200,34],[G.x+190,G.y-190,28],[G.x+205,G.y-70,20]].forEach(function(q){b.push(circle(q[0]+4,q[1]+5,q[2],'#4c6a4a55'),circle(q[0],q[1],q[2],'#7f9f72'),circle(q[0]-q[2]*.3,q[1]-q[2]*.3,q[2]*.55,'#95b386'));});
    b.push(rect(22,RY,PW-44,RB-RY,'#73787a',0),rect(22,RY,PW-44,18,'#d9d0bd',0),line(22,RY+18,PW-22,RY+18,'#b9b1a1',3));
    for(var sw=30;sw<PW-30;sw+=36)b.push(line(sw,RY+1,sw,RY+17,'#c7bea9',1));
    for(var dx=40;dx<PW-60;dx+=70)b.push(rect(dx,(RY+18+RB)/2-2,38,4,'#efe2b4',1));
    b.push(line(22,RB-6,PW-22,RB-6,'#5f6466',2),text(PW-120,RB-14,'马路',12,'#e4ddc9','letter-spacing="4"'));
    // front walk from the 玄关 entry door to the sidewalk
    var hall=(S.rooms(1).filter(function(q){return q.name==='玄关';})[0])||{x:270,y:530,h:120},ent=(((root.RoomModel||{}).openings||{})['玄关']||{}).S||[],door=ent.filter(function(o){return o[2]==='entry';})[0]||[370,420],ex=hall.x+door[0],hy=hall.y+hall.h;
    b.push(rect(ex,hy+4,door[1]-door[0],RY-hy-4,'#d8cdb4',3),line(ex+4,hy+10,ex+4,RY,'#c6b99d',1),line(ex+door[1]-door[0]-4,hy+10,ex+door[1]-door[0]-4,RY,'#c6b99d',1));
    // concrete driveway from the garage doors to the street, with expansion joints and a curb cut
    b.push(rect(dwx,gy,dww,RY+18-gy,'#c9c6bd',2),line(dwx+3,gy,dwx+3,RY+18,'#aeaba2',2),line(dwx+dww-3,gy,dwx+dww-3,RY+18,'#aeaba2',2));
    for(var j=gy+52;j<RY;j+=52)b.push(line(dwx+3,j,dwx+dww-3,j,'#b2afa6',1));
    b.push(line(dwx+dww/2,gy+6,dwx+dww/2,RY-4,'#b2afa6',1),rect(dwx-8,RY,dww+16,18,'#c0bcb2',2),path('M'+(dwx-8)+' '+(RY+18)+'l8 -6h'+dww+'l8 6','none','stroke="#a8a49a" stroke-width="2"'));
    return b.join('')+'</g>';}
  function PW_(){return S.width;}
  function PH_(){return S.height;}
  function garageRoof(id){var pr=S.garagePlanRect,x=0,y=0,w=GW,h=GH,b=['<g class="garage-roof" pointer-events="none" transform="translate('+pr.x+' '+pr.y+') scale('+(pr.w/w).toFixed(4)+' '+(pr.h/h).toFixed(4)+')">'];
    b.push(rect(x,y,w,h,'#9da09a',3),rect(x+8,y+8,w-16,h-16,'#b3b4ad',2));for(var i=0;i<140;i++)b.push(circle(x+12+((i*53)%(w-24)),y+12+((i*37+i*i*3)%(h-24)),1.1,i%2?'#9a9b94':'#c7c7bf'));
    b.push(rect(x+150,y+110,120,80,'#8fb3bd',4,'stroke="#e9ecea" stroke-width="5"'),line(x+210,y+112,x+210,y+188,'#e9ecea',2),rect(x+w-90,y+30,60,40,'#d9dbd6',4,'stroke="#9a9d98" stroke-width="2"'),circle(x+w-60,y+50,14,'#b8bbb5'),line(x+w-72,y+50,x+w-48,y+50,'#8d908b',2));
    b.push(rect(x+6,y+h-36,46,30,'#8e918b',2),line(x+10,y+h-30,x+48,y+h-30,'#b8bbb5',2),line(x+10,y+h-20,x+48,y+h-20,'#b8bbb5',2));
    b.push(rect(x+7,y+6,92,23,'#566c51e6',5),text(x+15,y+22,'1F 车库屋顶',12,'#f5e8cf','font-weight="600"'),'</g>');return b.join('');}
  function skyArt(e,w,h,openAir) {
    var b=[rect(0,0,w,h,'url(#view-sky)')];
    if(!openAir)b.push('<image href="assets/garden-landscape.png" width="'+w+'" height="'+h+'" preserveAspectRatio="xMidYMid slice" opacity="'+(e.dark?'.35':'.9')+'"/>');
    if(/clear|wind/.test(e.weather))b.push(circle(w*.78,h*.25,e.dark?10:17,e.dark?'#f2efcf':'#ffe4a7'));
    else b.push(ellipse(w*.72,h*.23,w*.18,h*.04,'#bdcec77a'),ellipse(w*.66,h*.19,w*.1,h*.05,'#bdcec77a'));
    b.push(path('M0 '+h*.7+'Q'+w*.2+' '+h*.32+' '+w*.43+' '+h*.7+'Q'+w*.7+' '+h*.4+' '+w+' '+h*.68+'V'+h+'H0Z','#648d86'));
    b.push(path('M0 '+h*.85+'Q'+w*.3+' '+h*.59+' '+w*.52+' '+h*.84+'T'+w+' '+h*.8+'V'+h+'H0Z','#476b6d'));
    for(var x=5;x<w;x+=27)b.push(path('M'+x+' '+h+'v-22l-7 9h14l-7-9','none','stroke="#284e51" stroke-width="3"'));
    return b.join('');
  }
  S.room = function(room,now,items,e,appearance) {
    var id='close-',size=S.rooms(S.floorFor(room)).filter(function(r){return r.name===room;})[0],open=/阳台|露台/.test(room);
    var result=root.RoomPerspective.draw(room,size,items,layout,e,appearance,now),c=result.camera;
    var op=((root.RoomModel||{}).openings||{})[room],nw=op?(op.N||[]).filter(function(o){return o[2]==='win';})[0]:null,wx=op?(nw?nw[0]:0):size.w*.35,ww=op?(nw?nw[1]-nw[0]:0):size.w*.3;
    var windowPoints=[[wx,0,120],[wx+ww,0,120],[wx+ww,0,68],[wx,0,68]].map(function(v){var p=c.point(v[0],v[1],v[2]);return (p[0]/6)+'% '+(p[1]/4.4)+'%';}).join(',');
    var weather=room==='影音室'?'':S.precipitation(e,!open);
    if(room==='阳台')weather=weather.replace(/weather-layer /g,'weather-layer covered-weather ');
    var style='--window-clip:polygon('+windowPoints+');';
    var look=appearance||{},name=esc(room);
    return '<div class="room-scene studio-close projected-room'+S.classes(e)+(open?' open-air-room':'')+'" data-room="'+name+'" style="'+style+'"><div class="room-canvas"><svg class="room-artwork" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid meet" role="img" aria-label="'+name+'同一布局的立体近景">'+defs(id,e)+result.artwork+'</svg>'+weather+'</div><div class="room-label">'+name+'<small>'+S.floorFor(room)+'F · '+esc(now&&now.activity||'自由时间')+'</small></div><div class="appearance-badge">'+esc(look.name||'白紫日常装')+'</div>'+S.badge(e)+'<div class="room-view-controls" role="group" aria-label="室内视图缩放"><button type="button" data-room-view="out" aria-label="缩小室内视图">−</button><output class="room-zoom-value" aria-live="polite">160%</output><button type="button" data-room-view="in" aria-label="放大室内视图">+</button><button type="button" data-room-view="reset" aria-label="显示完整房间">全景</button></div></div>';
  };
  S.precipitation = function(e,windowOnly) {
    var b=[], count=e.weather==='storm'?42:e.weather==='rain'?25:e.weather==='snow'?30:0;
    for(var i=0;i<count;i++)b.push('<i style="--left:'+((i*37+13)%101)+'%;--top:'+((i*53+19)%93)+'%;--delay:'+(-(i*0.37)%6)+'s;--speed:'+(e.weather==='snow'?4+i%5:.65+(i%4)*.16)+'s;--drift:'+((i%5)*9-18)+'px"></i>');
    return '<div aria-hidden="true" class="weather-layer precipitation '+(windowOnly?'window-weather':'')+'">'+b.join('')+'</div>'+(e.weather==='fog'?'<div class="weather-layer fog-bank '+(windowOnly?'window-weather':'')+'" aria-hidden="true"></div>':'')+(e.weather==='storm'?'<div class="weather-layer lightning '+(windowOnly?'window-weather':'')+'" aria-hidden="true"></div>':'');
  };
  S.outdoorDecor = function(key,e) {
    return root.DestinationArt.draw(key,e,defs('garden-',e));
  };
  S.travelMode = function(now) {
    var activity=String(now&&now.activity||'');
    if(/地铁|高铁|火车|列车|动车|轻轨/.test(activity))return 'rail';
    if(/公交|巴士|大巴|班车|接驳/.test(activity))return 'bus';
    if(/打车|出租|网约|驾车|开车|汽车|坐车|乘车/.test(activity))return 'car';
    if(/骑|自行车|单车/.test(activity))return 'cycle';
    return 'walk';
  };
  S.journeyTraffic = function(e) {
    var id='journey-',glass='url(#'+id+'glass)',metal='url(#'+id+'metal)',cream='url(#'+id+'cream)',out=[];
    function wheel(x){return '<g transform="translate('+x+' 44)"><g class="journey-wheel">'+circle(0,0,8,'#425b50')+circle(0,0,4.5,metal)+path('M-3 0h6M0-3v6','none','stroke="#5d7767" stroke-width="1"')+'</g></g>';}
    function vehicle(type,paint){
      if(root.VehicleArt)return root.VehicleArt.draw(type,paint,e.dark);
      var bus=/bus/.test(type),van=type==='delivery',suv=type==='suv',w=type==='bus'?146:type==='minibus'?126:van?118:108,b=[];
      b.push(ellipse(w/2,51,w*.49,3,'#304f3f35'));
      if(bus){
        b.push(rect(0,2,w,41,paint,6),rect(5,5,w-10,4,cream,2));
        for(var x=8;x<w-32;x+=23)b.push(rect(x,12,19,16,glass,2));
        b.push(rect(w-27,11,21,21,glass,2),line(w-30,12,w-30,40,'#cfdbc1',1.5),line(w-16,12,w-16,39,'#cfdbc1',1),text(15,38,'BUS',7,'#e8e5ca'));
      }else if(van){
        b.push(rect(1,3,w-44,39,paint,3),path('M'+(w-44)+' 15h23l18 18v10h-41Z',paint),path('M'+(w-40)+' 18h17l11 12h-28Z',glass),rect(17,13,29,19,cream,2),path('M21 22h21m-12-6v13','none','stroke="#a5b79e" stroke-width="1.5"'),line(w-43,16,w-43,41,'#7f958577',1));
      }else{
        b.push(path(suv?'M9 26V9q0-5 5-5h53l22 22Z':'M13 26L30 7h36l21 19Z',paint),rect(0,24,w,19,paint,7));
        b.push(path(suv?'M15 9h26v14H15Z':'M32 11h13v12H23Z',glass),path('M50 '+(suv?'9':'11')+'h13l14 '+(suv?'14':'12')+'H50Z',glass),line(48,9,48,39,'#d2dcc077',1),line(81,28,81,39,'#d2dcc077',1),line(53,29,59,29,'#d6deca',1.2));
        if(type==='taxi')b.push(rect(40,0,24,7,'#e8d7a0',2),text(52,5.5,'TAXI',4,'#6a7458','text-anchor="middle"'),line(4,34,w-6,34,'#c8b783',2));
        if(type==='hatchback')b.push(rect(4,18,4,11,'#5e7b70',1));
      }
      // All native silhouettes face east: the nose, white lamp and mirror lead.
      b.push(rect(w-7,29,6,6,e.dark?'#fff2b0':'#e9e5c4',2),rect(0,28,4,7,'#bb8c89',1),line(5,40,w-4,40,'#658474',1.5),rect(w-30,22,7,3,metal,1),wheel(22),wheel(w-22));
      if(e.dark)b.push(path('M'+w+' 29l37-7v23l-37-10Z','#f0e2a0','opacity=".16"'));
      return {width:w,art:b.join('')};
    }
    var lanes=[
      {name:'far',direction:'west',y:264,scale:.82,duration:20,phase:.10,cars:[['hatchback','#be9d9e'],['delivery','#b7b99a'],['sedan','#89aaa2'],['minibus','#a0b399'],['taxi','#c4b47e']]},
      {name:'near',direction:'east',y:298,scale:.95,duration:18,phase:.18,cars:[['sedan','#a3b698'],['taxi','#c4b47e'],['suv','#b2a7c0'],['bus','#93b4a5'],['delivery','#ba9d85']]}
    ];
    lanes.forEach(function(lane){lane.cars.forEach(function(spec,index){
      var v=vehicle(spec[0],spec[1]),delay=-(index/lane.cars.length+lane.phase)*lane.duration,rest=index*190+(lane.name==='near'?-110:-30),mirror=lane.direction==='west'?'translate('+v.width+' 0) scale(-1 1)':'';
      out.push('<g class="journey-vehicle journey-vehicle-'+lane.direction+'" data-lane="'+lane.name+'" data-direction="'+lane.direction+'" data-model="'+spec[0]+'" style="--traffic-duration:'+lane.duration+'s;--traffic-delay:'+delay.toFixed(3)+'s;--traffic-rest-x:'+rest+'px"><g transform="translate(0 '+lane.y+') scale('+lane.scale+')"><g class="vehicle-heading" data-facing="'+lane.direction+'" transform="'+mirror+'">'+v.art+'</g></g></g>');
    });});
    return '<g class="journey-traffic" data-vehicle-count="10">'+out.join('')+'</g>';
  };
  S.journeyDecor = function(e,mode) {
    var id='journey-',wood='url(#'+id+'wood)',glass='url(#'+id+'glass)',cream='url(#'+id+'cream)',sage='url(#'+id+'sage)',b=[defs(id,e)],far=[],near=[],front=[];
    b.push(rect(0,0,600,440,'url(#'+id+'sky)'),circle(493,56,e.dark?13:19,e.dark?'#ebe8cd':'#f6e3ae'));
    if(!/clear|wind/.test(e.weather))b.push(ellipse(441,61,59,13,'#bbcbc899'));
    for(var i=0;i<8;i++){
      var x=i*78-8,h=43+(i*37)%103;
      far.push(rect(x,268-h,65,h,i%2?'#8aa399':'#9ab0a2',2));
      for(var y=279-h;y<260;y+=19)far.push(line(x+7,y,x+55,y,e.dark?'#dbc89c66':'#d6ddc066',3));
    }
    for(i=0;i<3;i++){
      x=i*208+16;var fill=i===1?wood:cream;
      near.push(rect(x,172,157,99,fill,2),path('M'+(x-8)+' 174l32-38h109l32 38Z',sage,'stroke="#cebc99" stroke-width="2"'),rect(x+13,208,72,40,glass,2),line(x+49,209,x+49,247,'#e3d7b6',2),rect(x+110,217,27,54,glass,2),line(x+113,220,x+113,269,'#d3dcc0',1),circle(x+132,247,1.5,'#ddd0a9'),rect(x+14,181,126,9,i===1?'#ac8f80':'#8aa68b',1));
      near.push(rect(x+174,178,5,98,wood,1),ellipse(x+176,165,21,30,sage),ellipse(x+164,177,16,24,sage),rect(x+172,272,10,8,wood,1));
    }
    front.push(rect(52,342,4,91,wood,2),path('M45 346q9-26 19 0Z',cream),rect(271,399,76,6,wood,2),rect(276,383,66,9,wood,2),line(279,405,279,423,'#6f8875',2),line(338,405,338,423,'#6f8875',2));
    function loop(cls,body){return '<g class="journey-layer '+cls+'">'+body.join('')+'<g transform="translate(600 0)">'+body.join('')+'</g></g>';}
    b.push(loop('journey-distant',far),loop('journey-streetside',near),rect(0,276,600,71,'#82958c'),line(0,279,600,279,'#d8ceb1',4),'<g class="journey-lane">');
    for(x=0;x<1200;x+=100)b.push(rect(x+14,311,46,3,'#e1d6b7',1));
    for(x=0;x<1200;x+=200)b.push(path('M'+(x+64)+' 297h-23l6-4m-6 4l6 4M'+(x+124)+' 332h23l-6-4m6 4l-6 4','none','stroke="#d6d6b6" stroke-width="1.5" opacity=".6"'));
    b.push('</g>',rect(0,348,600,92,e.weather==='snow'?'#dce6da':'#c9bfa5'),line(0,349,600,349,'#e7d9b7',5),'<g class="journey-paving">');
    for(x=0;x<1200;x+=60)b.push(line(x,353,x-18,440,'#a193774d',1));
    b.push('</g>',line(0,394,600,394,'#a193773c',1),S.journeyTraffic(e),loop('journey-foreground',front));
    if(/rail|bus|car/.test(mode))b.push('<g class="journey-cabin" pointer-events="none">',rect(0,0,600,24,cream),rect(0,24,19,316,sage),rect(581,24,19,316,sage),rect(0,334,600,106,cream),rect(0,335,600,10,wood),rect(423,335,133,99,sage,18),rect(414,405,152,25,sage,10),line(33,20,33,334,'#e3dcc3',5),'</g>');
    var riding=/rail|bus|car/.test(mode),personH=riding?180:72,personW=personH*.74,personX=riding?488:437,personY=riding?455:416;
    if(riding)b.push('<defs><clipPath id="journey-passenger-clip"><rect x="417" y="260" width="150" height="145"/></clipPath></defs><g clip-path="url(#journey-passenger-clip)">');
    b.push('<g class="journey-traveler" data-height="'+personH+'" transform="translate('+personX+' '+personY+')"><g class="journey-person-drift"><g class="journey-person-step">',riding?'':ellipse(0,0,personW*.28,2.5,'#304a3933'),'<image class="journey-person-image" href="'+(root.__VL_CHARACTER_SRC||'assets/character_daily.png')+'" onerror="this.setAttribute(\'href\',\'assets/character_daily.png\')" x="'+(-personW/2)+'" y="'+(-personH)+'" width="'+personW+'" height="'+personH+'" preserveAspectRatio="xMidYMax meet"/>','</g></g></g>');
    if(riding)b.push('</g>',rect(414,405,152,25,sage,10));
    if(e.dark)b.push(rect(0,0,600,440,'#142a3c',0,'opacity=".25"'),ellipse(302,272,260,170,'url(#'+id+'warm)'));
    else if(e.band==='dusk')b.push(rect(0,0,600,440,'#daa574',0,'opacity=".09"'));
    return '<svg class="destination-art unified-art journey-art" data-destination="transit" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'+b.join('')+'</svg>';
  };
  S.newScenes = [{key:'botanical',label:'植物园'},{key:'riverside',label:'河岸步道'},{key:'lakeside',label:'湖畔'},{key:'campsite',label:'露营地'},{key:'amusement',label:'游乐园'},{key:'flower_shop',label:'花店'},{key:'bakery',label:'面包店'},{key:'library',label:'图书馆'}];
  root.SceneStudio=S;
})(typeof window==='undefined'?globalThis:window);
