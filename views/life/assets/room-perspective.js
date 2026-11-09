/* Cutaway rooms projected directly from the physical plan, including support heights. */
(function(root){
  'use strict';
  function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function camera(room,w,d){
    var a=/浴室|阳台|衣帽间|玄关/.test(room)?-.38:.38,k=.65,wall=132,s=Math.min(570/(w+Math.abs(a)*d),382/(wall+k*d));
    var ox=(600-(w+Math.abs(a)*d)*s)/2+(a<0?-a*d*s:0),oy=32+wall*s;
    return {a:a,k:k,s:s,ox:ox,oy:oy,wall:wall,point:function(x,y,z){return [ox+s*(x+a*y),oy+s*(k*y-(z||0))];}};
  }
  function draw(room,size,items,types,e,appearance,now){
    var M=root.RoomModel,c=camera(room,size.w,size.h),id='close-',b=[],wood='url(#'+id+'wood)',top='url(#'+id+'woodTop)',cloth='url(#'+id+'fabric)',sage='url(#'+id+'sage)',cream='url(#'+id+'cream)',metal='url(#'+id+'metal)',glass='url(#'+id+'glass)',open=/阳台|露台/.test(room),fixtures=M.fixtures[room]||[];
    function point(x,y,z){return c.point(x,y,z);}
    function polygon(points,color,extra){return '<polygon points="'+points.map(function(p){return point(p[0],p[1],p[2]).join(',');}).join(' ')+'" fill="'+color+'" '+(extra||'')+'/>';}
    function line(a,z,color,width){var x=point(a[0],a[1],a[2]),y=point(z[0],z[1],z[2]);return '<path d="M'+x.join(' ')+'L'+y.join(' ')+'" fill="none" stroke="'+color+'" stroke-width="'+(width||1)+'" stroke-linecap="round"/>';}
    function box(x,y,z,w,d,h,color,cap){
      var a=c.a>0?x:x+w;
      var left=[[a,y,z],[a,y+d,z],[a,y+d,z+h],[a,y,z+h]],front=[[x,y+d,z],[x+w,y+d,z],[x+w,y+d,z+h],[x,y+d,z+h]],upper=[[x,y,z+h],[x+w,y,z+h],[x+w,y+d,z+h],[x,y+d,z+h]];
      var art=polygon(left,color,'style="filter:brightness(.88)" stroke="#5d58403a" stroke-width=".5"')+polygon(front,color,'style="filter:brightness(.97)" stroke="#66503940" stroke-width=".55"')+polygon(upper,cap||color,'stroke="#fff0d680" stroke-width=".6"');
      if(color===wood||color===top)art+=polygon(left,'url(#'+id+'grain)','opacity=".6"')+polygon(front,'url(#'+id+'grain)','opacity=".7"')+polygon(upper,'url(#'+id+'grain)','opacity=".45"');
      if(color===cloth||color===sage)art+=polygon(front,'url(#'+id+'weave)')+polygon(upper,'url(#'+id+'weave)');
      return art;
    }
    function topArt(x,y,z,markup){var p=point(x,y,z);return '<g transform="matrix('+c.s+' 0 '+(c.a*c.s)+' '+(c.k*c.s)+' '+p[0]+' '+p[1]+')">'+markup+'</g>';}
    function frontArt(x,y,z,w,d,h,face,markup,twoSided){
      var p,ux,uy;if(!twoSided&&(face==='N'||face==='E'&&c.a>0||face==='W'&&c.a<0))return '';
      if(face==='S'){p=point(x,y+d,z+h);ux=c.s;uy=0;}
      else {p=point(face==='W'?x:x+w,y,z+h);ux=c.a*c.s;uy=c.k*c.s;}
      return '<g transform="matrix('+ux+' '+uy+' 0 '+c.s+' '+p[0]+' '+p[1]+')">'+markup+'</g>';
    }
    function native(type,w,h,front){return root.FurnitureArt.draw(type,w,h,id,e,front);}
    function slab(x,y,z,w,d,color){return box(x,y,z,w,d,2,color||top,color||top);}
    function local(p,face,u,v){if(face==='N')return [p[0]+p[2]-u,p[1]+p[3]-v];if(face==='E')return [p[0]+v,p[1]+p[3]-u];if(face==='W')return [p[0]+p[2]-v,p[1]+u];return [p[0]+u,p[1]+v];}
    function localBox(p,face,u,v,z,w,d,h,color){var a=local(p,face,u,v),q=local(p,face,u+w,v+d);return box(Math.min(a[0],q[0]),Math.min(a[1],q[1]),z,Math.abs(q[0]-a[0]),Math.abs(q[1]-a[1]),h,color);}
    function seat(p,face,h,chair){
      var L=/E|W/.test(face)?p[3]:p[2],D=/E|W/.test(face)?p[2]:p[3],out=[],parts=[],seatZ=chair?21:19;
      if(chair)parts.push([2,3,0,3,3,seatZ,wood],[L-5,3,0,3,3,seatZ,wood],[2,D-6,0,3,3,seatZ,wood],[L-5,D-6,0,3,3,seatZ,wood]);
      else parts.push([1,1,3,L-2,D-2,seatZ-3,wood]);
      parts.push([2,3,seatZ,L-4,D-6,chair?3:6,sage],[1,0,seatZ,L-2,chair?4:10,h-seatZ,cloth]);
      if(!chair)parts.push([0,6,seatZ,7,D-6,15,cloth],[L-7,6,seatZ,7,D-6,15,cloth]);
      parts.sort(function(a,b){var a1=local(p,face,a[0]+a[3]/2,a[1]+a[4]/2),b1=local(p,face,b[0]+b[3]/2,b[1]+b[4]/2);return (a1[1]-b1[1])+(c.a>0?b1[0]-a1[0]:a1[0]-b1[0])*.3;});
      parts.forEach(function(a){out.push(localBox(p,face,a[0],a[1],a[2],a[3],a[4],a[5],a[6]));});
      if(!chair){for(var i=1;i<3;i++){var t=local(p,face,L*i/3,13),u=local(p,face,L*i/3,D-5);out.push(line([t[0],t[1],26],[u[0],u[1],26],'#e4ddc1',.7));}}
      if(!chair){
        var cushionW=Math.min(20,L*.24), cushionD=Math.min(18,D*.38);
        [[L*.18,'#f5e8cd'],[L*.65,'#c8abc2']].forEach(function(spec){
          out.push(localBox(p,face,spec[0],11,26,cushionW,cushionD,9,spec[1]));
          var a=local(p,face,spec[0]+2,13),q=local(p,face,spec[0]+cushionW-2,13);
          out.push(line([a[0],a[1],35],[q[0],q[1],35],'#fff7e5',.8));
        });
        var t=local(p,face,L*.43,D*.40),q=local(p,face,L*.58,D*.88);
        out.push(topArt(Math.min(t[0],q[0]),Math.min(t[1],q[1]),26.2,'<rect width="'+Math.max(5,Math.abs(q[0]-t[0]))+'" height="'+Math.max(5,Math.abs(q[1]-t[1]))+'" rx="2" fill="#d8ccb6"/><path d="M2 2v8m4-8v8m4-8v8" stroke="#f4e8cf" stroke-width=".7"/>'));
      }
      return out.join('');
    }
    function table(p,h,type){var x=p[0],y=p[1],w=p[2],d=p[3],out=[];[[3,3],[w-7,3],[3,d-7],[w-7,d-7]].forEach(function(a){out.push(box(x+a[0],y+a[1],0,4,4,h-3,wood));});out.push(slab(x,y,h-3,w,d,top),topArt(x+1,y+1,h, '<rect width="'+(w-2)+'" height="'+(d-2)+'" rx="2" fill="url(#'+id+'grain)"/>'));if(type==='dining')out.push(topArt(x+w*.23,y+d*.42,h+.3,'<circle r="6" fill="#e5e8d3" stroke="#adbea8"/>'),topArt(x+w*.76,y+d*.42,h+.3,'<circle r="6" fill="#e5e8d3" stroke="#adbea8"/>'));return out.join('');}
    function object(p,type,m,z){
      var x=p[0],y=p[1],w=p[2],d=p[3],h=m.height,f=m.facing,out=[];z=z||0;
      if(m.inset&&(type==='oven'||type==='dishwasher')){
        var support=fixtures.filter(function(q){return q.id===m.mount;})[0];
        var counterHeight=support?support.h:h+2,doorTop=Math.min(h,counterHeight-2),doorBottom=2;
        var sideways=/E|W/.test(f),span=(sideways?d:w)-2;
        // Only the flush front is exposed; the cabinet owns the carcass and worktop.
        out.push('<g class="inset-appliance" data-appliance="'+type+'" data-door-top="'+doorTop+'" data-counter-height="'+counterHeight+'">');
        out.push(frontArt(x+(f==='W'?-.12:1),y+(sideways?1:0),doorBottom,sideways?w:span,sideways?d-2:d,doorTop-doorBottom,f,native(type,span,doorTop-doorBottom,true)));
        if(type==='oven'){
          var hobW=w-6,hobD=d-6,hob=[];
          hob.push('<rect width="'+hobW+'" height="'+hobD+'" rx="2" fill="#465c54" stroke="#b4c5b6" stroke-width=".7"/>');
          [[.28,.28],[.72,.28],[.28,.7],[.72,.7]].forEach(function(q){hob.push('<circle cx="'+hobW*q[0]+'" cy="'+hobD*q[1]+'" r="'+Math.min(hobW,hobD)*.16+'" fill="none" stroke="#becbbb" stroke-width=".8"/>');});
          hob.push('<path d="M'+hobW*.38+' '+hobD*.93+'h'+hobW*.24+'" stroke="#d2dac5" stroke-width=".7"/>');
          out.push(topArt(x+3,y+3,counterHeight+.15,'<g class="appliance-cooktop">'+hob.join('')+'</g>'));
        }
        out.push('</g>');
        return out.join('');
      }
      var finished=root.FurnitureFinish.draw(p,type,m,z,{point:point,polygon:polygon,line:line,box:box,top:topArt,front:frontArt,camera:c});
      if(finished!==null)return finished;
      var shaped=root.ObjectShapes.draw(p,type,m,z,{point:point,polygon:polygon,line:line,box:box,top:topArt,front:frontArt,camera:c,environment:e});
      if(shaped!==null)return shaped;
      if(type==='sofa'||type==='rockingchair')return seat(p,f,h,false);
      if(type==='bed')return box(x,y,z,w,5,43,wood)+box(x,y,z,w,d,19,wood)+box(x+2,y+2,z+19,w-4,d-4,7,cream)+topArt(x+4,y+7,z+27,'<rect width="'+(w-8)+'" height="'+(d-11)+'" rx="5" fill="url(#close-cream)"/><rect x="4" y="3" width="'+(w*.39)+'" height="20" rx="5" fill="#eee4c5" stroke="#b9ad8b" stroke-width=".5"/><rect x="'+(w*.51)+'" y="3" width="'+(w*.38)+'" height="20" rx="5" fill="#eee4c5" stroke="#b9ad8b" stroke-width=".5"/><rect x="1" y="31" width="'+(w-10)+'" height="'+(d-45)+'" rx="3" fill="url(#close-fabric)"/><path d="M7 40v'+(d-67)+'m18-'+(d-67)+'v'+(d-67)+'m18-'+(d-67)+'v'+(d-67)+'m18-'+(d-67)+'v'+(d-67)+'" stroke="#e5d1c9" stroke-width=".6"/><rect x="2" y="'+(d-37)+'" width="'+(w-12)+'" height="20" rx="2" fill="url(#close-sage)"/>');
      if(/^(desk|dining|table)$/.test(type))return table(p,h,type);
      if(/^(cabinet|jewelry|bookshelf|fridge|vanity)$/.test(type)){
        var bodyH=type==='vanity'?35:h,frontW=/E|W/.test(f)?d:w;
        out.push(box(x,y,z,w,d,bodyH,type==='fridge'?metal:wood, type==='fridge'?metal:top));
        out.push(frontArt(x,y,z,w,d,bodyH,f,native(type==='vanity'?'cabinet':type,frontW,bodyH,true)));
        if(type==='vanity')out.push(box(x+w*.6,y+7,z+bodyH,3,d-14,h-bodyH,metal),frontArt(x+w*.6,y+7,z+bodyH,3,d-14,h-bodyH,f,native('mirror',d-14,h-bodyH,true)));
      } else if(/^(monitor|screen|mirror)$/.test(type)){
        var panelZ=z+(type==='mirror'?8:type==='screen'&&m.mount==='wall'?48:6),panelH=type==='mirror'?h-8:h,fw=/E|W/.test(f)?d:w;
        out.push(box(x,y,panelZ,w,d,panelH,type==='mirror'?wood:'#354b4c',metal),frontArt(x-.1,y,panelZ,w,d,panelH,f,native(type==='monitor'?'screen':type,fw,panelH,true)));
        if(type==='monitor'&&!/tv/.test(m.id))out.push(box(x+w*.45,y+d*.35,z,Math.max(3,w*.1),Math.max(4,d*.5),7,metal));
        if(type==='screen'&&m.mount!=='wall')out.push(box(x+w*.3,y+d*.4,z,Math.max(3,w*.4),Math.max(4,d*.2),6,metal));
      } else if(type==='tub'){
        out.push(box(x,y,0,w,d,h,metal,cream),topArt(x+3,y+3,h+.2,native('tub',w-6,d-6,false)));
      } else if(type==='shower'){
        out.push(slab(x,y,0,w,d,cream),polygon([[x+w,y,0],[x+w,y+d,0],[x+w,y+d,h],[x+w,y,h]],'#a4d0ce4d','stroke="#c4d8bf" stroke-width="1"'),polygon([[x,y+d,0],[x+w,y+d,0],[x+w,y+d,h],[x,y+d,h]],'#b8ddce28','stroke="#b8d1bd" stroke-width="1"'),line([x+w-3,y+3,10],[x+w-3,y+3,98],'#a8bfae',2),box(x+w-10,y+1,92,13,13,3,metal));
        out.push(line([x+2,y+d,3],[x+w-2,y+d,3],'#dce7d2',2),line([x+w,y+2,3],[x+w,y+d,3],'#c0d3c2',2));
        out.push(line([x+w*.72,y+d,43],[x+w*.72,y+d,56],'#d9e3cc',2),line([x+w*.72+2,y+d,43],[x+w*.72+2,y+d,56],'#79968d',.7));
        out.push(line([x+w*.14,y+d,72],[x+w*.39,y+d,95],'#f4f9e545',1.2),line([x+w*.19,y+d,65],[x+w*.43,y+d,87],'#f4f9e530',.8));
        out.push(topArt(x+w*.55,y+d*.55,2.2,'<rect width="8" height="5" rx="1" fill="#97aca2"/><path d="M2 1v3m2-3v3m2-3v3" stroke="#d7dfce" stroke-width=".5"/>'));
      } else if(type==='piano'){
        var backDepth=d*.42,keyZ=h*.56;
        out.push(box(x,y,0,w,backDepth,h,wood,top));
        out.push(frontArt(x+5,y, keyZ+5,w-10,backDepth,h-keyZ-10,'S','<rect width="'+(w-10)+'" height="'+(h-keyZ-10)+'" rx="2" fill="none" stroke="#dfc9a3" stroke-width=".8"/><path d="M'+(w*.35)+' 4h'+w*.2+'" stroke="#f6df9c" stroke-width="1.3"/>'));
        out.push(box(x+4,y+d-7,0,5,6,keyZ,wood),box(x+w-9,y+d-7,0,5,6,keyZ,wood),slab(x,y,keyZ-2,w,d,wood));
        out.push(topArt(x+4,y+backDepth,keyZ+.1,native('pianokeys',w-8,d-backDepth-2,false)));
        out.push(frontArt(x+7,y,4,w-14,backDepth,keyZ-10,'S','<rect width="'+(w-14)+'" height="'+(keyZ-10)+'" rx="2" fill="none" stroke="#ddc39c" stroke-width=".6"/>'));
        [w*.43,w*.5,w*.57].forEach(function(px){out.push(box(x+px,y+backDepth,2,3,7,2,metal));});
      } else if(type==='easel'){
        out.push(box(x+3,y+d-6,0,5,6,16,wood),box(x+w-8,y+d-6,0,5,6,16,wood),frontArt(x,y,5,w,d,h-5,'S',native('easel',w,h-5,true)));
      } else if(type==='swing'){
        out.push(box(x,y,0,4,5,h,wood),box(x+w-4,y,0,4,5,h,wood),box(x,y,h-5,w,5,5,top),seat([x+10,y+8,w-20,d-10],'S',44,false),line([x+13,y+10,39],[x+13,y+2,h-5],'#d4bf99',1.2),line([x+w-13,y+10,39],[x+w-13,y+2,h-5],'#d4bf99',1.2));
      } else if(type==='stairs'){
        for(var i=8;i>=0;i--)out.push(box(x+i*w/9,y,0,w/9,d,(i+1)*h/9,wood,top));out.push(line([x,y,22],[x+w,y,h+22],'#bdd0b8',2),line([x,y+d,22],[x+w,y+d,h+22],'#bdd0b8',2));
      } else if(type==='treadmill'){
        out.push(box(x,y,0,w,d,5,'#4b6a5a',sage),topArt(x+3,y+4,6,'<rect width="'+(w-6)+'" height="'+(d-8)+'" rx="3" fill="#385346"/>'),box(x+3,y+4,4,3,5,h-8,metal),box(x+w-6,y+4,4,3,5,h-8,metal),frontArt(x+8,y+4,h-18,w-16,4,16,'S',native('console',w-16,16,true)));
      } else if(type==='towel'&&m.mount==='wall'){
        out.push(frontArt(x,y,57,w,d,24,'W',native('towel',d,24,true),true),line([x,y,82],[x,y+d,82],'#b6c9b1',2));
      } else if(type==='mat'||type==='towel'||type==='book'||type==='board'||type==='keyboard'||type==='keys'||type==='mask'||type==='tea'){
        out.push(box(x,y,z,w,d,Math.min(h,3),wood),topArt(x,y,z+Math.min(h,3)+.2,native(type,w,d,false)));
      } else if(type==='plants'){
        out.push(box(x,y,z,w,d,13,wood,top));for(var px=8;px<w-4;px+=22)out.push(frontArt(x+px-5,y+2,z+10,12,d-4,h,'S','<path d="M7 30V6m0 18q-12-2-6-14 8 2 6 14m0-4q12-6 10-17-10 0-10 17" fill="#83a67c" stroke="#668c68" stroke-width=".5"/><path d="M7 19q-6-14 0-18 8 7 0 18" fill="#abc399"/>'));
      } else if(type==='telescope'){
        out.push(line([x+w*.5,y+d*.5,46],[x+3,y+3,0],'#bbccba',1.5),line([x+w*.5,y+d*.5,46],[x+w-3,y+4,0],'#bbccba',1.5),line([x+w*.5,y+d*.5,46],[x+w*.5,y+d-3,0],'#bbccba',1.5),box(x,y+d*.4,44,w,9,10,metal,cream),frontArt(x+w-2,y+d*.4,44,2,9,10,'E','<ellipse cx="4.5" cy="5" rx="4" ry="4.5" fill="url(#close-glass)"/>'));
      } else if(type==='lamp'||type==='floorlamp'||type==='bear'||type==='umbrella'||type==='vacuum'||type==='chime'){
        out.push(frontArt(x,y,z,w,d,h,'S',native(type,w,h,true)));
      } else {
        var hw=/E|W/.test(f)?d:w;
        out.push(box(x,y,z,w,d,h,/washer|oven|coffee|speaker|popcorn|toaster|ricecooker/.test(type)?metal:wood,type==='aquarium'?glass:top));
        
        out.push(frontArt(x,y,z,w,d,h,f,native(type,hw,h,true)));
        if(type==='record')out.push(topArt(x,y,z+h+.1,native(type,w,d,false)));
        if(type==='aquarium')out.push(topArt(x+2,y+2,z+h+.1,'<rect width="'+(w-4)+'" height="'+(d-4)+'" rx="1" fill="#7eaea16b"/>'));
      }
      return out.join('');
    }
    function fixtureArt(f){
      var p=[f.x,f.y,f.w,f.d],out=[],h=f.h;
      if(f.type==='chair')return root.FurnitureFinish.draw(p,'chair',{height:h,facing:f.facing},0,{point:point,polygon:polygon,line:line,box:box,top:topArt,front:frontArt,camera:c});
      if(f.type==='stairs'){var n=16,run=f.w/n,top2=Math.min(h,128),order=[];for(var si=0;si<n;si++)order.push(si);if(c.point(1,0,0)[0]>c.point(0,0,0)[0]===false)order.reverse();
        // a flight rising along +x up to the next floor; painted far-to-near so each tread covers the riser behind
        order.reverse().forEach(function(i){out.push(box(f.x+i*run,f.y,0,run+.4,f.d,(i+1)*top2/n,wood,top));});
        out.push(line([f.x,f.y+f.d,top2/n+30],[f.x+f.w,f.y+f.d,top2+30],'#7d5a40',3));for(var bi=1;bi<n;bi+=2)out.push(line([f.x+bi*run,f.y+f.d,(bi+1)*top2/n],[f.x+bi*run,f.y+f.d,(bi+1)*top2/n+30],'#7d5a40',1.4));
        return out.join('');}
      if(f.type==='bench')return table(p,h,'table');
      if(f.type==='sink')return root.FurnitureFinish.draw(p,'sink',{height:h,facing:f.facing},0,{point:point,polygon:polygon,line:line,box:box,top:topArt,front:frontArt,camera:c});
      if(f.type==='clothes'){
        out.push(box(f.x+f.w/2,f.y,0,3,4,h,wood),box(f.x+f.w/2,f.y+f.d-4,0,3,4,h,wood),line([f.x+f.w/2,f.y,h-3],[f.x+f.w/2,f.y+f.d,h-3],'#b9c9b0',2));
        for(var hanger=12;hanger<f.d-9;hanger+=17)out.push(polygon([[f.x+f.w/2,f.y+hanger,h-10],[f.x+f.w/2,f.y+hanger-7,h-23],[f.x+f.w/2,f.y+hanger-4,h-62],[f.x+f.w/2,f.y+hanger+7,h-62],[f.x+f.w/2,f.y+hanger+10,h-23]],hanger%2?'#b496a4':'#a9bb9b','stroke="#e3d6ba" stroke-width=".4"'));
        return out.join('');
      }
      out.push(box(f.x,f.y,0,f.w,f.d,h,wood,cream));
      if(/counter|basin/.test(f.type)){
        var fw=/E|W/.test(f.facing)?f.d:f.w,panels=[],count=Math.max(1,Math.round(fw/40)),pw=fw/count;
        for(var door=0;door<count;door++)panels.push('<rect x="'+(door*pw+3)+'" y="5" width="'+(pw-6)+'" height="'+(h-10)+'" rx="1.8" fill="'+(room==='厨房'?'#c2cbb4':room==='浴室'?'#b4c9bd':'#c7b18e')+'" stroke="#eee3cb" stroke-width=".6"/><path d="M'+(door*pw+pw*.65)+' 12h'+(pw*.18)+'" stroke="#f4e1ae" stroke-width="1.5" stroke-linecap="round"/>');
        out.push(frontArt(f.x,f.y,0,f.w,f.d,h,f.facing,panels.join('')));
      }

      if(f.type==='basin')out.push(root.FurnitureFinish.draw([f.x+5,f.y+27,32,30],'sink',{height:h,facing:'S'},0,{point:point,polygon:polygon,line:line,box:box,top:topArt,front:frontArt,camera:c}));
      return out.join('');
    }
    // Far walls and floor use the same room outline and units as the plan.
    b.push('<rect width="600" height="440" fill="'+(open?'#bdd0b3':'#e8e9de')+'"/>');
    if(open)b.push('<rect width="600" height="240" fill="url(#close-sky)"/>','<path d="M0 205Q120 110 251 194T600 173V287H0Z" fill="#7d9c88"/>');
    b.push(polygon([[0,0,0],[size.w,0,0],[size.w,size.h,0],[0,size.h,0]],'url(#'+id+(/浴室|厨房/.test(room)?'tiles':'planks')+')','stroke="#bba784" stroke-width="2"'));
    if(root.HouseInterior)b.push(topArt(0,0,.02,root.HouseInterior.floor(room,size.w,size.h)));
    var lop=((root.RoomModel||{}).openings||{})[room],lw=lop?(lop.N||[]).filter(function(o){return o[2]==='win';})[0]:[size.w*.35,size.w*.65];if(lw&&!e.dark&&!open&&!/rain|storm|fog/.test(e.weather))b.push(polygon([[lw[0],5,.1],[lw[1],5,.1],[lw[1]+size.w*.14,size.h*.68,.1],[lw[0]-size.w*.05,size.h*.68,.1]],e.band==='dusk'?'#ffdaa344':'#fff7d844','pointer-events="none"'));
    var rug=M.rugs[room];if(rug)b.push(topArt(rug[0],rug[1],.15,root.HouseInterior.rug(room,rug[2],rug[3])));
    if(!open){
      b.push(polygon([[0,0,0],[size.w,0,0],[size.w,0,c.wall],[0,0,c.wall]],root.HouseInterior.theme(room).wall,'stroke="#c8b799" stroke-width="1.5"'));
      var side=c.a>0?size.w:0;
      b.push(polygon([[side,0,0],[side,size.h,0],[side,size.h,c.wall],[side,0,c.wall]],root.HouseInterior.theme(room).side,'stroke="#b2b99c" stroke-width="1.5"'));
      b.push(root.HouseInterior.walls(room,size,c,{front:frontArt,polygon:polygon,line:line,box:box},e));
      var op=((root.RoomModel||{}).openings||{})[room],nw=op?(op.N||[]).filter(function(o){return o[2]==='win';})[0]:null,wx=op?(nw?nw[0]:0):size.w*.35,ww=op?(nw?nw[1]-nw[0]:0):size.w*.3,hasWin=op?!!nw:room!=='影音室';
      if(hasWin)b.push(frontArt(wx,-.1,68,ww,0,52,'S','<rect width="'+ww+'" height="52" rx="2" fill="#c6b28c"/><rect x="3" y="3" width="'+(ww-6)+'" height="46" fill="url(#close-sky)"/><path d="M4 43l'+ww*.25+'-16 '+ww*.22+' 12 '+ww*.24+'-19 '+ww*.21+' 21Z" fill="#7c9b88"/><path d="M'+ww*.5+' 3v46M3 26h'+(ww-6)+'" stroke="#e6dec3" stroke-width="2"/>'));
      b.push(line([0,0,c.wall-3],[size.w,0,c.wall-3],'#fff5df',3),line([side,0,c.wall-3],[side,size.h,c.wall-3],'#d4ddc5',3));
      if(!/浴室|厨房|衣帽间|影音室|玄关|楼梯厅/.test(room)){
        b.push(frontArt(14,-.3,64,37,0,44,'S',root.HouseInterior.art(room)));
      }

    }else{
      function railing(x,y,w,d){var arr=[],length=w||d;for(var i=0;i<=length;i+=25){var rx=x+(w?i:0),ry=y+(d?i:0);arr.push(line([rx,ry,0],[rx,ry,50],'#d5ddbd',1.5));}arr.push(line([x,y,50],[x+w,y+d,50],'#e7dfc2',3));return arr.join('');}
      b.push(railing(0,0,size.w,0),railing(size.w,0,0,size.h));
      if(room==='阳台')b.push(box(0,0,128,size.w,6,5,wood),line([0,0,0],[0,0,128],'#b09a76',3),line([size.w,0,0],[size.w,0,128],'#b09a76',3));
      b.push(line([0,size.h*.38,0],[0,size.h*.70,0],'#a5c8bd',5));
    }
    if(rug){
      var trim='<rect x="6" y="6" width="'+(rug[2]-12)+'" height="'+(rug[3]-12)+'" rx="3" fill="none" stroke="#fff7df" stroke-width=".7" stroke-dasharray="2 2"/>';
      for(var fringe=8;fringe<rug[2]-5;fringe+=4)trim+='<path d="M'+fringe+' 0v-3M'+fringe+' '+rug[3]+'v3" stroke="#e8d8b9" stroke-width=".6"/>';
      b.push(topArt(rug[0],rug[1],.3,trim));
    }
    var supported={},roots=[],itemById={};
    items.forEach(function(item){if(item&&item.id)itemById[item.id]=item;});
    fixtures.forEach(function(f){
      var entry={id:f.id,p:[f.x,f.y,f.w,f.d],fixture:f};
      // A countertop sink must paint after its supporting cabinet, just like devices.
      var support=f.type==='sink'&&fixtures.find(function(q){return q.type==='counter'&&f.x>=q.x&&f.y>=q.y&&f.x+f.w<=q.x+q.w&&f.y+f.d<=q.y+q.d&&Math.abs(f.h-q.h)<=2;});
      if(support){entry.meta={inset:true};(supported[support.id]||(supported[support.id]=[])).push(entry);}
      else roots.push(entry);
    });
    items.filter(function(i){return i.room===room;}).forEach(function(item){
      var p=M.plan[item.id];
      if(item.custom_place && item.place && p){
        p=[Math.max(0.05,Math.min(0.95,Number(item.place.x)||0.5))*size.w,
           Math.max(0.05,Math.min(0.95,Number(item.place.y)||0.5))*size.h,
           p[2],p[3],p[4]||0];
      }
      if(!p||item.slot_id){
        if(item.place){
          var px=Math.max(0.05,Math.min(0.95,Number(item.place.x)||0.5))*size.w;
          var py=Math.max(0.05,Math.min(0.95,Number(item.place.y)||0.5))*size.h;
          var fp=root.GoodsSize?GoodsSize.footprint(item):[24,24];
          roots.push({id:item.id,p:[px,py,fp[0]/2,fp[1]/2,0],item:item,type:'decor',meta:{facing:'S',height:18},decor:true});
        }
        return;
      }
      var type=(types[item.id]||[])[4]||'box',m=M.meta(item,type),entry={id:item.id,p:p,item:item,type:type,meta:m};m.id=item.id;
      if(p[4]&&p[4]!=='wall'&&p[4]!=='ceiling'){(supported[p[4]]||(supported[p[4]]=[])).push(entry);}else roots.push(entry);
    });
    function decorArt(entry){
      // Installed goods (furniture slots) sit at their slot height and are sized by kind.
      var pl=entry.item&&entry.item.place||{},gid=String(entry.item&&(entry.item.possession_id||entry.item.id)||''),p=point(entry.p[0],entry.p[1],Math.max(0,Number(pl.z_cm)||0)*.5);
      var sizeMap={rug:58,bath_mat:46,towel:40,curtain:74,lamp:56,plant:40,plant_pot:34,guitar:46,storage_box:32,storage_basket:30,humidifier:28,tablecloth:44,thin_blanket:34,plush_bear:30,tshirt:34,hoodie:36,skirt:34,long_skirt:40,jeans:38,pajamas:36,cardigan:38,coat:44,trench_coat:46,scarf:30,cap:26,beret:26,monitor_arm:30,console:28,speaker:28};
      var size=sizeMap[gid];
      if(size==null&&root.GoodsSize){var fp=GoodsSize.footprint(entry.item||{});size=Math.max(16,Math.min(64,Math.max(fp[0],fp[1])*.55));}
      if(size==null)size=24;
      var art='';
      if(root.ItemArtwork){
        art=root.ItemArtwork.draw(entry.item)||'';
        art=art.replace('class="item-illustration"','class="placed-item-art"');
        art=art.replace('<svg ','<svg x="'+(-size/2)+'" y="'+(-size*0.86)+'" width="'+size+'" height="'+size+'" ');
      }
      if(!art)art='<text x="0" y="0" text-anchor="middle" dominant-baseline="middle" font-size="'+Math.max(12,size*.8)+'">📦</text>';
      return '<g transform="translate('+p[0].toFixed(1)+' '+p[1].toFixed(1)+')"><ellipse cx="0" cy="0" rx="'+(size*.32)+'" ry="'+(size*.13)+'" fill="#24382a26" pointer-events="none"/>'+art+'</g>';
    }
    function renderEntry(entry,z){
      var p=entry.p,body;
      if(entry.decor)body=decorArt(entry);
      else body=entry.fixture?fixtureArt(entry.fixture):object(p,entry.type,entry.meta,z);
      if(entry.item)body='<g class="furniture-hit studio-item" data-id="'+esc(entry.id)+'" data-facing="'+entry.meta.facing+'" data-world="'+p.slice(0,4).join(',')+'" role="button" tabindex="0" aria-label="'+esc(entry.item.name)+'"><title>'+esc(entry.item.name)+(entry.decor?' · 已摆放':'')+'</title>'+body+'</g>';
      else if(entry.fixture&&itemById[entry.id]){var fit=itemById[entry.id];body='<g class="furniture-hit studio-fixture" data-id="'+esc(entry.id)+'" role="button" tabindex="0" aria-label="'+esc(fit.name||entry.id)+'"><title>'+esc(fit.name||entry.id)+'</title>'+body+'</g>';}
      var children=supported[entry.id]||[],height=entry.fixture?entry.fixture.h:entry.meta.height;
      if(entry.type==='bed')height=27;if(entry.type==='rockingchair')height=25;
      children.sort(function(a,b){return a.p[1]-b.p[1];}).forEach(function(ch){body+=renderEntry(ch,ch.meta.inset?0:(z||0)+height);});
      return body;
    }
    roots.sort(function(a,b){var pa=a.p,pb=b.p;return (pa[1]+pa[3])-(pb[1]+pb[3])+(c.a>0?pb[0]-pa[0]:pa[0]-pb[0])*.15;});
    roots.forEach(function(r){var z=r.p[4]==='ceiling'?113:0;b.push(renderEntry(r,z));});
    // A single, physical entrance remains free of floor furniture.
    if(room==='车库')root.SceneStudio.garageBays.forEach(function(g){b.push(line([g.x-58,size.h,.3],[g.x+58,size.h,.3],'#c9cac3',6),line([g.x-58,size.h,1.2],[g.x+58,size.h,1.2],'#8b8e88',1));});
    else if(!open&&!/玄关|楼梯厅/.test(room))b.push(line([size.w*.43,size.h,.3],[size.w*.60,size.h,.3],'#e4d7b6',5),topArt(size.w*.43,size.h-25,.4,'<path d="M0 25V0Q25 0 25 25" fill="none" stroke="#dbcba7" stroke-width="1"/>'));
    if(open)b.push(line([0,size.h,50],[size.w,size.h,50],'#d8dfbc',2));
    // The gym ball is a 3D decor prop; mirror it into the 2D close-up so both views stay in sync.
    if(room==='健身室'&&itemById.gym_ball){
      var gp=point(205,200,2),gr=Math.max(7,16*c.s),gymBall=itemById.gym_ball;
      b.push('<g class="furniture-hit studio-decor" data-id="gym_ball" role="button" tabindex="0" aria-label="'+esc(gymBall.name||'健身球')+'"><title>'+esc(gymBall.name||'健身球')+'</title><ellipse cx="'+gp[0]+'" cy="'+(gp[1]+gr*.72)+'" rx="'+(gr*1.05)+'" ry="'+(gr*.28)+'" fill="#24382a26" pointer-events="none"/><circle cx="'+gp[0]+'" cy="'+gp[1]+'" r="'+gr+'" fill="#c8abc2" stroke="#a887a1" stroke-width="1"/><path d="M'+(gp[0]-gr*.7)+' '+gp[1]+'q'+gr*.7+' '+(-gr*.6)+' '+(gr*1.4)+' 0" fill="none" stroke="#e9d7e4" stroke-width="1.2"/><path d="M'+gp[0]+' '+(gp[1]-gr*.75)+'q'+(gr*.5)+' '+gr*.75+' 0 '+(gr*1.4)+'" fill="none" stroke="#b292aa" stroke-width="1"/></g>');
    }
    // 1F garage close-up: back-wall workshop, floor markings, and the parked cars projected from their real side profiles
    // (nose-in, tails toward the viewer). Cars and props are drawn far-to-near so the oblique view layers correctly.
    if(room==='车库'&&root.SceneStudio&&root.SceneStudio.garageBays){var SS=root.SceneStudio,G=[];
      function pts(list){return list.map(function(p){return point(p[0],p[1],p[2]).map(function(v){return v.toFixed(1);}).join(',');}).join(' ');}
      function poly(list,fill,extra){return '<polygon points="'+pts(list)+'" fill="'+fill+'" '+(extra||'')+'/>';}
      function area(list){var a=0,q=list.map(function(p){return point(p[0],p[1],p[2]);});for(var i=0;i<q.length;i++){var n=q[(i+1)%q.length];a+=q[i][0]*n[1]-n[0]*q[i][1];}return a;}
      function shadeOf(hex,k){var n=parseInt(hex.slice(1),16),r=n>>16,g=n>>8&255,bb=n&255;function f(v){return Math.max(0,Math.min(255,Math.round(k<0?v*(1+k):v+(255-v)*k)));}return '#'+((1<<24)|(f(r)<<16)|(f(g)<<8)|f(bb)).toString(16).slice(1);}
      function ring(cx,cy,cz,r,n,plane){var out=[];for(var i=0;i<n;i++){var a=i/n*Math.PI*2;out.push(plane==='x'?[cx,cy+Math.cos(a)*r,cz+Math.sin(a)*r]:[cx+Math.cos(a)*r,cy,cz+Math.sin(a)*r]);}return out;}
      // ---- back wall (y=0): pegboard + workbench, bumper guards, EV charger, tyre rack, clock; left wall (x=0): cabinet, bike
      var wall=[];
      wall.push(poly([[64,0,58],[138,0,58],[138,0,108],[64,0,108]],'#c9b08a','stroke="#a68d68" stroke-width=".6"'));
      for(var px=0;px<9;px++)for(var py=0;py<6;py++)wall.push(poly([[68+px*8,0,62+py*8],[69.4+px*8,0,62+py*8],[69.4+px*8,0,63.4+py*8],[68+px*8,0,63.4+py*8]],'#8a7458'));
      [['#c8564a',22],['#5f7e9b',30],['#e8c34a',18],['#3b3d42',26]].forEach(function(t,i){var x=76+i*15;wall.push(poly([[x,0.3,100],[x+2,0.3,100],[x+2,0.3,100-t[1]],[x,0.3,100-t[1]]],'#9ea5aa'),poly([[x-2,0.3,100-t[1]],[x+4,0.3,100-t[1]],[x+4,0.3,92-t[1]],[x-2,0.3,92-t[1]]],t[0]));});
      SS.garageBays.forEach(function(g){wall.push(poly([[g.x-28,0.3,20],[g.x+28,0.3,20],[g.x+28,0.3,30],[g.x-28,0.3,30]],'#e8c34a'));for(var z2=0;z2<4;z2++)wall.push(poly([[g.x-24+z2*14,0.5,20],[g.x-18+z2*14,0.5,20],[g.x-12+z2*14,0.5,30],[g.x-18+z2*14,0.5,30]],'#26282b'));});
      wall.push(poly([[212,0.3,46],[228,0.3,46],[228,0.3,68],[212,0.3,68]],'#f3eee6','stroke="#b9b4aa" stroke-width=".6"'),poly([[215,0.5,62],[225,0.5,62],[225,0.5,65],[215,0.5,65]],'#7fbf7f'));
      var ck=point(300,0.3,112);wall.push('<circle cx="'+ck[0].toFixed(1)+'" cy="'+ck[1].toFixed(1)+'" r="'+(8*c.s).toFixed(1)+'" fill="#f6f2e8" stroke="#3b3d42" stroke-width="'+(1.4*c.s).toFixed(1)+'"/>');
      wall.push(poly([[338,0.3,64],[392,0.3,64],[392,0.3,66],[338,0.3,66]],'#8f969b'),poly([[338,0.3,92],[392,0.3,92],[392,0.3,94],[338,0.3,94]],'#8f969b'));
      for(var ti=0;ti<4;ti++){var tc=point(345+ti*13,4,79);wall.push('<ellipse cx="'+tc[0].toFixed(1)+'" cy="'+tc[1].toFixed(1)+'" rx="'+(6.5*c.s).toFixed(1)+'" ry="'+(14*c.s).toFixed(1)+'" fill="#26282b" stroke="#3f4245" stroke-width="'+(1.2*c.s).toFixed(1)+'"/>');}
      wall.push(poly([[0,140,46],[0,190,46],[0,190,80],[0,140,80]],'#d9d4cc','stroke="#a9a49b" stroke-width=".6"'),line([0.5,165,47],[0.5,165,79],'#a9a49b',1));
      var bkc=[[0.6,250,46],[0.6,286,46]];bkc.forEach(function(q){wall.push(poly(ring(q[0],q[1],q[2],15,18,'x'),'none','stroke="#3b3d42" stroke-width="'+(2*c.s).toFixed(1)+'"'));});wall.push(line([0.6,250,46],[0.6,268,56],'#7d8f78',2),line([0.6,268,56],[0.6,286,46],'#7d8f78',2),line([0.6,256,58],[0.6,276,58],'#7d8f78',2));
      b.push('<g class="garage-walls" pointer-events="none">'+wall.join('')+'</g>');
      // ---- floor: bay lines, painted numbers, wheel stops, drip trays, drain, roll-up door tracks at the front edge
      var fl=[];[25,155,285,415].forEach(function(x){fl.push(poly([[x-1.6,70,.2],[x+1.6,70,.2],[x+1.6,size.h-18,.2],[x-1.6,size.h-18,.2]],'#e3c24f'));});
      SS.garageBays.forEach(function(g,i){fl.push(topArt(g.x-12,size.h-46,.3,'<text x="12" y="16" font-size="17" font-weight="700" text-anchor="middle" fill="#e3c24f" opacity=".85">A'+(i+1)+'</text>'));
        if(!SS.garageOut(g.home?'sedan':g.type))fl.push(poly([[g.x-18,48,.3],[g.x+18,48,.3],[g.x+18,70,.3],[g.x-18,70,.3]],'#3a3c40'));});
      fl.push(poly([[160,size.h-14,.3],[280,size.h-14,.3],[280,size.h-8,.3],[160,size.h-8,.3]],'#4a4d52'));
      SS.garageBays.forEach(function(g){fl.push(poly([[g.x-60,size.h-2,.2],[g.x+60,size.h-2,.2],[g.x+60,size.h,.2],[g.x-60,size.h,.2]],'#8b8e88'));});
      b.push('<g class="garage-floor" pointer-events="none">'+fl.join('')+'</g>');
      // workbench (free-standing, against the back wall) with legs, drawers and a vice
      b.push(box(70,2,40,62,28,4,wood,top),box(72,4,0,3,3,40,'#7d858a'),box(129,4,0,3,3,40,'#7d858a'),box(72,24,0,3,3,40,'#7d858a'),box(129,24,0,3,3,40,'#7d858a'),box(76,6,10,52,22,2,'#8f969b'),box(76,8,44,16,12,8,'#c8564a'),box(98,9,44,14,10,5,'#5f7e9b'),box(118,8,44,8,10,7,'#4a6b5a'));
      // car profiles: [t along length (0 = nose, north), z in metres]; window polygon; wheel radius; wheel t positions
      var PROF={
        sedan:{top:[[0,.34],[0,.62],[.04,.72],[.30,.82],[.37,.86],[.47,1.34],[.69,1.36],[.79,.9],[.95,.86],[1,.76],[1,.34]],win:[[.385,.9],[.475,1.28],[.68,1.3],[.765,.92]],R:.33,wh:[.2,.8],sill:.3},
        jeep:{top:[[0,.46],[0,1.0],[.03,1.06],[.24,1.06],[.27,1.82],[.98,1.84],[1,1.78],[1,.46]],win:[[.29,1.12],[.31,1.74],[.96,1.76],[.96,1.12]],R:.4,wh:[.2,.8],sill:.42},
        sports:{top:[[0,.27],[0,.5],[.05,.58],[.34,.74],[.46,1.12],[.6,1.14],[.84,.86],[1,.8],[1,.27]],win:[[.47,.82],[.5,1.06],[.6,1.08],[.72,.86]],R:.33,wh:[.2,.8],sill:.26}};
      SS.garageBays.slice().sort(function(p,q){return c.a>0?q.x-p.x:p.x-q.x;}).forEach(function(g){
        var cx=g.x,cy=187,L=220,Wd=92,x0=cx-Wd/2,x1=cx+Wd/2,y0=cy-L/2,pr=PROF[g.type]||PROF.sedan,paint=g.paint,J=g.type==='jeep',Sp=g.type==='sports';
        if(SS.garageOut(g.home?'sedan':g.type)){b.push(poly([[cx-24,cy+70,.3],[cx+24,cy+70,.3],[cx+28,cy+40,.3],[cx-28,cy+40,.3]],'#3c3a38','opacity=".3"'),poly([[x0+8,cy-30,.3],[x0+18,cy-30,.3],[x0+18,cy+90,.3],[x0+8,cy+90,.3]],'#2b2b2b','opacity=".08"'),poly([[x1-18,cy-30,.3],[x1-8,cy-30,.3],[x1-8,cy+90,.3],[x1-18,cy+90,.3]],'#2b2b2b','opacity=".08"'));return;}
        var NOSE_OUT=true,sg=NOSE_OUT?-1:1,Y=function(t){return NOSE_OUT?y0+(1-t)*L:y0+t*L;},Z=function(m){return m*50;},R=pr.R*50,out=['<g class="garage-car-hit" data-car="'+(g.home?'home':g.type)+'" role="button" tabindex="0" aria-label="'+esc(g.label)+'"><title>'+esc(g.label+(g.home?' · 点击打开车库':''))+'</title>'];
        out.push(poly([[x0-4,y0+6,0],[x1+6,y0+6,0],[x1+6,y0+L+4,0],[x0-4,y0+L+4,0]],'#1f2624','opacity=".22"'));
        // wheels on the visible (left) side, drawn before the body so the arches frame them
        pr.wh.forEach(function(t){var w=ring(x0-1,Y(t),R,R,18,'x');out.push(poly(w,'#1f2826'),poly(ring(x0-1.6,Y(t),R,R*.62,14,'x'),'#c8d2cc'),poly(ring(x0-1.8,Y(t),R,R*.22,10,'x'),'#5e6f68'));});
        // closed profile: nose-bottom -> top line -> tail-bottom -> bottom edge (with wheel arches) back to the nose
        var topL=pr.top.map(function(p){return [Y(p[0]),Z(p[1])];}),bottom=[];var sill=Z(pr.sill);
        bottom.push([Y(1),sill]);pr.wh.slice().reverse().forEach(function(t){var yc=Y(t),ar=R+5;bottom.push([yc+sg*ar,sill]);for(var k2=0;k2<=8;k2++){var a=k2/8*Math.PI;bottom.push([yc+sg*Math.cos(a)*ar,sill+Math.sin(a)*(ar-sill+R)*.85]);}bottom.push([yc-sg*ar,sill]);});bottom.push([Y(0),sill]);
        var side=topL.concat(bottom).map(function(p){return [x0,p[0],p[1]];});
        // top / tail facets (with back-face culling), far to near; glass where the profile is greenhouse
        var facets=[];for(var i=0;i<topL.length-1;i++){var p0=topL[i],p1=topL[i+1],q=[[x0,p0[0],p0[1]],[x1,p0[0],p0[1]],[x1,p1[0],p1[1]],[x0,p1[0],p1[1]]];facets.push({q:q,i:i,dz:p1[1]-p0[1],dy:p1[0]-p0[0]});}
        var roofI=facets.reduce(function(best,f){return Math.abs(f.dz)<1&&f.q[0][2]>(best?best.q[0][2]:-1)?f:best;},null),sign=roofI?Math.sign(area(roofI.q)):1;
        facets.forEach(function(f){if(Math.sign(area(f.q))!==sign)return;var steep=Math.abs(f.dz)>Math.abs(f.dy)*.5,isTail=f.i===topL.length-2,isGlass=!isTail&&steep&&f.q[0][2]>Z(pr.win[0][1])-6&&f.dz<0,col=isGlass?'#4f6c78':isTail?shadeOf(paint,-.12):f===roofI?shadeOf(paint,.12):paint;
          out.push(poly(f.q,col,'stroke="'+shadeOf(paint,-.4)+'" stroke-width=".4"'));});
        out.push(poly(side,shadeOf(paint,-.1),'stroke="'+shadeOf(paint,-.45)+'" stroke-width=".6"'));
        // side glass with B pillar, beltline highlight, door seams, handles, mirror
        var wn=pr.win.map(function(p){return [x0-.3,Y(p[0]),Z(p[1])];}),mid=(pr.win[1][0]+pr.win[2][0])/2;
        out.push(poly(wn,'#55707c','stroke="#2f3a3d" stroke-width=".5"'),line([x0-.4,Y(mid),Z(pr.win[0][1])],[x0-.4,Y(mid),Z(pr.win[1][1])],shadeOf(paint,-.2),3*c.s+1));
        out.push(line([x0-.4,Y(.06),Z(pr.win[0][1])-3],[x0-.4,Y(.94),Z(pr.win[0][1])-3],shadeOf(paint,.35),1.2));
        if(!Sp)out.push(line([x0-.4,Y(pr.win[0][0]),Z(pr.win[0][1])],[x0-.4,Y(pr.win[0][0]),sill+2],shadeOf(paint,-.45),.7));
        out.push(line([x0-.4,Y(mid),Z(pr.win[0][1])],[x0-.4,Y(mid),sill+2],shadeOf(paint,-.45),.7),line([x0-.4,Y(pr.win[3][0]),Z(pr.win[3][1])],[x0-.4,Y(pr.win[3][0]+.02),sill+2],shadeOf(paint,-.45),.7));
        [mid-.07,mid+.11].forEach(function(t){out.push(line([x0-.6,Y(t),Z(pr.win[0][1])-6],[x0-.6,Y(t)+7,Z(pr.win[0][1])-6],shadeOf(paint,.55),1.8));});
        out.push(poly([[x0-7,Y(pr.win[0][0])-2,Z(pr.win[0][1])+2],[x0,Y(pr.win[0][0])-2,Z(pr.win[0][1])+2],[x0,Y(pr.win[0][0])+6,Z(pr.win[0][1])+6],[x0-7,Y(pr.win[0][0])+6,Z(pr.win[0][1])+6]],paint,'stroke="'+shadeOf(paint,-.45)+'" stroke-width=".4"'));
        // tail face details: lights, plate, bumper; jeep spare tyre and roof rack; sports wing and stripes
        if(NOSE_OUT){var N0=Y(0)+.4,nz=Z(pr.top[1][1])-7,gl=J?'#2b302e':shadeOf(paint,-.35);
          out.push(poly([[x0+4,N0,nz],[x0+18,N0,nz],[x0+18,N0,nz+5],[x0+4,N0,nz+5]],'#f4efd8','stroke="#8d8a7a" stroke-width=".4"'),poly([[x1-18,N0,nz],[x1-4,N0,nz],[x1-4,N0,nz+5],[x1-18,N0,nz+5]],'#f4efd8','stroke="#8d8a7a" stroke-width=".4"'));
          out.push(poly([[cx-16,N0,nz-1],[cx+16,N0,nz-1],[cx+16,N0,nz+5],[cx-16,N0,nz+5]],gl));for(var gs=0;gs<5;gs++)out.push(line([cx-14+gs*7,N0+.1,nz],[cx-14+gs*7,N0+.1,nz+4],J?'#56604f':shadeOf(paint,-.55),.8));
          out.push(poly([[cx-14,N0,sill+4],[cx+14,N0,sill+4],[cx+14,N0,sill+11],[cx-14,N0,sill+11]],'#2f5fa8','stroke="#f3f3f3" stroke-width=".6"'),poly([[x0+1,N0+.2,sill-2],[x1-1,N0+.2,sill-2],[x1-1,N0+.2,sill+3],[x0+1,N0+.2,sill+3]],'#2b302e'));
          if(J)[x0+8,x1-8].forEach(function(hx){out.push(poly(ring(hx,N0+.3,nz+2.5,3.2,12,'y'),'#f4efd8'));});
          if(Sp)[[-9,-4],[4,9]].forEach(function(o){out.push(poly([[cx+o[0],Y(.02),Z(.56)],[cx+o[1],Y(.02),Z(.56)],[cx+o[1],Y(.3),Z(.72)],[cx+o[0],Y(.3),Z(.72)]],'#f6f4ee'));});}
        var T0=Y(1)+.4,tz=Z(pr.top[pr.top.length-2][1])-8;if(!NOSE_OUT){
        out.push(poly([[x0+4,T0,tz],[x0+20,T0,tz],[x0+20,T0,tz+5],[x0+4,T0,tz+5]],'#c4544a'),poly([[x1-20,T0,tz],[x1-4,T0,tz],[x1-4,T0,tz+5],[x1-20,T0,tz+5]],'#c4544a'),poly([[x0+4,T0,tz-3],[x0+10,T0,tz-3],[x0+10,T0,tz],[x0+4,T0,tz]],'#f0a640'),poly([[x1-10,T0,tz-3],[x1-4,T0,tz-3],[x1-4,T0,tz],[x1-10,T0,tz]],'#f0a640'));
        out.push(poly([[cx-14,T0,sill+6],[cx+14,T0,sill+6],[cx+14,T0,sill+13],[cx-14,T0,sill+13]],'#2f5fa8','stroke="#f3f3f3" stroke-width=".6"'),poly([[x0+1,T0+.2,sill-2],[x1-1,T0+.2,sill-2],[x1-1,T0+.2,sill+4],[x0+1,T0+.2,sill+4]],'#2b302e'));}
        if(J){if(!NOSE_OUT)out.push(poly(ring(cx,T0+5,Z(1.0),18,20,'y'),'#202826'),poly(ring(cx,T0+5.4,Z(1.0),9,16,'y'),'#56604f'));for(var rk=0;rk<4;rk++){var ry=Y(.32+rk*.2);out.push(line([x0+6,ry,Z(1.9)],[x1-6,ry,Z(1.9)],'#2b302e',1.6));}out.push(line([x0+6,Y(.3),Z(1.9)],[x0+6,Y(.95),Z(1.9)],'#2b302e',1.6),line([x1-6,Y(.3),Z(1.9)],[x1-6,Y(.95),Z(1.9)],'#2b302e',1.6));}
        if(Sp){[[-9,-4],[4,9]].forEach(function(o){out.push(poly([[cx+o[0],Y(.04),Z(.6)],[cx+o[1],Y(.04),Z(.6)],[cx+o[1],Y(.34),Z(.76)],[cx+o[0],Y(.34),Z(.76)]],'#f6f4ee'),poly([[cx+o[0],Y(.47),Z(1.15)],[cx+o[1],Y(.47),Z(1.15)],[cx+o[1],Y(.6),Z(1.16)],[cx+o[0],Y(.6),Z(1.16)]],'#f6f4ee'));});
          out.push(line([x0+10,Y(.94),Z(.82)],[x0+10,Y(.94),Z(1.0)],'#26282b',1.6),line([x1-10,Y(.94),Z(.82)],[x1-10,Y(.94),Z(1.0)],'#26282b',1.6),poly([[x0+2,Y(.9),Z(1.0)],[x1-2,Y(.9),Z(1.0)],[x1-2,Y(.98),Z(1.03)],[x0+2,Y(.98),Z(1.03)]],shadeOf(paint,-.15),'stroke="#26282b" stroke-width=".5"'));}
        out.push('</g>');b.push(out.join(''));});
      // free-standing shelving and the red tool chest by the right wall (in front of the cars on the right)
      var rk=size.w-28;[[rk,150],[rk+21,150],[rk,237],[rk+21,237]].forEach(function(q){b.push(box(q[0],q[1],0,3,3,96,'#7d858a'));});for(var lv=0;lv<4;lv++){b.push(box(rk,150,6+lv*28,24,90,2,'#9aa1a6'));[[154,18,'#c9a87a'],[184,22,'#d6c3a0'],[214,16,'#5f7e9b']].forEach(function(o,oi){if((lv+oi)%3!==2)b.push(box(rk+3,o[0],8+lv*28,18,o[1],10+((lv+oi)%2)*5,o[2]));});}
      b.push(box(size.w-28,262,0,24,34,46,'#c8564a'),box(size.w-27,264,46,22,30,2,'#8f969b'));}
    var a=M.anchors[room],char=point(a[0],a[1],0),ch=80*c.s,cw=ch*.73,look=appearance||{},src=look.src||'assets/character_daily.png';
    b.push('<g transform="translate('+char[0]+' '+char[1]+')"><ellipse cx="0" cy="0" rx="'+(cw*.22)+'" ry="'+(2*c.s)+'" fill="#24382a22" pointer-events="none"/><image class="projected-character" data-appearance="'+esc(look.key||'daily')+'" href="'+esc(src)+'" onerror="this.setAttribute(\'href\',\'assets/character_daily.png\')" x="'+(-cw/2)+'" y="'+(-ch)+'" width="'+cw+'" height="'+ch+'" preserveAspectRatio="xMidYMax meet" pointer-events="none"/></g>');
    if(e.dark)b.push('<rect width="600" height="440" fill="#142a3c" opacity=".22" pointer-events="none"/>');
    if(e.dark&&!open)items.filter(function(i){return i.room===room&&/^(floor_lamp|bedside_lamp)$/.test(i.id);}).forEach(function(i){var p=M.plan[i.id],m=M.meta(i,types[i.id][4]),q=point(p[0]+p[2]/2,p[1]+p[3]/2,m.height+(p[4]?28:0));b.push('<ellipse cx="'+q[0]+'" cy="'+q[1]+'" rx="'+(62*c.s)+'" ry="'+(52*c.s)+'" fill="url(#close-warm)" opacity=".65" pointer-events="none"/>');});
    return {artwork:b.join(''),camera:c};
  }
  root.RoomPerspective={camera:camera,draw:draw};
})(typeof window==='undefined'?globalThis:window);
