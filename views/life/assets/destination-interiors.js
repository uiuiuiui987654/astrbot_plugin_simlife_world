/* Destination rooms composed for the same portrait-friendly stage as the home. */
(function(root){
  'use strict';
  var serial=0;
  var styles={'咖啡馆':'cafe','书店':'books','图书馆':'library','美术馆':'gallery','电影院':'cinema','办公室':'office','食堂':'canteen','植物园':'greenhouse','花店':'flowers','面包店':'bakery','商场':'mall','城市':'mall','超市':'market','杂货铺':'market','车站':'station','机场':'airport','旅店':'hotel','露营地':'camp','异乡':'tea','小酒馆':'bar','神社':'shrine'};
  function R(x,y,w,h,c,r,more){return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(r||0)+'" fill="'+c+'" '+(more||'')+'/>';}
  function P(d,c,stroke,sw){return '<path d="'+d+'" fill="'+c+'"'+(stroke?' stroke="'+stroke+'" stroke-width="'+(sw||1)+'" stroke-linejoin="round" stroke-linecap="round"':'')+'/>';}
  function E(x,y,rx,ry,c){return '<ellipse cx="'+x+'" cy="'+y+'" rx="'+rx+'" ry="'+ry+'" fill="'+c+'"/>';}
  function C(x,y,r,c){return E(x,y,r,r,c);}
  function L(d,c,w){return P(d,'none',c,w);}
  function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function T(x,y,s,n,c){return '<text x="'+x+'" y="'+y+'" fill="'+(c||'#64775c')+'" font-size="'+(n||10)+'" font-family="sans-serif" text-anchor="middle">'+esc(s)+'</text>';}
  function G(name,art){return '<g data-interior-part="'+name+'">'+art+'</g>';}
  function draw(key,env){
    var style=styles[key];if(!style)return null;
    env=env||root.SceneStudio.environment({},'?time=12:00');
    var id='di-'+(++serial)+'-',night=env.dark,wet=/rain|storm|snow|fog/.test(env.weather),dark=style==='cinema'||style==='bar',b=[];
    var wall=style==='flowers'||style==='greenhouse'?'#dce4cd':style==='books'||style==='library'?'#e6e4d5':style==='gallery'?'#f1edde':dark?'#8e889d':'#eee4d0';
    var sage='#a7b99c',wood='#c5a67d',cream='#f7efda',ink='#5b7167';
    function art(type,x,y,w,h){return '<g transform="translate('+x+' '+y+')">'+root.FurnitureArt.draw(type,w,h,id,env,true)+'</g>';}
    function goods(item,x,y,w,h){var svg=root.ProductArtwork&&root.ProductArtwork.draw({id:item});return svg?svg.replace('<svg ','<svg x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" '):'';}
    function pendant(x,y){return G('pendant',R(x-9,15,18,4,ink,2)+L('M'+x+' 17V'+(y-13),ink,1.5)+P('M'+(x-17)+' '+(y-13)+'h34l9 15h-52Z','url(#'+id+'brass)','#b8a37f')+L('M'+(x-11)+' '+(y-10)+'h22','#f8e8c1',1)+E(x,y+2,25,4,'#c3a474')+E(x,y+3,20,3,'#fff0ba')+P('M'+(x-19)+' '+(y+6)+'l-43 143h124l-43-143Z','url(#'+id+'lamplight)')+(night?E(x,y+20,37,27,'#ffdc8b16'):''));}
    function plant(x,y,scale){return '<g transform="translate('+x+' '+y+') scale('+scale+')">'+E(0,18,15,4,'#4f6d5b20')+P('M-11-1h22l-3 21H-8Z',wood)+L('M0 1v-31','#648c66',2)+P('M0-8q-21-3-15-19Q0-26 0-8m0-8q20-2 15-23Q0-33 0-16',sage)+P('M0-28q-7-22 3-27 14 17-3 27','#bfd0a8')+'</g>';}
    function window(x,y,w,h,arch){
      var clip=id+'window-'+x+'-'+y,shape=arch?'M'+x+' '+(y+h)+'V'+(y+w*.45)+'Q'+x+' '+y+' '+(x+w*.5)+' '+y+'Q'+(x+w)+' '+y+' '+(x+w)+' '+(y+w*.45)+'V'+(y+h)+'Z':null;
      var outline=shape?P(shape,'none','#b59e79',6):R(x-3,y-3,w+6,h+6,'#b59e79',2);
      var pane=shape?P(shape,'white'):R(x,y,w,h,'white');
      var scenery=R(x,y,w,h,'url(#'+id+'sky)')+C(x+w*.75,y+h*.24,night?7:10,night?'#f0efda':'#fff1b9');
      scenery+=P('M'+x+' '+(y+h*.7)+'l'+w*.25+'-'+h*.2+' '+w*.3+' '+h*.16+' '+w*.25+'-'+h*.28+' '+w*.2+' '+h*.24+'V'+(y+h)+'H'+x+'Z',night?'#527579':'#91afa0');
      scenery+=P('M'+x+' '+(y+h*.87)+'q'+w*.3+'-'+h*.25+' '+w*.6+'-2t'+w*.4+' 0V'+(y+h)+'H'+x+'Z',night?'#395b60':'#6f9685');
      if(wet)for(var rain=9;rain<w;rain+=15)scenery+=L('M'+(x+rain)+' '+(y+15)+'l-5 19m8 18-5 22m8 19-5 20','#e2ecdf88',.8);
      return G('window','<defs><clipPath id="'+clip+'">'+pane+'</clipPath></defs>'+outline+'<g clip-path="url(#'+clip+')">'+scenery+'</g>'+L('M'+(x+w*.5)+' '+(y+3)+'V'+(y+h)+'M'+x+' '+(y+h*.58)+'h'+w,'#e7e9d5',2)+R(x-5,y+h,w+10,5,'#e2cfac',1));
    }
    function cabinet(x,y,w,h,color){
      var s=E(x+w/2,y+h+4,w*.49,5,'#50664e18')+R(x+4,y+5,w-8,h,wood,3)+R(x,y,w,h-3,color||sage,3)+R(x,y,w,h-3,'url(#'+id+'surface)',3)+R(x+4,y+h-6,w-8,6,'#746f5138')+R(x-3,y-3,w+6,7,'url(#'+id+'countertop)',2)+L('M'+(x-1)+' '+(y-2)+'h'+(w+2),'#fff5dc',1);
      var n=Math.max(1,Math.floor(w/50)),dw=w/n;
      for(var i=0;i<n;i++)s+=R(x+i*dw+5,y+9,dw-10,h-22,'none',2,'stroke="#eef0d5" stroke-width=".8"')+L('M'+(x+i*dw+8)+' '+(y+h-15)+'v-'+Math.max(2,h-28),'#53654c30',1)+L('M'+(x+i*dw+dw*.64)+' '+(y+18)+'h'+dw*.18,'#685b4544',2.7)+L('M'+(x+i*dw+dw*.64)+' '+(y+17)+'h'+dw*.18,'#f6db9f',1.7);
      return G('cabinet',s);
    }
    function shelf(x,y,w,h,market){
      var rows=4,rh=(h-12)/rows;
      var s=E(x+w/2,y+h+5,w*.48,4,'#596a4e20')+R(x,y,w,h,'#b79973',3)+R(x+6,y+7,w-12,h-14,'#8f856c',1)+R(x-2,y-3,w+4,5,'url(#'+id+'countertop)',1);
      for(var row=0;row<rows;row++){
        var yy=y+8+row*rh;
        s+=R(x+6,yy,w-12,rh-4,'#b9ad8e')+R(x+6,yy,w-12,4,'#73664f25')+R(x+5,yy+rh-4,w-10,4,'url(#'+id+'countertop)',1);
        for(var j=0,bx=x+10;bx<x+w-13;j++,bx+=market?19:10){
          var bh=rh*(.56+(j+row)%3*.08),color=['#b6a5bd','#a8b995','#bba17c','#8faeb0','#c3a2a2'][(j+row)%5];
          if(!market&&row%2===1&&j===2&&rh>30){
            for(var stack=0;stack<3;stack++)s+=R(bx,yy+rh-9-stack*6,25,5,['#c4b1b9','#e5d8bd','#9db4a2'][stack],1)+L('M'+(bx+4)+' '+(yy+rh-7-stack*6)+'h17','#eee6cf',.6);
            bx+=20;j+=2;continue;
          }
          s+=R(bx,yy+rh-bh-5,market?14:7,bh,color,market?3:1)+L('M'+(bx+2)+' '+(yy+rh-bh)+'h'+(market?10:3),'#f0e4cb',.7);
          if(market)s+=R(bx+3,yy+rh-bh*.6,8,5,cream,1);
          else s+=L('M'+(bx+1)+' '+(yy+rh-9)+'h5M'+(bx+2)+' '+(yy+rh-bh+5)+'v'+Math.max(1,bh*.27),'#fff1d470',.7);
        }
      }
      return G(market?'goods-shelf':'bookshelf',s+L('M'+(x+3)+' '+(y+7)+'v'+(h-12),'#ecd5b3',1)+R(x+6,y+h-3,w-12,5,'#917d5e',1));
    }
    function chair(x,y,color){return G('chair',E(x,y+30,17,4,'#50664e18')+L('M'+(x-10)+' '+y+'l-3 28m23-28 3 28',wood,3)+R(x-14,y-32,28,28,color||'#b5a6ba',6)+R(x-14,y-32,28,28,'url(#'+id+'surface)',6)+R(x-10,y-28,20,20,'none',4,'stroke="#eee3d1" stroke-width=".7" stroke-dasharray="1.5 1.6"')+C(x,y-18,1.2,'#ecdfd7')+E(x,y+1,17,5,'#b89d75')+E(x,y-2,16,5,sage)+E(x,y-3,13,3,'#c0cbaa')+L('M'+(x-13)+' '+(y+24)+'h26','#a58d6b',1.2));}
    function table(x,y,w){return G('round-table',E(x,y+47,w*.65,7,'#4c624b20')+L('M'+x+' '+y+'v43',wood,5)+L('M'+(x-1)+' '+(y+8)+'v32','#efdaba',1)+E(x,y+44,w*.4,4,'#a38965')+E(x,y+3,w,12,'#ae916b')+E(x,y,w,12,'url(#'+id+'countertop)')+E(x,y-1,w-4,9,'none').replace('fill="none"','fill="none" stroke="#f0debd" stroke-width=".8"')+L('M'+(x-w*.6)+' '+(y+3)+'q'+w*.3+'-4 '+w*.65+' 0','#aa89653b',.7)+E(x-w*.32,y-1,9,3,cream)+R(x-w*.32-5,y-10,10,8,cream,2)+E(x-w*.32,y-10,5,2,'#8b6c50')+L('M'+(x-w*.32+5)+' '+(y-8)+'q6-1 4 3q-1 2-4 1',cream,1.3));}
    function rug(x,y,w,h){return G('woven-rug',R(x,y+2,w,h,'#6a6c4a18',12)+R(x,y,w,h,'#c2b49b',10)+R(x+5,y+5,w-10,h-10,'none',7,'stroke="#ede0be" stroke-width="1.2"')+R(x+10,y+9,w-20,h-18,'url(#'+id+'venueweave)',5));}
    function clock(x,y){return G('wall-clock',C(x+1,y+2,18,'#71684e20')+C(x,y,18,'url(#'+id+'brass)')+C(x,y,15,cream)+L('M'+x+' '+(y-12)+'v2m12 10h-2m-10 12v-2m-12-10h2',wood,1.3)+L('M'+x+' '+(y-8)+'v8l6 3',ink,1.5)+C(x,y,1.5,ink));}
    function wallSconce(x,y){return G('wall-sconce',E(x,y+5,25,32,'#ffe7a41b')+R(x-3,y-9,6,27,'#ad9875',2)+P('M'+(x-9)+' '+(y-14)+'h18l5 18h-28Z','url(#'+id+'brass)')+E(x,y+4,14,3,'#fff1c4'));}
    function armchair(x,y){return G('reading-armchair',E(x+35,y+65,39,8,'#56614d20')+L('M'+(x+9)+' '+(y+53)+'v14m51-14v14',wood,4)+R(x+4,y-8,62,59,'#a693ad',10)+R(x+10,y-3,50,37,'#c5b3c5',8)+R(x+13,y,44,29,'none',6,'stroke="#e6d6df" stroke-width=".7" stroke-dasharray="2 2"')+R(x+7,y+31,56,23,'#a797ad',7)+R(x+10,y+30,50,16,'#cabaca',6)+R(x,y+18,11,36,'#b29db7',5)+R(x+59,y+18,11,36,'#b29db7',5)+R(x+19,y+12,25,22,'#b6c5a4',5)+L('M'+(x+23)+' '+(y+16)+'l16 14m-16 0 16-14','#e0e6c6',.7));}
    function curtains(x,y,w,h){
      var s=L('M'+(x-12)+' '+(y-8)+'h'+(w+24),wood,3)+C(x-14,y-8,3,'#d3bc91')+C(x+w+14,y-8,3,'#d3bc91');
      [x-9,x+w-21].forEach(function(cx){s+=P('M'+cx+' '+(y-4)+'h30l-6 '+h+'q-9 5-23 0Z','#c8c2a8');for(var j=6;j<28;j+=7)s+=L('M'+(cx+j)+' '+(y+2)+'l-3 '+(h-8),j%2?'#f1e8cc':'#aaa78b',1);s+=L('M'+cx+' '+(y+h*.65)+'h24','#b59b76',2);});
      return G('linen-curtains',s);
    }
    function meal(x,y){return G('place-setting',R(x-29,y-11,58,28,'#a9b69a',3)+L('M'+(x-26)+' '+(y+14)+'h52','#dfe2c5',.7)+E(x,y+2,18,7,'#778c7a40')+E(x,y,18,7,cream)+E(x,y,13,4,'#d9e2c9')+L('M'+(x-23)+' '+(y-6)+'v14m-2-14v4m4-4v4M'+(x+23)+' '+(y-6)+'v14',ink,1)+R(x+28,y-7,9,9,'#dfebe080',2,'stroke="#f4f0d9" stroke-width=".8"'));}
    function readingDesk(x,y,w){return G('reading-desk',L('M'+(x+8)+' '+y+'v45m'+(w-16)+'-45v45',wood,5)+R(x,y,w,8,'#d5bb91',3)+R(x+3,y+8,w-6,7,'#b69b77',1)+goods('book_cloud',x+22,y-28,28,28)+L('M'+(x+w-30)+' '+y+'v-28',ink,2)+P('M'+(x+w-45)+' '+(y-30)+'q15-15 30 0v6h-30Z','#88a590')+E(x+w-30,y,11,2,ink));}
    function picture(x,y,w,h,variant){return G('wall-art',R(x,y,w,h,'#b8a17d',2)+R(x+4,y+4,w-8,h-8,cream,1)+R(x+10,y+10,w-20,h-20,variant?'#b5c6b3':'#c6b5c9',1)+C(x+w*.68,y+h*.28,Math.min(w,h)*.1,'#e8cf9a')+P('M'+(x+11)+' '+(y+h-11)+'l'+w*.28+'-'+h*.4+' '+w*.21+' '+h*.23+' '+w*.23+'-'+h*.35+' '+w*.1+' '+h*.52+'Z',variant?'#809f91':'#96aaa4'));}
    function detailDefs(){return '<defs>'+
      '<linearGradient id="'+id+'surface" x2="0" y2="1"><stop stop-color="#fff7df" stop-opacity=".24"/><stop offset=".55" stop-color="#fff7df" stop-opacity="0"/><stop offset="1" stop-color="#485548" stop-opacity=".18"/></linearGradient>'+
      '<linearGradient id="'+id+'brass" x2="0" y2="1"><stop stop-color="#e8d4a8"/><stop offset=".45" stop-color="#d3ba8b"/><stop offset="1" stop-color="#b59c72"/></linearGradient>'+
      '<linearGradient id="'+id+'countertop" x2="0" y2="1"><stop stop-color="#f0dfbe"/><stop offset=".5" stop-color="#ddc6a1"/><stop offset="1" stop-color="#c3a37c"/></linearGradient>'+
      '<linearGradient id="'+id+'lamplight" x2="0" y2="1"><stop stop-color="#fff0bd" stop-opacity="'+(night?'.25':'.13')+'"/><stop offset="1" stop-color="#fff0bd" stop-opacity="0"/></linearGradient>'+
      '<linearGradient id="'+id+'wallwash" x2="0" y2="1"><stop stop-color="#fffae8" stop-opacity=".22"/><stop offset="1" stop-color="#8a836d" stop-opacity=".08"/></linearGradient>'+
      '<pattern id="'+id+'venueweave" width="5" height="5" patternUnits="userSpaceOnUse">'+L('M0 1h5M1 0v5','#f0e4cd55',.65)+'</pattern></defs>';}
    // The composition keeps a clear foreground aisle for the independently rendered character.
    b.push(root.SceneStudio.materialDefs(id,env),'<defs><pattern id="'+id+'floorgrain" width="72" height="23" patternUnits="userSpaceOnUse">'+L('M3 8q16-5 35 0m7 10 22-2','#f2dfba55',.7)+'</pattern></defs>');
    b.push(detailDefs());
    b.push(R(0,0,620,440,wall),P('M0 0h36v267L0 440Z',dark?'#797487':'#d7dec7'),P('M584 0h36v440l-36-173Z',dark?'#686477':'#bcccb7'));
    b.push(P('M36 267h548l36 173H0Z',style==='gallery'?'#d2cdbb':style==='greenhouse'?'#b6c0a7':dark?'#8a8190':'#c8b08c'));
    for(var row=280,step=14;row<440;row+=step,step+=4)b.push(L('M0 '+row+'h620',dark?'#c3b3c62b':'#e9dabd77',.8));
    for(var bx=-200;bx<900;bx+=88)b.push(L('M'+(310+(bx-310)*.4)+' 267L'+bx+' 440','#8d806345',.65));
    b.push(R(36,268,548,172,'url(#'+id+'floorgrain)'),R(36,216,548,50,dark?'#8c8496':'#b9c7aa'),L('M36 216h548M36 267h548',cream,2),L('M35 17h550',cream,4));
    if(!dark)for(var panel=48;panel<570;panel+=53)b.push(R(panel,227,40,28,'none',2,'stroke="#e5e6cc" stroke-width=".8"'));
    b.push(R(36,20,548,195,'url(#'+id+'wallwash)'),R(36,21,548,3,'#9a987326'),L('M36 211h548','#d4c9ac',1),R(36,262,548,5,'#8f99734a'),L('M36 262h548','#eee4cc',1));
    if(style==='cafe')b.push(rug(62,314,218,66));
    if(style==='books'||style==='library')b.push(rug(66,318,270,74));
    if(style==='hotel')b.push(rug(53,306,301,84));
    if(style==='cafe'){
      b.push(window(54,57,166,151,true),R(230,73,88,104,'#9c896d',3),R(235,78,78,94,'#688174',2),T(274,98,'COFFEE',11,cream),L('M248 112h50m-50 14h32m-32 13h45m-45 13h36','#dae0c8',1));
      b.push(cabinet(280,238,280,63),art('coffee',304,186,40,52),art('pourover',356,199,24,39),art('tea',405,214,55,22));
      b.push(R(320,148,220,5,wood,1));for(var cup=330;cup<530;cup+=28)b.push(R(cup,135,12,12,cream,2),L('M'+(cup+12)+' 138q9 0 0 7',cream,1.5));
      b.push(clock(560,93),R(343,169,145,4,wood,1));
      [351,378].forEach(function(x){b.push(P('M'+x+' 153h17l2 16h-21Z','#b29777'),L('M'+x+' 155h17','#ead4b0',1),R(x+3,158,11,7,cream,1),E(x+8,161.5,2,2.5,'#8f795f'));});
      b.push(R(414,156,23,13,'#c0b09c',2),T(425,165,'TEA',5,cream),R(445,156,23,13,'#b8b89e',2),T(456,165,'TEA',5,cream));
      b.push(pendant(356,72),pendant(491,72),chair(92,336),chair(235,336),table(163,325,53),plant(565,323,1.1));
    }else if(style==='books'||style==='library'){
      b.push(shelf(49,48,144,224),window(220,62,171,148,true),shelf(420,48,148,224),pendant(300,64));
      if(style==='books')b.push(R(214,231,177,5,wood),goods('book_garden',235,192,32,39),goods('book_sea',280,192,32,39),goods('book_cat',326,192,32,39),armchair(79,310),table(216,339,37));
      else b.push(readingDesk(208,247,187),chair(252,292),chair(353,292),readingDesk(75,341,242));
      b.push(wallSconce(204,133),wallSconce(405,133));
      if(style==='books')b.push(R(217,274,183,4,'#bdab8a',1),R(222,257,44,17,'#e2d1b5',2),T(244,268,'本周推荐',7),R(282,257,31,17,'#aebda0',2),R(328,257,64,17,'#d1b7bf',2));
      b.push(R(52,281,133,5,wood,1),T(118,296,'文学 · 旅行 · 生活',7),plant(560,314,1),T(300,39,style==='books'?'新书 · 慢慢翻阅':'静阅区',10));
    }else if(style==='gallery'){
      b.push(picture(65,75,130,133,0),picture(234,72,149,108,1),picture(424,75,124,133,0));
      [126,307,484].forEach(function(x){b.push(L('M'+x+' 22v15','#9f9e88',2),R(x-8,34,16,9,ink,2),P('M'+(x-5)+' 43l-42 160h94l-42-160Z','#fff3c420'));});
      b.push(G('gallery-bench',R(86,329,160,7,'#d3bd99',3)+R(89,336,154,5,'#b69b76',1)),L('M101 344v25m130-25v25',wood,4),R(304,291,65,70,'#e3dccb',1),E(336,290,25,6,'#f4efdf'),P('M318 286q-18-43 12-60 40 10 19 53Z','#a2b7aa','#7f978a',1));
      b.push(R(116,216,34,12,'#f8f3e7',1),R(289,187,39,15,'#f8f3e7',1),R(469,216,34,12,'#f8f3e7',1),L('M311 299v52h46','#bbb8a3',1),R(314,311,22,9,'#f8f3e7',1));
      b.push(T(133,223,'光与色',8),T(308,197,'山林的形状',8),T(485,224,'午后',8));
    }else if(style==='bakery'){
      b.push(window(52,63,143,144,false),shelf(408,65,146,197,true));
      b.push(cabinet(62,254,318,62,'#c6af93'),R(70,191,302,63,'#9fc0b75c',3,'stroke="#e6e8d1" stroke-width="2"'),L('M74 230h294','#d4d8bb',2));
      b.push(P('M72 194h82l-26 57H74Z','#ffffff20'),L('M75 195h292M75 234h292','#f7f4de',.8));
      for(var label=0;label<5;label++)b.push(R(87+label*53,247,27,7,cream,1),L('M'+(93+label*53)+' 250h14','#ac9877',.7));
      for(var row=0;row<2;row++)for(var loaf=0;loaf<5;loaf++){var xx=101+loaf*53,yy=218+row*24;b.push(E(xx,yy,18,7,'#d2a76c'),L('M'+(xx-8)+' '+(yy-3)+'l3 5m3-7 3 5m3-7 3 5','#f4d59e',1.3));}
      b.push(clock(356,110));
      b.push(cabinet(421,268,113,43,'#c5b299'),art('oven',435,210,86,58),pendant(126,60),pendant(307,60),chair(99,356),table(165,341,44),goods('cake',169,311,30,29),T(271,130,'今日出炉',15),T(271,153,'酸种面包 · 牛角可颂',9));
    }else if(style==='flowers'||style==='greenhouse'){
      b.push(window(57,43,503,190,true));
      if(style==='greenhouse'){
        for(var rib=92;rib<560;rib+=57)b.push(L('M'+rib+' 79V250','#dbe3cd',2));
        b.push(cabinet(65,263,164,46,'#b2b997'),cabinet(336,263,219,46,'#aab697'));
        b.push(L('M45 251h530','#e5e9d3',3));
        [89,133,178,357,405,451,517].forEach(function(x,i){
          var pot=plant(x,245,1.1+i%3*.25);
          if(i%3===1)pot=pot.replace(/#a7b99c/g,'#8faa8f').replace(/#bfd0a8/g,'#c5d7a5');
          if(i%3===2)pot=pot.replace(/#a7b99c/g,'#8eae9b');
          b.push(pot,L('M'+(x+12)+' 267v-15',ink,1),R(x+5,248,22,9,cream,1),T(x+16,255,['蕨类','观叶','香草'][i%3],5));
        });
        b.push(R(264,287,43,31,'#e3d8bc',2,'stroke="#b5a584"'),T(285,299,'温室导览',7),L('M271 305h28m-28 5h20','#a0b198',1),L('M270 318v25m30-25v25',wood,2));
        b.push(R(80,350,218,8,wood,3),L('M96 358v26m185-26v26',ink,3),T(301,47,'温室 · 观察与休憩',10));
      }else{
        b.push(cabinet(302,265,247,50),goods('flowers',340,201,57,61),goods('paint_set',444,224,37,39),R(406,247,30,10,'#d6c2b6',1));
        [74,132,191,249].forEach(function(x,i){b.push(R(x,281,38,52,i%2?'#a0b5a4':'#c4b3a2',4),goods('flowers',x-8,226,53,67));});
        b.push(L('M75 54h180',wood,3),goods('plant',103,77,52,70),goods('plant',186,69,48,68),L('M128 55v28m80-28v23',wood,1.5));
      }
    }else if(style==='office'){
      b.push(window(220,50,338,150,false),R(55,77,130,99,'#abbda9',2,'stroke="#d3c4a4" stroke-width="4"'),R(69,95,32,26,cream,1),R(115,110,49,22,'#d0bbcb',1));
      [[61,265,210],[315,265,240]].forEach(function(q){b.push(readingDesk(q[0],q[1],q[2]),art('screen',q[0]+40,q[1]-53,64,43),L('M'+(q[0]+72)+' '+(q[1]-10)+'v9',ink,3),art('keyboard',q[0]+46,q[1]-8,54,7));});
      b.push(clock(294,35),R(74,100,20,1,'#baaa8a'),R(120,116,30,1,'#ac96a9'));
      b.push(chair(165,316),chair(397,316),plant(571,264,1),shelf(55,142,117,80,true));
    }else if(style==='canteen'){
      b.push(window(329,53,220,134,false),curtains(329,53,220,134),cabinet(59,216,256,75,'#b6c6b4'),R(63,205,248,16,'#c5d4c4',2));
      for(var tray=0;tray<4;tray++)b.push(E(95+tray*59,208,24,8,'#769b90'),E(95+tray*59,206,20,5,tray%2?'#b8c792':'#d2b184'),L('M'+(93+tray*59)+' 191q-6-9 0-17','#edf0db',1.3));
      b.push(R(60,70,250,67,'#b6b995',3),R(65,75,240,57,'none',2,'stroke="#e8e5c9" stroke-width=".7"'),T(184,95,'今日餐食',13,cream),T(184,117,'热菜 · 汤品 · 主食',10,cream),pendant(164,48));
      b.push(cabinet(365,226,179,51,'#cab79a'),art('tea',385,204,61,22),R(469,207,29,18,cream,2),L('M474 211h19m-19 4h19m-19 4h19','#c0ba9e',1),T(505,220,'餐具',6));
      // Chairs behind the dining tabletop; a clear aisle remains on the right.
      b.push(chair(127,316),chair(269,316),E(202,390,128,8,'#5363461a'),L('M86 350v40m233-40v40',wood,5),P('M91 324h220l21 32H70Z','url(#'+id+'countertop)'),R(70,355,262,8,wood,2));
      b.push(P('M170 325h59l8 31h-75Z','#d4d8b8'),meal(121,341),meal(282,341),E(199,344,10,3,'#89765a30'),P('M194 332h11l-2 12h-7Z',cream),L('M199 333v-15',ink,1),P('M199 328q-13-2-10-10 10 0 10 10m0-4q10 0 10-10-9 0-10 10',sage));
    }else if(style==='cinema'){
      b.push(R(35,26,549,241,'#716d82'),R(85,51,450,194,'#4f5365',5),R(95,61,430,174,'#afc8c7',2),P('M96 220l100-92 90 60 130-109 108 141Z','#77958d'),C(436,97,16,'#e8d9b5'));
      for(var row=0;row<3;row++)for(var col=0;col<4;col++){var xx=57+col*77,yy=284+row*41;b.push(R(xx,yy,59,32,'#a58293',7),R(xx+5,yy+4,49,23,'#c0a0b1',5),R(xx-3,yy+19,5,20,'#806779',2),R(xx+57,yy+19,5,20,'#806779',2));}
      b.push(R(36,29,42,233,'#766175'),R(542,29,42,233,'#766175'));
      for(var fold=42;fold<77;fold+=8)b.push(L('M'+fold+' 31v228M'+(fold+502)+' 31v228','#b398ad55',3));
      b.push(R(49,247,24,11,'#a2b798',1),T(61,255,'EXIT',6,cream));
      b.push(L('M379 277v143','#e7c58b',1.2));for(var marker=294;marker<425;marker+=28)b.push(R(386,marker,8,3,'#ffe4a5',1));
    }else if(style==='mall'){
      b.push(window(167,33,288,112,true));
      [55,240,425].forEach(function(x,i){b.push(R(x,170,141,115,'#b0bea8',3),R(x+7,178,127,102,'#cfdbce',2),R(x+8,151,125,24,i===1?'#c6b2c2':'#bda67e',2),T(x+70,167,['生活选物','日常衣橱','小小书屋'][i],10,cream));if(i===1)b.push(goods('coat',x+23,192,43,62),goods('skirt',x+79,205,43,52));else b.push(shelf(x+17,199,109,64,i===0));});
      b.push(R(70,340,227,11,wood,4),L('M87 351v25m192-25v25',ink,3),plant(346,342,1.3));
    }else if(style==='market'){
      b.push(shelf(57,81,150,199,true),shelf(235,81,150,199,true),R(414,82,140,191,'#a2b8b0',3),R(422,92,124,168,'#c5dacf',2));
      for(var sy=134;sy<250;sy+=38)b.push(L('M426 '+sy+'h116','#e2e9d2',2));
      for(var bottle=0;bottle<6;bottle++)b.push(goods(bottle%2?'juice':'milk',426+(bottle%3)*37,103+Math.floor(bottle/3)*77,30,46));
      b.push(cabinet(68,342,232,42,'#bdc5aa'),R(254,319,27,23,ink,2),R(258,323,19,12,'#abc5b6',1),T(299,52,key==='杂货铺'?'街角杂货':'新鲜与日常',13));
    }else if(style==='station'||style==='airport'){
      b.push(window(56,50,508,169,false));
      for(var mullion=158;mullion<560;mullion+=100)b.push(L('M'+mullion+' 52v164','#e8ead7',3));
      b.push(L('M246 21v23m128-23v23',ink,2),R(224,43,172,65,'#c6b99b',3),R(229,48,162,55,ink,2),T(310,64,style==='airport'?'出发 · DEPARTURES':'站台 · PLATFORM',9,cream));
      ['10:30    01    候车','12:00    03    准点','14:20    02    准点'].forEach(function(t,i){b.push(T(310,77+i*10,t,7,'#dfe4c5'));});
      b.push(R(58,235,319,8,'#b8c8bb',3),L('M70 239h295','#edf0d6',1),clock(437,238));
      for(var seat=0;seat<5;seat++){
        var sx=66+seat*62;
        b.push(E(sx+26,327,26,4,'#56655020'),L('M'+(sx+10)+' 302l-4 25m36-25 4 25',ink,3),R(sx,261,53,41,'#89a59b',5),R(sx+4,265,45,29,'#b6c8bb',4),R(sx+8,269,37,21,'none',3,'stroke="#e8e8cf" stroke-width=".7"'),R(sx-3,295,59,8,'url(#'+id+'countertop)',3),L('M'+(sx-2)+' 286v12m57-12v12',ink,3));
      }
      b.push(G('luggage',E(109,389,25,4,'#59634e25')+R(90,341,38,43,'#bda6be',5)+R(94,345,30,35,'#cdbdd0',3)+L('M101 348v28m8-28v28m8-28v28','#ac96b0',1)+L('M101 341v-14h16v14',ink,2)+R(101,325,16,4,ink,2)+C(98,386,3,ink)+C(120,386,3,ink)+R(125,346,9,11,cream,1)));
      b.push(G('information-kiosk',E(544,323,24,5,'#66715720')+P('M529 247h30l8 73h-46Z','#b8b9a5')+R(523,229,42,52,ink,4)+R(528,234,32,38,'#c2d7c4',2)+T(544,249,'i',15,ink)+L('M534 258h20m-20 5h14',ink,1)+R(532,317,24,4,'#7b8b79',1)));
    }else if(style==='hotel'){
      b.push(window(367,61,183,137,false),curtains(367,61,183,137),picture(117,55,119,89,1));
      b.push(E(176,347,131,10,'#5d645225'),R(57,180,228,94,'#ab906e',6),R(64,187,214,60,'#c2b3a2',5),R(69,192,204,49,'none',4,'stroke="#eee1cb" stroke-width="1"'));
      for(var tuft=0;tuft<5;tuft++)b.push(C(88+tuft*42,211,1.5,'#e6d5bf'));
      b.push(R(62,236,219,104,'#9a8167',5),R(59,228,224,103,'#e4dcc7',7),R(64,257,214,70,'#b6a5bd',5),R(64,257,214,70,'url(#'+id+'surface)',5),R(74,233,81,27,cream,7),R(183,233,81,27,cream,7),R(79,237,71,19,'none',5,'stroke="#d1c4ac" stroke-width=".7"'),R(188,237,71,19,'none',5,'stroke="#d1c4ac" stroke-width=".7"'));
      for(var stitch=91;stitch<270;stitch+=35)b.push(L('M'+stitch+' 268v41','#e7d8e3',.6));
      b.push(R(65,304,211,19,sage,2),R(68,306,205,14,'url(#'+id+'venueweave)',1),L('M70 309h201m-201 10h201','#e3e5c8',.6),L('M76 337v8m190-8v8',wood,4));
      b.push(cabinet(301,264,49,55),art('lamp',309,226,29,38),wallSconce(79,144),wallSconce(271,144));
      b.push(readingDesk(390,260,165),art('tea',432,237,53,23),R(509,245,26,14,'#d9d1b8',1),T(522,255,'WELCOME',4,ink),chair(406,318));
      b.push(G('luggage-bench',E(170,389,96,7,'#62644822')+L('M86 363v23m167-23v23',wood,4)+R(76,349,190,18,'#b39f84',4)+R(79,346,184,15,'#cec7b0',5)+L('M86 351h171','#f0e5cc',.8)));
    }else if(style==='camp'){
      b.push(P('M0 440L310 18 620 440Z','#c3bc9b'),P('M78 440L310 63 542 440Z','#8da397'),P('M200 318l110-206 110 206Z','#587b71'),L('M310 24v72',wood,2),art('lamp',286,85,48,60),R(93,325,194,66,'#b1bfa1',20),R(105,333,39,50,cream,13),art('tea',305,298,90,34),R(288,327,127,9,wood,3),L('M300 336v36m102-36v36',ink,3));
    }else{
      b.push(window(60,61,213,158,false),shelf(322,67,222,182,style==='bar'),cabinet(322,247,222,48,style==='bar'?'#b4a0ae':'#b8be9d'),pendant(153,62),pendant(427,57));
      b.push(chair(91,340),chair(239,340),table(165,326,54),art('tea',142,305,53,22));
      if(style==='shrine')b.push(L('M70 64h190',wood,3),R(80,238,173,8,wood,2),goods('candle',113,201,26,39),goods('storage_box',173,204,35,36));
    }
    if(night)b.push(R(0,0,620,440,'#213b521e'));
    else if(env.band==='dusk')b.push(R(0,0,620,440,'#edbf8320'));
    return '<svg class="garage-destination-art destination-interior-detailed" data-interior-style="'+style+'" data-time="'+env.band+'" data-weather="'+env.weather+'" viewBox="0 0 620 440" preserveAspectRatio="xMidYMid slice" role="img" aria-label="'+esc(key)+'室内装潢">'+b.join('')+'</svg>';
  }
  root.DestinationInteriors={draw:draw,places:Object.keys(styles)};
})(window);
