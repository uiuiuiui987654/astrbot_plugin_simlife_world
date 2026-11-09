/* Shared vehicle artwork. Side views face east (nose on the right); top views point north (nose at y=0).
   draw(type,paint,dark) -> {width,art}  : side silhouette for traffic, garage cards and previews.
   top(type,paint,opts)  -> svg markup    : plan-view car, 44 wide x 100 long, for floor plans. */
(function(root){
  'use strict';
  var serial=0;
  function P(d,fill,extra){return '<path d="'+d+'" fill="'+fill+'" '+(extra||'')+'/>';}
  function R(x,y,w,h,c,r,extra){return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(r||0)+'" fill="'+c+'" '+(extra||'')+'/>';}
  function L(d,c,w,extra){return P(d,'none','stroke="'+c+'" stroke-width="'+(w||.7)+'" stroke-linecap="round" stroke-linejoin="round" '+(extra||''));}
  function C(x,y,r,c,extra){return '<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+c+'" '+(extra||'')+'/>';}
  function shade(hex,k){var n=parseInt(hex.slice(1),16),r=n>>16,g=n>>8&255,b=n&255;function f(v){return Math.max(0,Math.min(255,Math.round(k<0?v*(1+k):v+(255-v)*k)));}return '#'+((1<<24)|(f(r)<<16)|(f(g)<<8)|f(b)).toString(16).slice(1);}
  // Body proportions per type (east-facing). s:sill y, b:beltline, r:roof, rs/re:roof start/end, rb:rear glass base, wb:windshield base,
  // th:tail top, nh:nose top, wh:wheel x positions, wr:wheel radius.
  var SPEC={
    sedan:{w:110,s:43,b:27,r:7,rs:37,re:69,rb:24,wb:88,th:26,nh:29,wh:[22,88],wr:8.6},
    taxi:{w:110,s:43,b:27,r:7,rs:37,re:69,rb:24,wb:88,th:26,nh:29,wh:[22,88],wr:8.6},
    hatchback:{w:100,s:43,b:26,r:7,rs:20,re:62,rb:7,wb:80,th:19,nh:28,wh:[20,80],wr:8.4},
    wagon:{w:118,s:43,b:26,r:7,rs:13,re:76,rb:6,wb:95,th:18,nh:28,wh:[22,95],wr:8.6},
    suv:{w:114,s:41,b:24,r:3,rs:13,re:75,rb:7,wb:93,th:16,nh:24,wh:[23,91],wr:9.6},
    sports:{w:116,s:44,b:31,r:16,rs:40,re:66,rb:16,wb:88,th:30,nh:35,wh:[23,92],wr:8.8},
    jeep:{w:108,s:40,b:24,r:4,rs:10,re:74,rb:9,wb:78,th:15,nh:22,wh:[22,86],wr:10.2}
  };
  function wheelArt(x,y,r,o){o=o||{};var b=['<g transform="translate('+x+' '+y+')">'];
    b.push(C(0,0,r,'#1f2a27'),C(0,0,r-.9,'none','stroke="#3c4a45" stroke-width=".8"'));
    if(o.offroad)for(var t=0;t<12;t++)b.push(R(-1,-r-.4,2,2.2,'#1f2a27',.4,'transform="rotate('+t*30+')"'));
    b.push(C(0,0,r*.66,'#c8d2cc'),C(0,0,r*.6,'#9fb0a8'),'<g class="journey-wheel">');
    for(var i=0;i<(o.sport?10:5);i++)b.push(P('M-.9 '+(-r*.18)+'L-1.5 '+(-r*.56)+'L1.5 '+(-r*.56)+'L.9 '+(-r*.18)+'Z','#e6ece6','transform="rotate('+i*(o.sport?36:72)+')"'));
    b.push('</g>',C(0,0,r*.2,'#5e6f68'),C(0,0,r*.08,'#d8e0d8'));
    if(o.sport)b.push(R(r*.12,-r*.42,r*.22,r*.3,'#c8312b',.6));
    b.push(P('M'+(-r*.55)+' '+(-r*.5)+'A'+r*.75+' '+r*.75+' 0 0 1 '+(r*.45)+' '+(-r*.62),'none','stroke="#ffffff" stroke-opacity=".35" stroke-width=".8"'),'</g>');
    return b.join('');}
  function silhouette(S){var w=S.w,s=S.s,a=S.wh,ar=S.wr+2.6,k=S.r<10?4:3;
    // top edge: tail -> trunk/deck -> rear glass -> roof -> windshield -> hood -> nose
    var top='M3 '+(s-3)+'Q1 '+(S.th+3)+' 4 '+S.th+'L'+(S.rb-2)+' '+(S.b-1)+'Q'+(S.rs-6)+' '+(S.r+2)+' '+S.rs+' '+S.r+'L'+S.re+' '+S.r+'Q'+(S.re+k)+' '+S.r+' '+(S.re+k+2)+' '+(S.r+3)+'L'+(S.wb)+' '+(S.b-1)+'L'+(w-8)+' '+S.nh+'Q'+(w-1)+' '+(S.nh+1)+' '+w+' '+(S.nh+6)+'L'+w+' '+(s-4)+'Q'+w+' '+s+' '+(w-4)+' '+s;
    // bottom edge with wheel arches, front to rear
    var bot='L'+(a[1]+ar)+' '+s+'A'+ar+' '+ar+' 0 0 0 '+(a[1]-ar)+' '+s+'L'+(a[0]+ar)+' '+s+'A'+ar+' '+ar+' 0 0 0 '+(a[0]-ar)+' '+s+'L6 '+s+'Q3 '+s+' 3 '+(s-3)+'Z';
    return top+bot;}
  function glass(S){var c=S.r+2.4,bl=S.b-1.6,mid=(S.rs+S.re)/2+(S.re-S.rs)*.08;
    var rear='M'+(S.rb+2)+' '+bl+'Q'+(S.rs-4)+' '+(c+1)+' '+(S.rs+1.5)+' '+c+'L'+(mid-1.6)+' '+c+'L'+(mid-1.6)+' '+bl+'Z';
    var front='M'+(mid+1.6)+' '+c+'L'+(S.re-1)+' '+c+'Q'+(S.re+3)+' '+c+' '+(S.re+4.5)+' '+(c+2.5)+'L'+(S.wb-3)+' '+bl+'L'+(mid+1.6)+' '+bl+'Z';
    return {rear:rear,front:front,mid:mid};}
  function draw(type,paint,dark){
    paint=/^#[0-9a-f]{6}$/i.test(paint||'')?paint:'#dae0d7';
    var id='veh'+(++serial)+'-',b=[],hi=shade(paint,.55),lo=shade(paint,-.32),line=shade(paint,-.45),body='url(#'+id+'p)',gl='url(#'+id+'g)';
    b.push('<defs><linearGradient id="'+id+'p" x2="0" y2="1"><stop stop-color="'+hi+'"/><stop offset=".28" stop-color="'+paint+'"/><stop offset=".72" stop-color="'+paint+'"/><stop offset="1" stop-color="'+lo+'"/></linearGradient>'+
      '<linearGradient id="'+id+'g" x1="0" x2=".7" y1="0" y2="1"><stop stop-color="#bcd6dc"/><stop offset=".45" stop-color="#5f7f8b"/><stop offset="1" stop-color="#2f4650"/></linearGradient></defs>');
    var bus=/bus/.test(type),w;
    if(bus||type==='delivery'){
      w=type==='bus'?146:type==='minibus'?126:118;b.push('<ellipse cx="'+w/2+'" cy="52" rx="'+(w*.47)+'" ry="3" fill="#24302b" opacity=".22"/>');
      if(bus){
        b.push(P('M4 2H'+(w-14)+'Q'+(w-1)+' 2 '+w+' 13V38Q'+w+' 45 '+(w-6)+' 45H6Q1 45 1 39V7Q1 2 4 2Z',body,'stroke="'+line+'" stroke-width=".7"'));
        b.push(R(4,7,w-10,24,'#33474c',3));for(var x=7;x<w-30;x+=21)b.push(R(x,9,18,19,gl,1.6),L('M'+(x+3)+' 11l8 0-7 13','#ffffff',1.2,'opacity=".3"'));
        b.push(R(w-26,9,22,32,gl,2),L('M'+(w-15)+' 10v30','#d9e1d6',1),R(4,33,w-10,3.5,type==='bus'?'#e2c48d':'#cfe0bc',1),R(10,3.4,30,2.6,'#f4ecd2',1));
        b.push(L('M8 41h14m4 0h14m4 0h14','#617369',1),R(w-4,30,3.5,6,dark?'#fff3b8':'#f7efd4',1),R(1,30,3,7,'#c46e62',1));
        if(type==='bus')b.push('<text x="'+(w-14)+'" y="6.6" font-size="4" text-anchor="middle" font-family="sans-serif" fill="#f6eed4">12路</text>');
      }else{
        b.push(P('M2 6Q2 3 5 3H70Q74 3 76 6L90 15Q95 16 104 19L114 27Q117 30 117 36V41Q117 45 113 45H5Q2 45 2 42Z',body,'stroke="'+line+'" stroke-width=".7"'));
        b.push(P('M78 8H86L97 18H78Z',gl),P('M72 8H76V22H72Z',gl),L('M70 5V44M38 5V44','#00000033',.6),R(14,12,46,22,'#f4ead0',2),P('M24 23h26M37 15v16','none','stroke="#bfa57b" stroke-width="1.4"'));
        b.push(R(113,29,4,5,dark?'#fff3b8':'#f7efd4',1.4),R(1,26,3,9,'#c46e62',1),R(100,31,8,1.6,'#ffffff80',.6),R(1,40,116,4,'#4f5c57',2));
      }
      [w>130?24:20,w-(w>130?26:22)].forEach(function(x){b.push(P('M'+(x-11.5)+' 45A11.5 11.5 0 0 1 '+(x+11.5)+' 45','#1c2523'),wheelArt(x,44,8.6));});
      if(dark)b.push(P('M'+w+' 30l38-8v24l-38-12Z','#f5e5ad','opacity=".16"'));
      return {width:w,art:b.join('')};
    }
    if(type==='pickup'){
      w=124;b.push('<ellipse cx="'+w/2+'" cy="52" rx="'+(w*.46)+'" ry="3" fill="#24302b" opacity=".22"/>');
      b.push(P('M3 39V22Q3 20 5 20H52L56 6Q57 4 60 4H80Q84 4 87 8L97 20L115 23Q122 25 122 32V39Q122 42 118 42H112A11.6 11.6 0 0 0 86 42H36A11.6 11.6 0 0 0 12 42H6Q3 42 3 39Z',body,'stroke="'+line+'" stroke-width=".7"'));
      b.push(P('M59 8H69V19H57Z',gl),P('M72 8H80Q83 8 85 10L93 19H72Z',gl),L('M70 7V40M54 20V40M5 24H51','#00000040',.6),R(3,19.5,49,2,lo,1));
      b.push(R(118,27,4.5,4.5,dark?'#fff3b8':'#f6efd6',1.6),R(3,23,2.5,8,'#c25f55',.8),R(80,24,5,1.4,'#e8ece4',.6),R(91,15,3,4,line,.8));
      [24,98].forEach(function(x){b.push(wheelArt(x,44,9.2,{offroad:true}));});
      if(dark)b.push(P('M'+w+' 28l38-8v24l-38-12Z','#f5e5ad','opacity=".16"'));
      return {width:w,art:b.join('')};
    }
    var S=SPEC[type]||SPEC.sedan,G=glass(S);w=S.w;
    b.push('<ellipse cx="'+w/2+'" cy="'+(S.s+8.4)+'" rx="'+(w*.47)+'" ry="3" fill="#24302b" opacity=".22"/>');
    if(type==='sports')b.push(P('M2 '+(S.th-4)+'L4 '+(S.th-10)+'H20L18 '+(S.th-4)+'Z',lo),L('M8 '+(S.th-4)+'v4M15 '+(S.th-4)+'v4','#1d2421',1.4));
    b.push(P(silhouette(S),body,'stroke="'+line+'" stroke-width=".7"'));
    if(type==='jeep'){b.push(R(S.rs-3,S.r-1.5,S.re-S.rs+6,4,'#2b302e',1.5));for(var rr=0;rr<4;rr++)b.push(R(S.rs+4+rr*16,S.r-3.6,2,2.4,'#2b302e',.5));}
    // greenhouse: glass with B pillar, plus reflections
    b.push(P(G.rear,gl),P(G.front,gl),L('M'+(S.rb+5)+' '+(S.b-3)+'L'+(S.rs+4)+' '+(S.r+4),'#ffffff',1,'opacity=".28"'),L('M'+(G.mid+5)+' '+(S.b-3)+'L'+(G.mid+10)+' '+(S.r+4),'#ffffff',1.4,'opacity=".22"'));
    // shoulder highlight, door seams, handles, sill
    b.push(L('M6 '+(S.b+2)+'H'+(w-10),hi,1,'opacity=".7"'),L('M'+(G.mid)+' '+(S.b-1)+'V'+(S.s-6)+'M'+(S.wb-3)+' '+(S.b)+'Q'+(S.wb+1)+' '+(S.s-10)+' '+(S.wb-6)+' '+(S.s-5)+(type==='sports'?'':'M'+(S.rb+6)+' '+S.b+'V'+(S.s-7)),line,.6,'opacity=".75"'));
    b.push(R(G.mid-8,S.b+3,5,1.4,shade(paint,.65),.6,'stroke="'+line+'" stroke-width=".3"'));if(type!=='sports')b.push(R(G.mid+12,S.b+3,5,1.4,shade(paint,.65),.6,'stroke="'+line+'" stroke-width=".3"'));
    b.push(L('M'+(S.wh[0]+S.wr+4)+' '+(S.s-1.6)+'H'+(S.wh[1]-S.wr-4),lo,1.6));
    // mirror, lamps, bumpers
    b.push(P('M'+(S.wb-4)+' '+(S.b-2)+'h5q2 0 2 2v1h-7Z',paint,'stroke="'+line+'" stroke-width=".5"'));
    b.push(P('M'+(w-7)+' '+(S.nh+2)+'L'+(w-1)+' '+(S.nh+4.5)+'L'+(w-1)+' '+(S.nh+7)+'L'+(w-9)+' '+(S.nh+6)+'Z',dark?'#fff3b8':'#f7f0d8','stroke="'+line+'" stroke-width=".4"'));
    b.push(R(w-9,S.nh+7.6,6,1.2,'#f0a640',.5),P('M2 '+(S.th+1)+'L8 '+(S.th+2)+'L8 '+(S.th+6)+'L2 '+(S.th+6)+'Z','#c4544a'),R(2,S.th+6,4,1.6,'#f0a640',.5));
    b.push(R(w-6,S.s-8,5.5,5,shade(paint,-.55),1.6),R(1,S.s-8,6,5,shade(paint,-.55),1.6));
    if(type==='taxi'){b.push(R(42,S.r-6.5,24,6,'#f6e3ad',2,'stroke="#c3a764" stroke-width=".5"'),'<text x="54" y="'+(S.r-2.2)+'" font-size="4" font-family="sans-serif" text-anchor="middle" fill="#6c6448">TAXI</text>');for(var q=28;q<84;q+=5)b.push(R(q,S.b+8,3,2.4,(q/5)%2?'#3c4440':'#efe7cf',.2));}
    if(type==='sports'){b.push(L('M'+(S.wb+2)+' '+(S.nh-1.2)+'L'+(w-10)+' '+(S.nh-.2),'#ffffff',2,'opacity=".75"'),P('M'+(S.wh[0]+16)+' '+(S.b+6)+'h12l-3 4h-9Z','#1f2624'));}
    if(type==='jeep'){b.push(C(-1,S.th+9,7.4,'#202826'),C(-1,S.th+9,4,lo),C(-1,S.th+9,1.6,'#d8e0d8'));
      S.wh.forEach(function(x){b.push(P('M'+(x-S.wr-4)+' '+(S.s-2)+'Q'+(x-S.wr-3)+' '+(S.s-S.wr-6)+' '+x+' '+(S.s-S.wr-6.5)+'Q'+(x+S.wr+3)+' '+(S.s-S.wr-6)+' '+(x+S.wr+4)+' '+(S.s-2)+'L'+(x+S.wr+1)+' '+(S.s-2)+'Q'+(x+S.wr)+' '+(S.s-S.wr-3)+' '+x+' '+(S.s-S.wr-3.5)+'Q'+(x-S.wr)+' '+(S.s-S.wr-3)+' '+(x-S.wr-1)+' '+(S.s-2)+'Z','#2b302e'));});
      b.push(R(S.wh[0]+S.wr+4,S.s-2,S.wh[1]-S.wh[0]-2*S.wr-8,2.4,'#2b302e',1),R(w-2,S.nh+5,4,10,'#2b302e',1),L('M'+(S.wb+1)+' '+(S.b-1)+'L'+(S.wb+2)+' '+(S.r+1),'#2b302e',1.6));}
    if(type==='wagon'||type==='suv')b.push(L('M'+(S.rs+2)+' '+(S.r-1.6)+'H'+(S.re-4),'#3b4442',1.4));
    S.wh.forEach(function(x){b.push(wheelArt(x,S.s+1,S.wr,{sport:type==='sports',offroad:type==='jeep'}));});
    if(dark)b.push(P('M'+w+' '+(S.nh+4)+'l38-8v24l-38-12Z','#f5e5ad','opacity=".16"'));
    return {width:w,art:b.join('')};
  }
  // Plan view, nose up. Units: 44 wide x 100 long; caller scales/rotates.
  function top(type,paint,opts){opts=opts||{};paint=/^#[0-9a-f]{6}$/i.test(paint||'')?paint:'#dae0d7';
    var id='vtop'+(++serial)+'-',hi=shade(paint,.5),lo=shade(paint,-.3),line=shade(paint,-.45),b=[];
    b.push('<defs><linearGradient id="'+id+'p" x2="1"><stop stop-color="'+lo+'"/><stop offset=".22" stop-color="'+paint+'"/><stop offset=".5" stop-color="'+hi+'"/><stop offset=".78" stop-color="'+paint+'"/><stop offset="1" stop-color="'+lo+'"/></linearGradient>'+
      '<linearGradient id="'+id+'g" y2="1"><stop stop-color="#9fc0c9"/><stop offset="1" stop-color="#3a5560"/></linearGradient></defs>');
    var body='url(#'+id+'p)',gl='url(#'+id+'g)',jeep=type==='jeep',sports=type==='sports',pickup=type==='pickup',van=type==='delivery'||type==='van';
    b.push(R(2,4,44,96,'#1b2421',12,'opacity=".25"'));
    [[3,17],[3,77],[37,17],[37,77]].forEach(function(t){b.push(R(t[0]-(jeep?2:0),t[1],jeep?8:6,15,'#1f2826',2.4));});
    var nose=sports?16:jeep?5:10;
    if(jeep)b.push(R(4,1,36,97,body,4,'stroke="'+line+'" stroke-width=".8"'),R(1.5,14,4,20,'#2b302e',2),R(38.5,14,4,20,'#2b302e',2),R(1.5,72,4,20,'#2b302e',2),R(38.5,72,4,20,'#2b302e',2),R(6,-.6,32,3.4,'#2b302e',1.4));
    else b.push(P('M8 '+nose+'Q8 1 22 1Q36 1 36 '+nose+'L39 20Q41 50 39 88Q38 98 22 99Q6 98 5 88Q3 50 5 20Z',body,'stroke="'+line+'" stroke-width=".8"'));
    var ws=sports?34:jeep?28:van?14:30,rf0=sports?44:jeep?31:van?18:39,rf1=sports?62:jeep?86:van?92:pickup?52:type==='hatchback'?78:type==='wagon'||type==='suv'?86:72,rw=pickup||jeep||van?0:sports?78:rf1+10;
    b.push(P('M9 '+ws+'Q22 '+(ws-4)+' 35 '+ws+'L33 '+rf0+'H11Z',gl));
    b.push(R(10.5,rf0,23,rf1-rf0,jeep?'#2b302e':shade(paint,.18),4,'stroke="'+line+'" stroke-width=".5"'));
    if(jeep)for(var j=0;j<4;j++)b.push(R(9,rf0+6+j*13,26,1.6,'#4a524f',.6));
    if(/sedan|taxi|suv|wagon/.test(type))b.push(R(15,rf0+6,14,12,'#25333a',2,'opacity=".85"'));
    b.push(L('M9 '+(rf0+2)+'L7.4 '+(rf1-2)+'M35 '+(rf0+2)+'L36.6 '+(rf1-2),'#33494f',1.6));
    if(rw)b.push(P('M11 '+rf1+'H33L32 '+rw+'Q22 '+(rw+2)+' 12 '+rw+'Z',gl));
    if(pickup)b.push(R(8,rf1+3,28,40,shade(paint,-.5),2),L('M10 '+(rf1+12)+'H34M10 '+(rf1+22)+'H34M10 '+(rf1+32)+'H34',shade(paint,-.6),1));
    if(sports)b.push(R(17,4,3.6,rf0-6,'#f6f4ee',1),R(23.4,4,3.6,rf0-6,'#f6f4ee',1),R(3,90,38,5,lo,2,'stroke="#1d2421" stroke-width=".6"'),R(15,14,14,4,'#1d2421',1.4));
    if(jeep)b.push(C(22,97,7,'#202826'),C(22,97,3.4,lo));
    if(type==='taxi')b.push(R(16,rf0+12,12,6,'#f6e3ad',1.5,'stroke="#c3a764" stroke-width=".5"'));
    b.push(P('M5 '+(ws+2)+'l-4 1.6v3.4l4-.6Z',paint,'stroke="'+line+'" stroke-width=".5"'),P('M39 '+(ws+2)+'l4 1.6v3.4l-4-.6Z',paint,'stroke="'+line+'" stroke-width=".5"'));
    b.push(R(9,Math.max(1,nose-6),7,3,'#f7f0d8',1.4),R(28,Math.max(1,nose-6),7,3,'#f7f0d8',1.4),R(7.5,96,7,2.2,'#c4544a',1),R(29.5,96,7,2.2,'#c4544a',1));
    if(opts.label)b.push('<text x="22" y="'+(rf0+(rf1-rf0)/2+2)+'" font-size="5.5" text-anchor="middle" font-family="sans-serif" fill="#f7f3e6" stroke="#1d2421" stroke-width=".25" paint-order="stroke">'+String(opts.label).replace(/[<&]/g,'')+'</text>');
    return b.join('');}
  function svg(type,paint,label){var car=draw(type||'sedan',paint||'#e1e5dc',false);return '<svg class="vehicle-preview" viewBox="-6 -3 '+(car.width+12)+' 60" role="img" aria-label="'+(label||'珍珠白小汽车')+'">'+car.art+'</svg>';}
  root.VehicleArt={draw:draw,top:top,preview:svg,types:['sedan','hatchback','wagon','suv','taxi','sports','jeep','pickup','delivery','minibus','bus']};
  var parked=document.getElementById('garage-car-model');
  if(parked){var car=draw('sedan','#e1e5dc',false);parked.innerHTML='<g transform="translate(267 0) scale(2.65)">'+car.art+'</g>';}
})(window);
