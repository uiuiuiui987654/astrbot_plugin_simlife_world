/* Interior scenes for garage destinations. Flat vector rooms, no external assets. */
(function (root) {
  'use strict';

  var places = {
    '咖啡馆': {
      style: 'cafe', wall: '#5a4237', floor: '#7b5a42', accent: '#e1ae72',
      window: '#9dc9d8', desc: '拱形落地窗边摆着小圆桌，吧台后有咖啡机和一排杯子。'
    },
    '公园': {
      style: 'pavilion', wall: '#6f7e63', floor: '#8a795b', accent: '#c7d19b',
      window: '#a9d0c1', desc: '木亭子里能看见荷塘和树影，长椅边放着一盏小灯。'
    },
    '书店': {
      style: 'books', wall: '#4e4036', floor: '#76573e', accent: '#d9b27d',
      window: '#a8c8d2', desc: '窄高的书架一直顶到天花板，靠窗有一把阅读椅。'
    },
    '美术馆': {
      style: 'gallery', wall: '#d9d4c6', floor: '#9e9788', accent: '#b08b68',
      window: '#d8edf0', desc: '天窗把光落在白墙上，画框之间留了很宽的空白。'
    },
    '电影院': {
      style: 'cinema', wall: '#292833', floor: '#1f2029', accent: '#d98b78',
      window: '#1b1d26', desc: '银幕还亮着，红色座椅一排排向暗处延伸。'
    },
    '海边': {
      style: 'beach', wall: '#668a93', floor: '#b7a37e', accent: '#e7c98c',
      window: '#8dc8dc', desc: '半开放的海边小屋，窗外是浪线和远处的沙丘。'
    },
    '商场': {
      style: 'mall', wall: '#b9afa2', floor: '#8d8175', accent: '#e0b77d',
      window: '#c5dfeb', desc: '中庭玻璃顶下，店铺灯牌和扶梯一层层往上收。'
    },
    '办公室': {
      style: 'office', wall: '#9b9d93', floor: '#70746d', accent: '#7fa8c0',
      window: '#a9c9d9', desc: '整齐的工位、显示器和窗外的城市天际线。'
    },
    '老街': {
      style: 'teahouse', wall: '#6d5242', floor: '#8b694b', accent: '#dfb274',
      window: '#bbd1c5', desc: '木格窗、方桌和茶壶，门外是石板路和挂旗。'
    },
    '食堂': {
      style: 'canteen', wall: '#7d8173', floor: '#9b8a6f', accent: '#d8b67e',
      window: '#b5d1d8', desc: '长条餐桌、服务台和一排冒着热气的不锈钢餐盘。'
    },
    '植物园': {
      style: 'greenhouse', wall: '#688e7d', floor: '#8e9a7f', accent: '#c7d99e',
      window: '#b7d9d3', desc: '玻璃温室里植物从花坛一直爬到拱顶。'
    },
    '河岸步道': {
      style: 'riverside', wall: '#748d91', floor: '#95846b', accent: '#d2bd8d',
      window: '#9fcbdc', desc: '步道边的木亭，栏杆外是缓慢流动的河面。'
    },
    '湖畔': {
      style: 'lakeside', wall: '#5e6f6a', floor: '#806b51', accent: '#c3d2a4',
      window: '#a7cfd6', desc: '小木屋的窗框像画框，湖面就在外面发亮。'
    },
    '露营地': {
      style: 'camp', wall: '#3d4c47', floor: '#6c5a43', accent: '#e0b76c',
      window: '#7fa6b1', desc: '帐篷内的暖灯、睡袋和一只吊在火边的小水壶。'
    },
    '游乐园': {
      style: 'arcade', wall: '#3b3a5c', floor: '#2c2b43', accent: '#e78b9c',
      window: '#2d304c', desc: '霓虹灯下排着街机，远处传来过山车的尖叫。'
    },
    '花店': {
      style: 'flowers', wall: '#6e8474', floor: '#9a876d', accent: '#e6c3c9',
      window: '#b8d7d2', desc: '一桶桶花沿着窗边摆开，工作台上散着包装纸。'
    },
    '面包店': {
      style: 'bakery', wall: '#8a6d51', floor: '#a48561', accent: '#e8c989',
      window: '#b6d0d2', desc: '面包架、烤箱和木柜台，空气里像有黄油味。'
    },
    '图书馆': {
      style: 'library', wall: '#5a5140', floor: '#7e6749', accent: '#dfc086',
      window: '#b9d1d0', desc: '高书架围出安静的阅读区，绿色台灯亮着。'
    },
    '超市': {
      style: 'mall', wall: '#b6b2a2', floor: '#8f8779', accent: '#d9b57e',
      window: '#c9e0e4', desc: '一排排货架和冷柜，推车轮子在地砖上轻轻响。'
    },
    '山上': {
      style: 'pavilion', wall: '#596a5d', floor: '#7f6a4f', accent: '#c9d1a0',
      window: '#a8c6c9', desc: '山间木屋里能看到远处的树线，桌上放着一壶热茶。'
    },
    '江边': {
      style: 'riverside', wall: '#6d8589', floor: '#8b7a62', accent: '#d4c08c',
      window: '#9cc7d5', desc: '江边的木亭，栏杆外是慢慢流动的水面。'
    },
    '夜市': {
      style: 'arcade', wall: '#4b3f52', floor: '#37323f', accent: '#e7b36e',
      window: '#3a3550', desc: '夜市棚下的灯泡一串串亮着，空气里全是小吃的味道。'
    },
    '杂货铺': {
      style: 'mall', wall: '#8a7b63', floor: '#82705a', accent: '#d6b07c',
      window: '#b9d2c8', desc: '窄小的杂货铺，货架从地面一直堆到天花板，什么都能找到。'
    },
    '菜市场': {
      style: 'canteen', wall: '#7c8269', floor: '#948369', accent: '#cfb87e',
      window: '#b5d1c6', desc: '湿漉漉的地砖、菜筐和此起彼伏的吆喝声。'
    },
    '车站': {
      style: 'mall', wall: '#8f9599', floor: '#757a7d', accent: '#d8bd85',
      window: '#bcd6e0', desc: '候车厅的长椅、时刻表和拖着行李来来往往的人。'
    },
    '机场': {
      style: 'mall', wall: '#9aa5aa', floor: '#82898c', accent: '#c7d4da',
      window: '#bdd9e4', desc: '巨大的落地窗外停着飞机，广播里在报登机口。'
    },
    '旅店': {
      style: 'lakeside', wall: '#7d6a58', floor: '#8a7358', accent: '#d2b98d',
      window: '#b4cbd0', desc: '旅店房间不大，木桌上放着一盏台灯和一张手写地图。'
    },
    '异乡': {
      style: 'teahouse', wall: '#6f5b4a', floor: '#846a50', accent: '#dbb87d',
      window: '#b4cbc7', desc: '异乡的旧茶馆，窗外是不熟悉的街景和语言。'
    },
    '神社': {
      style: 'pavilion', wall: '#6b6050', floor: '#857655', accent: '#d9bc8a',
      window: '#aecbc4', desc: '神社檐下，木格窗边摆着签筒和一小碟盐。'
    },
    '温泉': {
      style: 'greenhouse', wall: '#698279', floor: '#82725f', accent: '#d8bc93',
      window: '#b9d6d0', desc: '汤屋的木格窗半开着，水汽从池边慢慢漫上来。'
    },
    '港口': {
      style: 'riverside', wall: '#6e8589', floor: '#887862', accent: '#d1ba87',
      window: '#9bc8d8', desc: '港口边的仓库改成了小店，窗外是桅杆和汽笛声。'
    },
    '山野': {
      style: 'pavilion', wall: '#586b5b', floor: '#7c674e', accent: '#c7d19c',
      window: '#a7c7b8', desc: '山野小屋的木窗正对树线，风一吹就沙沙响。'
    },
    '小酒馆': {
      style: 'teahouse', wall: '#594340', floor: '#6e5145', accent: '#d8a76c',
      window: '#a5c1bf', desc: '小酒馆只有几张高脚桌，灯罩是暖红色的。'
    },
    '城市': {
      style: 'mall', wall: '#9d9c99', floor: '#7b7672', accent: '#d7b87c',
      window: '#b8d5e2', desc: '街角商场的室内，玻璃门外是城市的车流。'
    }
  };

  var list = Object.keys(places);

  var OUTDOOR_ONLY = [
    '公园', '海边', '河岸步道', '湖畔', '山上', '山野',
    '港口', '老街', '游乐园', '夜市', '菜市场', '温泉'
  ];

  function hasInterior(key) {
    return Boolean(places[key]) && OUTDOOR_ONLY.indexOf(key) < 0;
  }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (char) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char];
    });
  }
  function R(x, y, w, h, fill, rx, extra) {
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
      '" rx="' + (rx || 0) + '" fill="' + fill + '" ' + (extra || '') + '/>';
  }
  function C(x, y, r, fill) {
    return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + fill + '"/>';
  }
  function E(x, y, rx, ry, fill) {
    return '<ellipse cx="' + x + '" cy="' + y + '" rx="' + rx + '" ry="' + ry + '" fill="' + fill + '"/>';
  }
  function P(d, fill, extra) {
    return '<path d="' + d + '" fill="' + fill + '" ' + (extra || '') + '/>';
  }
  function L(x, y, x2, y2, color, width) {
    return '<path d="M' + x + ' ' + y + 'L' + x2 + ' ' + y2 + '" fill="none" stroke="' +
      color + '" stroke-width="' + (width || 1) + '" stroke-linecap="round"/>';
  }
  function T(x, y, text, size, fill, anchor) {
    return '<text x="' + x + '" y="' + y + '" text-anchor="' + (anchor || 'middle') +
      '" font-family="sans-serif" font-size="' + (size || 12) + '" fill="' +
      (fill || '#f4e8d2') + '">' + esc(text) + '</text>';
  }
  function lamp(x, y, color) {
    return L(x, 0, x, y - 20, '#444b4a', 2) + P('M' + (x - 16) + ' ' + (y - 20) +
      'h32l-7 16h-18z', color || '#f0c783') + C(x, y - 2, 4, '#ffe6b0');
  }
  function plant(x, y, scale) {
    scale = scale || 1;
    return '<g transform="translate(' + x + ' ' + y + ') scale(' + scale + ')">' +
      E(0, 18, 14, 4, '#1f2a2633') + R(-9, 4, 18, 16, '#9b7a55', 3) +
      L(0, 5, 0, -24, '#5e815f', 2) + E(-7, -10, 6, 12, '#759b6e') +
      E(7, -16, 6, 13, '#8fb183') + '</g>';
  }
  function windowView(p, x, y, w, h, arch) {
    var frame = arch
      ? P('M' + (x - 4) + ' ' + (y + h) + 'V' + (y + w / 2) + 'Q' + (x - 4) + ' ' + (y - 4) +
        ' ' + (x + w / 2) + ' ' + (y - 4) + 'Q' + (x + w + 4) + ' ' + (y - 4) + ' ' +
        (x + w + 4) + ' ' + (y + w / 2) + 'V' + (y + h) + 'Z', '#84664b')
      : R(x - 4, y - 4, w + 8, h + 8, '#84664b', 3);
    var glass = arch
      ? P('M' + x + ' ' + (y + h) + 'V' + (y + w / 2) + 'Q' + x + ' ' + y + ' ' +
        (x + w / 2) + ' ' + y + 'Q' + (x + w) + ' ' + y + ' ' + (x + w) + ' ' +
        (y + w / 2) + 'V' + (y + h) + 'Z', p.window)
      : R(x, y, w, h, p.window, 2);
    return frame + glass + L(x + w / 2, y + 3, x + w / 2, y + h - 3, '#d8e7e1', 2) +
      L(x + 3, y + h * 0.55, x + w - 3, y + h * 0.55, '#d8e7e1', 2);
  }
  function shelf(x, y, w, h, colors) {
    var out = R(x, y, w, h, '#5b4330', 3) + R(x + 4, y + 4, w - 8, h - 8, '#745536', 2);
    for (var row = y + 18; row < y + h - 10; row += 22) {
      out += L(x + 6, row, x + w - 6, row, '#422f22', 2);
      for (var bx = x + 10; bx < x + w - 12; bx += 9) {
        out += R(bx, row - 13, 6, 13, colors[(bx + row) % colors.length], 1);
      }
    }
    return out;
  }
  function counter(x, y, w, p, items) {
    var panels='';
    for(var px=x+10;px<x+w-20;px+=38)panels+=R(px,y+13,28,32,'none',2,'stroke="#d6c4a2" stroke-width=".8"');
    return R(x, y, w, 52, '#b29976', 4) + panels + R(x-2,y,w+4,6,'#e9d9b7',2) +
      L(x+5,y+7,x+w-5,y+7,'#8c795f',1) + (items || '');
  }
  function table(x, y, w, p) {
    return E(x,y+40,w*.55,4,'#59644b20') + L(x,y+6,x,y+36,'#809078',4) +
      E(x,y+38,w*.32,3,'#6f8068') + E(x,y+2,w,8,'#a68b65') + E(x,y,w,7,'#d9c29a') +
      P('M'+(x-w*.8)+' '+y+'q'+w*.6+'-5 '+w*1.5+' 0','none','stroke="#efe0c1" stroke-width=".7"') +
      E(x-w*.35,y,7,2.7,'#eaf0de') + R(x-w*.35-4,y-6,8,6,'#f6ecd5',2) +
      E(x-w*.35,y-6,3.5,1.5,'#8b6d51') + C(x-w*.35+5,y-3,2,'none') +
      R(x+w*.18,y-2,12,4,'#a8b893',1);
  }
  function chair(x, y, p) {
    return L(x-8,y,x-10,y+15,'#a68b65',2) + L(x+8,y,x+10,y+15,'#a68b65',2) +
      R(x-12,y-23,24,19,p.accent,6) + R(x-9,y-21,18,13,'#a5b496',4) +
      E(x,y,13,4,'#b19a76') + E(x,y-2,12,3.5,'#bec9ac');
  }
  function screen(x, y, w, h, p) {
    return R(x - 8, y - 8, w + 16, h + 16, '#1d2025', 4) +
      R(x, y, w, h, '#d8e6e5', 2) + E(x + w / 2, y + h / 2, w * 0.27, h * 0.22, '#b9d8d7') +
      L(x + w / 2, y, x + w / 2, y + h, '#b7c9c6', 1);
  }

  function interiorFor(key, p) {
    var inner = [];
    if (p.style === 'cafe') {
      inner.push(windowView(p, 64, 52, 180, 142, true));
      inner.push(counter(296, 146, 238, p,
        R(330, 126, 42, 22, '#dfe4d9', 3) + R(382, 122, 28, 28, '#c07d51', 3) +
        T(396, 141, '☕', 13, '#f7e7c8') + R(420, 126, 54, 18, '#d7ded2', 2)));
      inner.push(lamp(360, 66, '#f0c783'), lamp(470, 66, '#f0c783'));
      inner.push(table(336, 236, 46, p), chair(288, 246, p), chair(384, 246, p));
      inner.push(table(492, 228, 38, p), chair(450, 238, p), chair(534, 238, p));
      inner.push(plant(586, 236, 1.1), R(0, 190, 620, 4, '#4a382b'));
      inner.push(T(92, 44, '窗边 · 手冲吧台', 11, '#e7d8bd', 'start'));
    } else if (p.style === 'books' || p.style === 'library') {
      inner.push(shelf(48, 30, 180, 226, ['#a68d88', '#8ca591', '#b6ac85', '#8f8da8']));
      inner.push(shelf(252, 30, 180, 226, ['#b6a17c', '#8fada4', '#a48f9d', '#c3b38d']));
      inner.push(shelf(456, 30, 116, 226, ['#8ca591', '#b6ac85', '#a68d88', '#9b8da1']));
      inner.push(windowView(p, 276, 56, 132, 110, true));
      inner.push(table(350, 248, 62, p), chair(300, 258, p), chair(400, 258, p));
      inner.push(plant(596, 238, 1.2), lamp(350, 70, '#e7c98d'));
      inner.push(L(48, 256, 572, 256, '#3f3024', 3));
      inner.push(T(92, 44, '高书架 · 阅读区', 11, '#e7d8bd', 'start'));
    } else if (p.style === 'gallery') {
      inner.push(R(52, 38, 196, 142, '#c9c3b4', 2) + R(62, 48, 176, 122, '#8a9da1', 1));
      inner.push(R(292, 38, 132, 104, '#c9c3b4', 2) + R(302, 48, 112, 84, '#b48975', 1));
      inner.push(R(468, 38, 112, 142, '#c9c3b4', 2) + R(478, 48, 92, 122, '#7c8f91', 1));
      inner.push(R(96, 210, 148, 8, '#8d7656', 2), L(108, 218, 108, 250, '#6a5540', 3),
        L(232, 218, 232, 250, '#6a5540', 3));
      inner.push(plant(596, 238, 1.2), lamp(360, 30, '#f4e2b8'));
      inner.push(R(0, 190, 620, 4, '#8c8271'));
      inner.push(T(92, 44, '天窗展厅', 11, '#5d5348', 'start'));
    } else if (p.style === 'cinema') {
      inner.push(R(0, 0, 620, 300, '#222430'));
      inner.push(screen(112, 42, 396, 154, p));
      for (var row = 0; row < 3; row++) {
        for (var col = 0; col < 6; col++) {
          inner.push(R(92 + col * 76, 214 + row * 22, 62, 15, '#8f4d50', 5));
        }
      }
      inner.push(L(72, 222, 72, 290, '#d0a86c', 2), L(548, 222, 548, 290, '#d0a86c', 2));
      inner.push(C(52, 236, 4, '#f2c27e'), C(568, 236, 4, '#f2c27e'));
      inner.push(T(310, 30, '银幕还亮着', 11, '#c9b7a4'));
    } else if (p.style === 'beach') {
      inner.push(windowView(p, 48, 38, 300, 166, false));
      inner.push(R(48, 204, 300, 12, '#6b5640', 3));
      inner.push(E(180, 236, 92, 24, '#c5b084') + E(180, 232, 78, 16, '#d8c89b'));
      inner.push(R(350, 224, 108, 12, '#9f7b55', 4), R(350, 236, 108, 6, '#7d5e40', 3));
      inner.push(L(358, 242, 350, 270, '#6f553c', 3), L(450, 242, 458, 270, '#6f553c', 3));
      inner.push(plant(592, 240, 1.2), R(0, 188, 620, 4, '#7b6650'));
      inner.push(T(92, 30, '海风从窗口吹进来', 11, '#e9dfc6', 'start'));
    } else if (p.style === 'mall') {
      inner.push(R(0, 0, 620, 300, '#aaa094'));
      inner.push(R(36, 34, 178, 138, '#887e74', 3) + R(46, 44, 158, 118, '#bcd7df', 2));
      inner.push(R(224, 34, 172, 138, '#887e74', 3) + R(234, 44, 152, 118, '#c8d9d6', 2));
      inner.push(R(414, 34, 172, 138, '#887e74', 3) + R(424, 44, 152, 118, '#d7c6b2', 2));
      inner.push(P('M48 240L250 194L452 240L452 258L48 258Z', '#c2b7a8'));
      inner.push(L(64, 240, 240, 202, '#7c9fa9', 3), L(256, 202, 448, 240, '#7c9fa9', 3));
      inner.push(plant(560, 240, 1.4), plant(62, 256, 1.1));
      inner.push(T(310, 280, '中庭 · 扶梯', 11, '#4f4c48'));
    } else if (p.style === 'office') {
      inner.push(windowView(p, 330, 40, 250, 130, false));
      inner.push(R(56, 128, 186, 72, '#8d8d83', 4) + R(64, 136, 170, 16, '#b7b4a6', 2));
      inner.push(R(92, 100, 60, 34, '#323c44', 2) + R(98, 106, 48, 22, '#9fc3d2', 1));
      inner.push(R(182, 100, 42, 34, '#323c44', 2));
      inner.push(R(300, 190, 200, 66, '#85877d', 4) + R(308, 198, 184, 14, '#b7b4a6', 2));
      inner.push(R(346, 164, 58, 32, '#323c44', 2) + R(352, 170, 46, 20, '#8fb4c4', 1));
      inner.push(chair(150, 238, p), chair(390, 276, p));
      inner.push(plant(596, 244, 1.2));
      inner.push(T(92, 44, '开放工位', 11, '#f0e6d5', 'start'));
    } else if (p.style === 'teahouse') {
      inner.push(windowView(p, 56, 44, 220, 150, false));
      inner.push(shelf(310, 40, 120, 170, ['#a98b64', '#c0a67c', '#8b7251']));
      inner.push(counter(454, 156, 124, p, R(486, 132, 26, 22, '#b7d4cf', 3) +
        T(499, 150, '茶', 12, '#4d5a56')));
      inner.push(table(200, 240, 54, p), chair(152, 250, p), chair(248, 250, p));
      inner.push(table(370, 250, 42, p), chair(330, 258, p), chair(410, 258, p));
      inner.push(lamp(120, 58, '#e7b67d'), lamp(300, 58, '#e7b67d'));
      inner.push(T(92, 36, '木格窗 · 茶桌', 11, '#f0e6d5', 'start'));
    } else if (p.style === 'canteen') {
      inner.push(R(56, 96, 230, 90, '#8b8e82', 4) + R(64, 104, 214, 18, '#c2c7ba', 2));
      for (var tray = 0; tray < 4; tray++) {
        inner.push(E(98 + tray * 52, 134, 22, 9, '#b9c2b6') + E(98 + tray * 52, 132, 18, 6, '#d8cba9'));
        inner.push(P('M' + (86 + tray * 52) + ' 121q12-16 24 0', 'none',
          'stroke="#eef0e5" stroke-opacity=".45" stroke-width="3"'));
      }
      inner.push(R(330, 164, 210, 54, '#91876f', 3));
      inner.push(R(64, 224, 480, 10, '#9e875f', 2), L(92, 234, 92, 262, '#7b6649', 3),
        L(516, 234, 516, 262, '#7b6649', 3));
      inner.push(chair(150, 210, p), chair(230, 210, p), chair(386, 210, p), chair(466, 210, p));
      inner.push(T(92, 44, '今日窗口', 11, '#f2e6d1', 'start'));
    } else if (p.style === 'greenhouse') {
      inner.push(P('M38 250V125Q38 32 310 32Q582 32 582 125V250Z', '#cfe0d4'));
      inner.push(P('M38 250V125Q38 32 310 32Q582 32 582 125V250Z', 'none',
        'stroke="#7c8f7f" stroke-width="4"'));
      for (var gx = 70; gx < 580; gx += 46) {
        inner.push(L(gx, 44, gx, 250, '#8aa394', 2));
      }
      inner.push(R(78, 188, 152, 52, '#7e6d52', 3), R(86, 196, 136, 16, '#9c8764', 2));
      inner.push(R(300, 188, 170, 52, '#7e6d52', 3), R(308, 196, 154, 16, '#9c8764', 2));
      inner.push(plant(112, 178, 1.4), plant(160, 178, 1.1), plant(350, 178, 1.5), plant(432, 178, 1.2));
      inner.push(L(310, 32, 310, 8, '#60766a', 2), E(310, 12, 24, 8, '#e8d7a0'));
      inner.push(T(310, 276, '玻璃温室', 12, '#4f6157'));
    } else if (p.style === 'riverside' || p.style === 'lakeside' || p.style === 'pavilion') {
      inner.push(windowView(p, 44, 44, 272, 160, false));
      inner.push(R(44, 204, 272, 10, '#6f5b45', 3));
      inner.push(R(348, 164, 220, 12, '#8c6d4a', 4));
      inner.push(L(356, 176, 356, 250, '#6e573d', 4), L(560, 176, 560, 250, '#6e573d', 4));
      inner.push(R(378, 134, 160, 30, '#9c7c57', 4));
      inner.push(plant(590, 244, 1.2), plant(56, 240, 1.1));
      inner.push(lamp(310, 58, '#e2bd7e'));
      inner.push(T(92, 34, p.style === 'lakeside' ? '湖边小屋' : p.style === 'pavilion' ? '荷塘木亭' : '河岸木亭', 11, '#f2e7d2', 'start'));
    } else if (p.style === 'camp') {
      inner.push(P('M58 250L310 44L562 250Z', '#5b6a5d'));
      inner.push(P('M112 250L310 82L508 250Z', '#303d37'));
      inner.push(R(264, 180, 92, 50, '#6f5740', 3) + R(272, 188, 76, 14, '#9a7b54', 2));
      inner.push(E(310, 240, 64, 8, '#7a5e3c') + E(310, 236, 48, 5, '#b98652'));
      inner.push(R(92, 206, 48, 28, '#7e623f', 3) + T(116, 224, '灯', 10, '#f5d69c'));
      inner.push(plant(596, 240, 1.2), T(310, 276, '帐篷内 · 暖灯', 12, '#e7d6b8'));
    } else if (p.style === 'arcade') {
      inner.push(R(0, 0, 620, 300, '#2e2d4a'));
      inner.push(R(36, 48, 130, 168, '#44425f', 5) + R(48, 60, 106, 62, '#9f6e93', 3) +
        R(48, 132, 106, 30, '#5b4b72', 3));
      inner.push(R(196, 48, 130, 168, '#44425f', 5) + R(208, 60, 106, 62, '#6e86a6', 3) +
        R(208, 132, 106, 30, '#5b4b72', 3));
      inner.push(R(356, 48, 130, 168, '#44425f', 5) + R(368, 60, 106, 62, '#b07c69', 3) +
        R(368, 132, 106, 30, '#5b4b72', 3));
      inner.push(R(516, 48, 68, 168, '#3c3a55', 5));
      inner.push(R(46, 160, 100, 8, '#d58a9e', 2), R(206, 160, 100, 8, '#e3b16f', 2), R(366, 160, 100, 8, '#8fc1bf', 2));
      inner.push(T(92, 30, '霓虹街机', 12, '#e7c9e0', 'start'));
      inner.push(P('M40 268h540', 'none', 'stroke="#5d5b82" stroke-width="3"'));
    } else if (p.style === 'flowers') {
      inner.push(windowView(p, 44, 44, 190, 150, true));
      for (var fx = 62; fx < 580; fx += 62) {
        inner.push(R(fx, 198, 46, 52, '#7a664b', 4));
        inner.push(C(fx + 10, 194, 10, '#dca3ae'), C(fx + 26, 188, 12, '#e6c890'), C(fx + 38, 198, 9, '#b59dc0'));
        inner.push(L(fx + 10, 204, fx + 10, 226, '#62805e', 2), L(fx + 26, 200, fx + 26, 226, '#62805e', 2));
      }
      inner.push(R(394, 132, 160, 58, '#8d7354', 4) + R(402, 140, 144, 14, '#c9b07f', 2));
      inner.push(T(474, 174, '花束包装台', 10, '#4e4131'));
      inner.push(plant(596, 240, 1.1));
      inner.push(T(92, 34, '一桶一桶的花', 11, '#f1e7d3', 'start'));
    } else if (p.style === 'bakery') {
      inner.push(windowView(p, 48, 44, 168, 144, false));
      inner.push(R(288, 42, 222, 152, '#6b4e36', 4));
      for (var s = 0; s < 3; s++) {
        inner.push(R(300, 62 + s * 42, 198, 6, '#b28757', 2));
        for (var b = 0; b < 5; b++) {
          inner.push(E(324 + b * 36, 56 + s * 42, 12, 7, '#c48d55'));
        }
      }
      inner.push(R(104, 154, 246, 62, '#7d5e41', 4) + R(112, 162, 230, 16, '#cfa775', 2));
      inner.push(R(378, 228, 130, 46, '#6d5139', 4) + R(386, 236, 114, 12, '#b18458', 2));
      inner.push(T(310, 32, '面包与烤箱', 12, '#f2e4cb'));
      inner.push(T(150, 248, '收银台', 10, '#f2e4cb'));
    } else {
      inner.push(windowView(p, 56, 44, 200, 150, true));
      inner.push(table(370, 248, 56, p), chair(320, 258, p), chair(420, 258, p));
      inner.push(plant(594, 240, 1.2), lamp(300, 60, p.accent));
      inner.push(T(92, 34, '室内一角', 11, '#f2e7d2', 'start'));
      inner.push(T(310, 280, '窗外光线很好', 11, '#d9cdb8'));
    }
    return inner.join('');
  }

  function interior(key, environment) {
    var p = places[key];
    if (!p) {
      return '<div class="garage-destination-fallback">还没有这个地点的内部造型。</div>';
    }
    if (!hasInterior(key)) {
      return '<div class="garage-destination-fallback">这是一个户外地点，没有室内场景。</div>';
    }
    if(root.DestinationInteriors){
      var detailed=root.DestinationInteriors.draw(key,environment);
      if(detailed)return detailed;
    }
    p = Object.assign({},p);
    var darkRoom=/cinema|arcade/.test(p.style);
    if(!darkRoom){
      var garden=/flowers|greenhouse|pavilion|onsen/.test(p.style);
      p.wall=garden?'#c9d9bc':'#e5dcc5';p.floor=garden?'#b9c5a1':'#baa184';p.accent='#bba17a';
    }
    var finish='';
    if(!darkRoom){
      finish+=L(0,12,620,12,'#faf2db',5)+L(0,168,620,168,'#b3b99b',2);
      for(var pane=12;pane<600;pane+=62)finish+=R(pane,177,48,29,'none',2,'stroke="#a8b38f" stroke-width="1"');
      for(var plank=246;plank<300;plank+=27)finish+=L(0,plank,620,plank,'#dfc9a855',1);
    }
    var id = 'gd-' + Math.abs(key.split('').reduce(function (sum, ch) {
      return sum * 31 + ch.charCodeAt(0);
    }, 7));
    return '<svg class="garage-destination-art" viewBox="0 0 620 300" preserveAspectRatio="xMidYMid slice" role="img" aria-label="' +
      esc(key) + ' 的内部">' +
      '<defs><linearGradient id="' + id + '-wall" x1="0" y1="0" x2="0" y2="1">' +
      '<stop stop-color="' + p.wall + '"/><stop offset="1" stop-color="' + (darkRoom?'#20282a':p.wall) + '"/>' +
      '</linearGradient></defs>' +
      R(0, 0, 620, 300, 'url(#' + id + '-wall)') +
      P('M0 300V216L620 216V300Z', p.floor) +
      L(0, 216, 620, 216, '#2b2620', 3) +
      finish + '<g class="garage-destination-furniture">' + interiorFor(key, p) + '</g>' +
      '</svg>';
  }

  root.GarageDestinations = {
    list: list,
    interior: interior,
    hasInterior: hasInterior,
    outdoorOnly: OUTDOOR_ONLY,
    description: function (key) {
      return places[key] ? places[key].desc : '';
    }
  };
})(window);
