/* Soft upholstery and joinery drawn in the existing physical furniture footprints. */
(function(root){
  'use strict';
  function rect(x,y,w,h,r,fill,extra){return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+r+'" fill="'+fill+'" '+(extra||'')+'/>';}
  function draw(p,type,m,z,a){
    if(!/^(cabinet|jewelry|bookshelf|tub|sink|chair|sofa|rockingchair|bed|table|dining|desk)$/.test(type))return null;
    var x=p[0],y=p[1],w=p[2],d=p[3],h=m.height,f=m.facing||'S',out=[],wood='url(#close-wood)',top='url(#close-woodTop)';
    z=z||0;
    function rounded(x,y,z,w,d,h,r,color){
      r=Math.min(r,w/2,d/2);
      var points=[],centers=[[x+w-r,y+r,-90],[x+w-r,y+d-r,0],[x+r,y+d-r,90],[x+r,y+r,180]];
      centers.forEach(function(v){for(var j=0;j<=6;j++){var angle=(v[2]+j*15)*Math.PI/180;points.push([v[0]+r*Math.cos(angle),v[1]+r*Math.sin(angle)]);}});
      var faces=[];
      points.forEach(function(q,i){var n=points[(i+1)%points.length],nx=n[1]-q[1],ny=q[0]-n[0];
        if(ny-(a.camera.a>0?1:-1)*nx*.6>0){var shade=.84+.12*Math.max(0,ny/Math.max(.01,Math.hypot(nx,ny)));faces.push(a.polygon([[q[0],q[1],z],[n[0],n[1],z],[n[0],n[1],z+h],[q[0],q[1],z+h]],color,'style="filter:brightness('+shade+')"'));}
      });
      return faces.join('')+a.top(x,y,z+h,rect(0,0,w,d,r,color,'stroke="#fff6e4" stroke-opacity=".55" stroke-width=".5"'));
    }
    function local(u,v){if(f==='N')return [x+w-u,y+d-v];if(f==='E')return [x+v,y+d-u];if(f==='W')return [x+w-v,y+u];return [x+u,y+v];}
    function localTop(u,v,z,markup){var q=local(u,v),b=local(u+1,v),c=local(u,v+1),o=a.point(q[0],q[1],z),i=a.point(b[0],b[1],z),j=a.point(c[0],c[1],z);return '<g transform="matrix('+(i[0]-o[0])+' '+(i[1]-o[1])+' '+(j[0]-o[0])+' '+(j[1]-o[1])+' '+o[0]+' '+o[1]+')">'+markup+'</g>';}
    function localRound(u,v,z,b,c,t,r,color){var q=local(u,v),end=local(u+b,v+c);return rounded(Math.min(q[0],end[0]),Math.min(q[1],end[1]),z,Math.abs(end[0]-q[0]),Math.abs(end[1]-q[1]),t,r,color);}
    function woven(u,v,z,b,c,r){return localTop(u,v,z,rect(0,0,b,c,r,'url(#close-weave)','opacity=".75"'));}
    function seam(u,v,z,b,c,r){return localTop(u,v,z,rect(0,0,b,c,r,'none','stroke="#fff7e8" stroke-width=".65" stroke-dasharray="1.6 1.2"'));}
    if(/^(cabinet|jewelry|bookshelf)$/.test(type)){
      var fw=/E|W/.test(f)?d:w,feet=m.id==='storage_bench'?3:6,face=[];
      [[3,3],[w-6,3],[3,d-6],[w-6,d-6]].forEach(function(q){out.push(a.box(x+q[0],y+q[1],z,3,3,feet,wood));});
      out.push(rounded(x,y,z+feet,w,d,h-feet,1.8,'#b99e7e'));
      out.push(a.top(x+1,y+1,z+h+.02,rect(0,0,w-2,d-2,1,'url(#close-grain)','opacity=".3"')));
      // Recessed joinery on the camera-facing side stays inside the existing footprint.
      var sideFace=a.camera.a>0?'W':'E';
      if(d>18&&h-feet>24&&sideFace!==f){
        var sh=h-feet-10;
        out.push(a.front(x,y,z+feet+4,w,d,sh,sideFace,rect(3,0,d-6,sh,1.5,'#b39b7d','stroke="#e9d8bd" stroke-width=".6"')+rect(6,3,d-12,sh-6,1,'#c6af8e')+rect(7,4,d-14,sh-8,.7,'url(#close-grain)','opacity=".38"')));
      }
      out.push(a.top(x,y,z+h+.06,rect(1.5,1.5,w-3,d-3,1,'none','stroke="#eedcc0" stroke-width=".65"')));
      if(type==='bookshelf'){
        var rows=4,sh=(h-feet-8)/rows;
        face.push(rect(3,3,fw-6,h-feet-6,1,'#817566'));
        for(var shelf=0;shelf<rows;shelf++){
          var sy=5+shelf*sh;
          face.push(rect(5,sy,fw-10,sh-3,1,'#aaa18a'));
          var colors=['#9eb3a1','#c0a1ac','#b6bf94','#cdb38c','#8da7ab'];
          for(var bi=0,bx=8;bx<fw-10;bi++,bx+=7){
            var bh=sh*(.58+(bi+shelf)%3*.08);
            if(shelf===2&&bi>3){
              if(bi===4)face.push(rect(bx,sy+sh-9,Math.min(24,fw-bx-7),5,1,'#d9c9ac'),rect(bx+1,sy+sh-13,Math.min(21,fw-bx-8),4,1,'#a9b7a5'));
              continue;
            }
            face.push(rect(bx,sy+sh-bh-4,5,bh,.8,colors[(bi+shelf)%5]),'<path d="M'+(bx+1)+' '+(sy+sh-bh-1)+'h3m-3 '+(bh-7)+'h3" stroke="#f2e6cf" stroke-width=".7"/>');
          }
          face.push(rect(3,sy+sh-3,fw-6,2.5,.4,'#d8bea0'),'<path d="M5 '+(sy+sh)+'h'+(fw-10)+'" stroke="#736756" stroke-width=".7"/>');
        }
      }else{
        var tall=h>75,rows=type==='jewelry'?3:1,cols=2,gap=3,pw=(fw-9)/cols,ph=(h-feet-8)/rows;
        face.push(rect(2,2,fw-4,h-feet-4,1,'#9b856d'));
        for(var row=0;row<rows;row++)for(var col=0;col<cols;col++){
          var dx=3+col*(pw+gap),dy=3+row*ph;
          face.push(rect(dx,dy,pw,ph-2,1.4,tall?'#d0b99b':'#c4b194','stroke="#ebddc4" stroke-width=".6"'));
          face.push(rect(dx+3,dy+3,pw-6,ph-8,1,'#bba58a','stroke="#b09a80" stroke-width=".5"'));
          face.push(rect(dx+4,dy+4,pw-8,ph-10,.7,'url(#close-grain)','opacity=".28"'));
          if(tall){
            for(var slat=dx+7;slat<dx+pw-5;slat+=4)face.push('<path d="M'+slat+' '+(dy+7)+'v'+(ph-16)+'" stroke="#e8d6b8" stroke-opacity=".48" stroke-width=".55"/>');
          }
          var hx=col===0?dx+pw-6:dx+5,hy=dy+ph*.46;
          face.push(rect(hx-.8,hy-.7,2.7,tall?16:6,1,'#8e826b'),rect(hx,hy,1.2,tall?14:4.5,.5,'#f2d8a3'));
        }
      }
      out.push(a.front(x,y,z+feet,w,d,h-feet,f,face.join('')));
      out.push(a.front(x,y,z+feet,w,d,2,f,rect(1,0,fw-2,1.4,.3,'#e7d5b7')));
    }else if(type==='tub'){
      // A curved freestanding shell, with a recessed water surface and a ceramic rim.
      out.push(a.top(x,y,z+.1,'<ellipse cx="'+w*.5+'" cy="'+d*.57+'" rx="'+w*.47+'" ry="'+d*.43+'" fill="#48695c23"/>'));
      out.push(rounded(x+3,y+2,z+3,w-6,d-4,h-3,d*.38,'#cbdcd2'));
      out.push(rounded(x,y,z+h-3,w,d,3,d*.43,'#f1f1de'));
      var iw=w-10,ih=d-10,r=Math.min(ih*.45,15);
      out.push(a.top(x+5,y+5,z+h+.05,rect(0,0,iw,ih,r,'#9db8b0')+rect(2,2,iw-4,ih-4,r-1,'#d3e0d5')+rect(4,4,iw-8,ih-8,r-2,'#86aeb0')));
      out.push(a.top(x+10,y+10,z+h+.1,'<path d="M2 '+d*.22+'q'+w*.17+'-5 '+w*.33+' 0t'+w*.32+' 0" fill="none" stroke="#d7ece2" stroke-width=".75" opacity=".7"/><ellipse cx="'+w*.33+'" cy="'+d*.25+'" rx="'+w*.22+'" ry="'+d*.13+'" fill="#d7eee224"/>'));
      var fx=x+w*.83,fy=y+5;
      out.push(a.line([fx,fy,z+h],[fx,fy,z+h+9],'#789b94',2.4),a.line([fx,fy,z+h+9],[fx-9,fy,z+h+9],'#e4ebd7',2.4),a.line([fx-9,fy,z+h+9],[fx-9,fy+4,z+h+7],'#b9d0c1',2.4));
    }else if(type==='sink'){
      var sw=w,sd=d;
      out.push(a.top(x,y,z+h,rect(0,0,sw,sd,5,'#eef0de','stroke="#b8cbbc" stroke-width=".7"')+rect(3,3,sw-6,sd-6,4,'#a4bdb2')+rect(5,5,sw-10,sd-10,3,'#d1dfd2')+'<ellipse cx="'+sw*.5+'" cy="'+sd*.58+'" rx="2" ry="1.5" fill="#78988b"/><path d="M7 7v'+(sd-15)+'" stroke="#f2f7e6" stroke-width="1"/>'));
      var fx=x+sw*.5,fy=y+3;
      out.push(a.line([fx,fy,z+h],[fx,fy,z+h+10],'#91aca0',2),a.line([fx,fy,z+h+10],[fx,fy+9,z+h+10],'#dce6d1',2),a.line([fx,fy+9,z+h+10],[fx,fy+9,z+h+7],'#b3c9b8',2));
      out.push(a.line([fx+5,fy,z+h+2],[fx+9,fy,z+h+3],'#a6bcab',1.5));
    }else if(type==='chair'){
      var L=/E|W/.test(f)?d:w,D=/E|W/.test(f)?w:d;
      [[2,3],[L-5,3],[2,D-5],[L-5,D-5]].forEach(function(q){out.push(localRound(q[0],q[1],z,3,3,21,.8,wood));});
      out.push(localRound(0,1,z+19,L,D-1,3,2,wood));
      out.push(localRound(1,3,z+22,L-2,D-4,3.2,3,'#a8bba0'));
      out.push(woven(1,3,z+25.25,L-2,D-4,3),seam(3,5,z+25.3,L-6,D-8,2));
      out.push(localRound(1,0,z+21,2.4,3,h-21,1,wood),localRound(L-3.4,0,z+21,2.4,3,h-21,1,wood));
      out.push(localRound(1,0,z+29,L-2,4,Math.max(5,h-29),1.8,'#b8a9ba'));
    }else if(type==='sofa'||type==='rockingchair'){
      var L=/E|W/.test(f)?d:w,D=/E|W/.test(f)?w:d,seatZ=19,parts=[];
      [[5,6],[L-9,6],[5,D-9],[L-9,D-9]].forEach(function(q){out.push(localRound(q[0],q[1],z,4,4,8,1.2,wood));});
      out.push(localRound(1,1,z+7,L-2,D-2,12,5,'#b1a0ad'));
      var n=type==='rockingchair'?1:L>110?3:2,cw=(L-16)/n;
      parts.push({u:1,v:0,w:L-2,d:9,z:seatZ,h:Math.max(12,h-seatZ),color:'#baa9ba',r:4});
      for(var i=0;i<n;i++)parts.push({u:8+i*cw,v:10,w:cw-1.4,d:D-13,z:seatZ,h:7,color:'#a9bda1',r:4,stitch:true});
      parts.push({u:0,v:7,w:7,d:D-7,z:seatZ,h:14,color:'#c2afbe',r:3.3},{u:L-7,v:7,w:7,d:D-7,z:seatZ,h:14,color:'#c2afbe',r:3.3});
      parts.sort(function(q,r){var q1=local(q.u+q.w/2,q.v+q.d/2),r1=local(r.u+r.w/2,r.v+r.d/2);return q1[1]-r1[1]+(a.camera.a>0?r1[0]-q1[0]:q1[0]-r1[0])*.3;});
      parts.forEach(function(q){out.push(localRound(q.u,q.v,z+q.z,q.w,q.d,q.h,q.r,q.color));if(q.stitch)out.push(woven(q.u,q.v,z+q.z+q.h+.02,q.w,q.d,4),seam(q.u+2,q.v+2,z+q.z+q.h+.03,q.w-4,q.d-4,3));});
      var pw=Math.min(21,L*.23),pd=Math.min(17,D*.36);
      [[10,'#f0e4c7'],[L-pw-11,'#cbaebb']].forEach(function(q){out.push(localRound(q[0],12,z+26,pw,pd,6,4,q[1]),woven(q[0],12,z+32.05,pw,pd,4),seam(q[0]+2,14,z+32.1,pw-4,pd-4,3));out.push(localTop(q[0]+pw/2,12+pd/2,z+32.15,'<path d="M-5-3Q0 3 5-3M-5 3Q0-3 5 3" fill="none" stroke="#fff4e2" stroke-opacity=".65" stroke-width=".7"/>'));});
      if(n>1){var bw=cw*.4,bx=L*.47;out.push(localTop(bx,D*.44,z+26.2,rect(0,0,bw,D*.5,2,'#ddd0b5')));for(var t=2;t<bw;t+=3)out.push(localTop(bx+t,D*.44,z+26.3,'<path d="M0 1v'+(D*.5-2)+'" stroke="#f6edda" stroke-width=".7"/>'));out.push(woven(bx,D*.44,z+26.35,bw,D*.5,2));for(var edge=2;edge<bw;edge+=3)out.push(localTop(bx+edge,D*.94,z+26.3,'<path d="M0 0l1 2" stroke="#eee1c7" stroke-width=".7"/>'));}
    }else if(type==='bed'){
      out.push(rounded(x,y,z,w,6,44,2,wood));
      out.push(a.front(x+4,y,z+23,w-8,6,17,'S',rect(0,0,w-8,17,4,'#c7b7be','stroke="#eee3d5" stroke-width=".6"')+rect(2,2,w-12,13,3,'none','stroke="#f5e8df" stroke-width=".55" stroke-dasharray="1.3 1.2"')));
      var tufts='';for(var button=12;button<w-12;button+=18)tufts+='<path d="M'+(button-5)+' 5l5 3 5-3m-10 6 5-3 5 3" fill="none" stroke="#b39dad" stroke-opacity=".4" stroke-width=".5"/><circle cx="'+button+'" cy="8" r=".85" fill="#eee0d8"/>';
      out.push(a.front(x+4,y,z+23,w-8,6,17,'S',tufts));
      [[7,8],[w-11,8],[7,d-11],[w-11,d-11]].forEach(function(q){out.push(rounded(x+q[0],y+q[1],z,4,4,7,1,wood));});
      out.push(rounded(x,y+4,z+5,w,d-4,14,4,wood),rounded(x+2,y+7,z+19,w-4,d-9,5,6,'#f0ebda'));
      for(var j=0;j<2;j++){
        var px=x+8+j*(w-14)/2,pw=(w-22)/2;
        out.push(rounded(px,y+11,z+24,pw,20,4.5,5,'#efe3c7'));
        out.push(a.top(px+2,y+13,z+28.6,rect(0,0,pw-4,16,4,'none','stroke="#cbbd9f" stroke-width=".5" stroke-dasharray="2 1.2"')));
      }
      out.push(rounded(x+4,y+38,z+24,w-8,d-43,3,3,'#bda4b3'));
      out.push(a.top(x+4,y+38,z+27.05,rect(0,0,w-8,d-43,3,'url(#close-weave)','opacity=".7"')));
      out.push(a.top(x+5,y+38,z+27.1,rect(0,0,w-10,10,2,'#dfc9cd')));
      for(var qx=15;qx<w-10;qx+=14)out.push(a.top(x+qx,y+51,z+27.2,'<path d="M0 0q-3 13 0 28t0 22" fill="none" stroke="#e4cfd8" stroke-width=".65"/>'));
      out.push(a.top(x+6,y+d-30,z+27.25,rect(0,0,w-12,21,2,'#a5b69b')+rect(2,2,w-16,17,1,'none','stroke="#e2e8cd" stroke-width=".6" stroke-dasharray="2 1.3"')));
      for(var fringe=9;fringe<w-8;fringe+=4)out.push(a.top(x+fringe,y+d-9,z+27.2,'<path d="M0 0v3" stroke="#dedec4" stroke-width=".8"/>'));
    }else{
      // Slender tapered legs and a softly bevelled top retain every support height.
      [[5,5],[w-9,5],[5,d-9],[w-9,d-9]].forEach(function(q){var lx=x+q[0],ly=y+q[1];out.push(a.polygon([[lx+1,ly+4,z],[lx+3,ly+4,z],[lx+4,ly+4,z+h-3],[lx,ly+4,z+h-3]],'#ad8b63'),a.polygon([[lx,ly,z+h-3],[lx,ly+4,z+h-3],[lx+1,ly+4,z],[lx+1,ly,z]],'#8f7959'));});
      out.push(a.box(x+6,y+d-8,z+h-10,w-12,3,7,wood));
      out.push(rounded(x,y,z+h-3,w,d,3,type==='table'?6:4,'#c8ad85'));
      out.push(a.top(x+1,y+1,z+h+.03,rect(0,0,w-2,d-2,type==='table'?5:3,'url(#close-grain)','opacity=".38"')));
      out.push(a.top(x+3,y+3,z+h+.06,rect(0,0,w-6,d-6,type==='table'?4:2,'none','stroke="#ebd6b0" stroke-width=".65"')));
      if(type==='desk')out.push(a.front(x+w*.58,y+d-10,z+h-11,w*.3,5,7,'S',rect(0,0,w*.3,7,1,'#bf9e73','stroke="#eee0bc" stroke-width=".5"')+'<path d="M'+w*.12+' 3h'+w*.06+'" stroke="#f6e7c4" stroke-width="1.4"/>'));
      if(type==='dining'){
        out.push(a.top(x+w*.42,y+2,z+h+.1,rect(0,0,w*.16,d-4,1,'#9eae91')+rect(2,2,w*.16-4,d-8,1,'none','stroke="#e1e5c9" stroke-width=".5" stroke-dasharray="1.8 1.3"')));
        [.23,.76].forEach(function(q){out.push(a.top(x+w*q,y+d*.45,z+h+.2,'<rect x="-15" y="-12" width="30" height="24" rx="3" fill="#b8c1a2"/><rect x="-13" y="-10" width="26" height="20" rx="2" fill="none" stroke="#e2e6ca" stroke-width=".5"/><ellipse rx="10" ry="9" fill="#d1c5a2"/><circle r="7" fill="#f5f0db" stroke="#9db49e" stroke-width=".7"/><circle r="5.4" fill="none" stroke="#d3ddc6" stroke-width=".6"/><path d="M-12-5v10M12-5v10m-13-10v3m2-3v3" stroke="#8b9f91" stroke-width=".8"/>'));});
      }
    }
    return '<g class="furniture-finish" data-finish="'+type+'">'+out.join('')+'</g>';
  }
  root.FurnitureFinish={draw:draw};
})(window);
