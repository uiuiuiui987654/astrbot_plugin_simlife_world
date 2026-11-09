/* Catalog pictures for home pieces that have no plan artwork of their own
   (fixtures, wall decor, lights, rugs, chairs). Drawn in the same 96x72 frame
   that ItemArtwork wraps, with the soft pastel palette of FurnitureArt. */
(function (root) {
  'use strict';
  var C = { wood:'#c9a57c', woodD:'#a98560', woodL:'#ddc39f', cream:'#f1e9d8', creamD:'#ddd2bc', sage:'#a8b89d', sageD:'#87997c', lav:'#c8b4cf', lavD:'#a995b3', blue:'#9fbccb', blueD:'#7d9aab', rose:'#e3b1ac', roseD:'#c98f8a', grey:'#9aa1a4', greyD:'#6f7679', dark:'#4c5257', gold:'#d9b46a', glass:'#cfe3e6', white:'#fbf8f1', leaf:'#8fae84', leafD:'#6f9468', cork:'#c99f73' };
  var S = 'stroke="#7d6b5533" stroke-width=".8"';
  function r(x, y, w, h, f, rx, ex) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (rx || 0) + '" fill="' + f + '" ' + (ex === undefined ? S : ex) + '/>'; }
  function e(cx, cy, rx, ry, f, ex) { return '<ellipse cx="' + cx + '" cy="' + cy + '" rx="' + rx + '" ry="' + ry + '" fill="' + f + '" ' + (ex === undefined ? S : ex) + '/>'; }
  function p(d, f, ex) { return '<path d="' + d + '" fill="' + f + '" ' + (ex === undefined ? S : ex) + '/>'; }
  function l(d, c, w) { return '<path d="' + d + '" fill="none" stroke="' + c + '" stroke-width="' + (w || 1.2) + '" stroke-linecap="round" stroke-linejoin="round"/>'; }
  function shadow(cx, w) { return e(cx || 48, 68, w || 38, 3.6, '#5d684b1f', ''); }
  function knob(x, y) { return e(x, y, 1.3, 1.3, C.gold, ''); }
  function picture(x, y, w, h, scene) {
    var s = r(x - 2, y - 2, w + 4, h + 4, C.woodD, 1.5) + r(x, y, w, h, scene === 'night' ? '#4f5d7a' : '#dfe9e2', .5, '');
    if (scene === 'night') s += e(x + w * .68, y + h * .32, w * .14, w * .14, '#f6e7b4', '') + e(x + w * .74, y + h * .28, w * .12, w * .12, '#4f5d7a', '') + e(x + w * .25, y + h * .3, .8, .8, '#fff', '') + e(x + w * .4, y + h * .55, .7, .7, '#fff', '');
    else if (scene === 'flower') s += e(x + w / 2, y + h * .78, w * .16, h * .1, C.rose, '') + l('M' + (x + w / 2) + ' ' + (y + h * .75) + 'V' + (y + h * .38), C.leafD, 1.2) + e(x + w / 2, y + h * .32, w * .14, w * .14, C.rose, '') + e(x + w * .4, y + h * .5, w * .1, w * .05, C.leaf, '');
    else if (scene === 'abstract') s += e(x + w * .35, y + h * .45, w * .22, w * .22, C.rose, '') + r(x + w * .48, y + h * .2, w * .34, h * .55, C.blue, 1, '') + l('M' + (x + 3) + ' ' + (y + h - 4) + 'Q' + (x + w / 2) + ' ' + (y + h * .5) + ' ' + (x + w - 3) + ' ' + (y + h * .7), C.gold, 1.6);
    else s += p('M' + x + ' ' + (y + h) + 'L' + (x + w * .35) + ' ' + (y + h * .45) + 'L' + (x + w * .58) + ' ' + (y + h * .72) + 'L' + (x + w * .78) + ' ' + (y + h * .5) + 'L' + (x + w) + ' ' + (y + h) + 'Z', C.sage, '') + e(x + w * .75, y + h * .25, w * .08, w * .08, '#f2d38f', '');
    return s;
  }
  function lowCabinet(top, opts) {
    opts = opts || {};
    var x = opts.x || 14, w = opts.w || 68, y = opts.y || 34, h = 64 - y, col = opts.col || C.wood;
    var s = shadow(48, w / 2 + 4) + r(x, y, w, h, col, 2) + r(x - 1.5, y - 3, w + 3, 4, opts.topCol || C.woodD, 1.5);
    var n = opts.doors || 2;
    for (var i = 0; i < n; i++) { var dx = x + 3 + i * (w - 6) / n; s += r(dx, y + 4, (w - 6) / n - 2, h - 9, opts.panel || C.woodL, 1.5) + knob(dx + ((w - 6) / n - 2) / 2, y + 8); }
    s += r(x + 3, 64, 3, 3, C.woodD, .5, '') + r(x + w - 6, 64, 3, 3, C.woodD, .5, '');
    return s + (top || '');
  }
  function chair(seat, back, opts) {
    opts = opts || {};
    var wood = opts.wood || C.wood;
    var s = shadow(48, 22) + l('M34 44L30 66M62 44L66 66M38 46L36 64M58 46L60 64', C.woodD, 2.4);
    s += r(28, 40, 40, 7, wood, 2) + r(30, 36, 36, 6, seat, 3);
    if (back) s += r(32, 8, 32, 28, wood, 3) + r(35, 11, 26, 18, back, 3) + l('M33 36V12M63 36V12', C.woodD, 2.2);
    return s;
  }
  function lamp(shade, glow) {
    return r(46.5, 4, 3, 22, C.greyD, 1, '') + p('M34 44L40 26H56L62 44Z', shade) + e(48, 44, 14, 3, glow || '#f8e2a8', '') + e(48, 50, 9, 2.5, '#f8e2a855', '');
  }
  function rug(fill, edge, round) {
    if (round) return shadow(48, 40) + e(48, 50, 40, 16, fill) + e(48, 50, 30, 11, edge, '') + e(48, 50, 18, 6.5, fill, '');
    return shadow(48, 44) + p('M10 40L86 40L92 62L4 62Z', fill) + p('M15 44L81 44L85 58L11 58Z', 'none', 'stroke="' + edge + '" stroke-width="2"') + l('M4 62v4M12 62v4M20 62v4M76 62v4M84 62v4M92 62v4', edge, 1);
  }
  var A = {
    kitchen_sink: function () { return lowCabinet(r(24, 26, 30, 6, C.grey, 2) + r(27, 27, 24, 4, '#c7d1d4', 1.5, '') + l('M58 30V18q0-4 4-4h4', C.greyD, 2.2) + r(64, 13, 5, 3, C.greyD, 1, '') + r(62, 26, 12, 6, C.creamD, 1.5), { col: C.cream, panel: C.white, topCol: C.grey }); },
    vanity_counter: function () { return lowCabinet(e(38, 30, 12, 3.5, C.white) + e(38, 30, 8, 2.2, C.glass, '') + l('M38 28v-8q0-3 3-3', C.greyD, 2) + r(56, 22, 5, 9, C.blue, 2) + r(64, 24, 6, 7, C.rose, 2) + r(32, 2, 32, 16, C.glass, 2, 'stroke="' + C.greyD + '" stroke-width="1.6"'), { col: C.cream, panel: C.white, y: 32 }); },
    kitchen_north: function () {
      var s = r(10, 2, 76, 16, C.cream, 2) + r(13, 4, 22, 12, C.white, 1.5) + r(38, 4, 22, 12, C.white, 1.5) + r(63, 4, 20, 12, C.white, 1.5) + knob(24, 14) + knob(49, 14) + knob(73, 14);
      return s + lowCabinet(r(20, 29, 20, 4, C.dark, 1) + e(25, 30.5, 3.4, 1.3, '#7b8287', '') + e(35, 30.5, 3.4, 1.3, '#7b8287', '') + r(52, 28, 22, 5, C.grey, 1.5) + l('M70 28V21q0-3 3-3', C.greyD, 1.8) + r(44, 24, 5, 7, C.sage, 1.5), { w: 76, x: 10, doors: 3, col: C.cream, panel: C.white, topCol: C.creamD });
    },
    kitchen_right: function () { return shadow(48, 34) + r(16, 4, 26, 60, C.cream, 2) + r(19, 7, 20, 26, C.white, 1.5) + r(19, 36, 20, 25, C.white, 1.5) + knob(36, 30) + knob(36, 39) + r(44, 34, 36, 30, C.cream, 2) + r(42, 31, 40, 4, C.creamD, 1.5) + r(47, 38, 30, 22, C.white, 1.5) + knob(62, 42) + e(54, 28, 5, 3, C.rose) + r(66, 22, 8, 9, C.sage, 2); },
    bath_ledge: function () { var s = shadow(48, 40) + r(10, 44, 76, 20, '#e6ecea', 2); for (var i = 0; i < 6; i++) s += l('M' + (14 + i * 12.5) + ' 46V62', '#cfd8d6', .8); return s + l('M10 54H86', '#cfd8d6', .8) + r(8, 41, 80, 4, C.white, 1.5) + r(18, 28, 7, 13, C.blue, 2.5) + r(28, 32, 6, 9, C.rose, 2.5) + e(48, 38, 7, 3, C.sage) + e(48, 36, 5, 2, '#c3d1b9', '') + r(62, 30, 10, 11, C.lav, 2) + p('M74 41q6-14 10 0Z', C.leaf); },
    nightstand: function () { return shadow(48, 22) + r(30, 30, 36, 34, C.wood, 2) + r(28.5, 27, 39, 4, C.woodD, 1.5) + r(33, 34, 30, 11, C.woodL, 1.5) + r(33, 48, 30, 12, C.woodL, 1.5) + knob(48, 39.5) + knob(48, 54) + r(34, 64, 3, 3, C.woodD, .5, '') + r(59, 64, 3, 3, C.woodD, .5, '') + r(46.5, 12, 3, 15, C.greyD, 1, '') + p('M38 14L42 4H54L58 14Z', '#f3e3c3') + r(56, 22, 9, 5, C.lav, 1); },
    record_console: function () { return lowCabinet(r(22, 24, 30, 6, C.dark, 1.5) + e(37, 26.5, 11, 2.2, '#2b2e33', '') + e(37, 26.5, 3, .9, C.rose, '') + l('M50 25L44 27', C.grey, 1.2) + r(58, 18, 16, 12, C.woodD, 1.5) + e(66, 24, 4, 4, C.dark, ''), { doors: 3 }); },
    aquarium_console: function () { var s = lowCabinet('', { y: 44, col: C.woodD, panel: C.wood }); return s + r(16, 10, 64, 32, '#bfe0e6', 2, 'stroke="' + C.greyD + '" stroke-width="1.4"') + r(16, 10, 64, 6, '#e8f3f2', 1.5, '') + p('M18 40q6-14 8 0M28 40q4-18 7 0M64 40q5-12 8 0', C.leafD, '') + p('M42 24q6-4 10 0q-4 4-10 0l-4-3v6z', '#f2a65a', '') + p('M58 30q4-3 7 0q-3 3-7 0l-3-2v4z', '#f6d28a', '') + e(30, 20, 1.2, 1.2, '#fff', '') + e(32, 16, .9, .9, '#fff', '') + r(16, 38, 64, 4, '#e3d6bc', 0, ''); },
    media_console: function () { return lowCabinet(r(20, 22, 10, 10, C.dark, 2) + e(25, 27, 3, 3, '#6d737a', '') + r(66, 22, 10, 10, C.dark, 2) + e(71, 27, 3, 3, '#6d737a', '') + r(38, 26, 20, 5, C.dark, 1.5) + e(42, 28.5, 1, 1, '#7fd18e', ''), { w: 76, x: 10, doors: 3, y: 36 }); },
    popcorn_console: function () { return lowCabinet(r(24, 6, 24, 24, '#c8564a', 2) + r(27, 9, 18, 15, '#fff6e4', 1.5) + e(32, 20, 2, 2, '#f6dfa0', '') + e(37, 18, 2, 2, '#f6dfa0', '') + e(41, 21, 2, 2, '#f6dfa0', '') + e(35, 22, 2, 2, '#f6dfa0', '') + r(22, 4, 28, 4, C.gold, 1.5) + r(58, 20, 10, 12, '#e8554a', 1.5) + p('M58 20l2-5h6l2 5z', '#fff6e4', '') + r(70, 24, 8, 8, C.white, 2), { col: '#5d5168', panel: '#7a6c86', topCol: '#463d51' }); },
    hall_shelf: function () { return shadow(48, 36) + r(14, 10, 4, 56, C.woodD, 1) + r(78, 10, 4, 56, C.woodD, 1) + r(14, 10, 68, 4, C.wood, 1) + r(14, 34, 68, 4, C.wood, 1) + r(14, 58, 68, 4, C.wood, 1) + r(20, 20, 18, 14, '#d9c29a', 3) + l('M22 24h14', '#bfa47b', 1) + r(42, 22, 14, 12, C.sage, 3) + p('M62 34q2-14 8-14q6 0 8 14z', C.leaf) + r(22, 44, 26, 14, C.cream, 2) + l('M26 48h18', C.creamD, 1) + p('M56 58l3-12h10l3 12z', C.woodL); },
    spice_shelf: function () { var s = shadow(48, 34) + r(12, 22, 72, 4, C.wood, 1) + r(12, 46, 72, 4, C.wood, 1) + l('M18 26v6M78 26v6M18 50v6M78 50v6', C.woodD, 2); var cols = [C.rose, C.gold, C.sage, '#c8564a', C.blue, C.lav]; for (var i = 0; i < 6; i++) { s += r(16 + i * 11, 10, 8, 12, '#eef4f2', 2) + r(16 + i * 11, 8, 8, 4, C.dark, 1.2, '') + r(17.5 + i * 11, 15, 5, 6, cols[i], 1, ''); s += r(16 + i * 11, 34, 8, 12, '#eef4f2', 2) + r(16 + i * 11, 32, 8, 4, C.woodD, 1.2, '') + r(17.5 + i * 11, 39, 5, 6, cols[(i + 3) % 6], 1, ''); } return s; },
    wall_shelf: function () { return shadow(48, 30) + r(14, 40, 68, 5, C.wood, 1.5) + l('M22 45v8M74 45v8', C.woodD, 2) + r(20, 18, 5, 22, C.blue, 1) + r(26, 21, 5, 19, C.rose, 1) + r(32, 16, 5, 24, C.sage, 1) + p('M38 40l4-20 4 1-3 19z', C.gold) + e(62, 36, 9, 4, '#d9a37e') + p('M54 34q8-22 16 0z', C.leaf) + r(72, 28, 8, 12, C.lav, 2); },
    kitchen_chair: function () { return chair(C.sage, null, { wood: C.woodL }) + r(32, 4, 32, 6, C.woodL, 2) + l('M34 10V36M62 10V36M40 10V36M48 10V36M56 10V36', C.wood, 2); },
    dining_chair: function () { return chair(C.sage, '#d7e0cc'); },
    desk_chair: function () { return shadow(48, 22) + l('M48 50V60M36 64L48 60L60 64M48 60V66', C.greyD, 2.4) + e(36, 65, 2.5, 2.5, C.dark, '') + e(60, 65, 2.5, 2.5, C.dark, '') + e(48, 67, 2.5, 2.5, C.dark, '') + r(30, 42, 36, 8, C.dark, 4) + r(33, 8, 30, 34, '#5d6a72', 6) + r(36, 11, 24, 26, '#76848c', 5, '') + l('M28 40v-8h6M68 40v-8h-6', C.greyD, 2); },
    art_chair: function () { return shadow(48, 18) + l('M38 34L32 66M58 34L64 66M44 36L44 64M52 36L52 64M35 52H61', C.woodD, 2.4) + e(48, 32, 16, 5, C.wood) + e(48, 30, 13, 3.5, C.woodL, '') + e(44, 30, 2, 1, '#c8786a', '') + e(53, 31, 1.5, .8, '#7fb3e6', ''); },
    piano_bench: function () { return shadow(48, 32) + l('M22 42L20 66M74 42L76 66M28 44L28 64M68 44L68 64', '#3a3434', 2.6) + r(16, 34, 64, 10, '#3a3434', 2) + r(18, 28, 60, 8, '#6a5560', 4) + l('M24 32h48', '#7c6672', 1); },
    ottoman: function () { return shadow(48, 26) + r(24, 34, 48, 28, C.lav, 8) + e(48, 34, 24, 7, '#d8c8de') + l('M30 40q18 6 36 0', C.lavD, 1) + e(48, 34, 2, 1.2, C.lavD, '') + r(28, 61, 4, 5, C.woodD, 1, '') + r(64, 61, 4, 5, C.woodD, 1, ''); },
    slippers: function () { return shadow(48, 30) + p('M22 60q-6-22 6-28q10-2 10 10l1 18q0 4-8 4h-6q-3 0-3-4z', C.rose) + p('M23 46q8-6 15 0v8H23z', '#f4d6d2') + p('M56 62q-6-22 6-28q10-2 10 10l1 18q0 4-8 4h-6q-3 0-3-4z', C.rose) + p('M57 48q8-6 15 0v8H57z', '#f4d6d2') + e(30, 47, 2, 2, '#fff', '') + e(64, 49, 2, 2, '#fff', ''); },
    weights_rack: function () { var s = shadow(48, 36) + l('M18 64L22 14M78 64L74 14M20 40H76M21 26H75', C.greyD, 3); [[30, 22, 4.5], [48, 22, 5], [66, 22, 5.5], [30, 36, 6], [48, 36, 6.5], [66, 36, 7]].forEach(function (d) { s += r(d[0] - 7, d[1] + 1, 14, 2.2, C.grey, 1, '') + r(d[0] - 9, d[1] + 2 - d[2] / 2 + 1, 4, d[2] + 1, C.dark, 1.5, '') + r(d[0] + 5, d[1] + 2 - d[2] / 2 + 1, 4, d[2] + 1, C.dark, 1.5, ''); }); return s + e(48, 58, 12, 6, '#5f7e9b') + e(48, 56, 9, 3.5, '#7d9aab', ''); },
    art_workbench: function () { return shadow(48, 40) + l('M14 36L12 66M82 36L84 66M20 38L20 64M76 38L76 64', C.woodD, 2.6) + r(8, 30, 80, 7, C.wood, 2) + p('M8 30h80', 'none', 'stroke="#e3b1ac" stroke-width="1.2" stroke-dasharray="3 5"') + r(16, 18, 8, 12, C.cream, 2) + l('M18 18l-3-10M21 18l1-11M23 18l4-9', C.woodD, 1.2) + e(36, 28, 7, 2.5, C.white) + e(34, 28, 1.8, 1, '#c8564a', '') + e(38, 27.5, 1.8, 1, '#7fb3e6', '') + e(37, 29, 1.6, .9, '#f2c14e', '') + r(48, 22, 9, 8, '#7fb3e6', 1.5) + r(59, 24, 8, 6, '#c8564a', 1.5) + r(70, 14, 12, 16, C.white, 1, 'stroke="' + C.woodD + '" stroke-width="1.2"') + l('M72 22q4-4 8 2', C.rose, 1.2); },
    gym_ball: function () { return shadow(48, 26) + e(48, 38, 26, 26, '#7fb3e6') + p('M28 22q20 10 40 0', 'none', 'stroke="#a8cbe9" stroke-width="3"') + p('M24 44q24 12 48 0', 'none', 'stroke="#5f93c4" stroke-width="2"') + e(40, 26, 6, 3, '#ffffff55', ''); },
    canvas: function (scene) { return shadow(48, 24) + l('M34 14L24 66M62 14L72 66M48 8V58', C.woodD, 2.4) + r(28, 40, 40, 3, C.woodD, 1, '') + picture(30, 12, 36, 26, scene); },
    canvas_stack: function () { return shadow(48, 34) + p('M16 64L22 18L50 16L46 64Z', C.white) + p('M28 64L32 24L60 22L58 64Z', '#f3efe6') + picture(44, 26, 32, 36, 'abstract') + l('M44 64H78', C.woodD, 2); },
    acoustic: function () { var s = shadow(48, 34) + r(14, 8, 68, 56, '#3e3a4a', 2); for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) s += r(17 + i * 22, 11 + j * 17.5, 20, 15.5, ['#6a5f86', '#5b5270', '#7a6c96'][(i + j) % 3], 2, ''); return s + l('M20 18h14M42 35h14M64 52h12', '#ffffff22', 1); },
    sconce: function () { return shadow(48, 16) + r(44, 20, 8, 22, C.woodD, 2) + l('M48 28h8v-6', C.gold, 2) + p('M48 22L52 6H64L68 22Z', '#f3e3c3') + e(58, 22, 10, 2.5, '#f8e2a8', '') + e(58, 34, 12, 8, '#f8e2a833', ''); },
    pendant: function () { return shadow(48, 20) + l('M48 0V20', C.greyD, 1.2) + p('M32 40Q32 20 48 20Q64 20 64 40Z', C.sage) + e(48, 40, 16, 3, '#f8e2a8', '') + e(48, 48, 6, 4, '#fbe9b9', '') + p('M30 64Q48 44 66 64Z', '#f8e2a822', ''); },
    chandelier: function () { var s = shadow(48, 24) + l('M48 0V16', C.gold, 1.4) + e(48, 20, 6, 4, C.gold) + l('M48 22Q30 22 24 36M48 22Q66 22 72 36M48 22V38M48 22Q38 26 36 40M48 22Q58 26 60 40', C.gold, 1.6); [[24, 36], [72, 36], [48, 38], [36, 40], [60, 40]].forEach(function (q) { s += r(q[0] - 2, q[1], 4, 8, C.white, 1) + p('M' + q[0] + ' ' + (q[1] - 5) + 'q2 3 0 5q-2-2 0-5z', '#f6c86a', '') + e(q[0], q[1] - 1, 5, 4, '#f8e2a844', ''); }); return s + e(48, 48, 3, 4, C.glass); },
    framed: function (scene, round) { if (round) return shadow(48, 20) + e(48, 36, 26, 26, C.woodD) + e(48, 36, 22, 22, '#4f5d7a', '') + e(54, 30, 9, 9, '#f6e7b4', '') + e(58, 27, 8, 8, '#4f5d7a', '') + e(36, 28, 1, 1, '#fff', '') + e(42, 46, .8, .8, '#fff', '') + e(60, 46, .9, .9, '#fff', ''); return shadow(48, 26) + picture(24, 10, 48, 44, scene); },
    gallery: function () { return shadow(48, 38) + picture(12, 10, 26, 20, 'land') + picture(44, 6, 18, 26, 'flower') + picture(68, 12, 18, 18, 'abstract') + picture(20, 38, 20, 22, 'abstract') + picture(48, 40, 30, 20, 'land'); },
    clock: function (digital) { if (digital) return shadow(48, 26) + r(22, 22, 52, 26, C.dark, 5) + r(26, 26, 44, 18, '#1f2328', 3, '') + '<text x="48" y="40" text-anchor="middle" font-family="monospace" font-size="13" font-weight="700" fill="#ff8a66">07:30</text>'; var s = shadow(48, 22) + e(48, 34, 26, 26, C.woodD) + e(48, 34, 22, 22, C.white, ''); for (var i = 0; i < 12; i++) { var a = i * Math.PI / 6; s += l('M' + (48 + Math.sin(a) * 18) + ' ' + (34 - Math.cos(a) * 18) + 'L' + (48 + Math.sin(a) * 20) + ' ' + (34 - Math.cos(a) * 20), C.greyD, i % 3 ? 1 : 2); } return s + l('M48 34L48 20M48 34L58 39', C.dark, 2) + e(48, 34, 1.8, 1.8, C.rose, ''); },
    laundry_rack: function () { var s = shadow(48, 38) + l('M16 66L30 18M80 66L66 18M30 66L22 40M66 66L74 40', C.grey, 2) + l('M22 26H74M20 34H76M18 42H78', C.grey, 1.6); return s + p('M28 26h14v18l-2 6h-10l-2-6z', C.blue) + p('M46 26h10v22h-10z', C.rose) + p('M60 26h12l-2 14h-8z', C.cream) + l('M30 26v-2M40 26v-2M48 26v-2M54 26v-2M62 26v-2M70 26v-2', C.greyD, 1); },
    lantern: function () { return shadow(48, 18) + l('M40 12Q48 0 56 12', C.dark, 1.6) + r(38, 12, 20, 6, C.dark, 2) + r(38, 46, 20, 6, C.dark, 2) + r(40, 18, 16, 28, '#f8e6b8', 2, 'stroke="' + C.dark + '" stroke-width="1.4"') + l('M44 18v28M52 18v28', C.dark, 1) + e(48, 32, 4, 7, '#ffd48a', '') + e(48, 32, 14, 16, '#f8e2a833', '') + r(40, 52, 16, 12, C.dark, 2); },
    facade_sconce: function () { return shadow(48, 16) + r(40, 10, 16, 6, C.dark, 1.5) + r(42, 16, 12, 24, '#f8e6b8', 1.5, 'stroke="' + C.dark + '" stroke-width="1.6"') + l('M48 16v24', C.dark, 1) + p('M38 16L48 6L58 16Z', C.dark) + r(44, 40, 8, 4, C.dark, 1, '') + r(46, 44, 4, 10, C.dark, 1, '') + r(40, 54, 16, 6, C.dark, 1.5) + e(48, 28, 12, 14, '#f8e2a833', ''); },
    string_lights: function () { var s = shadow(48, 38) + l('M6 14Q27 34 48 18Q69 34 90 14', C.dark, 1.2); [[14, 21], [24, 26], [34, 25], [42, 21], [54, 21], [62, 25], [72, 26], [82, 21]].forEach(function (q, i) { s += r(q[0] - 1, q[1], 2, 3, C.dark, .5, '') + e(q[0], q[1] + 6, 3, 4, ['#ffd48a', '#f6b6a6', '#bfe0a8', '#a8d0f0'][i % 4], '') + e(q[0], q[1] + 6, 7, 8, '#ffe0a633', ''); }); return s; },
    doormat: function () { return shadow(48, 40) + p('M14 42L82 42L88 62L8 62Z', '#b98a5a') + p('M19 45L77 45L81 59L15 59Z', '#a07548', '') + '<text x="48" y="56" text-anchor="middle" font-family="sans-serif" font-size="9" font-weight="700" fill="#e8d2ad" transform="skewX(-8)">WELCOME</text>'; },
    bath_mat: function () { var s = shadow(48, 38) + p('M14 40L82 40L88 62L8 62Z', '#b7d6d0'); for (var i = 0; i < 7; i++) s += l('M' + (18 + i * 10) + ' 42L' + (14 + i * 11.5) + ' 60', '#d5ebe6', 2); return s; },
    runner: function () { return rug(C.rose, '#f3e3d6'); },
    terrace_rug: function () { var s = rug('#d9c08a', '#9b8458'); return s + l('M30 44L26 58M48 44V58M66 44L70 58', '#b89c68', 2); },
    round_rug: function () { return rug('#c8b4cf', '#e7dcea', true); },
    coat_hooks: function () { return shadow(48, 30) + r(14, 10, 68, 7, C.wood, 2) + [24, 40, 56, 72].map(function (x) { return l('M' + x + ' 17v5q0 3 3 3', C.gold, 2); }).join('') + p('M30 24q-8 0-10 14l-2 24h22l-2-24q-2-14-8-14z', '#7d8f78') + l('M30 26v34', '#6a7a64', 1) + p('M52 24q-6 2-6 8h14q0-6-6-8z', '#c8786a') + p('M44 32h18v2H44z', '#a85c52', '') + p('M70 26l-4 30h8z', '#e3c48a') + l('M70 26v-1', C.woodD, 1); },
    hall_mirror: function () { return shadow(48, 20) + r(32, 2, 32, 64, C.woodD, 16) + r(35, 5, 26, 58, '#dbe8ea', 13, '') + p('M40 14l8-6v14l-8 6zM44 34l10-8v8l-10 8z', '#ffffff88', ''); },
    pinboard: function () { return shadow(48, 34) + r(14, 8, 68, 52, C.woodD, 2) + r(17, 11, 62, 46, C.cork, 1, '') + r(22, 16, 16, 14, '#fff6c8', 0, '') + r(42, 14, 14, 18, '#f4d6d2', 0, '') + r(60, 18, 14, 12, '#cfe3e6', 0, '') + r(26, 36, 22, 16, C.white, 0, '') + picture(54, 36, 18, 14, 'land') + e(30, 17, 1.5, 1.5, '#c8564a', '') + e(49, 15, 1.5, 1.5, '#5f7e9b', '') + e(67, 19, 1.5, 1.5, '#c8564a', '') + l('M29 42h14M29 46h10', C.greyD, 1); },
    towel_hook: function () { return shadow(48, 18) + r(40, 6, 16, 6, C.gold, 2) + l('M48 12v6', C.gold, 2) + p('M34 18h28l-2 42h-24z', C.blue) + p('M36 50h24v4H36z', C.blueD, '') + l('M40 22v26', '#c3d8e2', 1.4); },
    water_bottle: function () { return shadow(48, 12) + r(40, 18, 16, 46, '#7fb3e6', 6) + r(42, 26, 12, 30, '#a8cbe9', 4, '') + r(42, 10, 12, 9, C.dark, 2) + l('M54 13q8 0 8 8', C.dark, 2) + r(43, 40, 10, 6, C.white, 1, ''); },
    clothes_rail: function () { var s = shadow(48, 36) + l('M16 64V10M80 64V10M16 10H80M10 64h12M74 64h12', C.greyD, 2.4); [[20, C.rose, 34], [30, C.blue, 40], [40, C.cream, 30], [50, C.sage, 42], [60, C.lav, 36], [70, '#e3c48a', 32]].forEach(function (c) { s += l('M' + (c[0] + 4) + ' 10v3', C.greyD, 1) + p('M' + c[0] + ' 14h9l1 ' + c[2] + 'h-11z', c[1]); }); return s; },
    storage_bench: function () { return shadow(48, 36) + r(12, 34, 72, 30, C.wood, 2) + r(10, 28, 76, 8, '#cdbfd8', 4) + l('M16 32h64', C.lavD, 1) + r(16, 40, 20, 20, C.woodL, 1.5) + r(38, 40, 20, 20, C.woodL, 1.5) + r(60, 40, 20, 20, C.woodL, 1.5) + p('M18 46h16v12H18z', '#d9c29a') + p('M40 46h16v12H40z', '#c8b08a') + l('M20 50h12M42 50h12', '#b99e75', 1) + r(64, 48, 12, 10, C.sage, 2) + r(30, 20, 14, 8, C.rose, 3) + r(52, 22, 10, 6, C.blue, 3); },
    bath_towel: function () { return shadow(48, 26) + r(22, 8, 52, 4, C.gold, 2) + p('M26 12h44v40q0 4-4 4H30q-4 0-4-4z', '#f0c9cf') + p('M26 12h44v10H26z', '#e6b3bb', '') + l('M26 46h44M26 50h44', '#fbe3e6', 1.4) + p('M40 56h16v8H40z', '#e6b3bb'); },
    yoga_mat: function () { return shadow(48, 36) + p('M12 58L60 46L84 54L36 66Z', C.sage) + l('M18 58L60 48M24 60L66 50', '#c3d1b9', 1) + e(72, 44, 12, 12, '#93a88a') + e(72, 44, 8, 8, '#b5c6aa', '') + e(72, 44, 4, 4, '#93a88a', ''); },
    blanket: function () { return shadow(48, 32) + r(16, 40, 64, 24, C.lav, 5) + r(18, 28, 60, 14, '#d8c8de', 5) + r(20, 18, 56, 12, C.lav, 5) + l('M24 24h48M22 35h52M20 50h56', '#e7dcea', 1.4) + [24, 34, 44, 54, 64, 72].map(function (x) { return l('M' + x + ' 64v3', C.lavD, 1); }).join(''); },
    game_console: function () { return shadow(48, 32) + r(14, 34, 40, 26, '#e9ecef', 3) + r(14, 34, 40, 6, '#d7dce0', 3, '') + e(22, 50, 2, 2, '#7fd18e', '') + r(30, 48, 18, 2, '#c4cbd0', 1, '') + p('M58 52q0-8 8-8h12q8 0 8 8q0 8-6 8q-4 0-6-4h-4q-2 4-6 4q-6 0-6-8z', C.dark) + l('M66 50v6M63 53h6', '#c4cbd0', 1.6) + e(78, 51, 1.6, 1.6, '#e8857a', '') + e(82, 54, 1.6, 1.6, '#7fb3e6', ''); },
    delivery_box: function () { return shadow(48, 32) + p('M20 30L48 22L76 30L76 60L48 68L20 60Z', '#d4a873') + p('M20 30L48 38L76 30L48 22Z', '#e5bf8d') + p('M48 38V68', 'none', 'stroke="#b88a55" stroke-width="1"') + p('M30 27L58 35V42L52 40V33L24 25Z', '#c49a68', '') + r(54, 46, 14, 9, C.white, 1, '') + l('M56 49h10M56 52h7', C.greyD, .8); },
    shoe_cabinet: function () { return lowCabinet(r(22, 26, 14, 6, C.rose, 3) + r(40, 26, 14, 6, C.blue, 3) + r(58, 27, 12, 5, C.sage, 2.5), { y: 34, doors: 2 }) + l('M17 44h62', C.woodD, .8) + l('M20 41l4 2M28 41l4 2M60 41l4 2M68 41l4 2', '#00000022', 1); },
    sideboard: function () { return lowCabinet(e(30, 28, 6, 3, C.white) + p('M26 28q4-12 8 0z', C.leaf, '') + r(46, 20, 8, 12, C.rose, 3) + r(60, 26, 16, 5, C.cream, 1.5) + r(62, 22, 12, 5, C.blue, 1.5), { w: 76, x: 10, doors: 3, y: 34 }); },
    vacuum: function () { return shadow(48, 24) + l('M44 8V50', C.greyD, 3) + r(38, 6, 12, 8, C.dark, 3) + r(40, 20, 16, 24, '#7fb3e6', 6) + r(43, 24, 10, 12, '#bcd8ee', 4, '') + p('M30 58h40q4 0 4 4v2H26v-2q0-4 4-4z', C.dark) + l('M44 50l-6 8', C.greyD, 3); },
    sewing_kit: function () { return shadow(48, 30) + r(18, 34, 60, 28, '#e3b1ac', 4) + r(16, 28, 64, 10, '#c98f8a', 4) + r(40, 30, 16, 4, C.gold, 2, '') + e(28, 22, 6, 6, '#7fb3e6') + e(28, 22, 2, 2, '#fff', '') + e(44, 22, 6, 6, C.sage) + e(44, 22, 2, 2, '#fff', '') + r(56, 16, 14, 10, C.lav, 2) + l('M60 14l14-10', C.greyD, 1.2) + l('M24 46q24 8 48 0', '#f4d6d2', 1.4); },
    tree: function () { return shadow(48, 18) + r(38, 48, 20, 16, '#d9a37e', 3) + l('M48 48V26', C.woodD, 3) + e(48, 22, 20, 18, C.leaf) + e(38, 28, 10, 9, C.leafD, '') + e(58, 18, 10, 9, '#a5c39a', ''); }
  };
  var MAP = {
    kitchen_sink: 'kitchen_sink', vanity_counter: 'vanity_counter', kitchen_north: 'kitchen_north', kitchen_right: 'kitchen_right', bath_ledge: 'bath_ledge',
    nightstand: 'nightstand', record_console: 'record_console', aquarium_console: 'aquarium_console', media_console: 'media_console', popcorn_console: 'popcorn_console',
    hall_shelf: 'hall_shelf', spice_shelf: 'spice_shelf', wall_shelf: 'wall_shelf', kitchen_chair: 'kitchen_chair', dining_chair_l1: 'dining_chair', dining_chair_l2: 'dining_chair',
    dining_chair_r1: 'dining_chair', dining_chair_r2: 'dining_chair', desk_chair: 'desk_chair', art_chair: 'art_chair', piano_bench: 'piano_bench', ottoman: 'ottoman', slippers: 'slippers',
    weights_rack: 'weights_rack', art_workbench: 'art_workbench', gym_ball: 'gym_ball', canvas_0: ['canvas', 'land'], canvas_1: ['canvas', 'flower'], canvas_r: ['canvas', 'abstract'],
    canvas_stack_0: 'canvas_stack', canvas_stack_1: 'canvas_stack', canvas_stack_2: 'canvas_stack', acoustic_left: 'acoustic', acoustic_right: 'acoustic', sconce_left: 'sconce', sconce_right: 'sconce',
    pendant: 'pendant', pendant_1: 'pendant', pendant_2: 'pendant', chandelier: 'chandelier', wall_art: ['framed', 'land'], dining_art: ['framed', 'flower'], hall_art: ['framed', 'abstract'],
    moon_art: ['framed', 'night', true], gallery: 'gallery', clock: 'clock', gym_clock: ['clock', true], laundry_rack: 'laundry_rack', lantern: 'lantern', facade_sconce: 'facade_sconce',
    string_lights: 'string_lights', doormat: 'doormat', bath_mat: 'bath_mat', runner: 'runner', terrace_rug: 'terrace_rug', round_rug: 'round_rug', coat_hooks: 'coat_hooks',
    hall_mirror: 'hall_mirror', pinboard: 'pinboard', towel_hook: 'towel_hook', water_bottle: 'water_bottle', clothes_rail: 'clothes_rail', tree: 'tree', storage_bench: 'storage_bench', bath_towel: 'bath_towel', yoga_mat: 'yoga_mat', blanket: 'blanket', game_console: 'game_console', delivery_box: 'delivery_box', shoe_cabinet: 'shoe_cabinet', sideboard: 'sideboard', vacuum: 'vacuum', sewing_kit: 'sewing_kit'
  };
  function draw(item) {
    var id = item && item.id != null ? String(item.id) : '', m = MAP[id];
    if (!m) return '';
    var fn = A[Array.isArray(m) ? m[0] : m], art = Array.isArray(m) ? fn(m[1], m[2]) : fn();
    return '<svg class="item-illustration" viewBox="-16 -12 128 97" aria-hidden="true" focusable="false">' + art + '</svg>';
  }
  root.FurnitureIcons = { draw: draw, has: function (id) { return !!MAP[id]; } };
})(window);
