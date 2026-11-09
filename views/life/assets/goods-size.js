/* Shared footprint (cm) for shop goods, so the 2D room and 3D room agree
   closely on how much floor/surface space an item takes. */
(function (root) {
  'use strict';
  var SIZE = {
    headphones: [20, 20], camera: [16, 10], keyboard: [36, 14], console: [27, 19],
    powerbank: [8, 14], speaker: [10, 10], tablet: [25, 18], wireless_mouse: [7, 12],
    smart_watch: [6, 5], game_pad: [16, 10], hard_drive: [9, 12], monitor_arm: [30, 15],
    charging_pad: [15, 12], webcam: [8, 8], earbuds: [6, 5],
    tshirt: [30, 16], hoodie: [30, 16], skirt: [32, 18], sneakers: [28, 12],
    pajamas: [30, 16], coat: [32, 18], cap: [24, 24], cardigan: [30, 16],
    long_skirt: [32, 18], canvas_shoes: [28, 12], beret: [24, 24],
    earrings: [12, 8], necklace: [16, 10], trench_coat: [34, 18],
    indoor_slippers: [26, 12], jeans: [30, 15], cotton_socks: [22, 10],
    pillow: [42, 42], diffuser: [12, 12], lamp: [32, 32], towel: [40, 25],
    rug: [100, 70], storage_box: [42, 32], humidifier: [22, 22], curtain: [120, 8],
    scented_candle: [10, 10], cushion_cover: [42, 42], tablecloth: [80, 50],
    storage_basket: [40, 40], vase: [16, 16], night_light: [12, 12],
    bath_mat: [70, 45], thin_blanket: [50, 36],
    paint_set: [30, 20], puzzle: [30, 22], flowers: [25, 25], plant: [32, 32],
    guitar: [45, 20], model_kit: [12, 12], journal: [15, 21], paint: [30, 20],
    yarn: [20, 20], washi_tape: [20, 15], instant_film: [10, 8],
    sketchbook: [24, 17], puzzle_500: [30, 22], plant_pot: [30, 30],
    guitar_strings: [15, 20], board_game: [40, 40],
    bracelet: [16, 10], scarf: [30, 15], music_box: [18, 12], candle: [10, 10],
    perfume: [10, 10], handwritten_card: [12, 10], plush_bear: [26, 20],
    music_box_gift: [18, 12], bracelet_gift: [16, 10], bouquet: [25, 25]
  };
  var BY_CATEGORY = {
    '数码': [20, 15], '穿搭': [30, 15], '居家': [25, 25],
    '兴趣': [25, 20], '礼物': [18, 18]
  };
  function footprint(item) {
    item = item || {};
    var id = String(item.possession_id || item.id || '');
    if (SIZE[id]) return SIZE[id];
    return BY_CATEGORY[String(item.category || '')] || [24, 24];
  }
  var SURFACE_CM = {
    coffee_table: 46, dining_table: 76, dining_room_table: 76, sideboard: 78,
    desk: 74, shoe_cabinet: 88, nightstand: 55, vanity_counter: 86,
    kitchen_north: 92, kitchen_right: 92, kitchen_sink: 46,
    media_console: 60, record_console: 60, aquarium_console: 58,
    popcorn_console: 90, hall_shelf: 88, bed: 60, sofa: 46,
    balcony_chair: 44, terrace_swing: 44
  };
  var NOT_SURFACEABLE = {
    rug: 1, bath_mat: 1, curtain: 1, tablecloth: 1, guitar: 1,
    storage_box: 1, storage_basket: 1, monitor_arm: 1, thin_blanket: 1
  };
  function surfaceHeight(id) {
    return SURFACE_CM[String(id || '')] || 0;
  }
  function smallEnoughForSurface(item) {
    item = item || {};
    var id = String(item.possession_id || item.id || '');
    if (NOT_SURFACEABLE[id]) return false;
    var f = footprint(item);
    return Math.max(f[0], f[1]) <= 48;
  }
  root.GoodsSize = {
    footprint: footprint,
    sizes: SIZE,
    surfaces: SURFACE_CM,
    surfaceHeight: surfaceHeight,
    smallEnoughForSurface: smallEnoughForSurface
  };
})(window);
