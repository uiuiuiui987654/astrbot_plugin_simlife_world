/* Product silhouettes shared by the shop, possessions and placed decorations. */
(function (root) {
  'use strict';
  var serial = 0;
  var cream = '#fbf3dc', ink = '#53695f', green = '#91ac8b', purple = '#b4a4c4', wood = '#c5a071';
  function path(d, fill, stroke, width) { return '<path d="'+d+'" fill="'+(fill || 'none')+'"'+(stroke?' stroke="'+stroke+'" stroke-width="'+(width || 1.6)+'" stroke-linejoin="round" stroke-linecap="round"':'')+'/>'; }
  function rect(x,y,w,h,r,fill,stroke) { return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+r+'" fill="'+fill+'"'+(stroke?' stroke="'+stroke+'" stroke-width="1.4"':'')+'/>'; }
  function ellipse(x,y,rx,ry,fill,stroke) { return '<ellipse cx="'+x+'" cy="'+y+'" rx="'+rx+'" ry="'+ry+'" fill="'+fill+'"'+(stroke?' stroke="'+stroke+'" stroke-width="1.4"':'')+'/>'; }
  function circle(x,y,r,fill,stroke) { return ellipse(x,y,r,r,fill,stroke); }
  function line(d,color,width) { return path(d,'none',color,width); }
  function repeat(n,fn) { var s=''; for(var i=0;i<n;i++)s+=fn(i); return s; }
  function escape(s) { return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
  function plate() { return ellipse(50,70,41,16,'#c7d3bc')+ellipse(50,66,41,16,cream)+ellipse(50,66,34,11,'#e5e5cb'); }
  function leaves(x,y) { return path('M'+x+' '+y+'q-25-5-18-21 19 0 18 21q0-24 17-25 9 19-17 25',green)+line('M'+x+' '+(y+12)+'v-24','#6d906d'); }
  function cup(color, details) { return path('M28 30h44L67 82q-17 8-34 0Z',color,ink)+ellipse(50,30,22,6,cream,ink)+path('M32 39h36l-4 37q-14 6-28 0Z',color)+details+line('M34 39l3 29','#ffffff66',3); }
  function pouch(color,inside) { return path('M26 18q24 5 48 0l-3 12 6 49q-26 11-54 0l6-49Z',color,'#9b9178')+line('M28 24h43M25 76q25 6 49 0','#ffffff88',2)+inside; }
  function bowl(color,inside) { return path('M12 48q2 35 38 36 37-1 38-36Z',color,ink)+ellipse(50,48,38,14,cream,ink)+inside+line('M24 64q7 12 24 13','#ffffff88',3); }
  function garment(color,long,details) { return path(long?'M34 24l-17 9-9 33 13 5 12-22v36h34V49l12 22 13-5-9-33-17-9Z':'M34 24L16 34 8 51l16 9 9-12v36h34V48l9 12 16-9-8-17-18-10Z',color,'#7c8178')+details+line('M37 78h26','#ffffff88',2); }
  function book(item) {
    var id=String(item.book_id || item.possession_id || item.id || item.name || ''), hash=0;
    for(var i=0;i<id.length;i++)hash=(hash*31+id.charCodeAt(i))>>>0;
    var colors=['#8caa9d','#bda2ac','#83a6b6','#b4ac81','#918ea9','#c0a078'], c=colors[Math.floor(hash/7)%colors.length];
    var art=path('M25 15h48q5 0 5 5v65H27q-8 0-8-8V23q0-8 6-8Z',c,ink)+rect(26,77,51,8,2,cream)+line('M30 80h42M30 83h42','#cfccb5',.8)+path('M25 15v61q-6 0-6 7V23q0-8 6-8Z','#637b75')+rect(31,22,39,47,2,'#ffffff1f');
    var motif=hash%6;
    if(/sea|tide|ferry/.test(id))motif=0;
    if(/stars|signal/.test(id))motif=1;
    if(/garden|slow/.test(id))motif=2;
    var covers={book_cloud:6,book_rain:7,book_light:8,book_code:5,book_kitchen:9,book_history:4,book_mech:10,book_monday:12,book_mountain:3,book_food:9,book_repair:10,book_far:12,book_cat:11};
    if(Object.prototype.hasOwnProperty.call(covers,id))motif=covers[id];
    if(motif===0)art+=circle(57,36,7,'#e7d3a4')+path('M32 49q9-8 18 0t19 0v13H32Z','#e3ece1')+line('M32 55q9-8 18 0t19 0','#789c9e');
    if(motif===1)art+=circle(50,44,10,'none',cream)+ellipse(50,44,18,5,'none',cream)+circle(62,31,2,cream)+circle(38,58,1.6,cream);
    if(motif===2)art+=line('M50 62V34',cream,2)+path('M50 51q-18 0-12-12 13 0 12 12m0 7q18-1 13-13-14 1-13 13',cream)+circle(50,33,5,'#e7d3a4');
    if(motif===3)art+=path('M32 60l12-24 9 14 7-10 9 20Z',cream)+circle(61,31,5,'#e7d3a4');
    if(motif===4)art+=rect(36,37,29,24,2,cream)+rect(40,41,7,9,1,c)+rect(53,41,7,9,1,c)+rect(47,53,7,8,1,c)+path('M34 37l16-12 17 12Z','#e7d3a4');
    if(motif===5)art+=line('M41 35l-7 9 7 9m18-18 7 9-7 9m-6-22-8 28',cream,2.5);
    if(motif===6)art+=circle(59,35,6,'#e7d3a4')+path('M36 53q-8-5-1-10 0-11 12-8 8-8 13 3 13-1 8 14Z',cream);
    if(motif===7)art+=rect(39,31,23,29,4,cream)+rect(43,36,15,10,1,c)+circle(44,53,2,c)+circle(57,53,2,c)+line('M43 59l-7 7m22-7 7 7',cream,2);
    if(motif===8)art+=path('M33 57l13-26h8l14 26Z',cream)+circle(50,43,8,c)+circle(50,43,5,cream)+line('M38 61h26',cream,2);
    if(motif===9)art+=path('M35 43h31v11q0 7-16 7t-15-7Z',cream)+line('M34 41h33m-23-9q-4 5 0 7m10-7q-4 5 0 7',cream,2);
    if(motif===10)art+=circle(50,46,12,'none',cream)+circle(50,46,5,cream)+repeat(8,function(i){var a=i*Math.PI/4;return line('M'+(50+Math.cos(a)*12)+' '+(46+Math.sin(a)*12)+'l'+Math.cos(a)*5+' '+Math.sin(a)*5,cream,3);});
    if(motif===11)art+=path('M37 47V31l12 9h5l12-9v16q0 14-14 14T37 47Z',cream)+circle(45,49,2,c)+circle(58,49,2,c)+path('M49 54h5l-2.5 3Z',c);
    if(motif===12)art+=rect(34,37,34,23,2,cream)+line('M35 39l16 12 16-12M35 59l11-11m10 0 11 11',c,1.5)+path('M57 28l11-3-6 8Z','#e7d3a4');
    return art+path('M62 15h7v13l-3.5-3-3.5 3Z','#dec499');
  }
  var makers = {
    milk_tea:function(){return cup('#d3b18b',repeat(8,function(i){return circle(38+i%4*8,70+Math.floor(i/4)*8,3.2,'#665647');}))+path('M54 17l4-12h6L55 55h-5Z',purple)+ellipse(50,29,22,4,'#e2d4b5');},
    coffee:function(){return ellipse(48,80,34,8,'#d8dfc9')+path('M70 37q26-2 17 21-5 9-18 6',cream,ink,3)+path('M25 32h47v34q-2 13-23 13T25 66Z','#9bb4a8',ink)+ellipse(48,32,24,7,cream,ink)+ellipse(48,32,19,4,'#76543f')+line('M39 20q-7-7 1-14m13 14q-7-7 1-14','#aab9ac',2);},
    juice:function(){return cup('#e4b46b',circle(51,57,12,'#f4d48c','#e5a560')+line('M51 46v22m-10-11h20m-17-7 14 14m0-14-14 14','#fff1b7'))+line('M58 44l7-32h12',green,4);},
    fruit_tea:function(){return cup('#d9a67e',circle(45,55,10,'#f0d589','#c9ae68')+circle(59,71,6,'#bb7c70')+path('M37 66q13-13 14 1-8 8-14-1',green))+line('M60 46l4-33h13',purple,4);},
    milk:function(){return path('M29 27l9-14h28l9 14v58H29Z','#eaf0df',ink)+path('M29 27h46L65 14H39Z','#9bb6b5')+path('M65 14v71h10V27Z','#8faeae')+rect(29,42,36,27,0,'#bad0cc')+path('M47 46q-15 17 0 19 15-2 0-19Z',cream)+line('M39 14h26',ink,3);},
    soy_milk:function(){return cup('#f1e7c9',rect(34,48,31,19,4,'#aebd98')+ellipse(44,57,4,6,cream)+ellipse(55,57,4,6,cream))+line('M41 18q-5-6 1-12m14 12q-5-6 1-12','#9bab98',2);},
    sparkling:function(){return rect(40,9,20,9,3,'#b3accc',ink)+path('M41 18v13L31 42v37q0 9 19 9t19-9V42L59 31V18Z','#c9dfdb',ink)+rect(31,49,38,22,0,cream)+circle(50,60,7,green)+repeat(6,function(i){return circle(40+i%3*9,38+Math.floor(i/3)*39,2,'#f9fff2');})+line('M36 43v31','#ffffff88',3);},
    chips:function(){return pouch('#cfb779',ellipse(50,51,18,19,cream)+ellipse(45,46,9,14,'#e3bc70')+ellipse(56,58,9,13,'#d5a759')+line('M43 38l4 15m7-5 4 17','#f9d990',2));},
    chocolate:function(){return rect(29,15,43,66,2,'#735441',ink)+repeat(6,function(i){return rect(33+i%2*19,19+Math.floor(i/2)*16,15,12,2,'#98745a','#664b3a');})+path('M25 54l16 8 13-6 23 8v21H25Z',purple,ink)+line('M27 69h47',cream,2);},
    cake:function(){return plate()+path('M22 42l35-19 24 23v27H22Z','#f3d9b3','#bb9c7d')+rect(22,49,59,7,0,'#bf8b91')+rect(22,63,59,6,0,cream)+path('M22 42l35-19 24 23-59 3Z',cream)+ellipse(57,33,10,4,'#eadfcb')+path('M51 27q6-13 12 0 1 9-6 11-7-2-6-11Z','#c6817c')+path('M57 23l-5-4 5 1 3-4 1 5 5 1-6 2Z',green);},
    nuts:function(){return pouch('#a7b495',rect(31,34,38,34,8,cream)+repeat(5,function(i){return ellipse(38+i%3*12,44+Math.floor(i/3)*14,4,7,i%2?'#b38d62':'#d4b37d');}));},
    cookies:function(){return plate()+repeat(4,function(i){var x=30+i%2*25,y=47+Math.floor(i/2)*15;return ellipse(x,y,14,9,'#d7b47d','#b6905e')+repeat(5,function(j){return circle(x-7+j%3*7,y-3+Math.floor(j/3)*6,1.6,'#97714d');});});},
    icecream:function(){return path('M30 45h42L51 88Z','#d5b480','#b58b5b')+line('M36 51l24 18M40 62l14 10m10-21-23 18m20-8-14 11','#f3dcab',1.2)+path('M28 47q-7-14 7-18-5-12 9-17 4 12 16 11 16 3 10 13 15 9 3 16Z','#f0dfcd','#cfb6a3')+line('M34 31q13 8 29 1m-33 12q19 9 39-1','#d6bac0',3);},
    ramen:function(){return bowl('#a7b8a3',ellipse(50,48,33,10,'#d3ac75')+repeat(5,function(i){return line('M25 '+(42+i*3)+'q12-7 22 0t27 0','#f7e2aa',1.8);})+ellipse(66,45,9,6,cream)+ellipse(66,45,4,3,'#d9b268')+path('M25 40l8-6 5 10-8 4Z',green))+line('M65 16L32 49m39-30L39 51',wood,3);},
    rice_bowl:function(){return bowl('#b2bd9c',ellipse(50,47,32,11,'#f4f0da')+repeat(5,function(i){return ellipse(31+i*9,46+(i%2)*4,7,4,'#ba8d64');})+path('M58 49q-12-4-8-9 8-2 10 6 3-11 10-8 5 7-8 11Z',green));},
    hotpot:function(){return path('M18 47H7v12h15m60-12h11v12H78','none',ink,5)+bowl('#899f99',ellipse(50,48,33,10,'#d1b47a')+path('M50 38q-16 11 0 20 16-9 0-20','#b98068')+repeat(6,function(i){return ellipse(27+i%3*21,45+Math.floor(i/3)*7,5,2,i%2?green:cream);})) +line('M37 27q-8-8 0-15m17 15q-8-8 0-15m14 19q-8-8 0-15','#b0baab',2);},
    bento:function(){return rect(12,29,76,53,8,wood,ink)+rect(16,33,32,44,4,cream)+rect(52,33,31,20,3,green)+rect(52,57,31,20,3,'#d8b080')+circle(32,53,6,'#c5847d')+repeat(3,function(i){return ellipse(58+i*9,42,4,6,'#c7d39f')+line('M56 '+(62+i*5)+'h23','#9a7559',2);});},
    dumplings:function(){return plate()+repeat(5,function(i){var x=26+i%3*23,y=43+Math.floor(i/3)*17;return path('M'+(x-11)+' '+(y+5)+'q11-25 22 0-11 10-22 0Z',cream,'#c4b496')+line('M'+(x-7)+' '+(y+3)+'l3-5m3 3 1-5m4 5-1-5m4 7-1-4','#c4b496',1);});},
    sushi:function(){return rect(12,37,76,44,6,wood,ink)+repeat(6,function(i){var x=27+i%3*23,y=47+Math.floor(i/3)*22;return rect(x-9,y-4,18,15,5,cream)+ellipse(x,y-2,9,5,ink)+ellipse(x,y-2,6,3,cream)+circle(x,y-2,2.5,i%2?green:'#c8937a');});},
    bbq:function(){return plate()+repeat(3,function(i){var x=30+i*20;return line('M'+(x-10)+' 30l18 49',wood,2.5)+repeat(3,function(j){return rect(x-10+j*4,35+j*12,14,10,3,(i+j)%2?'#b78b62':'#93a17b','#947251');});});},
    camera:function(){return rect(18,31,66,45,8,'#88a49c',ink)+path('M28 31l6-9h22l6 9Z',ink)+rect(64,36,13,8,2,cream)+circle(47,54,19,cream,ink)+circle(47,54,14,ink)+circle(47,54,9,'#7ba2a6')+circle(43,50,3,'#d5e5da')+rect(25,23,9,5,1,wood)+rect(19,41,8,25,3,'#68857b');},
    headphones:function(){return path('M22 58V43q0-31 28-31t28 31v15','none',ink,9)+path('M25 40q2-25 25-25t25 25','none',purple,5)+rect(16,45,16,34,7,purple,ink)+rect(68,45,16,34,7,purple,ink)+rect(27,48,7,29,3,cream)+rect(66,48,7,29,3,cream)+line('M77 79q0 11-17 8',ink,2);},
    keyboard:function(){return path('M15 31h70l8 43H7Z','#9cb4aa',ink)+path('M19 35h62l6 31H13Z',cream)+repeat(40,function(i){return rect(21+i%10*6,38+Math.floor(i/10)*6,4.4,4,1,i%13===0?purple:'#ccd5bf');})+rect(33,63,33,5,1,wood);},
    console:function(){return rect(9,29,82,47,10,ink)+rect(10,30,16,45,8,'#a3b7c4')+rect(74,30,16,45,8,purple)+rect(29,34,42,35,2,'#8eb4b6')+path('M31 62l13-17 12 11 13-13v24H31Z',green)+circle(61,43,4,cream)+line('M18 46v10m-5-5h10',ink,3)+circle(82,44,3,ink)+repeat(4,function(i){return circle(79+i%2*6,58+Math.floor(i/2)*6,1.5,ink);});},
    powerbank:function(){return rect(28,17,44,69,8,'#a3b8b3',ink)+rect(35,23,14,4,1,ink)+rect(55,23,8,4,1,ink)+path('M52 37L40 58h11l-4 16 17-24H52Z',cream)+line('M34 34v40','#d7e6da',2);},
    speaker:function(){return rect(26,16,48,70,9,'#94a49c',ink)+rect(32,23,36,56,6,'#637c74')+circle(50,41,11,'#9eb6a9',cream)+circle(50,41,4,ink)+circle(50,65,9,'#849e94',cream)+repeat(4,function(i){return circle(39+i*7,20,1,cream);});},
    tablet:function(){return rect(23,11,55,78,6,ink)+rect(28,17,45,62,2,'#9fbac0')+circle(60,31,7,cream)+path('M29 67l17-25 9 13 17-9v31H29Z','#799b8f')+circle(50,84,2,cream)+line('M31 21v40','#dfece488',2);},
    tshirt:function(){return garment('#a5b6b3',false,path('M35 25q15 20 30 0',cream,'#7c8178')+rect(53,44,10,10,2,cream));},
    hoodie:function(){return garment(purple,true,path('M34 26q-2-22 16-22t16 22L50 38Z','#c8bdd2','#87808f')+path('M38 61h24l4 13H34Z','#a596b5')+line('M45 35v18m10-18v18',cream,2));},
    coat:function(){return garment('#c4b79a',true,path('M34 24l16 12 16-12-7 27-9-10-9 10Z',cream)+line('M50 41v42','#8e8876')+rect(35,61,10,8,1,'#b1a78b')+rect(55,61,10,8,1,'#b1a78b')+repeat(3,function(i){return circle(53,49+i*11,1.6,ink);}));},
    skirt:function(){return path('M32 22h36l17 60q-35 10-70 0Z',purple,'#87808f')+rect(32,19,36,9,2,'#92879e')+repeat(5,function(i){return line('M'+(35+i*7)+' 30L'+(24+i*13)+' 81','#d7ccdf',1.7);});},
    pajamas:function(){return '<g transform="translate(0 0) scale(.69)">'+garment('#c0b6d0',true,path('M34 24l16 12 16-12-10 21-6-8-6 8Z',cream)+line('M50 37v46',cream)+repeat(3,function(i){return circle(53,48+i*10,1.6,ink);}))+'</g>'+path('M58 47h29l3 40H77l-5-24-2 24H56Z','#c0b6d0',ink)+line('M59 51h27M58 82h11m9 0h10',cream,2);},
    sneakers:function(){return path('M22 36h21l10 18 29 8q11 3 10 13H17q-8-6-4-16Z','#9bb3a8',ink)+path('M12 70q35 5 80 0v10H15Z',cream,ink)+path('M44 47l16 10-9 9-13-15Z',cream)+line('M39 48l11-3m-6 9 12-4m-8 10 13-4',ink,2)+path('M20 38h18v22H18Z',purple);},
    cap:function(){return path('M22 57q0-36 30-36 30 1 29 38Z','#a4b3a2',ink)+path('M22 57q40-8 59 2l14 12q-30 13-73-4Z','#8ca18d',ink)+line('M52 22q-14 13-13 34','#d8dfc7',2)+circle(52,21,3,ink)+rect(53,38,15,10,3,cream);},
    pillow:function(){return path('M21 22q29 6 58 0-6 30 0 58-30-6-58 0 6-30 0-58Z',purple,'#8e8699')+rect(28,29,44,44,9,'#c9bed2')+line('M31 34h37M32 68h36','#f4ecdc',1.2)+circle(50,51,8,cream);},
    diffuser:function(){return line('M43 41L31 12m17 26V9m8 33 15-29',wood,3)+rect(33,39,35,10,3,wood,ink)+path('M32 48h37l5 28q-3 12-24 12T27 76Z','#c4d4bc',ink)+rect(35,57,30,17,4,cream)+leaves(50,69);},
    lamp:function(){return ellipse(50,84,24,5,'#b5a07c')+rect(47,39,6,43,2,wood)+path('M35 14h30l17 34q-32 12-64 0Z',cream,'#c4b48b')+ellipse(50,48,31,6,'#e2c58b')+ellipse(50,49,20,3,'#fff4c4')+line('M39 20l-9 24','#fffaf0',3);},
    towel:function(){return rect(18,45,64,35,6,'#aabca6',ink)+rect(24,22,54,35,5,'#d6d4bd',ink)+rect(24,22,16,35,5,cream)+line('M43 29h29m-29 5h29m-29 15h29M23 70h53M23 74h53','#8da38b',1.5);},
    scarf:function(){return path('M29 16h38q13 6 8 23L61 58l9 24-18 6-13-37 20-22H43L37 76H19Z','#bfaaaf','#8f7e85')+line('M30 22h30M24 57l17 3m-18 2 18 3m12 9 14-5m-12 10 14-5',cream,2)+repeat(5,function(i){return line('M'+(20+i*4)+' 76v8M'+(53+i*4)+' '+(88-i)+'l3 6','#9a818a',1.5);});},
    rug:function(){return path('M23 24h58L73 81H15Z','#9caf91',ink)+path('M29 32h44l-6 41H23Z','#d4cfb2')+path('M48 37l17 15-21 16-15-15Z',purple)+line('M16 28h-5m5 8h-6m4 8H9m4 8H8m4 8H7m4 8H6m4 8H5M82 28h5m-6 8h5m-6 8h5m-6 8h5m-6 8h5m-6 8h5m-6 8h5',wood,2);},
    storage_box:function(){return rect(16,34,68,48,5,'#b8c6ac',ink)+rect(11,27,78,14,4,'#d0d9bd',ink)+rect(37,51,26,11,3,cream,ink)+line('M23 47v28m54-28v28','#e5e9d0',2);},
    humidifier:function(){return path('M27 43q23-16 46 0l6 31q-1 14-29 14T21 74Z','#d1dfd4',ink)+ellipse(50,43,23,8,cream,ink)+ellipse(50,43,9,3,'#87a69c')+circle(50,69,5,green)+line('M35 53v20','#f8fff0',3)+line('M45 31q-9-10 0-21m11 23q-9-10 0-21','#bdcebf',3);},
    curtain:function(){return rect(22,18,56,63,1,'#c4d6cc')+line('M50 20v60M23 49h53',cream,3)+line('M13 15h74',wood,4)+path('M17 19h28q0 27-17 40l7 27H15Z',purple,'#9a8eaa')+path('M55 19h28l2 67H65l7-27Q55 45 55 19Z',purple,'#9a8eaa')+line('M24 21l-3 29m13-29-8 32m40-32 7 32m3-32 3 29','#ded3e3',2)+line('M17 60h13m40 0h13',wood,4);},
    flowers:function(){return path('M24 43l26 44 27-44-27 12Z','#d9c9ad','#b7a487')+line('M50 77L33 33m17 44V26m0 51 17-46','#74926d',2)+repeat(5,function(i){var x=29+i%3*20,y=27+Math.floor(i/3)*17;return leaves(x,y+8)+repeat(5,function(j){var a=j*6.28/5;return circle(x+Math.cos(a)*6,y+Math.sin(a)*6,5,i%2?'#d2b4bf':'#e6cf9d');})+circle(x,y,4,'#fff1c2');})+path('M50 69q-18-12-16 1 0 10 16-1 18-12 17 1 0 10-17-1Z',purple);},
    plant:function(){return line('M50 67V24','#728f6b',3)+leaves(50,43)+leaves(49,62)+path('M29 62h42l-6 24H35Z',wood,ink)+rect(26,59,48,9,3,'#d8b78c',ink);},
    bracelet:function(){return ellipse(50,56,29,22,'none',wood)+ellipse(50,53,29,22,'none','#ddc293')+repeat(12,function(i){var a=i*Math.PI/6;return circle(50+Math.cos(a)*29,53+Math.sin(a)*22,3,i%3?cream:purple,'#bfaa87');})+path('M47 73h6l4 8-7 7-7-7Z',purple,'#b09cb9');},
    candle:function(){return rect(29,37,42,47,7,'#bcb1c8',ink)+ellipse(50,37,21,6,cream,ink)+line('M50 37V26',ink,2)+path('M50 9q-18 20 0 23 15-3 0-23Z','#e3bd77')+path('M50 21q-6 10 0 11 6-2 0-11Z','#fff1ba')+rect(36,51,28,19,3,cream)+line('M42 58h16m-12 5h8',purple,2);},
    paint:function(){return rect(16,29,68,54,5,'#e5ddc5',ink)+rect(20,21,60,15,3,cream,ink)+repeat(10,function(i){return rect(23+i%5*11,42+Math.floor(i/5)*16,8,12,2,['#b3a0be','#92ac90','#82a9b2','#dab879','#c48e83'][i%5]);})+line('M22 77h56',wood,2);},
    paint_set:function(){return ellipse(44,60,30,22,wood,ink)+ellipse(55,53,7,5,cream)+repeat(5,function(i){return circle(24+i*9,59+(i%2)*10,5,['#c28b80','#e3c68f','#a5bc95','#88aab2','#baacc6'][i]);})+line('M59 72L78 22',wood,5)+path('M75 27l2-15q14 1 5 17Z',ink)+line('M70 38l5-12','#d9d8bb',5);},
    puzzle:function(){return rect(17,22,66,61,4,cream,ink)+path('M20 25h29v13q10-5 10 4t-10 4v12H35q5 10-3 10t-4-10h-8Z',green)+path('M51 25h29v31H67q5-10-4-10t-4 10h-8V44q9 4 9-4t-9-4Z',purple)+path('M51 59h29v21H51V69q-10 4-10-4t10-4Z','#d6ba85')+line('M24 76h19',wood,2);},
    guitar:function(){return path('M47 10h10l-3 39q19 0 17 16 18 23-11 24-37-1-22-22-7-16 9-18Z',wood,ink)+rect(48,17,7,39,1,'#8e785b')+circle(51,65,8,ink)+rect(43,79,17,4,1,cream)+line('M50 15v65m3-65v65','#eadab6',.8)+line('M45 13h14m-14 6h14',ink,2);},
    model_kit:function(){return rect(12,55,34,28,3,'#c0b89b',ink)+path('M14 56l9-12h34l-12 12Z',cream,ink)+rect(55,27,25,21,4,'#a2b5ad',ink)+rect(61,32,13,6,1,ink)+rect(51,50,33,23,4,green,ink)+path('M50 53l-8 13 7 4 9-13m27-4 8 13-6 4-9-13',purple,ink)+rect(55,73,10,12,2,ink)+rect(72,73,10,12,2,ink)+circle(67,60,5,cream)+line('M67 27v-8',ink,2);},
    journal:function(){return rect(24,15,52,70,5,'#bba9bf',ink)+rect(29,20,42,59,3,'#d6c7d6')+rect(37,31,27,25,2,cream)+line('M43 39h15m-15 6h10',wood,2)+line('M66 17v66','#8d7f9d',3)+repeat(5,function(i){return line('M20 '+(27+i*10)+'h9',ink,2);})+path('M49 80v12l4-4 4 4V80Z',green);},
    music_box:function(){return path('M22 50l5-29h48l5 29Z',wood,ink)+path('M28 46l3-20h40l4 20Z',cream)+rect(19,50,62,35,5,wood,ink)+ellipse(50,55,26,8,'#e0ceb0')+rect(45,71,10,7,2,cream)+line('M54 50V29l13-3v18',ink,2)+ellipse(50,50,5,3,ink)+ellipse(63,44,5,3,ink)+line('M27 78h10m26 0h10','#f0dab5',2);}
  };
  function resolve(item) {
    var id=String(item.possession_id || item.id || ''), name=String(item.name || '');
    // Book identity/category must precede generic words like flower or tea in a title.
    if (item.book_id || /^book_/.test(id) || item.category==='书籍') return 'book';
    if (Object.prototype.hasOwnProperty.call(makers,id)) return id;
    var aliases=[['milk_tea',/奶茶/],['coffee',/咖啡(?!机)/],['juice',/果汁/],['fruit_tea',/果茶/],['flowers',/花束/],['plant',/盆栽|绿植/],['pillow',/抱枕/],['candle',/蜡烛/],['lamp',/台灯/],['book',/手札|小说|绘本/]];
    for(var i=0;i<aliases.length;i++)if(aliases[i][1].test(name))return aliases[i][0];
    return null;
  }
  function draw(item) {
    item=item || {};
    var kind=resolve(item); if(!kind)return null;
    var key='product-'+(++serial), art=kind==='book'?book(item):makers[kind]();
    return '<svg class="item-illustration" data-product-art="'+kind+'" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><defs><radialGradient id="'+key+'"><stop stop-color="#fffdf3"/><stop offset="1" stop-color="#edf1e3" stop-opacity="0"/></radialGradient></defs><title>'+escape(item.name || kind)+'</title>'+ellipse(50,51,47,44,'url(#'+key+')')+ellipse(50,90,32,4,'#59735b18')+art+'</svg>';
  }
  root.ProductArtwork={draw:draw,resolve:resolve};
})(window);
