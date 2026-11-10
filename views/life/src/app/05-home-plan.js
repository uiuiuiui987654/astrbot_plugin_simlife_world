  function svgRect(x, y, w, h, fill, rx, cls, extra) {
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
      '" rx="' + (rx || 0) + '" fill="' + fill + '"' +
      (cls ? ' class="' + cls + '"' : '') +
      (extra ? ' ' + extra : '') + '/>';
  }

  function svgCircle(cx, cy, r, fill, cls, extra) {
    return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + fill + '"' +
      (cls ? ' class="' + cls + '"' : '') +
      (extra ? ' ' + extra : '') + '/>';
  }

  function svgEllipse(cx, cy, rx, ry, fill, cls, extra) {
    return '<ellipse cx="' + cx + '" cy="' + cy + '" rx="' + rx + '" ry="' + ry +
      '" fill="' + fill + '"' +
      (cls ? ' class="' + cls + '"' : '') +
      (extra ? ' ' + extra : '') + '/>';
  }

  function svgLine(x1, y1, x2, y2, stroke, width, cls, dash) {
    return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 +
      '" stroke="' + (stroke || 'rgba(207,222,238,.3)') + '" stroke-width="' + (width || 1) + '"' +
      (cls ? ' class="' + cls + '"' : '') +
      (dash ? ' stroke-dasharray="' + dash + '"' : '') + '/>';
  }

  function svgPath(d, fill, cls, extra) {
    return '<path d="' + d + '" fill="' + (fill || 'none') + '"' +
      (cls ? ' class="' + cls + '"' : '') +
      (extra ? ' ' + extra : '') + '/>';
  }

  function svgText(x, y, text, cls, anchor) {
    return '<text x="' + x + '" y="' + y + '"' +
      (cls ? ' class="' + cls + '"' : '') +
      (anchor ? ' text-anchor="' + anchor + '"' : '') + '>' +
      escapeHtml(text) + '</text>';
  }

  function furnitureHit(id, name, inner) {
    return '<g class="furniture-hit" data-id="' + escapeHtml(id) + '" role="button" ' +
      'tabindex="0" focusable="true" aria-label="' + escapeHtml(name) + '">' +
      '<title>' + escapeHtml(name) + '</title>' + inner + '</g>';
  }

  function furnitureBed(x, y) {
    return [
      svgEllipse(x + 78, y + 102, 82, 12, '#070a0e', '', 'opacity=".55"'),
      svgRect(x, y, 150, 12, '#5a4b62', 5, 'furniture'),
      svgRect(x + 4, y + 12, 142, 88, '#3b3040', 8, 'furniture'),
      svgRect(x + 8, y + 42, 134, 54, '#4a3a4d', 7, 'furniture'),
      svgRect(x + 12, y + 18, 44, 18, '#d8cfc4', 5, 'furniture'),
      svgRect(x + 94, y + 18, 44, 18, '#d8cfc4', 5, 'furniture'),
      svgLine(x + 8, y + 56, x + 142, y + 56, '#5d4a61', 1),
      svgLine(x + 8, y + 80, x + 142, y + 80, '#5d4a61', 1)
    ].join('');
  }

  function furnitureWardrobe(x, y) {
    return [
      svgEllipse(x + 28, y + 134, 32, 7, '#070a0e', '', 'opacity=".45"'),
      svgRect(x, y, 56, 130, '#3a3140', 4, 'furniture'),
      svgLine(x + 28, y + 4, x + 28, y + 126, '#6a5a72', 1),
      svgCircle(x + 23, y + 62, 2, '#d8cfc4'),
      svgCircle(x + 33, y + 62, 2, '#d8cfc4')
    ].join('');
  }

  function furnitureNightstand(x, y) {
    return [
      svgRect(x, y, 26, 26, '#4a3b2f', 3, 'furniture'),
      svgCircle(x + 13, y - 9, 8, '#f0b86e', '', 'opacity=".2" filter="url(#softGlow)"'),
      svgCircle(x + 13, y - 9, 4, '#f0b86e'),
      svgLine(x + 13, y - 5, x + 13, y + 1, '#f0b86e', 1)
    ].join('');
  }

  function furnitureVanity(x, y) {
    return [
      svgEllipse(x + 20, y + 34, 26, 6, '#070a0e', '', 'opacity=".42"'),
      svgRect(x, y + 4, 44, 24, '#4a3b2f', 5, 'furniture'),
      svgRect(x + 4, y + 8, 36, 8, '#6a513d', 2, 'furniture'),
      svgRect(x + 38, y - 4, 6, 34, '#3a2f27', 2, 'furniture'),
      svgRect(x + 40, y - 2, 2, 30, '#8fa3bb', 1, '', 'opacity=".8"'),
      svgCircle(x + 10, y + 18, 3, '#d8cfc4'),
      svgCircle(x + 16, y + 21, 2, '#c78b5c'),
      svgRect(x + 23, y + 15, 8, 10, '#b9a36b', 1, 'furniture'),
      svgCircle(x + 24, y + 38, 8, '#3b3040', '', 'stroke="#6a5a72" stroke-width="1"')
    ].join('');
  }

  function furnitureYogaMat(x, y) {
    return [
      svgRect(x, y, 64, 22, '#2f6b4f', 9, 'furniture'),
      svgRect(x + 6, y + 5, 52, 12, 'none', 6, 'line-soft'),
      svgCircle(x + 8, y + 11, 6, '#3f8a63'),
      svgCircle(x + 8, y + 11, 2, '#1d2d25'),
      svgLine(x + 56, y + 4, x + 56, y + 18, '#4a8c6d', 1)
    ].join('');
  }

  function furnitureConsole(x, y) {
    return [
      svgEllipse(x + 20, y + 17, 27, 5, '#070a0e', '', 'opacity=".4"'),
      svgRect(x, y, 40, 11, '#2f3a44', 3, 'furniture'),
      svgRect(x + 5, y + 3, 16, 2, '#7dc8ff', 1, '', 'opacity=".7"'),
      '<g transform="rotate(-20 ' + (x + 10) + ' ' + (y + 23) + ')">',
      svgRect(x + 3, y + 17, 13, 10, '#3b4a5b', 4, 'furniture'),
      svgCircle(x + 7, y + 21, 1.7, '#7dc8ff'),
      '</g>',
      '<g transform="rotate(20 ' + (x + 30) + ' ' + (y + 23) + ')">',
      svgRect(x + 23, y + 17, 13, 10, '#3b4a5b', 4, 'furniture'),
      svgCircle(x + 32, y + 21, 1.7, '#f0b86e'),
      '</g>',
      svgLine(x + 33, y + 5, x + 38, y + 5, '#8fa3bb', 1)
    ].join('');
  }

  function furniturePlants(x, y) {
    return [
      svgEllipse(x + 24, y + 32, 30, 6, '#070a0e', '', 'opacity=".4"'),
      svgRect(x, y + 18, 48, 12, '#4a3b2f', 4, 'furniture'),
      svgEllipse(x + 7, y + 10, 7, 12, '#2f6b4f'),
      svgEllipse(x + 20, y + 5, 8, 15, '#3f8a63'),
      svgEllipse(x + 34, y + 9, 7, 13, '#2f6b4f'),
      svgEllipse(x + 44, y + 14, 5, 9, '#3f8a63'),
      svgEllipse(x + 2, y + 15, 5, 8, '#3f8a63'),
      svgLine(x + 20, y + 16, x + 20, y + 20, '#2f6b4f', 1)
    ].join('');
  }

  function furnitureTelescope(x, y) {
    return [
      svgEllipse(x + 14, y + 18, 24, 6, '#070a0e', '', 'opacity=".45"'),
      '<g transform="rotate(-28 ' + (x + 14) + ' ' + (y + 10) + ')">',
      svgRect(x - 8, y + 4, 44, 10, '#3a4a5a', 5, 'furniture'),
      svgRect(x + 28, y + 2, 14, 14, '#2f3a44', 4, 'furniture'),
      svgCircle(x + 35, y + 9, 4, '#7dc8ff', '', 'opacity=".65"'),
      svgRect(x - 12, y + 5, 8, 8, '#8fa3bb', 3, 'furniture'),
      '</g>',
      svgLine(x + 14, y + 14, x, y + 32, '#6f8b9b', 2),
      svgLine(x + 14, y + 14, x + 26, y + 32, '#6f8b9b', 2),
      svgLine(x + 14, y + 14, x + 14, y + 34, '#6f8b9b', 2)
    ].join('');
  }

  function furnitureVacuum(x, y) {
    return [
      svgEllipse(x + 14, y + 14, 20, 5, '#070a0e', '', 'opacity=".4"'),
      svgCircle(x + 14, y + 12, 10, '#3b4a5b', '', 'stroke="#6f8b9b" stroke-width="1"'),
      svgCircle(x + 14, y + 12, 4, '#1a222c'),
      svgRect(x + 2, y + 2, 24, 6, '#52657a', 3, 'furniture'),
      svgLine(x + 26, y + 10, x + 34, y + 20, '#6f8b9b', 2),
      svgRect(x + 30, y + 18, 8, 12, '#2f3a44', 2, 'furniture')
    ].join('');
  }

  function furniturePlant(x, y, scale) {
    scale = scale || 1;
    return [
      svgRect(x - 8 * scale, y + 10 * scale, 16 * scale, 14 * scale, '#4a3b2f', 3, 'furniture'),
      svgEllipse(x, y - 2 * scale, 10 * scale, 16 * scale, '#2f6b4f'),
      svgEllipse(x + 7 * scale, y - 7 * scale, 7 * scale, 12 * scale, '#3f8a63'),
      svgEllipse(x - 7 * scale, y - 4 * scale, 6 * scale, 10 * scale, '#3f8a63')
    ].join('');
  }

  function furnitureRug(x, y, w, h, cls) {
    return svgRect(x, y, w, h, '#2d2a25', 10, cls || 'rug') +
      svgRect(x + 8, y + 8, w - 16, h - 16, 'none', 8, 'line-soft');
  }

  function furnitureDesk(x, y) {
    return [
      svgEllipse(x + 60, y + 42, 64, 7, '#070a0e', '', 'opacity=".45"'),
      svgRect(x, y + 12, 120, 12, '#4a3b2f', 3, 'furniture'),
      svgLine(x + 8, y + 24, x + 8, y + 44, '#6a513d', 3),
      svgLine(x + 112, y + 24, x + 112, y + 44, '#6a513d', 3),
      svgRect(x + 24, y - 22, 50, 32, '#1a222c', 3, 'furniture'),
      svgRect(x + 28, y - 18, 42, 24, '#27405a', 2, 'tv-glow'),
      svgRect(x + 34, y + 12, 34, 8, '#374452', 2, 'furniture'),
      svgRect(x + 92, y + 4, 10, 10, '#d8cfc4', 2, 'furniture')
    ].join('');
  }

  function furnitureChair(x, y) {
    return [
      svgRect(x, y, 34, 8, '#3b3040', 4, 'furniture'),
      svgRect(x + 3, y - 26, 28, 28, '#4a3e4c', 5, 'furniture'),
      svgLine(x + 14, y + 8, x + 14, y + 24, '#6a5a72', 2),
      svgLine(x + 20, y + 8, x + 20, y + 24, '#6a5a72', 2)
    ].join('');
  }

  function furnitureBookshelf(x, y) {
    var out = [svgRect(x, y, 48, 130, '#3a2f27', 3, 'furniture')];
    [24, 50, 76, 102].forEach(function (offset) {
      out.push(svgLine(x + 3, y + offset, x + 45, y + offset, '#6a5442', 1));
    });
    var colors = ['#a56b6b', '#6b8fa5', '#b9a36b', '#7ea57e', '#9b7ea5', '#c78b5c'];
    for (var i = 0; i < 5; i++) {
      out.push(svgRect(x + 5 + i * 8, y + 6, 5, 16, colors[i % colors.length], 1));
      out.push(svgRect(x + 5 + i * 8, y + 32, 5, 15, colors[(i + 2) % colors.length], 1));
      out.push(svgRect(x + 5 + i * 8, y + 58, 5, 14, colors[(i + 4) % colors.length], 1));
    }
    return out.join('');
  }

  function furnitureSofa(x, y) {
    return [
      svgEllipse(x + 30, y + 112, 42, 10, '#070a0e', '', 'opacity=".5"'),
      svgRect(x, y + 12, 58, 100, '#3e3440', 8, 'furniture'),
      svgRect(x - 2, y, 62, 18, '#4a3e4c', 7, 'furniture'),
      svgRect(x + 7, y + 24, 44, 28, '#514354', 6, 'furniture'),
      svgRect(x + 7, y + 58, 44, 28, '#4a3e4c', 6, 'furniture'),
      svgRect(x + 4, y + 94, 50, 14, '#3b3040', 5, 'furniture')
    ].join('');
  }

  function furnitureCoffeeTable(x, y) {
    return [
      svgEllipse(x + 48, y + 36, 54, 8, '#070a0e', '', 'opacity=".45"'),
      svgRect(x, y, 96, 44, '#4a3b2f', 7, 'furniture'),
      svgRect(x + 10, y + 8, 26, 18, '#d8cfc4', 2, 'furniture'),
      svgCircle(x + 70, y + 18, 8, '#8d9aab', '', 'opacity=".8"')
    ].join('');
  }

  function furnitureTv(x, y) {
    return [
      svgRect(x, y, 20, 72, '#1a222c', 3, 'furniture'),
      svgRect(x + 3, y + 4, 14, 56, '#27405a', 2, 'tv-glow'),
      svgLine(x + 10, y + 72, x + 10, y + 82, '#4a5a6a', 3),
      svgLine(x - 4, y + 84, x + 24, y + 84, '#4a5a6a', 3)
    ].join('');
  }

  function furnitureRecord(x, y) {
    return [
      svgRect(x, y, 44, 26, '#2f3a44', 3, 'furniture'),
      svgCircle(x + 14, y + 13, 8, '#1a222c', '', 'stroke="#6f8b9b" stroke-width="1"'),
      svgCircle(x + 14, y + 13, 2, '#f0b86e'),
      svgLine(x + 30, y + 5, x + 40, y + 18, '#d8cfc4', 1.5)
    ].join('');
  }

  function furnitureCounter(x, y, w) {
    return [
      svgRect(x, y, w, 38, '#3a3b2a', 5, 'furniture'),
      svgCircle(x + 28, y + 20, 11, '#16242c', '', 'stroke="#6f8b9b" stroke-width="1"'),
      svgCircle(x + 28, y + 20, 4, '#6f8b9b'),
      svgCircle(x + 112, y + 14, 4, '#1a222c', '', 'stroke="#6f8b9b"'),
      svgCircle(x + 126, y + 14, 4, '#1a222c', '', 'stroke="#6f8b9b"'),
      svgCircle(x + 112, y + 27, 4, '#1a222c', '', 'stroke="#6f8b9b"'),
      svgCircle(x + 126, y + 27, 4, '#1a222c', '', 'stroke="#6f8b9b"'),
      svgRect(x + 175, y + 6, 26, 15, '#8d9aab', 2, 'furniture')
    ].join('');
  }

  function furnitureCoffeeMachine(x, y) {
    return [
      svgRect(x, y, 30, 24, '#2f3a44', 4, 'furniture'),
      svgRect(x + 4, y + 4, 22, 8, '#4b5b6b', 2, 'furniture'),
      svgCircle(x + 8, y + 18, 3, '#f0b86e'),
      svgRect(x + 16, y + 16, 8, 6, '#1a222c', 1, 'furniture')
    ].join('');
  }

  function furnitureFridge(x, y) {
    return [
      svgRect(x, y, 46, 100, '#2f3a44', 4, 'furniture'),
      svgLine(x + 4, y + 36, x + 42, y + 36, '#536575', 1),
      svgLine(x + 36, y + 10, x + 36, y + 30, '#9fb6c5', 2),
      svgLine(x + 36, y + 44, x + 36, y + 64, '#9fb6c5', 2),
      svgCircle(x + 14, y + 18, 2, '#f0b86e'),
      svgCircle(x + 20, y + 22, 2, '#7dc8ff')
    ].join('');
  }

  function furnitureDining(x, y) {
    var out = [
      svgEllipse(x + 48, y + 38, 54, 8, '#070a0e', '', 'opacity=".45"'),
      svgRect(x, y, 96, 52, '#4a3b2f', 9, 'furniture'),
      svgCircle(x + 24, y + 18, 8, '#d8cfc4'),
      svgCircle(x + 70, y + 18, 8, '#c78b5c'),
      svgCircle(x + 48, y + 36, 10, '#8d9aab', '', 'opacity=".65"')
    ];
    [[-18, 8], [100, 8], [-18, 55], [100, 55]].forEach(function (pos) {
      out.push(svgRect(x + pos[0], y + pos[1], 18, 18, '#3b3040', 4, 'furniture'));
    });
    return out.join('');
  }

  function furnitureTub(x, y) {
    return [
      svgRect(x, y, 150, 64, '#2b3c46', 18, 'furniture'),
      svgEllipse(x + 75, y + 32, 60, 20, '#1f303a', '', 'stroke="#54707f" stroke-width="1.2"'),
      svgCircle(x + 138, y + 20, 5, '#9fb6c5'),
      svgPath('M' + (x + 132) + ' ' + (y + 20) + ' L' + (x + 132) + ' ' + (y + 5) + ' L' + (x + 145) + ' ' + (y + 5), 'none', 'line')
    ].join('');
  }

  function furnitureSink(x, y) {
    return [
      svgRect(x, y, 60, 30, '#34434d', 5, 'furniture'),
      svgEllipse(x + 30, y + 15, 18, 8, '#16242c', '', 'stroke="#6f8b9b" stroke-width="1"'),
      svgRect(x + 12, y - 28, 36, 24, '#27405a', 3, 'furniture'),
      svgRect(x + 15, y - 25, 30, 18, '#6fb6d9', 2, '', 'opacity=".35"')
    ].join('');
  }

  function furnitureToilet(x, y) {
    return [
      svgRect(x, y, 34, 16, '#34434d', 4, 'furniture'),
      svgEllipse(x + 17, y + 30, 18, 20, '#1f303a', '', 'stroke="#6f8b9b" stroke-width="1"')
    ].join('');
  }

  function furnitureRailing(x, y, w) {
    var out = [svgLine(x, y, x + w, y, '#6f8b9b', 2)];
    for (var i = 0; i <= w; i += 18) {
      out.push(svgLine(x + i, y - 12, x + i, y + 4, '#6f8b9b', 1));
    }
    return out.join('');
  }

  function sceneEnvironment() { return SceneStudio.environment(state.data, window.location.search); }

  function homeSvg(now) {
    if (window.SceneStudio) return SceneStudio.home(now, state.previewFloor || SceneStudio.floorFor(now && now.room), state.homeItems, sceneEnvironment());
    var current = now && now.kind === 'home' ? now.room : null;
    var out = [];
    out.push('<defs>');
    out.push('<filter id="roomGlow" x="-20%" y="-20%" width="140%" height="140%">');
    out.push('<feGaussianBlur stdDeviation="5" result="blur"/>');
    out.push('<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>');
    out.push('</filter>');
    out.push('<filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%">');
    out.push('<feGaussianBlur stdDeviation="8"/>');
    out.push('</filter>');
    out.push('<pattern id="woodLines" width="40" height="14" patternUnits="userSpaceOnUse">');
    out.push('<path d="M0 7 H40" stroke="#453d2f" stroke-width="1" opacity=".55"/>');
    out.push('<path d="M20 0 V14" stroke="#3a3328" stroke-width=".8" opacity=".45"/>');
    out.push('</pattern>');
    out.push('<pattern id="tileLines" width="24" height="24" patternUnits="userSpaceOnUse">');
    out.push('<path d="M0 24 H24 M24 0 V24" stroke="#33505b" stroke-width="1" opacity=".55"/>');
    out.push('</pattern>');
    out.push('<pattern id="deckLines" width="30" height="12" patternUnits="userSpaceOnUse">');
    out.push('<path d="M0 6 H30" stroke="#345044" stroke-width="1" opacity=".5"/>');
    out.push('</pattern>');
    out.push('</defs>');

    out.push(svgRect(15, 15, 810, 590, '#111820', 10, '', 'stroke="#4a5a6d" stroke-width="6"'));
    out.push(svgCircle(420, 310, 260, '#5a4a78', '', 'opacity=".05" filter="url(#softGlow)"'));

    ROOMS.forEach(function (room) {
      var isCurrent = room.name === current;
      out.push(svgRect(room.x, room.y, room.w, room.h, room.fill, 5,
        'room-floor' + (isCurrent ? ' current' : '')));
      if (room.name === '浴室' || room.name === '厨房') {
        out.push(svgRect(room.x + 2, room.y + 2, room.w - 4, room.h - 4, 'url(#tileLines)', 4, '', 'opacity=".5"'));
      } else if (room.name === '阳台') {
        out.push(svgRect(room.x + 2, room.y + 2, room.w - 4, room.h - 4, 'url(#deckLines)', 4, '', 'opacity=".55"'));
      } else if (room.name !== '玄关') {
        out.push(svgRect(room.x + 2, room.y + 2, room.w - 4, room.h - 4, 'url(#woodLines)', 4, '', 'opacity=".45"'));
      }
      if (isCurrent) {
        out.push(svgRect(room.x - 2, room.y - 2, room.w + 4, room.h + 4, 'none', 7,
          '', 'stroke="#f0b86e" stroke-width="2" opacity=".55"'));
      }
    });

    // 卧室
    out.push(furnitureRug(60, 150, 170, 52, 'rug-2'));
    out.push(furnitureHit('bed', '床', furnitureBed(50, 84)));
    out.push(furnitureHit('wardrobe', '衣柜', furnitureWardrobe(230, 40)));
    out.push(furnitureHit('bedside_lamp', '床头灯', furnitureNightstand(210, 92)));
    out.push(furniturePlant(250, 226, 0.85));
    out.push(furnitureHit('vanity_mirror', '穿衣镜和护肤台', furnitureVanity(286, 168)));
    out.push(svgRect(96, 48, 52, 30, '#3a2f27', 2, '', 'stroke="#6a5442" stroke-width="1"'));
    out.push(svgRect(100, 52, 44, 22, '#6b8fa5', 1, '', 'opacity=".35"'));
    out.push(svgPath('M104 70 L118 58 L128 66 L138 54', 'none', 'line', 'stroke="#d8cfc4" stroke-width="1.2"'));

    // 浴室
    out.push(svgRect(365, 208, 100, 26, '#2b3a42', 6, 'rug'));
    out.push(furnitureHit('bathtub', '浴缸', furnitureTub(365, 50)));
    out.push(furnitureSink(365, 138));
    out.push(furnitureToilet(455, 150));
    out.push(svgLine(512, 110, 512, 190, '#6f8b9b', 1));
    out.push(svgRect(504, 118, 16, 20, '#b6c8d4', 1, 'furniture'));
    out.push(furniturePlant(510, 210, 0.65));

    // 书房
    out.push(furnitureRug(640, 186, 100, 34, 'rug-2'));
    out.push(furnitureHit('bookshelf', '书架', furnitureBookshelf(565, 45)));
    out.push(furnitureHit('desk', '书桌', furnitureDesk(650, 135)));
    out.push(furnitureChair(690, 180));
    out.push(furniturePlant(790, 205, 0.9));
    out.push(svgRect(650, 48, 62, 38, '#3a2f27', 2, '', 'stroke="#6a5442" stroke-width="1"'));
    out.push(svgRect(655, 53, 16, 12, '#d8cfc4', 1, '', 'opacity=".7"'));
    out.push(svgRect(676, 53, 16, 12, '#7dc8ff', 1, '', 'opacity=".45"'));
    out.push(svgRect(697, 53, 10, 12, '#f0b86e', 1, '', 'opacity=".45"'));
    out.push(svgCircle(736, 66, 12, 'none', '', 'stroke="#8fa3bb" stroke-width="1"'));
    out.push(svgLine(736, 66, 736, 58, '#8fa3bb', 1));
    out.push(svgLine(736, 66, 743, 70, '#8fa3bb', 1));

    // 客厅
    out.push(furnitureRug(105, 345, 170, 110, 'rug'));
    out.push(furnitureHit('sofa', '沙发', furnitureSofa(48, 310)));
    out.push(furnitureCoffeeTable(150, 375));
    out.push(furnitureHit('tv', '电视', furnitureTv(305, 315)));
    out.push(furnitureHit('game_console', '游戏机', furnitureConsole(294, 409)));
    out.push(furnitureHit('yoga_mat', '瑜伽垫', furnitureYogaMat(168, 447)));
    out.push(furnitureHit('record_player', '黑胶唱片机', furnitureRecord(232, 292)));
    out.push(furniturePlant(318, 455, 0.9));
    out.push(svgRect(150, 286, 62, 28, '#3a2f27', 2, '', 'stroke="#6a5442" stroke-width="1"'));
    out.push(svgRect(154, 290, 54, 20, '#6b8fa5', 1, '', 'opacity=".22"'));
    // 厨房
    out.push(furnitureCounter(395, 290, 210));
    out.push(furnitureHit('coffee_machine', '咖啡机', furnitureCoffeeMachine(538, 292)));
    out.push(furnitureHit('fridge', '冰箱', furnitureFridge(395, 345)));
    out.push(furnitureHit('dining_table', '餐桌', furnitureDining(468, 388)));
    out.push(furniturePlant(588, 470, 0.75));
    // 阳台
    out.push(furnitureRailing(652, 492, 146));
    out.push(furnitureHit('plants', '绿植', furniturePlants(642, 306)));
    out.push(furniturePlant(778, 322, 0.75));
    out.push(furniturePlant(660, 444, 0.7));
    out.push(furnitureHit('balcony_chair', '摇椅',
      svgRect(690, 380, 48, 42, '#3e3440', 6, 'furniture') +
      svgRect(694, 372, 40, 12, '#4a3e4c', 5, 'furniture')));
    out.push(svgCircle(760, 400, 20, '#4a3b2f', '', 'stroke="#7a614a" stroke-width="1"'));
    out.push(svgCircle(760, 400, 5, '#d8cfc4'));
    out.push(furnitureHit('telescope', '望远镜', furnitureTelescope(760, 436)));
    for (var light = 0; light < 7; light++) {
      out.push(svgCircle(660 + light * 22, 285, 2, '#f0b86e'));
    }

    // 玄关
    out.push(svgRect(130, 546, 580, 30, '#2b2a25', 7, 'rug'));
    out.push(furnitureHit('shoe_cabinet', '鞋柜',
      svgRect(50, 540, 64, 38, '#3a2f27', 3, 'furniture') +
      svgLine(82, 544, 82, 574, '#6a5442', 1)));
    out.push(furnitureHit('vacuum', '吸尘器', furnitureVacuum(188, 546)));
    out.push(svgLine(758, 538, 758, 580, '#6f8b9b', 1));
    for (var coat = 0; coat < 3; coat++) {
      out.push(svgCircle(754 + (coat % 2) * 8, 548 + coat * 10, 2, '#b6c8d4'));
    }
    out.push(svgRect(700, 542, 26, 30, '#27405a', 2, '', 'stroke="#6f8b9b" stroke-width="1"'));
    out.push(svgRect(703, 545, 20, 24, '#6fb6d9', 1, '', 'opacity=".25"'));
    out.push(svgRect(402, 570, 56, 16, '#2b3a42', 4, 'rug'));

    // 外窗 / 门
    var windows = [
      [80, 20, 170, 20], [360, 20, 430, 20], [600, 20, 680, 20],
      [20, 300, 20, 380], [820, 300, 820, 380]
    ];
    windows.forEach(function (w) {
      if (w[1] === w[3]) {
        out.push(svgLine(w[0], w[1], w[2], w[3], '#79c6e8', 2.2, 'window-line'));
        out.push(svgLine(w[0], w[1] - 4, w[0], w[1] + 4, '#8fd4ee', 1));
        out.push(svgLine(w[2], w[3] - 4, w[2], w[3] + 4, '#8fd4ee', 1));
      } else {
        out.push(svgLine(w[0], w[1], w[2], w[3], '#79c6e8', 2.2, 'window-line'));
        out.push(svgLine(w[0] - 4, w[1], w[0] + 4, w[1], '#8fd4ee', 1));
        out.push(svgLine(w[2] - 4, w[3], w[2] + 4, w[3], '#8fd4ee', 1));
      }
    });
    out.push(svgRect(405, 586, 60, 18, '#0f151d', 0, 'door-gap'));
    out.push(svgLine(405, 590, 465, 590, '#7a8ba3', 2, 'door-line'));
    out.push(svgLine(405, 590, 407, 560, '#7a8ba3', 1.2, 'door-line'));
    out.push(svgPath('M405 560 Q435 560 435 590', 'none', 'door-line', 'stroke-dasharray="2 3"'));

    ROOMS.forEach(function (room) {
      out.push(svgText(room.x + 14, room.y + 20, room.name, 'room-label'));
    });

    return out.join('');
  }

  function renderHome() {
    var data = state.data || {};
    var signature = homeSignature(data);
    if (signature === renderState.home) return;
    renderState.home = signature;
    var now = data.now || null;
    var kind = now ? now.kind : 'home';
    var room = roomFor(now);
    var floor = state.previewFloor || SceneStudio.floorFor(room);
    var rooms = SceneStudio.planRooms ? SceneStudio.planRooms(floor) : SceneStudio.rooms(floor);
    rooms.forEach(function(r) {
      var anchor = InteriorLayout.anchors[r.name];
      if (r.name === '车库') anchor = [120,120];
      if (r.name === '卧室' && now && now.state === 'sleep') anchor = [100,125];
      MARKER[r.name] = {x:(r.x+anchor[0])/((SceneStudio.width||840)/100),y:(r.y+anchor[1])/((SceneStudio.height||620)/100)};
    });
    $('home-stage').className = 'home-stage' + SceneStudio.classes(sceneEnvironment());
    document.querySelectorAll('.floor-tab').forEach(function(b) { b.classList.toggle('active', Number(b.dataset.floor) === floor); b.setAttribute('aria-pressed', Number(b.dataset.floor) === floor ? 'true' : 'false'); });
    $('floor-note').textContent = floor + 'F · ' + (floor === 1 ? '日常起居 / 餐厨 / 健身 / 车库' : '休息 / 创作 / 影音 / 露台');
    if (window.SceneStudio && SceneStudio.width) $('home-svg').setAttribute('viewBox', '0 0 ' + SceneStudio.width + ' ' + (SceneStudio.height || 620));
    $('home-svg').innerHTML = homeSvg(now);
    var marker = $('character-marker');
    var dim = $('home-dim');
    var badge = $('home-badge');
    if (kind === 'home' && room && floor === SceneStudio.floorFor(room)) {
      marker.classList.remove('hidden');
      var pos = MARKER[room] || { x: 50, y: 50 };
      marker.style.setProperty('--x', pos.x + '%');
      marker.style.setProperty('--y', pos.y + '%');
      marker.classList.toggle('sleeping', now && now.state === 'sleep');
      $('marker-name').textContent = data.persona || '角色';
      dim.classList.add('hidden');
      badge.className = 'pill green';
      badge.textContent = '当前 · ' + floor + 'F ' + room;
      $('home-effects').innerHTML = effectsMarkup(activityKey(now && now.activity), pos.x, pos.y);
    } else {
      marker.classList.add('hidden');
      dim.classList.remove('hidden');
      dim.querySelector('span').textContent = kind === 'home' ? '角色在 ' + SceneStudio.floorFor(room) + 'F' : kind === 'transit' ? '在路上' : '外出中';
      dim.querySelector('small').textContent = kind === 'home' ? '点击跟随角色可返回所在楼层' : kind === 'transit' ? '正在往返途中' : '家里暂时没人';
      badge.className = 'pill ' + (kind === 'transit' ? 'amber' : 'blue');
      badge.textContent = kind === 'home' ? '当前 · ' + SceneStudio.floorFor(room) + 'F ' + room : kind === 'transit' ? '在路上' : '外出中';
      $('home-effects').innerHTML = '';
    }
    renderGarageRoom();
  }

  function renderGarageRoom() {
    // Share the car's parked/out state with the 1F garage room (2D plan, close-up and 3D).
    var shared = (state.data && state.data.garage) || {}, sharedVehicle = shared.vehicle || {};
    window.VirtualLifeGarage = {
      mode: sharedVehicle.status === 'out' ? 'out' : 'parked|' + (sharedVehicle.plate || ''),
      plate: sharedVehicle.plate || '',
      vehicles: (shared.vehicles || []).map(function (item) {
        return {
          id: String(item.id || ''),
          plate: String(item.plate || ''),
          status: String(item.status || 'parked'),
          destination: String(item.destination || '')
        };
      })
    };
    var room = $('garage-room');
    var status = $('garage-room-status');
    if (!room || !status) return;
    var garage = (state.data && state.data.garage) || {};
    var vehicle = garage.vehicle || {};
    var trip = garage.trip || {};
    var isOut = vehicle.status === 'out';
    if (state.lastGarageStatus === 'out' && !isOut) {
      showToast('车已经回来了');
    }
    state.lastGarageStatus = isOut ? 'out' : 'parked';
    room.classList.toggle('is-out', isOut);
    if (isOut) {
      var who = trip.driver === 'master' ? '主人开车' : '月月载你';
      status.textContent = '车不在 · ' + who + '去' +
        (trip.destination || '兜风') + ' · 预计 ' +
        garageTime(trip.eta) + ' 回来' +
        (garageEtaText(trip.eta) ? ' · ' + garageEtaText(trip.eta) : '');
    } else {
      var fuel = Number(vehicle.fuel || 0);
      status.textContent = (vehicle.name || '白色小车') +
        ' 已停好 · 油量 ' + fuel + '%' + (fuel <= 20 ? '（偏低）' : '');
      status.classList.toggle('low-fuel', fuel <= 20);
    }
  }

  function effectsMarkup(key, baseX, baseY) {
    var out = [];
    var x = Number(baseX) || 50;
    var y = Number(baseY) || 50;
    function add(cls, dx, dy, delay) {
      out.push('<span class="effect ' + cls + '" style="--x:' + (x + dx) + '%;--y:' +
        (y + dy) + '%;--delay:' + delay + 's"></span>');
    }
    if (key === 'bath') {
      for (var i = 0; i < 5; i++) add('steam', -12 + i * 6, -8 - (i % 2) * 3, i * 0.35);
      for (var b = 0; b < 7; b++) add('bubble', -14 + b * 5, 2 + (b % 3) * 3, b * 0.24);
    } else if (key === 'tidy') {
      for (var s = 0; s < 4; s++) add('sparkle', -14 + s * 9, -8 + (s % 2) * 8, s * 0.28);
      for (var box = 0; box < 2; box++) add('boxmark', -5 + box * 12, 4 + box * 4, box * 0.4);
    } else if (key === 'sleep') {
      for (var z = 0; z < 3; z++) add('zmark', 6 + z * 5, -10 - z * 5, z * 0.5);
    } else if (key === 'food') {
      for (var f = 0; f < 4; f++) add('steam', -8 + f * 5, -7 - (f % 2) * 3, f * 0.4);
    } else if (key === 'read') {
      for (var r = 0; r < 3; r++) add('sparkle', -10 + r * 10, -5 + (r % 2) * 6, r * 0.35);
    } else if (key === 'music') {
      for (var m = 0; m < 3; m++) add('note', -10 + m * 10, -8 - (m % 2) * 6, m * 0.5);
    } else if (key === 'tv') {
      for (var tv = 0; tv < 2; tv++) add('sparkle', -8 + tv * 14, -3, tv * 0.5);
    }
    return out.join('');
  }

  function placedSignature() {
    return (state.homeItems || [])
      .filter(function (item) { return item && item.place; })
      .map(function (item) {
        return [item.id, item.room, item.place.x, item.place.y].join(':');
      })
      .join('|');
  }

  function homeSignature(data) {
    var now = (data && data.now) || {};
    return [
      data && data.persona,
      data && data.plan_date,
      data && data.appearance && data.appearance.key,
      data && data.appearance && data.appearance.src,
      data && data.appearance && data.appearance.avatar_src,
      now.id,
      now.start,
      now.end,
      now.activity,
      now.location,
      now.kind,
      now.room,
      now.state,
      state.previewFloor || '',
      state.homeItems.length,
      placedSignature(),
      window.SceneStudio ? sceneEnvironment().signature : ''
    ].join('|');
  }

  function sceneSignature(data) {
    var now = (data && data.now) || {};
    return [
      data && data.persona,
      data && data.plan_date,
      data && data.appearance && data.appearance.key,
      data && data.appearance && data.appearance.src,
      data && data.appearance && data.appearance.avatar_src,
      now.id,
      now.start,
      now.end,
      now.activity,
      now.location,
      now.city || '',
      now.kind,
      now.room,
      now.state,
      now.availability,
      state.previewScene || '',
      state.previewRoom || '',
      state.placement ? state.placement.item + '|' + state.placement.room : '',
      state.indoorView ? 'indoor' : 'outdoor',
      state.homeItems.length,
      placedSignature(),
      window.SceneStudio ? sceneEnvironment().signature : '',
      // 画面模式切换或 3D 脚本加载完成时要重画场景
      (use3D() ? '3d' : '2d') + (lazy3d.worldReady ? '+world' : '')
    ].join('|');
  }

  function pickerSignature(data) {
    var now = (data && data.now) || {};
    return [
      data && data.persona,
      now.kind || '',
      now.scene || '',
      state.previewScene || ''
    ].join('|');
  }

  function characterArtSrc() {
    return (state.data && state.data.appearance && state.data.appearance.src) ||
      'assets/character_daily.png';
  }

  function standeeMarkup(extraClass) {
    return '<img class="standee ' + (extraClass || '') +
      '" src="' + escapeHtml((state.data && state.data.appearance || {}).src || 'assets/character_daily.png') + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt="角色立绘">';
  }

  function activityProps(key) {
    if (key === 'bath') {
      return [
        '<span class="prop-bubble pb1"></span>',
        '<span class="prop-bubble pb2"></span>',
        '<span class="prop-bubble pb3"></span>',
        '<span class="prop-bubble pb4"></span>'
      ].join('');
    }
    if (key === 'tidy') {
      return [
        '<span class="prop-box px1"></span>',
        '<span class="prop-box px2"></span>',
        '<span class="prop-box px3"></span>',
        '<span class="prop-spark sp1"></span>',
        '<span class="prop-spark sp2"></span>',
        '<span class="prop-spark sp3"></span>'
      ].join('');
    }
    if (key === 'sleep') {
      return [
        '<span class="prop-z pz1">Z</span>',
        '<span class="prop-z pz2">z</span>',
        '<span class="prop-z pz3">z</span>'
      ].join('');
    }
    if (key === 'food') {
      return [
        '<span class="prop-steam pst1"></span>',
        '<span class="prop-steam pst2"></span>',
        '<span class="prop-steam pst3"></span>'
      ].join('');
    }
    if (key === 'read') {
      return '<span class="prop-book"></span><span class="prop-spark sp1"></span><span class="prop-spark sp2"></span>';
    }
    if (key === 'music') {
      return [
        '<span class="prop-note pn1">♪</span>',
        '<span class="prop-note pn2">♫</span>',
        '<span class="prop-note pn3">♪</span>'
      ].join('');
    }
    if (key === 'tv') {
      return '<span class="prop-glow"></span>';
    }
    return '';
  }

