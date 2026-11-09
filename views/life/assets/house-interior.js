/* Architectural finishes share the room's physical coordinates. No interaction targets. */
(function(root){
  'use strict';
  var palettes={
    '客厅':['#eee6d4','#aabda5','#c8ac85'], '卧室':['#f0e3df','#c9b9c6','#c7a88c'],
    '餐厅':['#eee1c6','#b6c4a1','#c8aa80'], '书房':['#e7e8d8','#a1b7ad','#bfa580'],
    '画室':['#f3e9d6','#ccd2b3','#d1b895'], '影音室':['#d8d0df','#918d9f','#aa968a'],
    '衣帽间':['#f0e6df','#c1b5b3','#c9af92'], '健身室':['#e2e9dd','#a8beb2','#bead94'],
    '浴室':['#e4eddf','#b4cec6','#dbe4d2'], '厨房':['#f0ead7','#b9c7aa','#d8ddc6'],
    '车库':['#e4e2da','#cfd2cc','#9a9c98']
  };
  function theme(room){var p=palettes[room]||['#eee5d1','#b8c5a5','#c8af8c'];return {wall:p[0],side:p[1],floor:p[2],tile:/浴室|厨房/.test(room),open:/阳台|露台/.test(room)};}
  function rect(x,y,w,h,fill,stroke,r){return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(r||0)+'" fill="'+fill+'" '+(stroke?'stroke="'+stroke+'" stroke-width=".6"':'')+'/>';}
  function line(d,color,width){return '<path d="'+d+'" fill="none" stroke="'+color+'" stroke-width="'+(width||.6)+'"/>';}
  function floor(room,w,d){
    var t=theme(room),id='finish-'+Object.keys(palettes).indexOf(room),b=[];
    if(t.tile){
      var c=room==='浴室'?'#c8dcd3':'#e2dfcb';
      b.push('<defs><pattern id="'+id+'" width="28" height="28" patternUnits="userSpaceOnUse">'+rect(0,0,28,28,'#b3c4b3')+rect(1,1,26,26,c,null,1)+line('M3 4l8-1m7 21 7-1','#ffffff55',1)+rect(12,12,4,4,room==='浴室'?'#9db9ad':'#c1c8a7',null,.5)+'</pattern></defs>');
    }else{
      b.push('<defs><pattern id="'+id+'" width="84" height="32" patternUnits="userSpaceOnUse">'+rect(0,0,84,32,t.floor)+rect(0,0,42,16,'#fff8df17')+rect(22,16,42,16,'#745b3910')+line('M0 0h84M0 16h84M0 32h84M42 0v16M22 16v16M64 16v16','#826d5050',.6)+line('M3 7q14-4 33 0M46 10q17-4 34-2M25 23q14-3 32 0M2 27h15','#f6e3be77',.55)+'</pattern></defs>');
    }
    b.push(rect(0,0,w,d,'url(#'+id+')'),rect(3,3,w-6,d-6,'none','#f7ebcf'));
    if(!t.open&&!t.tile)b.push(rect(7,7,w-14,d-14,'none','#a8926f55'));
    return '<g class="architectural-floor" pointer-events="none">'+b.join('')+'</g>';
  }
  function walls(room,size,c,api,e){
    var t=theme(room);if(t.open)return '';
    var w=size.w,d=size.h,h=c.wall,side=c.a>0?w:0,b=[],fa=api.front,poly=api.polygon,ln=api.line;
    // Lower wall panels, crown moulding and a continuous skirting board.
    b.push(poly([[0,0,0],[w,0,0],[w,0,32],[0,0,32]],t.side),poly([[side,0,0],[side,d,0],[side,d,32],[side,0,32]],t.side));
    b.push(ln([0,0,3],[w,0,3],'#f6eedb',3),ln([side,0,3],[side,d,3],'#dce4cf',3),ln([0,0,32],[w,0,32],'#f8efdb',2.5),ln([side,0,32],[side,d,32],'#dfe6d0',2));
    b.push(ln([0,0,29],[w,0,29],'#7d8b7026',1),ln([side,0,29],[side,d,29],'#6c806926',1),ln([0,0,h-3],[w,0,h-3],'#fff5e1',2),ln([side,0,h-3],[side,d,h-3],'#ecedda',1.8));
    b.push(ln([0,0,h-8],[w,0,h-8],'#d7c7ab',1),ln([side,0,h-8],[side,d,h-8],'#c1cbb5',1));
    // Carry the room finish around the corner in world space, behind every furnishing.
    var sideFace=side===0?'E':'W';
    if(t.tile){
      for(var ty=35;ty<125;ty+=12){
        b.push(ln([side,0,ty],[side,d,ty],'#f8f6e780',.6));
        for(var td=(ty%24===11?0:12);td<d;td+=24)b.push(ln([side,td,ty],[side,td,Math.min(ty+12,125)],'#f8f6e76b',.55));
      }
      if(room==='浴室')b.push(ln([0,0,57],[w,0,57],'#93b4ab',1.3),ln([side,0,57],[side,d,57],'#93b4ab',1.3),ln([0,0,59],[w,0,59],'#f5f4df',.7),ln([side,0,59],[side,d,59],'#f5f4df',.7));
    }else{
      for(var sp=10;sp+30<d;sp+=40)b.push(fa(side,sp,7,0,30,19,sideFace,rect(0,0,30,19,'none','#e5e5d0',1)));
      if(room==='影音室'){
        for(var ac=12;ac+22<d;ac+=31)b.push(fa(side,ac,44,0,22,68,sideFace,rect(0,0,22,68,'#817f91','#bcb3c7',3)+rect(3,3,16,62,'none','#9992a8',2)));
      }else if(/客厅|餐厅|卧室|衣帽间/.test(room)){
        for(var fr=14;fr+43<d;fr+=59)b.push(fa(side,fr,45,0,43,69,sideFace,rect(0,0,43,69,'none','#dae0ca88',2)+rect(2,2,39,65,'none','#6f806318',1)));
      }
    }
    if(/客厅|餐厅|书房/.test(room)){
      // Botanical reliefs sit high on the side wall, clear of the floor and windows.
      var frames=room==='餐厅'?2:3,span=30,total=frames*span-8,start=(d-total)*.5;
      for(var f=0;f<frames;f++){
        var relief=rect(0,0,22,30,'#c6b08c','#a89371',1)+rect(2,2,18,26,'#f5ecda',null,.5);
        if(f%2===0)relief+='<path d="M11 24V9m0 11Q2 19 5 13q7 0 6 7m0-5q8-1 7-8-8 1-7 8" fill="#a3b59a" stroke="#859d7f" stroke-width=".4"/>';
        else relief+='<circle cx="14" cy="10" r="4" fill="#d5ba8b"/><path d="M4 25l7-14 7 14Z" fill="#a7b8ad"/>';
        b.push(fa(side,start+f*span,88,0,22,30,sideFace,relief));
      }
    }
    if(room==='卧室'){
      // Fine botanical wallpaper, spaced far enough apart to read as a quiet texture.
      for(var leafX=9;leafX<w;leafX+=21)for(var leafZ=43;leafZ<122;leafZ+=23){
        b.push(fa(leafX,-.15,leafZ,9,0,12,'S','<path d="M4 11V2m0 6Q-2 8 1 3q5 0 3 5m0-2q7-1 4-6Q4 0 4 6" fill="#b79eb221" stroke="#aa8fa82e" stroke-width=".35"/>'));
      }
    }
    if(e.dark||e.band==='dusk'){
      var light=room==='影音室'?'#d6bfdc':'#ffe8b5',opacity=e.dark?.65:.28;
      b.push('<g class="interior-cove-light" opacity="'+opacity+'">',ln([0,0,h-6],[w,0,h-6],light,6),ln([side,0,h-6],[side,d,h-6],light,4),ln([0,0,h-6],[w,0,h-6],'#fff4d5',1.2),'</g>');
    }
    if(t.tile){
      for(var row=35;row<125;row+=12){
        b.push(ln([0,0,row],[w,0,row],'#f6f7e599',.65));
        for(var x=(row%24===11?0:12);x<w;x+=24)b.push(ln([x,0,row],[x,0,Math.min(row+12,125)],'#f9f7e999',.6));
      }
      if(room==='厨房')b.push(fa(w*.73,-.4,91,43,0,22,'S',rect(0,0,43,22,'#e0d5b9','#b5a27f',1)+rect(3,3,37,16,'#f5edd9')+line('M10 7v9m8-9v9m8-9v9m8-9v9','#8b9d7b',1.3)));
    }else if(room==='影音室'){
      for(var slat=8;slat<w;slat+=7)b.push(ln([slat,0,34],[slat,0,121],'#b1a3b466',1.8));
    }else{
      for(var panel=10;panel+30<w;panel+=40)b.push(fa(panel,-.2,7,30,0,19,'S',rect(0,0,30,19,'none','#e6e4cf',1)));
      // A quiet pinstripe finish above the dado, with distinct room palettes.
      for(var stripe=6;stripe<w;stripe+=10)b.push(ln([stripe,0,34],[stripe,0,h-10],'#fff9e526',.5));
    }
    // Doors and windows come from the shared openings table, so the close-up matches the plan and 3D.
    var O=((root.RoomModel||{}).openings||{})[room],nwin=O?(O.N||[]).filter(function(o){return o[2]==='win';})[0]:null;
    function doorArt(dw,kind){var glass=kind==='glass',leaf=glass?'#f4efe4':kind==='entry'?'#7d8f78':'#b08a63',pan=glass?'#cfe3e0':kind==='entry'?'#8fa189':'#c29d75';
      return rect(-2,-3,dw+4,109,'#f3ead8','#cdbb98',1)+rect(0,0,dw,106,leaf,'#8e7a62',1)+(glass?rect(4,5,dw/2-6,72,pan,'#e8e2d4',1)+rect(dw/2+2,5,dw/2-6,72,pan,'#e8e2d4',1)+line('M'+dw/2+' 0v106','#d8cdb8',1):rect(5,8,dw-10,40,pan,null,1)+rect(5,56,dw-10,44,pan,null,1))+'<circle cx="'+(glass?dw/2+(dw>30?-4:-2):dw-6)+'" cy="58" r="1.8" fill="#c8ad7c"/>';}
    if(O){
      (O.N||[]).forEach(function(o){if(o[2]!=='win')b.push(fa(o[0],-.45,0,o[1]-o[0],0,106,'S',doorArt(o[1]-o[0],o[2])));});
      ((side?O.E:O.W)||[]).forEach(function(o){var len=o[1]-o[0];if(o[2]==='win')b.push(fa(side,o[0],68,0,len,52,sideFace,rect(-2,-2,len+4,56,'#f3ead8','#cdbb98',1)+rect(0,0,len,52,'#c9e0dc','#e8e2d4',1)+line('M'+len/2+' 0v52M0 '+(52*.36)+'h'+len,'#f6f1e6',1.6)));else b.push(fa(side,o[0],0,0,len,106,sideFace,doorArt(len,o[2])));});
    }
    if(O?nwin:room!=='影音室'){
      var wx=O?nwin[0]:w*.35,ww=O?nwin[1]-nwin[0]:w*.3;
      b.push(api.box(wx-3,0,65,ww+6,5,3,'#d0bd98','#f7edd7'));
      b.push(fa(wx+5,-.4,72,ww-10,0,42,'S',line('M4 3l12 0-12 16M22 4l9 0-21 28','#fffdf54a',2)));
      if(!t.tile&&!/玄关|楼梯厅/.test(room)){
        var cloth=room==='卧室'?'#cbb4c7':room==='书房'?'#a4b8ac':room==='餐厅'?'#b7bd9a':'#d6c5aa';
        b.push(ln([wx-19,1,128],[wx+ww+19,1,128],'#a58d68',1.7));
        [wx-20,wx+ww+20].forEach(function(end){var q=c.point(end,1,128);b.push('<circle cx="'+q[0]+'" cy="'+q[1]+'" r="'+2*c.s+'" fill="#c1a274"/>');});
        [wx-17,wx+ww+1].forEach(function(x,n){
          var drape='<path d="M0 0H17Q15 27 10 48Q12 62 16 85Q8 88 0 85Z" fill="'+cloth+'" stroke="#b1a38d" stroke-width=".45"/>'+line('M3 3Q6 27 4 48L3 83M8 3Q11 27 7 48L8 83M13 3Q15 27 9 48L13 83','#fff5e490',.9)+line('M2 48Q7 51 11 48','#9d865f',1.4)+line('M11 50l2 10','#c4a77c',.8);
          for(var ring=2;ring<17;ring+=4)drape+='<ellipse cx="'+ring+'" cy="1" rx="1.3" ry="2" fill="none" stroke="#aa916d" stroke-width=".6"/>';
          b.push(fa(x,-.6,40,17,0,87,'S','<g class="tailored-curtain"'+(n?' transform="translate(17 0) scale(-1 1)"':'')+'>'+drape+'</g>'));
        });
      }else if(t.tile){
        var blindColor=room==='浴室'?'#c5d5c6':'#ded3b9';
        b.push(fa(wx-2,-.5,119,ww+4,0,8,'S','<g class="window-blind">'+rect(0,0,ww+4,8,blindColor,'#b6b69e',1)+line('M2 3h'+ww+'m-'+ww+' 3h'+ww,'#f6eed8',.6)+'</g>'));
      }
    }
    // Decorative wall lamps belong to the architecture and do not obstruct furniture.
    if(/客厅|餐厅|卧室|书房/.test(room)){
      var lx=w*.86;
      b.push(fa(lx,-.6,88,14,0,25,'S',rect(6,4,2,20,'#b19c76',null,1)+'<path d="M3 2H11L14 13H0Z" fill="#f4e6c4" stroke="#c9b68f" stroke-width=".7"/>'+rect(4,23,6,2,'#b19c76',null,1)));
      if(e.dark){var p=c.point(lx+7,0,100);b.push('<ellipse cx="'+p[0]+'" cy="'+p[1]+'" rx="'+36*c.s+'" ry="'+42*c.s+'" fill="url(#close-warm)" opacity=".7"/>');}
    }
    return '<g class="architectural-detail" pointer-events="none">'+b.join('')+'</g>';
  }
  function rug(room,w,d){
    var color=room==='卧室'?'#c5b4bd':room==='书房'?'#a8b9ad':room==='影音室'?'#a9a1b5':room==='餐厅'?'#b9bea0':'#cfc1a4';
    var b=[rect(0,0,w,d,color,null,8),rect(4,4,w-8,d-8,'none','#eee7d2',5),rect(7,7,w-14,d-14,'none','#f6efdc',4)];
    if(room==='客厅'){
      for(var i=0;i<4;i++)b.push('<path d="M'+(w*.2+i*5)+' '+(d*.7)+'V'+(d*.4)+'a'+(w*.3-i*5)+' '+(d*.27-i*3)+' 0 0 1 '+(w*.6-i*10)+' 0v'+d*.3+'" fill="none" stroke="#f3e9d0" stroke-opacity=".48" stroke-width="1.2"/>');
      for(var dot=15;dot<w-12;dot+=9)b.push('<circle cx="'+dot+'" cy="11" r=".8" fill="#988f7055"/><circle cx="'+dot+'" cy="'+(d-11)+'" r=".8" fill="#988f7055"/>');
    }else if(room==='卧室'){
      for(var yy=18;yy<d-12;yy+=17)for(var xx=18;xx<w-12;xx+=20)b.push('<path d="M'+xx+' '+(yy-3)+'l3 3-3 3-3-3Z" fill="none" stroke="#ead9df" stroke-width=".6" opacity=".55"/>');
    }else if(room==='餐厅'){
      for(var edge=13;edge<w-12;edge+=10)b.push('<path d="M'+edge+' 10l4 4-4 4-4-4Zm0 '+(d-28)+'l4 4-4 4-4-4Z" fill="none" stroke="#ecdfc1" stroke-width=".75"/>');
      b.push(rect(14,22,w-28,d-44,'none','#dce0c1',2));
    }else if(room==='书房'){
      for(var yy=15;yy<d-10;yy+=12)b.push(line('M11 '+yy+'h'+(w-22),'#e6e9d252',.7));
      for(var xx=15;xx<w-10;xx+=12)b.push(line('M'+xx+' 11v'+(d-22),'#e6e9d235',.7));
    }else{
      for(var t=13;t<d-10;t+=9)b.push(line('M10 '+t+'h'+(w-20),'#eee5d125',.8));
    }
    if(!/阳台|露台/.test(room))for(var fringe=9;fringe<w-8;fringe+=4)b.push(line('M'+fringe+' 0l1-2M'+fringe+' '+d+'l1 2','#e8dcc2',.7));
    b.push(rect(0,0,w,d,'url(#close-weave)',null,8));
    return '<g class="room-rug" pointer-events="none">'+b.join('')+'</g>';
  }
  function art(room){
    var b=[rect(0,0,37,44,'#bca17a','#977f5f',2),rect(2,2,33,40,'#f5edda',null,1),rect(5,5,27,34,'none','#e5d7bb',1)];
    if(room==='卧室')b.push('<path d="M25 11a9 9 0 1 0 3 16 11 11 0 0 1-3-16Z" fill="#c1aec6"/>',line('M10 12v4m-2-2h4M27 32v4m-2-2h4','#baa67f',.8));
    else if(room==='书房')b.push('<path d="M8 33V15q6-4 11 0 5-4 10 0v18q-6-4-10 0-5-4-11 0Z" fill="#a8b9a9"/>',line('M19 15v18M10 20h6m-6 4h6m6-4h5m-5 4h5','#edf0d8',.8));
    else if(room==='餐厅')b.push('<ellipse cx="19" cy="28" rx="10" ry="5" fill="#c6c9a7"/><path d="M10 22h16q0 9-8 9t-8-9Z" fill="#b8a4b6"/>',line('M14 19q-4-5 0-8m6 8q-4-5 0-8','#b09e7f',.8));
    else if(room==='画室')b.push('<circle cx="14" cy="17" r="7" fill="#d9b68e"/><path d="M8 35l12-20 11 20Z" fill="#a1b6a0"/><path d="M8 29q12-12 22 2" fill="none" stroke="#b49cba" stroke-width="4"/>');
    else if(room==='健身室')b.push('<circle cx="19" cy="15" r="4" fill="#c7ae85"/>',line('M19 20v10m0-6-9 5m9-5 9-6m-9 12-9 6m9-6 9 6','#8aa59c',2));
    else b.push('<circle cx="26" cy="12" r="5" fill="#d5b482"/><path d="M7 34q-1-13 11-19m-8 14q-7-7-6-12 9 1 6 12m4-7q11-3 14-9-12-3-14 9" fill="#8ea685" stroke="#6e8e71" stroke-width=".5"/>');
    return b.join('');
  }
  root.HouseInterior={theme:theme,floor:floor,walls:walls,rug:rug,art:art};
})(window);
