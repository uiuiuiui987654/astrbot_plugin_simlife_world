/* View-only zoom and pan; furniture positions and scheduled activities stay unchanged. */
(function(){
  'use strict';
  var views=new Map(),drag=null,suppressClick=false;
  function state(room){var key=room.dataset.room;if(!views.has(key))views.set(key,{zoom:1.6,x:0,y:0,focused:false});return views.get(key);}
  function paint(room){
    var s=state(room),xLimit=room.clientWidth*(s.zoom-1)/2,yLimit=room.clientHeight*(s.zoom-1)/2;
    // Start with the character in view even when a room's anchor is off-center.
    if(!s.focused){
      var character=room.querySelector('.projected-character');
      if(character&&room.clientWidth){var bounds=room.getBoundingClientRect(),person=character.getBoundingClientRect();s.x=bounds.left+bounds.width*.55-(person.left+person.width/2);s.y=bounds.top+bounds.height*.58-(person.top+person.height/2);s.focused=true;}
    }
    s.x=Math.max(-xLimit,Math.min(xLimit,s.x));s.y=Math.max(-yLimit,Math.min(yLimit,s.y));
    room.style.setProperty('--room-zoom',s.zoom);room.style.setProperty('--room-pan-x',s.x+'px');room.style.setProperty('--room-pan-y',s.y+'px');
    var value=room.querySelector('.room-zoom-value');if(value)value.textContent=Math.round(s.zoom*100)+'%';
    room.querySelector('[data-room-view="out"]').disabled=s.zoom<=1;
    room.querySelector('[data-room-view="in"]').disabled=s.zoom>=2.6;
  }
  function zoom(room,amount){var s=state(room);s.zoom=Math.round(Math.max(1,Math.min(2.6,s.zoom+amount))*10)/10;if(s.zoom===1){s.x=0;s.y=0;}paint(room);}
  document.addEventListener('click',function(event){
    if(suppressClick&&event.target.closest('.room-canvas')){suppressClick=false;event.preventDefault();event.stopImmediatePropagation();return;}
    var button=event.target.closest('[data-room-view]');if(!button)return;
    var room=button.closest('.projected-room');if(!room)return;
    event.preventDefault();event.stopPropagation();
    if(button.dataset.roomView==='reset'){var s=state(room);s.zoom=1;s.x=0;s.y=0;paint(room);}else zoom(room,button.dataset.roomView==='in'?.2:-.2);
  },true);
  document.addEventListener('pointerdown',function(event){
    var canvas=event.target.closest('.room-canvas');if(!canvas||event.button!==0)return;
    var room=canvas.closest('.projected-room'),s=state(room);suppressClick=false;
    drag={canvas:canvas,room:room,id:event.pointerId,startX:event.clientX,startY:event.clientY,x:s.x,y:s.y,moved:false};
  });
  document.addEventListener('pointermove',function(event){
    if(!drag||event.pointerId!==drag.id)return;
    var dx=event.clientX-drag.startX,dy=event.clientY-drag.startY;
    if(!drag.moved&&Math.hypot(dx,dy)<5)return;
    if(!drag.moved){drag.moved=true;drag.canvas.classList.add('is-dragging');drag.canvas.setPointerCapture(event.pointerId);}
    var s=state(drag.room);s.x=drag.x+dx;s.y=drag.y+dy;paint(drag.room);event.preventDefault();
  },{passive:false});
  function release(event){if(!drag||event.pointerId!==drag.id)return;suppressClick=drag.moved;drag.canvas.classList.remove('is-dragging');if(drag.canvas.hasPointerCapture(event.pointerId))drag.canvas.releasePointerCapture(event.pointerId);drag=null;}
  document.addEventListener('pointerup',release);document.addEventListener('pointercancel',release);
  document.addEventListener('wheel',function(event){
    var canvas=event.target.closest('.room-canvas');if(!canvas||!event.ctrlKey)return;
    event.preventDefault();zoom(canvas.closest('.projected-room'),event.deltaY<0?.2:-.2);
  },{passive:false});
  document.addEventListener('keydown',function(event){
    var room=event.target.closest('.projected-room');if(!room||event.target.matches('input,textarea'))return;
    if(event.key==='+'||event.key==='='){zoom(room,.2);event.preventDefault();}
    if(event.key==='-'){zoom(room,-.2);event.preventDefault();}
  });
  var resizing=new ResizeObserver(function(entries){entries.forEach(function(e){paint(e.target);});});
  function attach(){document.querySelectorAll('.projected-room:not([data-view-ready])').forEach(function(room){room.dataset.viewReady='true';paint(room);resizing.observe(room);});}
  new MutationObserver(function(records){
    records.forEach(function(record){record.removedNodes.forEach(function(node){if(node.nodeType!==1)return;if(node.matches('.projected-room'))resizing.unobserve(node);node.querySelectorAll('.projected-room').forEach(function(room){resizing.unobserve(room);});});});attach();
  }).observe(document.documentElement,{childList:true,subtree:true});
  attach();
})();
