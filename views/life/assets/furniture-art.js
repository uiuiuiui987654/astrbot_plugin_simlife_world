/* Detailed furniture artwork shared by the plan and room close-ups. */
(function(root) {
  'use strict';
  function rect(x,y,w,h,c,r,extra) { return '<rect x="'+x+'" y="'+y+'" width="'+Math.max(0,w)+'" height="'+Math.max(0,h)+'" rx="'+(r||0)+'" fill="'+c+'" '+(extra||'')+'/>'; }
  function path(d,c,extra) { return '<path d="'+d+'" fill="'+c+'" '+(extra||'')+'/>'; }
  function line(x,y,a,b,c,width,extra) { if(/^url\(/.test(c))c=/metal/.test(c)?'#bdcbb7':'#b39670';return path('M'+x+' '+y+'L'+a+' '+b,'none','stroke="'+c+'" stroke-width="'+(width||1)+'" '+(extra||'')); }
  function oval(x,y,w,h,c,extra) { return '<ellipse cx="'+x+'" cy="'+y+'" rx="'+w+'" ry="'+h+'" fill="'+c+'" '+(extra||'')+'/>'; }
  function circle(x,y,r,c,extra) { return '<circle cx="'+x+'" cy="'+y+'" r="'+Math.max(0,r)+'" fill="'+c+'" '+(extra||'')+'/>'; }
  function draw(type,w,h,id,e,front) {
    if(type==='oven'||type==='dishwasher')return appliance(type,w,h,id);
    if(!front && (type==='sofa'||type==='monitor') && h>w) return '<g transform="translate('+w+' 0) rotate(90)">'+draw(type,h,w,id,e,false)+'</g>';
    var wood='url(#'+id+'wood)', top='url(#'+id+'woodTop)', cloth='url(#'+id+'fabric)', sage='url(#'+id+'sage)', cream='url(#'+id+'cream)', white='url(#'+id+'porcelain)', glass='url(#'+id+'glass)', metal='url(#'+id+'metal)';
    var b=[],i,j,x,y,step;
    function grain(x,y,a,c,r) { return rect(x,y,a,c,'url(#'+id+'grain)',r||2); }
    function seam(x,y,a,c,r) { return rect(x,y,a,c,'none',r||3,'stroke="#f9eddb" stroke-opacity=".52" stroke-width=".75" stroke-dasharray="2 1.6"'); }
    function edge(x,y,a,c,r) { return rect(x,y,a,c,'none',r||3,'stroke="#fff5d5" stroke-opacity=".42" stroke-width=".8"'); }
    function foot(x,y) { return rect(x,y,Math.max(3,w*.045),Math.max(3,h*.07),'#66513e',1); }
    function cup(x,y,s) { return oval(x,y+s*.8,s*.83,s*.28,'#243b3b22')+rect(x-s*.55,y-s*.5,s*1.1,s,white,2)+oval(x,y-s*.5,s*.54,s*.25,'#edf0db')+oval(x,y-s*.5,s*.4,s*.15,'#9a7351')+oval(x+s*.73,y,s*.27,s*.35,'none','stroke="#d3ddc8" stroke-width="1.3"'); }
    function leaves(x,y,s) { return path('M'+x+' '+y+'q-'+(s*.6)+' -'+s+' -'+s+' -'+(s*1.3)+'q-'+(s*.3)+' '+s+' '+s+' '+(s*1.3),'#7f9e72')+path('M'+x+' '+y+'q'+(s*.3)+' -'+(s*1.2)+' '+(s*.9)+' -'+(s*1.5)+'q'+(s*.3)+' '+s+' -'+(s*.9)+' '+(s*1.5),'#a1b98a')+line(x,y,x,y-s*1.3,'#668164',.7); }
    b.push(oval(w*.52,h*.96,w*.49,Math.min(4,h*.06),'#243a3227'));
    if(type==='bed') {
      b.push(foot(9,h-4),foot(w-16,h-4),rect(0,0,w,h-3,wood,7),grain(2,2,w-4,16),rect(5,8,w-10,h-16,white,8),rect(3,2,w-6,13,top,4),edge(5,4,w-10,8,2));
      for(i=0;i<2;i++){x=11+i*w*.48;b.push(rect(x,19,w*.36,23,'#c7bba8',6),rect(x,17,w*.36,23,cream,6),seam(x+3,20,w*.36-6,17,4),path('M'+(x+7)+' 21q'+w*.12+' 5 '+w*.22+' 0','none','stroke="#cdbca2" stroke-width=".8"'));}
      b.push(rect(7,43,w-14,h-51,cloth,6),rect(8,43,w-16,13,'#e4d1ce',4),line(11,56,w-11,56,'#ad8e98',1),seam(11,60,w-22,h-72,4));
      for(x=22;x<w-15;x+=19)b.push(path('M'+x+' 61q-3 '+h*.1+' 0 '+h*.24,'none','stroke="#f7e6dc" stroke-opacity=".32"'));
      b.push(rect(8,h-32,w-16,20,sage,3),rect(8,h-32,w-16,20,'url(#'+id+'weave)',3),seam(12,h-29,w-24,14,2));
    } else if(type==='sofa') {
      b.push(foot(9,h-5),foot(w-14,h-5),rect(2,5,w-4,h-11,'#816e6a',8),rect(3,0,w-6,h*.36,cloth,9),edge(7,4,w-14,h*.24,6),rect(6,h*.24,w-12,h*.62,cloth,7));
      var seats=w>140?3:2,seat=(w-24)/seats;
      for(i=0;i<seats;i++){x=12+i*seat;b.push(rect(x,h*.31,seat-3,h*.5,sage,5),seam(x+3,h*.34,seat-9,h*.43,3),line(x+5,h*.7,x+seat-8,h*.7,'#dce6c444',.7));}
      b.push(rect(0,h*.17,11,h*.71,cloth,5),rect(w-11,h*.17,11,h*.71,cloth,5),edge(2,h*.2,7,h*.63,3),edge(w-9,h*.2,7,h*.63,3));
      b.push('<g transform="rotate(-8 '+w*.22+' '+h*.49+')">'+rect(w*.12,h*.33,w*.19,h*.33,cream,4)+seam(w*.12+2,h*.33+2,w*.19-4,h*.33-4,2)+'</g>',rect(w*.72,h*.48,w*.14,h*.25,'#c9a7b0',4),seam(w*.72+2,h*.48+2,w*.14-4,h*.25-4,2));
    } else if(type==='cabinet'||type==='jewelry') {
      b.push(foot(5,h-4),foot(w-10,h-4),rect(0,2,w,h-6,wood,3),rect(0,0,w,5,top,2),grain(3,5,w-6,h-12),rect(w-5,5,4,h-11,'#6c513b33',1));
      var rows=type==='jewelry'?3:1;
      for(j=0;j<rows;j++){y=7+j*(h-16)/rows;var dh=(h-16)/rows-2;for(i=0;i<2;i++){x=5+i*(w-10)/2;b.push(rect(x,y,(w-14)/2,dh,top,2),grain(x+2,y+2,(w-18)/2,dh-4),edge(x+2,y+2,(w-18)/2,dh-4,1));var hx=i===0?w/2-5:w/2+4;b.push(rect(hx,y+dh*.4,2,Math.max(4,dh*.2),metal,1),circle(hx+1,y+dh*.4,1,'#f1dbb3'));}}
      b.push(line(4,h-7,w-4,h-7,'#644e3d',1));
    } else if(type==='fridge') {
      b.push(rect(0,0,w,h-3,metal,5),rect(2,2,w-6,h-7,white,4),rect(w-5,4,3,h-9,'#708e8955',1),line(3,h*.31,w-5,h*.31,'#7e9a94',1),rect(w-11,h*.12,3,h*.12,metal,1),rect(w-11,h*.41,3,h*.31,metal,1),rect(7,h*.41,w*.34,h*.18,'#f1dfb5',2),line(10,h*.46,w*.32,h*.46,'#b0a78b',.7),line(10,h*.49,w*.3,h*.49,'#b0a78b',.7),circle(w*.25,h*.11,3,'#bf907c'),circle(w*.43,h*.15,2.5,'#8ba6a9'),line(7,h-7,w-9,h-7,'#778f89',1));
    } else if(type==='bookshelf') {
      b.push(foot(5,h-3),foot(w-10,h-3),rect(0,0,w,h-3,wood,3),grain(1,1,w-2,h-4),rect(5,5,w-10,h-12,'#594d40',1),rect(0,0,w,5,top,2));
      var colors=['#b98782','#809a96','#cbb480','#9aa785','#9892ad'];
      for(j=0;j<4;j++){y=6+j*(h-14)/4;var shelf=(h-14)/4;for(i=0,x=8;x<w-10;x+=8,i++){var bh=shelf*(.6+((i+j)%3)*.08);b.push(rect(x,y+shelf-bh-4,5.5,bh,colors[(i+j)%5],.8),line(x+1,y+shelf-bh,x+4,y+shelf-bh,'#eadab8',.6),line(x+1,y+shelf-8,x+4,y+shelf-8,'#d6c8ac',.6),line(x+1,y+shelf-bh-2,x+1,y+shelf-6,'#f9e7c144',.6));}b.push(rect(4,y+shelf-3,w-8,3,top,1),line(5,y+shelf,w-5,y+shelf,'#4d4136',.7));}
    } else if(type==='tub') {
      b.push(rect(0,4,w,h-6,'#8ba7a4',h*.4),rect(0,0,w,h-9,white,h*.4),rect(6,5,w-12,h-20,'#e8efe1',h*.35),rect(11,9,w-22,h-28,glass,h*.3),edge(3,2,w-6,h-13,h*.37),oval(w*.45,h*.42,w*.3,h*.15,'#c5e3d244'),path('M20 '+h*.45+'q'+w*.2+' -9 '+w*.4+' 0t'+w*.35+' 0','none','stroke="#d3e8db77" stroke-width="1"'));
      b.push(line(w-22,5,w-22,h*.42,'#dbe4cf',3),path('M'+(w-22)+' 6q-10 -2 -10 8','none','stroke="#eff3df" stroke-width="3"'),circle(w*.45,h*.58,2,'#bbd3cb'));
      for(i=0;i<5;i++)b.push(circle(25+i*(w-55)/5,h*.44+(i%2)*6,1.6+(i%2),'#eaf4e4aa'));
      b.push(line(15,h-9,w-15,h-9,'#c9d9c7',1.2));
    } else if(type==='table'||type==='dining'||type==='desk') {
      var tabletop=front?h*.46:h-5;
      if(front){b.push(rect(10,tabletop-2,6,h-tabletop-1,wood,1),rect(w-16,tabletop-2,6,h-tabletop-1,wood,1),line(17,h-8,w-17,h-8,'#8d7151',3));}
      if(type==='dining'&&front) {
        var cw=Math.max(16,Math.min(28,w*.12)),cy=h*.22;
        [-cw+5,w-5].forEach(function(cx){b.push(rect(cx,cy,cw,h*.38,wood,4),rect(cx+3,cy+3,cw-6,h*.28,sage,3),rect(cx-2,h*.67,cw+4,7,sage,2),line(cx+4,h*.71,cx+3,h-2,'#886b49',3),line(cx+cw-4,h*.71,cx+cw-2,h-2,'#886b49',3));});
      } else if(type==='dining')for(i=0;i<2;i++){y=10+i*Math.max(0,h-42);b.push(rect(-12,y,13,24,wood,3),rect(-10,y+2,10,18,sage,3),rect(w-1,y,13,24,wood,3),rect(w+1,y+2,10,18,sage,3));}
      b.push(rect(0,4,w,tabletop,wood,6),rect(0,0,w,tabletop,top,6),grain(2,2,w-4,tabletop-4,5),edge(3,3,w-6,tabletop-6,4),line(7,tabletop,w-7,tabletop,'#705438',1.2));
      if(type==='desk'){b.push(rect(9,7,w*.18,Math.max(13,tabletop-15),'#e5dcc2',1),line(13,12,w*.16,12,'#b4b294',.7),line(13,16,w*.15,16,'#b4b294',.7),cup(w-20,tabletop*.48,8));if(front)b.push(rect(w*.67,tabletop+4,w*.24,h-tabletop-14,wood,2),line(w*.69,tabletop+12,w*.89,tabletop+12,'#dfbf8a',1));}
      else {for(i=0;i<2;i++){x=w*(i?.75:.25);var rad=Math.min(13,tabletop*.29);b.push(circle(x,tabletop*.5,rad,white),circle(x,tabletop*.5,rad*.73,'none','stroke="#d7c9ac" stroke-width=".9"'),line(x-rad-5,tabletop*.25,x-rad-5,tabletop*.78,metal,1.5),line(x+rad+5,tabletop*.25,x+rad+5,tabletop*.78,metal,1.5));}b.push(oval(w*.5,tabletop*.59,6,3,'#867058'),rect(w*.5-4,tabletop*.42,8,7,cream,2),leaves(w*.5,tabletop*.45,7));}
    } else if(type==='monitor'||type==='screen'||type==='mirror') {
      var displayH=front&&type==='monitor'?h*.83:h;
      if(front&&type==='monitor')b.push(rect(w*.45,displayH-1,w*.1,h-displayH-3,metal,1),oval(w*.5,h-3,w*.23,3,metal));
      b.push(rect(0,0,w,displayH,type==='mirror'?wood:'#344b50',4),rect(3,3,w-6,displayH-6,type==='mirror'?metal:glass,2),edge(1,1,w-2,displayH-2,3));
      if(type==='mirror')b.push(path('M5 '+displayH*.7+'L'+(w-6)+' 7V'+displayH*.32+'L5 '+(displayH-6),'#f5f1d875'),line(w-9,9,w-9,displayH*.3,'#f7f6df',1));
      else {b.push(path('M4 '+(displayH-5)+'L'+w*.28+' '+displayH*.42+'L'+w*.48+' '+displayH*.69+'L'+w*.72+' '+displayH*.27+'L'+(w-4)+' '+displayH*.65+'V'+(displayH-4)+'Z','#8fa79e'),path('M4 '+(displayH-5)+'L'+w*.25+' '+displayH*.7+'L'+w*.4+' '+displayH*.82+'L'+w*.6+' '+displayH*.55+'L'+(w-4)+' '+displayH*.87+'V'+(displayH-4)+'Z','#5f807b'),circle(w*.2,displayH*.24,Math.max(2,displayH*.08),'#e8d3a0'),path('M5 5H'+w*.7+'L'+w*.25+' '+(displayH-5)+'H5Z','#d8ecde12'),circle(w-6,displayH-2,1,'#9dd7b5'));}
    } else if(type==='aquarium') {
      b.push(rect(0,0,w,h,'#3d514e',3),rect(3,4,w-6,h-9,glass,2),rect(0,0,w,5,wood,2),rect(0,h-6,w,6,wood,2),path('M4 '+(h-8)+'q'+w*.2+' -5 '+w*.4+' 0t'+w*.55+' -1v5H4Z','#c9b98b'));
      for(i=0;i<3;i++){x=12+i*(w-24)/3;b.push(path('M'+x+' '+(h-7)+'q-8 -9 -3 -'+h*.44+'q7 6 3 '+h*.44,'#789c7a'),path('M'+(x+3)+' '+(h-7)+'q8 -6 8 -'+h*.3,'none','stroke="#aec594" stroke-width="1.2"'));}
      for(i=0;i<2;i++){x=w*(.37+i*.35);y=h*(.38+i*.17);b.push(oval(x,y,5,2.7,i?'#d8bf91':'#dbad7a'),path('M'+(x+4)+' '+y+'l4-3v6Z','#d6c498'),circle(x-3,y-.4,.7,'#415553'));}
      b.push(rect(w-12,7,5,h*.45,'#405e5c',1),circle(w-14,h*.3,1.4,'none','stroke="#d7e8d7" stroke-width=".7"'),circle(w-16,h*.19,1,'none','stroke="#d7e8d7" stroke-width=".7"'),line(5,8,w-8,8,'#d8ead677',.8));
    } else if(type==='plants') {
      b.push(rect(0,h*.59,w,h*.38,wood,3),grain(3,h*.64,w-6,h*.24),edge(2,h*.61,w-4,h*.31,2));
      for(x=12;x<w-3;x+=23){b.push(rect(x-5,h*.48,10,h*.2,'#c79975',2),oval(x,h*.48,5,2,'#735b43'),leaves(x,h*.51,12),leaves(x+1,h*.48,9));}
    } else if(type==='rockingchair') {
      b.push(path('M'+w*.1+' '+h*.88+'Q'+w*.5+' '+h*1.07+' '+w*.91+' '+h*.87,'none','stroke="#886a48" stroke-width="4"'),path('M'+w*.17+' '+h*.16+'L'+w*.3+' '+h*.85+'M'+w*.69+' '+h*.43+'L'+w*.8+' '+h*.91,'none','stroke="#bb976c" stroke-width="3"'),rect(w*.2,h*.05,w*.5,h*.55,wood,7),rect(w*.24,h*.09,w*.42,h*.43,sage,6),seam(w*.27,h*.12,w*.36,h*.37,4),rect(w*.25,h*.55,w*.52,h*.17,wood,4),rect(w*.28,h*.52,w*.46,h*.15,cloth,4),seam(w*.31,h*.55,w*.4,h*.09,2),line(w*.15,h*.43,w*.81,h*.43,'#c7aa7f',4));
    } else if(type==='lamp'||type==='floorlamp') {
      b.push(oval(w*.5,h*.92,w*.35,h*.07,wood),rect(w*.46,h*.26,w*.08,h*.65,metal,1),path('M'+w*.2+' '+h*.12+'Q'+w*.5+' 0 '+w*.8+' '+h*.12+'L'+w*.95+' '+h*.48+'Q'+w*.5+' '+h*.64+' '+w*.05+' '+h*.48+'Z',cream),oval(w*.5,h*.48,w*.44,h*.1,'#e6bd7e'),oval(w*.5,h*.48,w*.25,h*.06,'#ffe7a7'),line(w*.3,h*.15,w*.21,h*.45,'#f9ecd4',.8),line(w*.67,h*.15,w*.78,h*.45,'#c5b69a',.7));
    } else if(type==='record') {
      b.push(rect(0,0,w,h,wood,3),grain(2,2,w-4,h-4),edge(2,2,w-4,h-4,2));var r=Math.min(h*.4,w*.29);b.push(circle(w*.35,h*.5,r,'#354440'));for(i=1;i<=4;i++)b.push(circle(w*.35,h*.5,r*i/5,'none','stroke="#738179" stroke-width=".55"'));b.push(circle(w*.35,h*.5,r*.22,'#c9b189'),circle(w*.35,h*.5,1,'#dce2ca'),circle(w*.77,h*.24,3,metal),path('M'+w*.77+' '+h*.24+'L'+w*.83+' '+h*.68+'L'+w*.66+' '+h*.8,'none','stroke="#e2d3af" stroke-width="1.8"'),rect(w*.62,h*.75,5,3,'#52645d',1),circle(w*.91,h*.85,1.5,'#93bea8'));
    } else if(type==='piano'&&front) {
      b.push(rect(3,0,w-6,h*.91,wood,3),grain(5,3,w-10,h*.83),rect(0,0,w,6,top,2),edge(7,9,w-14,h*.41,2),rect(6,h*.56,w-12,h*.22,'#3d4940',1));
      var pk=(w-16)/20;for(i=0;i<20;i++)b.push(rect(8+i*pk,h*.57,pk-.5,h*.16,white,.4));
      for(i=0;i<19;i++)if(i%7!==2&&i%7!==6)b.push(rect(8+(i+.67)*pk,h*.57,pk*.56,h*.1,'#34433e',.4));
      b.push(rect(0,h*.76,w,5,top,1),rect(4,h*.77,7,h*.22,wood,1),rect(w-11,h*.77,7,h*.22,wood,1),rect(w*.41,h*.88,w*.18,3,metal,1),line(w*.4,8,w*.6,8,'#e1c69a',1));
    } else if(type==='keyboard') {
      b.push(rect(0,0,w,h,'#53695d',2),rect(1,1,w-2,h-2,metal,1));
      var rowH=(h-3)/5,keyW=(w-3)/14;
      for(j=0;j<4;j++)for(i=0;i<14;i++)b.push(rect(1.5+i*keyW,1.3+j*rowH,keyW*.76,rowH*.72,'#e4e8d4',.2));
      b.push(rect(w*.27,h-rowH-1,w*.42,rowH*.65,'#dfe6d0',.2));
    } else if(type==='pianokeys'||type==='piano') {
      b.push(rect(0,0,w,h,type==='piano'?wood:'#536761',3),grain(2,2,w-4,h-4),edge(2,2,w-4,h-4,2));var ky=type==='piano'?h*.31:3,kh=type==='piano'?h*.52:h-6,kw=(w-8)/14;
      for(i=0;i<14;i++)b.push(rect(4+i*kw,ky,kw-.6,kh,white,.6),line(5+i*kw,ky+kh-3,4+(i+1)*kw-2,ky+kh-3,'#bfc5b2',.5));
      for(i=0;i<13;i++)if(i%7!==2&&i%7!==6)b.push(rect(4+(i+.67)*kw,ky,kw*.58,kh*.61,'#33413f',.5),line(5+(i+.67)*kw,ky+1,4+(i+1.2)*kw,ky+1,'#788177',.5));
      if(type==='piano')b.push(line(5,h*.19,w-5,h*.19,'#e1c79c',.7),rect(w*.42,h*.08,w*.17,2,metal,.5));
      if(type==='piano'&&front)b.push(rect(w*.08,h*.83,w*.08,h*.15,wood,1),rect(w*.84,h*.83,w*.08,h*.15,wood,1),rect(w*.13,h*.85,w*.74,h*.04,wood,1));
    } else if(type==='easel') {
      b.push(line(w*.48,2,w*.12,h,'#98774f',5),line(w*.48,2,w*.88,h,'#98774f',5),line(w*.53,h*.15,w*.72,h,'#775c40',3),rect(w*.04,h*.1,w*.92,h*.66,wood,2),grain(w*.04,h*.1,w*.92,h*.66),rect(w*.09,h*.15,w*.82,h*.54,'#e9dfbf',1),path('M'+w*.1+' '+h*.65+'L'+w*.36+' '+h*.3+'L'+w*.63+' '+h*.56+'L'+w*.79+' '+h*.38+'L'+w*.9+' '+h*.68+'Z','#8ba598'),path('M'+w*.1+' '+h*.68+'L'+w*.3+' '+h*.5+'L'+w*.55+' '+h*.67+'Z','#668f84'),circle(w*.7,h*.29,w*.07,'#d8ba86'),rect(0,h*.76,w,h*.04,top,1),line(w*.13,h*.97,w*.28,h*.83,'#d9b98d',.8));
    } else if(type==='treadmill'&&front) {
      b.push(path('M22 '+h*.4+'H'+(w-22)+'L'+w+' '+(h-5)+'H0Z','#60776a'),path('M31 '+h*.43+'H'+(w-31)+'L'+(w-13)+' '+(h-12)+'H13Z','#354e44'));
      for(i=1;i<11;i++){y=h*.43+i*h*.048;var inset=31-(y-h*.43)/(h*.5)*18;b.push(line(inset,y,w-inset,y,'#809580',.7));}
      b.push(line(14,h*.17,24,h*.6,metal,6),line(w-14,h*.17,w-24,h*.6,metal,6),line(14,h*.17,w-14,h*.17,metal,5),rect(w*.27,0,w*.46,h*.22,white,5),rect(w*.33,h*.04,w*.34,h*.1,glass,2),line(w*.38,h*.09,w*.55,h*.09,'#cce9c4',1),circle(w*.65,h*.17,2.5,'#c39481'),rect(2,h-10,w-4,8,metal,3));
    } else if(type==='treadmill') {
      b.push(rect(0,0,w,h,'#63746d',6),rect(8,8,w-16,h-15,'#33433f',4),rect(13,18,w-26,h-29,'#3f514a',2));for(y=28;y<h-14;y+=7)b.push(line(15,y,w-15,y,'#6d7d71',.7));b.push(rect(4,7,6,h*.6,metal,2),rect(w-10,7,6,h*.6,metal,2),rect(11,2,w-22,20,white,4),rect(w*.3,5,w*.4,10,glass,2),line(w*.35,10,w*.52,10,'#b5e1c2',1),circle(w*.79,12,2.5,'#c68f81'),circle(w*.2,12,2,'#9ea683'));
    } else if(type==='stairs'&&front) {
      b.push(path('M'+w*.27+' 3H'+w*.73+'L'+w+' '+h+'H0Z',wood));
      for(i=0;i<9;i++){var t=i/9,nt=(i+1)/9,ax=w*.27*(1-t),nx=w*.27*(1-nt);y=t*h;var ny=nt*h;b.push(path('M'+ax+' '+y+'H'+(w-ax)+'L'+(w-nx)+' '+ny+'H'+nx+'Z',top),line(nx,ny,w-nx,ny,'#755c3f',1.3),line(nx,ny-3,w-nx,ny-3,'#e8c99b',1));}
      b.push(line(0,h-26,w*.27,0,metal,3),line(w,h-26,w*.73,0,metal,3));for(i=1;i<7;i++){var ry=i/7*h,rx=w*.27*(1-i/7);b.push(line(rx,ry,rx,Math.max(0,ry-23),metal,2),line(w-rx,ry,w-rx,Math.max(0,ry-23),metal,2));}
      b.push(path('M'+w*.5+' '+h*.85+'V'+h*.12+'l-5 8m5-8l5 8','none','stroke="#f5e6c4" stroke-width="1.5"'));
    } else if(type==='stairs') {
      b.push(rect(0,0,w,h,wood,2));step=Math.max(4,Math.min(14,h/7));for(y=step/2;y<h-step/2;y+=step)b.push(rect(4,y,w-8,step-1,top,1),grain(5,y,w-10,step-2),line(4,y+step-1,w-4,y+step-1,'#6c543b',.8));b.push(line(1,1,1,h-1,metal,2),line(w-1,1,w-1,h-1,metal,2),path('M'+w*.5+' '+(h-5)+'V6l-4 5m4-5l4 5','none','stroke="#f6e5c3" stroke-width="1.5"'));
    } else if(type==='swing') {
      b.push(path('M5 '+h+'L13 3H'+(w-13)+'L'+(w-5)+' '+h,'none','stroke="#b89a72" stroke-width="4"'),line(18,4,w-18,4,'#ebd1a3',2),line(23,4,23,h*.81,'#e8d6ae',1.6),line(w-23,4,w-23,h*.81,'#e8d6ae',1.6),rect(17,h*.46,w-34,h*.36,wood,5),rect(22,h*.41,w-44,h*.3,sage,5),seam(25,h*.44,w-50,h*.23,3),rect(19,h*.7,w-38,h*.15,cloth,3),seam(22,h*.72,w-44,h*.1,2));
    } else if(type==='telescope') {
      b.push(line(w*.53,h*.46,w*.28,h,metal,2.2),line(w*.53,h*.46,w*.82,h,metal,2.2),line(w*.53,h*.46,w*.5,h,metal,2),circle(w*.53,h*.47,3,'#6f8e86'),'<g transform="rotate(-14 '+w*.52+' '+h*.3+')">'+rect(5,h*.12,w-12,h*.28,white,h*.1)+rect(8,h*.15,w-24,h*.2,'#d0dcca',2)+rect(w-14,h*.1,10,h*.32,metal,2)+oval(w-8,h*.26,4,h*.14,glass)+rect(0,h*.2,9,h*.12,'#637c75',1)+'</g>');
    } else if(type==='mat'||type==='towel') {
      b.push(rect(0,0,w,h,type==='mat'?sage:cloth,4),rect(2,2,w-4,h-4,'url(#'+id+'weave)',3),seam(3,3,w-6,h-6,2),rect(w-9,0,9,h,type==='mat'?'#73977d':'#b297a1',4),oval(w-5,h*.5,3,h*.34,type==='mat'?'#587e68':'#8f7685'),line(5,h*.26,w-15,h*.26,'#e9ead044',.7));
    } else if(type==='book') {
      b.push(rect(0,2,w,h-2,'#69867b',2),rect(2,0,w-4,h-4,cream,1),line(w*.5,1,w*.5,h-5,'#b6a383',1));for(y=5;y<h-6;y+=4)b.push(line(5,y,w*.45,y,'#b1aa91',.6),line(w*.56,y,w-5,y,'#b1aa91',.6));
    } else if(type==='box'||type==='board') {
      b.push(rect(0,3,w,h-4,wood,2),rect(0,0,w,h-6,top,2),grain(2,2,w-4,h-10),edge(2,2,w-4,h-10,1));
      if(type==='box')b.push(rect(w*.42,0,w*.14,h-6,'#dfccaa',.5),rect(w*.65,h*.23,w*.24,h*.3,cream,1),line(w*.69,h*.32,w*.84,h*.32,'#8f8d7c',.7),line(w*.69,h*.38,w*.8,h*.38,'#8f8d7c',.7));
      else {b.push(rect(4,4,w-8,h-13,'#8fa88e',1));for(i=0;i<3;i++)b.push(circle(w*(.25+i*.24),h*.4,Math.max(1.5,h*.08),['#cfb481','#ad8082','#628c8a'][i]));b.push(rect(w*.66,h*.62,5,5,cream,1),circle(w*.69,h*.65,.6,'#758074'));}
    } else if(/^(washer|oven|coffee|speaker|popcorn|grill|toaster|console|kettle|tea|keys|camera|iron|bottle|ricecooker|pourover|wateringcan|projector|diffuser|jar|mask)$/.test(type)) {
      b.push(smallDevice(type,w,h,id,e));
    } else if(type==='vanity') {
      b.push(rect(0,h*.55,w,h*.4,wood,3),grain(2,h*.59,w-4,h*.3),rect(0,h*.52,w,h*.1,top,2),oval(w*.57,h*.29,w*.3,h*.28,wood),oval(w*.57,h*.29,w*.26,h*.24,metal),path('M'+w*.4+' '+h*.4+'L'+w*.71+' '+h*.12,'none','stroke="#f4f0d5" stroke-width="2"'),line(w*.46,h*.65,w*.46,h*.9,'#7c5e44',.8),rect(w*.15,h*.74,w*.12,2,metal,1),rect(w*.63,h*.74,w*.12,2,metal,1),rect(w*.1,h*.33,w*.1,h*.2,'#b6bbb3',1),rect(w*.12,h*.26,w*.06,h*.08,metal,1));
    } else if(type==='weights') {
      b.push(rect(5,h*.42,w-10,h*.16,metal,2));[3,11,w-20,w-12].forEach(function(a){b.push(rect(a,2,8,h-4,'#405858',2),line(a+2,4,a+2,h-6,'#a2b5a4',.9),rect(a,h*.45,8,h*.1,'#2c4443',1));});b.push(line(w*.36,h*.48,w*.63,h*.48,'#e5dfc3',1));
    } else if(type==='bear') {
      b.push(circle(w*.25,h*.2,w*.17,'#b28e71'),circle(w*.75,h*.2,w*.17,'#b28e71'),circle(w*.25,h*.2,w*.1,'#d5b297'),circle(w*.75,h*.2,w*.1,'#d5b297'),oval(w*.5,h*.62,w*.37,h*.35,'#d7b697'),oval(w*.5,h*.36,w*.44,h*.3,'#dfc2a3'),oval(w*.5,h*.48,w*.22,h*.14,'#f0dcc0'),circle(w*.34,h*.34,1.3,'#594f42'),circle(w*.66,h*.34,1.3,'#594f42'),oval(w*.5,h*.43,2,1.3,'#81624f'),line(w*.5,h*.44,w*.5,h*.5,'#98775f',.7),path('M'+w*.5+' '+h*.68+'l-5-3v6Z','#a3b49a'),path('M'+w*.5+' '+h*.68+'l5-3v6Z','#a3b49a'),oval(w*.2,h*.86,w*.17,h*.12,'#c7a081'),oval(w*.8,h*.86,w*.17,h*.12,'#c7a081'));
    } else if(type==='shower') {
      b.push(rect(0,0,w,h,'#acd4cb3d',3),edge(1,1,w-2,h-2,2),line(w*.55,3,w*.55,h*.48,metal,2),path('M'+w*.55+' 4q-9 0 -9 8','none','stroke="#edf0d9" stroke-width="2"'),oval(w*.55-7,h*.34,w*.27,3,metal));for(i=0;i<4;i++)b.push(line(w*.2+i*w*.16,h*.45,w*.2+i*w*.16,h*.69,'#cce7d2',.7,'stroke-dasharray="2 2"'));b.push(rect(w*.43,h*.8,w*.26,3,metal,1),line(4,7,4,h-8,'#f0efdb77',1));
    } else if(type==='paints') {
      b.push(rect(0,h*.25,w,h*.05,wood,1),rect(0,h*.72,w,h*.05,wood,1),line(4,h*.26,4,h*.94,metal,2),line(w-4,h*.26,w-4,h*.94,metal,2),circle(7,h*.94,3,'#57695e'),circle(w-7,h*.94,3,'#57695e'));
      for(i=0;i<4;i++){x=7+i*(w-13)/4;b.push(rect(x,h*.45,7,h*.26,['#c18e8c','#9ba787','#8ba3ab','#d3b78a'][i],1),rect(x+1,h*.41,5,h*.06,cream,.5),line(x+2,h*.5,x+5,h*.5,'#f3e8d5',.6));}b.push(rect(w*.67,h*.07,w*.19,h*.18,cream,2),line(w*.72,0,w*.73,h*.19,'#987650',1.2),line(w*.78,2,w*.78,h*.19,'#b5a179',1.2));
    } else if(type==='chime') {
      b.push(line(w*.5,0,w*.5,h,metal,.8),path('M'+w*.14+' '+h*.37+'Q'+w*.5+' 1 '+w*.86+' '+h*.37+'Z',glass),oval(w*.5,h*.37,w*.35,h*.07,metal),circle(w*.5,h*.47,2,'#c5a574'),rect(w*.34,h*.65,w*.32,h*.3,cream,1),line(w*.42,h*.71,w*.56,h*.71,'#b5bda0',.6),line(w*.42,h*.77,w*.56,h*.77,'#b5bda0',.6));
    } else if(type==='headphones') {
      b.push(path('M4 '+h*.65+'V'+h*.42+'a'+(w*.5-4)+' '+h*.33+' 0 0 1 '+(w-8)+' 0V'+h*.65,'none','stroke="#516c68" stroke-width="5"'),path('M6 '+h*.42+'a'+(w*.5-6)+' '+h*.28+' 0 0 1 '+(w-12)+' 0','none','stroke="#c9d2be" stroke-width="1.4"'),rect(0,h*.42,9,h*.5,wood,3),rect(w-9,h*.42,9,h*.5,wood,3),rect(3,h*.46,5,h*.4,'#acb6a5',2),rect(w-8,h*.46,5,h*.4,'#acb6a5',2));
    } else if(type==='umbrella') {
      b.push(path('M2 '+h*.55+'Q'+w*.5+' 0 '+(w-2)+' '+h*.55+'Q'+w*.75+' '+h*.48+' '+w*.5+' '+h*.55+'Q'+w*.25+' '+h*.48+' 2 '+h*.55+'Z',sage),path('M'+w*.5+' '+h*.14+'Q'+w*.25+' '+h*.3+' '+w*.22+' '+h*.53+'M'+w*.5+' '+h*.14+'Q'+w*.75+' '+h*.3+' '+w*.78+' '+h*.53,'none','stroke="#d3dcb4" stroke-width=".7"'),path('M'+w*.5+' '+h*.15+'V'+h*.85+'q0 '+h*.15+' -'+w*.18+' '+h*.08,'none','stroke="#d6bb8c" stroke-width="1.7"'));
    } else if(type==='vacuum') {
      b.push(rect(w*.45,0,w*.15,h*.59,metal,2),rect(w*.4,0,w*.25,h*.13,'#6f8c82',2),rect(w*.31,h*.3,w*.42,h*.28,white,3),rect(w*.36,h*.34,w*.32,h*.13,glass,2),path('M'+w*.48+' '+h*.55+'L'+w*.32+' '+h*.83,'none','stroke="#9eafa1" stroke-width="3"'),rect(0,h*.8,w,h*.16,metal,4),rect(4,h*.84,w-8,h*.06,'#67847b',2),circle(w*.53,h*.47,1.4,'#b5c8a8'));
    } else b.push(rect(0,0,w,h,cream,3),edge(2,2,w-4,h-4,2));
    b.push(rect(-2,-2,w+4,h+4,'transparent',3,'class="item-footprint"'));
    return b.join('');
  }
  // Small devices each retain their own silhouette, hardware and material details.
  function smallDevice(type,w,h,id,e) {
    var wood='url(#'+id+'wood)', white='url(#'+id+'porcelain)', glass='url(#'+id+'glass)', metal='url(#'+id+'metal)', cream='url(#'+id+'cream)', b=[],i,x,y;
    if(type==='washer'||type==='oven') {
      b.push(rect(0,0,w,h,metal,3),rect(2,2,w-5,h-5,white,2),rect(3,3,w-6,h*.19,'#bfd0c0',1),rect(5,5,w*.25,h*.08,glass,1),circle(w*.78,h*.12,Math.min(w,h)*.055,metal));
      if(type==='washer'){var rad=Math.min(w*.36,h*.3);b.push(circle(w*.5,h*.61,rad,'#f3f0db'),circle(w*.5,h*.61,rad*.82,metal),circle(w*.5,h*.61,rad*.65,glass),path('M'+(w*.5-rad*.5)+' '+h*.6+'q'+rad*.5+' '+rad*.7+' '+rad+' 0','none','stroke="#d3e2d0" stroke-width="1.2"'),rect(w*.8,h*.56,2,h*.12,'#82988b',1));}
      else {b.push(rect(4,h*.3,w-8,h*.58,'#425a55',2),rect(7,h*.36,w-14,h*.43,glass,1),rect(7,h*.28,w-14,3,metal,1));for(i=0;i<3;i++)b.push(line(9,h*(.49+i*.11),w-9,h*(.49+i*.11),'#b6bfaa77',.6));}
      b.push(line(5,h-4,w-5,h-4,'#748b7c',1));
    } else if(type==='coffee') {
      b.push(rect(0,0,w,h,metal,3),rect(2,2,w-4,h*.24,'#4d6860',2),rect(3,h*.28,w-6,h*.57,'#627c70',2),rect(w*.15,h*.41,w*.7,h*.37,'#314c48',1),rect(w*.3,h*.3,w*.35,h*.1,metal,1),rect(w*.43,h*.38,w*.1,h*.15,'#e6e8cc',1),rect(w*.3,h*.58,w*.34,h*.2,white,2),oval(w*.47,h*.58,w*.17,h*.04,'#ad8b60'),rect(3,h*.85,w-6,h*.08,metal,1));
      for(i=0;i<3;i++)b.push(circle(w*(.28+i*.22),h*.13,1.1,i?'#c9d5ba':'#e4c793'));
    } else if(type==='speaker') {
      b.push(rect(0,0,w,h,wood,3),rect(3,3,w-6,h-6,'#3f5550',2),circle(w*.5,h*.28,w*.13,'#a0b2a0'),circle(w*.5,h*.65,w*.29,'#2c4441'),circle(w*.5,h*.65,w*.2,'#728b7c'),circle(w*.5,h*.65,w*.09,'#bec9b2'),line(4,h-3,w-4,h-3,'#c4a47c',1));
    } else if(type==='popcorn') {
      b.push(rect(0,0,w,h,wood,3),rect(3,h*.17,w-6,h*.56,glass,2),rect(1,0,w-2,h*.13,cream,2),rect(3,h*.77,w-6,h*.17,'#b98d83',1),line(w*.5,h*.17,w*.5,h*.72,'#d4d8b8',.8));for(i=0;i<9;i++)b.push(circle(6+(i%4)*(w-12)/4,h*.51+Math.floor(i/4)*4,2.3,'#e8d5a3'));
    } else if(type==='grill') {
      b.push(line(w*.22,h*.43,w*.12,h,metal,2),line(w*.78,h*.43,w*.88,h,metal,2),line(w*.5,h*.5,w*.5,h*.94,metal,2),oval(w*.5,h*.4,w*.48,h*.29,'#54685c'),oval(w*.5,h*.29,w*.44,h*.15,'#2f4640'));
      for(i=0;i<6;i++)b.push(line(w*.18+i*w*.12,h*.2,w*.18+i*w*.12,h*.38,metal,.8));b.push(rect(w*.4,h*.03,w*.2,h*.08,wood,2),line(w*.25,h*.82,w*.74,h*.82,metal,1.2));
    } else if(type==='toaster') {
      b.push(rect(0,h*.08,w,h*.85,metal,4),rect(3,h*.12,w-6,h*.7,white,3),rect(w*.15,0,w*.22,h*.2,'#d8ba87',2),rect(w*.54,0,w*.22,h*.2,'#d8ba87',2),rect(w*.14,h*.17,w*.65,2,'#6c8071',1),circle(w*.78,h*.63,2,wood),rect(w*.86,h*.35,2,h*.2,'#819789',1));
    } else if(type==='console') {
      b.push(rect(0,0,w,h,'#486258',3),rect(2,2,w-4,h-5,white,2),rect(w*.18,h*.21,w*.64,h*.45,'#63867f',2),line(w*.35,h*.38,w*.35,h*.56,'#dfe8cf',1.4),line(w*.27,h*.47,w*.43,h*.47,'#dfe8cf',1.4),circle(w*.68,h*.36,1.2,'#cfac8b'),circle(w*.75,h*.5,1.2,'#a0ba9d'),circle(w*.5,h*.77,.8,'#7b9a88'));
    } else if(type==='kettle') {
      b.push(path('M'+w*.24+' '+h*.3+'Q'+w*.2+' '+h*.1+' '+w*.59+' '+h*.2+'L'+w*.78+' '+h*.76+'Q'+w*.52+' '+h+' '+w*.19+' '+h*.77+'Z',white),path('M'+w*.67+' '+h*.3+'q'+w*.45+' -'+h*.06+' '+w*.18+' '+h*.42,'none','stroke="#9ab6a3" stroke-width="2.4"'),path('M'+w*.22+' '+h*.45+'L0 '+h*.25+'L'+w*.15+' '+h*.65+'Z',metal),oval(w*.43,h*.23,w*.2,h*.06,metal),circle(w*.42,h*.16,2,wood),line(w*.3,h*.36,w*.28,h*.67,'#f7f3dc',1.1));
    } else if(type==='tea') {
      b.push(rect(0,h*.13,w,h*.8,wood,4),rect(3,h*.24,w-6,h*.58,cream,3),oval(w*.38,h*.53,w*.17,h*.29,white),oval(w*.38,h*.3,w*.1,h*.06,metal),path('M'+w*.22+' '+h*.48+'L'+w*.09+' '+h*.29+'L'+w*.2+' '+h*.67+'Z',white),circle(w*.38,h*.23,1.5,wood),rect(w*.65,h*.38,w*.14,h*.29,white,2),oval(w*.72,h*.39,w*.07,h*.06,'#a48b5f'));
    } else if(type==='keys') {
      b.push(rect(0,0,w,h,wood,5),rect(3,3,w-6,h-6,cream,4),circle(w*.33,h*.46,Math.min(w,h)*.17,'none','stroke="#ac966c" stroke-width="1.4"'),line(w*.43,h*.5,w*.75,h*.66,metal,2),line(w*.66,h*.61,w*.64,h*.76,metal,1.4),rect(w*.6,h*.19,w*.2,h*.3,'#899f8a',2));
    } else if(type==='ricecooker') {
      b.push(rect(0,h*.16,w,h*.76,white,5),oval(w*.5,h*.17,w*.48,h*.15,metal),oval(w*.5,h*.13,w*.36,h*.08,'#d3deca'),rect(w*.25,h*.37,w*.5,h*.35,metal,2),rect(w*.31,h*.43,w*.38,h*.13,glass,1),circle(w*.4,h*.64,1.1,'#e1c599'),circle(w*.6,h*.64,1.1,'#9cb49a'),rect(w*.39,h*.02,w*.22,h*.08,'#718c7a',1),line(4,h*.83,w-4,h*.83,'#94aa95',.7));
    } else if(type==='pourover') {
      b.push(oval(w*.5,h*.9,w*.44,h*.08,wood),path('M'+w*.24+' '+h*.49+'H'+w*.69+'L'+w*.81+' '+h*.86+'Q'+w*.5+' '+h+' '+w*.16+' '+h*.86+'Z',glass),path('M'+w*.19+' '+h*.75+'H'+w*.76+'L'+w*.8+' '+h*.86+'Q'+w*.5+' '+h*.94+' '+w*.18+' '+h*.86+'Z','#927657'),path('M'+w*.1+' '+h*.12+'H'+w*.89+'L'+w*.57+' '+h*.52+'H'+w*.42+'Z',white),oval(w*.5,h*.12,w*.39,h*.08,'#d8cfad'),oval(w*.5,h*.12,w*.27,h*.045,'#a17b55'),line(w*.29,h*.22,w*.44,h*.45,'#cad4bb',.8),line(w*.7,h*.22,w*.57,h*.45,'#cad4bb',.8));
    } else if(type==='wateringcan') {
      b.push(rect(w*.2,h*.25,w*.56,h*.62,metal,4),path('M'+w*.69+' '+h*.35+'Q'+w*1.1+' '+h*.08+' '+w*.86+' '+h*.79,'none','stroke="#a5bba4" stroke-width="3"'),path('M'+w*.22+' '+h*.58+'L'+w*.02+' '+h*.22+'L0 '+h*.37+'L'+w*.23+' '+h*.78+'Z',white),oval(w*.03,h*.26,w*.05,h*.1,metal),oval(w*.48,h*.26,w*.27,h*.07,'#bad0b8'),path('M'+w*.3+' '+h*.26+'Q'+w*.52+' -'+h*.1+' '+w*.68+' '+h*.26,'none','stroke="#d0d9bc" stroke-width="2"'),line(w*.31,h*.39,w*.31,h*.71,'#f1edd8',.8));
    } else if(type==='projector') {
      b.push(rect(0,h*.1,w,h*.79,metal,3),rect(2,h*.12,w-4,h*.65,white,3),circle(w*.73,h*.48,h*.22,'#344e48'),circle(w*.73,h*.48,h*.16,glass),circle(w*.7,h*.43,1.2,'#e1e9cd'),rect(w*.11,h*.25,w*.22,h*.08,'#92aa97',1));for(i=0;i<4;i++)b.push(line(w*.1,h*(.46+i*.065),w*.34,h*(.46+i*.065),'#81978a',.6));
    } else if(type==='diffuser') {
      b.push(oval(w*.5,h*.86,w*.45,h*.09,wood),path('M'+w*.1+' '+h*.8+'Q'+w*.02+' '+h*.4+' '+w*.5+' '+h*.3+'Q'+w*.96+' '+h*.4+' '+w*.9+' '+h*.8+'Z',white),oval(w*.5,h*.37,w*.11,h*.03,'#718f80'),path('M'+w*.48+' '+h*.27+'q-'+w*.14+' -'+h*.1+' 0 -'+h*.23,'none','stroke="#dce7d1" stroke-opacity=".7" stroke-width="1"'),circle(w*.51,h*.7,1,'#a2bd95'));
    } else if(type==='jar') {
      b.push(rect(w*.13,h*.18,w*.74,h*.74,glass,3),rect(w*.09,h*.07,w*.82,h*.17,wood,2),rect(w*.22,h*.43,w*.56,h*.28,cream,2));for(i=0;i<6;i++)b.push(circle(w*(.24+(i%3)*.22),h*(.78+Math.floor(i/3)*.065),1,'#e7dfbe'));b.push(line(w*.31,h*.53,w*.69,h*.53,'#b2aa8a',.8));
    } else if(type==='mask') {
      b.push(rect(0,0,w,h,cream,2),rect(2,2,w-4,h-4,'#a5b8a1',2),oval(w*.51,h*.46,w*.19,h*.3,'#e9edda'),oval(w*.44,h*.41,w*.04,h*.025,'#8a9e88'),oval(w*.58,h*.41,w*.04,h*.025,'#8a9e88'),path('M'+w*.44+' '+h*.63+'Q'+w*.51+' '+h*.68+' '+w*.58+' '+h*.63,'none','stroke="#9ba88d" stroke-width=".7"'),line(w*.27,h*.84,w*.74,h*.84,'#e0e5cd',.6));
    } else if(type==='camera') {
      b.push(rect(0,h*.16,w,h*.73,'#465e56',3),rect(w*.12,0,w*.3,h*.23,metal,2),rect(w*.7,h*.05,w*.15,h*.12,wood,1),rect(3,h*.26,w-6,h*.5,'#789084',2),circle(w*.53,h*.54,Math.min(w,h)*.29,metal),circle(w*.53,h*.54,Math.min(w,h)*.22,'#2c4c4d'),circle(w*.53,h*.54,Math.min(w,h)*.13,glass),circle(w*.49,h*.5,1.5,'#d4e3c9'),rect(w*.1,h*.32,w*.12,h*.09,cream,1));
    } else if(type==='iron') {
      b.push(path('M0 '+h*.74+'Q'+w*.27+' '+h*.17+' '+w*.88+' '+h*.27+'L'+w+' '+h*.85+'Z',metal),path('M3 '+h*.68+'Q'+w*.3+' '+h*.28+' '+w*.83+' '+h*.36+'L'+w*.91+' '+h*.71+'Z',white),path('M'+w*.3+' '+h*.45+'Q'+w*.52+' -'+h*.14+' '+w*.82+' '+h*.45,'none','stroke="#91aa96" stroke-width="3"'),circle(w*.6,h*.49,2,wood),line(2,h*.83,w-1,h*.9,'#5f7e72',1.4));
    } else {
      b.push(rect(w*.18,h*.26,w*.64,h*.68,white,3),rect(w*.24,h*.05,w*.52,h*.25,metal,1.5),rect(w*.28,h*.44,w*.44,h*.28,'#9bb39a',1.5),line(w*.35,h*.53,w*.65,h*.53,'#ebead4',.7),line(w*.37,h*.61,w*.61,h*.61,'#ebead4',.7),line(w*.26,h*.37,w*.26,h*.8,'#f6f3dd',.9));
    }
    return b.join('');
  }
  // Draw in normalized coordinates so slim perspective panels never invert details.
  function appliance(type,w,h,id){
    var b=[],metal='url(#'+id+'metal)';
    b.push(rect(0,0,60,60,'#647d73',2),rect(1,1,58,58,metal,1.5),rect(3,3,54,10,'#c2d1c4',1));
    if(type==='oven'){
      b.push(circle(10,8,2.6,'#6d857a'),circle(50,8,2.6,'#6d857a'),rect(24,5,13,6,'#455e55',1),line(27,8,34,8,'#bbd3bd',.7));
      b.push(rect(4,16,52,38,'#40564f',2),rect(8,21,44,28,'#688b88',1.5),rect(8,14,44,3,'#d9e2cf',1));
      for(var i=0;i<3;i++)b.push(line(11,30+i*7,49,30+i*7,'#c4d4c09a',.65));
      b.push(path('M10 23h14L10 38Z','#d5e4da22'),line(9,56,51,56,'#70867a',.8));
    }else{
      b.push(rect(8,6,17,4,'#718f83',1),circle(48,8,1.7,'#7d9a82'),circle(53,8,1.2,'#b0c8ad'));
      b.push(rect(4,15,52,40,'#d4dfd1',1.5),rect(18,16,24,4,'#7e998b',1),line(20,17,40,17,'#eef0dc',.8));
      b.push(line(7,24,7,50,'#f5f3e2',1),line(8,55,52,55,'#a5baac',.8),rect(5,56,50,2,'#819b8d',.5));
    }
    return '<g class="appliance-panel" data-appliance="'+type+'" transform="scale('+(w/60)+' '+(h/60)+')">'+b.join('')+'</g>';
  }
  root.FurnitureArt={draw:draw};
})(typeof window==='undefined'?globalThis:window);
