/* Floor plan artwork from the shared room footprints and facing directions. */
(function(root) {
  'use strict';
  var plan=root.RoomModel.plan;
  function rect(x,y,w,h,c,r,extra){return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(r||0)+'" fill="'+c+'" '+(extra||'')+'/>';}
  function line(x,y,a,b,c,w){if(/^url\(/.test(c))c=/metal/.test(c)?'#bdcbb7':'#b39670';return '<path d="M'+x+' '+y+'L'+a+' '+b+'" fill="none" stroke="'+c+'" stroke-width="'+(w||1)+'"/>';}
  function oval(x,y,w,h,c){return '<ellipse cx="'+x+'" cy="'+y+'" rx="'+w+'" ry="'+h+'" fill="'+c+'"/>';}
  function surface(x,y,w,h,id){return rect(x,y,w,h,'url(#'+id+'wood)',3)+rect(x+2,y+2,w-4,h-4,'url(#'+id+'grain)',2)+line(x+3,y+h-3,x+w-3,y+h-3,'#ebcca0',1);}
  function orientedSeat(w,d,face){
    var sideways=/E|W/.test(face),L=sideways?d:w,D=sideways?w:d;
    var body=rect(0,0,L,D,'url(#map-fabric)',5)+rect(5,10,L-10,D-15,'url(#map-sage)',3)+rect(3,1,L-6,10,'#a07e8a',3);
    for(var i=1;i<3;i++)body+=line(L*i/3,13,L*i/3,D-6,'#e1dfc5',.7);
    body+=rect(0,7,6,D-8,'#b998a2',2)+rect(L-6,7,6,D-8,'#b998a2',2);
    var transform=face==='E'?'translate(0 '+d+') rotate(-90)':face==='N'?'translate('+w+' '+d+') rotate(180)':face==='W'?'translate('+w+' 0) rotate(90)':'';
    return '<g class="seat-plan" data-facing="'+face+'" transform="'+transform+'">'+body+'</g>';
  }
  function planFixtures(room,id){
    var b=[];
    (root.RoomModel.fixtures[room]||[]).forEach(function(f){
      if(f.type==='chair')b.push('<g transform="translate('+f.x+' '+f.y+')">'+orientedSeat(f.w,f.d,f.facing)+'</g>');
      else if(f.type==='stairs'){var n=16,run=f.w/n;b.push('<g class="stair-plan-link" data-stair-floor="2" role="button" tabindex="0" aria-label="楼梯，上二楼" pointer-events="all">');b.push(rect(f.x,f.y,f.w,f.d,'#33261c',4,'opacity=".16"'),surface(f.x,f.y,f.w,f.d,id));for(var s=1;s<n;s++){var sx=f.x+s*run;b.push(line(sx,f.y+2,sx,f.y+f.d-2,'#f1d2a7',1.2),line(sx+1.5,f.y+2,sx+1.5,f.y+f.d-2,'#7d6143',.7));}
        b.push(rect(f.x+f.w*.62,f.y,f.w*.38,f.d,'#3b2e24',2,'opacity=".18"'),line(f.x+1,f.y+f.d-1,f.x+f.w-1,f.y+f.d-1,'#5d4636',2.5),'<path d="M'+(f.x+14)+' '+(f.y+f.d*.5)+'H'+(f.x+f.w-16)+'l-7-5m7 5l-7 5" stroke="#f8e8c7" fill="none" stroke-width="1.6"/>','<rect x="'+(f.x+f.w-58)+'" y="'+(f.y+5)+'" width="52" height="18" rx="9" fill="#7d6143" opacity=".92"/>','<text x="'+(f.x+f.w-32)+'" y="'+(f.y+18)+'" text-anchor="middle" font-size="10" fill="#fff3d6" font-weight="700">上 2F</text>','</g>');}
      else if(f.type==='sink'||f.type==='basin')b.push(surface(f.x,f.y,f.w,f.d,id),oval(f.x+f.w/2,f.y+f.d/2,f.w*.33,Math.min(12,f.d*.32),'#dce6d5'),oval(f.x+f.w/2,f.y+f.d/2,f.w*.24,Math.min(8,f.d*.24),'#829e92'));
      else b.push(surface(f.x,f.y,f.w,f.d,id));
    });
    return b.join('');
  }
  function planArtwork(item,type,id,e){
    var p=plan[item.id],w=p[2],h=p[3],b=[],face=root.RoomModel.facing[item.id]||'S',wood='url(#'+id+'wood)',metal='url(#'+id+'metal)',glass='url(#'+id+'glass)';
    if(type==='sofa'||type==='rockingchair')b.push(orientedSeat(w,h,face));
    else if(type==='fridge')b.push(rect(0,0,w,h,metal,3),rect(3,3,w-6,h-6,'#dce6d3',2),line(w-2,5,w-2,h-5,'#859b8e',2));
    else if(/^(cabinet|jewelry|bookshelf)$/.test(type)) {
      b.push(surface(0,0,w,h,id),line(w/2,3,w/2,h-3,'#7c6449',.8),rect(w*.35,h-4,w*.11,2,metal,1),rect(w*.54,h-4,w*.11,2,metal,1));
      if(type==='bookshelf')for(var i=6;i<w-5;i+=8)b.push(rect(i,4,5,h-9,['#a68d88','#8ca591','#b6ac85'][i%3],1));
    } else if(/^(monitor|screen|mirror)$/.test(type)) {
      b.push(rect(0,0,w,h,metal,2),rect(2,2,w-4,h-4,glass,1));
      if(w>h)b.push(oval(w/2,h+3,w*.17,3,'#6c8176'));else b.push(oval(w+2,h/2,3,h*.17,'#6c8176'));
    } else if(/^(dining|desk|table)$/.test(type)) {

      b.push(surface(0,0,w,h,id));
      if(type==='dining'&&item.id!=='dining_table')b.push(oval(w*.25,h*.49,7,7,'#e9ebdb'),oval(w*.75,h*.49,7,7,'#e9ebdb'),oval(w*.5,h*.51,4,4,'#a7b99b'));
    } else if(type==='stairs') {
      b.push(surface(0,0,w,h,id));for(var x=10;x<w;x+=13)b.push(line(x,2,x,h-2,'#f1d2a7',1),line(x+2,2,x+2,h-2,'#7d6143',.65));b.push(line(1,1,w-1,1,metal,2),line(1,h-1,w-1,h-1,metal,2),'<path d="M15 '+h*.5+'H'+(w-16)+'l-7-5m7 5l-7 5" stroke="#f8e8c7" fill="none" stroke-width="1.4"/>');
    } else if(type==='lamp'||type==='floorlamp') {
      b.push(oval(w*.5,h*.62,w*.36,w*.36,wood),oval(w*.5,h*.43,w*.48,w*.48,'#e6d6b3'),oval(w*.5,h*.43,w*.33,w*.33,'#fff0c6'));
    } else if(item.id==='oven') {
      b.push(rect(0,0,w,h,metal,3),rect(3,3,w-6,h-6,'#4d6259',2));[[.29,.28],[.72,.28],[.29,.72],[.72,.72]].forEach(function(a){b.push(oval(w*a[0],h*a[1],w*.15,w*.15,'#a8b3a0'),oval(w*a[0],h*a[1],w*.09,w*.09,'#4b5f56'));});
    } else b.push(root.FurnitureArt.draw(type,w,h,id,e,false));
    b.push(rect(-2,-2,w+4,h+4,'transparent',2,'class="item-footprint"'));
    return b.join('');
  }
  root.InteriorLayout={plan:plan,anchors:root.RoomModel.anchors,planFixtures:planFixtures,planArtwork:planArtwork};
})(typeof window==='undefined'?globalThis:window);
