/* Distinct destination compositions using the same materials as the indoor scenes. */
(function(root){
  'use strict';
  var descriptions={
    cafe:'街角两层坡顶咖啡馆，有拱形落地窗、圆阁窗、侧挂杯形招牌、露天伞桌和手写菜单板',
    bookstore:'窄高三层山墙书店，通高书窗、阁楼老虎窗、门边书箱和阅读小凳',
    museum:'错落的奶油色立方展馆、锯齿玻璃天窗、海报墙与庭前几何雕塑',
    cinema:'阶梯山墙电影院，胶片徽章、灯泡跑马招牌、售票亭和双侧电影海报',
    mall:'弧形玻璃中庭连接两翼商场，三层水平楼带、可见扶梯和宽推拉入口',
    office:'六层细长玻璃办公楼、低层入口裙楼、屋顶天线与整齐绿篱',
    street:'弯曲石板老街，两侧高低木屋、瓦屋顶、二楼木阳台、挂旗和茶摊',
    food:'开放式食堂亭，人字棚下是长服务台、蒸汽锅、菜单和高脚凳',
    supermarket:'宽低商超、蓝绿色雨棚、通宽推拉门、屋顶光伏板和购物车区',
    grocery:'小木杂货亭，敞开的百叶窗、玻璃罐货架、布袋与门边干草束',
    market:'早市的蔬菜、鲜鱼、水果三座帆布摊棚，货筐排列在中央通道两侧',
    nightmarket:'灯笼拱架下的夜市，串烧摊、蒸笼摊、暖灯和露天小桌',
    station:'老车站钟楼和尖顶入口，侧面弧形站台雨棚下停着一截列车',
    airport:'曲面屋顶航站楼、倾斜支柱、独立控制塔和停机坪上的飞机',
    hotel:'L形三层木旅店，连续阳台、入口门廊、花箱和行李推车',
    travel:'异乡石板广场，钟塔、拱廊和左右不同高度的石色建筑',
    temple:'前景鸟居通往多层弧檐神社，石灯笼、注连绳和台阶围着安静前庭',
    onsen:'竹篱围合的岩石露天汤池，小瀑布、氤氲蒸汽与后方木汤屋',
    harbor:'灯塔与港湾码头，系泊渔船、绳桩、浮球和低矮船具仓房',
    mountain:'层叠陡峭山岭、悬空木观景台、索道和小缆车，远处是雾线',
    izakaya:'狭长暗木小酒馆，深瓦檐、格栅纸窗、暖帘、红灯笼与门前木凳',
    transit:'街角公交站，玻璃候车棚、半进入的巴士、交通灯与斑马线',
    generic:'城市公共广场，圆环雕塑、阶梯花坛、自行车架和高低楼群',
    park:'弯曲园路绕过荷塘与六角凉亭，花境、导览牌和树荫长椅',
    beach:'沙丘海岸有救生瞭望亭、条纹遮阳伞、冲浪板、贝壳与层层浪线',
    botanical:'维多利亚式玻璃穹顶温室、低矮侧翼、藤蔓花廊和分层花坛',
    riverside:'细窄曲河上的石拱桥，两侧垂柳与沿河弯步道，岸边有芦苇',
    lakeside:'宽阔湖面、小艇屋、斜向入水的栈桥、划艇和近岸芦苇',
    campsite:'松林草坡上的两顶帐篷、篝火石圈、野餐桌、收纳箱与露营灯串',
    amusement:'摩天轮与旋转木马错落布置，入口售票亭、气球架和彩旗沿路排列',
    flower_shop:'玻璃斜顶小花房，圆窗、藤蔓拱门、阶梯花桶架与门前插花桌',
    bakery:'陡赭色屋顶面包小屋，烟囱、圆烤炉窗、扇贝雨棚和装满面包的推车',
    library:'宽阔公共图书馆，三拱柱廊、中央玻璃天窗、长台阶与书形雕塑'
  };
  function R(x,y,w,h,c,r,a){return '<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(r||0)+'" fill="'+c+'" '+(a||'')+'/>';}
  function P(d,c,a){return '<path d="'+d+'" fill="'+c+'" '+(a||'')+'/>';}
  function L(x,y,a,b,c,w){if(/^url\(/.test(c))c=/metal/.test(c)?'#bdcbb7':/wood/.test(c)?'#b39670':'#9eaf98';return P('M'+x+' '+y+'L'+a+' '+b,'none','stroke="'+c+'" stroke-width="'+(w||1)+'" stroke-linecap="round"');}
  function C(x,y,r,c,a){return '<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+c+'" '+(a||'')+'/>';}
  function E(x,y,w,h,c){return '<ellipse cx="'+x+'" cy="'+y+'" rx="'+w+'" ry="'+h+'" fill="'+c+'"/>';}
  function T(x,y,t,s,c){return '<text x="'+x+'" y="'+y+'" text-anchor="middle" font-family="sans-serif" font-size="'+(s||12)+'" fill="'+(c||'#f6e7c6')+'">'+t+'</text>';}
  function A(x,y,w,h,c){return P('M'+x+' '+(y+h)+'V'+(y+w/2)+'Q'+x+' '+y+' '+(x+w/2)+' '+y+'Q'+(x+w)+' '+y+' '+(x+w)+' '+(y+w/2)+'V'+(y+h)+'Z',c);}
  function draw(key,e,defs){
    if(!descriptions[key])key='generic';
    var b=[defs],wood='url(#garden-wood)',top='url(#garden-woodTop)',glass='url(#garden-glass)',cream='url(#garden-cream)',sage='url(#garden-sage)',fabric='url(#garden-fabric)',metal='url(#garden-metal)',win=e.dark?'#e5c68e':glass;
    var natural=/^(park|beach|botanical|riverside|lakeside|campsite|mountain|onsen|temple|harbor)$/.test(key),wet=/rain|storm/.test(e.weather);
    function window(x,y,w,h,arch){return (arch?A(x-3,y-3,w+6,h+6,wood)+A(x,y,w,h,win):R(x-3,y-3,w+6,h+6,wood,2)+R(x,y,w,h,win,1))+L(x+w/2,y+2,x+w/2,y+h-2,'#ddd8b9',2)+L(x+2,y+h*.52,x+w-2,y+h*.52,'#ddd8b9',2);}
    function door(x,y,w,h,arch){return (arch?A(x-4,y-4,w+8,h+4,wood)+A(x,y,w,h,win):R(x-4,y-4,w+8,h+4,wood,2)+R(x,y,w,h,win,1))+L(x+w/2,y+3,x+w/2,y+h,'#dfd7b8',2)+C(x+w*.76,y+h*.6,2,'#edce98');}
    function sign(x,y,w,label){return R(x,y,w,24,sage,4)+R(x+3,y+3,w-6,18,'none',2,'stroke="#e6d9b1" stroke-opacity=".5"')+T(x+w/2,y+17,label,11);}
    function roof(d){return P(d,'#6d8476','stroke="#d3c29e" stroke-width="3" stroke-linejoin="round"');}
    function plant(x,y,s,flower){return '<g transform="translate('+x+' '+y+') scale('+(s||1)+')">'+E(0,18,13,4,'#30493822')+R(-8,5,16,16,wood,3)+E(0,5,8,3,'#dbc09b')+L(0,6,0,-18,'#567d58',2)+E(-6,-7,5,11,'#6a9e75')+E(6,-13,5,12,'#9db58a')+(flower?C(0,-22,6,flower)+C(0,-22,2,'#edd5a3'):'')+'</g>';}
    function tree(x,y,s,pine){return '<g transform="translate('+x+' '+y+') scale('+(s||1)+')">'+E(0,15,25,5,'#364b3a22')+R(-4,-55,8,72,wood,2)+(pine?P('M-33-18L0-91L33-18Z',sage)+P('M-29-42L0-108L29-42Z','#6e927c'):E(-16,-52,22,31,sage)+E(17,-57,24,34,sage)+E(0,-78,24,31,sage))+L(0,-55,0,5,'#cad0a45c',1)+'</g>';}
    function bench(x,y,w){return R(x,y,w,12,wood,3)+R(x+5,y-25,w-10,17,top,3)+L(x+7,y-17,x+w-7,y-17,'#edd2a066',1)+L(x+9,y+11,x+9,y+31,'#738376',3)+L(x+w-9,y+11,x+w-9,y+31,'#738376',3);}
    function flowerbox(x,y,w){var a=R(x,y,w,19,wood,3)+R(x+3,y+4,w-6,3,'#e2c298',1);for(var z=x+11;z<x+w;z+=21)a+=plant(z,y-9,.6,z%2?'#cba3a9':'#ead1a1');return a;}
    function table(x,y){return E(x,y,31,10,top)+L(x,y+7,x,y+43,'#877c65',4)+L(x,y+42,x-21,y+48,'#877c65',3)+L(x,y+42,x+21,y+48,'#877c65',3)+C(x+6,y-3,6,'#ece5cf');}
    function lantern(x,y){return L(x,y-22,x,y-12,'#6e7361',1)+E(x,y,10,14,'#bd8b83')+R(x-7,y-14,14,3,wood,1)+L(x-4,y-10,x-4,y+10,'#e6b29c',1)+R(x-6,y+13,12,3,top,1);}
    function steam(x,y){return P('M'+x+' '+y+'q-9-9 0-19t0-19m13 39q-8-9 0-20t0-17','none','stroke="#e6e8d2" stroke-opacity=".6" stroke-width="3"');}
    function poster(x,y,w,h,c){return R(x-3,y-3,w+6,h+6,wood,1)+R(x,y,w,h,c,1)+C(x+w*.7,y+h*.25,w*.13,'#dfc89f')+P('M'+x+' '+(y+h*.86)+'l'+w*.35+' -'+h*.35+' '+w*.24+' '+h*.14+' '+w*.41+' -'+h*.32+'V'+(y+h)+'H'+x+'Z','#75948a')+L(x+5,y+h-7,x+w-5,y+h-7,'#e4ddbe',2);}
    // Horizon, ground and paving vary with the destination rather than one shared plaza.
    b.push(R(0,0,600,440,'url(#garden-sky)'));
    if(/clear|wind/.test(e.weather))b.push(C(502,57,e.dark?13:20,e.dark?'#eee9cf':'#fae4ae'));
    if(e.dark&&e.weather==='clear')for(var i=0;i<18;i++)b.push(C(16+(i*61)%570,13+(i*31)%117,i%3===0?1.3:.7,'#f3ead1'));
    if(!e.dark)for(i=0;i<3;i++)b.push('<g opacity=".4">'+E(45+i*218,58+i*12,37,8,'#f1eed9')+E(56+i*218,50+i*12,23,13,'#f1eed9')+'</g>');
    if(natural){b.push(P('M0 224Q81 146 188 207T391 185T600 201V316H0Z','#9eb29b'),P('M0 267Q144 196 290 249T600 229V332H0Z','#829e88'));}
    else {for(i=0;i<10;i++){var bx=i*69-20,bh=42+(i*31)%88;b.push(R(bx,272-bh,57,bh,i%2?'#829a92':'#97aba0',2));for(var sy=285-bh;sy<254;sy+=19)b.push(L(bx+7,sy,bx+46,sy,'#c4cdb263',3));}b.push(P('M0 285Q290 252 600 277V330H0Z','#7e9986'));}
    var lawn=/park|campsite|mountain|temple|onsen/.test(key),sand=key==='beach';
    b.push(R(0,293,600,147,e.weather==='snow'?'#dce7db':sand?'#ead8b4':lawn?'#a9be96':wet?'#b8c9be':'#ddd4ba'));
    if(lawn)b.push(P('M-40 440Q85 351 237 316L272 319Q220 371 279 440Z',e.weather==='snow'?'#c6d6d0':'#c5bea1'));
    else if(!sand){for(var y=322;y<440;y+=28)b.push(L(0,y,600,y,'#8c927a40',.8));for(var x=-190;x<900;x+=86)b.push(L(300+(x-300)*.5,294,x,440,'#8c927a40',.8));}
    b.push(E(482,405,34,6,'#2e483b20'));
    var art=[];
    switch(key){
    case 'cafe':
      art.push(P('M72 154L235 76L386 157V306H72Z',cream),P('M386 157l37 18v131h-37Z','#a69e84'),roof('M54 155L235 65L405 157L389 169L235 91L71 169Z'),R(107,78,21,51,wood,1));
      art.push(C(235,130,24,wood),C(235,130,19,win),L(216,130,254,130,'#e5d4ad',2),L(235,111,235,149,'#e5d4ad',2),window(89,198,71,91,true),window(179,198,71,91,true),door(282,197,66,109,true),sign(141,165,168,'街角咖啡馆'));
      art.push(L(389,173,425,173,'#776d59',3),R(406,180,32,27,cream,4),P('M411 186h16v9q-8 9-16 0Z',wood),P('M427 187q12 0 0 9','none','stroke="#886f51" stroke-width="2"'),table(98,357),L(98,246,98,349,'#a89470',3),P('M41 268Q98 203 155 268Z',sage),R(213,315,39,57,wood,3),R(217,319,31,46,'#4c655c',2),T(232,334,'COFFEE',5),L(223,343,242,343,'#d8d8ba',1),L(223,351,239,351,'#d8d8ba',1),flowerbox(288,310,106));break;
    case 'bookstore':
      art.push(R(103,118,206,193,cream,3),P('M309 118l60 32v161h-60Z','#a7a08a'),roof('M88 120L206 30L326 120Z'),P('M161 89V65L205 34L249 66V90Z',wood),window(177,63,56,29),sign(125,127,162,'纸间 · 书店'),window(120,171,100,123),door(244,205,46,106,true),window(242,160,47,31));
      for(y=185;y<284;y+=29){art.push(R(124,y+17,92,4,wood));for(x=129;x<215;x+=12)art.push(R(x,y,8,17,['#9aae8b','#c9b18b','#b18d92'][x%3],1));}
      art.push(R(78,329,72,27,wood,2),R(83,324,12,20,fabric,1),R(99,318,12,26,sage,1),R(115,321,18,23,cream,1),bench(258,340,59),flowerbox(326,302,60));break;
    case 'museum':
      art.push(R(48,172,135,128,cream,2),R(178,117,162,183,'#dfd7bd',2),R(331,187,108,113,cream,2),P('M178 117l24-31h138v31Z',glass),P('M202 86h36l-14 31h-46Z','#a7bfb6'),R(172,294,180,14,wood,1),door(228,216,59,84),poster(68,202,69,74,'#bac5b1'),poster(352,213,57,61,'#b5a5a7'),sign(202,146,113,'美术馆'));
      art.push(R(93,350,55,21,cream),P('M106 349l-18-38 29-31 32 24-12 45Z',sage),P('M117 280l2 52 30-28Z','#b5c3a5'),L(119,332,106,349,'#e6dfbe',1),R(172,317,174,6,'#d7c7a8',1),flowerbox(356,324,76));break;
    case 'cinema':
      art.push(P('M69 306V143H123V99H174V69H293V99H343V143H401V306Z',cream),R(189,85,90,78,wood,34),C(234,124,31,'#bac1a7'));for(i=0;i<5;i++)art.push(C(234+18*Math.cos(i*1.256),124+18*Math.sin(i*1.256),6,'#64786d'));
      art.push(R(83,170,305,42,wood,4),R(88,175,295,32,'#ddd1af',2),T(235,197,'月 光 电 影 院',18,'#576f65'));for(x=91;x<383;x+=15)art.push(C(x,174,1.8,'#f5d794'),C(x,209,1.8,'#f5d794'));
      art.push(door(194,225,83,81),poster(91,227,51,70,'#a4bbb5'),poster(326,227,51,70,'#bba7a2'),R(150,240,32,66,sage,4),window(155,246,22,26,true),R(144,274,44,6,top,2),R(60,307,350,13,'#baaa89',2),R(88,342,317,6,'#aeb49a',1));break;
    case 'mall':
      art.push(R(35,143,129,163,cream,3),R(328,143,112,163,cream,3),P('M157 306V117Q244 72 333 117V306Z',glass,'stroke="#dbd3b3" stroke-width="5"'));
      for(y=154;y<290;y+=47){art.push(R(41,y,117,8,top,1),R(335,y,100,8,top,1),L(161,y,329,y,'#d9d4b7',5));}for(x=183;x<328;x+=36)art.push(L(x,110,x,303,'#c9d4bc',3));
      art.push(P('M182 255l87-44h21l-88 44Z','#c5cdb4'),P('M198 209l87-43h19l-87 43Z','#c5cdb4'),sign(192,123,109,'生活商场'),door(215,258,65,49),R(29,308,414,10,'#dccbad',2),flowerbox(58,321,74),flowerbox(334,321,74));break;
    case 'office':
      art.push(R(112,32,174,274,glass,3),P('M286 32l51 23v251h-51Z','#698b8c'),R(101,29,189,9,metal,2),R(263,237,159,69,cream,3),door(303,254,80,52),sign(289,225,110,'办公楼'),L(243,32,243,7,'#71887c',3));
      for(y=62;y<295;y+=39)art.push(L(115,y,284,y,'#c1cfb6',3),L(289,y,334,y+18,'#8fa89b',2));for(x=140;x<278;x+=36)art.push(L(x,36,x,304,'#b0c7b3',2));art.push(R(95,307,332,11,'#c9b99a',2),flowerbox(102,338,105),flowerbox(301,338,111));break;
    case 'street':
      art.push(P('M152 440L240 239H288L360 440Z','#cbbfa0'),P('M23 156L138 120L210 157V321H23Z',cream),roof('M11 156L130 107L217 151L205 164L132 126L27 169Z'),R(28,226,178,28,wood),door(66,265,55,57),window(45,176,51,45),window(123,176,50,45));
      for(x=36;x<198;x+=14)art.push(L(x,226,x,254,'#e0c49d',2));art.push(P('M304 182L371 152L439 184V320H304Z',wood),roof('M292 182L372 136L447 183Z'),window(320,202,88,35),door(342,257,47,63),R(201,199,34,59,fabric,2),T(218,219,'茶',14),R(273,224,28,42,sage,1),T(287,243,'布',12));art.push(lantern(52,257),lantern(414,260),table(381,351));break;
    case 'food':
      art.push(L(62,180,62,323,wood,9),L(399,180,399,323,wood,9),roof('M35 183L229 86L430 183L412 199L229 109L55 199Z'),R(89,203,281,42,'#dcd6b8',2),T(230,230,'今 日 食 堂',20,'#5c786a'),R(69,276,325,56,wood,3),R(63,271,337,12,cream,3),R(108,248,61,22,metal,8),steam(127,241),R(271,251,59,20,glass,4));for(x=103;x<376;x+=78)art.push(E(x,352,21,7,sage),L(x,358,x-6,388,'#897b61',3),L(x+10,357,x+17,388,'#897b61',3));art.push(sign(302,244,70,'套餐'));break;
    case 'supermarket':
      art.push(R(38,157,396,150,cream,3),R(34,149,404,20,sage,2),R(49,186,377,27,'#6c9593',2),T(239,205,'日 常 · 生 鲜 商 超',15),window(57,226,89,65),door(169,220,164,87),poster(356,226,54,66,'#a0b694'),R(111,117,220,29,glass,2));for(x=118;x<330;x+=31)art.push(L(x,119,x,144,'#c7d5b7',1));
      for(i=0;i<3;i++)art.push(P('M'+(70+i*18)+' 338h39l-6 24h-29Z','none','stroke="#788f80" stroke-width="2"'),L(65+i*18,331,76+i*18,362,'#788f80',2),C(80+i*18,370,4,'#667c72'),C(100+i*18,370,4,'#667c72'));art.push(flowerbox(344,317,82));break;
    case 'grocery':
      art.push(R(100,155,245,154,wood,3),roof('M79 159L224 98L367 159L354 175H91Z'),R(118,190,129,73,'#4d685b',2),R(94,185,19,86,sage,2),R(252,185,19,86,sage,2),door(286,199,39,110),sign(130,161,167,'巷口杂货铺'));for(y=202;y<256;y+=25){art.push(R(120,y+18,125,4,top));for(x=129;x<240;x+=24)art.push(R(x,y,14,17,glass,3),R(x+1,y-3,12,3,cream,1));}
      art.push(R(117,267,132,12,top,2),E(175,338,31,24,'#c4b79a'),L(167,315,180,315,'#7a775f',2),P('M351 266q-27-36-9-53m9 53q-2-31 18-48','none','stroke="#c7b48b" stroke-width="3"'),flowerbox(281,327,80));break;
    case 'market':
      for(i=0;i<3;i++){var mx=31+i*139,my=i===1?202:188;art.push(L(mx+5,my+10,mx+5,315,wood,4),L(mx+119,my+10,mx+119,315,wood,4),P('M'+(mx-5)+' '+(my+12)+'l18-44h98l18 44Z',i===1?fabric:sage),R(mx+2,my+13,122,9,cream,2),R(mx+9,272,107,43,wood,2));for(x=mx+17;x<mx+106;x+=23)art.push(R(x,261,20,17,top,1),i===1?E(x+10,268,9,3,glass):C(x+10,264,7,i===2?'#cea277':'#8fa16f'));art.push(T(mx+63,my+6,['菜蔬','鲜鱼','水果'][i],11));}art.push(R(56,337,58,28,wood,2),R(361,337,53,27,wood,2),P('M160 440L201 324H258L298 440Z','#ddd0af'));break;
    case 'nightmarket':
      art.push(L(38,122,38,327,wood,7),L(424,122,424,327,wood,7),P('M24 123Q230 153 438 123','none','stroke="#b99c74" stroke-width="6"'));for(x=67;x<425;x+=49)art.push(lantern(x,161+(x%3)*8));
      for(i=0;i<2;i++){x=66+i*211;art.push(R(x,229,129,87,wood,4),P('M'+(x-9)+' 230l18-30h110l20 30Z',i?fabric:sage),R(x+6,264,116,10,top,2),sign(x+20,235,86,i?'蒸笼小食':'炭火串烧'));if(i)art.push(E(x+62,287,33,10,'#bfa678'),R(x+29,277,66,10,'#cbb48d',3),steam(x+57,265));else for(var q=0;q<5;q++)art.push(L(x+20+q*18,276,x+29+q*18,296,'#e4cc9d',2),C(x+23+q*18,284,5,'#ba987c'));}art.push(table(232,360),R(355,345,50,17,wood,3));break;
    case 'station':
      art.push(R(42,186,222,121,cream,3),R(101,94,93,213,cream,2),roof('M85 96L147 34L210 96Z'),C(147,136,28,wood),C(147,136,23,'#ece4ca'),L(147,136,147,119,'#687c6c',2),L(147,136,159,144,'#687c6c',2),door(119,220,57,87,true),window(58,225,36,52,true),window(207,225,36,52,true),sign(107,177,80,'山间站'));
      art.push(P('M265 222Q340 127 431 220V229H265Z',glass,'stroke="#d7d4b2" stroke-width="4"'),L(276,228,276,313,metal,5),L(422,228,422,313,metal,5),R(281,251,146,55,sage,11));for(x=291;x<424;x+=35)art.push(R(x,261,26,22,glass,3));art.push(L(266,321,438,321,'#716c5e',3),L(266,333,438,333,'#716c5e',3),R(34,308,223,11,'#c7b594',2),bench(285,354,109));break;
    case 'airport':
      art.push(R(40,192,321,99,glass,3),P('M26 194Q136 114 383 165L359 193Q176 158 26 214Z',cream,'stroke="#d3cfb5" stroke-width="2"'));for(x=61;x<355;x+=48)art.push(L(x,202,x-12,292,metal,5));art.push(R(28,289,339,15,metal,2),sign(137,205,155,'航 站 楼'),R(393,129,21,160,cream),P('M374 129l-8-49h76l-8 49Z',glass,'stroke="#d9d5b5" stroke-width="4"'),R(369,73,70,7,metal,2),L(405,72,405,46,'#7a8f83',3));
      art.push(R(0,320,600,120,'#8c9b94'),L(24,397,426,397,'#e3d5b0',3),P('M71 351q18-10 100-6l75-32 16 3-42 34 90 4q17 6-2 12l-94 1 37 32-15 2-69-33-58 1-18 16-12-1 6-20-15-5Z',cream,'stroke="#9aab9b" stroke-width="1.5"'));break;
    case 'hotel':
      art.push(R(49,124,226,183,wood,3),R(275,164,135,143,cream,3),roof('M33 125L163 72L290 125Z'),roof('M266 166L342 126L424 166Z'));
      for(y=147;y<274;y+=57){for(x=68;x<260;x+=65)art.push(window(x,y,39,34));art.push(R(57,y+38,212,6,top),L(59,y+24,266,y+24,metal,2));for(x=65;x<262;x+=19)art.push(L(x,y+24,x,y+38,metal,1.4));}art.push(door(316,238,55,69),P('M289 238l55-36 54 36Z',sage),L(299,237,299,308,wood,4),L(389,237,389,308,wood,4),sign(90,95,144,'风 居 旅 店'),flowerbox(294,314,113),R(75,341,58,31,fabric,4),L(67,323,67,375,metal,3),L(67,375,145,375,metal,3),C(80,380,5,'#6e7b6d'),C(136,380,5,'#6e7b6d'));break;
    case 'travel':
      art.push(R(38,158,120,148,'#d0b79c',2),R(310,123,121,183,cream,2),R(197,69,67,236,cream,2),roof('M184 71L230 20L277 71Z'),C(230,111,19,'#e9e3c9'),L(230,111,230,98,'#738474',2),L(230,111,241,118,'#738474',2));
      for(x=49;x<422;x+=63){if(x>157&&x<310)continue;art.push(door(x,245,40,61,true),window(x,181,38,37));}art.push(P('M140 310L190 272H275L327 310Z','#baad91'),R(192,307,79,11,top,2),P('M180 440L217 320H252L301 440Z','#d9cbb0'),flowerbox(35,325,90),bench(326,343,90));break;
    case 'temple':
      art.push(R(114,191,223,106,wood,2),roof('M88 193Q148 174 224 119Q303 174 363 193L345 209H106Z'),roof('M143 128Q187 113 224 80Q260 113 306 128L293 138H156Z'),R(161,216,46,81,'#6f8270'),R(244,216,46,81,'#6f8270'),P('M131 220Q224 240 321 220','none','stroke="#c9b287" stroke-width="4"'),R(108,298,238,13,'#bda884',1),R(92,311,270,12,'#d9c8a5',1));
      art.push(L(66,175,66,347,'#b98b79',10),L(382,175,382,347,'#b98b79',10),P('M40 165Q225 186 409 165','none','stroke="#b98b79" stroke-width="12"'),L(54,199,395,199,'#b98b79',7));for(x=103;x<370;x+=252)art.push(R(x,307,13,42,'#a8af9b',2),R(x-8,288,29,20,cream,2),roof('M'+(x-13)+' 288l19-17 19 17Z'));art.push(tree(16,280,1.1,true),tree(443,275,1,true));break;
    case 'onsen':
      for(x=47;x<431;x+=17)art.push(R(x,166,12,151,sage,4),L(x,213,x+10,213,'#b7c29c',1));art.push(R(280,160,138,113,wood,3),roof('M263 162L350 107L435 162Z'),R(314,194,53,79,fabric,1),T(340,224,'湯',25,'#e6d7b3'));
      art.push(E(215,330,178,62,'#9aa58d'),E(215,325,152,44,glass),E(215,321,139,31,'#bddad255'));for(i=0;i<12;i++)art.push(E(215+166*Math.cos(i*.524),330+49*Math.sin(i*.524),20+(i%3)*3,12+(i%2)*5,'#afb39c'));art.push(P('M83 283q15-47 28 0v33H83Z','#a6ad96'),P('M91 282q9 22 2 38','none','stroke="#d4e3d1" stroke-width="6"'),steam(169,300),steam(249,288),R(364,354,31,29,wood,5));break;
    case 'harbor':
      art.push(R(0,243,600,134,glass),P('M0 351L331 322L407 440H0Z',wood));for(y=360;y<440;y+=21)art.push(L(0,y,377,y,'#d3b68b80',1));art.push(P('M61 271L77 117H116L132 271Z',cream),R(77,155,41,23,'#a78f87'),R(74,112,45,34,glass,2),roof('M66 112L96 85L127 112Z'),R(64,146,66,6,metal,1),R(91,237,14,34,wood,2),R(288,207,123,73,wood,2),roof('M273 209L346 167L426 209Z'),door(326,237,43,43));
      art.push(P('M177 281l126 4-21 30h-83Z',cream),R(214,252,49,31,sage,3),window(220,258,35,17),L(249,251,249,200,wood,2),L(249,201,285,226,'#b9c8ae',1),P('M249 207l37 20h-37Z',fabric));for(x=35;x<315;x+=80)art.push(R(x,328,9,35,wood,2),P('M'+(x+4)+' 335q40 19 80-8','none','stroke="#e0cea7" stroke-width="2"'));art.push(C(199,304,9,'none','stroke="#6e847a" stroke-width="5"'),C(284,301,8,'none','stroke="#6e847a" stroke-width="5"'));break;
    case 'mountain':
      art.push(P('M0 278L132 95L232 239L341 53L499 268L570 151L600 270V319H0Z','#739386'),P('M72 178l60-83 49 71-40-15-18 28-15-11Z','#d3dfcf'),P('M288 131l53-78 61 83-42-12-19 20-19-25Z','#d3dfcf'),P('M0 317L138 188L243 296L351 151L481 315Z','#56796e'));
      art.push(P('M30 356L287 276L400 331L137 422Z',wood),P('M30 344L287 265L400 319','none','stroke="#dfc9a3" stroke-width="4"'));for(i=0;i<6;i++)art.push(L(47+i*48,340-i*15,47+i*48,365-i*14,'#c5b590',3));art.push(L(11,127,432,53,'#667d75',2),L(245,86,245,110,'#7c9488',3),R(220,110,51,44,cream,8),R(226,117,39,22,glass,3),L(246,118,246,138,'#c6d3b7',2),bench(196,342,82));break;
    case 'izakaya':
      art.push(R(88,170,267,141,wood,2),roof('M61 173L220 100L382 173L364 195H78Z'),R(108,207,92,80,'#d9d2ac',2));for(x=114;x<199;x+=13)art.push(L(x,208,x,287,'#7c7055',3));art.push(door(236,211,65,100),R(226,205,86,38,fabric,1),L(254,205,254,243,'#dfb7b4',1),L(284,205,284,243,'#dfb7b4',1),T(267,228,'小酒馆',12),lantern(78,231),lantern(366,231),bench(102,337,106),R(326,316,42,47,wood,5),R(331,327,32,7,'#aeb99b',2),R(331,347,32,5,'#aeb99b',2));break;
    case 'transit':
      art.push(R(0,319,600,121,'#87988f'));for(x=26;x<300;x+=40)art.push(P('M'+x+' 386l14-22h24l-9 22Z','#e1ddc2'));art.push(R(229,190,171,119,glass,3),P('M215 190l15-15h178l13 15Z',metal),L(235,191,235,308,metal,5),L(397,191,397,308,metal,5),bench(255,291,113),R(405,218,19,61,cream,2),T(414,237,'BUS',6),R(-44,237,225,93,sage,14),R(-32,248,200,40,glass,6),L(111,248,111,325,'#c9d8be',3),C(27,330,18,'#566c61'),C(144,330,18,'#566c61'),C(27,330,8,'#cdd3ba'),C(144,330,8,'#cdd3ba'),L(438,207,438,334,'#708576',4),R(427,186,22,59,'#4a635b',5),C(438,198,5,'#ba8e84'),C(438,216,5,'#c6b98a'),C(438,234,5,'#a8bd88'));break;
    case 'generic':
      art.push(R(46,305,127,15,'#a7af97',2),R(59,293,101,13,'#c2c7ab',2),flowerbox(72,278,77),R(221,320,90,17,cream,2),E(266,246,45,70,'none').replace('/>',' stroke="#a4b5a0" stroke-width="14" transform="rotate(24 266 246)"/>'),R(248,303,36,16,wood,2),bench(331,331,88));for(x=57;x<160;x+=34)art.push(P('M'+x+' 381v-22q14-20 25 0v22','none','stroke="#6c8b80" stroke-width="3"'));art.push(tree(18,289,1.1),tree(441,290,1.05));break;
    case 'park':
      art.push(E(162,322,114,33,glass),E(162,318,102,25,'#a5c9ba77'));for(x=90;x<234;x+=38)art.push(E(x,316+(x%3)*4,11,4,sage),C(x+3,311,4,'#d0abb5'));art.push(L(311,211,311,311,wood,5),L(400,211,400,311,wood,5),L(357,202,357,288,wood,4),roof('M286 215L355 152L426 215L408 226H301Z'),L(309,272,403,272,'#d7c6a4',3),bench(309,288,95),tree(43,278,1.3),tree(258,260,.85),flowerbox(40,370,93),R(260,309,8,50,wood,1),sign(236,289,60,'园区导览'));break;
    case 'beach':
      art.push(R(0,218,600,125,glass));for(y=245;y<335;y+=26)art.push(P('M0 '+y+'q75-13 150 0t150 0t150 0t150 0','none','stroke="#d1e0cf" stroke-width="2"'));art.push(P('M0 345Q147 300 315 347T600 330V440H0Z','#ddc9a2'),L(310,239,300,354,wood,5),L(383,239,397,354,wood,5),R(301,192,90,64,cream,2),roof('M287 192L344 150L403 192Z'),window(318,210,54,29),P('M315 264l59 94m-70-77h25m-15 16h25m-15 16h25m-15 16h25','none','stroke="#b39a74" stroke-width="3"'),L(121,252,121,363,wood,3),P('M53 263Q120 182 190 263Z',sage),P('M91 263Q120 183 151 263Z',fabric),R(61,374,132,28,fabric,3),E(244,357,10,49,cream),L(244,313,244,400,'#9cbaaa',2),P('M27 415q7-16 16 0Z','#e3d7bc'));break;
    case 'botanical':
      art.push(R(39,219,103,90,glass,2),R(318,219,112,90,glass,2),P('M142 309V177Q142 72 229 72Q318 72 318 177V309Z',glass,'stroke="#e0d9b8" stroke-width="5"'),P('M30 219l53-41 59 41Z',glass,'stroke="#d4d6b6" stroke-width="3"'),P('M318 219l56-41 65 41Z',glass,'stroke="#d4d6b6" stroke-width="3"'),R(216,52,27,19,glass,3),P('M210 52l19-15 20 15Z',cream));
      for(x=155;x<318;x+=25)art.push(P('M'+x+' 309V'+(88+Math.abs(229-x)*.78),'none','stroke="#d6d7b8" stroke-width="2"'));for(y=177;y<305;y+=44)art.push(L(143,y,316,y,'#d7d8b7',2));for(x=51;x<430;x+=28)if(x<142||x>318)art.push(L(x,220,x,309,'#d6d7b8',2));art.push(door(207,225,46,84,true),sign(186,193,88,'植物温室'),plant(176,277,1.3),plant(283,276,1.5),plant(74,276,1.1),plant(384,276,1.1),R(34,310,401,10,'#c6bb9b',2),flowerbox(43,333,113),flowerbox(302,333,113),P('M172 352V304q58-40 116 0v48','none','stroke="#8da383" stroke-width="4"'));for(x=179;x<285;x+=21)art.push(E(x,299+(x%3)*4,8,4,'#9eb68b'));break;
    case 'riverside':
      art.push(P('M385 225Q167 261 249 324T138 440H305Q452 380 341 321T470 225Z',glass),P('M364 223Q144 254 221 326T96 440H130Q301 366 244 323T388 223Z','#c5c0a0'),P('M158 320Q259 211 368 302L372 316Q258 248 169 335Z','#c6b89a'),P('M156 307Q257 199 369 290','none','stroke="#d7c7a4" stroke-width="5"'));for(i=0;i<8;i++)art.push(L(164+i*28,301-Math.sin(i/7*Math.PI)*47,169+i*27,321-Math.sin(i/7*Math.PI)*39,'#a59a7d',3));art.push(tree(63,279,1.3));for(x=31;x<110;x+=13)art.push(P('M62 189Q'+x+' 213 '+x+' 276','none','stroke="#83a486" stroke-width="4"'));art.push(bench(338,354,88));for(x=115;x<162;x+=13)art.push(L(x,390,x+4,353,'#7f9a70',2),E(x+4,351,3,7,'#ad9871'));break;
    case 'lakeside':
      art.push(R(0,229,600,161,glass));for(x=14;x<590;x+=49)art.push(L(x,264+x%27,x+29,264+x%27,'#cadfcd80',1));art.push(R(52,223,118,79,wood,2),roof('M36 225L108 169L187 225Z'),R(81,247,57,55,glass,2),P('M145 440L217 314H279L264 440Z',wood));for(y=328;y<440;y+=18)art.push(L(211-(y-328)*.55,y,280-(y-328)*.1,y,'#dfc29880',1));art.push(L(218,308,165,412,'#cbb38c',3),L(273,308,270,412,'#cbb38c',3));for(y=319;y<419;y+=29)art.push(L(216-(y-319)*.5,y,216-(y-319)*.5,y+23,wood,4),L(274,y,274,y+23,wood,4));art.push(P('M309 292q39-21 83-2l-15 19h-52Z',wood),L(340,284,377,317,'#dfc6a0',3),L(397,284,370,319,'#dfc6a0',3));for(x=49;x<126;x+=16)art.push(L(x,416,x+5,369,'#738f70',2),E(x+5,366,3,8,'#b19c75'));break;
    case 'campsite':
      art.push(tree(34,278,1.45,true),tree(132,250,.95,true),tree(358,256,1.05,true),tree(439,281,1.3,true),P('M39 330L141 167L254 330Z',fabric),P('M141 167l28 163h85Z',sage),P('M97 330l44-83 30 83Z','#596e5e'),L(29,337,263,337,'#dcc49b',2),P('M294 308l51-84 72 84Z',sage),P('M322 308l24-47 24 47Z','#557166'),L(281,310,430,310,'#dcc49b',2),R(287,347,124,12,wood,3),L(308,358,298,397,wood,5),L(391,358,401,397,wood,5),R(282,380,135,7,top,2),R(333,319,32,25,sage,4));
      art.push(E(211,383,38,12,'#8a8c72'));for(i=0;i<9;i++)art.push(E(211+34*Math.cos(i*.698),381+12*Math.sin(i*.698),7,5,'#b4b59e'));art.push(L(196,382,225,374,wood,6),L(201,371,227,384,wood,6),P('M203 378q-8-13 7-30-2 16 10 20 8-3 5-9 15 20-8 25Z','#d8b17e'),P('M71 151Q220 197 409 148','none','stroke="#6b7e69" stroke-width="1.5"'));for(x=93;x<408;x+=41)art.push(C(x,160+Math.sin((x-70)/340*Math.PI)*21,3,'#f0d39c'));break;
    case 'amusement':
      art.push(P('M75 321L159 161L239 321','none','stroke="#a29170" stroke-width="7"'),'<g class="ferris-wheel" style="transform-origin:159px 161px">'+C(159,161,96,'none','stroke="#e0d5b4" stroke-width="5"'));for(i=0;i<8;i++){var angle=i*Math.PI/4,px=159+96*Math.cos(angle),py=161+96*Math.sin(angle);art.push(L(159,161,px,py,'#d5cfb0',2),R(px-12,py-4,24,22,i%2?fabric:sage,5),R(px-8,py,16,11,glass,2));}art.push('</g>',E(350,321,82,14,wood),P('M270 225L350 159L431 225Z',sage),P('M313 225L350 159L389 225Z',fabric),R(271,225,157,10,cream,4),L(350,233,350,312,metal,5));for(x=291;x<423;x+=49)art.push(L(x,235,x,307,metal,2),P('M'+(x-14)+' 278h22l8-8 7 3-4 12h-20l-5 11h-4l-1-13Z',cream));art.push(R(271,309,158,11,top,3),R(75,328,59,53,cream,3),roof('M65 328l40-38 40 38Z'),window(86,340,36,20),sign(82,368,46,'票务'));for(i=0;i<4;i++)art.push(L(397,380,390+i*12,329,'#a19779',1),E(384+i*13,319-i%2*13,10,15,i%2?fabric:sage));break;
    case 'flower_shop':
      art.push(R(112,159,240,147,cream,3),P('M101 161L176 96H285L365 161Z',glass,'stroke="#dbd2b1" stroke-width="4"'));for(x=136;x<342;x+=34)art.push(L(x,159,176+(x-136)*.55,99,'#c7d0b0',2));art.push(C(170,195,22,wood),C(170,195,17,win),door(257,210,55,96,true),window(127,232,84,54),sign(162,161,138,'四 季 花 房'),P('M245 307V215Q282 166 322 215V307','none','stroke="#8aab84" stroke-width="6"'));for(i=0;i<6;i++)art.push(plant(243+i*15,200+Math.abs(2.5-i)*7,.5,i%2?'#d3a7b5':'#e3ca9a'));
      art.push(R(56,332,132,12,wood,2),R(69,309,108,9,wood,2),R(82,288,82,7,wood,2));for(i=0;i<9;i++)art.push(plant(65+(i%4)*31,315-Math.floor(i/4)*21,.8,i%2?'#cca3b1':'#e9cd9f'));art.push(table(361,354),flowerbox(257,323,67));break;
    case 'bakery':
      art.push(R(75,169,310,137,cream,3),P('M67 171L159 65H298L397 171Z','#b18c71','stroke="#d2b390" stroke-width="3"'),R(312,77,24,61,wood,2),R(308,73,32,8,top,1),C(164,219,38,wood),C(164,219,32,win),R(99,254,128,10,top,2),door(281,206,65,100,true),sign(143,156,175,'麦 香 面 包 房'),P('M91 180h146l13 23q-9 12-19 0-10 12-19 0-10 12-19 0-10 12-19 0-10 12-19 0-10 12-19 0-10 12-19 0-10 12-21 0Z',sage));for(x=137;x<198;x+=25)art.push(E(x,240,12,8,'#dec08f'),L(x-4,236,x+3,244,'#a1845d',1));
      art.push(R(77,326,127,42,wood,3),R(70,319,141,10,top,2),C(94,375,10,'#7a826d'),C(188,375,10,'#7a826d'));for(x=91;x<200;x+=27)art.push(E(x,312,11,8,'#d8b782'),L(x-4,307,x+2,314,'#a48a60',1));art.push(flowerbox(294,325,103));break;
    case 'library':
      art.push(R(41,156,394,149,cream,3),P('M140 155l51-64h99l53 64Z',glass,'stroke="#d5d3b3" stroke-width="3"'),R(30,154,417,13,top,2),R(46,197,383,9,wood,1),sign(174,167,131,'城 市 图 书 馆'));for(x=82;x<418;x+=119)art.push(door(x,220,71,86,true),R(x-15,206,10,99,metal,2));art.push(R(35,307,410,11,'#b9ab8e',2),R(24,318,430,11,'#cbbd9f',2),R(13,329,452,11,'#ddcfb1',2),R(77,360,66,16,wood,2),P('M87 359v-51q20-7 36 7v46q-20-12-36-2Z',cream),P('M123 315q17-14 34-8v51q-18-5-34 3Z','#c8d0b5'),L(123,315,123,361,'#a3906b',2),flowerbox(337,356,95));break;
    }
    // Small details share the scene's perspective and stay behind the character.
    var detail=[];
    function bloom(x,y,color){return L(x,y+10,x,y,'#72906d',1.2)+P('M'+x+' '+(y+7)+'q-7-8-10-4 2 6 10 4','#94ac80')+C(x-3,y,3,color)+C(x+3,y,3,color)+C(x,y-3,3,color)+C(x,y+3,3,color)+C(x,y,1.5,'#f5e5b4');}
    function flowers(x,y,count){for(var f=0;f<count;f++)detail.push(bloom(x+f*10,y+(f%3)*3,['#ddbacb','#e6cf9d','#baaaca'][f%3]));}
    function bollard(x,y){detail.push(R(x-3,y-34,6,34,'#718575',2),R(x-5,y-36,10,9,'#f1dfaa',2));if(e.dark)detail.push(E(x,y-31,24,35,'url(#garden-warm)'));}
    if(/cafe|bakery|bookstore|flower_shop/.test(key)){
      detail.push(P('M78 174Q235 188 387 174','none','stroke="#747e63" stroke-width="1"'));
      for(var lx=91;lx<381;lx+=26){var ly=175+Math.sin((lx-78)/310*Math.PI)*9;detail.push(L(lx,ly,lx,ly+5,'#8b8b6f',1),C(lx,ly+7,2.6,e.dark?'#ffe3a1':'#e4d4aa'));}
      flowers(292,304,8);
      detail.push(P('M184 406q31-15 63-4','none','stroke="#e5dbbf" stroke-width="3" stroke-linecap="round"'));
      if(key==='cafe')detail.push(E(98,349,9,3,'#f7efda'),R(94,340,8,8,'#f5eddb',2),P('M102 342q7-1 0 5','none','stroke="#f5eddb" stroke-width="1.5"'));
      if(key==='bookstore')detail.push(R(18,364,41,8,'#b89670',2),R(22,358,34,6,'#c8b0bf',1),R(25,352,30,6,'#b4c49c',1));
    }
    if(key==='botanical'){
      detail.push(P('M115 258Q238 204 357 260','none','stroke="#eaf2e2" stroke-opacity=".25" stroke-width="3"'),P('M160 124L207 287M179 112L224 287','none','stroke="#f9fff0" stroke-opacity=".23" stroke-width="10"'));
      flowers(51,337,10);flowers(287,343,8);bollard(30,396);bollard(407,391);
    }
    if(/park|riverside|lakeside/.test(key)){
      flowers(16,385,8);flowers(324,404,7);
      for(var ripple=0;ripple<5;ripple++)detail.push(P('M'+(163+ripple*27)+' '+(329+(ripple%2)*9)+'q8 3 17 0','none','stroke="#e4f0dc88" stroke-width="1"'));
      if(key==='park')detail.push(P('M215 360q-12-14-19-5 0 11 19 5 8-12 17-8-1 10-17 8','none','stroke="#d8afbd" stroke-width="2"'));
    }
    if(key==='campsite'){
      detail.push(R(306,338,14,7,'#eee5cc',2),L(309,339,317,343,'#d0b78b',1),R(371,333,17,10,'#aa8e78',2),R(376,328,7,6,'#d4b59b',1));
      for(var ember=0;ember<5;ember++)detail.push(C(207+ember*4,352-ember*9,1.2,'#eed7a3','class="detail-ember" style="animation-delay:'+ember*.3+'s"'));
    }
    if(/beach|harbor/.test(key)){
      detail.push(P('M322 92q7-7 14 0 7-7 14 0M402 114q5-5 10 0 5-5 10 0','none','stroke="#fff7e2" stroke-width="2" stroke-linecap="round"'));
      if(key==='beach')for(var shell=0;shell<5;shell++)detail.push(P('M'+(50+shell*38)+' '+(397-shell%2*13)+'q-7-9 0-12 9 1 8 10Z','#f0e0c4','stroke="#bbaa8a" stroke-width=".6"'));
    }
    if(/museum|library|cinema|mall|office|station/.test(key)){
      bollard(35,387);bollard(417,385);
      detail.push(P('M166 395h139','none','stroke="#f0e6cc" stroke-width="2" stroke-dasharray="20 5"'));
      if(/museum|library/.test(key))flowers(333,350,7);
    }
    if(key==='temple')detail.push(P('M80 391q31-9 62 0m138 7q31-9 62 0','none','stroke="#a1b293" stroke-width="3"'),R(195,351,45,6,'#e9dfbd',1));
    if(key==='onsen')for(var r=0;r<5;r++)detail.push(P('M'+(146+r*35)+' '+(344+r%2*15)+'q14 5 28 0','none','stroke="#deebd788" stroke-width="1.4"'));
    art.push('<g class="destination-details" pointer-events="none">'+detail.join('')+'</g>');
    b.push('<g class="destination-landmarks" data-design="'+key+'">'+art.join('')+'</g>');
    if(natural&&key!=='beach'&&key!=='harbor')b.push(tree(577,289,1.1,key==='mountain'||key==='campsite'));
    if(!/beach|harbor|airport|lakeside/.test(key))b.push(plant(567,390,.9));
    if(e.weather==='snow')b.push(P('M0 414Q78 402 137 416T285 419T600 414V440H0Z','#e7eee2'),E(68,322,37,5,'#e4ecdf'),E(391,326,32,5,'#e4ecdf'));
    if(e.dark)b.push(R(0,0,600,440,'#142a3c',0,'opacity=".26"'),E(232,275,200,159,'url(#garden-warm)'));
    else if(e.band==='dusk')b.push(R(0,0,600,440,'#d9a475',0,'opacity=".08"'));
    if(wet)b.push(E(174,397,60,5,'#d0ddd13b'),E(359,374,37,4,'#d0ddd13b'));
    if(/rain|storm|fog/.test(e.weather))b.push(R(0,0,600,440,'#617f82',0,'opacity=".1"'));
    return '<svg class="destination-art unified-art" data-destination="'+key+'" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'+b.join('')+'</svg>';
  }
  root.DestinationArt={draw:draw,descriptions:descriptions};
})(typeof window==='undefined'?globalThis:window);
