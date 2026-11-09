/* Dedicated geometry for devices and loose objects; never add a cabinet behind them. */
(function(root){
  'use strict';
  function draw(p,type,m,z,a){
    var x=p[0],y=p[1],w=p[2],d=p[3],h=m.height,f=m.facing,b=[],metal='url(#close-metal)',glass='url(#close-glass)';z=z||0;
    function tag(markup){return '<g class="object-shape shape-'+type+'" data-shape="'+(m.id==='digital_tablet'?'drawing-tablet':type)+'">'+a.polygon([[x,y,z+.1],[x+w,y,z+.1],[x+w,y+d,z+.1],[x,y+d,z+.1]],'transparent','pointer-events="all"')+markup+'</g>';}
    function shadow(){return a.top(x,y,z+.05,'<ellipse cx="'+w/2+'" cy="'+d*.55+'" rx="'+w*.43+'" ry="'+d*.28+'" fill="#2b44301c"/>');}
    if(m.id==='digital_tablet'){
      // Pen display rests at an angle on a small folding stand.
      var rear=y+d*.13,front=y+d*.9,topZ=z+Math.min(15,d*.6),bottomZ=z+2;
      b.push(shadow(),a.line([x+w*.25,rear,topZ-2],[x+w*.25,y+d*.6,z],'#798c81',1.3),a.line([x+w*.75,rear,topZ-2],[x+w*.75,y+d*.6,z],'#798c81',1.3));
      b.push(a.polygon([[x,rear,topZ],[x+w,rear,topZ],[x+w,front,bottomZ],[x,front,bottomZ]],'#465c59','stroke="#a5b7a7" stroke-width=".7"'));
      var q=a.point(x+3,rear+2,topZ-1),r=a.point(x+3,front-2,bottomZ+1),scale=(w-6)/60;
      b.push('<g transform="matrix('+a.camera.s*scale+' 0 '+((r[0]-q[0])/35)+' '+((r[1]-q[1])/35)+' '+q.join(' ')+')"><rect width="60" height="35" rx="1" fill="'+glass+'"/><path d="M2 32L18 11l14 14 11-19 15 26Z" fill="#a4c1ad"/><circle cx="47" cy="8" r="3" fill="#f4ddb2"/></g>');
      b.push(a.line([x+w+1,front-1,z+2],[x+w+1,rear+5,topZ-3],'#657c72',1.7));
      return tag(b.join(''));
    }
    if(type==='monitor'||type==='screen'){
      var side=/E|W/.test(f),span=side?d:w,thick=1.4,panelH=Math.min(h,span*.60),wall=m.mount==='wall',stand=wall?0:Math.min(9,h*.24),bottom=wall?48:z+stand;
      var px=side?x:x,py=side?y:y+d*.28,pw=side?thick:w,pd=side?d:thick;
      if(!wall){
        b.push(shadow(),a.box(x+w*.25,y+d*.25,z,w*.5,Math.max(3,d*.55),1.2,'#9eafa2',metal));
        b.push(a.box(x+w*.46,y+d*.28,z+1,w*.08,Math.min(d,3),stand+1,'#91a99b',metal));
      }
      b.push(a.box(px,py,bottom,pw,pd,panelH,'#3a514e','#758d83'));
      b.push(a.front(px,py,bottom,pw,pd,panelH,f,root.FurnitureArt.draw('screen',span,panelH,'close-',a.environment,true)));
      return tag(b.join(''));
    }
    if(type==='grill'){
      var cx=x+w*.5,cy=y+d*.45,rx=w*.45,ry=d*.34,top=z+h*.67;
      b.push(shadow());
      [[-.65,-.6],[.65,-.6],[0,.75]].forEach(function(v){b.push(a.line([cx+rx*v[0],cy+ry*v[1],top-5],[cx+rx*v[0]*1.18,cy+ry*v[1]*1.18,z+2],'#768e83',2));});
      b.push(a.line([cx-rx*.75,cy-ry*.65,z+10],[cx+rx*.75,cy-ry*.65,z+10],'#a5b7a4',1.4));
      function ring(scale,zz,start,end){var out=[];for(var i=start;i<=end;i++){var t=i*Math.PI/20;out.push([cx+rx*scale*Math.cos(t),cy+ry*scale*Math.sin(t),zz]);}return out;}
      b.push(a.polygon(ring(1,top,0,40),'#3e5750','stroke="#b2c2ae" stroke-width="1"'));
      var upper=ring(1,top,0,20),lower=ring(.44,top-h*.22,0,20).reverse();
      b.push(a.polygon(upper.concat(lower),'#71887a','stroke="#4a655a" stroke-width=".6"'));
      b.push(a.polygon(ring(.9,top+.3,0,40),'#293e38'));
      for(var gx=-.75;gx<=.8;gx+=.18){var dy=Math.sqrt(.81-gx*gx)*ry;b.push(a.line([cx+rx*gx,cy-dy,top+1],[cx+rx*gx,cy+dy,top+1],'#bdc9b7',.8));}
      b.push(a.line([cx-rx-2,cy,top-3],[cx-rx-5,cy,top-3],'#c7b18d',2.5),a.line([cx+rx+2,cy,top-3],[cx+rx+5,cy,top-3],'#c7b18d',2.5));
      return tag(b.join(''));
    }
    var sizes={camera:[64,48],headphones:[64,60],diffuser:[48,52],iron:[70,42],wateringcan:[64,62],weights:[80,32],speaker:[40,62],ricecooker:[54,48],pourover:[44,64],jar:[40,52],toaster:[62,44],coffee:[52,66],projector:[68,40],paints:[54,72],record:[70,55],console:[65,28]};
    if(!sizes[type])return null;
    var wh=sizes[type],scale=Math.min(w/wh[0],h/wh[1]),aw=wh[0]*scale,ah=wh[1]*scale;
    if(type==='headphones'){scale=w/wh[0];aw=w;ah=wh[1]*scale;}
    if(type==='weights'||type==='record'){
      var ts=Math.min(w/wh[0],d/wh[1]);
      b.push(shadow(),a.top(x+(w-wh[0]*ts)*.5,y+(d-wh[1]*ts)*.5,z+.7,'<g transform="scale('+ts+')">'+root.FurnitureArt.draw(type,wh[0],wh[1],'close-',a.environment,false)+'</g>'));
    }else{
      b.push(shadow());
      if(type==='projector'&&m.mount==='ceiling')b.push(a.line([x+w*.5,y+d*.5,z+ah],[x+w*.5,y+d*.5,a.camera.wall],'#91a899',2));
      b.push(a.front(x+(w-aw)*.5,y,z,aw,d*.6,ah,'S','<g transform="scale('+scale+')">'+root.FurnitureArt.draw(type,wh[0],wh[1],'close-',a.environment,true)+'</g>'));
    }
    return tag(b.join(''));
  }
  root.ObjectShapes={draw:draw};
})(window);
