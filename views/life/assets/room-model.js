/* One physical layout for the floor plan, perspective view and spatial validation. */
(function(root){
  'use strict';
  var plan={
    sofa:[18,71,57,130],tv:[283,99,6,87,'media_console'],coffee_table:[112,112,64,40],record_player:[126,47,27,25,'record_console'],game_console:[269,161,13,23,'media_console'],board_game:[130,122,20,19,'coffee_table'],floor_lamp:[81,76,18,21],yoga_mat:[184,162,77,33],piano:[188,38,85,35],aquarium:[22,39,76,27,'aquarium_console'],
    bathtub:[14,43,108,48],shower:[128,43,38,61],bath_salts:[105,51,14,15,'bath_ledge'],waterproof_speaker:[23,172,13,16,'vanity_counter'],face_mask:[20,121,21,14,'vanity_counter'],bath_towel:[163,129,8,35,'wall'],
    fridge:[15,37,38,43],coffee_machine:[70,46,17,21,'kitchen_north'],pour_over:[105,49,12,15,'kitchen_north'],oven:[210,91,37,43,'kitchen_right'],toaster:[133,47,20,17,'kitchen_north'],dining_table:[15,153,70,38],recipe_book:[172,48,21,16,'kitchen_north'],tea_set:[37,165,28,16,'dining_table'],rice_cooker:[219,185,18,19,'kitchen_right'],dishwasher:[210,145,37,34,'kitchen_right'],
    dining_room_table:[116,102,98,58],sideboard:[290,73,32,94],
    treadmill:[25,56,50,103],dumbbells:[151,161,27,14,'weights_rack'],fitness_mirror:[126,37,108,8,'wall'],
    balcony_chair:[49,81,53,55],plants:[70,40,86,23],watering_can:[129,73,21,22],wind_chime:[134,34,16,22,'ceiling'],telescope:[103,145,43,53],blanket:[60,105,31,14,'balcony_chair'],washing_machine:[17,170,36,37],iron:[23,178,23,15,'washing_machine'],
    shoe_cabinet:[74,15,94,28],umbrella:[199,14,23,29],key_tray:[133,23,26,17,'shoe_cabinet'],vacuum:[292,14,23,29],sewing_kit:[365,24,35,23,'hall_shelf'],delivery_box:[413,18,33,28],
    bed:[40,52,101,114],wardrobe:[195,41,88,33],bedside_lamp:[160,57,17,17,'nightstand'],vanity_mirror:[254,88,30,67],aroma_diffuser:[156,78,11,11,'nightstand'],plush:[60,127,21,25,'bed'],bedtime_book:[171,76,13,15,'nightstand'],
    dressing_mirror:[14,89,8,65,'wall'],accessory_cabinet:[81,42,85,33],
    bookshelf:[18,40,76,29],desk:[105,64,141,59],desk_lamp:[112,69,14,14,'desk'],monitor:[152,72,40,8,'desk'],keyboard:[159,99,27,10,'desk'],notebook:[116,89,24,16,'desk'],camera:[217,76,10,9,'desk'],headphones:[218,99,12,12,'desk'],
    art_easel:[26,48,51,55],paint_cart:[103,57,36,32],digital_tablet:[218,79,45,26,'art_workbench'],
    cinema_screen:[29,3,181,7,'wall'],cinema_sofa:[52,140,136,57],popcorn_machine:[199,85,27,33,'popcorn_console'],
    terrace_swing:[55,100,95,55],flower_bed:[15,196,138,23],bbq_grill:[116,38,35,44],
    stairs:[530,8,225,50],storage_bench:[75,15,113,28]
  };
  var facing={sideboard:'W',sofa:'E',tv:'W',cinema_sofa:'N',cinema_screen:'S',monitor:'S',digital_tablet:'S',wardrobe:'S',bookshelf:'S',bed:'S',desk:'S',dressing_mirror:'E',fitness_mirror:'S',vanity_mirror:'W',balcony_chair:'E',telescope:'E',washing_machine:'E',fridge:'S',oven:'W',dishwasher:'W',bbq_grill:'S',treadmill:'N',stairs:'E'};
  var height={bed:27,sofa:45,cabinet:56,jewelry:53,fridge:96,bookshelf:108,tub:30,shower:108,table:23,dining:38,desk:37,monitor:34,screen:53,mirror:95,aquarium:29,plants:30,rockingchair:45,lamp:27,floorlamp:82,record:7,piano:62,keyboard:2,easel:83,treadmill:63,stairs:104,swing:98,telescope:67,mat:1,towel:2,book:2,box:23,board:3,vanity:72,weights:9,bear:14,headphones:8,washer:43,oven:43,dishwasher:43,coffee:21,speaker:12,popcorn:36,grill:48,toaster:14,console:5,tea:8,keys:3,camera:13,iron:8,ricecooker:14,pourover:18,wateringcan:16,diffuser:12,jar:12,mask:2,chime:27,umbrella:40,vacuum:57,paints:48};
  var itemHeight={wardrobe:105,shoe_cabinet:44,storage_bench:23,sideboard:43,tv:48,digital_tablet:24};
  function fixture(id,x,y,w,d,h,type,face){return {id:id,x:x,y:y,w:w,d:d,h:h,type:type||'counter',facing:face||'S'};}
  var fixtures={
    客厅:[fixture('record_console',116,39,48,38,36),fixture('aquarium_console',20,37,80,31,45),fixture('media_console',264,88,26,108,29,'counter','W'),fixture('piano_bench',205,85,44,16,23,'bench')],
    浴室:[fixture('vanity_counter',14,116,42,80,43,'basin','E'),fixture('bath_ledge',102,45,20,30,31,'ledge')],
    厨房:[fixture('kitchen_north',60,37,187,39,45),fixture('kitchen_right',210,76,37,132,45,'counter','W'),fixture('kitchen_sink',200,43,40,27,46,'sink'),fixture('kitchen_chair',89,157,20,26,43,'chair','W')],
    餐厅:[fixture('dining_chair_l1',94,107,19,20,43,'chair','E'),fixture('dining_chair_l2',94,138,19,20,43,'chair','E'),fixture('dining_chair_r1',217,107,19,20,43,'chair','W'),fixture('dining_chair_r2',217,138,19,20,43,'chair','W')],
    健身室:[fixture('weights_rack',131,150,71,35,28,'bench')],
    卧室:[fixture('nightstand',155,54,35,37,28)],
    衣帽间:[fixture('clothes_rail',145,95,25,99,99,'clothes','W')],
    书房:[fixture('desk_chair',158,136,34,30,47,'chair','N')],
    画室:[fixture('art_workbench',179,64,121,52,39),fixture('art_chair',222,130,27,25,43,'chair','N')],
    影音室:[fixture('popcorn_console',194,81,36,41,40)],
    玄关:[fixture('hall_shelf',360,20,44,30,39,'ledge'),fixture('stair_flight',530,8,225,50,150,'stairs','S')]
  };
  var anchors={客厅:[204,128],浴室:[96,164],厨房:[151,168],餐厅:[271,161],健身室:[105,174],阳台:[57,154],玄关:[365,70],卧室:[178,170],衣帽间:[63,161],书房:[69,151],画室:[145,169],影音室:[119,100],露台:[65,145],楼梯厅:[338,70],车库:[220,110]};
  function meta(item,type){return {facing:facing[item.id]||'S',height:itemHeight[item.id]||height[type]||16,mount:plan[item.id][4]||'',inset:item.id==='oven'||item.id==='dishwasher'};}
  var rugs={客厅:[91,101,99,63],餐厅:[83,91,164,83],卧室:[28,45,166,134],书房:[101,61,148,115],画室:[174,60,131,118],影音室:[39,115,155,89],健身室:[18,49,65,121]};
  // Doors and windows per wall, in each room's own plan units (N/S walls: x range, W/E walls: y range).
  // 2D floor plan and 3D walls both read this, so a door always meets the matching door of the next room.
  var openings={
    客厅:{N:[[108,192,'win',1.0,2.35]],S:[[130,175,'door']]},
    浴室:{N:[[48,104,'win',1.45,2.25]],S:[[110,155,'door']]},
    厨房:{N:[[96,168,'win',1.36,2.3]],S:[[110,155,'glass'],[165,240,'win',1.05,2.25]]},
    餐厅:{N:[[130,175,'door']],W:[[38,80,'door']],S:[[240,285,'door']]},
    健身室:{N:[[80,125,'door']],E:[[40,92,'win',1.0,2.25],[107,153,'glass']],S:[[106,151,'door']]},
    阳台:{N:[[20,65,'glass'],[75,150,'win',1.05,2.25]],W:[[40,92,'win',1.0,2.25],[107,153,'glass']]},
    玄关:{N:[[240,285,'door'],[456,501,'door']],S:[[200,300,'win',1.1,2.25],[370,420,'entry'],[520,620,'win',1.1,2.25]]},
    车库:{E:[[63,133,'door']]},
    卧室:{N:[[50,131,'win',1.32,2.46]],E:[[162,202,'door']],S:[[140,179,'door']]},
    衣帽间:{N:[[62,118,'win',1.36,2.3]],W:[[162,202,'door']]},
    书房:{N:[[110,192,'win',1.1,2.35]],S:[[130,175,'glass'],[182,240,'win',1.05,2.25]]},
    画室:{N:[[140,179,'door']],W:[[100,200,'win',.95,2.45]],S:[[240,285,'door']]},
    影音室:{E:[[150,195,'glass']],S:[[13,52,'door']]},
    露台:{N:[[40,85,'glass'],[92,150,'win',1.05,2.25]],W:[[150,195,'glass']]},
    楼梯厅:{N:[[240,285,'door'],[362,401,'door']],S:[[200,330,'win',1.1,2.3],[560,700,'win',1.1,2.3]]}
  };
  root.RoomModel={plan:plan,facing:facing,height:height,fixtures:fixtures,anchors:anchors,rugs:rugs,meta:meta,openings:openings};
})(typeof window==='undefined'?globalThis:window);
