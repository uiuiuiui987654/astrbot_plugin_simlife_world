/* 由 views/life/src/app/ 下的片段生成，请勿直接修改；改完片段后运行 python tools/build_frontend.py */
(function () {
  'use strict';

  window.__VIRTUAL_LIFE_UI_VERSION = '20261110-perf3';
  console.log('[VirtualLife UI] ' + window.__VIRTUAL_LIFE_UI_VERSION);

  var $ = function (id) { return document.getElementById(id); };

  function storedSort(key, allowed, fallback) {
    try {
      var value = localStorage.getItem('vl-' + key);
      return allowed.indexOf(value) >= 0 ? value : fallback;
    } catch (error) {
      return fallback;
    }
  }

  function saveSort(key, value) {
    try {
      localStorage.setItem('vl-' + key, String(value || ''));
    } catch (error) {
      /* 忽略本地存储异常 */
    }
  }

  var state = {
    data: null,
    persona: null,
    previewScene: null,
    previewFloor: null,
    previewRoom: null,
    placement: null,
    indoorView: false,
    animations: true,
    renderMode: '',
    autoRenderReason: null,
    error: false,
    lastData: null,
    homeItems: [],
    wishes: [],
    decorMode: false,
    decorItems: [],
    decorDrag: null,
    decorSuppressClick: false,
    selectedItem: null,
    pendingItem: null,
    fridge: null,
    interaction: { busy: false },
    userSleeping: false,
    lastGarageStatus: null,
    garageData: null,
    lastAffectionLevel: null,
    lastAffectionScore: 0,
    memoryData: null,
    memoryQuery: '',
    memoryFilter: storedSort(
      'memory-filter',
      ['all', 'long', 'recent', 'relation'],
      'all'
    ),
    systemData: null,
    statusTrendMetric: storedSort(
      'status-trend-metric',
      ['mood', 'energy', 'satiety'],
      'mood'
    ),
    statusTrendRange: Number(storedSort(
      'status-trend-range',
      ['7', '14', '30'],
      '7'
    )),
    statusActivityHtml: '',
    statusActivityLoaded: false,
    statusActivityAt: 0,
    statusActivityLoading: false,
    bookFontScale: 1,
    bookTheme: 'dark',
    bookId: null,
    bookChapter: 1,
    bookChapters: 1,
    bookChapterTitles: [],
    bookNotes: [],
    bookNoteTotal: 0,
    bookNoteQuery: '',
    bookRestoreScroll: null,
    bookOpenedAt: 0,
    bookTitle: '',
    photos: loadStoredPhotos(),
    photoIndex: -1,
    garageHistoryExpanded: false,
    garageHistoryFilter: storedSort(
      'garage-history-filter',
      ['all', 'returned', 'active'],
      'all'
    ),
    relationsTimelineExpanded: false,
    diaryEntries: [],
    tripsData: null,
    tripsExpanded: {},
    tripsFilter: storedSort(
      'trips-filter',
      ['all', 'upcoming', 'ongoing', 'past'],
      'all'
    ),
    activityEvents: [],
    activityFilter: storedSort(
      'activity-filter',
      ['all', 'diary', 'world', 'cooking', 'money', 'garage', 'health'],
      'all'
    ),
    activityQuery: '',
    diaryQuery: '',
    diaryFilter: storedSort(
      'diary-filter',
      ['all', 'ai', 'weekly', 'special'],
      'all'
    ),
    shelfFilter: storedSort(
      'shelf-filter',
      ['all', 'finished', 'reading', 'unread'],
      'all'
    ),
    dayScheduleFilter: storedSort(
      'day-schedule-filter',
      ['all', 'home', 'outside', 'transit'],
      'all'
    ),
    inventoryQuery: '',
    shelfSort: storedSort(
      'shelf-sort',
      ['default', 'title', 'progress', 'notes', 'reading'],
      'default'
    ),
    readingGoal: Number(storedSort(
      'reading-goal',
      ['15', '30', '45', '60'],
      '30'
    )),
    itemQuery: '',
    fridgeQuery: '',
    cookFilter: 'all',
    cookingHistory: [],
    scheduleItem: null,
    shopItems: [],
    shopQuery: '',
    shopSort: storedSort(
      'shop-sort',
      ['default', 'name', 'price_asc', 'price_desc'],
      'default'
    ),
    shopOnlyFavorites: storedSort(
      'shop-favorites',
      ['0', '1'],
      '0'
    ) === '1',
    walletFilter: storedSort(
      'wallet-filter',
      ['all', 'income', 'expense'],
      'all'
    ),
    walletQuery: '',
    walletTransactions: [],
    weeklyDays: Number(storedSort('weekly-days', ['7', '30', '365'], '7')),
    weeklyMetric: storedSort('weekly-metric', ['mood', 'energy', 'satiety'], 'mood'),
    weeklyPrevious: null,
    weeklyChartTheme: storedSort('weekly-theme', ['dark', 'warm', 'light'], 'dark'),
    deliveryMap: null
  };
  var renderState = { home: '', scene: '', picker: '', next: '', timeline: '' };

  var SCENES = [
    { key: 'cafe', label: '咖啡馆' },
    { key: 'park', label: '公园' },
    { key: 'bookstore', label: '书店' },
    { key: 'museum', label: '美术馆' },
    { key: 'cinema', label: '电影院' },
    { key: 'beach', label: '海边' },
    { key: 'mall', label: '商场' },
    { key: 'office', label: '办公室' },
    { key: 'street', label: '老街' },
    { key: 'food', label: '食堂' },
    { key: 'supermarket', label: '超市' },
    { key: 'grocery', label: '杂货铺' },
    { key: 'market', label: '菜市场' },
    { key: 'nightmarket', label: '夜市' },
    { key: 'station', label: '车站' },
    { key: 'airport', label: '机场' },
    { key: 'hotel', label: '旅店' },
    { key: 'travel', label: '异乡' },
    { key: 'temple', label: '神社' },
    { key: 'onsen', label: '温泉' },
    { key: 'harbor', label: '港口' },
    { key: 'mountain', label: '山野' },
    { key: 'izakaya', label: '小酒馆' },
    { key: 'transit', label: '路上' },
    { key: 'generic', label: '城市' }
  ];

  if (window.SceneStudio) SCENES = SCENES.concat(SceneStudio.newScenes);

  var SCENE_INTERIORS = {
    cafe: '咖啡馆', park: '公园', bookstore: '书店', museum: '美术馆',
    cinema: '电影院', beach: '海边', mall: '商场', office: '办公室',
    street: '老街', food: '食堂', supermarket: '超市', grocery: '杂货铺',
    market: '菜市场', nightmarket: '夜市', station: '车站', airport: '机场',
    hotel: '旅店', travel: '异乡', temple: '神社', onsen: '温泉',
    harbor: '港口', mountain: '山野', izakaya: '小酒馆', generic: '城市',
    botanical: '植物园', riverside: '河岸步道', lakeside: '湖畔',
    campsite: '露营地', amusement: '游乐园', flower_shop: '花店',
    bakery: '面包店', library: '图书馆'
  };

  function sceneInteriorName(key) {
    if (key === 'generic') return '';
    var name = SCENE_INTERIORS[key] || '';
    if (!name) return '';
    if (!window.GarageDestinations || !GarageDestinations.hasInterior(name)) {
      return '';
    }
    return name;
  }

  var ROOMS = [
    { name: '卧室', x: 30, y: 30, w: 300, h: 220, fill: '#241f2d', area: '3.0 × 2.2 m' },
    { name: '浴室', x: 350, y: 30, w: 180, h: 220, fill: '#1b2b33', area: '1.8 × 2.2 m' },
    { name: '书房', x: 550, y: 30, w: 260, h: 220, fill: '#1f2a34', area: '2.6 × 2.2 m' },
    { name: '客厅', x: 30, y: 270, w: 330, h: 240, fill: '#2a271f', area: '3.3 × 2.4 m' },
    { name: '厨房', x: 380, y: 270, w: 240, h: 240, fill: '#272a1f', area: '2.4 × 2.4 m' },
    { name: '阳台', x: 640, y: 270, w: 170, h: 240, fill: '#1d2d25', area: '1.7 × 2.4 m' },
    { name: '玄关', x: 30, y: 530, w: 780, h: 60, fill: '#222a33', area: '7.8 × 0.6 m' }
  ];

  var MARKER = {
    '卧室': { x: 20.5, y: 23.5 },
    '浴室': { x: 52.2, y: 20.0 },
    '书房': { x: 80.5, y: 24.0 },
    '客厅': { x: 26.0, y: 63.0 },
    '厨房': { x: 60.0, y: 67.0 },
    '阳台': { x: 86.5, y: 64.0 },
    '玄关': { x: 50.0, y: 90.5 }
  };

  var STATE_LABEL = {
    sleep: '睡眠', busy: '忙碌', focus: '专注', transit: '路上', available: '空闲', social: '社交'
  };
  var AVAIL_LABEL = {
    blocked: '勿扰', low: '不太方便', normal: '一般', high: '有空'
  };
  var ROOM_CLASS = {
    '卧室': 'bedroom', '浴室': 'bathroom', '书房': 'study',
    '客厅': 'living', '厨房': 'kitchen', '阳台': 'balcony', '玄关': 'hall'
  };

  var ITEM_ICONS = {
    bed: '<path d="M3 6v12M3 12h13a3 3 0 0 1 3 3v3M2 18h20"/><rect x="5" y="9" width="4" height="3" rx="1"/>',
    stairs: '<path d="M3 21h4v-4h4v-4h4v-4h4V5h4"/><path d="M6 3l1 2 2 1-2 1-1 2-1-2-2-1 2-1z"/>',
    wardrobe: '<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M12 3v18M9.5 11v2.5M14.5 11v2.5M8 21v1M16 21v1"/>',
    bedside_lamp: '<path d="M8 3h8l2 6H6z"/><path d="M12 9v9M8 21h8"/>',
    aroma_diffuser: '<path d="M9 10h6v8a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z"/><path d="M10 7h4M12 7V3M9 7c-1.5.4-2.3 1.2-2.6 2.4M15 7c1.5.4 2.3 1.2 2.6 2.4M17.5 13c1.5 0 2.5.9 2.5 2M18.5 17c1 0 1.5.5 1.5 1.3"/>',
    vanity_mirror: '<ellipse cx="12" cy="8" rx="5" ry="6"/><path d="M12 14v3M8.5 20h7M9.5 17h5"/>',
    plush: '<circle cx="8" cy="7" r="2.4"/><circle cx="16" cy="7" r="2.4"/><circle cx="12" cy="13" r="6"/><path d="M10 12h.01M14 12h.01M10.5 15c.8.9 2.2.9 3 0"/>',
    bedtime_book: '<path d="M12 6c-2-1.5-4.5-2-8-2v14c3.5 0 6 .5 8 2 2-1.5 4.5-2 8-2V4c-3.5 0-6 .5-8 2z"/><path d="M12 6v14"/>',
    bathtub: '<path d="M3 11h18v3a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5z"/><path d="M6 11V6a2 2 0 0 1 4 0"/><path d="M16 6h4M7 19l-1 2M17 19l1 2"/>',
    shower: '<path d="M4 8a8 8 0 0 1 16 0"/><path d="M12 8v3"/><path d="M8.5 13v1M12 13v1M15.5 13v1M10 17v1M14 17v1"/>',
    bath_salts: '<path d="M9 9h6v8a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z"/><path d="M8 6h8M10 6V3h4v3"/><path d="M12 12v4M10 14h4"/>',
    waterproof_speaker: '<rect x="7" y="4" width="10" height="17" rx="2"/><circle cx="12" cy="9" r="2"/><path d="M9 15h6M9 18h6M19 8c.8 1.4.8 3.6 0 5"/>',
    face_mask: '<circle cx="12" cy="11" r="6.5"/><path d="M8 12h8v1.5a4 4 0 0 1-8 0z"/><path d="M9 8.5h.01M15 8.5h.01M5.5 11H3.5M20.5 11h-2"/>',
    bath_towel: '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M4 9h16M7 13h10M7 16h6M7 19v2M17 19v2"/>',
    desk: '<path d="M2 9h20v3H2z"/><path d="M5 12v9M19 12v9M5 16h14"/>',
    monitor: '<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M12 16v3M8 21h8"/>',
    keyboard: '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h1M9 10h1M12 10h1M15 10h1M18 10h1M7 14h10"/>',
    bookshelf: '<path d="M5 3h14v18H5z"/><path d="M5 9h14M5 15h14"/><path d="M8 3v6M11 3v6M9 9v6M13 9v6M16 9v6M8 15v6M12 15v6M16 15v6"/>',
    notebook: '<rect x="6" y="4" width="13" height="17" rx="2"/><path d="M9 4v17M12 8h4M12 11h4M12 14h2M4 8h2M4 12h2M4 16h2"/>',
    camera: '<path d="M3 8h4l2-2h6l2 2h4v11H3z"/><circle cx="12" cy="13" r="3.5"/><path d="M17 10h.01"/>',
    headphones: '<path d="M4 13a8 8 0 0 1 16 0"/><rect x="3" y="13" width="4" height="7" rx="2"/><rect x="17" y="13" width="4" height="7" rx="2"/>',
    sofa: '<path d="M5 10V8a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v2"/><path d="M3 11a2 2 0 0 1 4 0v4h10v-4a2 2 0 0 1 4 0v7H3z"/><path d="M6 18v2M18 18v2"/>',
    tv: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    game_console: '<path d="M6 8h12a4 4 0 0 1 4 4l-1 5a2 2 0 0 1-3.5 1L15 16H9l-2.5 2a2 2 0 0 1-3.5-1L2 12a4 4 0 0 1 4-4z"/><path d="M8 11v3M6.5 12.5h3"/><circle cx="16" cy="11.5" r=".9" fill="currentColor" stroke="none"/><circle cx="18" cy="13.5" r=".9" fill="currentColor" stroke="none"/>',
    record_player: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="10" cy="12" r="4"/><circle cx="10" cy="12" r=".9" fill="currentColor" stroke="none"/><path d="M16 8l3 7M18.5 7.5l1.5 1"/>',
    coffee_table: '<path d="M3 11h18v3H3z"/><path d="M6 14v7M18 14v7"/><path d="M9 8h4v3H9zM13 9h1a1 1 0 0 1 0 2h-1"/>',
    board_game: '<rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="9" cy="9" r=".9" fill="currentColor" stroke="none"/><circle cx="15" cy="9" r=".9" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r=".9" fill="currentColor" stroke="none"/><circle cx="9" cy="15" r=".9" fill="currentColor" stroke="none"/><circle cx="15" cy="15" r=".9" fill="currentColor" stroke="none"/>',
    floor_lamp: '<path d="M9 3h6l2 6H7z"/><path d="M12 9v10M8 21h8"/>',
    yoga_mat: '<rect x="3" y="9" width="18" height="6" rx="3"/><circle cx="6.5" cy="12" r="1.6"/><path d="M10 9v6M15 9v6"/>',
    projector: '<rect x="3" y="8" width="12" height="9" rx="2"/><circle cx="9" cy="12.5" r="2"/><path d="M15 10l6-3M15 15l6 3"/>',
    coffee_machine: '<rect x="4" y="3" width="16" height="6" rx="1.5"/><path d="M8 9v3h8V9M12 12v3"/><path d="M9 15h6v2a3 3 0 0 1-6 0z"/><path d="M12 5v2"/>',
    pour_over: '<path d="M6 9h9v6a4 4 0 0 1-4 4H9a3 3 0 0 1-3-3z"/><path d="M6 11c-2.5.6-4 2-4 4.5"/><path d="M15 10h2a3 3 0 0 1 0 6h-2"/><path d="M9 6h4"/>',
    oven: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 8h16"/><circle cx="8" cy="5.5" r=".8" fill="currentColor" stroke="none"/><circle cx="12" cy="5.5" r=".8" fill="currentColor" stroke="none"/><rect x="7" y="11" width="10" height="7" rx="1"/><path d="M7 14h10"/>',
    toaster: '<rect x="3" y="9" width="18" height="9" rx="2"/><path d="M7 9V6h4v3M13 9V6h4v3M7 14h.01M10 14h.01"/>',
    fridge: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M5 10h14M9 6v2M9 13v3"/>',
    dining_table: '<path d="M3 11h18M6 11v9M18 11v9"/><ellipse cx="9" cy="9.5" rx="2.2" ry="1.1"/><ellipse cx="15" cy="9.5" rx="2.2" ry="1.1"/>',
    recipe_book: '<path d="M5 3h11a2 2 0 0 1 2 2v16H7a2 2 0 0 1-2-2z"/><path d="M5 17h13M8 7h6M8 10h6M15 3v5l-2-1-2 1V3"/>',
    tea_set: '<path d="M4 10h11v4a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M15 11h2a2.5 2.5 0 0 1 0 5h-2"/><path d="M7 10V8h5v2M7 4V2M10 5V3M4 21h15"/>',
    balcony_chair: '<path d="M8 4v8h8"/><path d="M16 4v8"/><path d="M5 12h11"/><path d="M5 12c0 4 2.5 7 5.5 7M16 12c0 3-2 6-5 7"/><path d="M3 21c5 1.5 13 1.5 18 0"/>',
    terrace_swing: '<path d="M8 4v8h8"/><path d="M16 4v8"/><path d="M5 12h11"/><path d="M5 12c0 4 2.5 7 5.5 7M16 12c0 3-2 6-5 7"/><path d="M3 21c5 1.5 13 1.5 18 0"/>',
    plants: '<path d="M8 14h8l-1 6H9z"/><path d="M12 14V8"/><path d="M12 10c-4 0-6-2-6-5 4 0 6 2 6 5z"/><path d="M12 8c4 0 6-2 6-5-4 0-6 2-6 5z"/>',
    watering_can: '<path d="M4 9h9v6a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3z"/><path d="M13 11h3l4-4v10l-4-4h-3"/><path d="M7 9V6h4v3"/><path d="M18 15v1M20 17v1"/>',
    wind_chime: '<path d="M12 2v4M6 6h12M8 6v4M12 6v6M16 6v4"/><rect x="6.5" y="10" width="3" height="5" rx="1"/><rect x="10.5" y="12" width="3" height="5" rx="1"/><rect x="14.5" y="10" width="3" height="5" rx="1"/>',
    telescope: '<path d="M4 13l13-6 2 4-13 6z"/><path d="M6 14l-2 6M12 16l3 5M11 17l-4 3"/><circle cx="18.5" cy="9.5" r=".9" fill="currentColor" stroke="none"/>',
    blanket: '<path d="M4 6h16v10a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3z"/><path d="M4 10c4 2 12 2 16 0"/><path d="M7 19v2M11 19v2M15 19v2M19 19v2"/>',
    washing_machine: '<rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="13" r="5"/><circle cx="12" cy="13" r="2"/><path d="M7 6h3M15 6h2"/>',
    iron: '<path d="M3 17h15a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4z"/><path d="M9 13V8a2 2 0 0 1 2-2h4l2 4"/><path d="M6 20h7"/>',
    shoe_cabinet: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 12h18M12 4v16M7 15h2M15 15h2"/>',
    umbrella: '<path d="M3 12a9 9 0 0 1 18 0z"/><path d="M12 12v6a2 2 0 0 0 4 0M12 3v2"/>',
    key_tray: '<path d="M3 15h18v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><circle cx="9" cy="9" r="3"/><path d="M11 11l4 4M14 14l1.5-1.5M16 16l1.5-1.5"/>',
    vacuum: '<path d="M10 3h4v9h-4z"/><path d="M12 12v3"/><path d="M5 17h14v3H5z"/><path d="M14 3h4v6"/>',
    sewing_kit: '<circle cx="9" cy="15" r="4"/><circle cx="9" cy="15" r="1"/><path d="M9 11V4M12 4l8 8"/><path d="M20 12l1 1"/>',
    delivery_box: '<path d="M3 8l9-4 9 4-9 4z"/><path d="M3 8v9l9 4 9-4V8"/><path d="M12 12v9M7 6l9 4"/>',
    _fallback: '<path d="M4 11l8-6 8 6v9H4z"/><path d="M9 20v-5h6v5"/>'
  };

  function itemIconSvg(item) {
    if (window.ItemArtwork) return ItemArtwork.draw(item);
    var id = item && item.id ? String(item.id) : '';
    var aliases = {clothes_rail:'wardrobe',kitchen_sink:'washing_machine',vanity_counter:'washing_machine',kitchen_north:'oven',piano_bench:'keyboard',weights_rack:'yoga_mat',art_workbench:'notebook',popcorn_console:'coffee_machine',hall_shelf:'shoe_cabinet',nightstand:'wardrobe',record_console:'tv',aquarium_console:'tv',media_console:'tv',bath_ledge:'bathtub',kitchen_right:'oven',kitchen_chair:'dining_table',dining_chair_l1:'dining_table',dining_chair_l2:'dining_table',dining_chair_r1:'dining_table',dining_chair_r2:'dining_table',desk_chair:'desk',art_chair:'desk',piano:'keyboard',aquarium:'tv',rice_cooker:'pour_over',dishwasher:'oven',dining_room_table:'dining_table',sideboard:'shoe_cabinet',treadmill:'yoga_mat',dumbbells:'yoga_mat',fitness_mirror:'vanity_mirror',art_easel:'notebook',paint_cart:'sewing_kit',digital_tablet:'monitor',cinema_screen:'projector',cinema_sofa:'sofa',popcorn_machine:'coffee_machine',dressing_mirror:'vanity_mirror',accessory_cabinet:'wardrobe',terrace_swing:'balcony_chair',flower_bed:'plants',bbq_grill:'oven',stairs:'stairs',stair_flight:'stairs',storage_bench:'shoe_cabinet'};
    var body = ITEM_ICONS[id] || ITEM_ICONS[aliases[id]] || ITEM_ICONS._fallback;
    return '<svg class="item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      body + '</svg>';
  }

  var SCENE_ICONS = {
    cafe: '<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 10h2a2.5 2.5 0 0 1 0 5h-2"/><path d="M6 3v2M9 2v3M12 3v2M3 21h14"/>',
    park: '<path d="M12 3l5 7h-3l4 6H6l4-6H7z"/><path d="M12 16v5M9 21h6"/>',
    bookstore: '<path d="M4 4h6v16H4zM10 4h6v16h-6zM16 5l4-1v16l-4 1z"/>',
    museum: '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M7 9h4v4H7zM14 9h3M14 12h3M14 15h3M7 16h10"/>',
    cinema: '<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18M7 6l2-3M12 6l2-3M17 6l2-3"/>',
    beach: '<circle cx="17" cy="6" r="3"/><path d="M2 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0M2 19c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/>',
    mall: '<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    office: '<path d="M4 21V5h10v16M14 10h6v11M7 8h4M7 12h4M7 16h4M17 13h1M17 17h1M2 21h20"/>',
    street: '<path d="M12 2v3M8 5h8l-1 3H9zM8 8h8l-1 8H9zM12 16v3M9 21h6"/>',
    food: '<path d="M4 11h16a8 8 0 0 1-16 0z"/><path d="M8 11c0-3 1.5-5 4-5s4 2 4 5M3 21h18"/>',
    supermarket: '<path d="M3 5h2l2 10h11l2-7H6"/><circle cx="9" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
    grocery: '<path d="M5 9h14v11H5zM8 9V6h8v3M9 13h6M9 17h6"/>',
    market: '<path d="M4 10h16l-2 10H6z"/><path d="M8 10l2-6M16 10l-2-6M9 14h6M9 17h6"/>',
    nightmarket: '<path d="M12 2v3M7.5 5h9l1.6 5a6 6 0 0 1-12 0z"/><path d="M8.5 16h7M12 19v3M9 9h6"/>',
    station: '<rect x="5" y="3" width="14" height="12" rx="3"/><path d="M5 9h14M9 12h6M8 15l-2 5M16 15l2 5M6 20h12"/>',
    airport: '<path d="M3 11.5L21 4l-7.2 17-3.1-6.6z"/><path d="M10.7 14.4L21 4"/>',
    hotel: '<path d="M3 20V8l9-5 9 5v12"/><path d="M3 20h18M9.5 20v-5h5v5"/><path d="M7 11h.01M12 11h.01M17 11h.01"/>',
    travel: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3.4 4 3.4 14 0 18M12 3c-3.4 4-3.4 14 0 18"/>',
    temple: '<path d="M3 5h18M4.5 5v3M19.5 5v3M6 8h12M9 8v12M15 8v12M6 13h12M4 20h16"/>',
    onsen: '<path d="M4 15h16v3a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3z"/><path d="M8 11c0-1.4 1-2 1-3.4M12 10c0-1.4 1-2 1-3.4M16 11c0-1.4 1-2 1-3.4"/>',
    harbor: '<path d="M4 15h16l-2-6H6z"/><path d="M12 9V3M9 3h6"/><path d="M2 20c2 1.2 4 1.2 6 0s4-1.2 6 0 4 1.2 6 0"/>',
    mountain: '<path d="M2 19l6-10 4 6 3-4 5 8z"/><path d="M8 9l1.6 2.4L12 9M2 22h20"/>',
    izakaya: '<path d="M10 3h4v4l2 3v10H8V10l2-3z"/><path d="M8 13h8M6 22h12"/>',
    transit: '<path d="M4 17h16M4 17l2-8h12l2 8M7 17v2M17 17v2M6 13h4M14 13h4"/>',
    generic: '<path d="M3 21V9l5-4 5 4v12M13 21V12h8v9M2 21h20M6 12h2M6 16h2M16 15h2M16 18h2"/>'
  };

  function sceneIconSvg(key) {
    var aliases = {botanical:'park',riverside:'harbor',lakeside:'beach',campsite:'mountain',amusement:'mall',flower_shop:'park',bakery:'food',library:'bookstore'};
    var body = SCENE_ICONS[key] || SCENE_ICONS[aliases[key]] || SCENE_ICONS.generic;
    return '<svg class="scene-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      body + '</svg>';
  }

  function hasAny(text, words) {
    text = String(text || '');
    for (var i = 0; i < words.length; i++) {
      if (text.indexOf(words[i]) >= 0) return true;
    }
    return false;
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function activityKey(activity) {
    var text = String(activity || '');
    if (hasAny(text, ['洗澡', '泡澡', '沐浴'])) return 'bath';
    if (hasAny(text, ['整理', '收纳', '打扫', '手账', '收拾'])) return 'tidy';
    if (hasAny(text, ['睡眠', '午睡', '小睡', '睡觉', '休息'])) return 'sleep';
    if (hasAny(text, ['做饭', '早餐', '午餐', '晚餐', '咖啡', '茶', '喝'])) return 'food';
    if (hasAny(text, ['读书', '阅读', '看书'])) return 'read';
    if (hasAny(text, ['黑胶', '音乐', '听歌'])) return 'music';
    if (hasAny(text, ['看剧', '电视', '电影'])) return 'tv';
    return 'idle';
  }

  function category(item) {
    if (!item) return 'home';
    if (item.state === 'sleep') return 'sleep';
    return item.kind || 'home';
  }

  function categoryClass(item) {
    var c = category(item);
    return c === 'outside' ? 'outside' : c === 'transit' ? 'transit' : c === 'sleep' ? 'sleep' : 'home';
  }

  function roomFor(item) {
    if (!item) return null;
    return item.room || null;
  }

  function sceneFor(item) {
    if (!item) return 'generic';
    return item.scene || 'generic';
  }

  function sceneLabel(key) {
    for (var i = 0; i < SCENES.length; i++) {
      if (SCENES[i].key === key) return SCENES[i].label;
    }
    return '城市';
  }

  function pillClassForAvailability(value) {
    if (value === 'blocked') return 'red';
    if (value === 'low') return 'amber';
    if (value === 'high') return 'green';
    return 'blue';
  }

  function checkDeliveryArrivals(deliveries) {
    var current = {};
    (deliveries || []).forEach(function (order) {
      var id = String(order.id || '');
      if (!id) return;
      current[id] = String((order.goods || {}).name || '商品');
    });
    if (state.deliveryMap !== null) {
      var arrived = Object.keys(state.deliveryMap).filter(function (id) {
        return !current[id];
      });
      if (arrived.length) {
        var names = arrived.map(function (id) {
          return state.deliveryMap[id];
        }).filter(Boolean);
        showToast(
          names.length > 1
            ? '快递到了：' + names.slice(0, 2).join('、') +
              (names.length > 2 ? '等 ' + names.length + ' 件' : '')
            : '快递到了：' + (names[0] || '商品')
        );
      }
    }
    state.deliveryMap = current;
  }

  function showLevelUp(level, score) {
    var node = document.createElement('div');
    node.className = 'affection-levelup';
    node.innerHTML = '<div class="affection-levelup-icon">✨</div>' +
      '<div class="affection-levelup-copy"><small>关系提升</small><b>' +
      escapeHtml(level || '更亲近') + '</b><span>好感 ' +
      Number(score || 0) + '</span></div>';
    document.body.appendChild(node);
    window.setTimeout(function () {
      if (node.parentNode) node.remove();
    }, 2600);
  }

  function checkAffectionLevel(affection) {
    if (!affection || affection.level == null) return;
    var level = String(affection.level);
    var score = Number(affection.score) || 0;
    if (state.lastAffectionLevel !== null &&
        level !== state.lastAffectionLevel &&
        score >= state.lastAffectionScore) {
      showToast('关系提升：' + level);
      showLevelUp(level, score);
    }
    state.lastAffectionLevel = level;
    state.lastAffectionScore = score;
  }

  function fetchState() {
    var params = new URLSearchParams();
    if (state.persona) params.set('persona', state.persona);
    var pageParams = new URLSearchParams(window.location.search);
    if (pageParams.get('time')) params.set('time', pageParams.get('time'));
    var url = '/api/state' + (params.toString() ? '?' + params.toString() : '');
    fetch(url, { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        state.data = data;
        state.error = !data.ok;
        state.lastData = data;
        state.lastFetchErrorAt = 0;
        if (data.ok && data.persona) state.persona = data.persona;
        try {
          checkDeliveryArrivals(data.deliveries || []);
        } catch (error) {
          console.error('[VirtualLife] delivery check failed', error);
        }
        try {
          checkAffectionLevel(data.affection || {});
        } catch (error) {
          console.error('[VirtualLife] affection level check failed', error);
        }
        try {
          renderPendingActions(data.pending_actions);
        } catch (error) {
          console.error('[VirtualLife] pending actions render failed', error);
        }
        render();
      })
      .catch(function () {
        state.error = true;
        var now = Date.now();
        if (!state.lastFetchErrorAt || now - state.lastFetchErrorAt > 15000) {
          showToast('无法连接本地数据服务，稍后自动重试');
          state.lastFetchErrorAt = now;
        }
        renderHeader();
      });
  }

  function showToast(text) {
    var toast = $('toast');
    if (!toast) return;
    toast.textContent = text;
    toast.classList.remove('hidden');
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(function () { toast.classList.add('hidden'); }, 3200);
  }

  function renderPendingActions(actions) {
    var box = $('pending-actions');
    if (!box) {
      box = document.createElement('div');
      box.id = 'pending-actions';
      box.className = 'pending-actions pending-floating';
      document.body.appendChild(box);
    }
    var items = Array.isArray(actions) ? actions : [];
    var baseTitle = document.title.replace(/^【\d+ 个待处理】/, '');
    document.title = items.length
      ? ('【' + items.length + ' 个待处理】' + baseTitle)
      : baseTitle;
    box.setAttribute('aria-live', 'polite');
    box.classList.toggle('pending-floating', items.length > 0);
    if (!items.length) {
      box.classList.add('hidden');
      box.innerHTML = '';
      return;
    }
    box.classList.remove('hidden');
    box.innerHTML = '<span class="pending-actions-label">待处理</span>' +
      items.map(function (action) {
      var id = escapeHtml(action.id || '');
      var source = String(action.source || '').trim();
      var labelText = action.label || '把东西递给月月';
      var kind = String(action.kind || 'gift');
      var hint = source
        ? ('来自：' + source)
        : (kind === 'money'
          ? '填写金额后给月月钱'
          : kind === 'wish'
            ? '点击实现月月的愿望'
            : '点击把东西递过去');
      var ariaLabel = labelText + '，' + hint;
      var control = '';
      if (kind === 'money') {
        var suggested = Number(action.amount) || 0;
        control =
          '<span class="pending-action-label">' + escapeHtml(labelText) + '</span>' +
          '<input type="number" class="pending-money-input" min="1" step="1" ' +
          'max="100000" value="' + (suggested > 0 ? suggested : '') + '" ' +
          'placeholder="填写金额" aria-label="给月月的金额">' +
          '<button type="button" class="pending-action-btn" data-pending-kind="money" ' +
          'data-pending-id="' + id + '" title="' + escapeHtml(hint) + '" ' +
          'aria-label="' + escapeHtml(ariaLabel) + '">给</button>';
      } else {
        control = '<button type="button" class="pending-action-btn" data-pending-kind="' +
          escapeHtml(kind) + '" data-pending-id="' + id + '" title="' +
          escapeHtml(hint) + '" aria-label="' + escapeHtml(ariaLabel) + '">' +
          escapeHtml(labelText) + '</button>';
      }
      return '<span class="pending-action-item">' +
        '<span class="pending-action-main">' +
        control +
        '<button type="button" class="pending-action-cancel" data-dismiss-id="' +
        id + '" title="取消这个待处理" aria-label="取消这个待处理">×</button>' +
        '</span>' +
        (source
          ? '<span class="pending-action-source" title="' +
            escapeHtml(hint) + '">' + escapeHtml(hint) + '</span>'
          : '') +
        '</span>';
    }).join('');
    box.querySelectorAll('[data-pending-id]').forEach(function (button) {
      button.addEventListener('click', function () {
        var kind = button.getAttribute('data-pending-kind') || 'gift';
        var item = button.closest('.pending-action-item');
        var input = item ? item.querySelector('.pending-money-input') : null;
        var amount = input ? Number(input.value) : 0;
        if (kind === 'money' && (!amount || amount <= 0)) {
          showToast('先填写要给月月的金额');
          if (input) input.focus();
          return;
        }
        acceptPendingAction(
          button.getAttribute('data-pending-id'),
          button,
          kind,
          amount
        );
      });
    });
    box.querySelectorAll('[data-dismiss-id]').forEach(function (button) {
      button.addEventListener('click', function () {
        dismissPendingAction(button.getAttribute('data-dismiss-id'), button);
      });
    });
  }

  function dismissPendingAction(id, button) {
    if (!id) return;
    if (button) {
      button.disabled = true;
      button.textContent = '…';
    }
    fetch('/api/gift/dismiss', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '取消失败');
        showToast('已取消这个待处理');
        fetchState();
      })
      .catch(function (error) {
        if (button) {
          button.disabled = false;
          button.textContent = '×';
        }
        showToast(error && error.message ? error.message : '取消失败');
        fetchState();
      });
  }

  function acceptPendingAction(id, button, kind, amount) {
    if (!id) return;
    kind = kind || 'gift';
    var originalText = button ? button.textContent : '';
    if (button) {
      button.disabled = true;
      button.textContent = kind === 'money'
        ? '正在给钱...'
        : kind === 'wish'
          ? '正在实现...'
          : '正在递过去...';
    }
    var payload = { id: id };
    if (kind === 'money') {
      payload.amount = Number(amount) || 0;
    }
    fetch('/api/gift/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '操作失败');
        if (data.kind === 'money') {
          showToast('已给月月 ' + data.amount + ' 元');
          fetchState();
          return;
        }
        if (data.kind === 'wish') {
          showToast('已实现月月的愿望');
          fetchState();
          return;
        }
        state.interaction.busy = true;
        state.interaction.fromGift = true;
        setInteractionReply('她正在接你递过去的东西...');
        showToast('已经把东西递过去了');
        fetchState();
        pollInteraction(data.id, Date.now());
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '操作失败');
        if (button) {
          button.disabled = false;
          button.textContent = originalText || '把东西递给月月';
        }
        fetchState();
      });
  }

  function todayString() {
    var now = new Date();
    return [
      now.getFullYear(),
      String(now.getMonth() + 1).padStart(2, '0'),
      String(now.getDate()).padStart(2, '0')
    ].join('-');
  }

  function fetchHomeItems() {
    var persona = String((state.data && state.data.persona) || '');
    fetch('/api/home_items?persona=' + encodeURIComponent(persona), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        state.homeItems = Array.isArray(data.items) ? data.items : [];
        renderState.home = ""; renderState.scene = "";
        render();
        renderItemDrawer();
        updateItemCounts();
        if (state.pendingItem) {
          openItem(state.pendingItem);
          state.pendingItem = null;
        }
      })
      .catch(function () {
        state.homeItems = [];
        updateItemCounts();
      });
  }

  function renderWishes() {
    var body = $('wish-body');
    if (!body) return;
    var today = todayString();
    var wishes = state.wishes || [];
    var todays = wishes.filter(function (wish) {
      return String(wish.date || '') === today;
    });
    var older = wishes.filter(function (wish) {
      return String(wish.date || '') !== today;
    }).slice(-8).reverse();
    if (!todays.length && !older.length) {
      body.innerHTML = '<p class="inventory-empty">今天还没有新的灵感。</p>';
      return;
    }
    var wishItem = function (wish, showDate) {
      return '<div class="wish-item">' +
        '<span class="wish-icon">💡</span>' +
        '<span class="wish-copy"><b>' + escapeHtml(wish.room || '家') +
        ' · ' + escapeHtml(wish.name || '家具') + '</b><small>' +
        (showDate ? escapeHtml(String(wish.date || '')) + ' · ' : '') +
        escapeHtml(wish.action || '做点什么') + '</small></span>' +
        '<span class="wish-actions">' +
        '<button type="button" class="wish-open" data-wish-open="' +
        escapeHtml(wish.id || '') + '">看看</button>' +
        '<button type="button" class="wish-do" data-wish-do="' +
        escapeHtml(wish.id || '') + '" data-wish-action="' +
        escapeHtml(wish.action || '') + '">实现</button></span></div>';
    };
    var html = '';
    if (todays.length) {
      html += '<div class="wish-section-title">今天</div>' +
        todays.map(function (wish) {
          return wishItem(wish, false);
        }).join('');
    } else {
      html += '<p class="inventory-empty">今天还没有新的灵感。</p>';
    }
    if (older.length) {
      html += '<div class="wish-section-title">更早的灵感</div>' +
        older.map(function (wish) {
          return wishItem(wish, true);
        }).join('');
    }
    body.innerHTML = html;
    body.querySelectorAll('[data-wish-open]').forEach(function (button) {
      button.addEventListener('click', function () {
        openWishItem(button.getAttribute('data-wish-open'));
      });
    });
    body.querySelectorAll('[data-wish-do]').forEach(function (button) {
      button.addEventListener('click', function () {
        implementWish(
          button.getAttribute('data-wish-do'),
          button.getAttribute('data-wish-action'),
          button
        );
      });
    });
  }

  function implementWish(id, action, button) {
    var item = (state.homeItems || []).find(function (entry) {
      return String(entry.id) === String(id);
    });
    if (!item) {
      showToast('这件家具暂时不在家里');
      return;
    }
    if (button) button.disabled = true;
    var pending = sendItemWish(item, action, button);
    if (pending && pending.then) {
      pending.then(function () {
        renderWishes();
      });
    }
  }

  function openWishes() {
    renderWishes();
    $('wish-modal').classList.remove('hidden');
  }

  function closeWishes() {
    $('wish-modal').classList.add('hidden');
  }

  function openWishItem(id) {
    if (!id) return;
    var item = state.homeItems.find(function (entry) {
      return String(entry.id) === String(id);
    });
    if (!item) {
      showToast('这件家具暂时不在家里');
      return;
    }
    closeWishes();
    openItem(item.id);
  }

  function fetchWishes() {
    fetch('/api/item_wishes', { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        state.wishes = Array.isArray(data.wishes) ? data.wishes : [];
        updateItemCounts();
      })
      .catch(function () {});
  }

  function renderItemDrawer() {
    if (state.decorMode) {
      renderDecorDrawer();
      return;
    }
    var root = $('item-groups');
    if (!root) return;
    if (!state.homeItems.length) {
      root.innerHTML = '<div class="empty-next">还没有加载到物品清单</div>';
      return;
    }
    var query = String(state.itemQuery || '').trim().toLowerCase();
    var items = query
      ? state.homeItems.filter(function (item) {
          return [item.name, item.room, item.description]
            .join(' ').toLowerCase().indexOf(query) >= 0;
        })
      : state.homeItems;
    if (!items.length) {
      root.innerHTML = '<div class="empty-next">没有匹配的家具。</div>';
      return;
    }
    var groups = {};
    items.forEach(function (item) {
      var room = item.room || '家';
      if (!groups[room]) groups[room] = [];
      groups[room].push(item);
    });
    var html = [];
    Object.keys(groups).forEach(function (room) {
      html.push('<div class="item-group"><h4>' + escapeHtml(room) + '</h4><div class="item-buttons">');
      groups[room].forEach(function (item) {
        html.push(
          '<button type="button" class="item-chip" data-id="' + escapeHtml(item.id) + '">' +
          itemIconSvg(item) + '<span>' + escapeHtml(item.name) + '</span></button>'
        );
      });
      html.push('</div></div>');
    });
    root.innerHTML = html.join('');
  }

  function decorRooms() {
    var names = [];
    if (window.SceneStudio && SceneStudio.rooms) {
      [1, 2].forEach(function (floor) {
        (SceneStudio.rooms(floor) || []).forEach(function (room) {
          if (room && room.name && names.indexOf(room.name) < 0) {
            names.push(room.name);
          }
        });
      });
    }
    return names;
  }

  function fetchDecorItems(open) {
    var persona = (state.data && state.data.persona) || '';
    return fetch('/api/decor/items?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '装潢模式加载失败');
        state.decorItems = Array.isArray(data.items) ? data.items : [];
        if (open) toggleItemDrawer(true);
        else if (state.decorMode) renderDecorDrawer();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '装潢模式加载失败');
      });
  }

  function renderDecorDrawer() {
    var root = $('item-groups');
    if (!root) return;
    var countNode = $('item-count');
    if (countNode) countNode.textContent = '移动、收起或放回原始家具';
    var query = String(state.itemQuery || '').trim().toLowerCase();
    var items = (state.decorItems || []).filter(function (item) {
      return !query || [item.name, item.room]
        .join(' ').toLowerCase().indexOf(query) >= 0;
    });
    var groups = {};
    items.forEach(function (item) {
      var key = item.stored ? '已收起' : (item.room || '家');
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });
    var rooms = decorRooms();
    var html = [];
    Object.keys(groups).forEach(function (room) {
      html.push('<div class="item-group"><h4>' + escapeHtml(room) +
        '</h4><div class="decor-furniture-list">');
      groups[room].forEach(function (item) {
        var selectedRoom = String(
          item.override_room || item.room || ''
        );
        var options = rooms.map(function (name) {
          return '<option value="' + escapeHtml(name) + '"' +
            (name === selectedRoom ? ' selected' : '') + '>' +
            escapeHtml(name) + '</option>';
        }).join('');
        html.push(
          '<div class="decor-furniture-row" data-decor-id="' +
          escapeHtml(item.id) + '">' +
          '<span class="decor-furniture-icon">' + itemIconSvg(item) + '</span>' +
          '<span class="decor-furniture-name">' + escapeHtml(item.name || item.id) +
          '<small>' + escapeHtml(item.stored ? '已收起' : selectedRoom) +
          '</small></span>' +
          '<select class="mini-btn" data-decor-room>' + options + '</select>' +
          '<button type="button" class="mini-btn" data-decor-move>' +
          (item.stored ? '放回' : '移动') + '</button>' +
          (item.stored ? '' :
            '<button type="button" class="mini-btn" data-decor-store>' +
            '收起</button>') +
          (item.custom_place || item.stored ?
            '<button type="button" class="mini-btn" data-decor-reset>' +
            '重置</button>' : '') +
          '</div>'
        );
      });
      html.push('</div></div>');
    });
    root.innerHTML = html.length
      ? html.join('')
      : '<div class="empty-next">没有匹配的家具。</div>';
    root.querySelectorAll('[data-decor-move]').forEach(function (button) {
      button.addEventListener('click', function () {
        var row = button.closest('[data-decor-id]');
        var select = row ? row.querySelector('[data-decor-room]') : null;
        if (!row) return;
        startDecorMove(
          row.getAttribute('data-decor-id'),
          select ? select.value : ''
        );
      });
    });
    root.querySelectorAll('[data-decor-store]').forEach(function (button) {
      button.addEventListener('click', function () {
        var row = button.closest('[data-decor-id]');
        if (!row) return;
        storeDecorItem(row.getAttribute('data-decor-id'), button);
      });
    });
    root.querySelectorAll('[data-decor-reset]').forEach(function (button) {
      button.addEventListener('click', function () {
        var row = button.closest('[data-decor-id]');
        if (!row) return;
        resetDecorItem(row.getAttribute('data-decor-id'), button);
      });
    });
  }

  function openDecorDrawer() {
    state.decorMode = true;
    if (window.Room3D) Room3D.dragEnabled = true;
    var toggle = $('decor-toggle');
    if (toggle) toggle.classList.add('active');
    renderScene(true);
    var heading = document.querySelector('#item-drawer .drawer-head h3');
    if (heading) heading.textContent = '装潢模式';
    var search = $('item-search');
    if (search) search.placeholder = '搜索要移动的家具...';
    fetchDecorItems(true);
  }

  function exitDecorMode() {
    state.decorMode = false;
    if (window.Room3D) Room3D.dragEnabled = false;
    var toggle = $('decor-toggle');
    if (toggle) toggle.classList.remove('active');
    var heading = document.querySelector('#item-drawer .drawer-head h3');
    if (heading) heading.textContent = '可互动物品';
    var search = $('item-search');
    if (search) search.placeholder = '搜索家具...';
    toggleItemDrawer(false);
    renderScene(true);
  }

  function resetDecorItem(itemId, button) {
    if (!itemId) return;
    if (button) button.disabled = true;
    fetch('/api/decor/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        item_id: itemId
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '重置失败');
        showToast('已恢复这件家具的默认位置');
        fetchHomeItems();
        fetchState();
        fetchDecorItems(state.decorMode);
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '重置失败');
      });
  }

  function startDecorMove(itemId, room) {
    if (!itemId || !room) {
      showToast('先选一个房间');
      return;
    }
    closeItem();
    state.decorMode = true;
    state.previewScene = null;
    state.previewRoom = room;
    state.placement = { decor: true, item: itemId, room: room };
    toggleItemDrawer(false);
    renderScene(true);
    showToast('点击' + room + '的地面，或直接拖动家具调整位置');
  }

  function decorDragMarker(event) {
    var stage = $('scene-stage');
    if (!stage) return;
    var marker = document.getElementById('decor-drag-marker');
    if (!marker) {
      marker = document.createElement('div');
      marker.id = 'decor-drag-marker';
      marker.className = 'decor-drag-marker';
      marker.textContent = '放这里';
      stage.appendChild(marker);
    }
    var rect = stage.getBoundingClientRect();
    marker.style.left = (event.clientX - rect.left) + 'px';
    marker.style.top = (event.clientY - rect.top) + 'px';
    marker.style.display = 'block';
  }

  function hideDecorDragMarker() {
    var marker = document.getElementById('decor-drag-marker');
    if (marker) marker.style.display = 'none';
  }

  function onDecorPointerDown(event) {
    if (!state.decorMode || state.placement) return;
    var hit = event.target.closest('.furniture-hit');
    if (!hit) return;
    var item = (state.homeItems || []).find(function (entry) {
      return String(entry.id) === String(hit.getAttribute('data-id'));
    });
    if (!item) return;
    var placed = Boolean(item.placed);
    state.decorDrag = {
      kind: placed ? 'placed' : 'decor',
      id: placed ? String(item.possession_id || item.name || '') : item.id,
      name: item.name || '',
      room: item.room || '',
      startX: event.clientX,
      startY: event.clientY,
      moved: false
    };
    state.decorSuppressClick = false;
    // Do not let the room-pan handler start while dragging furniture.
    event.stopPropagation();
    try { $('scene-stage').setPointerCapture(event.pointerId); } catch (e) {}
  }

  function onDecorPointerMove(event) {
    var drag = state.decorDrag;
    if (!drag) return;
    var distance = Math.hypot(
      event.clientX - drag.startX, event.clientY - drag.startY
    );
    if (distance > 4) {
      drag.moved = true;
      event.preventDefault();
      event.stopPropagation();
      decorDragMarker(event);
    }
  }

  function onDecorPointerUp(event) {
    var drag = state.decorDrag;
    if (!drag) return;
    state.decorDrag = null;
    hideDecorDragMarker();
    event.stopPropagation();
    try {
      if ($('scene-stage').hasPointerCapture(event.pointerId)) {
        $('scene-stage').releasePointerCapture(event.pointerId);
      }
    } catch (e) {}
    if (!drag.moved) return;
    state.decorSuppressClick = true;
    setTimeout(function () { state.decorSuppressClick = false; }, 500);
    var point = placementRoomPoint(event, drag.room);
    if (!point) {
      showToast('没找到房间地面，再拖一次');
      return;
    }
    var placed = drag.kind === 'placed';
    var surface = placed ? surfaceAtPoint(drag.room, point, event) : null;
    var url = placed ? '/api/place_item' : '/api/decor/place';
    var payload = placed
      ? {
          item: drag.id || drag.name,
          room: drag.room,
          x: point.x,
          y: point.y,
          z_cm: surface ? surface.z_cm : 0,
          surface_id: surface ? surface.surface_id : ''
        }
      : {
          persona: (state.data && state.data.persona) || '',
          item_id: drag.id,
          room: drag.room,
          x: point.x,
          y: point.y
        };
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '移不动');
        showToast('已调整位置');
        fetchHomeItems();
        fetchState();
        if (state.decorMode) fetchDecorItems(false);
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '移不动');
      });
  }

  function storeDecorItem(itemId, button) {
    if (!itemId) return;
    if (button) button.disabled = true;
    fetch('/api/decor/store', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        item_id: itemId
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '收不起来');
        showToast('已收进储藏');
        fetchHomeItems();
        fetchDecorItems(false);
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '收不起来');
      });
  }

  function updateItemCounts() {
    var hotspotCount = state.homeItems.filter(function (item) { return item.hotspot; }).length;
    var toggle = $('items-toggle');
    if (toggle) toggle.textContent = '物品 ' + state.homeItems.length;
    var itemCount = $('item-count');
    if (itemCount) {
      itemCount.textContent = '共 ' + state.homeItems.length + ' 件 · ' +
        hotspotCount + ' 件家具可直接点击';
    }
    var today = todayString();
    var wishCount = state.wishes.filter(function (wish) {
      return String(wish.date || '') === today;
    }).length;
    var wishLabel = $('wish-count');
    if (wishLabel) wishLabel.textContent = '今日灵感 ' + wishCount;
  }

  function renderItemActions(item) {
    var actions = Array.isArray(item.actions) ? item.actions : [];
    $('item-actions').innerHTML = actions.map(function (action) {
      return '<button type="button" class="pop-action" data-action="' +
        escapeHtml(action) + '">' + escapeHtml(action) + '</button>';
    }).join('') || '<span class="item-desc">暂时没有记录动作</span>';
  }

  function renderItemState(item) {
    var node = $('item-state');
    if (!node) return;
    var label = String((item && item.state_label) || '').trim();
    if (!label) {
      node.textContent = '';
      node.classList.add('hidden');
      node.classList.remove('on', 'off');
      return;
    }
    node.textContent = label;
    node.classList.remove('hidden');
    node.classList.toggle('on', Boolean(item.power_on));
    node.classList.toggle('off', item.power_on === false);
  }

  function updateItemView(item) {
    if (!item) return;
    state.selectedItem = item;
    $('item-desc').textContent = item.description || '可以在这里做点小事。';
    renderItemState(item);
    renderItemActions(item);
    var interactButton = $('interact-action');
    if (interactButton) interactButton.textContent = interactLabelFor(item);
  }

  function openItem(itemId) {
    var item = null;
    for (var i = 0; i < state.homeItems.length; i++) {
      if (String(state.homeItems[i].id) === String(itemId)) {
        item = state.homeItems[i];
        break;
      }
    }
    if (!item) return;
    state.selectedItem = item;
    $('item-room').textContent = (item.floor || (window.SceneStudio ? SceneStudio.floorFor(item.room) : 1)) + 'F · ' + (item.room || '');
    $('item-name').textContent = item.name || '';
    $('item-icon').innerHTML = itemIconSvg(item);
    $('item-desc').textContent = item.description || '可以在这里做点小事。';
    var fridgeBox = $('fridge-box');
    var isFridge = String(item.id) === 'fridge' ||
      String(item.name || '').indexOf('冰箱') >= 0;
    if (isFridge) {
      fridgeBox.classList.remove('hidden');
      $('fridge-recipe').classList.add('hidden');
      loadFridge();
    } else {
      fridgeBox.classList.add('hidden');
      $('fridge-recipe').classList.add('hidden');
    }
    var cookBox = $('cook-box');
    if (cookBox) cookBox.classList.toggle('hidden', !isDiningTable(item));
    var gameBox = $('game-box');
    if (gameBox) gameBox.classList.toggle('hidden', !isGameItem(item));
    var gameOpen = $('game-open');
    if (gameOpen) gameOpen.textContent = isBoardGame(item) ? '开一局桌游' : '和月月打游戏';
    renderItemState(item);
    renderItemActions(item);
    var interactButton = $('interact-action');
    if (interactButton) interactButton.textContent = interactLabelFor(item);
    setInteractionReply('');
    $('item-popover').classList.remove('hidden');
    $('item-drawer').classList.add('hidden');
  }

  function genericPropActions(name) {
    var label = String(name || '');
    if (/楼梯/.test(label)) {
      return ['上楼', '下楼', '在扶手边歇会儿'];
    }
    if (/灯|吊灯|壁灯|串灯/.test(label)) {
      return ['开灯', '关灯', '调暗'];
    }
    if (/绿植|盆栽|花箱|花|树|草/.test(label)) {
      return ['浇水', '看看', '整理'];
    }
    if (/画|照片|挂画|画布/.test(label)) {
      return ['看看', '扶正', '擦灰'];
    }
    if (/椅|凳|沙发/.test(label)) {
      return ['坐下', '挪开', '看看'];
    }
    if (/毯|地垫|垫/.test(label)) {
      return ['踩一踩', '整理', '拍灰'];
    }
    if (/钟|表/.test(label)) {
      return ['看时间', '擦一擦', '调准'];
    }
    if (/水壶|水杯|杯|壶/.test(label)) {
      return ['拿起来', '放回去', '看看'];
    }
    return ['看看', '摸摸', '待一会儿'];
  }

  function openGenericProp(info) {
    if (!info || !info.id) return;
    var rawName = String(info.name || '').trim();
    var knownName = window.Room3DModels && Room3DModels.names
      ? Room3DModels.names[info.id] : '';
    var name = knownName ||
      (rawName && !/^[a-z0-9_-]+$/i.test(rawName) ? rawName : '这件家具');
    var room = String(
      info.room ||
      ((state.data && state.data.now && state.data.now.room) || '')
    );
    var floor = window.SceneStudio && room ? SceneStudio.floorFor(room) : 1;
    var actions = genericPropActions(name);
    var isStair = /楼梯/.test(name);
    var itemId = 'prop-' + String(room || 'home').replace(/\s+/g, '-') +
      '-' + String(info.id).replace(/[^a-zA-Z0-9_-]/g, '-');
    state.homeItems = (state.homeItems || []).filter(function (entry) {
      return !entry.generic_prop;
    });
    state.homeItems.push({
      id: itemId,
      name: name,
      room: room,
      floor: floor,
      description: isStair ? '连接两个楼层的固定木楼梯。' : ('在' + name + '边可以做点小事。'),
      actions: actions,
      interact_label: isStair ? '上下楼走走' : actions[0],
      generic_prop: true,
      hotspot: false
    });
    openItem(itemId);
  }

  function closeItem() {
    state.selectedItem = null;
    state.homeItems = (state.homeItems || []).filter(function (entry) {
      return !entry.generic_prop;
    });
    $('item-popover').classList.add('hidden');
  }

  // ------------------------------------------------------------ interactions

  var INTERACT_TIMEOUT_MS = 45000;

  function interactLabelFor(item) {
    var id = String((item && item.id) || '');
    var name = String((item && item.name) || '');
    if (id === 'bed') return state.userSleeping ? '我醒了，起床' : '我上床睡了';
    if (id !== 'game_console' && item && item.power_on !== null && item.power_on !== undefined) {
      return item.power_on ? '问问她' + name + '的事' : '和她说说' + name;
    }
    var saved = String((item && item.interact_label) || '').trim();
    if (saved) return saved;
    if (id === 'dining_table' || name.indexOf('餐桌') >= 0) return '一起吃饭';
    if (id === 'fridge' || name.indexOf('冰箱') >= 0) return '翻冰箱';
    if (id === 'tea_set' || name.indexOf('茶具') >= 0) return '邀请喝茶';
    if (id === 'game_console' || name.indexOf('游戏机') >= 0) return '邀请打游戏';
    if (id === 'sofa' || name.indexOf('沙发') >= 0) return '在沙发上聊两句';
    var actions = Array.isArray(item && item.actions) ? item.actions : [];
    if (actions.length) return String(actions[0]);
    return '在这里待一会儿';
  }

  function setInteractionReply(text) {
    var nodes = [$('interact-reply'), $('talk-reply')];
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      if (!node) continue;
      node.textContent = text || '';
      node.classList.toggle('hidden', !text);
    }
  }

  function showSpeech(text, thinking) {
    var bubble = $('speech-bubble');
    var textNode = $('speech-text');
    if (!bubble || !textNode || !text) return;
    var stage = $('scene-stage');
    var home = $('home-stage');
    var target = stage && stage.offsetParent !== null ? stage : home;
    if (!target) return;
    var rect = target.getBoundingClientRect();
    bubble.classList.remove('hidden');
    bubble.classList.toggle('thinking', Boolean(thinking));
    textNode.textContent = text;
    var width = Math.min(300, Math.max(170, textNode.offsetWidth + 30));
    var left = rect.left + rect.width * 0.52 - width * 0.5;
    var top = rect.top + Math.max(6, rect.height * 0.05);
    bubble.style.width = width + 'px';
    bubble.style.left = Math.max(10, Math.min(window.innerWidth - width - 10, left)) + 'px';
    bubble.style.top = Math.max(10, top) + 'px';
    if (showSpeech._timer) clearTimeout(showSpeech._timer);
    showSpeech._timer = setTimeout(function () {
      bubble.classList.add('hidden');
      bubble.classList.remove('thinking');
    }, thinking ? 60000 : 10000);
  }

  function startInteraction(payload, label) {
    if (state.interaction.busy) {
      showToast('上一个互动还在等她回应');
      return;
    }
    state.interaction.busy = true;
    state.interaction.fromGift = false;
    state.interaction.affectionAction = payload && payload.affection_action
      ? String(payload.affection_action) : '';
    setInteractionReply('');
    showSpeech('（' + (label || '她想了想') + '…）', true);
    fetch('/api/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '请求失败');
        pollInteraction(data.id, Date.now());
      })
      .catch(function (error) {
        state.interaction.busy = false;
        showSpeech('（没连上插件：' + error.message + '）');
      });
  }

  function pollInteraction(id, startedAt) {
    fetch('/api/interact?id=' + encodeURIComponent(id), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (data.ok && data.response) {
          finishInteraction(data.response);
          return;
        }
        if (Date.now() - startedAt > INTERACT_TIMEOUT_MS) {
          state.interaction.busy = false;
          state.interaction.fromGift = false;
          showSpeech('（她没听见…… 插件可能没在运行）');
          return;
        }
        setTimeout(function () { pollInteraction(id, startedAt); }, 1200);
      })
      .catch(function () {
        setTimeout(function () { pollInteraction(id, startedAt); }, 2000);
      });
  }

  function finishInteraction(response) {
    state.interaction.busy = false;
    var fromGift = Boolean(state.interaction.fromGift);
    var affectionAction = state.interaction.affectionAction || '';
    state.interaction.fromGift = false;
    state.interaction.affectionAction = '';
    var speech = String((response && response.speech) || '').trim();
    showSpeech(speech || '（她笑了笑）');
    if (affectionAction) {
      if (response && response.rejected) {
        showToast('还需要再亲近一点');
      } else {
        showAffectionFeedback(
          affectionAction, speech, Number(response && response.affection_points) || 0
        );
      }
    }
    if (fromGift) {
      showToast(speech ? ('月月：' + speech.slice(0, 80)) : '月月接过了你递过去的东西');
    }
    // 对话框里只保留「菜品 + 回复」，食材、做法、库存变化都不再展示。
    var parts = [];
    var dish = (response && response.dish) || null;
    if (dish && dish.name) parts.push('🍽️ ' + dish.name);
    if (speech) parts.push(speech);
    setInteractionReply(parts.join('\n'));
    if ($('fridge-box') && !$('fridge-box').classList.contains('hidden')) {
      loadFridge();
    }
  }

  function showAffectionFeedback(action, speech, points) {
    var labels = {
      headpat: ['摸摸头', '🤚'],
      handhold: ['牵了牵手', '🤝'],
      hug: ['抱了一下', '🤗'],
      kiss: ['亲了一下', '💋']
    };
    var item = labels[action] || ['靠近了一点', '💗'];
    var node = document.createElement('div');
    node.className = 'affection-burst';
    var hearts = '';
    for (var i = 0; i < 5; i++) {
      hearts += '<span class="affection-heart" style="--i:' + i + '">♥</span>';
    }
    var gain = Number(points) > 0 ? ' · 好感+' + Number(points) : '';
    node.innerHTML = '<div class="affection-burst-hearts">' + hearts + '</div>' +
      '<div class="affection-burst-label">' + item[1] + ' ' +
      escapeHtml(item[0]) + escapeHtml(gain) + '</div>';
    document.body.appendChild(node);
    window.setTimeout(function () {
      if (node.parentNode) node.remove();
    }, 1600);
  }

  function sendChat() {
    var input = $('talk-input');
    if (!input) return;
    var text = String(input.value || '').trim();
    if (!text) return;
    input.value = '';
    startInteraction({ kind: 'chat', text: text }, '她正在听');
  }

  function interactItemAction(item, action, button) {
    if (!item) return;
    if (isGameItem(item)) {
      openGameModal();
      return;
    }
    var chosen = String(action || '').trim();
    if (!chosen) {
      chosen = Array.isArray(item.actions) && item.actions.length
        ? String(item.actions[0]) : '';
    }
    if (item.generic_prop) {
      startInteraction({
        kind: 'chat',
        item_name: item.name || '家具',
        room: String(item.room || ''),
        text: '我在' + (item.room ? String(item.room) + '的' : '') +
          (item.name || '家具') + '旁边，想' + (chosen || '看看') +
          '，你在干嘛？'
      }, '她抬起头');
      if (button) button.textContent = '已互动';
      return;
    }
    if (item.placed) {
      var consumeVerb = ['吃掉', '喝掉', '使用'].indexOf(chosen) >= 0;
      if (consumeVerb) {
        useInventoryItem(item.name, button);
        closeItem();
        return;
      }
      startInteraction({
        kind: 'chat',
        item_id: item.id,
        item_name: item.name || '物品',
        room: String(item.room || ''),
        action: chosen,
        text: '我在' + String(item.room || '') + '的' +
          (item.name || '这里') + '，你在干嘛？'
      }, '她看过来');
      if (button) button.textContent = '已互动';
      return;
    }
    var isDish = String(item.id) === 'dining_table' ||
      String(item.name || '').indexOf('餐桌') >= 0;
    if (isDish) {
      startInteraction({
        kind: 'chat',
        item_id: item.id,
        item_name: item.name || '',
        room: item.room || '',
        action: chosen,
        text: '我在' + (item.room || '') + '的' + (item.name || '餐桌') +
          '边，想' + (chosen || '坐下待一会儿') + '，你在干嘛？'
      }, '她抬起头');
    } else {
      startInteraction({
        kind: 'chat',
        item_id: item.id,
        item_name: item.name || '',
        room: item.room || '',
        action: chosen,
        text: '我在' + (item.room || '') + '的' + (item.name || '这里') +
          '，想' + (chosen || '待一会儿') + '，你在干嘛？'
      }, '她抬起头');
    }
    if (button) button.textContent = '已互动';
  }

  function sendItemWish(item, action, button) {
    if (!item) return;
    if (isGameItem(item) && ['打一局', '双人游戏', '开一局桌游', '邀请打游戏'].indexOf(String(action || '')) >= 0) {
      openGameModal();
      return;
    }
    if (item.placed) {
      var placedAction = action || (Array.isArray(item.actions) ? item.actions[0] : '') || '看看';
      var consumeVerb = ['吃掉', '喝掉', '使用'].indexOf(placedAction) >= 0;
      if (consumeVerb) {
        useInventoryItem(item.name, button);
        closeItem();
        return;
      }
      // 摆出来的物品不再走「愿望/实现」接口，直接和角色互动。
      var placedRoom = String(item.room || '');
      startInteraction({
        kind: 'chat',
        item_id: item.id,
        item_name: item.name || '物品',
        room: placedRoom,
        action: placedAction,
        text: '我在' + placedRoom + '的' + (item.name || '这里') + '，你在干嘛？'
      }, '她看过来');
      if (button) button.textContent = '已互动';
      return;
    }
    var selectedAction = action || (Array.isArray(item.actions) ? item.actions[0] : '') || '';
    if (button) {
      button.disabled = true;
      button.textContent = '记下中...';
    }
    return fetch('/api/item_wish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: item.id,
        action: selectedAction,
        date: todayString()
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '写入失败');
        state.wishes = Array.isArray(data.wishes) ? data.wishes : state.wishes;
        if (data.item) {
          var updated = data.item;
          for (var i = 0; i < state.homeItems.length; i++) {
            if (String(state.homeItems[i].id) === String(updated.id)) {
              state.homeItems[i] = updated;
              break;
            }
          }
          if (state.selectedItem && String(state.selectedItem.id) === String(updated.id)) {
            updateItemView(updated);
          }
        }
        updateItemCounts();
        showToast(data.message || ('已记录：' + item.name + ' · ' + selectedAction));
        if (button) button.textContent = '已记录';
      })
      .catch(function (error) {
        showToast('记下失败：' + error.message);
        if (button) {
          button.disabled = false;
          button.textContent = selectedAction;
        }
      });
  }

  function exportFridge() {
    var allIngredients = state.fridge && Array.isArray(state.fridge.ingredients)
      ? state.fridge.ingredients
      : [];
    var query = String(state.fridgeQuery || '').trim().toLowerCase();
    var ingredients = query
      ? allIngredients.filter(function (item) {
          return [item.name, item.category]
            .join(' ').toLowerCase().indexOf(query) >= 0;
        })
      : allIngredients;
    if (!ingredients.length) {
      showToast(query
        ? '当前搜索没有可导出的食材'
        : '冰箱里还没有食材可以导出');
      return;
    }
    var lines = ['分类,名称,数量,单位'];
    ingredients.forEach(function (item) {
      lines.push([
        csvCell(item.category || ''),
        csvCell(item.name || ''),
        item.quantity == null ? '' : Number(item.quantity),
        csvCell(item.unit || '')
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '冰箱食材-' + day + (query ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('冰箱食材已导出');
  }

  function loadFridge() {
    var list = $('fridge-list');
    if (!list) return;
    var search = $('fridge-search');
    if (search) search.value = state.fridgeQuery || '';
    list.innerHTML = '<span class="fridge-loading">正在读取冰箱...</span>';
    fetch('/api/fridge', { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        state.fridge = data;
        renderFridge();
        renderFridgeMenu();
      })
      .catch(function () {
        list.innerHTML = '<span class="fridge-empty">暂时读取不到冰箱</span>';
      });
  }

  function renderFridge() {
    var list = $('fridge-list');
    if (!list) return;
    var allIngredients = state.fridge && Array.isArray(state.fridge.ingredients)
      ? state.fridge.ingredients
      : [];
    var query = String(state.fridgeQuery || '').trim().toLowerCase();
    var ingredients = query
      ? allIngredients.filter(function (item) {
          return [item.name, item.category]
            .join(' ').toLowerCase().indexOf(query) >= 0;
        })
      : allIngredients;
    if (!allIngredients.length) {
      var emptyTitle = $('fridge-title');
      if (emptyTitle) emptyTitle.textContent = '冰箱现有食材';
      list.innerHTML = '<span class="fridge-empty">冰箱里还没有食材</span>';
      return;
    }
    var title = $('fridge-title');
    if (title) {
      title.textContent = query
        ? '筛选出 ' + ingredients.length + ' / ' + allIngredients.length + ' 种'
        : '冰箱现有食材 · ' + allIngredients.length + ' 种';
    }
    if (!ingredients.length) {
      list.innerHTML = '<span class="fridge-empty">没有匹配的食材</span>';
      return;
    }
    var groups = {};
    ingredients.forEach(function (item) {
      var category = item.category || '其他';
      if (!groups[category]) groups[category] = [];
      groups[category].push(item);
    });
    var html = '';
    Object.keys(groups).forEach(function (category) {
      html += '<div class="fridge-group"><span class="fridge-cat">' +
        escapeHtml(category) + '</span><div class="fridge-chips">';
      groups[category].forEach(function (item) {
        var amount = '';
        if (item.quantity !== undefined && item.quantity !== null && item.quantity !== '') {
          amount = '×' + escapeHtml(String(item.quantity)) + escapeHtml(item.unit || '');
        }
        var quantity = Number(item.quantity);
        var empty = !isNaN(quantity) && quantity <= 0;
        html += '<span class="fridge-chip' + (empty ? ' empty' : '') + '">' + escapeHtml(item.name || '') +
          (amount ? '<b>' + amount + '</b>' : '') + '</span>';
      });
      html += '</div></div>';
    });
    var shopping = state.fridge && Array.isArray(state.fridge.shopping)
      ? state.fridge.shopping.slice(-5).reverse()
      : [];
    if (shopping.length) {
      html += '<div class="fridge-shopping"><h4>最近采购</h4>' +
        shopping.map(function (entry) {
          return '<div class="fridge-shopping-row"><span>' +
            escapeHtml(String(entry.date || '').slice(5)) + ' · ' +
            escapeHtml(entry.scene || '采买') + '</span><b>' +
            escapeHtml((entry.items || []).join('、')) + '</b></div>';
        }).join('') + '</div>';
    }
    list.innerHTML = html;
  }

  function renderFridgeMenu() {
    var box = $('fridge-menu');
    if (!box) return;
    var menu = state.fridge && state.fridge.menu;
    if (!menu || !Array.isArray(menu.meals) || !menu.meals.length) {
      box.classList.add('hidden');
      box.innerHTML = '';
      return;
    }
    var labels = { home: '在家做', out: '外食', simple: '简单解决' };
    var html = '<div class="fridge-menu-title">今日菜单</div>';
    menu.meals.forEach(function (meal) {
      var dish = meal.dish || (meal.source === 'simple' ? '剩菜或加餐' : '');
      html += '<div class="fridge-menu-row"><span>' + escapeHtml(meal.meal || '') +
        '</span><b>' + escapeHtml(dish) + '</b><em>' +
        escapeHtml(labels[meal.source] || '') + '</em></div>';
      var alternatives = Array.isArray(meal.alternatives)
        ? meal.alternatives : [];
      if (alternatives.length) {
        html += '<div class="fridge-menu-alt">备选：' +
          alternatives.map(function (item) {
            var name = String((item || {}).name || '');
            var missing = Array.isArray((item || {}).missing)
              ? (item || {}).missing : [];
            return escapeHtml(name) +
              (missing.length
                ? '（缺 ' + missing.map(escapeHtml).join('、') + '）'
                : '');
          }).join('、') + '</div>';
      }
    });
    if (Array.isArray(menu.shopping) && menu.shopping.length) {
      html += '<div class="fridge-menu-shopping">待采购：' +
        menu.shopping.map(escapeHtml).join('、') + '</div>';
    }
    if (Array.isArray(menu.low_stock) && menu.low_stock.length) {
      html += '<div class="fridge-menu-low">库存偏低：' +
        menu.low_stock.map(escapeHtml).join('、') + '</div>';
    }
    box.innerHTML = html;
    box.classList.remove('hidden');
  }

  function randomFridgeRecipe() {
    var box = $('fridge-recipe');
    if (!box) return;
    box.classList.remove('hidden');
    box.innerHTML = '<span class="fridge-loading">正在从现有食材里搭配...</span>';
    fetch('/api/fridge/recipe', { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok || !data.recipe) throw new Error('暂时搭配不出来');
        renderFridgeRecipe(data.recipe);
      })
      .catch(function (error) {
        box.innerHTML = '<span class="fridge-empty">' + escapeHtml(error.message) + '</span>';
      });
  }

  function renderFridgeRecipe(recipe) {
    var box = $('fridge-recipe');
    if (!box) return;
    var ingredients = Array.isArray(recipe.ingredients)
      ? recipe.ingredients.map(escapeHtml).join('、')
      : '';
    var method = recipe.method ? ' · 做法：' + escapeHtml(recipe.method) : '';
    var missing = Array.isArray(recipe.missing) ? recipe.missing : [];
    var html = '<div class="fridge-recipe-head"><span>' +
      escapeHtml(recipe.meal || '推荐') + '</span><h4>' +
      escapeHtml(recipe.name || '') + '</h4></div>';
    html += '<div class="fridge-recipe-meta">食材：' + ingredients + method + '</div>';
    if (missing.length) {
      html += '<div class="fridge-missing">还缺：' +
        missing.map(escapeHtml).join('、') + '</div>';
    } else {
      html += '<div class="fridge-ready">现有食材足够，可以直接做</div>';
    }
    box.innerHTML = html;
  }

  function toggleItemDrawer(show) {
    var drawer = $('item-drawer');
    if (!drawer) return;
    var shouldShow = typeof show === 'boolean' ? show : drawer.classList.contains('hidden');
    drawer.classList.toggle('hidden', !shouldShow);
    if (shouldShow) {
      var search = $('item-search');
      if (search) search.value = state.itemQuery || '';
      renderItemDrawer();
      $('item-popover').classList.add('hidden');
    }
  }

  function clockText() {
    var data = state.data;
    var pageParams = new URLSearchParams(window.location.search);
    if (pageParams.get('time') && data && data.now_time) return data.now_time;
    var now = new Date();
    return [now.getHours(), now.getMinutes(), now.getSeconds()]
      .map(function (n) { return String(n).padStart(2, '0'); })
      .join(':');
  }

  function updateClock() {
    var clock = $('clock');
    if (clock) clock.textContent = clockText();
    var timelineNow = $('timeline-now');
    if (timelineNow) timelineNow.textContent = '现在 ' + clockText().slice(0, 5);
  }

  function render() {
    updateClock();
    window.__VL_CHARACTER_SRC = characterArtSrc();
    renderHeader();
    renderHome();
    renderScene();
    renderRoomDecor();
    renderNext();
    renderTimeline();
    renderScenePicker();
  }

  function renderRoomDecor() {
    // 已摆放物品现在直接画进房间 SVG，和家具一起受镜头、遮挡与点击处理。
    var old = document.querySelector('.room-decor');
    if (old) old.remove();
  }

  function renderNeedPills(needs) {
    var root = $('need-pills');
    if (!root) return;
    if (!needs || typeof needs !== 'object') {
      root.innerHTML = '';
      return;
    }
    var meta = [
      ['energy', '⚡', '精力'],
      ['satiety', '🍚', '饱腹'],
      ['hydration', '💧', '水分'],
      ['hygiene', '🫧', '清洁'],
      ['mood', '🙂', '心情'],
      ['willingness', '✨', '意愿'],
      ['health', '❤️', '健康']
    ];
    var labels = needs.labels || {};
    var html = '';
    meta.forEach(function (item) {
      var value = Number(needs[item[0]]);
      if (isNaN(value)) return;
      var label = String(labels[item[0]] || '');
      html += '<span class="need-pill ' + item[0] + '" title="' +
        escapeHtml(item[2] + (label ? ' · ' + label : '')) + '">' +
        item[1] + ' ' + Math.round(value) + '</span>';
    });
    if (needs.sick) {
      var sickTitle = String(needs.illness_label || '生病中') +
        (needs.sick_days > 1 ? ' · 第 ' + Math.round(Number(needs.sick_days)) + ' 天' : '') +
        (Array.isArray(needs.symptoms) && needs.symptoms.length
          ? ' · ' + needs.symptoms.join('、')
          : '');
      html += '<span class="need-pill sick" title="' + escapeHtml(sickTitle) + '">🤒 生病</span>';
    } else if (needs.recovering) {
      var recoverTitle = '恢复期' +
        (needs.sick_days > 1 ? ' · 病程第 ' + Math.round(Number(needs.sick_days)) + ' 天' : '') +
        (needs.recovery_days_left ? ' · 预计还需 ' + Math.round(Number(needs.recovery_days_left)) + ' 天' : '') +
        (Array.isArray(needs.symptoms) && needs.symptoms.length
          ? ' · ' + needs.symptoms.join('、')
          : '');
      html += '<span class="need-pill recovering" title="' + escapeHtml(recoverTitle) + '">🤒 恢复期</span>';
    }
    if (needs.weak_constitution) {
      html += '<span class="need-pill weak" title="' +
        escapeHtml('最近30天生病 ' + Math.round(Number(needs.recent_illness_days || 0)) + ' 天，身体底子有点虚') +
        '">🫀 体虚</span>';
    }
    if (needs.social_hangover_yesterday) {
      html += '<span class="need-pill social-hangover" title="' +
        escapeHtml('昨天聊得太久，今天还有点没缓过来') +
        '">😮‍💨 社交后劲</span>';
    }
    if (needs.need_solitude) {
      html += '<span class="need-pill social-low" title="' +
        escapeHtml('今天聊得太久，社交电量用完了，想安静待会儿') +
        '">🔋 社交电量低</span>';
    }
    if (needs.socially_satisfied) {
      html += '<span class="need-pill social-satisfied" title="' +
        escapeHtml('最近 7 天和朋友见得挺多，心里踏实') +
        '">🫂 社交满足</span>';
    }
    if (needs.evening_sleepiness) {
      html += '<span class="need-pill evening-sleepiness" title="' +
        escapeHtml('这个点有点困了，想早点睡') + '">🌙 困了</span>';
    }
    if (needs.morning_grogginess && !needs.morning_grogginess_relief) {
      html += '<span class="need-pill morning-grogginess" title="' +
        escapeHtml('昨晚没睡够，早上有点懵') + '">🥱 没睡醒</span>';
    }
    if (needs.afternoon_dip && !needs.afternoon_dip_relief) {
      html += '<span class="need-pill afternoon-dip" title="' +
        escapeHtml('午后有点犯困，效率不太高') + '">😴 午后犯困</span>';
    }
    if (needs.good_sleep_streak) {
      var earlySleepDays = Math.max(0, Math.round(Number(needs.good_sleep_days_7d || 0)));
      var earlySleepTitle = earlySleepDays > 0
        ? '最近 7 天有 ' + earlySleepDays + ' 天睡得比较早，作息在往好的方向走'
        : '连续几天睡得不晚，作息在往好的方向走';
      html += '<span class="need-pill good-sleep" title="' +
        escapeHtml(earlySleepTitle) + '">🌙 早睡</span>';
    }
    var debt = Number(needs.sleep_debt_minutes);
    if (!isNaN(debt) && debt >= 60) {
      var debtHours = (debt / 60).toFixed(1);
      html += '<span class="need-pill debt" title="' +
        escapeHtml('睡眠债 · 约 ' + debtHours + ' 小时') + '">💤 ' +
        debtHours + 'h</span>';
    }
    var discomfort = Number(needs.discomfort_count);
    if (!isNaN(discomfort) && discomfort >= 2) {
      var discomfortNames = [];
      if (needs.eye_strain) discomfortNames.push('眼睛酸');
      if (needs.muscle_soreness) discomfortNames.push('肌肉酸痛');
      if (needs.nap_inertia) discomfortNames.push('午睡发懵');
      if (needs.stomach_discomfort) discomfortNames.push('肠胃不适');
      if (needs.late_meal) discomfortNames.push('夜宵胃胀');
      if (needs.breakfast_skipped) discomfortNames.push('没吃早饭');
      if (needs.commute_fatigue) discomfortNames.push('通勤疲劳');
      if (needs.bad_weather_commute) discomfortNames.push('雨天通勤');
      if (needs.dehydration_headache) discomfortNames.push('缺水头痛');
      if (needs.sunburn) discomfortNames.push('晒伤');
      if (needs.sunburn_aftermath) discomfortNames.push('晒伤未退');
      if (needs.reading_fatigue) discomfortNames.push('看书眼酸');
      if (needs.tooth_sensitivity) discomfortNames.push('牙齿酸');
      if (needs.body_odor) discomfortNames.push('身上有味道');
      if (needs.stiff_neck) discomfortNames.push('肩颈发僵');
      if (needs.overtraining) discomfortNames.push('运动过量');
      if (needs.overtraining_yesterday) discomfortNames.push('昨天练太狠');
      if (needs.afternoon_dip) discomfortNames.push('午后犯困');
      if (needs.pollen_allergy) discomfortNames.push('花粉过敏');
      var discomfortSeverity = discomfort >= 5
        ? ' discomfort-high'
        : (discomfort >= 3 ? ' discomfort-mid' : '');
      html += '<span class="need-pill discomfort' + discomfortSeverity + '" title="' +
        escapeHtml('不适 · ' + discomfortNames.join('、')) + '">🩹 ' +
        Math.round(discomfort) + '</span>';
    }
    root.innerHTML = html;
  }

  function renderCompactStatus(data) {
    var brief = $('status-brief');
    var dot = $('status-dot');
    if (!brief) return;
    var now = data.now || null;
    var needs = data.needs || {};
    var labels = needs.labels || {};
    var money = data.money || {};
    var affection = data.affection || {};
    var kind = now ? now.kind : 'home';
    var parts = [
      kind === 'outside' ? '外出' : kind === 'transit' ? '路上' : '在家',
      '精力 ' + Number(needs.energy == null ? 0 : needs.energy),
      '饱腹 ' + Number(needs.satiety == null ? 0 : needs.satiety),
      '心情 ' + Number(needs.mood == null ? 0 : needs.mood)
    ];
    var balance = Number(money.balance);
    if (!isNaN(balance)) parts.push('💰 ' + balance);
    var score = Number(affection.score);
    if (!isNaN(score)) parts.push('💗 ' + (affection.level || '') + ' ' + score);
    var lowNeeds = [
      ['精力', needs.energy], ['饱腹', needs.satiety],
      ['水分', needs.hydration], ['心情', needs.mood],
      ['健康', needs.health], ['清洁', needs.hygiene]
    ].filter(function (item) {
      return item[1] != null && Number(item[1]) < 30;
    });
    if (lowNeeds.length) {
      parts.push('⚠️ ' + lowNeeds.slice(0, 2).map(function (item) {
        return item[0];
      }).join('、') + '偏低');
      brief.title = '需要关注：' + lowNeeds.map(function (item) {
        return item[0] + ' ' + Math.round(Number(item[1]));
      }).join('、');
    } else {
      brief.title = '查看完整状态';
    }
    brief.textContent = parts.join(' · ');
    if (dot) {
      dot.className = 'status-dot ' + (
        kind === 'outside' ? 'outside' : kind === 'transit' ? 'transit' : 'home'
      ) + (lowNeeds.length ? ' warning' : '');
    }
    if (!$('status-modal').classList.contains('hidden')) {
      renderStatusModal();
    }
  }

  function statusMetric(label, value) {
    return '<div class="status-metric"><small>' + escapeHtml(label) +
      '</small><b>' + escapeHtml(String(value)) + '</b></div>';
  }

  function statusMeter(label, value, desc) {
    var number = Number(value);
    var percent = isNaN(number) ? 0 : Math.max(0, Math.min(100, number));
    var tone = percent >= 70 ? 'good' : percent >= 40 ? 'mid' : 'low';
    return '<div class="status-meter"><div class="status-meter-head"><small>' +
      escapeHtml(label) + '</small><b>' +
      (isNaN(number) ? '--' : Math.round(number) + ' · ' + (desc || '')) +
      '</b></div><div class="status-meter-bar"><span class="' + tone +
      '" style="width:' + percent + '%"></span></div></div>';
  }

  function trendRangeDays() {
    var value = Number(state.statusTrendRange);
    return [7, 14, 30].indexOf(value) >= 0 ? value : 7;
  }

  function exportStatusTrend() {
    var metric = state.statusTrendMetric || 'mood';
    var labels = { mood: '心情', energy: '精力', satiety: '饱腹', hydration: '水分', health: '健康' };
    var range = trendRangeDays();
    var rows = ((state.data && state.data.mood_history) || []).slice(-range);
    if (!rows.length) {
      showToast('还没有可导出的记录');
      return;
    }
    var day = new Date().toISOString().slice(0, 10);
    var lines = ['日期,' + labels[metric]];
    rows.forEach(function (entry) {
      var value = entry[metric] == null ? '' : entry[metric];
      lines.push(String(entry.date || '') + ',' + value);
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '虚拟人生-' + labels[metric] + '-' + day + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('状态趋势已导出');
  }

  function statusTrend(history) {
    var metric = state.statusTrendMetric || 'mood';
    var range = trendRangeDays();
    var labels = { mood: '心情', energy: '精力', satiety: '饱腹', hydration: '水分', health: '健康' };
    var switchHtml = '<div class="status-trend-switch">' + [
      ['mood', '心情'], ['energy', '精力'], ['satiety', '饱腹'], ['hydration', '水分'], ['health', '健康']
    ].map(function (item) {
      return '<button type="button" data-status-metric="' + item[0] + '"' +
        (metric === item[0] ? ' class="active"' : '') + '>' + item[1] + '</button>';
    }).join('') + '</div>';
    var rangeHtml = '<div class="status-trend-range">' + [7, 14, 30].map(function (days) {
      return '<button type="button" data-status-range="' + days + '"' +
        (range === days ? ' class="active"' : '') + '>' + days + '天</button>';
    }).join('') + '</div>';
    var exportHtml = '<button type="button" class="status-trend-export" ' +
      'data-status-export="1">导出</button>';
    var entries = (history || []).filter(function (entry) {
      return entry && entry[metric] != null;
    }).slice(-range);
    var head = '<div class="status-trend-head"><small>最近 ' + range + ' 天' +
      labels[metric] + '</small><div class="status-trend-controls">' +
      switchHtml + rangeHtml + exportHtml + '</div></div>';
    if (!entries.length) {
      return '<div class="status-trend metric-' + metric + '">' + head +
        '<p class="memory-empty">还没有这项记录。</p></div>';
    }
    var width = 100;
    var height = 34;
    var values = entries.map(function (entry) {
      return Math.max(0, Math.min(100, Number(entry[metric]) || 0));
    });
    var average = values.reduce(function (sum, value) {
      return sum + value;
    }, 0) / values.length;
    var points = values.map(function (value, index) {
      var x = entries.length === 1 ? width / 2 : index / (entries.length - 1) * width;
      var y = height - value / 100 * height;
      return x.toFixed(1) + ',' + y.toFixed(1);
    }).join(' ');
    var averageY = (height - average / 100 * height).toFixed(1);
    var last = entries[entries.length - 1];
    var latest = Number(values[values.length - 1]).toFixed(0);
    var delta = Number(values[values.length - 1]) - Number(values[0]);
    var deltaText = (delta >= 0 ? '+' : '') + delta.toFixed(0);
    return '<div class="status-trend metric-' + metric + '">' + head +
      '<div class="status-trend-value">' + latest +
      '<small>平均 ' + average.toFixed(0) + ' · 较起点 ' + deltaText + '</small></div>' +
      '<svg viewBox="0 0 ' + width + ' ' + height + '" preserveAspectRatio="none">' +
      '<line class="status-trend-average" x1="0" y1="' + averageY +
      '" x2="100" y2="' + averageY + '"/>' +
      '<polyline points="' + points + '"/></svg>' +
      '<div class="status-trend-dates"><span>' +
      escapeHtml(String(entries[0].date || '').slice(5)) + '</span><span>' +
      escapeHtml(String(last.date || '').slice(5)) + '</span></div></div>';
  }

  function statusLowTips(needs) {
    var checks = [
      ['energy', '精力偏低，去床上休息一会儿。'],
      ['satiety', '饱腹偏低，去厨房吃点东西。'],
      ['hydration', '水分偏低，去冰箱拿点喝的。'],
      ['mood', '心情偏低，去阳台或咖啡馆散散心。'],
      ['health', '健康偏低，记得按时吃饭和休息。'],
      ['hygiene', '清洁偏低，去浴室洗漱一下。']
    ];
    var tips = checks.filter(function (item) {
      return needs[item[0]] != null && Number(needs[item[0]]) < 30;
    }).map(function (item) {
      return item[1];
    });
    if (!tips.length) return '';
    return '<div class="status-low-tips"><h5>需要关注</h5>' +
      tips.map(function (tip) {
        return '<p>' + escapeHtml(tip) + '</p>';
      }).join('') + '</div>';
  }

  function renderStatusModal() {
    var body = $('status-modal-body');
    if (!body) return;
    var data = state.data || {};
    var now = data.now || null;
    var needs = data.needs || {};
    var labels = needs.labels || {};
    var money = data.money || {};
    var affection = data.affection || {};
    var userState = data.user_state || {};
    var html = '<div class="status-hero"><div><small>现在</small><b>' +
      escapeHtml(now ? (now.activity || '自由时间') : '今日还没有日程') +
      '</b><span>' + escapeHtml(now ? (now.location || '未知') : '等待生成') +
      '</span></div><div class="status-hero-side">' +
      (userState.sleeping ? '<span class="status-sleep">主人在睡</span>' : '') +
      '<span>' + escapeHtml(now ? (AVAIL_LABEL[now.availability] || now.availability || '--') : '--') +
      ' 可打扰度</span></div></div>';
    var weather = data.weather || {};
    var outfit = data.outfit || {};
    var weatherText = weather.condition
      ? weather.condition +
        (weather.temperature_low != null && weather.temperature_high != null
          ? ' ' + weather.temperature_low + '~' + weather.temperature_high + '°C'
          : '')
      : '--';
    html += '<div class="status-context">' + [
      ['天气', weatherText],
      ['今日主题', data.theme || data.mood || '--'],
      ['穿搭', outfit.summary || outfit.style || '--'],
      ['计划', data.plan_date || '未生成']
    ].map(function (row) {
      return statusMetric(row[0], row[1]);
    }).join('') + '</div>';
    var timelineItems = data.timeline || [];
    if (timelineItems.length) {
      var planCounts = { home: 0, outside: 0, transit: 0, sleep: 0 };
      var planMinutes = 0;
      timelineItems.forEach(function (item) {
        if (planCounts[item.kind] != null) planCounts[item.kind] += 1;
        planMinutes += Math.max(
          0,
          Number(item.end_min || 0) - Number(item.start_min || 0)
        );
      });
      html += '<div class="status-plan-summary clickable" ' +
        'data-status-plan="1" role="button" tabindex="0" ' +
        'title="查看今日日程"><small>今日日程</small><b>' +
        timelineItems.length + ' 段</b><span>在家 ' + planCounts.home +
        ' · 外出 ' + planCounts.outside + ' · 路上 ' + planCounts.transit +
        ' · 共 ' + Math.round(planMinutes / 60 * 10) / 10 + ' 小时</span>' +
        (data.now
          ? '<span class="status-plan-now">现在：' +
            escapeHtml(data.now.activity || '一段日程') +
            (data.now.location
              ? ' · ' + escapeHtml(data.now.location)
              : '') +
            '</span>'
          : '') +
        '</div>';
    }
    var outfitItems = outfit.items || [];
    if (outfitItems.length) {
      var outfitLabels = {
        hairstyle: '发型', headwear: '帽子与发饰', underwear: '内衣与打底',
        underpants: '内裤', top: '上装', bottom: '下装',
        dress: '连衣身着装', legwear: '袜子与腿部穿搭', outerwear: '外套',
        shoes: '鞋履', accessory: '配饰', bag: '包具',
        makeup: '妆容', fragrance: '香氛', other: '其他'
      };
      html += '<div class="status-outfit clickable" data-status-outfit="1" ' +
        'role="button" tabindex="0" title="查看穿搭详情">' +
        '<small>今日穿搭</small><div>' +
        outfitItems.map(function (entry) {
          return '<span title="' + escapeHtml(entry.details || '') + '">' +
            escapeHtml(outfitLabels[entry.category] || entry.category) +
            ' · ' + escapeHtml(entry.name) + '</span>';
        }).join('') + '</div></div>';
    }
    var travelInfo = data.travel;
    if (travelInfo && travelInfo.city) {
      var daysUntil = Number(travelInfo.days_until || 0);
      var travelPhase = String(travelInfo.phase || '');
      var duringTrip = ['depart', 'away', 'return'].indexOf(travelPhase) >= 0;
      var travelText = duringTrip
        ? (travelPhase === 'return' ? '今天返程' : '旅行中')
        : travelPhase === 'afterglow' ? '旅行余韵'
          : daysUntil > 0 ? '还有 ' + daysUntil + ' 天出发'
            : daysUntil === 0 ? '今天出发' : '旅行中';
      html += '<div class="status-travel clickable" data-status-travel="1" ' +
        'role="button" tabindex="0" title="查看旅行计划">' +
        '<small>' + (duringTrip || travelPhase === 'afterglow'
          ? '正在旅行' : '下一次旅行') + '</small><b>' +
        escapeHtml(travelInfo.city) + '</b><span>' +
        escapeHtml(travelInfo.depart || '') + ' → ' +
        escapeHtml(travelInfo.back || '') + ' · ' +
        escapeHtml(travelText) + ' · ' +
        escapeHtml(travelInfo.transport || '') + '</span></div>';
    }
    var holidayInfo = data.holidays || {};
    var todayHolidays = holidayInfo.today || [];
    var upcomingHolidays = holidayInfo.upcoming || [];
    if (todayHolidays.length || upcomingHolidays.length) {
      var holidayParts = todayHolidays.map(function (item) {
        return '今天 · ' + String(item.name || '');
      });
      var holidayBase = new Date(
        String(data.plan_date || '') + 'T00:00:00'
      ).getTime();
      upcomingHolidays.slice(0, 3).forEach(function (item) {
        var target = new Date(
          String(item.date || '') + 'T00:00:00'
        ).getTime();
        var days = isFinite(target) && isFinite(holidayBase)
          ? Math.round((target - holidayBase) / 86400000) : NaN;
        holidayParts.push(
          (isFinite(days) && days > 0 ? days + ' 天后 · ' : '') +
          String(item.name || '')
        );
      });
      html += '<div class="status-holiday"><small>节日提醒</small><div>' +
        holidayParts.map(function (text) {
          return '<span>' + escapeHtml(text) + '</span>';
        }).join('') + '</div></div>';
    }
    var walletInfo = data.wallet || {};
    if (walletInfo.balance != null) {
      var walletBalance = Math.round(Number(walletInfo.balance) * 100) / 100;
      var walletGoal = walletInfo.goal;
      var walletGoalHtml = '';
      if (walletGoal && Number(walletGoal.target || 0) > 0) {
        var walletTarget = Number(walletGoal.target);
        var walletProgress = Number(
          walletGoal.progress == null ? walletBalance : walletGoal.progress
        );
        var walletPercent = Math.max(0, Math.min(100, Math.round(
          walletProgress / walletTarget * 100
        )));
        var walletAchieved = Boolean(walletGoal.achieved) ||
          walletProgress >= walletTarget;
        walletGoalHtml = '<span> · 目标 ' +
          escapeHtml(String(walletGoal.name || '')) + ' ' +
          Math.round(walletProgress) + '/' +
          Math.round(walletTarget) +
          (walletAchieved
            ? ' · 已达成'
            : ' · 还差 ' + Math.round(walletTarget - walletProgress)) +
          '</span>' +
          '<div class="status-wallet-progress"><span style="width:' +
          walletPercent + '%"></span></div>';
      }
      var walletTodayHtml = '';
      var walletTodayExpense = Number(walletInfo.today_expense || 0);
      var walletTodayIncome = Number(walletInfo.today_income || 0);
      if (walletTodayExpense > 0) {
        walletTodayHtml = '<span class="status-wallet-today">今日支出 -' +
          Math.round(walletTodayExpense * 100) / 100 + ' 元</span>';
      } else if (walletTodayIncome > 0) {
        walletTodayHtml = '<span class="status-wallet-today">今日收入 +' +
          Math.round(walletTodayIncome * 100) / 100 + ' 元</span>';
      }
      html += '<div class="status-wallet clickable" data-status-wallet="1" ' +
        'role="button" tabindex="0" title="打开钱包"><small>钱包</small><b>' +
        escapeHtml(String(walletBalance)) + ' 元</b>' +
        walletTodayHtml + walletGoalHtml + '</div>';
    }
    var statusTodayReading = periodBookReadingLabel(1);
    var statusReadingStreak = bookReadingStreak();
    var statusReadingGoal = Math.max(1, Number(state.readingGoal) || 30);
    var statusReadingGoalPercent = Math.min(100, Math.round(
      periodBookReadingSeconds(1) / (statusReadingGoal * 60) * 100
    ));
    if (statusTodayReading || statusReadingStreak > 1) {
      var statusReadingMeta = [];
      if (statusReadingStreak > 1) {
        statusReadingMeta.push('连续 ' + statusReadingStreak + ' 天');
      }
      statusReadingMeta.push(statusTodayReading
        ? '目标 ' + statusReadingGoalPercent + '%'
        : '目标 ' + statusReadingGoal + ' 分钟');
      html += '<div class="status-reading clickable" data-status-reading="1" ' +
        'role="button" tabindex="0" title="打开书架"><small>阅读</small><b>' +
        (statusTodayReading
          ? '今日 ' + escapeHtml(statusTodayReading)
          : '今天还没读') + '</b>' +
        '<span class="status-reading-streak">' +
        escapeHtml(statusReadingMeta.join(' · ')) + '</span></div>';
    }
    var healthInfo = data.health || {};
    var healthParts = [];
    var healthStatus = String(healthInfo.status || '');
    if (healthStatus === 'sick') {
      healthParts.push('生病中 · 第 ' +
        Math.max(1, Number(healthInfo.sick_days || 1)) + ' 天');
      if (Number(healthInfo.recovery_required_days || 0) > 0) {
        healthParts.push('需要恢复 ' +
          Number(healthInfo.recovery_required_days) + ' 天');
      }
    } else if (healthStatus === 'recovering') {
      healthParts.push('恢复中' +
        (Number(healthInfo.recovery_required_days || 0) > 0
          ? ' · 还需 ' + Number(healthInfo.recovery_required_days) + ' 天'
          : ''));
    } else if (Number(healthInfo.recent_illness_days || 0) > 0) {
      healthParts.push('最近 30 天生病 ' +
        Number(healthInfo.recent_illness_days) + ' 天');
    }
    if (healthInfo.weak_constitution) {
      healthParts.push('身体底子偏弱');
    }
    var statusRecoveryLog = Array.isArray(healthInfo.recovery_log)
      ? healthInfo.recovery_log : [];
    var statusLatestRecovery = statusRecoveryLog.length &&
      statusRecoveryLog[statusRecoveryLog.length - 1] &&
      typeof statusRecoveryLog[statusRecoveryLog.length - 1] === 'object'
      ? statusRecoveryLog[statusRecoveryLog.length - 1] : null;
    if (statusLatestRecovery &&
        (healthStatus === 'sick' || healthStatus === 'recovering')) {
      var statusRecoveryActions = Array.isArray(statusLatestRecovery.actions)
        ? statusLatestRecovery.actions : [];
      if (statusRecoveryActions.length) {
        healthParts.push('今日恢复 ' + statusRecoveryActions.length + ' 项');
      }
    }
    if (healthParts.length) {
      html += '<div class="status-health clickable" data-status-health="1" ' +
        'role="button" tabindex="0" title="查看健康记录">' +
        '<small>健康记录</small><div>' +
        healthParts.map(function (text) {
          return '<span>' + escapeHtml(text) + '</span>';
        }).join('') + '</div></div>';
    }
    html += '<div class="status-grid status-meters">' + [
      ['精力', needs.energy, labels.energy],
      ['饱腹', needs.satiety, labels.satiety],
      ['水分', needs.hydration, labels.hydration],
      ['心情', needs.mood, labels.mood],
      ['意愿', needs.willingness, labels.willingness],
      ['健康', needs.health, labels.health],
      ['清洁', needs.hygiene, labels.hygiene]
    ].map(function (row) {
      return statusMeter(row[0], row[1], row[2]);
    }).join('') + '</div>';
    html += statusLowTips(needs);
    var worldEvent = data.world_event || {};
    if (worldEvent.title || worldEvent.summary) {
      html += '<div class="status-world clickable" data-status-world="1" ' +
        'role="button" tabindex="0" title="打开记忆">' +
        '<small>今天的小世界</small><b>' +
        escapeHtml(worldEvent.title || '今日小事') + '</b><p>' +
        escapeHtml(worldEvent.summary || '') + '</p></div>';
    }
    html += '<div class="status-wallet">' + [
      ['钱包', (money.balance == null ? '--' : money.balance + ' 元')],
      ['关系', (affection.level || '陌生') + ' · ' + (affection.score == null ? '--' : affection.score)],
      ['认识', (affection.days_known == null ? '--' : affection.days_known + ' 天')],
      ['称呼', affection.nickname || '主人']
    ].map(function (row) {
      return statusMetric(row[0], row[1]);
    }).join('') + '</div>';
    if (needs.summary) {
      html += '<div class="status-summary">' + escapeHtml(needs.summary) + '</div>';
    }
    html += statusTrend(data.mood_history || []);
    html += '<div class="status-quick">' + [
      ['wallet-toggle', '💰 钱包'],
      ['garage-toggle', '🚗 车库'],
      ['cook-open', '🍳 做饭'],
      ['trips-open', '✈️ 旅行'],
      ['affection-pill', '💗 关系'],
      ['system-toggle', '⚙️ 系统']
    ].map(function (item) {
      return '<button type="button" data-status-target="' + item[0] + '">' +
        item[1] + '</button>';
    }).join('') + '</div>';
    var statusActivityContent = state.statusActivityHtml ||
      (state.statusActivityLoaded
        ? ''
        : '<p class="inventory-empty">最近动态加载中...</p>');
    html += '<div class="status-activity" id="status-activity">' +
      statusActivityContent + '</div>';
    var previousScroll = body.scrollTop;
    body.innerHTML = html;
    if (previousScroll) body.scrollTop = previousScroll;
    if (state.statusActivityLoaded &&
        Date.now() - Number(state.statusActivityAt || 0) > 30000) {
      loadStatusActivity();
    }
  }

  function loadStatusActivity() {
    if (state.statusActivityLoading) return;
    state.statusActivityLoading = true;
    var box = $('status-activity');
    if (!box) {
      state.statusActivityLoading = false;
      return;
    }
    fetch('/api/recent_activity?persona=' + encodeURIComponent(
      (state.data && state.data.persona) || ''
    ), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        var events = (data && data.events) || [];
        var content = '';
        if (events.length) {
          content = '<div class="status-activity-head">' +
            '<small>最近动态</small>' +
            '<button type="button" class="mini-btn" ' +
            'data-status-activity-refresh="1">刷新</button>' +
            '<button type="button" class="mini-btn" ' +
            'data-status-activity="1">查看全部</button></div>' +
            events.slice(0, 3).map(function (event) {
              return '<div class="activity-row clickable" ' +
                'data-status-activity-kind="' + escapeHtml(event.kind || '') + '" ' +
                'role="button" tabindex="0"><span class="activity-icon">' +
                escapeHtml(event.icon || '·') + '</span>' +
                '<div class="activity-copy"><b>' +
                escapeHtml(event.title || '一件小事') + '</b><small>' +
                escapeHtml(event.detail || '') + '</small></div><em>' +
                escapeHtml(activityTimeText(event.at)) + '</em></div>';
            }).join('');
        }
        state.statusActivityHtml = content;
        state.statusActivityLoaded = true;
        state.statusActivityAt = Date.now();
        state.statusActivityLoading = false;
        box.innerHTML = content;
      })
      .catch(function () {
        state.statusActivityHtml = '';
        state.statusActivityLoaded = true;
        state.statusActivityAt = Date.now();
        state.statusActivityLoading = false;
        box.innerHTML = '';
      });
  }

  function openStatus() {
    state.statusActivityHtml = '';
    state.statusActivityLoaded = false;
    state.statusActivityAt = 0;
    state.statusActivityLoading = false;
    $('status-modal').classList.remove('hidden');
    renderStatusModal();
    loadStatusActivity();
  }

  function closeStatus() {
    $('status-modal').classList.add('hidden');
  }

  function openFunctionMenu() {
    $('function-menu').classList.remove('hidden');
  }

  function closeFunctionMenu() {
    $('function-menu').classList.add('hidden');
  }

  function openIntegrations() {
    closeFunctionMenu();
    $('integration-modal').classList.remove('hidden');
    loadIntegrations();
  }

  function closeIntegrations() {
    $('integration-modal').classList.add('hidden');
  }

  function integrationConfigText(summary) {
    if (!summary || typeof summary !== 'object') return '';
    var parts = [];
    Object.keys(summary).forEach(function (key) {
      var value = summary[key];
      if (value === null || value === undefined || value === '') return;
      if (typeof value === 'object') {
        try { value = JSON.stringify(value); } catch (error) { value = ''; }
      }
      if (value === '') return;
      parts.push(key + '=' + String(value));
    });
    return parts.slice(0, 5).join(' · ');
  }

  function renderIntegrations(data) {
    var list = $('integration-list');
    if (!list) return;
    var items = data && Array.isArray(data.items) ? data.items : [];
    var counts = (data && data.counts) || {};
    $('integration-sub').textContent = items.length
      ? ('共 ' + (counts.total || items.length) + ' 个插件 · 运行中 ' +
         (counts.active || 0) + ' · 未启用 ' + (counts.inactive || 0))
      : '没有发现已安装插件';
    if (!items.length) {
      list.innerHTML = '<div class="integration-empty">没有发现可整合的插件。</div>';
      return;
    }
    list.innerHTML = items.map(function (item) {
      var active = Boolean(item.activated);
      var title = item.title || item.display_name || item.name || '未命名插件';
      var name = item.name || '';
      var version = item.version ? ('v' + String(item.version).replace(/^v/i, '')) : '';
      var tags = Array.isArray(item.capabilities) ? item.capabilities : [];
      var configText = integrationConfigText(item.config_summary);
      return '<article class="integration-card' + (active ? '' : ' inactive') + '">' +
        '<div class="integration-card-head">' +
          '<span class="integration-emoji">' + escapeHtml(item.emoji || '🧩') + '</span>' +
          '<b class="integration-title">' + escapeHtml(title) + '</b>' +
          (version ? '<span class="integration-version">' + escapeHtml(version) + '</span>' : '') +
          '<span class="integration-badge' + (active ? '' : ' off') + '">' +
            (active ? '运行中' : '未启用') + '</span>' +
        '</div>' +
        '<p class="integration-desc">' + escapeHtml(item.desc || '') + '</p>' +
        (tags.length
          ? '<div class="integration-tags">' + tags.map(function (tag) {
              return '<span class="integration-tag">' + escapeHtml(tag) + '</span>';
            }).join('') + '</div>'
          : '') +
        '<p class="integration-note">' + escapeHtml(item.note || '') + '</p>' +
        (configText
          ? '<div class="integration-config">' + escapeHtml(configText) + '</div>'
          : '') +
      '</article>';
    }).join('');
  }

  function loadIntegrations() {
    var list = $('integration-list');
    if (list) list.innerHTML = '<div class="integration-empty">正在读取插件状态…</div>';
    fetch('/api/integrations', { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data || !data.ok) throw new Error((data && data.error) || '读取失败');
        renderIntegrations(data);
      })
      .catch(function (error) {
        $('integration-sub').textContent = '读取失败';
        if (list) {
          list.innerHTML = '<div class="integration-empty">' +
            escapeHtml(error && error.message ? error.message : '读取失败') +
            '</div>';
        }
      });
  }

  function renderHeader() {
    var data = state.data || {};
    var now = data.now || null;
    var avatarImage = $('avatar');
    var appearance = data.appearance || {};
    if (avatarImage && appearance.avatar_src) {
      avatarImage.src = appearance.avatar_src;
      avatarImage.onerror = function () {
        avatarImage.onerror = null;
        avatarImage.src = 'assets/character_daily.png';
      };
    }
    var markerImage = document.querySelector('#character-marker img');
    if (markerImage && (appearance.avatar_src || appearance.src)) {
      markerImage.src = appearance.avatar_src || appearance.src;
      markerImage.onerror = function () {
        markerImage.onerror = null;
        markerImage.src = 'assets/character_daily.png';
      };
    }
    renderNeedPills(data.needs);
    var persona = data.persona || '未连接';
    $('persona').textContent = persona;
    $('marker-name').textContent = persona;
    var weather = data.weather || {};
    var weatherText = weather.condition
      ? ' · ' + weather.condition +
        (weather.temperature_low != null && weather.temperature_high != null
          ? ' ' + weather.temperature_low + '~' + weather.temperature_high + '°C'
          : '')
      : '';
    $('meta').textContent = data.plan_date
      ? data.plan_date + ' · ' + (data.theme || '未生成') + ' · ' + (data.mood || '未知') + weatherText
      : '等待模拟人生_世界数据';
    $('clock').textContent = clockText();
    if (now) {
      $('now-line').textContent = (now.activity || '暂无活动') + '  ·  ' + (now.location || '未知');
    } else {
      $('now-line').textContent = state.error ? '等待数据服务...' : '今日还没有日程';
    }
    var planBadge = $('plan-badge');
    if (data.plan_date && data.is_today === false) {
      planBadge.textContent = '显示 ' + data.plan_date + ' 的计划';
      planBadge.classList.remove('hidden');
    } else {
      planBadge.classList.add('hidden');
    }
    var kindPill = $('kind-pill');
    var kind = now ? now.kind : 'home';
    kindPill.className = 'pill ' + (kind === 'outside' ? 'blue' : kind === 'transit' ? 'amber' : 'green');
    kindPill.textContent = kind === 'outside' ? '外出中' : kind === 'transit' ? '在路上' : '在家';
    var avail = now ? now.availability : 'normal';
    var availPill = $('avail-pill');
    availPill.className = 'pill ' + pillClassForAvailability(avail);
    availPill.textContent = '可打扰度 · ' + (AVAIL_LABEL[avail] || avail);
    var userState = data.user_state || {};
    state.userSleeping = Boolean(userState.sleeping);
    var sleepPill = $('sleep-pill');
    if (sleepPill) {
      sleepPill.classList.toggle('hidden', !state.userSleeping);
      if (state.userSleeping) {
        sleepPill.textContent = '主人在睡' + (userState.place ? ' · ' + userState.place : '');
      }
    }
    var moneyPill = $('money-pill');
    if (moneyPill) {
      var wallet = data.money || {};
      var walletBalance = Number(wallet.balance);
      if (!isNaN(walletBalance)) {
        var walletText = Number.isInteger(walletBalance)
          ? String(walletBalance)
          : walletBalance.toFixed(2);
        moneyPill.textContent = '💰 ' + walletText + ' 元';
      } else {
        moneyPill.classList.add('hidden');
      }
    }
    var affectionPill = $('affection-pill');
    if (affectionPill) {
      var affection = data.affection || {};
      var score = Number(affection.score);
      if (!isNaN(score)) {
        affectionPill.textContent = '💗 ' + (affection.level || '') + ' ' + score;
        affectionPill.title = '好感度 ' + score + ' / 1000';
      } else {
        affectionPill.classList.add('hidden');
      }
    }
    if ($('interact-action') && state.selectedItem) {
      $('interact-action').textContent = interactLabelFor(state.selectedItem);
    }
    var cycle = $('persona-cycle');
    if (data.personas && data.personas.length > 1) {
      cycle.classList.remove('hidden');
    } else {
      cycle.classList.add('hidden');
    }
    renderCompactStatus(data);
  }

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

  // ---------------------------------------------------------------------------
  // 画面模式（性能模式）：自动 / 3D / 2D
  //
  // 3D 场景脚本不随页面一起加载。index.html 里把它们写成
  // <script type="text/x-lazy-3d" data-src="…" [data-group="world"]>，需要 3D 时才按顺序注入：
  // core 组（room-3d-models、room-3d-atmosphere、bedroom-3d，约 0.2 MB，外加约 0.7 MB 的
  // three.js）用于家里的房间；world 组（room-3d-outdoor、destination-3d，约 0.3 MB）
  // 只在去户外、车库、阳台 / 露台时才加载。
  //
  // “自动”在以下情况默认用 2D：浏览器不支持 WebGL、开启了省流量、内存 ≤ 4 GB、
  // CPU ≤ 4 核，或面板不是在本机 / 局域网打开（远程访问时加载 3D 资源很慢）。
  // 选择保存在 localStorage 的 vl-render 中。
  // ---------------------------------------------------------------------------
  var RENDER_MODES = ['auto', '3d', '2d'];
  var RENDER_MODE_LABEL = { auto: '自动', '3d': '3D', '2d': '2D' };
  var lazy3d = { promise: null, ready: false, failed: false, worldPromise: null, worldReady: false, worldFailed: false };

  function storedRenderMode() {
    try {
      var value = localStorage.getItem('vl-render');
      return RENDER_MODES.indexOf(value) >= 0 ? value : 'auto';
    } catch (error) {
      return 'auto';
    }
  }

  function webglAvailable() {
    try {
      var canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl2') || canvas.getContext('webgl')));
    } catch (error) {
      return false;
    }
  }

  function isLocalHost(hostname) {
    var host = String(hostname || '').toLowerCase().replace(/^\[|\]$/g, '');
    if (!host || host === 'localhost' || host === '::1' || /\.local$/.test(host)) return true;
    if (/^127\./.test(host) || /^10\./.test(host) || /^192\.168\./.test(host)) return true;
    if (/^172\.(1[6-9]|2\d|3[01])\./.test(host)) return true;
    if (/^169\.254\./.test(host) || /^f[cd][0-9a-f]{2}:/.test(host) || /^fe80:/.test(host)) return true;
    return false;
  }

  // 返回自动模式下选 2D 的原因；空字符串表示可以用 3D。
  function lowPerformanceReason() {
    var nav = window.navigator || {};
    if (!webglAvailable()) return '浏览器不支持 WebGL';
    if (nav.connection && nav.connection.saveData) return '已开启省流量';
    if (typeof nav.deviceMemory === 'number' && nav.deviceMemory > 0 && nav.deviceMemory <= 4) return '设备内存较小';
    if (typeof nav.hardwareConcurrency === 'number' && nav.hardwareConcurrency > 0 && nav.hardwareConcurrency <= 4) return 'CPU 核心较少';
    if (!isLocalHost(window.location && window.location.hostname)) return '远程访问';
    return '';
  }

  function renderMode() {
    if (!state.renderMode) state.renderMode = storedRenderMode();
    return state.renderMode;
  }

  // 当前是否应当显示 3D（不管脚本是否已经加载）。
  function want3D() {
    var mode = renderMode();
    if (mode === '2d') return false;
    if (mode === '3d') return true;
    if (state.autoRenderReason == null) state.autoRenderReason = lowPerformanceReason();
    return !state.autoRenderReason;
  }

  // 渲染时使用：想要 3D 且家里房间用的 3D 脚本已经就绪。未就绪时顺便开始加载，加载完会重新渲染。
  function use3D() {
    if (!want3D() || lazy3d.failed) return false;
    if (lazy3d.ready) return true;
    ensure3DScripts('core');
    return false;
  }

  // 户外目的地、车库、阳台 / 露台还需要 world 组（room-3d-outdoor、destination-3d）。
  function use3DWorld() {
    if (!use3D()) return false;
    if (lazy3d.worldReady) return true;
    if (!lazy3d.worldFailed) ensure3DScripts('world');
    return false;
  }

  function loadScriptInOrder(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = src;
      script.async = false;
      script.onload = function () { resolve(); };
      script.onerror = function () { reject(new Error('加载失败：' + src)); };
      document.body.appendChild(script);
    });
  }

  function lazyPlaceholders(group) {
    return Array.prototype.slice.call(document.querySelectorAll('script[type="text/x-lazy-3d"][data-src]')).filter(function (node) {
      return (node.getAttribute('data-group') || 'core') === group;
    });
  }

  function loadGroup(group) {
    return lazyPlaceholders(group).reduce(function (chain, node) {
      return chain.then(function () { return loadScriptInOrder(node.getAttribute('data-src')); });
    }, Promise.resolve());
  }

  // 按需分两组加载：core = 家里房间（模型、光照、3D 引擎），world = 户外与目的地。
  function ensure3DScripts(group) {
    applyQuality3D();
    if (!lazy3d.promise) {
      lazy3d.promise = loadGroup('core').then(function () {
        lazy3d.ready = !!window.Room3D;
        if (!lazy3d.ready) throw new Error('3D 模块未注册');
        wire3D();
        render();
      }).catch(function (error) {
        lazy3d.failed = true;
        console.warn('[VirtualLife UI] 3D 场景加载失败，改用 2D', error);
        showToast('3D 场景加载失败，已改用 2D');
        render();
      });
    }
    if (group !== 'world') return lazy3d.promise;
    if (!lazy3d.worldPromise) {
      lazy3d.worldPromise = lazy3d.promise.then(function () {
        if (!lazy3d.ready) return;
        return loadGroup('world').then(function () {
          lazy3d.worldReady = true;
          render();
        });
      }).catch(function (error) {
        lazy3d.worldFailed = true;
        console.warn('[VirtualLife UI] 户外 3D 场景加载失败，户外改用 2D', error);
        render();
      });
    }
    return lazy3d.worldPromise;
  }

  // 3D 画质：high / balanced / low，可用 localStorage 的 vl-3d-quality 手动指定。
  function quality3D() {
    try {
      var stored = localStorage.getItem('vl-3d-quality');
      if (stored === 'high' || stored === 'balanced' || stored === 'low') return stored;
    } catch (error) { /* 忽略本地存储异常 */ }
    var nav = window.navigator || {};
    var cores = typeof nav.hardwareConcurrency === 'number' ? nav.hardwareConcurrency : 0;
    var memory = typeof nav.deviceMemory === 'number' ? nav.deviceMemory : 0;
    if ((cores && cores <= 4) || (memory && memory <= 4)) return 'low';
    if (cores >= 8 && (!memory || memory >= 8)) return 'high';
    return 'balanced';
  }

  function applyQuality3D() {
    if (!window.__VL_3D_QUALITY) window.__VL_3D_QUALITY = quality3D();
  }

  function renderModeLabel() {
    var mode = renderMode();
    if (mode !== 'auto') return '画面：' + RENDER_MODE_LABEL[mode];
    return '画面：自动（' + (want3D() ? '3D' : '2D') + '）';
  }

  function applyRenderMode() {
    var button = $('render-toggle');
    if (!button) return;
    button.textContent = renderModeLabel();
    var reason = renderMode() === 'auto' && !want3D() ? state.autoRenderReason : '';
    button.title = reason ? '自动选择了 2D：' + reason + '。点击切换' : '点击在 自动 / 3D / 2D 之间切换';
  }

  function cycleRenderMode() {
    var next = RENDER_MODES[(RENDER_MODES.indexOf(renderMode()) + 1) % RENDER_MODES.length];
    state.renderMode = next;
    try { localStorage.setItem('vl-render', next); } catch (error) { /* 忽略本地存储异常 */ }
    applyRenderMode();
    if (want3D()) ensure3DScripts('core');
    showToast(renderModeLabel() + (next === '2d' ? '，更省电、加载更快' : ''));
    render();
  }

  function roomScene(room, now) {
    if ((/阳台|露台/.test(room) ? use3DWorld() : use3D()) && window.Bedroom3D && Bedroom3D.supports && Bedroom3D.supports(room) && !state.placement) return Bedroom3D.markup(now, state.homeItems, sceneEnvironment(), (state.data || {}).appearance, room);
    if (window.SceneStudio) return SceneStudio.room(room, now, state.homeItems, sceneEnvironment(), (state.data || {}).appearance);
    var roomClass = ROOM_CLASS[room] || 'living';
    var key = activityKey(now && now.activity);
    var activity = escapeHtml((now && now.activity) || '自由时间');
    var label = escapeHtml(room || '家');
    var effects = effectsMarkup(key, 72, 58);
    var body = '';
    if (roomClass === 'bedroom') {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="room-window win-a"><i></i><i></i></div>',
        '<div class="room-art"></div>',
        '<div class="furn wardrobe"><i class="handle"></i></div>',
        '<div class="furn bed"><i class="pillow p1"></i><i class="pillow p2"></i><i class="blanket"></i></div>',
        '<div class="furn nightstand"><i class="lamp"></i></div>',
        '<div class="furn plant small"></div>',
        '<div class="room-rug"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'bathroom') {
      body = [
        '<div class="room-back-wall tiled"></div>',
        '<div class="room-floor tiled"></div>',
        '<div class="room-window win-b"><i></i><i></i></div>',
        '<div class="furn mirror"></div>',
        '<div class="furn sink"><i></i></div>',
        '<div class="furn toilet"></div>',
        '<div class="furn towel"></div>',
        '<div class="furn tub"><i class="water"></i><i class="faucet"></i></div>',
        '<div class="bath-avatar"><img src="' + characterArtSrc() + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt=""></div>',
        '<div class="room-rug bath-mat"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        '<div class="steam-cloud"><i></i><i></i><i></i></div>'
      ].join('');
    } else if (roomClass === 'study') {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="room-window win-c"><i></i><i></i></div>',
        '<div class="room-art corkboard"></div>',
        '<div class="furn bookshelf"><i></i><i></i><i></i><i></i></div>',
        '<div class="furn desk"><i class="monitor"></i><i class="keyboard"></i><i class="mug"></i></div>',
        '<div class="furn chair"></div>',
        '<div class="furn plant small"></div>',
        '<div class="room-rug"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'kitchen') {
      body = [
        '<div class="room-back-wall tiled"></div>',
        '<div class="room-floor tiled"></div>',
        '<div class="room-window win-d"><i></i><i></i></div>',
        '<div class="furn upper-cabinets"></div>',
        '<div class="furn counter"><i class="sink"></i><i class="stove"></i><i class="pot"></i></div>',
        '<div class="furn fridge"><i class="handle"></i></div>',
        '<div class="furn dining-table"><i class="plate p1"></i><i class="plate p2"></i><i class="cup"></i></div>',
        '<div class="room-rug"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'balcony') {
      body = [
        '<div class="room-back-wall balcony-sky"></div>',
        '<div class="room-floor balcony-deck"></div>',
        '<div class="room-window win-e"><i></i><i></i></div>',
        '<div class="furn railing"></div>',
        '<div class="furn balcony-plant p1"></div>',
        '<div class="furn balcony-plant p2"></div>',
        '<div class="furn balcony-plant p3"></div>',
        '<div class="furn balcony-chair"></div>',
        '<div class="furn balcony-table"><i></i></div>',
        '<div class="string-lights"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else if (roomClass === 'hall') {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="furn shoe-cabinet"><i></i></div>',
        '<div class="furn coat-rack"><i></i><i></i><i></i></div>',
        '<div class="furn hall-mirror"></div>',
        '<div class="room-rug hall-runner"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    } else {
      body = [
        '<div class="room-back-wall"></div>',
        '<div class="room-floor"></div>',
        '<div class="room-window win-a"><i></i><i></i></div>',
        '<div class="furn sofa"></div>',
        '<div class="furn coffee-table"><i></i></div>',
        '<div class="furn tv"><i></i></div>',
        '<div class="furn record"></div>',
        '<div class="furn plant"></div>',
        '<div class="room-rug"></div>',
        '<div class="room-art"></div>',
        '<div class="room-label">' + label + '<small>在家 · ' + activity + '</small></div>',
        effects,
        standeeMarkup()
      ].join('');
    }
    return '<div class="room-scene room-' + roomClass + '">' + body + activityProps(key) + '</div>';
  }

  function sceneBuildings() {
    return [
      '<div class="building b1"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="building b2"><i></i><i></i><i></i><i></i></div>',
      '<div class="building b3"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="building b4"><i></i><i></i><i></i><i></i></div>',
      '<div class="building b5"><i></i><i></i><i></i></div>',
      '<div class="antenna a1"></div><div class="antenna a2"></div>'
    ].join('');
  }

  function sceneTrees() {
    return [
      '<div class="tree t1"><span class="trunk"></span><span class="crown c1"></span><span class="crown c2"></span><span class="crown c3"></span></div>',
      '<div class="tree t2"><span class="trunk"></span><span class="crown c1"></span><span class="crown c2"></span><span class="crown c3"></span></div>',
      '<div class="tree t3"><span class="trunk"></span><span class="crown c1"></span><span class="crown c2"></span><span class="crown c3"></span></div>'
    ].join('');
  }

  function sceneAmbient() {
    return [
      '<div class="sky-birds"><i></i><i></i><i></i><i></i></div>',
      '<div class="ambient-motes"><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="foreground-bushes"><i class="fb1"></i><i class="fb2"></i><i class="fb3"></i></div>'
    ].join('');
  }

  function sceneProps(key, now) {
    if (key === 'nightmarket') {
      return [
        '<div class="nm-stall s1"><span class="awning"></span><i class="counter"></i><i class="lamp"></i></div>',
        '<div class="nm-stall s2"><span class="awning"></span><i class="counter"></i><i class="lamp"></i></div>',
        '<div class="nm-stall s3"><span class="awning"></span><i class="counter"></i><i class="lamp"></i></div>',
        '<div class="nm-string"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="nm-lanterns"><i></i><i></i><i></i></div>',
        '<div class="nm-steam"><i></i><i></i><i></i></div>',
        '<div class="nm-sign">夜市</div>',
        '<div class="nm-stools"><i></i><i></i><i></i></div>',
        '<div class="nm-crates"><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'station') {
      return [
        '<div class="station-roof"><i></i><i></i><i></i><i></i></div>',
        '<div class="station-train"><span class="nose"></span><i></i><i></i><i></i><i class="door"></i></div>',
        '<div class="station-rail"><i></i><i></i><i></i></div>',
        '<div class="station-platform"></div>',
        '<div class="station-line"></div>',
        '<div class="station-board"><span>12:40 · 京都</span><i></i></div>',
        '<div class="station-clock"><i></i></div>',
        '<div class="station-pillar p1"></div><div class="station-pillar p2"></div>',
        '<div class="station-bench"><i></i></div>',
        '<div class="station-luggage"><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'airport') {
      return [
        '<div class="airport-terminal"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="airport-tower"><span class="mast"></span><i class="light"></i></div>',
        '<div class="airport-runway"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="airport-plane"><span class="body"></span><span class="wing"></span><span class="tail"></span><i></i><i></i><i></i></div>',
        '<div class="airport-board"><span>DEPARTURES</span><i></i><i></i><i></i></div>',
        '<div class="airport-luggage"><i></i><i></i></div>',
        '<div class="airport-cart"><span></span><i></i></div>',
        '<div class="airport-windsock"><span></span></div>',
        '<div class="airport-lights"><i></i><i></i><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'hotel') {
      return [
        '<div class="hotel-building"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="hotel-sign">HOTEL</div>',
        '<div class="hotel-canopy"></div>',
        '<div class="hotel-door"><i></i><i></i></div>',
        '<div class="hotel-lamp l1"></div><div class="hotel-lamp l2"></div>',
        '<div class="hotel-planter p1"><i></i><i></i><i></i></div>',
        '<div class="hotel-cart"><span></span><i></i><i></i></div>',
        '<div class="hotel-flag"><span></span></div>',
        '<div class="hotel-steps"></div>'
      ].join('');
    }
    if (key === 'travel') {
      var cityName = (now && now.city) ? String(now.city) : 'CITY';
      return [
        '<div class="travel-row"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="travel-roofs"><i></i><i></i><i></i></div>',
        '<div class="travel-bunting"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="travel-lanterns"><i></i><i></i><i></i></div>',
        '<div class="travel-sign">' + escapeHtml(cityName) + '</div>',
        '<div class="travel-cobble"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="travel-lamp l1"></div><div class="travel-lamp l2"></div>',
        '<div class="travel-cafe"><span class="table"></span><i></i><i></i></div>',
        '<div class="travel-fountain"><i></i></div>',
        '<div class="travel-pigeons"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'temple') {
      return [
        '<div class="temple-torii"><i class="beam"></i><i class="tie"></i><i class="post p1"></i><i class="post p2"></i></div>',
        '<div class="temple-hall"><span class="roof"></span><i class="pillar p1"></i><i class="pillar p2"></i><i class="door"></i></div>',
        '<div class="temple-lantern l1"><i></i></div><div class="temple-lantern l2"><i></i></div>',
        '<div class="temple-incense"><i></i><i></i><i></i></div>',
        '<div class="temple-emas"><i></i><i></i><i></i><i></i></div>',
        '<div class="temple-petals"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="temple-path"></div>',
        '<div class="temple-bell"><span></span></div>'
      ].join('');
    }
    if (key === 'onsen') {
      return [
        '<div class="onsen-fence"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="onsen-pool"><span class="ripple r1"></span><span class="ripple r2"></span></div>',
        '<div class="onsen-rocks"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="onsen-steam"><i></i><i></i><i></i><i></i></div>',
        '<div class="onsen-lantern"><i></i></div>',
        '<div class="onsen-bucket"><span></span></div>',
        '<div class="onsen-towel"></div>',
        '<div class="onsen-pine"></div>'
      ].join('');
    }
    if (key === 'harbor') {
      return [
        '<div class="harbor-sea"><i class="harbor-wave w1"></i><i class="harbor-wave w2"></i></div>',
        '<div class="harbor-houses"><i></i><i></i><i></i><i></i></div>',
        '<div class="harbor-pier"></div>',
        '<div class="harbor-boat"><span class="hull"></span><span class="cabin"></span><span class="mast"></span><i></i></div>',
        '<div class="harbor-crates"><i></i><i></i></div>',
        '<div class="harbor-net"></div>',
        '<div class="harbor-gulls"><i></i><i></i><i></i></div>',
        '<div class="harbor-lighthouse"><i></i></div>'
      ].join('');
    }
    if (key === 'mountain') {
      return [
        '<div class="mountain-ridge r1"></div><div class="mountain-ridge r2"></div><div class="mountain-ridge r3"></div>',
        '<div class="mountain-mist m1"></div><div class="mountain-mist m2"></div>',
        '<div class="mountain-pines"><i></i><i></i><i></i></div>',
        '<div class="mountain-deck"><span class="rail"></span><i></i><i></i></div>',
        '<div class="mountain-scope"><span></span><i></i></div>',
        '<div class="mountain-cable"><span class="car"></span></div>',
        '<div class="mountain-birds"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'izakaya') {
      return [
        '<div class="izakaya-front"><span class="roof"></span><span class="noren"></span><i class="door"></i></div>',
        '<div class="izakaya-sign"><i></i><i></i><i></i></div>',
        '<div class="izakaya-lanterns"><i></i><i></i><i></i></div>',
        '<div class="izakaya-crates"><i></i><i></i><i></i></div>',
        '<div class="izakaya-stools"><i></i><i></i></div>',
        '<div class="izakaya-smoke"><i></i><i></i></div>',
        '<div class="izakaya-lamp"></div>'
      ].join('');
    }
    if (key === 'cafe') {
      return [
        '<div class="cafe-building"></div>',
        '<div class="cafe-awning"></div>',
        '<div class="cafe-sign">CAFE</div>',
        '<div class="cafe-window"><i></i><i></i></div>',
        '<div class="cafe-pastry"><i></i><i></i><i></i></div>',
        '<div class="cafe-table"><i class="cup"></i></div>',
        '<div class="cafe-chair"></div>',
        '<div class="street-lamp"><i></i></div>',
        '<div class="cafe-menu"><i></i><i></i><i></i></div>',
        '<div class="cafe-table t2"><i class="cup"></i></div>',
        '<div class="cafe-chair c2"></div>',
        '<div class="cafe-lights"><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="cafe-planter"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'park') {
      return [
        '<div class="park-pond"></div>',
        '<div class="park-bench"><i></i><i></i></div>',
        '<div class="park-duck d1"></div>',
        '<div class="park-duck d2"></div>',
        '<div class="park-leaves"><i></i><i></i><i></i><i></i></div>',
        '<div class="park-flowers"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="park-lamp l1"></div><div class="park-lamp l2"></div>',
        '<div class="park-lily l1"></div><div class="park-lily l2"></div><div class="park-lily l3"></div>',
        '<div class="park-reeds"><i></i><i></i><i></i><i></i></div>',
        '<div class="park-fountain"></div>',
        '<div class="park-bench b2"><i></i><i></i></div>',
        '<div class="park-butterflies"><i></i><i></i></div>',
        '<div class="park-kite"><i></i></div>'
      ].join('');
    }
    if (key === 'bookstore') {
      return [
        '<div class="shop bookstore"><div class="shop-window"><i></i><i></i><i></i><i></i></div><div class="shop-awning"></div></div>',
        '<div class="floating-pages"><i></i><i></i><i></i></div>',
        '<div class="bookcart"><i></i><i></i><i></i></div>',
        '<div class="book-open-sign">OPEN</div>',
        '<div class="book-plant"><i></i><i></i><i></i></div>',
        '<div class="book-bench"><i></i><i></i></div>',
        '<div class="book-ladder"></div>',
        '<div class="book-stack"><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'museum') {
      return [
        '<div class="museum-building"></div>',
        '<div class="museum-column c1"></div><div class="museum-column c2"></div><div class="museum-column c3"></div>',
        '<div class="museum-frame f1"></div><div class="museum-frame f2"></div>',
        '<div class="museum-spot"></div>',
        '<div class="museum-statue"><i></i></div>',
        '<div class="museum-pedestal"></div>',
        '<div class="museum-banner">ART</div>',
        '<div class="museum-rope r1"></div><div class="museum-rope r2"></div>',
        '<div class="museum-bench"><i></i><i></i></div>',
        '<div class="museum-steps"></div>',
        '<div class="museum-flags"><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'cinema') {
      return [
        '<div class="cinema-building"></div>',
        '<div class="cinema-marquee">NOW SHOWING</div>',
        '<div class="cinema-screen"></div>',
        '<div class="cinema-seats"><i></i><i></i><i></i></div>',
        '<div class="popcorn"></div>',
        '<div class="cinema-poster p1"></div><div class="cinema-poster p2"></div>',
        '<div class="cinema-ticket"><i></i></div>',
        '<div class="cinema-carpet"></div>',
        '<div class="cinema-rope r1"></div><div class="cinema-rope r2"></div>',
        '<div class="cinema-bulbs"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="cinema-stars"><i></i><i></i><i></i></div>',
        '<div class="cinema-reel"></div>'
      ].join('');
    }
    if (key === 'beach') {
      return [
        '<div class="sea"></div>',
        '<div class="wave w1"></div><div class="wave w2"></div>',
        '<div class="palm"><i></i><span></span></div>',
        '<div class="birds"><i></i><i></i><i></i></div>',
        '<div class="beach-umbrella"></div>',
        '<div class="beach-towel"></div>',
        '<div class="beach-star s1"></div><div class="beach-star s2"></div>',
        '<div class="beach-shell sh1"></div><div class="beach-shell sh2"></div>',
        '<div class="beach-driftwood"></div>',
        '<div class="beach-lighthouse"><i></i></div>',
        '<div class="beach-umbrella u2"></div>',
        '<div class="beach-sailboat"><i></i></div>',
        '<div class="beach-lifebuoy"></div>'
      ].join('');
    }
    if (key === 'mall') {
      return [
        '<div class="mall-building"><i></i><i></i><i></i><i></i></div>',
        '<div class="neon-sign n1">SALE</div>',
        '<div class="neon-sign n2">MALL</div>',
        '<div class="shopping-bags"><i></i><i></i></div>',
        '<div class="mall-mannequin m1"><i></i></div><div class="mall-mannequin m2"><i></i></div>',
        '<div class="mall-planter p1"><i></i><i></i></div>',
        '<div class="mall-planter p2"><i></i><i></i></div>',
        '<div class="mall-banner">NEW</div>',
        '<div class="mall-bench"><i></i><i></i></div>',
        '<div class="sky-balloons"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'office') {
      return [
        '<div class="office-building"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="office-desk"></div>',
        '<div class="office-monitor"></div>',
        '<div class="office-cup"></div>',
        '<div class="office-plant"></div>',
        '<div class="office-desk d2"></div>',
        '<div class="office-monitor m2"></div>',
        '<div class="office-chair"></div>',
        '<div class="office-whiteboard"><i></i></div>',
        '<div class="office-cooler"></div>',
        '<div class="office-cabinet"></div>',
        '<div class="office-clock"><i></i></div>'
      ].join('');
    }
    if (key === 'street') {
      return [
        '<div class="street-shop s1"><i></i><i></i></div>',
        '<div class="street-shop s2"><i></i><i></i></div>',
        '<div class="lantern l1"></div><div class="lantern l2"></div><div class="lantern l3"></div>',
        '<div class="bike"><i></i><i></i></div>',
        '<div class="street-shop s3"><i></i><i></i></div>',
        '<div class="street-awning"></div>',
        '<div class="street-sign">茶</div>',
        '<div class="street-planter p1"><i></i><i></i></div>',
        '<div class="street-planter p2"><i></i><i></i></div>',
        '<div class="street-bench"><i></i><i></i></div>',
        '<div class="lantern l4"></div><div class="lantern l5"></div>',
        '<div class="street-banners"><i></i><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'food') {
      return [
        '<div class="food-stall"></div>',
        '<div class="food-awning"></div>',
        '<div class="food-steam"><i></i><i></i><i></i></div>',
        '<div class="food-bowl"></div>',
        '<div class="food-stool"></div>',
        '<div class="food-crate c1"><i></i><i></i><i></i></div>',
        '<div class="food-crate c2"><i></i><i></i></div>',
        '<div class="food-menu">MENU</div>',
        '<div class="food-lantern l1"></div><div class="food-lantern l2"></div>',
        '<div class="food-stool s2"></div>',
        '<div class="food-bench"><i></i><i></i></div>',
        '<div class="food-skewers"><i></i><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'supermarket') {
      return [
        '<div class="supermarket-building"><i></i><i></i><i></i><i></i></div>',
        '<div class="supermarket-sign">FRESH</div>',
        '<div class="supermarket-door"><i></i><i></i></div>',
        '<div class="supermarket-shelf"><i></i><i></i><i></i><i></i><i></i><i></i></div>',
        '<div class="supermarket-cart"><i></i><i></i></div>',
        '<div class="supermarket-produce"><i></i><i></i><i></i></div>',
        '<div class="supermarket-checkout"></div>',
        '<div class="supermarket-bags"><i></i><i></i></div>'
      ].join('');
    }
    if (key === 'grocery') {
      return [
        '<div class="grocery-building"></div>',
        '<div class="grocery-awning"></div>',
        '<div class="grocery-sign">杂货</div>',
        '<div class="grocery-window"><i></i><i></i></div>',
        '<div class="grocery-jars"><i></i><i></i><i></i></div>',
        '<div class="grocery-sacks"><i></i><i></i></div>',
        '<div class="grocery-counter"></div>',
        '<div class="grocery-lantern"></div>'
      ].join('');
    }
    if (key === 'market') {
      return [
        '<div class="market-awning"></div>',
        '<div class="market-stall s1"><i></i><i></i></div>',
        '<div class="market-stall s2"><i></i><i></i></div>',
        '<div class="market-produce"><i></i><i></i><i></i><i></i></div>',
        '<div class="market-fish"><i></i></div>',
        '<div class="market-basket"><i></i></div>',
        '<div class="market-lantern l1"></div><div class="market-lantern l2"></div>'
      ].join('');
    }
    if (key === 'transit') {
      return [
        '<div class="road"></div>',
        '<div class="sidewalk"></div>',
        '<div class="road-line"></div>',
        '<div class="transit-crosswalk"></div>',
        '<div class="bus"><i></i><i></i><i></i></div>',
        '<div class="car c1"><i></i></div>',
        '<div class="car c2"><i></i></div>',
        '<div class="bus-stop"></div>',
        '<div class="transit-shelter"><i></i></div>',
        '<div class="transit-light"><i></i><i></i><i></i></div>',
        '<div class="transit-sign">BUS</div>',
        '<div class="transit-lamp l1"></div><div class="transit-lamp l2"></div>'
      ].join('');
    }
    return [
      '<div class="generic-shop"><i></i><i></i></div>',
      '<div class="generic-tree"></div>',
      '<div class="generic-bench"><i></i><i></i></div>',
      '<div class="generic-lamp"></div>',
      '<div class="generic-planter"><i></i><i></i><i></i></div>',
      '<div class="generic-sign">CITY</div>',
      '<div class="generic-bush b1"></div><div class="generic-bush b2"></div>',
      '<div class="sky-balloons"><i></i><i></i></div>'
    ].join('');
  }

  function outdoorScene(key, now, preview) {
    var label = sceneLabel(key);
    var city = (now && now.city) || '';
    if (key === 'travel' && city) label = city + ' · 街景';
    var travelKeys = { airport: 1, station: 1, hotel: 1, travel: 1 };
    var activity = (now && now.activity) || '';
    var effectKey = key === 'cafe' || key === 'food' || key === 'nightmarket' ? 'food' : activityKey(activity);
    var walking = key === 'transit' || hasAny(activity, [
      '走路', '步行', '散步', '回家', '前往', '赶路', '走去', '通勤', '出发', '出门'
    ]);
    var journeyMode = key === 'transit' ? SceneStudio.travelMode(preview ? null : now) : '';
    if (journeyMode) walking = journeyMode === 'walk' || journeyMode === 'cycle';
    var characterClass = 'scene-character' + (walking ? ' walking' : '');
    var wrapClass = 'scene-character-wrap' + (walking ? ' walking' : '');
    var statusText = preview ? '预览' : journeyMode ? ({walk:'步行中',cycle:'骑行中',bus:'乘公交中',car:'乘车中',rail:'乘列车中'}[journeyMode]) : walking ? '走路中' : travelKeys[key] ? '旅行中' : '外出中';
    var extra = key === 'beach' ? 'beach-sun' : '';
    var environment = sceneEnvironment();
    var band = environment.band;
    var html2d = [
      '<div class="scene studio-outdoor scene-' + key + ' scene-' + band + SceneStudio.classes(environment) + (journeyMode ? ' journey journey-' + journeyMode : '') + '" style="--sky-top:' + environment.sky[0] + ';--sky-bottom:' + environment.sky[1] + '">',
      '<div class="scene-sky"></div>',
      '<div class="scene-sun ' + extra + '"></div>',
      '<div class="scene-cloud c1"></div><div class="scene-cloud c2"></div><div class="scene-cloud c3"></div>' +
        '<div class="scene-cloud c4"></div><div class="scene-cloud c5"></div>',
      '<div class="scene-ground"></div>',
      '<div class="scene-buildings">' + sceneBuildings() + '</div>',
      '<div class="scene-trees">' + sceneTrees() + '</div>',
      '<div class="scene-path"></div>',
      '<div class="scene-props">' + sceneProps(key, now) + '</div>',
      (journeyMode ? SceneStudio.journeyDecor(environment, journeyMode) : SceneStudio.outdoorDecor(key, environment)),
      '<div class="scene-timewash"></div>',
      SceneStudio.precipitation(environment, false),
      SceneStudio.badge(environment),
      (/rain|storm/.test(environment.weather) ? '<div class="scene-weather-reflection"></div>' : ''),
      '<div class="scene-stars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
      '<div class="scene-ambient">' + sceneAmbient() + '</div>',
      '<div class="' + wrapClass + '">',
      (walking ? '<div class="walk-dust"><i></i><i></i><i></i></div>' : ''),
      '<div class="' + characterClass + '"><img src="' + characterArtSrc() + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt="白紫固定立绘"></div>',
      '<div class="scene-effects">' + effectsMarkup(effectKey, 66, 58) + '</div>',
      '</div>',
      '<div class="scene-label"><span class="scene-label-icon">' + sceneIconSvg(key) +
        '</span>' + escapeHtml(label) + '<small>' + statusText + '</small>' +
        (sceneInteriorName(key) ? '<button type="button" class="scene-mode-toggle" data-scene-mode="indoor">室内</button>' : '') +
        '</div>',
      '</div>'
    ].join('');
    return destination3d(key, 'outdoor', label, statusText, environment, html2d, sceneInteriorName(key) ? 'indoor' : '', journeyMode);
  }

  // 3D outing scenes (assets/destination-3d.js); the 2D art above stays as the fallback.
  function destination3d(key, view, label, status, environment, html2d, toggleTo, mode) {
    if (!use3DWorld() || !window.Room3D || !Room3D.destinationMarkup || !Room3D.supportsDestination(key, view)) return html2d;
    var toggle = toggleTo ? '<button type="button" class="scene-mode-toggle" data-scene-mode="' + toggleTo + '">' + (toggleTo === 'indoor' ? '室内' : '室外') + '</button>' : '';
    var labelHtml = '<div class="scene-label"><span class="scene-label-icon">' + sceneIconSvg(key) + '</span>' + escapeHtml(label) + '<small>' + escapeHtml(status) + '</small>' + toggle + '</div>';
    var appearance = (state.data && state.data.appearance) || {};
    var look = {
      src: characterArtSrc(),
      key: appearance.key || 'daily',
      name: appearance.name || ''
    };
    return Room3D.destinationMarkup({ key: key, view: view, mode: mode || '', env: environment, labelHtml: labelHtml, fallback: html2d, look: look });
  }

  function indoorScene(key, now, preview) {
    var label = sceneLabel(key);
    var city = (now && now.city) || '';
    if (key === 'travel' && city) label = city + ' · 室内';
    var interior = sceneInteriorName(key);
    if (!interior || !window.GarageDestinations) {
      return outdoorScene(key, now, preview);
    }
    var environment = sceneEnvironment();
    var activity = (now && now.activity) || '';
    var effectKey = key === 'cafe' || key === 'food' || key === 'nightmarket' ? 'food' : activityKey(activity);
    var html2d = [
      '<div class="scene studio-indoor scene-' + key + ' ' + SceneStudio.classes(environment) + '">',
      '<div class="scene-indoor-art">' + GarageDestinations.interior(interior, environment) + '</div>',
      '<div class="scene-indoor-wash"></div>',
      SceneStudio.badge(environment),
      '<div class="scene-character-wrap">',
      '<div class="scene-character"><img src="' + characterArtSrc() + '" onerror="this.onerror=null;this.src=\'assets/character_daily.png\'" alt="白紫固定立绘"></div>',
      '<div class="scene-effects">' + effectsMarkup(effectKey, 66, 58) + '</div>',
      '</div>',
      '<div class="scene-label"><span class="scene-label-icon">' + sceneIconSvg(key) +
        '</span>' + escapeHtml(label) + '<small>' +
        (preview ? '预览 · 室内' : '室内') + '</small>' +
        '<button type="button" class="scene-mode-toggle" data-scene-mode="outdoor">室外</button>' +
        '</div>',
      '</div>'
    ].join('');
    return destination3d(key, 'indoor', label, preview ? '预览 · 室内' : '室内', environment, html2d, 'outdoor');
  }

  function flashSceneMode(text) {
    var stage = $('scene-stage');
    if (!stage) return;
    var previous = stage.querySelector('.scene-mode-flash');
    if (previous) previous.remove();
    var node = document.createElement('div');
    node.className = 'scene-mode-flash';
    node.textContent = text;
    stage.appendChild(node);
    window.setTimeout(function () {
      if (node.parentNode) node.remove();
    }, 900);
  }

  function renderScene(force) {
    var data = state.data || {};
    var signature = sceneSignature(data);
    if (!force && signature === renderState.scene) return;
    renderState.scene = signature;
    var now = data.now || null;
    var stage = $('scene-stage');
    var picker = $('scene-picker');
    var previewBadge = $('preview-badge');
    if (!now) {
      stage.innerHTML = '<div class="empty-scene"><span>今天还没有当前活动</span><small>先在模拟人生_世界插件里生成日程</small></div>';
      picker.classList.add('hidden');
      previewBadge.classList.add('hidden');
      $('activity').textContent = '自由时间';
      $('location').textContent = data.plans_path || '未连接';
      $('state-pill').className = 'pill';
      $('state-pill').textContent = '状态 · --';
      $('avail-pill2').className = 'pill';
      $('avail-pill2').textContent = '可打扰 · --';
      $('next-line').textContent = '';
      return;
    }
    var kind = now.kind;
    var actualScene = sceneFor(now);
    var previewScene = state.previewScene && (kind === 'home' || state.previewScene !== actualScene) ? state.previewScene : null;
    var sceneKey = previewScene || actualScene;
    var placement = kind === 'home' ? state.placement : null;
    var previewRoom = kind === 'home' ? state.previewRoom : null;
    var previewReturn = $('preview-return');
    if (placement) {
      stage.innerHTML = roomScene(placement.room, now);
      stage.classList.add('placement-mode');
      picker.classList.add('hidden');
      previewBadge.classList.remove('hidden');
      previewBadge.textContent = '摆放 · 点击地面选择位置';
      if (previewReturn) {
        previewReturn.classList.remove('hidden');
        previewReturn.textContent = '取消摆放';
      }
    } else if (previewRoom) {
      stage.innerHTML = roomScene(previewRoom, now);
      stage.classList.remove('placement-mode');
      picker.classList.add('hidden');
      previewBadge.classList.remove('hidden');
      previewBadge.textContent = '查看 · ' + previewRoom;
      if (previewReturn) {
        previewReturn.classList.remove('hidden');
        previewReturn.textContent = '回到当前';
      }
    } else {
      stage.classList.remove('placement-mode');
      if (previewReturn) previewReturn.textContent = '回到当前';
      if (kind === 'home' && !previewScene) {
        stage.innerHTML = roomScene(roomFor(now) || '客厅', now);
        picker.classList.remove('hidden');
        previewBadge.classList.add('hidden');
      } else {
        stage.innerHTML = state.indoorView && sceneInteriorName(sceneKey)
          ? indoorScene(sceneKey, now, Boolean(previewScene))
          : outdoorScene(sceneKey, now, Boolean(previewScene));
        picker.classList.remove('hidden');
        if (previewScene) {
          previewBadge.classList.remove('hidden');
          previewBadge.textContent = '预览 · ' + sceneLabel(sceneKey) +
            (state.indoorView && sceneInteriorName(sceneKey) ? ' · 室内' : '');
          if (previewReturn) previewReturn.classList.remove('hidden');
        } else {
          previewBadge.classList.add('hidden');
          if (previewReturn) previewReturn.classList.add('hidden');
        }
      }
    }
    $('activity').textContent = now.activity || '暂无活动';
    $('location').textContent = now.location || '未知';
    var statePill = $('state-pill');
    statePill.className = 'pill';
    statePill.textContent = '状态 · ' + (STATE_LABEL[now.state] || now.state || '--');
    var availPill = $('avail-pill2');
    availPill.className = 'pill ' + pillClassForAvailability(now.availability);
    availPill.textContent = '可打扰 · ' + (AVAIL_LABEL[now.availability] || now.availability || '--');
    var dot = $('now-dot');
    dot.style.background = kind === 'outside' ? 'var(--blue)' : kind === 'transit' ? 'var(--amber)' : 'var(--green)';
    dot.style.boxShadow = '0 0 12px ' + (kind === 'outside' ? 'rgba(125,200,255,.7)' : kind === 'transit' ? 'rgba(240,184,110,.7)' : 'rgba(125,219,166,.7)');
    var next = data.next && data.next[0];
    $('next-line').innerHTML = next
      ? '<b>下一站</b> ' + escapeHtml(next.start + '–' + next.end) + ' · ' +
        escapeHtml(next.activity) + ' <span style="color:var(--blue)">' + escapeHtml(next.location) + '</span>'
      : '<b>下一站</b> 今天没有后续安排了';
  }

  function nextWaitText(startText) {
    var now = timeToMinutes(clockText());
    var start = timeToMinutes(startText);
    if (!start) return '';
    var diff = start - now;
    if (diff <= 0) return '现在';
    if (diff < 60) return diff + ' 分钟后';
    var hours = Math.floor(diff / 60);
    var minutes = diff % 60;
    return hours + ' 小时' + (minutes ? ' ' + minutes + ' 分' : '') + '后';
  }

  function renderNext() {
    var data = state.data || {};
    var signature = JSON.stringify([
      data.persona, data.next || [], data.outfit || {},
      data.appearance || {}, clockText().slice(0, 5)
    ]);
    if (signature === renderState.next) return;
    renderState.next = signature;
    var list = $('next-list');
    var next = data.next || [];
    if (!next.length) {
      list.innerHTML = '<div class="empty-next">今天没有后续安排了</div>';
    } else {
      list.innerHTML = next.map(function (item, index) {
        return '<div class="next-item' + (index === 0 ? ' primary' : '') +
          '" data-next-index="' + index + '" title="' + escapeHtml((item.start || '') + '–' + (item.end || '') +
            ' · ' + (item.activity || '') + ' · ' + (item.location || '')) + '">' +
          '<span class="dot ' + categoryClass(item) + '"></span>' +
          '<div><div class="time">' + escapeHtml(item.start + '–' + item.end) +
          '<span class="next-countdown">' + escapeHtml(nextWaitText(item.start)) +
          '</span></div>' +
          '<div class="activity">' + escapeHtml(item.activity) + '</div></div>' +
          '<div class="place">' + escapeHtml(item.location) + '</div>' +
          '</div>';
      }).join('');
    }
    var outfit = data.outfit || {};
    var text = outfit.style && outfit.summary
      ? outfit.style + ' · ' + outfit.summary
      : (outfit.summary || outfit.style || '还没有穿搭记录');
    var appearance = data.appearance || {};
    if (appearance.is_sleepwear) {
      $('outfit-text').textContent = appearance.name || '睡衣';
    } else if (appearance.key === 'daily_outfit' || String(appearance.key || '').indexOf('daily_outfit') === 0) {
      $('outfit-text').textContent = text || '按今日穿搭';
    } else {
      $('outfit-text').textContent = appearance.name
        ? appearance.name + ' · 日常与外出服装'
        : text;
    }
  }

  function timeToMinutes(text) {
    var parts = String(text || '').split(':');
    if (parts.length < 2) return 0;
    return Number(parts[0]) * 60 + Number(parts[1]);
  }

  function activityStateLabel(state) {
    var text = String(state || '').trim().toLowerCase();
    var labels = {
      sleep: '睡眠', sleeping: '睡眠', rest: '休息', resting: '休息',
      busy: '忙碌', available: '空闲', free: '空闲',
      work: '工作', working: '工作', at_work: '工作',
      commute: '路上', transit: '路上', travelling: '路上',
      dining: '用餐', eating: '用餐', meal: '用餐',
      shopping: '购物', reading: '阅读', cooking: '做饭',
      bath: '洗漱', bathing: '泡澡', exercise: '运动',
      study: '学习', studying: '学习', leisure: '休闲'
    };
    return labels[text] || String(state || '') || '--';
  }

  function scheduleSceneAvailable(item) {
    return Boolean(
      item && item.scene &&
      item.kind !== 'home' && item.kind !== 'sleep'
    );
  }

  function openScheduleDetail(item) {
    if (!item) return;
    state.scheduleItem = item;
    var body = $('schedule-body');
    if (!body) return;
    $('schedule-title').textContent = '日程详情';
    $('schedule-sub').textContent = '这一段时间她在做什么';
    var kinds = {
      home: '在家', outside: '外出', transit: '路上', sleep: '睡眠'
    };
    var rows = [
      ['时间', (item.start || '') + '–' + (item.end || '')],
      ['活动', item.activity || '--'],
      ['地点', item.location || '--'],
      ['类型', kinds[item.kind] || item.state || item.kind || '--'],
      ['状态', activityStateLabel(item.state)]
    ];
    var durationMinutes = Math.max(
      0,
      Number(item.end_min || 0) - Number(item.start_min || 0)
    );
    if (durationMinutes > 0) {
      var hours = Math.floor(durationMinutes / 60);
      var minutes = durationMinutes % 60;
      rows.splice(1, 0, ['时长', hours > 0
        ? hours + ' 小时' + (minutes ? ' ' + minutes + ' 分钟' : '')
        : minutes + ' 分钟']);
    }
    if (item.room) rows.push(['房间', item.room]);
    var canPreviewScene = scheduleSceneAvailable(item);
    if (canPreviewScene) rows.push(['场景', sceneLabel(item.scene)]);
    body.innerHTML = '<div class="schedule-detail-title">' +
      escapeHtml(item.activity || '一段日程') + '</div>' +
      '<div class="schedule-detail-rows">' + rows.map(function (row) {
        return '<div><small>' + escapeHtml(row[0]) + '</small><b>' +
          escapeHtml(String(row[1])) + '</b></div>';
      }).join('') + '</div>' +
      (canPreviewScene
        ? '<button type="button" class="cook-main-btn schedule-preview" ' +
          'id="schedule-preview">看看这个场景</button>'
        : '');
    $('schedule-modal').classList.remove('hidden');
  }

  function previewScheduleScene() {
    var item = state.scheduleItem;
    if (!scheduleSceneAvailable(item)) return;
    state.previewScene = item.scene;
    closeScheduleDetail();
    renderScene(true);
    showToast('场景预览：' + sceneLabel(item.scene));
  }

  function openDaySchedule() {
    var data = state.data || {};
    var timeline = data.timeline || [];
    var body = $('schedule-body');
    if (!body) return;
    var kinds = { home: '在家', outside: '外出', transit: '路上', sleep: '睡眠' };
    var counts = { home: 0, outside: 0, transit: 0 };
    timeline.forEach(function (item) {
      if (counts[item.kind] != null) counts[item.kind] += 1;
    });
    var dayFilter = state.dayScheduleFilter || 'all';
    var entries = timeline.map(function (item, index) {
      return { item: item, index: index };
    }).filter(function (entry) {
      return dayFilter === 'all' || entry.item.kind === dayFilter;
    });
    $('schedule-title').textContent = '今日日程';
    $('schedule-sub').textContent = (data.plan_date || '今天') +
      ' · 共 ' + timeline.length + ' 段 · 在家 ' + counts.home +
      ' / 外出 ' + counts.outside + ' / 路上 ' + counts.transit;
    if (!timeline.length) {
      body.innerHTML = '<p class="inventory-empty">今天还没有日程。</p>';
      $('schedule-modal').classList.remove('hidden');
      return;
    }
    var filters = [
      ['all', '全部'], ['home', '在家'],
      ['outside', '外出'], ['transit', '路上']
    ];
    body.innerHTML = '<div class="schedule-day-tools">' +
      '<div class="schedule-day-filters">' +
      filters.map(function (filter) {
        var filterCount = filter[0] === 'all'
          ? timeline.length
          : (counts[filter[0]] || 0);
        return '<button type="button" data-day-filter="' + filter[0] + '"' +
          (dayFilter === filter[0] ? ' class="active"' : '') + '>' +
          filter[1] + ' <b>' + filterCount + '</b></button>';
      }).join('') + '</div>' +
      '<button type="button" class="mini-btn" data-day-export="1">导出今日日程</button>' +
      '</div><div class="schedule-day-list">' +
      (entries.length
        ? entries.map(function (entry) {
            var item = entry.item;
            var isNow = data.now && String(data.now.id) === String(item.id);
            return '<button type="button" class="schedule-day-row' +
              (isNow ? ' current' : '') + '" data-day-index="' + entry.index + '">' +
              '<span class="schedule-day-time">' + escapeHtml(item.start || '') +
              '–' + escapeHtml(item.end || '') + '</span>' +
              '<span class="schedule-day-main"><b>' +
              escapeHtml(item.activity || '一段日程') + '</b><small>' +
              escapeHtml(item.location || '') + ' · ' +
              escapeHtml(kinds[item.kind] || item.kind || '') +
              (activityStateLabel(item.state) &&
               activityStateLabel(item.state) !== '--'
                ? ' · ' + escapeHtml(activityStateLabel(item.state))
                : '') +
              '</small></span>' +
              (isNow ? '<em>现在</em>' : '') +
              '</button>';
          }).join('')
        : '<p class="inventory-empty">这个分类今天没有日程。</p>') +
      '</div>';
    $('schedule-modal').classList.remove('hidden');
    var currentRow = body.querySelector('.schedule-day-row.current');
    if (currentRow && currentRow.scrollIntoView) {
      currentRow.scrollIntoView({ block: 'center', behavior: 'auto' });
    }
  }

  function exportDaySchedule() {
    var data = state.data || {};
    var filter = state.dayScheduleFilter || 'all';
    var filterLabels = {
      all: '全部', home: '在家', outside: '外出', transit: '路上'
    };
    var timeline = (data.timeline || []).filter(function (item) {
      return filter === 'all' || item.kind === filter;
    });
    if (!timeline.length) {
      showToast(filter === 'all'
        ? '今天还没有日程'
        : '当前分类今天没有日程');
      return;
    }
    var lines = [[
      '时间', '时长', '活动', '地点', '类型', '状态'
    ].map(csvCell).join(',')];
    timeline.forEach(function (item) {
      var minutes = Math.max(
        0,
        Number(item.end_min || 0) - Number(item.start_min || 0)
      );
      var duration = minutes > 0
        ? (minutes >= 60
          ? Math.floor(minutes / 60) + ' 小时' +
            (minutes % 60 ? ' ' + (minutes % 60) + ' 分钟' : '')
          : minutes + ' 分钟')
        : '';
      lines.push([
        (item.start || '') + '–' + (item.end || ''),
        duration,
        item.activity || '',
        item.location || '',
        item.kind || '',
        activityStateLabel(item.state)
      ].map(csvCell).join(','));
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '今日日程-' + String(data.plan_date || '') +
      (filter === 'all' ? '' : '-' + filterLabels[filter]) + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('今日日程已导出');
  }

  function closeScheduleDetail() {
    $('schedule-modal').classList.add('hidden');
  }

  function renderTimeline() {
    var data = state.data || {};
    var timeline = data.timeline || [];
    var clock = clockText();
    var currentMinutes = timeToMinutes(clock);
    var signature = JSON.stringify([data.persona, timeline, clock.slice(0, 5)]);
    if (signature === renderState.timeline) return;
    renderState.timeline = signature;
    var root = $('timeline');
    if (!timeline.length) {
      root.innerHTML = '<div class="empty-timeline">暂无时间线</div>';
      return;
    }
    var html = [];
    timeline.forEach(function (item, index) {
      var start = Number(item.start_min) || 0;
      var end = Number(item.end_min) || 0;
      if (end <= start) return;
      var left = start / 1440 * 100;
      var width = (end - start) / 1440 * 100;
      var cat = categoryClass(item);
      var currentClass = currentMinutes >= start && currentMinutes < end
        ? ' current' : '';
      var label = width > 4.0 ? escapeHtml(item.location || item.activity) : '';
      var tip = (item.start || '') + '–' + (item.end || '') + ' · ' +
        (item.activity || '') + ' · ' + (item.location || '');
      html.push('<div class="timeline-segment ' + cat + currentClass +
        '" data-schedule-index="' + index + '" title="' + escapeHtml(tip) + '" style="left:' + left +
        '%;width:' + width + '%"><span>' + label + '</span></div>');
    });
    var markerLeft = Math.min(100, Math.max(0, currentMinutes / 1440 * 100));
    html.push('<div class="timeline-marker" style="left:' + markerLeft + '%"><span>' +
      escapeHtml(clock.slice(0, 5)) + '</span></div>');
    html.push('<div class="timeline-ticks">');
    [0, 360, 720, 1080, 1440].forEach(function (tick) {
      var text = tick === 1440 ? '24:00' : String(Math.floor(tick / 60)).padStart(2, '0') + ':00';
      html.push('<span style="left:' + (tick / 1440 * 100) + '%">' + text + '</span>');
    });
    html.push('</div>');
    root.innerHTML = html.join('');
    $('timeline-now').textContent = '现在 ' + clock.slice(0, 5);
    $('timeline-legend').innerHTML = [
      '<span><i class="dot home"></i>在家</span>',
      '<span><i class="dot outside"></i>外出</span>',
      '<span><i class="dot transit"></i>路上</span>',
      '<span><i class="dot sleep"></i>睡眠</span>'
    ].join('');
  }

  function renderScenePicker(force) {
    var data = state.data || {};
    var signature = pickerSignature(data);
    if (!force && signature === renderState.picker) return;
    renderState.picker = signature;
    var now = data.now || null;
    var picker = $('scene-picker');
    var chips = $('scene-chips');
    if (!now) {
      picker.classList.add('hidden');
      return;
    }
    picker.classList.remove('hidden');
    var actual = now.kind === 'home' ? null : sceneFor(now);
    var active = state.previewScene || actual;
    chips.innerHTML = SCENES.map(function (scene) {
      return '<button class="chip ' + (scene.key === active ? 'active' : '') +
        '" data-scene="' + scene.key + '"><span class="chip-icon">' +
        sceneIconSvg(scene.key) + '</span>' + scene.label + '</button>';
    }).join('');
    Array.prototype.forEach.call(chips.querySelectorAll('.chip'), function (chip) {
      chip.addEventListener('click', function () {
        var key = chip.getAttribute('data-scene');
        if (key === actual) {
          state.previewScene = null;
        } else {
          state.previewScene = key;
        }
        renderScene(true);
        renderScenePicker(true);
      });
    });
  }

  // ---------------------------------------------------------------- 由我下厨
  var COOK_GAMES = [
    { id: 'chop', label: '切菜', hint: '按顺序把食材切好' },
    { id: 'heat', label: '火候', hint: '看准绿色区域，点「下锅」' },
    { id: 'season', label: '调味', hint: '把盐、酱、辣加到目标区' }
  ];

  var cookState = {
    dishes: [],
    dish: null,
    games: [],
    gameIndex: 0,
    scores: [],
    result: null,
    pollTimer: 0,
    stopHandler: null
  };

  var cookRuntime = { cleanup: null, timer: 0, done: false };

  function isDiningTable(item) {
    if (!item) return false;
    var id = String(item.id || '');
    var name = String(item.name || '');
    return id === 'dining_table' || id === 'dining_room_table' || name.indexOf('餐桌') >= 0;
  }

  function openCookModal() {
    if (!state.selectedItem || !isDiningTable(state.selectedItem)) return;
    closeItem();
    clearCookRuntime();
    clearCookPoll();
    cookState.dishes = [];
    cookState.dish = null;
    cookState.games = [];
    cookState.gameIndex = 0;
    cookState.scores = [];
    cookState.result = null;
    cookState.stopHandler = null;
    state.cookFilter = 'all';
    document.querySelectorAll('[data-cook-filter]').forEach(function (button) {
      button.classList.toggle('active', button.getAttribute('data-cook-filter') === 'all');
    });
    $('cook-sub').textContent = '冰箱里能做这些菜';
    $('cook-dishes').innerHTML = '<div class="cook-loading">打开冰箱看看有什么...</div>';
    $('cook-dish-step').classList.remove('hidden');
    $('cook-game-step').classList.add('hidden');
    $('cook-result-step').classList.add('hidden');
    $('cook-reply').classList.add('hidden');
    $('cook-reply').textContent = '';
    $('cook-modal').classList.remove('hidden');
    loadCookDishes();
    loadCookingHistory();
  }

  function closeCookModal() {
    clearCookRuntime();
    clearCookPoll();
    cookState.stopHandler = null;
    $('cook-modal').classList.add('hidden');
  }

  function clearCookRuntime() {
    if (cookRuntime.cleanup) {
      try { cookRuntime.cleanup(); } catch (e) {}
      cookRuntime.cleanup = null;
    }
    if (cookRuntime.timer) {
      clearTimeout(cookRuntime.timer);
      cookRuntime.timer = 0;
    }
    cookRuntime.done = false;
    cookState.stopHandler = null;
  }

  function loadCookDishes() {
    fetch('/api/cooking/dishes?persona=' + encodeURIComponent(state.persona || ''), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '读取失败');
        cookState.dishes = Array.isArray(data.dishes) ? data.dishes : [];
        renderCookDishes();
      })
      .catch(function (error) {
        $('cook-dishes').innerHTML = '<div class="cook-empty">冰箱打不开了：' +
          escapeHtml(error.message) + '</div>';
      });
  }

  function loadCookingHistory() {
    var box = $('cook-history');
    if (!box) return;
    box.innerHTML = '';
    fetch('/api/cooking/history', { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) return;
        var items = data.items || [];
        state.cookingHistory = items;
        if (!items.length) return;
        var scoreTotal = 0;
        var dishCounts = {};
        var topDish = '';
        var topDishCount = 0;
        items.forEach(function (item) {
          scoreTotal += Number(item.score || 0);
          var dish = String(item.dish || '');
          if (!dish) return;
          dishCounts[dish] = (dishCounts[dish] || 0) + 1;
          if (dishCounts[dish] > topDishCount) {
            topDish = dish;
            topDishCount = dishCounts[dish];
          }
        });
        var averageScore = Math.round(
          scoreTotal / items.length * 10
        ) / 10;
        box.innerHTML = '<div class="cook-history-head"><h4>最近下厨</h4>' +
          '<small class="cook-history-summary">共 ' + items.length +
          ' 道 · 均分 ' + averageScore +
          (topDishCount > 1
            ? ' · 常做 ' + escapeHtml(topDish) + ' ' + topDishCount + ' 次'
            : '') +
          '</small>' +
          '<button type="button" class="mini-btn" id="cook-history-export">导出</button>' +
          '</div>' +
          items.slice(-5).reverse().map(function (item) {
            return '<div class="cook-history-row"><b>' +
              escapeHtml(item.dish || '一道菜') + '</b><span>' +
              Number(item.score || 0) + ' 分 · ' +
              escapeHtml(item.grade || '') + ' · ' +
              escapeHtml(item.label || '') + '</span><small>' +
              escapeHtml(String(item.at || '').slice(5, 16).replace('T', ' ')) +
              '</small></div>';
          }).join('');
        var exportButton = $('cook-history-export');
        if (exportButton) {
          exportButton.addEventListener('click', exportCookingHistory);
        }
      })
      .catch(function () {
        box.innerHTML = '';
      });
  }

  function exportCookingHistory() {
    var items = state.cookingHistory || [];
    if (!items.length) {
      showToast('还没有可导出的下厨记录');
      return;
    }
    var lines = [['时间', '菜名', '分数', '等级', '评价', '食材']
      .map(csvCell).join(',')];
    items.forEach(function (item) {
      lines.push([
        String(item.at || ''),
        String(item.dish || ''),
        Number(item.score || 0),
        String(item.grade || ''),
        String(item.label || ''),
        (item.ingredients || []).join('、')
      ].map(csvCell).join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '下厨记录-' + day + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('下厨记录已导出');
  }

  function renderCookDishes() {
    var root = $('cook-dishes');
    var filter = state.cookFilter || 'all';
    var dishes = (cookState.dishes || []).filter(function (dish) {
      if (filter === 'all') return true;
      return (dish.meals || []).indexOf(filter) >= 0;
    });
    if (!dishes.length) {
      root.innerHTML = '<div class="cook-empty">' +
        (filter === 'all'
          ? '冰箱里凑不出一整道菜，先去买菜吧。'
          : '这个时段没有合适的菜。') + '</div>';
      return;
    }
    root.innerHTML = dishes.map(function (dish) {
      var ingredients = (dish.ingredients || []).join('、');
      var meals = (dish.meals || []).join(' / ');
      return '<button type="button" class="cook-dish" data-name="' + escapeHtml(dish.name) + '">' +
        ItemArtwork.draw(dish, 'dish') + '<span class="cook-dish-name">' + escapeHtml(dish.name) + '</span>' +
        '<span class="cook-dish-meta">食材：' + escapeHtml(ingredients) + '</span>' +
        '<span class="cook-dish-foot"><span>' + escapeHtml(dish.method || '家常做法') + '</span>' +
        '<em>' + escapeHtml(meals) + '</em></span></button>';
    }).join('');
  }

  function startCookGame(name) {
    var dish = null;
    for (var i = 0; i < cookState.dishes.length; i++) {
      if (String(cookState.dishes[i].name) === String(name)) {
        dish = cookState.dishes[i];
        break;
      }
    }
    if (!dish) return;
    clearCookRuntime();
    cookState.dish = dish;
    cookState.games = COOK_GAMES.slice();
    cookState.gameIndex = 0;
    cookState.scores = [];
    cookState.result = null;
    $('cook-dish-step').classList.add('hidden');
    $('cook-game-step').classList.remove('hidden');
    $('cook-result-step').classList.add('hidden');
    $('cook-reply').classList.add('hidden');
    $('cook-reply').textContent = '';
    $('cook-sub').textContent = '做：' + dish.name;
    startCookStage();
  }

  function startCookStage() {
    clearCookRuntime();
    if (cookState.gameIndex >= cookState.games.length) {
      finishCookGame();
      return;
    }
    var game = cookState.games[cookState.gameIndex];
    $('cook-round').textContent = '第 ' + (cookState.gameIndex + 1) + ' / ' +
      cookState.games.length + ' 关 · ' + game.label;
    $('cook-hint').textContent = game.hint;
    $('cook-stop').classList.add('hidden');
    $('cook-stop').disabled = false;
    $('cook-stop').textContent = '下锅！';
    $('cook-game-stage').innerHTML = '';
    if (game.id === 'chop') startChopStage();
    else if (game.id === 'heat') startHeatStage();
    else startSeasonStage();
  }

  function completeCookStage(score, note) {
    if (cookRuntime.done) return;
    cookRuntime.done = true;
    var value = Math.max(0, Math.min(100, Math.round(Number(score) || 0)));
    cookState.scores.push(value);
    if (cookRuntime.cleanup) {
      try { cookRuntime.cleanup(); } catch (e) {}
      cookRuntime.cleanup = null;
    }
    cookState.stopHandler = null;
    $('cook-stop').disabled = true;
    $('cook-stop').classList.add('hidden');
    var game = cookState.games[cookState.gameIndex] || {};
    $('cook-hint').textContent = (game.label || '这一关') + '：' + value + ' 分' +
      (note ? '，' + note : '');
    cookRuntime.timer = window.setTimeout(function () {
      cookRuntime.timer = 0;
      cookState.gameIndex += 1;
      startCookStage();
    }, 850);
  }

  // ---------------------------------------------------------- 切菜
  function startChopStage() {
    var dish = cookState.dish || {};
    var source = Array.isArray(dish.ingredients) ? dish.ingredients.slice() : [];
    var ingredients = [];
    for (var i = 0; i < source.length && ingredients.length < 4; i++) {
      var name = String(source[i] || '').trim();
      if (name && ingredients.indexOf(name) < 0) ingredients.push(name);
    }
    if (ingredients.length < 2) {
      ingredients = ['青菜', '肉片', '葱花'].slice(0, Math.max(2, ingredients.length || 2));
    }
    var order = ingredients.slice();
    var buttons = ingredients.slice().sort(function () { return Math.random() - 0.5; });
    var step = 0;
    var mistakes = 0;
    var stage = $('cook-game-stage');
    $('cook-hint').textContent = '按顺序切：先切「' + order[0] + '」';
    stage.innerHTML = '<div class="cook-chop">' +
      '<div class="cook-chop-now">要切：<b id="cook-chop-target">' + escapeHtml(order[0]) + '</b></div>' +
      '<div class="cook-chop-progress" id="cook-chop-progress">1 / ' + order.length + '</div>' +
      '<div class="cook-chop-buttons">' + buttons.map(function (name) {
        return '<button type="button" class="cook-chop-btn" data-name="' +
          escapeHtml(name) + '">' + escapeHtml(name) + '</button>';
      }).join('') + '</div></div>';

    var nodes = stage.querySelectorAll('.cook-chop-btn');
    var onClick = function (event) {
      if (cookRuntime.done) return;
      var button = event.currentTarget;
      var name = button.getAttribute('data-name');
      if (name === order[step]) {
        step += 1;
        if (step >= order.length) {
          completeCookStage(Math.max(0, 100 - mistakes * 15), mistakes ? '手有点抖' : '刀工利落');
          return;
        }
        var target = $('cook-chop-target');
        var progress = $('cook-chop-progress');
        if (target) target.textContent = order[step];
        if (progress) progress.textContent = (step + 1) + ' / ' + order.length;
        $('cook-hint').textContent = '下一刀：「' + order[step] + '」';
      } else {
        mistakes += 1;
        button.classList.add('wrong');
        window.setTimeout(function () { button.classList.remove('wrong'); }, 260);
        $('cook-hint').textContent = '切歪了！下一刀还是「' + order[step] + '」';
      }
    };
    Array.prototype.forEach.call(nodes, function (node) {
      node.addEventListener('click', onClick);
    });
    cookRuntime.cleanup = function () {
      Array.prototype.forEach.call(nodes, function (node) {
        node.removeEventListener('click', onClick);
      });
    };
  }

  // ---------------------------------------------------------- 火候
  function startHeatStage() {
    var totalRounds = 2;
    var round = 0;
    var roundScores = [];
    var marker = 0;
    var direction = 1;
    var speed = 0;
    var active = false;
    var locked = false;
    var raf = 0;
    var lastTs = 0;
    var stage = $('cook-game-stage');
    stage.innerHTML = '<div class="cook-bar"><div class="cook-zone"></div>' +
      '<div class="cook-marker" id="cook-marker"></div></div>';
    $('cook-stop').classList.remove('hidden');

    function tick(ts) {
      if (!active) return;
      var last = lastTs || ts;
      var delta = Math.min(64, ts - last);
      lastTs = ts;
      marker += direction * speed * delta / 1000;
      if (marker >= 100) { marker = 100; direction = -1; }
      if (marker <= 0) { marker = 0; direction = 1; }
      var node = $('cook-marker');
      if (node) node.style.left = marker + '%';
      raf = requestAnimationFrame(tick);
    }

    function beginRound() {
      round += 1;
      if (round > totalRounds) {
        var total = 0;
        for (var i = 0; i < roundScores.length; i++) total += roundScores[i];
        completeCookStage(Math.round(total / Math.max(1, roundScores.length)), '两锅都出锅了');
        return;
      }
      marker = 0;
      direction = 1;
      speed = 70 + round * 26;
      locked = false;
      active = true;
      $('cook-stop').disabled = false;
      $('cook-stop').classList.remove('hidden');
      $('cook-stop').textContent = '下锅！';
      $('cook-hint').textContent = '第 ' + round + ' 锅：看准绿色区域，点「下锅」';
      lastTs = 0;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(tick);
    }

    function stopRound() {
      if (!active || locked) return;
      locked = true;
      active = false;
      cancelAnimationFrame(raf);
      var score = Math.max(0, Math.min(100, Math.round(100 - Math.abs(marker - 50) * 2.2)));
      roundScores.push(score);
      $('cook-stop').disabled = true;
      $('cook-hint').textContent = '第 ' + round + ' 锅：' + score + ' 分' +
        (score >= 80 ? '，火候刚好' : score >= 50 ? '，还能吃' : '，有点悬');
      cookRuntime.timer = window.setTimeout(function () {
        cookRuntime.timer = 0;
        beginRound();
      }, 850);
    }

    cookState.stopHandler = stopRound;
    cookRuntime.cleanup = function () {
      active = false;
      cancelAnimationFrame(raf);
      cookState.stopHandler = null;
    };
    beginRound();
  }

  // ---------------------------------------------------------- 调味
  function startSeasonStage() {
    var flavors = [
      { key: 'salt', label: '盐', speed: 72, pos: Math.random() * 100, direction: 1 },
      { key: 'soy', label: '酱', speed: 98, pos: Math.random() * 100, direction: -1 },
      { key: 'spice', label: '辣', speed: 126, pos: Math.random() * 100, direction: 1 }
    ];
    var done = {};
    var scores = [];
    var raf = 0;
    var lastTs = 0;
    var stage = $('cook-game-stage');
    $('cook-hint').textContent = '看准目标区，点「加」，把三种味道调到合适的位置';
    stage.innerHTML = '<div class="cook-season">' + flavors.map(function (flavor) {
      return '<div class="cook-season-row" data-flavor="' + flavor.key + '">' +
        '<span class="cook-season-name">' + flavor.label + '</span>' +
        '<div class="cook-season-bar"><div class="cook-season-zone"></div>' +
        '<div class="cook-season-marker" id="cook-season-marker-' + flavor.key + '"></div></div>' +
        '<button type="button" class="cook-season-btn" data-flavor="' + flavor.key + '">加</button></div>';
    }).join('') + '</div>';

    function paint() {
      flavors.forEach(function (flavor) {
        var marker = $('cook-season-marker-' + flavor.key);
        if (marker) marker.style.left = flavor.pos + '%';
      });
    }

    function tick(ts) {
      var last = lastTs || ts;
      var delta = Math.min(64, ts - last);
      lastTs = ts;
      flavors.forEach(function (flavor) {
        if (done[flavor.key]) return;
        flavor.pos += flavor.direction * flavor.speed * delta / 1000;
        if (flavor.pos >= 100) { flavor.pos = 100; flavor.direction = -1; }
        if (flavor.pos <= 0) { flavor.pos = 0; flavor.direction = 1; }
      });
      paint();
      raf = requestAnimationFrame(tick);
    }

    function onAdd(event) {
      var key = event.currentTarget.getAttribute('data-flavor');
      var flavor = null;
      for (var i = 0; i < flavors.length; i++) {
        if (flavors[i].key === key) { flavor = flavors[i]; break; }
      }
      if (!flavor || done[key]) return;
      done[key] = true;
      var score = Math.max(0, Math.min(100, Math.round(100 - Math.abs(flavor.pos - 50) * 2.2)));
      scores.push(score);
      event.currentTarget.disabled = true;
      event.currentTarget.textContent = score + ' 分';
      $('cook-hint').textContent = flavor.label + '：' + score + ' 分' +
        (score >= 80 ? '，味道刚好' : score >= 50 ? '，还能入口' : '，手抖了');
      var remaining = 0;
      for (var k = 0; k < flavors.length; k++) {
        if (!done[flavors[k].key]) remaining += 1;
      }
      if (remaining === 0) {
        var total = 0;
        for (var j = 0; j < scores.length; j++) total += scores[j];
        completeCookStage(Math.round(total / scores.length), '味道定下来了');
      }
    }

    var nodes = stage.querySelectorAll('.cook-season-btn');
    Array.prototype.forEach.call(nodes, function (node) {
      node.addEventListener('click', onAdd);
    });
    cookRuntime.cleanup = function () {
      cancelAnimationFrame(raf);
      Array.prototype.forEach.call(nodes, function (node) {
        node.removeEventListener('click', onAdd);
      });
    };
    paint();
    raf = requestAnimationFrame(tick);
  }

  function stopCookRound() {
    if (cookState.stopHandler) cookState.stopHandler();
  }

  function finishCookGame() {
    clearCookRuntime();
    var total = 0;
    var count = cookState.scores.length;
    for (var i = 0; i < count; i++) total += cookState.scores[i];
    var average = Math.round(total / Math.max(1, count));
    $('cook-game-step').classList.add('hidden');
    $('cook-result-step').classList.remove('hidden');
    $('cook-result-dish').innerHTML = '<div class="cook-cooking">正在尝味道...</div>';
    $('cook-taste').innerHTML = '';
    $('cook-reply').classList.add('hidden');
    $('cook-reply').textContent = '';
    fetch('/api/cooking/cook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dish: cookState.dish.name, score: average })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '做菜失败');
        cookState.result = data;
        renderCookResult(data);
      })
      .catch(function (error) {
        $('cook-result-dish').innerHTML = '<div class="cook-empty">' +
          escapeHtml(error.message) + '</div>';
      });
  }

  function renderCookResult(data) {
    var dish = data.dish || {};
    var taste = data.taste || {};
    $('cook-sub').textContent = '做好了：' + (dish.name || '一道菜');
    $('cook-result-dish').innerHTML =
      '<button type="button" class="cook-result-card" id="cook-result-card">' +
      '<span class="cook-result-emoji">🍲</span>' +
      '<span class="cook-result-info"><b>' + escapeHtml(dish.name || '') + '</b>' +
      '<small>食材：' + escapeHtml((dish.ingredients || []).join('、')) + '</small>' +
      '<small>' + escapeHtml(dish.method || '家常做法') + '</small></span></button>';
    $('cook-taste').innerHTML =
      '<div class="cook-taste-line"><span class="cook-grade grade-' + escapeHtml(taste.grade || 'C') + '">' +
      escapeHtml(taste.grade || '') + '</span><b>' + escapeHtml(taste.label || '') + '</b>' +
      '<span class="cook-score">' + escapeHtml(String(taste.score != null ? taste.score : '')) +
      ' 分</span></div><p>' + escapeHtml(taste.comment || '') + '</p>';
    $('cook-serve').classList.remove('hidden');
    $('cook-serve').disabled = false;
    $('cook-serve').textContent = '点这道菜，叫月月来吃饭';
    $('cook-reply').classList.add('hidden');
    $('cook-reply').textContent = '';
    var card = $('cook-result-card');
    if (card) card.addEventListener('click', serveCookedDish);
  }

  function serveCookedDish() {
    if (!cookState.result || cookState.pollTimer) return;
    var dish = cookState.result.dish || {};
    var taste = cookState.result.taste || {};
    $('cook-serve').disabled = true;
    $('cook-serve').textContent = '去叫她了...';
    $('cook-reply').classList.remove('hidden');
    $('cook-reply').textContent = '她正往餐桌这边走...';
    fetch('/api/cooking/serve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dish: dish.name, taste: taste })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '呼叫失败');
        pollCookReply(data.id, Date.now());
      })
      .catch(function (error) {
        $('cook-serve').disabled = false;
        $('cook-serve').textContent = '再叫她一次';
        $('cook-reply').textContent = '没叫应：' + error.message;
      });
  }

  function pollCookReply(id, startedAt) {
    cookState.pollTimer = window.setTimeout(function () {
      fetch('/api/interact?id=' + encodeURIComponent(id), { cache: 'no-store' })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (!data.ok) throw new Error(data.error || '读取失败');
          if (data.pending) {
            if (Date.now() - startedAt > 45000) throw new Error('她好像没听见');
            pollCookReply(id, startedAt);
            return;
          }
          var reply = data.response || {};
          $('cook-reply').textContent = reply.speech || reply.reply || reply.text || '她过来了。';
          $('cook-serve').textContent = '她已经上桌了';
          clearCookPoll();
        })
        .catch(function (error) {
          $('cook-serve').disabled = false;
          $('cook-serve').textContent = '再叫她一次';
          $('cook-reply').textContent = '没叫应：' + error.message;
          clearCookPoll();
        });
    }, 1200);
  }

  function clearCookPoll() {
    if (cookState.pollTimer) {
      clearTimeout(cookState.pollTimer);
      cookState.pollTimer = 0;
    }
  }

  // ---------------------------------------------------------------- 观察窗相机
  var cameraMode = false;

  function enterCameraMode() {
    cameraMode = true;
    closeItem();
    $('camera-target').textContent = '取景：点击画面选择目标';
    $('camera-overlay').classList.remove('hidden');
    showToast('点击画面里的月月 / 家具 / 房间来取景');
  }

  function exitCameraMode() {
    cameraMode = false;
    $('camera-overlay').classList.add('hidden');
  }

  function onCameraStageClick(event) {
    if (!cameraMode) return;
    event.preventDefault();
    event.stopPropagation();
    var room3d = event.target.closest('.bedroom-3d');
    if (room3d && event.target.closest('.bedroom-3d-viewport') && window.Bedroom3D) {
      var engine = Bedroom3D.instances.get(room3d);
      var picked = engine && engine.pick(event);
      if (picked === 'character') takeCameraPhoto({ target: 'character' }, '拍一张月月');
      else if (picked) takeCameraPhoto({ target: 'item', item_id: picked }, '拍一件家具');
      else takeCameraPhoto({ target: 'room' }, '拍下这个房间');
      return;
    }
    var character = event.target.closest('.character-marker');
    if (character) {
      takeCameraPhoto({ target: 'character' }, '拍一张月月');
      return;
    }
    var hit = event.target.closest('.furniture-hit');
    if (hit) {
      takeCameraPhoto(
        { target: 'item', item_id: hit.getAttribute('data-id') },
        '拍一件家具'
      );
      return;
    }
    takeCameraPhoto({ target: 'room' }, '拍下这个房间');
  }

  function onCameraHover(event) {
    if (!cameraMode || !event.target || !event.target.closest) return;
    var label = '当前房间';
    if (event.target.closest('.character-marker')) {
      label = '月月';
    } else {
      var hit = event.target.closest('.furniture-hit');
      if (hit) {
        var id = hit.getAttribute('data-id');
        var items = state.homeItems || [];
        for (var i = 0; i < items.length; i++) {
          if (String(items[i].id) === String(id)) {
            label = items[i].name || id;
            break;
          }
        }
        if (label === '当前房间') label = id;
      }
    }
    var node = $('camera-target');
    if (node) node.textContent = '取景：' + label;
  }

  function loadStoredPhotos() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-photo-gallery') || '[]');
      return Array.isArray(parsed)
        ? parsed.filter(function (item) {
            return item && typeof item.src === 'string' && item.src;
          }).slice(-6)
        : [];
    } catch (error) {
      return [];
    }
  }

  function persistPhotos(photos) {
    var chosen = [];
    var total = 0;
    for (var index = (photos || []).length - 1; index >= 0; index -= 1) {
      var item = photos[index];
      if (!item || !item.src) continue;
      var serialized = JSON.stringify(item);
      if (total + serialized.length > 2400000) break;
      chosen.unshift(item);
      total += serialized.length;
    }
    try {
      localStorage.setItem('vl-photo-gallery', JSON.stringify(chosen));
    } catch (error) {
      /* 本地空间不足时仅保留当前会话照片 */
    }
  }

  function photoTimeText(value) {
    var text = String(value || '');
    if (!text) return '';
    return text.slice(5, 16).replace('T', ' ');
  }

  function showPhotoAt(index) {
    var photos = state.photos || [];
    if (!photos.length) return;
    var next = ((Number(index) || 0) % photos.length + photos.length) % photos.length;
    state.photoIndex = next;
    var photo = photos[next];
    if (!photo) return;
    $('photo-image').src = photo.src;
    $('photo-image').classList.remove('hidden');
    $('photo-loading').classList.add('hidden');
    var takenAt = photoTimeText(photo.at);
    $('photo-caption').textContent = ((photo.caption || '') +
      (takenAt ? ' · ' + takenAt : '')).trim();
    var gallery = $('photo-gallery');
    if (gallery) {
      gallery.querySelectorAll('[data-photo-index]').forEach(function (button) {
        button.classList.toggle(
          'active',
          Number(button.getAttribute('data-photo-index')) === next
        );
      });
    }
  }

  function renderPhotoGallery() {
    var gallery = $('photo-gallery');
    if (!gallery) return;
    var photos = state.photos || [];
    if (!photos.length) {
      gallery.innerHTML = '';
      return;
    }
    gallery.innerHTML = '<div class="photo-gallery-head">' +
      '<span class="photo-gallery-label">最近照片</span>' +
      '<button type="button" class="photo-gallery-clear" id="photo-gallery-clear">清空</button>' +
      '</div>' +
      photos.map(function (photo, index) {
        return '<span class="photo-thumb-wrap">' +
          '<button type="button" class="photo-thumb" data-photo-index="' +
          index + '" title="' + escapeHtml(photoTimeText(photo.at)) +
          '"><img src="' + escapeHtml(photo.src) + '" alt="照片 ' +
          (index + 1) + '"></button>' +
          '<button type="button" class="photo-thumb-delete" data-photo-delete="' +
          index + '" aria-label="删除这张照片" title="删除这张照片">×</button>' +
          '</span>';
      }).join('');
    gallery.querySelectorAll('[data-photo-index]').forEach(function (button) {
      button.addEventListener('click', function () {
        showPhotoAt(Number(button.getAttribute('data-photo-index')));
      });
    });
    gallery.querySelectorAll('[data-photo-delete]').forEach(function (button) {
      button.addEventListener('click', function () {
        var index = Number(button.getAttribute('data-photo-delete'));
        state.photos.splice(index, 1);
        if (state.photoIndex >= state.photos.length) {
          state.photoIndex = state.photos.length - 1;
        }
        persistPhotos(state.photos);
        if (!state.photos.length) {
          state.photoIndex = -1;
          $('photo-image').classList.add('hidden');
          $('photo-image').removeAttribute('src');
          $('photo-caption').textContent = '';
          $('photo-loading').classList.add('hidden');
        } else {
          showPhotoAt(Math.min(index, state.photos.length - 1));
        }
        renderPhotoGallery();
        showToast('已删除这张照片');
      });
    });
    var clearButton = $('photo-gallery-clear');
    if (clearButton) {
      clearButton.addEventListener('click', function () {
        state.photos = [];
        try {
          localStorage.removeItem('vl-photo-gallery');
        } catch (error) {
          /* 忽略本地存储异常 */
        }
        state.photoIndex = -1;
        $('photo-image').classList.add('hidden');
        $('photo-image').removeAttribute('src');
        $('photo-caption').textContent = '';
        $('photo-loading').classList.add('hidden');
        renderPhotoGallery();
        showToast('最近照片已清空');
      });
    }
  }

  function takeCameraPhoto(payload, label) {
    exitCameraMode();
    payload.persona = state.persona || '';
    $('photo-modal').classList.remove('hidden');
    $('photo-image').classList.add('hidden');
    $('photo-image').removeAttribute('src');
    renderPhotoGallery();
    $('photo-loading').classList.remove('hidden');
    $('photo-loading').textContent = '显影中...（大约 20-60 秒）';
    $('photo-caption').textContent = label || '';
    $('photo-image').onerror = function () {
      this.classList.add('hidden');
      $('photo-loading').classList.remove('hidden');
      $('photo-loading').textContent = '图片加载失败，请再试一次';
    };
    fetch('/api/camera/photo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '拍照失败');
        $('photo-loading').classList.add('hidden');
        $('photo-image').src = data.image;
        $('photo-image').classList.remove('hidden');
        $('photo-caption').textContent = data.caption || label || '';
        state.photos = (state.photos || []).concat([{
          src: data.image,
          caption: data.caption || label || '',
          at: new Date().toISOString()
        }]).slice(-6);
        state.photoIndex = state.photos.length - 1;
        persistPhotos(state.photos);
        renderPhotoGallery();
      })
      .catch(function (error) {
        $('photo-loading').classList.remove('hidden');
        $('photo-loading').textContent = '没拍成：' + error.message;
      });
  }

  function saveCameraPhoto() {
    var image = $('photo-image');
    if (!image || image.classList.contains('hidden') || !image.getAttribute('src')) {
      showToast('还没有照片可保存');
      return;
    }
    var src = image.getAttribute('src');
    var extension = src.indexOf('image/jpeg') >= 0 ? 'jpg' : 'png';
    var day = new Date().toISOString().slice(0, 10);
    var link = document.createElement('a');
    link.href = src;
    link.download = '虚拟人生-拍立得-' + day + '.' + extension;
    document.body.appendChild(link);
    link.click();
    link.remove();
    showToast('照片已保存');
  }

  function closePhotoModal() {
    $('photo-modal').classList.add('hidden');
  }

  // ---------------------------------------------------------------- 游戏机 · 多小游戏
  var GAME_MAX_HP = 60;
  var GAME_MAX_ROUNDS = 12;
  var GAME_MOVE_LABELS = { attack: '攻击', defend: '防御', special: '必杀' };
  var GAME_TAUNTS = {
    attack: ['就这？', '这一拳软绵绵的。', '你是在给我挠痒？', '力度还行，准头不行。'],
    defend: ['缩得倒挺快。', '就知道你会防。', '防吧，反正你也打不疼我。'],
    special: ['看招！', '这招你接得住吗？', '别眨眼。', '吃我这记必杀！']
  };
  var RPS_LABELS = { rock: '石头', scissors: '剪刀', paper: '布' };
  var gameState = {
    current: '',
    replyTimer: 0,
    battle: { playerHp: GAME_MAX_HP, aiHp: GAME_MAX_HP, round: 1, busy: false, playerCd: 0, aiCd: 0, over: false },
    rps: { player: 0, ai: 0, round: 1, busy: false, over: false },
    mole: { score: 0, aiScore: 0, timeLeft: 8, tickTimer: 0, spawnTimer: 0, endTimer: 0, active: false, over: false },
    ttt: { board: ['', '', '', '', '', '', '', '', ''], busy: false, over: false, timer: 0 },
    memory: { deck: [], flipped: [], matched: 0, moves: 0, aiMoves: 0, busy: false, over: false, timer: 0 },
    guess: { target: 0, attempts: 0, max: 7, over: false },
    dice: { player: 0, ai: 0, round: 1, busy: false, over: false },
    gomoku: { board: [], busy: false, over: false, timer: 0 },
    connect4: { board: [], busy: false, over: false, timer: 0 },
    reversi: { board: [], busy: false, over: false, timer: 0 },
    launchItem: 'game_console',
    launchAction: '打游戏'
  };

  function isGameConsole(item) {
    if (!item) return false;
    var id = String(item.id || '');
    var name = String(item.name || '');
    return id === 'game_console' || name.indexOf('游戏机') >= 0;
  }

  function isBoardGame(item) {
    if (!item) return false;
    var id = String(item.id || '');
    var name = String(item.name || '');
    return id === 'board_game' || name.indexOf('桌游') >= 0 || name.indexOf('拼图') >= 0;
  }

  function isGameItem(item) {
    return isGameConsole(item) || isBoardGame(item);
  }

  function stopTttTimer() {
    if (gameState.ttt.timer) {
      clearTimeout(gameState.ttt.timer);
      gameState.ttt.timer = 0;
    }
  }

  function stopMemoryTimer() {
    if (gameState.memory.timer) {
      clearTimeout(gameState.memory.timer);
      gameState.memory.timer = 0;
    }
  }

  function stopGomokuTimer() {
    if (gameState.gomoku.timer) {
      clearTimeout(gameState.gomoku.timer);
      gameState.gomoku.timer = 0;
    }
  }

  function stopConnect4Timer() {
    if (gameState.connect4.timer) {
      clearTimeout(gameState.connect4.timer);
      gameState.connect4.timer = 0;
    }
  }

  function stopReversiTimer() {
    if (gameState.reversi.timer) {
      clearTimeout(gameState.reversi.timer);
      gameState.reversi.timer = 0;
    }
  }

  function openGameModal() {
    if (!state.selectedItem || !isGameItem(state.selectedItem)) return;
    var boardMode = isBoardGame(state.selectedItem);
    gameState.launchItem = boardMode ? 'board_game' : 'game_console';
    gameState.launchAction = boardMode ? '开一局桌游' : '打一局';
    closeItem();
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    gameState.current = '';
    $('game-ai-reply').classList.add('hidden');
    $('game-ai-reply').textContent = '';
    $('game-restart').classList.add('hidden');
    $('game-play-step').classList.add('hidden');
    $('game-select-step').classList.remove('hidden');
    $('game-head-title').textContent = boardMode ? '桌游' : '游戏机';
    $('game-sub').textContent = boardMode
      ? '选一个桌游，和月月下一局'
      : '选一个小游戏，和月月打';
    document.querySelectorAll('#game-select-step .game-pick').forEach(function (button) {
      button.classList.toggle('hidden', boardMode && button.getAttribute('data-board') !== '1');
    });
    $('game-modal').classList.remove('hidden');
  }

  function closeGameModal() {
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    $('game-modal').classList.add('hidden');
  }

  function startGame(game) {
    if (['battle', 'rps', 'mole', 'ttt', 'memory', 'guess', 'dice', 'gomoku', 'connect4', 'reversi'].indexOf(game) < 0) return;
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    gameState.current = game;
    $('game-select-step').classList.add('hidden');
    $('game-play-step').classList.remove('hidden');
    $('game-restart').classList.add('hidden');
    $('game-ai-reply').classList.add('hidden');
    $('game-ai-reply').textContent = '';
    ['game-battle-step', 'game-rps-step', 'game-mole-step', 'game-ttt-step', 'game-memory-step', 'game-guess-step', 'game-dice-step', 'game-gomoku-step', 'game-connect4-step', 'game-reversi-step'].forEach(function (id) {
      $(id).classList.add('hidden');
    });
    if (game === 'battle') {
      $('game-battle-step').classList.remove('hidden');
      $('game-title').textContent = '街机对战';
      $('game-sub').textContent = '你 VS 月月';
      startBattle();
    } else if (game === 'rps') {
      $('game-rps-step').classList.remove('hidden');
      $('game-title').textContent = '猜拳';
      $('game-sub').textContent = '三局两胜';
      startRps();
    } else if (game === 'mole') {
      $('game-mole-step').classList.remove('hidden');
      $('game-title').textContent = '打地鼠';
      $('game-sub').textContent = '8 秒手速挑战';
      startMole();
    } else if (game === 'memory') {
      $('game-memory-step').classList.remove('hidden');
      $('game-title').textContent = '翻牌记忆';
      $('game-sub').textContent = '和月月比步数';
      startMemory();
    } else if (game === 'guess') {
      $('game-guess-step').classList.remove('hidden');
      $('game-title').textContent = '猜数字';
      $('game-sub').textContent = '1–100，7 次机会';
      startGuess();
    } else if (game === 'dice') {
      $('game-dice-step').classList.remove('hidden');
      $('game-title').textContent = '比大小';
      $('game-sub').textContent = '三局两胜掷骰子';
      startDice();
    } else if (game === 'gomoku') {
      $('game-gomoku-step').classList.remove('hidden');
      $('game-title').textContent = '五子棋';
      $('game-sub').textContent = '15×15 连成五子';
      startGomoku();
    } else if (game === 'connect4') {
      $('game-connect4-step').classList.remove('hidden');
      $('game-title').textContent = '四子棋';
      $('game-sub').textContent = '7×6 连成四子';
      startConnect4();
    } else if (game === 'reversi') {
      $('game-reversi-step').classList.remove('hidden');
      $('game-title').textContent = '黑白棋';
      $('game-sub').textContent = '8×8 翻子比多少';
      startReversi();
    } else {
      $('game-ttt-step').classList.remove('hidden');
      $('game-title').textContent = '井字棋';
      $('game-sub').textContent = '你执 X，月月执 O';
      startTtt();
    }
  }

  function restartCurrentGame() {
    if (!gameState.current) return;
    startGame(gameState.current);
  }

  function leaveGame() {
    clearGameReply();
    stopMoleTimers();
    stopTttTimer();
    stopMemoryTimer();
    stopGomokuTimer();
    stopConnect4Timer();
    stopReversiTimer();
    gameState.current = '';
    $('game-play-step').classList.add('hidden');
    $('game-select-step').classList.remove('hidden');
    $('game-restart').classList.add('hidden');
    $('game-ai-reply').classList.add('hidden');
    $('game-ai-reply').textContent = '';
    $('game-sub').textContent = isBoardGame(state.selectedItem)
      ? '选一个桌游，和月月下一局'
      : '选一个小游戏，和月月打';
  }

  function gameResultNode() {
    if (gameState.current === 'battle') return $('game-log');
    if (gameState.current === 'rps') return $('game-rps-log');
    if (gameState.current === 'mole') return $('game-mole-status');
    if (gameState.current === 'ttt') return $('game-ttt-status');
    if (gameState.current === 'memory') return $('game-memory-status');
    if (gameState.current === 'guess') return $('game-guess-status');
    if (gameState.current === 'dice') return $('game-dice-status');
    if (gameState.current === 'gomoku') return $('game-gomoku-status');
    if (gameState.current === 'connect4') return $('game-connect4-status');
    if (gameState.current === 'reversi') return $('game-reversi-status');
    return $('game-log');
  }

  function appendGameResult(text) {
    var node = gameResultNode();
    node.textContent = text;
  }

  function showGameResult(summary, chat, gameMeta) {
    $('game-restart').classList.remove('hidden');
    appendGameResult(summary);
    sendGameChat(chat, gameMeta || null, summary);
  }

  function showGameReply(text) {
    var node = $('game-ai-reply');
    node.textContent = text;
    node.classList.remove('hidden');
  }

  function clearGameReply() {
    if (gameState.replyTimer) {
      clearTimeout(gameState.replyTimer);
      gameState.replyTimer = 0;
    }
  }

  function sendGameChat(text, gameMeta, summary) {
    clearGameReply();
    showGameReply('她放下手柄，正在回你……');
    var gameItem = gameState.launchItem || 'game_console';
    var gameAction = gameState.launchAction || '打游戏';
    var payload = {
      kind: 'chat',
      item_id: gameItem,
      action: gameAction,
      text: text
    };
    if (gameMeta) {
      payload = {
        kind: 'game',
        item_id: gameItem,
        action: gameAction,
        text: '',
        game_name: gameMeta.name || '小游戏',
        game_result: gameMeta.result || '',
        game_score: gameMeta.score || '',
        game_summary: summary || ''
      };
    }
    fetch('/api/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '呼叫失败');
        pollGameReply(data.id, Date.now());
      })
      .catch(function (error) {
        showGameReply('她没应声：' + error.message);
      });
  }

  function pollGameReply(id, startedAt) {
    gameState.replyTimer = window.setTimeout(function () {
      fetch('/api/interact?id=' + encodeURIComponent(id), { cache: 'no-store' })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (!data.ok) throw new Error(data.error || '读取失败');
          if (data.pending) {
            if (Date.now() - startedAt > 45000) throw new Error('她好像没听见');
            pollGameReply(id, startedAt);
            return;
          }
          var reply = data.response || {};
          showGameReply(reply.speech || reply.reply || reply.text || '她哼了一声。');
          clearGameReply();
        })
        .catch(function (error) {
          showGameReply('她没应声：' + error.message);
          clearGameReply();
        });
    }, 1200);
  }

  // ---------------------------------------------------------- 街机对战
  function startBattle() {
    var battle = gameState.battle;
    battle.playerHp = GAME_MAX_HP;
    battle.aiHp = GAME_MAX_HP;
    battle.round = 1;
    battle.busy = false;
    battle.playerCd = 0;
    battle.aiCd = 0;
    battle.over = false;
    $('game-log').textContent = '选一个招式，开打。';
    updateBattleHud();
    setBattleButtons(true);
  }

  function setBattleButtons(enabled) {
    Array.prototype.forEach.call(document.querySelectorAll('#game-battle-step .game-move'), function (button) {
      var move = button.getAttribute('data-move');
      button.disabled = !enabled || (move === 'special' && gameState.battle.playerCd > 0);
    });
  }

  function updateBattleHud() {
    var battle = gameState.battle;
    var playerFill = $('game-hp-player');
    var aiFill = $('game-hp-ai');
    if (playerFill) playerFill.style.width = (battle.playerHp / GAME_MAX_HP * 100) + '%';
    if (aiFill) aiFill.style.width = (battle.aiHp / GAME_MAX_HP * 100) + '%';
    $('game-hp-player-text').textContent = battle.playerHp + ' / ' + GAME_MAX_HP;
    $('game-hp-ai-text').textContent = battle.aiHp + ' / ' + GAME_MAX_HP;
    $('game-round').textContent = battle.over ? '对战结束' : '第 ' + battle.round + ' 回合';
    var special = document.querySelector('#game-battle-step .game-move[data-move="special"]');
    if (special) {
      special.innerHTML = battle.playerCd > 0
        ? '必杀<small>冷却 ' + battle.playerCd + ' 回合</small>'
        : '必杀<small>冷却 2 回合</small>';
    }
  }

  function appendBattleLog(text) {
    var log = $('game-log');
    log.textContent = (log.textContent ? log.textContent + '\n' : '') + text;
    log.scrollTop = log.scrollHeight;
  }

  function pickBattleAiMove() {
    var battle = gameState.battle;
    var roll = Math.random();
    if (battle.aiCd <= 0 && (battle.playerHp <= 22 || roll < 0.16)) return 'special';
    if (battle.aiHp <= 18 && roll < 0.45) return 'defend';
    if (roll < 0.58) return 'attack';
    if (roll < 0.86) return 'defend';
    return 'attack';
  }

  function battleMoveDamage(move) {
    if (move === 'attack') return 8 + Math.floor(Math.random() * 6);
    if (move === 'special') return 16 + Math.floor(Math.random() * 7);
    return 0;
  }

  function battleTaunt(move) {
    var list = GAME_TAUNTS[move] || GAME_TAUNTS.attack;
    return list[Math.floor(Math.random() * list.length)];
  }

  function chooseBattleMove(move) {
    var battle = gameState.battle;
    if (battle.busy || battle.over) return;
    if (move === 'special' && battle.playerCd > 0) return;
    battle.busy = true;
    setBattleButtons(false);
    appendBattleLog('你：' + GAME_MOVE_LABELS[move] + '！');
    appendBattleLog('月月正在选招式……');
    var aiMove = pickBattleAiMove();
    window.setTimeout(function () {
      resolveBattleTurn(move, aiMove);
    }, 480);
  }

  function resolveBattleTurn(playerMove, aiMove) {
    var battle = gameState.battle;
    var playerDamage = 0;
    var aiDamage = 0;
    if (playerMove !== 'defend') {
      playerDamage = battleMoveDamage(playerMove);
      if (aiMove === 'defend') playerDamage = Math.max(1, Math.round(playerDamage * 0.3));
      if (playerMove === 'special') battle.playerCd = 2;
    }
    if (aiMove !== 'defend') {
      aiDamage = battleMoveDamage(aiMove);
      if (playerMove === 'defend') aiDamage = Math.max(1, Math.round(aiDamage * 0.25));
      if (aiMove === 'special') battle.aiCd = 2;
    }
    battle.aiHp = Math.max(0, battle.aiHp - playerDamage);
    battle.playerHp = Math.max(0, battle.playerHp - aiDamage);
    var lines = ['月月：' + GAME_MOVE_LABELS[aiMove] + '！'];
    if (playerDamage > 0) lines.push('你对月月造成 ' + playerDamage + ' 点伤害。');
    else if (playerMove === 'defend') lines.push('你摆出防御姿态。');
    if (aiDamage > 0) lines.push('月月对你造成 ' + aiDamage + ' 点伤害。');
    else if (aiMove === 'defend') lines.push('月月选择了防御。');
    if (aiMove !== 'defend' && Math.random() < 0.55) lines.push('月月：' + battleTaunt(aiMove));
    if (battle.playerCd > 0) battle.playerCd -= 1;
    if (battle.aiCd > 0) battle.aiCd -= 1;
    appendBattleLog(lines.join('\n'));
    updateBattleHud();
    if (battle.playerHp <= 0 || battle.aiHp <= 0 || battle.round >= GAME_MAX_ROUNDS) {
      finishBattle();
      return;
    }
    battle.round += 1;
    battle.busy = false;
    updateBattleHud();
    setBattleButtons(true);
  }

  function finishBattle() {
    var battle = gameState.battle;
    battle.over = true;
    battle.busy = false;
    setBattleButtons(false);
    updateBattleHud();
    var result;
    if (battle.playerHp <= 0 && battle.aiHp <= 0) result = 'draw';
    else if (battle.aiHp <= 0) result = 'win';
    else if (battle.playerHp <= 0) result = 'lose';
    else result = battle.playerHp === battle.aiHp ? 'draw' : battle.playerHp > battle.aiHp ? 'win' : 'lose';
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！月月还剩 ' + battle.aiHp + ' 点血。';
      chat = '刚刚跟你打街机，我赢了，你只剩 ' + battle.aiHp + ' 血，服不服？';
    } else if (result === 'lose') {
      summary = '月月赢了。你还剩 ' + battle.playerHp + ' 点血。';
      chat = '刚刚跟你打街机我输了，我还剩 ' + battle.playerHp + ' 血，下次再来。';
    } else {
      summary = '平局，谁也没服谁。';
      chat = '刚刚跟你打街机打成平手，谁也没赢，再来一局？';
    }
    appendBattleLog('\n' + summary);
    showGameResult(summary, chat, {
      name: '街机对战',
      result: result,
      score: battle.playerHp + ':' + battle.aiHp
    });
  }

  // ---------------------------------------------------------- 猜拳
  function startRps() {
    var rps = gameState.rps;
    rps.player = 0;
    rps.ai = 0;
    rps.round = 1;
    rps.busy = false;
    rps.over = false;
    $('game-rps-player').textContent = '0';
    $('game-rps-ai').textContent = '0';
    $('game-rps-round').textContent = '第 1 局';
    $('game-rps-log').textContent = '选石头、剪刀或布。';
    setRpsButtons(true);
  }

  function setRpsButtons(enabled) {
    Array.prototype.forEach.call(document.querySelectorAll('#game-rps-step [data-rps]'), function (button) {
      button.disabled = !enabled;
    });
  }

  function chooseRps(choice) {
    var rps = gameState.rps;
    if (rps.busy || rps.over) return;
    rps.busy = true;
    setRpsButtons(false);
    var choices = ['rock', 'paper', 'scissors'];
    var aiChoice = choices[Math.floor(Math.random() * choices.length)];
    var playerLabel = RPS_LABELS[choice];
    var aiLabel = RPS_LABELS[aiChoice];
    var result;
    if (choice === aiChoice) {
      result = 'draw';
    } else if (
      (choice === 'rock' && aiChoice === 'scissors') ||
      (choice === 'scissors' && aiChoice === 'paper') ||
      (choice === 'paper' && aiChoice === 'rock')
    ) {
      result = 'player';
    } else {
      result = 'ai';
    }
    if (result === 'player') {
      rps.player += 1;
      $('game-rps-player').textContent = String(rps.player);
    } else if (result === 'ai') {
      rps.ai += 1;
      $('game-rps-ai').textContent = String(rps.ai);
    }
    $('game-rps-round').textContent = '第 ' + rps.round + ' 局';
    var line = '你出' + playerLabel + '，月月出' + aiLabel + '。' +
      (result === 'draw' ? '平局。' : result === 'player' ? '你赢一局。' : '月月赢一局。');

    if (rps.player >= 2 || rps.ai >= 2) {
      rps.over = true;
      rps.busy = false;
      var win = rps.player >= 2;
      var summary = win ? '你赢了！最终比分 ' + rps.player + ' : ' + rps.ai + '。'
        : '月月赢了，最终比分 ' + rps.player + ' : ' + rps.ai + '。';
      var chat = win ? '刚刚跟你猜拳我赢了，最终 ' + rps.player + ' : ' + rps.ai + '，服不服？'
        : '刚刚跟你猜拳我输了，最终 ' + rps.ai + ' : ' + rps.player + '，再来一局？';
      $('game-rps-log').textContent = line + '\n' + summary;
      showGameResult(summary, chat, {
        name: '猜拳',
        result: win ? 'win' : 'lose',
        score: rps.player + ':' + rps.ai
      });
      return;
    }
    rps.round += 1;
    rps.busy = false;
    $('game-rps-log').textContent = line;
    $('game-rps-round').textContent = '第 ' + rps.round + ' 局';
    setRpsButtons(true);
  }

  // ---------------------------------------------------------- 打地鼠
  function startMole() {
    var mole = gameState.mole;
    stopMoleTimers();
    mole.score = 0;
    mole.aiScore = 5 + Math.floor(Math.random() * 5);
    mole.timeLeft = 8;
    mole.active = false;
    mole.over = false;
    $('game-mole-player').textContent = '0';
    $('game-mole-ai').textContent = String(mole.aiScore);
    $('game-mole-time').textContent = '8.0s';
    $('game-mole-status').textContent = '准备打地鼠，月月已经准备好了。';
    $('game-mole-start').classList.remove('hidden');
    $('game-mole-start').disabled = false;
    renderMoleGrid();
  }

  function renderMoleGrid() {
    var grid = $('game-mole-grid');
    grid.innerHTML = '';
    for (var i = 0; i < 9; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-mole-cell';
      button.setAttribute('data-cell', String(i));
      grid.appendChild(button);
    }
  }

  function stopMoleTimers() {
    var mole = gameState.mole;
    if (mole.tickTimer) clearInterval(mole.tickTimer);
    if (mole.spawnTimer) clearInterval(mole.spawnTimer);
    if (mole.endTimer) clearTimeout(mole.endTimer);
    mole.tickTimer = 0;
    mole.spawnTimer = 0;
    mole.endTimer = 0;
  }

  function startMoleRound() {
    var mole = gameState.mole;
    if (mole.active || mole.over) return;
    stopMoleTimers();
    mole.active = true;
    mole.score = 0;
    mole.timeLeft = 8;
    $('game-mole-player').textContent = '0';
    $('game-mole-status').textContent = '开始！快打地鼠。';
    $('game-mole-start').classList.add('hidden');
    spawnMole();
    mole.spawnTimer = window.setInterval(spawnMole, 650);
    mole.tickTimer = window.setInterval(function () {
      mole.timeLeft = Math.max(0, mole.timeLeft - 0.1);
      $('game-mole-time').textContent = mole.timeLeft.toFixed(1) + 's';
    }, 100);
    mole.endTimer = window.setTimeout(endMoleRound, 8000);
  }

  function spawnMole() {
    var mole = gameState.mole;
    if (!mole.active) return;
    Array.prototype.forEach.call(document.querySelectorAll('.game-mole-cell'), function (button) {
      button.classList.remove('active');
      button.textContent = '';
    });
    var cells = document.querySelectorAll('.game-mole-cell');
    if (!cells.length) return;
    var target = cells[Math.floor(Math.random() * cells.length)];
    target.classList.add('active');
    target.textContent = '🐹';
  }

  function hitMole(event) {
    var mole = gameState.mole;
    if (!mole.active) return;
    var cell = event.target.closest('.game-mole-cell');
    if (!cell || !cell.classList.contains('active')) return;
    mole.score += 1;
    $('game-mole-player').textContent = String(mole.score);
    spawnMole();
  }

  function endMoleRound() {
    var mole = gameState.mole;
    if (!mole.active) return;
    mole.active = false;
    stopMoleTimers();
    Array.prototype.forEach.call(document.querySelectorAll('.game-mole-cell'), function (button) {
      button.classList.remove('active');
      button.textContent = '';
    });
    mole.over = true;
    var win = mole.score > mole.aiScore;
    var draw = mole.score === mole.aiScore;
    var summary = win ? '你赢了！你打了 ' + mole.score + ' 只，月月打了 ' + mole.aiScore + ' 只。'
      : draw ? '平局，你们都打了 ' + mole.score + ' 只。'
        : '月月赢了。你打了 ' + mole.score + ' 只，月月打了 ' + mole.aiScore + ' 只。';
    var chat = win ? '刚刚跟你打地鼠我赢了，我打了 ' + mole.score + ' 只，你才 ' + mole.aiScore + ' 只。'
      : draw ? '刚刚跟你打地鼠打成平手，都打了 ' + mole.score + ' 只，再来？'
        : '刚刚跟你打地鼠我输了，你打了 ' + mole.aiScore + ' 只，我只有 ' + mole.score + ' 只。';
    $('game-mole-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '打地鼠',
      result: win ? 'win' : draw ? 'draw' : 'lose',
      score: mole.score + ':' + mole.aiScore
    });
  }

  // ---------------------------------------------------------- 井字棋
  var TTT_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6]
  ];

  function startTtt() {
    var ttt = gameState.ttt;
    if (ttt.timer) {
      clearTimeout(ttt.timer);
      ttt.timer = 0;
    }
    ttt.board = ['', '', '', '', '', '', '', '', ''];
    ttt.busy = false;
    ttt.over = false;
    renderTtt();
    $('game-ttt-status').textContent = '你执 X，月月执 O，你先手。';
    setTttButtons(true);
  }

  function renderTtt() {
    var board = $('game-ttt-board');
    board.innerHTML = '';
    for (var i = 0; i < 9; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-ttt-cell' + (gameState.ttt.board[i] ? ' filled' : '');
      button.setAttribute('data-cell', String(i));
      button.textContent = gameState.ttt.board[i];
      board.appendChild(button);
    }
  }

  function setTttButtons(enabled) {
    Array.prototype.forEach.call(document.querySelectorAll('.game-ttt-cell'), function (button) {
      button.disabled = !enabled || Boolean(gameState.ttt.board[Number(button.getAttribute('data-cell'))]);
    });
  }

  function findTttWinner(mark) {
    for (var i = 0; i < TTT_LINES.length; i++) {
      var line = TTT_LINES[i];
      if (
        gameState.ttt.board[line[0]] === mark &&
        gameState.ttt.board[line[1]] === mark &&
        gameState.ttt.board[line[2]] === mark
      ) {
        return true;
      }
    }
    return false;
  }

  function tttBoardFull() {
    for (var i = 0; i < 9; i++) {
      if (!gameState.ttt.board[i]) return false;
    }
    return true;
  }

  function tttPlayerMove(index) {
    var ttt = gameState.ttt;
    if (ttt.busy || ttt.over || ttt.board[index]) return;
    ttt.board[index] = 'X';
    renderTtt();
    if (findTttWinner('X')) {
      finishTtt('win');
      return;
    }
    if (tttBoardFull()) {
      finishTtt('draw');
      return;
    }
    ttt.busy = true;
    $('game-ttt-status').textContent = '月月正在想……';
    ttt.timer = window.setTimeout(function () {
      tttAiMove();
    }, 380);
  }

  function tttAiMove() {
    var ttt = gameState.ttt;
    if (ttt.over) return;
    var move = pickTttMove();
    if (move < 0) {
      ttt.busy = false;
      return;
    }
    ttt.board[move] = 'O';
    renderTtt();
    if (findTttWinner('O')) {
      finishTtt('lose');
      return;
    }
    if (tttBoardFull()) {
      finishTtt('draw');
      return;
    }
    ttt.busy = false;
    setTttButtons(true);
    $('game-ttt-status').textContent = '轮到你落子。';
  }

  function pickTttMove() {
    var board = gameState.ttt.board;
    var i;
    var empty = [];
    for (i = 0; i < 9; i++) if (board[i] === '') empty.push(i);
    if (!empty.length) return -1;
    // 月月偶尔走神，给玩家留出赢棋机会。
    if (Math.random() < 0.42) {
      return empty[Math.floor(Math.random() * empty.length)];
    }
    for (i = 0; i < 9; i++) if (board[i] === '') { board[i] = 'O'; if (findTttWinner('O')) { board[i] = ''; return i; } board[i] = ''; }
    for (i = 0; i < 9; i++) if (board[i] === '') { board[i] = 'X'; if (findTttWinner('X')) { board[i] = ''; return i; } board[i] = ''; }
    if (board[4] === '') return 4;
    var corners = [0, 2, 6, 8].filter(function (index) { return board[index] === ''; });
    if (corners.length) return corners[Math.floor(Math.random() * corners.length)];
    return empty[Math.floor(Math.random() * empty.length)];
  }

  function finishTtt(result) {
    var ttt = gameState.ttt;
    ttt.over = true;
    ttt.busy = false;
    if (ttt.timer) {
      clearTimeout(ttt.timer);
      ttt.timer = 0;
    }
    renderTtt();
    setTttButtons(false);
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！你连成一线了。';
      chat = '刚刚跟你下井字棋我赢了，我连成一线了，再来一局？';
    } else if (result === 'lose') {
      summary = '月月赢了，她连成一线了。';
      chat = '刚刚跟你下井字棋我输了，你连成一线了，再来一局？';
    } else {
      summary = '平局，棋盘满了，谁也没连成线。';
      chat = '刚刚跟你下井字棋打成平手，棋盘满了，再来一局？';
    }
    $('game-ttt-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '井字棋',
      result: result,
      score: ''
    });
  }

  // ---------------------------------------------------------- 翻牌记忆
  var MEMORY_SYMBOLS = ['🐳', '🐟', '🦊', '🍙', '🎮', '🍰'];

  function startMemory() {
    var memory = gameState.memory;
    stopMemoryTimer();
    memory.deck = [];
    MEMORY_SYMBOLS.concat(MEMORY_SYMBOLS).forEach(function (symbol) {
      memory.deck.push({ symbol: symbol, faceUp: false, matched: false });
    });
    for (var i = memory.deck.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = memory.deck[i];
      memory.deck[i] = memory.deck[j];
      memory.deck[j] = tmp;
    }
    memory.flipped = [];
    memory.matched = 0;
    memory.moves = 0;
    memory.aiMoves = 7 + Math.floor(Math.random() * 4);
    memory.busy = false;
    memory.over = false;
    $('game-memory-moves').textContent = '0';
    $('game-memory-ai').textContent = String(memory.aiMoves);
    $('game-memory-status').textContent = '点开两张牌，找出相同图案。月月说 ' + memory.aiMoves + ' 步内能完成。';
    renderMemoryGrid();
  }

  function renderMemoryGrid() {
    var grid = $('game-memory-grid');
    grid.innerHTML = '';
    gameState.memory.deck.forEach(function (card, index) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-memory-card' +
        (card.faceUp || card.matched ? ' flipped' : '') +
        (card.matched ? ' matched' : '');
      button.setAttribute('data-index', String(index));
      button.textContent = card.faceUp || card.matched ? card.symbol : '?';
      button.disabled = card.matched;
      grid.appendChild(button);
    });
  }

  function memoryClick(index) {
    var memory = gameState.memory;
    if (memory.busy || memory.over) return;
    var card = memory.deck[index];
    if (!card || card.faceUp || card.matched) return;
    card.faceUp = true;
    memory.flipped.push(index);
    renderMemoryGrid();
    if (memory.flipped.length < 2) return;
    memory.moves += 1;
    $('game-memory-moves').textContent = String(memory.moves);
    var first = memory.flipped[0];
    var second = memory.flipped[1];
    if (memory.deck[first].symbol === memory.deck[second].symbol) {
      memory.deck[first].matched = true;
      memory.deck[second].matched = true;
      memory.matched += 2;
      memory.flipped = [];
      memory.busy = false;
      renderMemoryGrid();
      if (memory.matched >= memory.deck.length) {
        finishMemory();
      } else {
        $('game-memory-status').textContent = '配对成功，继续。';
      }
      return;
    }
    memory.busy = true;
    memory.timer = window.setTimeout(function () {
      memory.deck[first].faceUp = false;
      memory.deck[second].faceUp = false;
      memory.flipped = [];
      memory.busy = false;
      memory.timer = 0;
      renderMemoryGrid();
      $('game-memory-status').textContent = '没配上，再试试。';
    }, 700);
  }

  function finishMemory() {
    var memory = gameState.memory;
    memory.over = true;
    memory.busy = false;
    var win = memory.moves <= memory.aiMoves;
    var summary = win
      ? '你赢了！你用了 ' + memory.moves + ' 步，月月目标 ' + memory.aiMoves + ' 步。'
      : '月月赢了。你用了 ' + memory.moves + ' 步，超过她的 ' + memory.aiMoves + ' 步。';
    var chat = win
      ? '刚刚跟你玩翻牌记忆我赢了，我 ' + memory.moves + ' 步就翻完了，还挺快。'
      : '刚刚跟你玩翻牌记忆我输了，我用了 ' + memory.moves + ' 步，你给的目标是 ' + memory.aiMoves + ' 步。';
    $('game-memory-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '翻牌记忆',
      result: win ? 'win' : 'lose',
      score: memory.moves + ':' + memory.aiMoves
    });
  }

  // ---------------------------------------------------------- 猜数字
  function startGuess() {
    var guess = gameState.guess;
    guess.target = 1 + Math.floor(Math.random() * 100);
    guess.attempts = 0;
    guess.over = false;
    $('game-guess-input').disabled = false;
    $('game-guess-submit').disabled = false;
    $('game-guess-input').value = '';
    $('game-guess-range').textContent = '范围 1 – 100';
    $('game-guess-status').textContent = '月月想好数字了，你猜。还剩 7 次机会。';
    window.setTimeout(function () {
      var input = $('game-guess-input');
      if (input) input.focus();
    }, 60);
  }

  function submitGuess() {
    var guess = gameState.guess;
    if (guess.over) return;
    var input = $('game-guess-input');
    var value = Number(input.value);
    if (!Number.isInteger(value) || value < 1 || value > 100) {
      $('game-guess-status').textContent = '请输入 1–100 的整数。';
      return;
    }
    guess.attempts += 1;
    input.value = '';
    if (value === guess.target) {
      finishGuess(true);
      return;
    }
    if (guess.attempts >= guess.max) {
      finishGuess(false);
      return;
    }
    var hint = value < guess.target ? '小了' : '大了';
    $('game-guess-range').textContent = '范围 1 – 100';
    $('game-guess-status').textContent =
      '你猜 ' + value + '，' + hint + '。还剩 ' + (guess.max - guess.attempts) + ' 次机会。';
    input.focus();
  }

  function finishGuess(win) {
    var guess = gameState.guess;
    guess.over = true;
    $('game-guess-input').disabled = true;
    $('game-guess-submit').disabled = true;
    var summary;
    var chat;
    if (win) {
      summary = '猜中了！答案是 ' + guess.target + '，你用了 ' + guess.attempts + ' 次。';
      chat = '刚刚跟你玩猜数字，你选的 ' + guess.target + ' 被我 ' + guess.attempts + ' 次就猜中了，运气不错。';
    } else {
      summary = '没猜中。月月选的数字是 ' + guess.target + '，7 次机会用完了。';
      chat = '刚刚跟你玩猜数字我输了，你选的 ' + guess.target + ' 我 7 次都没猜到，下次再练练。';
    }
    $('game-guess-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '猜数字',
      result: win ? 'win' : 'lose',
      score: guess.attempts + ' 次'
    });
  }

  // ---------------------------------------------------------- 比大小
  function startDice() {
    var dice = gameState.dice;
    dice.player = 0;
    dice.ai = 0;
    dice.round = 1;
    dice.busy = false;
    dice.over = false;
    $('game-dice-player').textContent = '0';
    $('game-dice-ai').textContent = '0';
    $('game-dice-player-face').textContent = '?';
    $('game-dice-ai-face').textContent = '?';
    $('game-dice-round').textContent = '第 1 局';
    $('game-dice-status').textContent = '掷骰子比大小，三局两胜。';
    $('game-dice-roll').disabled = false;
  }

  function rollDice() {
    var dice = gameState.dice;
    if (dice.busy || dice.over) return;
    dice.busy = true;
    $('game-dice-roll').disabled = true;
    var playerRoll = 1 + Math.floor(Math.random() * 6);
    var aiRoll = 1 + Math.floor(Math.random() * 6);
    $('game-dice-player-face').textContent = String(playerRoll);
    $('game-dice-ai-face').textContent = String(aiRoll);
    var line;
    if (playerRoll > aiRoll) {
      dice.player += 1;
      line = '你掷出 ' + playerRoll + '，月月掷出 ' + aiRoll + '，你赢一局。';
    } else if (playerRoll < aiRoll) {
      dice.ai += 1;
      line = '你掷出 ' + playerRoll + '，月月掷出 ' + aiRoll + '，月月赢一局。';
    } else {
      line = '都是 ' + playerRoll + ' 点，平局，重掷。';
    }
    $('game-dice-player').textContent = String(dice.player);
    $('game-dice-ai').textContent = String(dice.ai);
    if (dice.player >= 2 || dice.ai >= 2) {
      dice.over = true;
      dice.busy = false;
      var win = dice.player >= 2;
      var summary = win
        ? '你赢了！最终比分 ' + dice.player + ' : ' + dice.ai + '。'
        : '月月赢了，最终比分 ' + dice.player + ' : ' + dice.ai + '。';
      var chat = win
        ? '刚刚跟你掷骰子我赢了，比分 ' + dice.player + ' : ' + dice.ai + '，运气也是实力。'
        : '刚刚跟你掷骰子我输了，比分 ' + dice.ai + ' : ' + dice.player + '，你运气不错。';
      $('game-dice-status').textContent = line + '\n' + summary;
      showGameResult(summary, chat, {
        name: '比大小',
        result: win ? 'win' : 'lose',
        score: dice.player + ':' + dice.ai
      });
      return;
    }
    dice.round += 1;
    dice.busy = false;
    $('game-dice-round').textContent = '第 ' + dice.round + ' 局';
    $('game-dice-status').textContent = line;
    $('game-dice-roll').disabled = false;
  }

  // ---------------------------------------------------------- 五子棋
  var GOMOKU_SIZE = 15;
  var GOMOKU_DIRS = [[1, 0], [0, 1], [1, 1], [1, -1]];

  function startGomoku() {
    var gomoku = gameState.gomoku;
    stopGomokuTimer();
    gomoku.board = [];
    for (var i = 0; i < GOMOKU_SIZE * GOMOKU_SIZE; i++) gomoku.board.push('');
    gomoku.busy = false;
    gomoku.over = false;
    renderGomoku();
    $('game-gomoku-status').textContent = '你执 X，月月执 O，你先手。';
  }

  function renderGomoku() {
    var board = $('game-gomoku-board');
    board.innerHTML = '';
    for (var i = 0; i < GOMOKU_SIZE * GOMOKU_SIZE; i++) {
      var button = document.createElement('button');
      var value = gameState.gomoku.board[i];
      button.type = 'button';
      button.className = 'game-gomoku-cell' +
        (value === 'X' ? ' x' : value === 'O' ? ' o' : '') +
        (value ? ' filled' : '');
      button.setAttribute('data-index', String(i));
      button.textContent = value;
      board.appendChild(button);
    }
  }

  function gomokuInside(x, y) {
    return x >= 0 && x < GOMOKU_SIZE && y >= 0 && y < GOMOKU_SIZE;
  }

  function gomokuWinner(index, mark) {
    var board = gameState.gomoku.board;
    var x = index % GOMOKU_SIZE;
    var y = Math.floor(index / GOMOKU_SIZE);
    for (var d = 0; d < GOMOKU_DIRS.length; d++) {
      var dx = GOMOKU_DIRS[d][0];
      var dy = GOMOKU_DIRS[d][1];
      var count = 1;
      for (var sign = -1; sign <= 1; sign += 2) {
        var nx = x + dx * sign;
        var ny = y + dy * sign;
        while (gomokuInside(nx, ny) && board[ny * GOMOKU_SIZE + nx] === mark) {
          count += 1;
          nx += dx * sign;
          ny += dy * sign;
        }
      }
      if (count >= 5) return true;
    }
    return false;
  }

  function gomokuBoardFull() {
    return gameState.gomoku.board.every(function (cell) { return Boolean(cell); });
  }

  function gomokuPlayerMove(index) {
    var gomoku = gameState.gomoku;
    if (gomoku.busy || gomoku.over || gomoku.board[index]) return;
    gomoku.board[index] = 'X';
    renderGomoku();
    if (gomokuWinner(index, 'X')) {
      finishGomoku('win');
      return;
    }
    if (gomokuBoardFull()) {
      finishGomoku('draw');
      return;
    }
    gomoku.busy = true;
    $('game-gomoku-status').textContent = '月月正在落子……';
    gomoku.timer = window.setTimeout(gomokuAiMove, 380);
  }

  function gomokuPotential(index, mark) {
    var board = gameState.gomoku.board;
    var x = index % GOMOKU_SIZE;
    var y = Math.floor(index / GOMOKU_SIZE);
    var total = 0;
    for (var d = 0; d < GOMOKU_DIRS.length; d++) {
      var dx = GOMOKU_DIRS[d][0];
      var dy = GOMOKU_DIRS[d][1];
      var count = 1;
      var openEnds = 0;
      for (var sign = -1; sign <= 1; sign += 2) {
        var nx = x + dx * sign;
        var ny = y + dy * sign;
        while (gomokuInside(nx, ny) && board[ny * GOMOKU_SIZE + nx] === mark) {
          count += 1;
          nx += dx * sign;
          ny += dy * sign;
        }
        if (gomokuInside(nx, ny) && board[ny * GOMOKU_SIZE + nx] === '') {
          openEnds += 1;
        }
      }
      if (count >= 5) return 1000000000;
      if (count === 4) total += openEnds >= 2 ? 3000000 : openEnds === 1 ? 300000 : 0;
      else if (count === 3) total += openEnds >= 2 ? 60000 : openEnds === 1 ? 6000 : 0;
      else if (count === 2) total += openEnds >= 2 ? 1200 : openEnds === 1 ? 160 : 0;
    }
    return total;
  }

  function gomokuCandidates() {
    var board = gameState.gomoku.board;
    var candidates = [];
    var hasStone = false;
    for (var i = 0; i < board.length; i++) {
      if (board[i]) {
        hasStone = true;
        break;
      }
    }
    if (!hasStone) return [Math.floor(GOMOKU_SIZE * GOMOKU_SIZE / 2)];
    for (var index = 0; index < board.length; index++) {
      if (board[index]) continue;
      var x = index % GOMOKU_SIZE;
      var y = Math.floor(index / GOMOKU_SIZE);
      var near = false;
      for (var dy = -2; dy <= 2 && !near; dy++) {
        for (var dx = -2; dx <= 2; dx++) {
          var nx = x + dx;
          var ny = y + dy;
          if (!gomokuInside(nx, ny)) continue;
          if (board[ny * GOMOKU_SIZE + nx]) {
            near = true;
            break;
          }
        }
      }
      if (near) candidates.push(index);
    }
    return candidates;
  }

  function pickGomokuMove() {
    var board = gameState.gomoku.board;
    var candidates = gomokuCandidates();
    if (!candidates.length) return -1;
    // 先走一步随手的棋，月月不再是每一手都算到底。
    if (Math.random() < 0.45) {
      return candidates[Math.floor(Math.random() * candidates.length)];
    }
    var i;
    for (i = 0; i < candidates.length; i++) {
      if (gomokuPotential(candidates[i], 'O') >= 1000000000) return candidates[i];
    }
    for (i = 0; i < candidates.length; i++) {
      if (gomokuPotential(candidates[i], 'X') >= 1000000000) return candidates[i];
    }
    var best = candidates[0];
    var bestScore = -Infinity;
    for (i = 0; i < candidates.length; i++) {
      var index = candidates[i];
      var attack = gomokuPotential(index, 'O');
      var defense = gomokuPotential(index, 'X');
      var x = index % GOMOKU_SIZE;
      var y = Math.floor(index / GOMOKU_SIZE);
      var centerBonus = 7 - (Math.abs(x - 7) + Math.abs(y - 7));
      var score = attack * 1.15 + defense + centerBonus * 4;
      if (score > bestScore) {
        bestScore = score;
        best = index;
      }
    }
    return best;
  }

  function gomokuAiMove() {
    var gomoku = gameState.gomoku;
    if (gomoku.over) return;
    var index = pickGomokuMove();
    if (index < 0) {
      gomoku.busy = false;
      finishGomoku('draw');
      return;
    }
    gomoku.board[index] = 'O';
    renderGomoku();
    if (gomokuWinner(index, 'O')) {
      finishGomoku('lose');
      return;
    }
    if (gomokuBoardFull()) {
      finishGomoku('draw');
      return;
    }
    gomoku.busy = false;
    $('game-gomoku-status').textContent = '轮到你落子。';
  }

  function finishGomoku(result) {
    var gomoku = gameState.gomoku;
    gomoku.over = true;
    gomoku.busy = false;
    stopGomokuTimer();
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！你先连成了五子。';
      chat = '刚刚跟你下五子棋我赢了，我先连成五子，服不服？';
    } else if (result === 'lose') {
      summary = '月月赢了，她先连成了五子。';
      chat = '刚刚跟你下五子棋我输了，你先连成五子，再来一局？';
    } else {
      summary = '平局，棋盘满了也没人连成五子。';
      chat = '刚刚跟你下五子棋打成平手，棋盘都满了，再来一局？';
    }
    $('game-gomoku-status').textContent = summary;
    showGameResult(summary, chat, {
      name: '五子棋',
      result: result,
      score: ''
    });
  }

  // ---------------------------------------------------------- 四子棋
  function startConnect4() {
    var game = gameState.connect4;
    game.board = [];
    for (var i = 0; i < 42; i++) game.board.push(0);
    game.busy = false;
    game.over = false;
    stopConnect4Timer();
    renderConnect4('你执红，月月执黄，点一列落子。');
  }

  function renderConnect4(message) {
    var board = $('game-connect4-board');
    if (!board) return;
    var game = gameState.connect4;
    board.innerHTML = '';
    for (var i = 0; i < 42; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-connect4-cell' +
        (game.board[i] === 1 ? ' player' : game.board[i] === 2 ? ' ai' : '');
      button.setAttribute('data-col', String(i % 7));
      button.setAttribute('aria-label', '第 ' + ((i % 7) + 1) + ' 列');
      button.disabled = Boolean(game.board[i]) || game.busy || game.over;
      board.appendChild(button);
    }
    if (message) $('game-connect4-status').textContent = message;
  }

  function connect4Drop(who, col) {
    var board = gameState.connect4.board;
    for (var row = 5; row >= 0; row--) {
      var index = row * 7 + col;
      if (!board[index]) {
        board[index] = who;
        return row;
      }
    }
    return -1;
  }

  function connect4Winner(who) {
    var board = gameState.connect4.board;
    var directions = [[1, 0], [0, 1], [1, 1], [1, -1]];
    for (var row = 0; row < 6; row++) {
      for (var col = 0; col < 7; col++) {
        if (board[row * 7 + col] !== who) continue;
        for (var d = 0; d < directions.length; d++) {
          var dr = directions[d][0];
          var dc = directions[d][1];
          var count = 1;
          for (var step = 1; step < 4; step++) {
            var r = row + dr * step;
            var c = col + dc * step;
            if (r < 0 || r > 5 || c < 0 || c > 6 || board[r * 7 + c] !== who) break;
            count++;
          }
          if (count >= 4) return true;
        }
      }
    }
    return false;
  }

  function connect4LegalCols() {
    var board = gameState.connect4.board;
    var cols = [];
    for (var col = 0; col < 7; col++) {
      if (!board[col]) cols.push(col);
    }
    return cols;
  }

  function connect4WinningCol(who) {
    var game = gameState.connect4;
    var cols = connect4LegalCols();
    for (var i = 0; i < cols.length; i++) {
      var col = cols[i];
      var row = connect4Drop(who, col);
      if (row >= 0) {
        var win = connect4Winner(who);
        game.board[row * 7 + col] = 0;
        if (win) return col;
      }
    }
    return -1;
  }

  function connect4AiMove() {
    var game = gameState.connect4;
    if (game.over) return;
    var col = -1;
    // 月月会漏看一部分胜点和堵点，玩家更容易连成四子。
    if (Math.random() < 0.5) col = connect4WinningCol(2);
    if (col < 0 && Math.random() < 0.5) col = connect4WinningCol(1);
    if (col < 0) {
      var legal = connect4LegalCols();
      var order = [3, 2, 4, 1, 5, 0, 6];
      if (Math.random() < 0.45) {
        col = legal[Math.floor(Math.random() * legal.length)];
      } else {
        for (var i = 0; i < order.length; i++) {
          if (legal.indexOf(order[i]) >= 0) { col = order[i]; break; }
        }
      }
    }
    if (col == null || col < 0) {
      finishConnect4('draw');
      return;
    }
    connect4Drop(2, col);
    renderConnect4();
    if (connect4Winner(2)) {
      finishConnect4('lose');
      return;
    }
    game.busy = false;
    if (!connect4LegalCols().length) {
      finishConnect4('draw');
      return;
    }
    renderConnect4('轮到你落子。');
  }

  function connect4PlayerMove(col) {
    var game = gameState.connect4;
    if (game.busy || game.over) return;
    if (connect4Drop(1, col) < 0) return;
    renderConnect4();
    if (connect4Winner(1)) {
      finishConnect4('win');
      return;
    }
    if (!connect4LegalCols().length) {
      finishConnect4('draw');
      return;
    }
    game.busy = true;
    renderConnect4('月月在盯着棋盘想……');
    stopConnect4Timer();
    game.timer = window.setTimeout(connect4AiMove, 420);
  }

  function finishConnect4(result) {
    var game = gameState.connect4;
    game.over = true;
    game.busy = false;
    stopConnect4Timer();
    var summary;
    var chat;
    if (result === 'win') {
      summary = '你赢了！先连成了四个。';
      chat = '刚刚四子棋我赢了，先连成四子，服不服？';
    } else if (result === 'lose') {
      summary = '月月赢了，她先连成了四个。';
      chat = '刚刚四子棋我输了，你先连成四子，再来一局？';
    } else {
      summary = '平局，棋盘满了也没人连成四个。';
      chat = '刚刚四子棋打成平手，棋盘都满了，再来一局？';
    }
    renderConnect4(summary);
    showGameResult(summary, chat, { name: '四子棋', result: result, score: '' });
  }

  // ---------------------------------------------------------- 黑白棋
  var REVERSI_DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];

  function startReversi() {
    var game = gameState.reversi;
    game.board = [];
    for (var i = 0; i < 64; i++) game.board.push(0);
    game.board[27] = 2;
    game.board[28] = 1;
    game.board[35] = 1;
    game.board[36] = 2;
    game.busy = false;
    game.over = false;
    stopReversiTimer();
    updateReversiScores();
    renderReversi('你执黑先手，点一个能夹住白棋的位置。');
  }

  function reversiFlips(board, index, who) {
    if (index < 0 || index >= 64 || board[index]) return [];
    var row = Math.floor(index / 8);
    var col = index % 8;
    var opponent = who === 1 ? 2 : 1;
    var flips = [];
    REVERSI_DIRECTIONS.forEach(function (dir) {
      var r = row + dir[0];
      var c = col + dir[1];
      var line = [];
      while (r >= 0 && r < 8 && c >= 0 && c < 8 && board[r * 8 + c] === opponent) {
        line.push(r * 8 + c);
        r += dir[0];
        c += dir[1];
      }
      if (line.length && r >= 0 && r < 8 && c >= 0 && c < 8 && board[r * 8 + c] === who) {
        flips = flips.concat(line);
      }
    });
    return flips;
  }

  function reversiMoves(who) {
    var moves = {};
    for (var i = 0; i < 64; i++) {
      var flips = reversiFlips(gameState.reversi.board, i, who);
      if (flips.length) moves[i] = flips;
    }
    return moves;
  }

  function updateReversiScores() {
    var board = gameState.reversi.board;
    var player = 0;
    var ai = 0;
    for (var i = 0; i < 64; i++) {
      if (board[i] === 1) player++;
      else if (board[i] === 2) ai++;
    }
    $('game-reversi-player').textContent = String(player);
    $('game-reversi-ai').textContent = String(ai);
  }

  function renderReversi(message) {
    var node = $('game-reversi-board');
    if (!node) return;
    var game = gameState.reversi;
    var moves = game.busy || game.over ? {} : reversiMoves(1);
    node.innerHTML = '';
    for (var i = 0; i < 64; i++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'game-reversi-cell' +
        (game.board[i] === 1 ? ' player' : game.board[i] === 2 ? ' ai' : '') +
        (moves[i] ? ' hint' : '');
      button.setAttribute('data-index', String(i));
      button.setAttribute('aria-label', '第 ' + (Math.floor(i / 8) + 1) + ' 行第 ' + (i % 8 + 1) + ' 列');
      button.disabled = !moves[i];
      node.appendChild(button);
    }
    updateReversiScores();
    if (message) $('game-reversi-status').textContent = message;
  }

  function reversiApply(index, who) {
    var board = gameState.reversi.board;
    var flips = reversiFlips(board, index, who);
    if (!flips.length) return false;
    board[index] = who;
    flips.forEach(function (flip) { board[flip] = who; });
    return true;
  }

  function reversiAiMove() {
    var game = gameState.reversi;
    if (game.over) return;
    var moves = reversiMoves(2);
    var keys = Object.keys(moves);
    if (!keys.length) {
      if (!Object.keys(reversiMoves(1)).length) finishReversi();
      else {
        game.busy = false;
        renderReversi('月月没有位置可下，轮到你了。');
      }
      return;
    }
    var best = keys[0];
    if (Math.random() < 0.45) {
      best = keys[Math.floor(Math.random() * keys.length)];
    } else {
      var bestScore = -100;
      keys.forEach(function (key) {
        var index = Number(key);
        var row = Math.floor(index / 8);
        var col = index % 8;
        var corner = (row === 0 || row === 7) && (col === 0 || col === 7);
        var score = moves[key].length + (corner ? 3 : 0) + Math.random();
        if (score > bestScore) { bestScore = score; best = key; }
      });
    }
    reversiApply(Number(best), 2);
    game.busy = false;
    var playerMoves = reversiMoves(1);
    renderReversi(Object.keys(playerMoves).length ? '轮到你落子。' : '你没有位置可下，月月继续。');
    if (!Object.keys(reversiMoves(1)).length && !Object.keys(moves).length) {
      finishReversi();
    } else if (!Object.keys(playerMoves).length) {
      game.busy = true;
      stopReversiTimer();
      game.timer = window.setTimeout(reversiAiMove, 500);
    }
  }

  function reversiPlayerMove(index) {
    var game = gameState.reversi;
    if (game.busy || game.over) return;
    if (!reversiApply(index, 1)) return;
    game.busy = true;
    renderReversi('月月在翻棋……');
    if (!Object.keys(reversiMoves(2)).length) {
      if (!Object.keys(reversiMoves(1)).length) finishReversi();
      else {
        game.busy = false;
        renderReversi('月月没有位置可下，轮到你了。');
      }
      return;
    }
    stopReversiTimer();
    game.timer = window.setTimeout(reversiAiMove, 480);
  }

  function finishReversi() {
    var game = gameState.reversi;
    game.over = true;
    game.busy = false;
    stopReversiTimer();
    var player = 0;
    var ai = 0;
    game.board.forEach(function (value) {
      if (value === 1) player++;
      else if (value === 2) ai++;
    });
    var result = player > ai ? 'win' : player < ai ? 'lose' : 'draw';
    var summary = result === 'win'
      ? '你赢了！黑棋 ' + player + ' 比 ' + ai + '。'
      : result === 'lose'
        ? '月月赢了，白棋 ' + ai + ' 比 ' + player + '。'
        : '平局，黑白棋 ' + player + ' 比 ' + ai + '。';
    renderReversi(summary);
    showGameResult(summary, summary + ' 再来一局？', {
      name: '黑白棋',
      result: result,
      score: player + ':' + ai
    });
  }

  function deliveryEtaText(value) {
    var target = new Date(String(value || '')).getTime();
    if (!isFinite(target)) return '';
    var minutes = Math.round((target - Date.now()) / 60000);
    if (minutes <= 0) return '即将送到';
    if (minutes < 60) return '约 ' + minutes + ' 分钟后';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return '约 ' + hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '') + '后';
  }

  function renderInventory() {
    var body = $('inventory-body');
    if (!body) return;
    var data = state.data || {};
    var money = data.money || {};
    var possessions = money.possessions || [];
    var query = String(state.inventoryQuery || '').trim().toLowerCase();
    var matchText = function (parts) {
      return !query || parts.join(' ').toLowerCase().indexOf(query) >= 0;
    };
    var allShelf = data.bookshelf || [];
    var shelf = allShelf;
    var shelfFilter = state.shelfFilter || 'all';
    if (shelfFilter === 'finished') {
      shelf = allShelf.filter(function (book) { return book.finished; });
    } else if (shelfFilter === 'reading') {
      shelf = allShelf.filter(function (book) {
        return !book.finished && Number(book.chapter || 0) > 0;
      });
    } else if (shelfFilter === 'unread') {
      shelf = allShelf.filter(function (book) {
        return !book.finished && Number(book.chapter || 0) <= 0;
      });
    }
    shelf = shelf.filter(function (book) {
      return matchText([book.title, book.genre, book.author]);
    });
    var shelfSort = state.shelfSort || 'default';
    if (shelfSort === 'title') {
      shelf = shelf.slice().sort(function (a, b) {
        return String(a.title || '').localeCompare(String(b.title || ''), 'zh');
      });
    } else if (shelfSort === 'progress') {
      shelf = shelf.slice().sort(function (a, b) {
        var aTotal = Math.max(1, Number(a.total_chapters) || 1);
        var bTotal = Math.max(1, Number(b.total_chapters) || 1);
        var aPercent = a.finished ? 100 : Number(a.chapter || 0) / aTotal;
        var bPercent = b.finished ? 100 : Number(b.chapter || 0) / bTotal;
        return bPercent - aPercent;
      });
    } else if (shelfSort === 'notes') {
      shelf = shelf.slice().sort(function (a, b) {
        return Number(b.notes || 0) - Number(a.notes || 0);
      });
    } else if (shelfSort === 'reading') {
      var readingStore = bookReadingStore();
      shelf = shelf.slice().sort(function (a, b) {
        return Number(readingStore[String(b.id || '')] || 0) -
          Number(readingStore[String(a.id || '')] || 0);
      });
    }
    state.visibleShelf = shelf;
    var deliveries = data.deliveries || [];
    deliveries = deliveries.filter(function (order) {
      return matchText([(order.goods || {}).name, (order.goods || {}).category]);
    });
    var rooms = ['卧室', '浴室', '书房', '客厅', '厨房', '阳台', '餐厅', '健身室', '玄关', '衣帽间', '画室', '影音室', '露台', '楼梯厅'];
    var icons = {
      '饮品': '🧋', '零食': '🍫', '食物': '🍜', '书籍': '📖',
      '数码': '🎧', '穿搭': '👕', '居家': '🛋️', '兴趣': '🎨',
      '礼物': '🎁', '愿望': '⭐'
    };
    var html = '';
    if (allShelf.length) {
      var finishedBooks = allShelf.filter(function (book) { return book.finished; }).length;
      var readingBooks = allShelf.filter(function (book) {
        return !book.finished && Number(book.chapter || 0) > 0;
      }).length;
      var unreadBooks = Math.max(0, allShelf.length - finishedBooks - readingBooks);
      var averageBookProgress = Math.round(allShelf.reduce(function (sum, book) {
        var totalChapters = Math.max(1, Number(book.total_chapters) || 1);
        var percent = book.finished
          ? 100
          : Math.min(100, Math.round(
            Math.max(0, Number(book.chapter) || 0) / totalChapters * 100
          ));
        return sum + percent;
      }, 0) / allShelf.length);
      var bookshelfReadingTotal = totalBookReadingLabel();
      var bookshelfReadingToday = periodBookReadingLabel(1);
      var bookshelfReadingStreak = bookReadingStreak();
      var readingGoal = Math.max(1, Number(state.readingGoal) || 30);
      var readingGoalPercent = Math.min(100, Math.round(
        periodBookReadingSeconds(1) / (readingGoal * 60) * 100
      ));
      var filterButton = function (key, label, count, always) {
        return (always || count)
          ? '<button type="button" class="shelf-filter' +
            (shelfFilter === key ? ' active' : '') +
            '" data-shelf-filter="' + key + '">' + label + ' ' + count + '</button>'
          : '';
      };
      html += '<div class="inventory-section" id="bookshelf-section"><h4>书架</h4>' +
        '<div class="bookshelf-summary">' +
        filterButton('all', '共', allShelf.length, true) +
        filterButton('finished', '读完', finishedBooks) +
        filterButton('reading', '在读', readingBooks) +
        filterButton('unread', '未读', unreadBooks) +
        '<span class="bookshelf-avg">平均 ' + averageBookProgress +
        '%</span>' +
        '</div><div class="bookshelf-tools"><select id="shelf-sort">' + [
          ['default', '默认排序'], ['title', '按书名'],
          ['progress', '按进度'], ['notes', '按笔记数'],
          ['reading', '按阅读时长']
        ].map(function (item) {
          return '<option value="' + item[0] + '"' +
            (state.shelfSort === item[0] ? ' selected' : '') + '>' +
            item[1] + '</option>';
        }).join('') + '</select>' +
          '<select id="reading-goal" title="每日阅读目标">' + [
            [15, '目标 15 分钟'], [30, '目标 30 分钟'],
            [45, '目标 45 分钟'], [60, '目标 60 分钟']
          ].map(function (item) {
            return '<option value="' + item[0] + '"' +
              (readingGoal === item[0] ? ' selected' : '') + '>' +
              item[1] + '</option>';
          }).join('') + '</select>' +
          '<button type="button" class="mini-btn" id="shelf-reading-clear">清空阅读记录</button>' +
          '<button type="button" class="mini-btn" id="shelf-export">导出书架</button>' +
          '</div>' +
          (bookshelfReadingTotal
            ? '<div class="bookshelf-reading-total">累计阅读 ' +
              escapeHtml(bookshelfReadingTotal) +
              (bookshelfReadingToday
                ? ' · 今日 ' + escapeHtml(bookshelfReadingToday)
                : '') +
              (bookshelfReadingStreak > 1
                ? ' · 连续 ' + bookshelfReadingStreak + ' 天'
                : '') +
              '</div>'
            : '') +
          '<div class="bookshelf-reading-goal" title="今日阅读目标 ' +
          readingGoal + ' 分钟"><span style="width:' + readingGoalPercent +
          '%"></span><small>' +
          (periodBookReadingSeconds(1) >= readingGoal * 60
            ? '今日目标已达成'
            : '今日目标 ' + readingGoal + ' 分钟 · ' + readingGoalPercent + '%') +
          '</small></div>' +
          '<div class="inventory-list">';
      if (!shelf.length) {
        html += '<p class="inventory-empty">' +
          (query ? '没有匹配的书。' : '这个分类下还没有书。') + '</p>';
      }
      shelf.forEach(function (book) {
        var total = Math.max(1, Number(book.total_chapters) || 1);
        var chapter = Math.max(0, Number(book.chapter) || 0);
        var percent = book.finished ? 100 : Math.round(chapter / total * 100);
        var progressText = book.finished
          ? '已读完'
          : '读到第 ' + chapter + ' / ' + total + ' 章';
        html += '<button type="button" class="inventory-book" data-book-id="' +
          escapeHtml(book.id) + '" data-book-chapter="' +
          (book.finished ? total : chapter + 1) + '">' +
          '<div class="inventory-book-title">《' + escapeHtml(book.title) + '》' +
          '<span>' + escapeHtml(book.genre || '') + '</span></div>' +
          '<div class="inventory-book-meta">' + escapeHtml(progressText) +
          (book.notes ? ' · ' + book.notes + ' 条笔记' : '') +
          (bookReadingLabel(book.id) ? ' · ' + bookReadingLabel(book.id) : '') +
          '</div>' +
          '<div class="inventory-progress"><span style="width:' + percent + '%"></span></div>' +
          '</button>';
      });
      html += '</div></div>';
    }
    if (deliveries.length) {
      html += '<div class="inventory-section"><h4>送货中</h4><div class="inventory-list">';
      deliveries.forEach(function (order) {
        var goods = order.goods || {};
        var time = String(order.deliver_at || '').slice(11, 16);
        var eta = deliveryEtaText(order.deliver_at);
        html += '<div class="inventory-item inventory-delivery">' +
          '<span class="inventory-icon">🚚</span>' +
          '<span class="inventory-name">' + escapeHtml(goods.name || '商品') +
          ' ×' + Number(order.quantity || 1) + '</span>' +
          '<span class="inventory-category">预计 ' + escapeHtml(time) +
          ' 送到' + (eta ? ' · ' + escapeHtml(eta) : '') + '</span>' +
          '</div>';
      });
      html += '</div></div>';
    }
    if (possessions.length) {
      var visiblePossessions = possessions.filter(function (item) {
        return matchText([item.name, item.category, item.room]);
      });
      var possessionValue = Math.round(possessions.reduce(function (total, item) {
        var price = Number(item.price);
        return total + (isFinite(price) ? price : 0);
      }, 0) * 100) / 100;
      html += '<div class="inventory-section"><h4>物品 · ' +
        possessions.length + ' 件' +
        (possessionValue > 0
          ? ' · 总价值 ' + possessionValue + ' 元'
          : '') +
        '</h4><div class="inventory-list">';
      if (query && !visiblePossessions.length) {
        html += '<p class="inventory-empty">没有匹配的物品。</p>';
      }
      visiblePossessions.slice().reverse().forEach(function (item) {
        var icon = icons[item.category] || '📦';
        var price = Number(item.price);
        var name = String(item.name || '东西');
        var roomOptions = '<option value="">摆到房间…</option>' +
          rooms.map(function (room) {
            return '<option value="' + room + '"' +
              (item.room === room ? ' selected' : '') + '>' + room + '</option>';
          }).join('');
        html += '<div class="inventory-item">' +
          '<span class="inventory-icon">' + ItemArtwork.draw(item) + '</span>' +
          '<span class="inventory-name">' + escapeHtml(name) +
          (item.room ? '<small class="inventory-room-tag">' + escapeHtml(item.room) +
            (item.slot_label ? ' · ' + escapeHtml(item.slot_label) : '') +
            '</small>' : '') +
          '</span>' +
          '<span class="inventory-category">' + escapeHtml(item.category || '') + '</span>' +
          (isNaN(price) ? '' : '<span class="inventory-price">' + price + ' 元</span>') +
          '<button type="button" class="mini-btn inventory-use" data-use-name="' +
          escapeHtml(name) + '">使用</button>' +
          (item.installable ? '<select class="inventory-room-select" data-room-for="' +
            escapeHtml(name) + '">' + roomOptions + '</select>' +
            '<button type="button" class="mini-btn inventory-place" data-place-name="' +
            escapeHtml(name) + '">摆放</button>' : '') +
          '</div>';
      });
      html += '</div></div>';
    }
    if (!html) {
      html = '<p class="inventory-empty">' +
        (query ? '没有匹配的物品或书。' : '她还没有买过或实现过什么东西。') +
        '</p>';
    }
    body.innerHTML = html;
    body.querySelectorAll('[data-shelf-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.shelfFilter = button.getAttribute('data-shelf-filter') || 'all';
        saveSort('shelf-filter', state.shelfFilter);
        renderInventory();
      });
    });
    var shelfSortSelect = $('shelf-sort');
    if (shelfSortSelect) {
      shelfSortSelect.addEventListener('change', function () {
        state.shelfSort = shelfSortSelect.value || 'default';
        saveSort('shelf-sort', state.shelfSort);
        renderInventory();
      });
    }
    var readingGoalSelect = $('reading-goal');
    if (readingGoalSelect) {
      readingGoalSelect.addEventListener('change', function () {
        var picked = Number(readingGoalSelect.value);
        state.readingGoal = [15, 30, 45, 60].indexOf(picked) >= 0
          ? picked : 30;
        saveSort('reading-goal', String(state.readingGoal));
        renderInventory();
      });
    }
    var readingClear = $('shelf-reading-clear');
    if (readingClear) {
      readingClear.addEventListener('click', function () {
        if (!window.confirm('清空所有书籍的阅读时长记录吗？')) return;
        try {
          localStorage.removeItem('vl-book-reading');
          localStorage.removeItem('vl-book-reading-daily');
        } catch (error) {
          /* 忽略本地存储异常 */
        }
        renderInventory();
        showToast('阅读时长记录已清空');
      });
    }
    var shelfExport = $('shelf-export');
    if (shelfExport) {
      shelfExport.addEventListener('click', exportShelf);
    }
    body.querySelectorAll('[data-use-name]').forEach(function (button) {
      button.addEventListener('click', function () {
        useInventoryItem(button.getAttribute('data-use-name'), button);
      });
    });
    body.querySelectorAll('[data-place-name]').forEach(function (button) {
      button.addEventListener('click', function () {
        var row = button.closest('.inventory-item');
        var select = row ? row.querySelector('[data-room-for]') : null;
        if (!select || !select.value) {
          showToast('先选一个房间');
          return;
        }
        placeInventoryItem(
          button.getAttribute('data-place-name'), select.value, button
        );
      });
    });
    body.querySelectorAll('[data-book-id]').forEach(function (button) {
      button.addEventListener('click', function () {
        openBook(
          button.getAttribute('data-book-id'),
          Number(button.getAttribute('data-book-chapter') || 1),
          button
        );
      });
    });
  }

  function formatItemEffects(effects) {
    var labels = {
      mood: '心情', energy: '精力', satiety: '饱腹', hunger: '饱腹',
      hydration: '水分', health: '健康', willingness: '意愿',
      hygiene: '清洁', cleanliness: '清洁'
    };
    var parts = [];
    Object.keys(effects || {}).forEach(function (key) {
      var value = Number(effects[key]);
      if (!labels[key] || !value) return;
      parts.push(labels[key] + (value > 0 ? '+' : '') + value);
    });
    return parts.slice(0, 4).join(' · ');
  }

  function showItemEffectBurst(name, effects, icon) {
    var text = formatItemEffects(effects);
    var node = document.createElement('div');
    node.className = 'item-effect-burst';
    node.innerHTML = '<span class="item-effect-icon">' + (icon || '✨') +
      '</span><b>' + escapeHtml(name) + '</b>' +
      (text ? '<small>' + escapeHtml(text) + '</small>' : '');
    document.body.appendChild(node);
    window.setTimeout(function () {
      if (node.parentNode) node.remove();
    }, 1500);
  }

  function itemUseVerb(category) {
    var verbs = {
      '饮品': '喝了',
      '食物': '吃了',
      '零食': '吃了',
      '书籍': '看了',
      '穿搭': '穿上了',
      '数码': '用了',
      '兴趣': '玩了',
      '礼物': '拆开了',
      '居家': '用了',
      '愿望': '用了'
    };
    return verbs[category] || '用了';
  }

  function useInventoryItem(name, button) {
    if (button) button.disabled = true;
    fetch('/api/use_item', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item: name })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '用不了');
        var effectText = formatItemEffects(data.effects);
        var verb = itemUseVerb(data.category);
        showToast('月月' + verb + name + (effectText ? ' · ' + effectText : ''));
        showItemEffectBurst(
          name,
          data.effects || {},
          (data.item && data.item.icon) || '✨'
        );
        renderInventory();
        if (data.consumed) {
          if (state.selectedItem && String(state.selectedItem.name || '') === String(name)) {
            closeItem();
          }
          fetchHomeItems();
        }
        fetchState();
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '用不了');
      });
  }

  function placementPoint(room) {
    if (!window.SceneStudio || !window.RoomModel) return null;
    var floor = SceneStudio.floorFor(room);
    var size = SceneStudio.rooms(floor).filter(function (entry) {
      return entry.name === room;
    })[0];
    if (!size) return null;
    var occupied = [];
    var plan = RoomModel.plan || {};
    (state.homeItems || []).forEach(function (item) {
      if (String(item.room || '') !== room) return;
      var rect = plan[item.id];
      if (rect) {
        occupied.push({ x: rect[0] - 14, y: rect[1] - 14, w: rect[2] + 28, h: rect[3] + 28 });
      } else if (item.place) {
        occupied.push({
          x: Number(item.place.x) * size.w - 14,
          y: Number(item.place.y) * size.h - 14,
          w: 28,
          h: 28
        });
      }
    });
    ((RoomModel.fixtures && RoomModel.fixtures[room]) || []).forEach(function (fixture) {
      occupied.push({
        x: fixture.x - 12,
        y: fixture.y - 12,
        w: fixture.w + 24,
        h: fixture.d + 24
      });
    });
    var best = null;
    for (var gy = 2; gy <= 8; gy++) {
      for (var gx = 1; gx <= 9; gx++) {
        var x = (gx + 0.5) * size.w / 10;
        var y = (gy + 0.5) * size.h / 10;
        var blocked = occupied.some(function (rect) {
          return x > rect.x && x < rect.x + rect.w &&
            y > rect.y && y < rect.y + rect.h;
        });
        if (blocked) continue;
        var score = Math.abs(x - size.w * 0.5) + Math.abs(y - size.h * 0.68);
        if (!best || score < best.score) best = { x: x, y: y, score: score };
      }
    }
    if (!best) return null;
    return {
      x: Math.round(best.x / size.w * 1000) / 1000,
      y: Math.round(best.y / size.h * 1000) / 1000
    };
  }

  function placementRoomPoint(event, room) {
    var stage = $('scene-stage');
    if (!stage || !window.SceneStudio || !window.RoomPerspective) return null;
    var svg = stage.querySelector('.room-artwork');
    var size = SceneStudio.rooms(SceneStudio.floorFor(room)).filter(function (entry) {
      return entry.name === room;
    })[0];
    if (!svg || !size || typeof svg.getScreenCTM !== 'function') return null;
    var point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    var matrix = svg.getScreenCTM();
    if (!matrix) return null;
    var local = point.matrixTransform(matrix.inverse());
    var camera = RoomPerspective.camera(room, size.w, size.h);
    var y = (local.y - camera.oy) / (camera.s * camera.k);
    var x = (local.x - camera.ox) / camera.s - camera.a * y;
    return {
      x: Math.round(Math.max(0.05, Math.min(0.95, x / size.w)) * 1000) / 1000,
      y: Math.round(Math.max(0.05, Math.min(0.95, y / size.h)) * 1000) / 1000
    };
  }

  function cancelPlacement() {
    if (!state.placement) return false;
    state.placement = null;
    state.previewRoom = null;
    var stage = $('scene-stage');
    if (stage) stage.classList.remove('placement-mode');
    var back = $('preview-return');
    if (back) back.textContent = '回到当前';
    renderScene(true);
    showToast('已取消摆放');
    return true;
  }

  function surfaceAtPoint(room, point, event) {
    if (!window.GoodsSize || !point) return null;
    var hit = event && event.target && event.target.closest
      ? event.target.closest('.furniture-hit') : null;
    if (hit) {
      var hitId = String(hit.getAttribute('data-id') || '');
      var hitHeight = GoodsSize.surfaceHeight(hitId);
      if (hitHeight) return { surface_id: hitId, z_cm: hitHeight };
    }
    if (!window.RoomModel || !window.SceneStudio) return null;
    var floor = SceneStudio.floorFor(room);
    var size = (SceneStudio.rooms(floor) || []).filter(function (entry) {
      return entry.name === room;
    })[0];
    if (!size) return null;
    var px = Number(point.x) * size.w;
    var py = Number(point.y) * size.h;
    var best = null;
    function consider(id, rect) {
      var height = GoodsSize.surfaceHeight(id);
      if (!height || !rect || rect.length < 4) return;
      if (px < rect[0] || px > rect[0] + rect[2] ||
          py < rect[1] || py > rect[1] + rect[3]) return;
      if (!best || height > best.z_cm) {
        best = { surface_id: id, z_cm: height };
      }
    }
    var plan = RoomModel.plan || {};
    Object.keys(plan).forEach(function (id) { consider(id, plan[id]); });
    var fixtures = (RoomModel.fixtures || {})[room] || [];
    fixtures.forEach(function (fixture) {
      consider(String(fixture.id || ''), [fixture.x, fixture.y, fixture.w, fixture.d]);
    });
    return best;
  }

  function placementSurfaceFor(event, placement, point) {
    if (!window.GoodsSize || !GoodsSize.smallEnoughForSurface) return null;
    var itemId = String(placement.itemId || '');
    if (!itemId) {
      var possessions = (state.data && state.data.money
        && state.data.money.possessions) || [];
      var found = possessions.find(function (entry) {
        return String(entry.name || '') === String(placement.item || '');
      });
      itemId = String((found && found.id) || '');
    }
    if (!itemId || !GoodsSize.smallEnoughForSurface({ id: itemId })) {
      return null;
    }
    return surfaceAtPoint(placement.room, point, event);
  }

  function onPlacementStageClick(event) {
    if (!state.placement) return;
    event.preventDefault();
    event.stopPropagation();
    var placement = state.placement;
    var point = placementRoomPoint(event, placement.room);
    if (!point) {
      showToast('没找到房间地面，再点一次');
      return;
    }
    var isDecor = Boolean(placement.decor);
    var surface = isDecor ? null : placementSurfaceFor(event, placement, point);
    var url = isDecor ? '/api/decor/place' : '/api/place_item';
    var payload = isDecor
      ? {
          persona: (state.data && state.data.persona) || '',
          item_id: placement.item,
          room: placement.room,
          x: point.x,
          y: point.y
        }
      : {
          item: placement.item,
          room: placement.room,
          x: point.x,
          y: point.y,
          z_cm: surface ? surface.z_cm : 0,
          surface_id: surface ? surface.surface_id : ''
        };
    var label = placement.item;
    if (isDecor) {
      var found = (state.decorItems || []).find(function (entry) {
        return String(entry.id) === String(placement.item);
      });
      if (found) label = found.name || label;
    }
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '摆不了');
        state.placement = null;
        state.previewRoom = placement.room;
        var stage = $('scene-stage');
        if (stage) stage.classList.remove('placement-mode');
        var back = $('preview-return');
        if (back) back.textContent = '回到当前';
        showToast('已把' + label + '摆在' + placement.room);
        fetchHomeItems();
        fetchState();
        if (isDecor) fetchDecorItems(true);
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '摆不了');
      });
  }

  function placeInventoryItem(name, room, button) {
    if (button) button.disabled = false;
    state.previewScene = null;
    state.previewRoom = room;
    var itemId = '';
    var possessions = (state.data && state.data.money
      && state.data.money.possessions) || [];
    var found = possessions.find(function (entry) {
      return String(entry.name || '') === String(name);
    });
    if (found) itemId = String(found.id || '');
    state.placement = { item: name, itemId: itemId, room: room };
    closeInventory();
    renderScene(true);
    showToast('点击' + room + '的地面或桌面，决定' + name + '摆在哪');
  }

  function applyBookFontScale() {
    var content = $('book-content');
    if (!content) return;
    var scale = Number(state.bookFontScale) || 1;
    content.style.fontSize = (13 * scale).toFixed(1) + 'px';
  }

  function changeBookFont(delta) {
    state.bookFontScale = Math.max(
      0.8, Math.min(1.8, (Number(state.bookFontScale) || 1) + delta)
    );
    applyBookFontScale();
    try {
      localStorage.setItem('vl-book-font', String(state.bookFontScale));
    } catch (error) {
      // 本地存储不可用时只在当前会话生效。
    }
  }

  function applyBookTheme() {
    var content = $('book-content');
    if (!content) return;
    var theme = ['dark', 'sepia', 'light'].indexOf(state.bookTheme) >= 0
      ? state.bookTheme : 'dark';
    content.className = 'book-content book-theme-' + theme;
  }

  function cycleBookTheme() {
    var order = ['dark', 'sepia', 'light'];
    var current = order.indexOf(state.bookTheme);
    state.bookTheme = order[(current + 1) % order.length];
    applyBookTheme();
    try {
      localStorage.setItem('vl-book-theme', state.bookTheme);
    } catch (error) {
      // 本地存储不可用时只在当前会话生效。
    }
  }

  function bookBookmarks() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-book-bookmarks') || '{}');
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function bookBookmarkKey() {
    return String(state.bookId || '') + '::' + String(state.bookChapter || 1);
  }

  function bookmarkSnapshot(raw) {
    if (raw && typeof raw === 'object') {
      return {
        scroll: Math.max(0, Number(raw.scroll) || 0),
        ratio: raw.ratio == null ? null : Math.max(0, Math.min(1, Number(raw.ratio) || 0)),
        at: raw.at || ''
      };
    }
    return { scroll: Math.max(0, Number(raw) || 0), ratio: null, at: '' };
  }

  function bookmarkScrollFor(panel, data) {
    if (!panel) return 0;
    var max = Math.max(0, (panel.scrollHeight || 0) - (panel.clientHeight || 0));
    if (data && data.ratio != null && max > 0) {
      return Math.round(Math.max(0, Math.min(1, Number(data.ratio))) * max);
    }
    return Math.max(0, Number(data && data.scroll) || 0);
  }

  function applyBookBookmark(panel, data) {
    if (!panel) return;
    panel.scrollTop = bookmarkScrollFor(panel, data);
  }

  function updateBookBookmarkInfo() {
    var info = $('book-bookmark-info');
    if (!info) return;
    var bookmarks = bookBookmarks();
    var has = Object.prototype.hasOwnProperty.call(bookmarks, bookBookmarkKey());
    info.textContent = has ? '本章有书签' : '';
  }

  function updateBookNoteStatus(count) {
    var status = $('book-note-status');
    if (!status) return;
    var number = Number(count) || 0;
    status.textContent = number > 0 ? '已有 ' + number + ' 条笔记' : '';
  }

  function lastBookNotes(notes, limit) {
    var all = notes || [];
    var count = limit ? Math.max(1, limit) : all.length;
    var start = Math.max(0, all.length - count);
    return all.slice(start).map(function (note, offset) {
      return {
        text: note.text || '',
        at: note.at || '',
        chapter: Math.max(0, Number(note.chapter || 0)),
        index: start + offset
      };
    });
  }

  function filterBookNotes(notes, query) {
    var text = String(query || '').trim().toLowerCase();
    if (!text) return notes || [];
    return (notes || []).filter(function (note) {
      return [note.text, note.at, note.chapter ? '第 ' + note.chapter + ' 章' : '']
        .join(' ').toLowerCase().indexOf(text) >= 0;
    });
  }

  function renderBookNotes() {
    var list = $('book-note-list');
    if (!list) return;
    var allNotes = state.bookNotes || [];
    var query = String(state.bookNoteQuery || '').trim().toLowerCase();
    var notes = filterBookNotes(allNotes, query);
    if (!notes.length) {
      list.innerHTML = allNotes.length
        ? '<p class="inventory-empty">没有匹配的笔记。</p>'
        : '';
      return;
    }
    list.innerHTML = notes.map(function (note, index) {
      var absolute = note.index == null ? index : note.index;
      var chapterTag = Number(note.chapter || 0) > 0
        ? '<button type="button" class="book-note-chapter" ' +
          'data-book-note-goto="' + Number(note.chapter) +
          '" title="跳到第 ' + Number(note.chapter) + ' 章">第 ' +
          Number(note.chapter) + ' 章</button>'
        : '';
      return '<div class="book-note-item"><span>' + chapterTag +
        escapeHtml(note.text || '') + '</span>' +
        '<button type="button" data-book-note-delete="' + absolute +
        '" title="删除笔记">×</button></div>';
    }).join('');
    list.querySelectorAll('[data-book-note-goto]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (!state.bookId) return;
        openBook(state.bookId, Number(button.getAttribute('data-book-note-goto')) || 1);
      });
    });
    list.querySelectorAll('[data-book-note-delete]').forEach(function (button) {
      button.addEventListener('click', function () {
        deleteBookNote(Number(button.getAttribute('data-book-note-delete')));
      });
    });
  }

  function deleteBookNote(index) {
    if (!state.bookId) return;
    fetch('/api/book/note/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        id: state.bookId,
        index: index
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '删不掉');
        state.bookNotes = lastBookNotes(data.notes || []);
        state.bookNoteTotal = (data.notes || []).length;
        updateBookNoteStatus(state.bookNoteTotal);
        renderBookNotes();
        showToast('笔记已删除');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '删不掉');
      });
  }

  function exportBookNotes() {
    var notes = filterBookNotes(state.bookNotes || [], state.bookNoteQuery);
    if (!notes.length) {
      showToast(state.bookNoteQuery
        ? '当前筛选没有可导出的笔记'
        : '还没有读书笔记可以导出');
      return;
    }
    var lines = ['章节,时间,笔记'];
    notes.forEach(function (note) {
      lines.push([
        csvCell(note.chapter ? '第 ' + note.chapter + ' 章' : ''),
        csvCell(note.at || ''),
        csvCell(note.text || '')
      ].join(','));
    });
    var title = String(state.bookTitle || '书籍').replace(/[\\/:*?"<>|]/g, '_');
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = title + '-读书笔记' +
      (state.bookNoteQuery ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('读书笔记已导出');
  }

  function saveBookNote() {
    if (!state.bookId) return;
    var input = $('book-note-input');
    var text = String(input && input.value || '').trim();
    if (!text) {
      showToast('先写一句笔记');
      return;
    }
    fetch('/api/book/note', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        id: state.bookId,
        text: text,
        chapter: Number(state.bookChapter || 0)
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '笔记没记下');
        if (input) input.value = '';
        state.bookNotes = lastBookNotes(data.notes || []);
        state.bookNoteTotal = (data.notes || []).length;
        updateBookNoteStatus(state.bookNoteTotal);
        renderBookNotes();
        showToast('读书笔记已记下');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '笔记没记下');
      });
  }

  function renderBookBookmarks() {
    var list = $('book-bookmark-list');
    if (!list) return;
    var bookmarks = bookBookmarks();
    var prefix = String(state.bookId || '') + '::';
    var rows = [];
    Object.keys(bookmarks).forEach(function (key) {
      if (key.indexOf(prefix) !== 0) return;
      var chapter = Number(key.slice(prefix.length)) || 1;
      var data = bookmarkSnapshot(bookmarks[key]);
      rows.push({
        chapter: chapter,
        scroll: data.scroll,
        ratio: data.ratio,
        at: data.at
      });
    });
    rows.sort(function (a, b) { return a.chapter - b.chapter; });
    if (!rows.length) {
      list.innerHTML = '';
      return;
    }
    list.innerHTML = rows.map(function (row) {
      var title = String((state.bookChapterTitles || [])[row.chapter - 1] || '');
      var meta = row.ratio != null
        ? '已读 ' + Math.round(row.ratio * 100) + '%'
        : '位置 ' + row.scroll;
      return '<div class="book-bookmark-item">' +
        '<button type="button" class="book-bookmark-jump" ' +
        'data-bookmark-chapter="' + row.chapter + '" ' +
        'data-bookmark-scroll="' + row.scroll + '" ' +
        'data-bookmark-ratio="' + (row.ratio == null ? '' : row.ratio) + '">' +
        '<span>第 ' + row.chapter + ' 章' + (title ? ' · ' + escapeHtml(title) : '') +
        '</span><small>' + meta + '</small></button>' +
        '<button type="button" class="book-bookmark-delete" ' +
        'data-bookmark-delete="' + row.chapter + '" title="删除书签">×</button></div>';
    }).join('');
    list.querySelectorAll('[data-bookmark-chapter]').forEach(function (button) {
      button.addEventListener('click', function () {
        var chapter = Number(button.getAttribute('data-bookmark-chapter')) || 1;
        var ratioText = button.getAttribute('data-bookmark-ratio');
        var data = {
          scroll: Number(button.getAttribute('data-bookmark-scroll')) || 0,
          ratio: ratioText == null || ratioText === '' ? null : Number(ratioText)
        };
        var panel = document.querySelector('.book-panel');
        if (chapter === Number(state.bookChapter) && panel) {
          applyBookBookmark(panel, data);
          return;
        }
        state.bookRestoreScroll = data;
        openBook(state.bookId, chapter);
      });
    });
    list.querySelectorAll('[data-bookmark-delete]').forEach(function (button) {
      button.addEventListener('click', function (event) {
        event.stopPropagation();
        removeBookBookmark(Number(button.getAttribute('data-bookmark-delete')));
      });
    });
  }

  function removeBookBookmark(chapter) {
    if (!state.bookId) return;
    var bookmarks = bookBookmarks();
    delete bookmarks[String(state.bookId) + '::' + chapter];
    try {
      localStorage.setItem('vl-book-bookmarks', JSON.stringify(bookmarks));
    } catch (error) {
      showToast('书签删除失败');
      return;
    }
    updateBookBookmarkInfo();
    renderBookBookmarks();
    showToast('第 ' + chapter + ' 章书签已删除');
  }

  function saveBookBookmark() {
    var panel = document.querySelector('.book-panel');
    if (!panel || !state.bookId) return;
    var bookmarks = bookBookmarks();
    var max = Math.max(0, (panel.scrollHeight || 0) - (panel.clientHeight || 0));
    var scroll = Math.max(0, Math.round(panel.scrollTop || 0));
    bookmarks[bookBookmarkKey()] = {
      scroll: scroll,
      ratio: max > 0 ? Math.round((scroll / max) * 10000) / 10000 : 0,
      at: new Date().toISOString()
    };
    try {
      localStorage.setItem('vl-book-bookmarks', JSON.stringify(bookmarks));
    } catch (error) {
      showToast('书签保存失败');
      return;
    }
    updateBookBookmarkInfo();
    renderBookBookmarks();
    showToast('书签已保存');
  }

  function restoreBookBookmark() {
    var panel = document.querySelector('.book-panel');
    if (!panel || !state.bookId) return;
    var bookmarks = bookBookmarks();
    var key = bookBookmarkKey();
    if (!Object.prototype.hasOwnProperty.call(bookmarks, key)) {
      showToast('本章还没有书签');
      return;
    }
    applyBookBookmark(panel, bookmarkSnapshot(bookmarks[key]));
    showToast('已回到书签位置');
  }

  function updateBookNav() {
    var previous = $('book-prev');
    var next = $('book-next');
    if (previous) previous.disabled = state.bookChapter <= 1;
    if (next) next.disabled = state.bookChapter >= state.bookChapters;
    var select = $('book-chapter-select');
    if (select) {
      var count = Math.max(1, Number(state.bookChapters) || 1);
      var bookKey = String(state.bookId || '');
      if (
        Number(select.getAttribute('data-count') || 0) !== count ||
        String(select.getAttribute('data-book') || '') !== bookKey
      ) {
        var titles = state.bookChapterTitles || [];
        select.innerHTML = Array.from({ length: count }, function (_, index) {
          var chapter = index + 1;
          var title = String(titles[index] || '');
          var label = '第 ' + chapter + ' 章' + (title ? ' · ' + title : '');
          return '<option value="' + chapter + '" title="' + escapeHtml(label) + '">' +
            escapeHtml(label) + '</option>';
        }).join('');
        select.setAttribute('data-count', String(count));
        select.setAttribute('data-book', bookKey);
      }
      select.value = String(state.bookChapter || 1);
    }
  }

  function changeBookChapter(delta) {
    if (!state.bookId) return;
    var target = Number(state.bookChapter) + delta;
    if (target < 1 || target > Number(state.bookChapters)) return;
    openBook(state.bookId, target, null);
  }

  function bookReadingStore() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-book-reading') || '{}');
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function bookReadingLabel(bookId) {
    var seconds = Number(bookReadingStore()[String(bookId || '')] || 0);
    if (!seconds || seconds < 60) return '';
    var minutes = Math.round(seconds / 60);
    if (minutes < 60) return '已读 ' + minutes + ' 分钟';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return '已读 ' + hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '');
  }

  function totalBookReadingLabel() {
    var store = bookReadingStore();
    var total = 0;
    Object.keys(store).forEach(function (key) {
      total += Number(store[key] || 0);
    });
    return formatReadingSeconds(total);
  }

  function formatReadingSeconds(seconds) {
    if (!seconds || seconds < 60) return '';
    var minutes = Math.round(seconds / 60);
    if (minutes < 60) return minutes + ' 分钟';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '');
  }

  function bookReadingDailyStore() {
    try {
      var parsed = JSON.parse(
        localStorage.getItem('vl-book-reading-daily') || '{}'
      );
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function periodBookReadingSeconds(days) {
    var store = bookReadingDailyStore();
    var total = 0;
    var now = new Date();
    var span = Math.max(1, Number(days) || 7);
    for (var i = 0; i < span; i++) {
      var day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
      total += Number(store[dateKeyFromDate(day)] || 0);
    }
    return total;
  }

  function periodBookReadingLabel(days) {
    return formatReadingSeconds(periodBookReadingSeconds(days));
  }

  function periodBookReadingDays(days) {
    var store = bookReadingDailyStore();
    var count = 0;
    var now = new Date();
    var span = Math.max(1, Number(days) || 7);
    for (var i = 0; i < span; i++) {
      var day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
      if (Number(store[dateKeyFromDate(day)] || 0) >= 60) count += 1;
    }
    return count;
  }

  function bookReadingStreak() {
    var store = bookReadingDailyStore();
    var day = new Date();
    var key = dateKeyFromDate(day);
    if (Number(store[key] || 0) < 60) {
      day.setDate(day.getDate() - 1);
    }
    var streak = 0;
    while (streak < 400 && Number(store[dateKeyFromDate(day)] || 0) >= 60) {
      streak += 1;
      day.setDate(day.getDate() - 1);
    }
    return streak;
  }

  function flushBookReadingTime() {
    var startedAt = Number(state.bookOpenedAt || 0);
    var bookId = String(state.bookId || '');
    state.bookOpenedAt = 0;
    if (!startedAt || !bookId) return;
    var seconds = Math.round((Date.now() - startedAt) / 1000);
    if (seconds < 1) return;
    var store = bookReadingStore();
    store[bookId] = Number(store[bookId] || 0) + seconds;
    try {
      localStorage.setItem('vl-book-reading', JSON.stringify(store));
    } catch (error) {
      /* 本地记录失败不影响阅读 */
    }
    var daily = bookReadingDailyStore();
    var todayKey = dateKeyFromDate(new Date());
    var previousTodaySeconds = Number(daily[todayKey] || 0);
    daily[todayKey] = previousTodaySeconds + seconds;
    var cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 400);
    var cutoffKey = dateKeyFromDate(cutoff);
    Object.keys(daily).forEach(function (key) {
      if (key < cutoffKey) delete daily[key];
    });
    try {
      localStorage.setItem('vl-book-reading-daily', JSON.stringify(daily));
    } catch (error) {
      /* 本地记录失败不影响阅读 */
    }
    var goalSeconds = Math.max(1, Number(state.readingGoal) || 30) * 60;
    if (previousTodaySeconds < goalSeconds &&
        previousTodaySeconds + seconds >= goalSeconds) {
      showToast('今日阅读目标已达成');
    }
  }

  function recordBookProgress(bookId, chapter) {
    var id = String(bookId || '');
    var value = Math.max(1, Number(chapter) || 1);
    if (!id) return;
    fetch('/api/book/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        id: id,
        chapter: value
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) return;
        var shelf = (state.data && state.data.bookshelf) || [];
        var entry = shelf.find(function (book) {
          return String(book.id) === id;
        });
        if (entry) {
          entry.chapter = Math.max(Number(entry.chapter) || 0, Number(data.chapter) || 0);
          entry.finished = Boolean(data.finished);
        }
        var inventoryModal = $('inventory-modal');
        if (inventoryModal && !inventoryModal.classList.contains('hidden')) {
          renderInventory();
        }
      })
      .catch(function () {
        /* 阅读进度保存失败时不打断当前阅读。 */
      });
  }

  function openBook(id, chapter, button) {
    if (!id) return;
    var sameBook = String(state.bookId || '') === String(id);
    var modalOpen = !$('book-modal').classList.contains('hidden');
    if (!sameBook || !modalOpen) {
      flushBookReadingTime();
      state.bookOpenedAt = Date.now();
    }
    if (button) button.disabled = true;
    fetch('/api/book?persona=' + encodeURIComponent(
      (state.data && state.data.persona) || ''
    ) + '&id=' + encodeURIComponent(id) + '&chapter=' + chapter)
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '读不了');
        $('book-title').textContent = '《' + data.title + '》';
        var chapterNumber = Number(data.chapter || chapter) || 1;
        var chapterTitle = String(
          (data.chapter_titles || [])[chapterNumber - 1] || ''
        );
        $('book-sub').textContent = data.author + ' · ' + data.genre +
          ' · 共 ' + data.chapters + ' 章 · 第 ' + chapterNumber + ' 章' +
          (chapterTitle ? ' ' + chapterTitle : '');
        $('book-content').textContent = data.content;
        state.bookId = data.id || id;
        state.bookChapter = Number(data.chapter || chapter) || 1;
        state.bookChapters = Number(data.chapters) || 1;
        state.bookChapterTitles = data.chapter_titles || [];
        var bookProgress = Math.round(
          state.bookChapter / Math.max(1, state.bookChapters) * 100
        );
        var progressFill = $('book-progress-fill');
        if (progressFill) progressFill.style.width = bookProgress + '%';
        applyBookFontScale();
        applyBookTheme();
        updateBookNav();
        updateBookBookmarkInfo();
        state.bookNotes = data.note_items || [];
        state.bookNoteTotal = Number(data.notes) || 0;
        state.bookTitle = String(data.title || '');
        var noteSearch = $('book-note-search');
        if (noteSearch) noteSearch.value = state.bookNoteQuery || '';
        updateBookNoteStatus(state.bookNoteTotal);
        renderBookNotes();
        renderBookBookmarks();
        recordBookProgress(state.bookId, state.bookChapter);
        $('book-modal').classList.remove('hidden');
        if (state.bookRestoreScroll != null) {
          var restoreData = bookmarkSnapshot(state.bookRestoreScroll);
          state.bookRestoreScroll = null;
          window.setTimeout(function () {
            var panel = document.querySelector('.book-panel');
            if (panel) applyBookBookmark(panel, restoreData);
          }, 0);
        } else {
          var bookPanel = document.querySelector('.book-panel');
          if (bookPanel) bookPanel.scrollTop = 0;
        }
        if (button) button.disabled = false;
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '读不了');
      });
  }

  function closeBook() {
    flushBookReadingTime();
    $('book-modal').classList.add('hidden');
  }

  function syncShopControls() {
    var filterButton = $('shop-fav-filter');
    if (!filterButton) return;
    var favorites = shopFavorites();
    filterButton.textContent = '⭐ 收藏' + (favorites.length ? ' (' + favorites.length + ')' : '');
    filterButton.classList.toggle('active', Boolean(state.shopOnlyFavorites));
    $('shop-search').value = state.shopQuery || '';
    $('shop-sort').value = state.shopSort || 'default';
  }

  function openShop() {
    $('shop-modal').classList.remove('hidden');
    syncShopControls();
    loadShop();
  }

  function closeShop() {
    $('shop-modal').classList.add('hidden');
  }

  function openWallet() {
    $('wallet-modal').classList.remove('hidden');
    renderWallet();
  }

  function closeWallet() {
    $('wallet-modal').classList.add('hidden');
  }

  function renderWallet() {
    var body = $('wallet-body');
    var persona = (state.data && state.data.persona) || '';
    body.innerHTML = '<p class="inventory-empty">正在翻钱包...</p>';
    fetch('/api/wallet?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '钱包打不开');
        var wallet = data.wallet || {};
        var balance = Number(wallet.balance || 0);
        var goal = wallet.goal;
        var transactions = (wallet.transactions || []).slice().reverse();
        state.walletTransactions = transactions;
        var incomeTotal = 0;
        var expenseTotal = 0;
        transactions.forEach(function (tx) {
          var amount = Number(tx.amount || 0);
          if (amount >= 0) incomeTotal += amount;
          else expenseTotal += Math.abs(amount);
        });
        var moneyText = function (value) {
          var number = Number(value) || 0;
          return Number.isInteger(number) ? number : number.toFixed(2);
        };
        var html = '<div class="wallet-summary">' +
          '<div class="wallet-balance-card">' +
          '<small>当前余额</small><strong>' +
          moneyText(balance) + ' 元</strong></div>' +
          '<div class="wallet-total-card"><small>最近流水</small><strong>' +
          transactions.length + ' 条</strong></div>' +
          '<div class="wallet-flow-card income"><small>最近收入</small><strong>+' +
          moneyText(incomeTotal) + '</strong></div>' +
          '<div class="wallet-flow-card expense"><small>最近支出</small><strong>-' +
          moneyText(expenseTotal) + '</strong></div>' +
          '</div>';
        if (goal) {
          var target = Number(goal.target || 0);
          var progress = Number(goal.progress || 0);
          var percent = target > 0
            ? Math.max(0, Math.min(100, Math.round(progress / target * 100)))
            : 0;
          var achieved = Boolean(goal.achieved);
          html += '<div class="wallet-goal' + (achieved ? ' achieved' : '') +
            '"><div class="wallet-goal-head">' +
            '<b>存款目标：' + escapeHtml(goal.name || '') + '</b>' +
            (achieved ? '<em class="wallet-goal-badge">已达成</em>' : '') +
            '<span>' + (Number.isInteger(progress) ? progress : progress.toFixed(2)) +
            ' / ' + target + ' 元</span></div>' +
            '<div class="wallet-goal-bar"><span style="width:' + percent + '%"></span></div>' +
            (goal.wish
              ? '<p class="wallet-goal-wish">' + escapeHtml(goal.wish) + '</p>'
              : '') +
            '</div>';
        }
        var goalName = goal ? String(goal.name || '') : '';
        var goalTarget = goal ? Number(goal.target || 0) : '';
        var goalWish = goal ? String(goal.wish || '') : '';
        html += '<div class="wallet-goal-form"><h4>' +
          (goal ? '更改存款目标' : '设置存款目标') + '</h4>' +
          '<div class="wallet-goal-fields">' +
          '<input id="wallet-goal-name" maxlength="40" placeholder="目标名称" value="' +
          escapeHtml(goalName) + '">' +
          '<input id="wallet-goal-target" type="number" min="1" step="1" ' +
          'placeholder="目标金额" value="' + (goalTarget || '') + '">' +
          '</div>' +
          '<input id="wallet-goal-wish" maxlength="120" placeholder="愿望说明（可选）" value="' +
          escapeHtml(goalWish) + '">' +
          '<button type="button" class="ghost-btn" id="wallet-goal-save">保存目标</button>' +
          (goal
            ? '<button type="button" class="mini-btn" id="wallet-goal-clear">清除目标</button>'
            : '') +
          '</div>';
        html += '<div class="wallet-give">' +
          '<label>直接给月月钱</label>' +
          '<div class="wallet-give-row">' +
          '<input id="wallet-give-amount" type="number" min="1" max="100000" ' +
          'step="1" placeholder="金额">' +
          '<button type="button" id="wallet-give">给</button></div>' +
          '<small>从这里给的钱会记入流水，关系 +2。</small></div>';
        html += '<div class="wallet-section"><h4>最近流水</h4>';
        var walletFilter = state.walletFilter || 'all';
        var walletTransactions = state.walletTransactions || [];
        var walletTxCounts = {
          all: walletTransactions.length,
          income: walletTransactions.filter(function (tx) {
            return Number(tx.amount || 0) >= 0;
          }).length,
          expense: walletTransactions.filter(function (tx) {
            return Number(tx.amount || 0) < 0;
          }).length
        };
        html += '<div class="wallet-tools">' +
          '<input id="wallet-search" type="search" placeholder="搜索流水...">' +
          '<div class="wallet-filters">' + [
            ['all', '全部'], ['income', '收入'], ['expense', '支出']
          ].map(function (item) {
            return '<button type="button" data-wallet-filter="' + item[0] + '"' +
              (walletFilter === item[0] ? ' class="active"' : '') + '>' +
              item[1] + ' <b>' + (walletTxCounts[item[0]] || 0) +
              '</b></button>';
          }).join('') + '</div></div><div id="wallet-tx-list"></div></div>';
        body.innerHTML = html;
        var giveButton = $('wallet-give');
        if (giveButton) {
          giveButton.addEventListener('click', giveWalletMoney);
        }
        var goalButton = $('wallet-goal-save');
        if (goalButton) {
          goalButton.addEventListener('click', saveWalletGoal);
        }
        var clearGoalButton = $('wallet-goal-clear');
        if (clearGoalButton) {
          clearGoalButton.addEventListener('click', clearWalletGoal);
        }
        $('wallet-search').addEventListener('input', function () {
          state.walletQuery = $('wallet-search').value;
          renderWalletTransactions();
        });
        body.querySelectorAll('[data-wallet-filter]').forEach(function (button) {
          button.addEventListener('click', function () {
            state.walletFilter = button.getAttribute('data-wallet-filter') || 'all';
            saveSort('wallet-filter', state.walletFilter);
            body.querySelectorAll('[data-wallet-filter]').forEach(function (item) {
              item.classList.toggle(
                'active',
                item.getAttribute('data-wallet-filter') === state.walletFilter
              );
            });
            renderWalletTransactions();
          });
        });
        renderWalletTransactions();
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '钱包打不开') +
          '</p>';
      });
  }

  function walletKindLabels() {
    return {
      work: '工作收入', living: '生活开销', shop: '商店',
      gift: '主人给的', ask: '向主人要的', goal: '存款目标',
      reward: '愿望奖励', master: '主人给的', other: '其他'
    };
  }

  function filterWalletTransactions(transactions, query, filter) {
    var text = String(query || '').trim().toLowerCase();
    var kind = filter || 'all';
    var labels = walletKindLabels();
    return (transactions || []).filter(function (tx) {
      var amount = Number(tx.amount || 0);
      if (kind === 'income' && amount < 0) return false;
      if (kind === 'expense' && amount >= 0) return false;
      if (!text) return true;
      return [
        labels[tx.kind] || tx.kind || '收支',
        tx.reason || '',
        tx.at || ''
      ].join(' ').toLowerCase().indexOf(text) >= 0;
    });
  }

  function renderWalletTransactions() {
    var list = $('wallet-tx-list');
    if (!list) return;
    var transactions = state.walletTransactions || [];
    var walletFilter = state.walletFilter || 'all';
    var query = String(state.walletQuery || '').trim().toLowerCase();
    var kindLabels = walletKindLabels();
    var visible = filterWalletTransactions(transactions, query, walletFilter);
    if (!visible.length) {
      list.innerHTML = '<p class="inventory-empty">' +
        (query ? '没有匹配的流水。' : '还没有收支记录。') + '</p>';
      return;
    }
    var groups = {};
    var order = [];
    visible.slice(0, 20).forEach(function (tx) {
      var day = String(tx.at || '').slice(0, 10) || '未知日期';
      if (!groups[day]) {
        groups[day] = [];
        order.push(day);
      }
      groups[day].push(tx);
    });
    list.innerHTML = order.map(function (day) {
      return '<div class="wallet-tx-day">' + escapeHtml(day) + '</div>' +
        groups[day].map(function (tx) {
          var amount = Number(tx.amount || 0);
          var time = String(tx.at || '').slice(11, 16);
          return '<div class="wallet-tx">' +
            '<span class="wallet-tx-kind">' +
            escapeHtml(kindLabels[tx.kind] || tx.kind || '收支') + '</span>' +
            '<span class="wallet-tx-reason">' +
            escapeHtml(String(tx.reason || '').slice(0, 40)) + '</span>' +
            (time ? '<small class="wallet-tx-time">' + escapeHtml(time) + '</small>' : '') +
            '<b class="' + (amount >= 0 ? 'positive' : 'negative') + '">' +
            (amount >= 0 ? '+' : '') + amount + ' 元</b></div>';
        }).join('');
    }).join('');
  }

  function exportWalletTransactions() {
    var query = state.walletQuery || '';
    var transactions = filterWalletTransactions(
      state.walletTransactions || [],
      query,
      state.walletFilter
    );
    if (!transactions.length) {
      showToast(query || (state.walletFilter || 'all') !== 'all'
        ? '当前筛选没有可导出的流水'
        : '还没有收支记录可以导出');
      return;
    }
    var labels = walletKindLabels();
    var lines = ['时间,类型,金额,说明'];
    transactions.forEach(function (tx) {
      lines.push([
        csvCell(tx.at || ''),
        csvCell(labels[tx.kind] || tx.kind || '其他'),
        Number(tx.amount || 0),
        csvCell(tx.reason || '')
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var filtered = Boolean(query) || (state.walletFilter || 'all') !== 'all';
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '钱包流水-' + day + (filtered ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('钱包流水已导出');
  }

  function saveWalletGoal() {
    var nameInput = $('wallet-goal-name');
    var targetInput = $('wallet-goal-target');
    var wishInput = $('wallet-goal-wish');
    var name = String(nameInput && nameInput.value || '').trim();
    var target = Number(targetInput && targetInput.value);
    if (!name) {
      showToast('先填写目标名称');
      return;
    }
    if (!target || target <= 0) {
      showToast('目标金额必须大于 0');
      return;
    }
    var button = $('wallet-goal-save');
    if (button) button.disabled = true;
    fetch('/api/wallet/goal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        name: name,
        target: target,
        wish: String(wishInput && wishInput.value || '').trim()
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '目标没保存');
        showToast('存款目标已保存');
        renderWallet();
        fetchState();
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '目标没保存');
      });
  }

  function clearWalletGoal() {
    if (!window.confirm('确定清除当前存款目标吗？')) return;
    fetch('/api/wallet/goal/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || ''
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '目标没清除');
        showToast('存款目标已清除');
        renderWallet();
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '目标没清除');
      });
  }

  function giveWalletMoney() {
    var input = $('wallet-give-amount');
    var button = $('wallet-give');
    var amount = input ? Number(input.value) : 0;
    if (!amount || amount <= 0) {
      showToast('先填写要给月月的金额');
      if (input) input.focus();
      return;
    }
    if (amount > 100000) {
      showToast('一次最多给 100000 元');
      return;
    }
    if (button) {
      button.disabled = true;
      button.textContent = '给...';
    }
    fetch('/api/wallet/give', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: garagePersona(),
        amount: amount
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '给钱失败');
        showToast('已给月月 ' + data.amount + ' 元');
        renderWallet();
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '给钱失败');
        if (button) {
          button.disabled = false;
          button.textContent = '给';
        }
      });
  }

  function openGarage() {
    $('garage-modal').classList.remove('hidden');
    loadGarage();
  }

  function closeGarage() {
    $('garage-modal').classList.add('hidden');
  }

  var VEHICLE_CARS = {
    jeep: { key: 'jeep', id: 'car_jeep', bay: 'A1', name: '吉普', type: 'jeep', paint: '#6f7f5c', plate: '沪A·J4X4' },
    white: { key: 'white', id: 'car_white', bay: 'A2', name: '白色小车', type: 'sedan', paint: '#eef2ef', plate: '沪A·M320' },
    sports: { key: 'sports', id: 'car_sports', bay: 'A3', name: '跑车', type: 'sports', paint: '#c8423a', plate: '沪A·GT886' }
  };

  function vehicleKeyFromCar(value) {
    var text = String(value || '').trim();
    if (text === 'home' || text === 'home_car' || text === 'white' || text === 'sedan') return 'white';
    if (text === 'jeep' || text === 'garage_jeep') return 'jeep';
    if (text === 'sports' || text === 'garage_sports') return 'sports';
    return 'white';
  }

  function vehicleGarageData() {
    return state.garageData || (state.data && state.data.garage) || {};
  }

  function openVehicle(key) {
    state.vehicleKey = vehicleKeyFromCar(key || state.vehicleKey || 'white');
    $('vehicle-modal').classList.remove('hidden');
    renderVehicle();
  }

  function closeVehicle() {
    $('vehicle-modal').classList.add('hidden');
  }

  function renderVehicle() {
    var body = $('vehicle-body');
    if (!body) return;
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var garage = vehicleGarageData();
    var list = garage.vehicles || [];
    var staticInfo = VEHICLE_CARS[key];
    var live = list.find(function (item) {
      return item && String(item.id) === staticInfo.id;
    }) || (key === 'white' ? (garage.vehicle || {}) : {});
    var info = {
      key: key,
      id: staticInfo.id,
      bay: staticInfo.bay,
      name: String(live.name || staticInfo.name),
      type: staticInfo.type,
      paint: staticInfo.paint,
      plate: String(live.plate || staticInfo.plate)
    };
    var isOut = live.status === 'out';
    var fuel = Number(live.fuel || 0);
    var trip = live.trip || (key === 'white' ? (garage.trip || {}) : {});
    var art = (window.VehicleArt && VehicleArt.preview)
      ? VehicleArt.preview(info.type, info.paint, info.name)
      : '';
    var tabs = ['jeep', 'white', 'sports'].map(function (carKey) {
      var car = VEHICLE_CARS[carKey];
      var tabLive = list.find(function (item) {
        return item && String(item.id) === car.id;
      }) || {};
      var tabState = tabLive.status === 'out' ? '出车中' : '在库';
      return '<button type="button" class="vehicle-tab' + (carKey === key ? ' active' : '') +
        '" data-vehicle-key="' + carKey + '"><b>' + escapeHtml(car.bay) + ' · ' +
        escapeHtml(car.name) + '</b><small>' + escapeHtml(tabState) + ' · ' +
        escapeHtml(car.plate) + '</small></button>';
    }).join('');
    var status = isOut
      ? ('出车中 · ' + escapeHtml(trip.destination || ''))
      : '已停好';
    var html = '<div class="vehicle-tabs">' + tabs + '</div>' +
      '<div class="vehicle-hero">' + art + '</div>' +
      '<div class="vehicle-meta"><div><h4>' + escapeHtml(info.name) + '</h4>' +
      '<small>' + escapeHtml(info.bay) + ' 车位 · ' + status + '</small></div>' +
      '<span class="vehicle-plate">' + escapeHtml(info.plate) + '</span></div>' +
      '<div class="vehicle-fuel">油量 ' + fuel + '%' +
      '<div class="vehicle-fuel-bar"><span style="width:' + Math.max(0, Math.min(100, fuel)) + '%"></span></div></div>';
    if (isOut) {
      var percent = trip && trip.started_at ? garageTripPercent(trip) : 0;
      html += '<div class="garage-trip"><h4>正在路上</h4><p><b>' +
        escapeHtml(trip.driver === 'master' ? '主人开车' : '月月载你') + '</b> · ' +
        escapeHtml(trip.destination || '') + '</p><small>出发 ' +
        escapeHtml(garageTime(trip.started_at)) + ' · 预计 ' +
        escapeHtml(garageTime(trip.eta)) + ' 回来 · ' +
        escapeHtml(garageEtaText(trip.eta) || '') + '</small>' +
        '<div class="garage-trip-progress"><span style="width:' + percent + '%"></span></div>' +
        '<small>行程进度 ' + percent + '%</small>' +
        '<button type="button" class="ghost-btn" id="vehicle-return">已经回来了</button></div>';
    } else {
      var destinations = garage.destinations || [];
      html += '<div class="garage-choice"><label>去哪里</label><select id="vehicle-destination">' +
        destinations.map(function (destination) {
          return '<option value="' + escapeHtml(destination) + '">' + escapeHtml(destination) + '</option>';
        }).join('') + '</select><div class="garage-actions">' +
        '<button type="button" class="ghost-btn" data-vehicle-driver="master">我带她出去</button>' +
        '<button type="button" class="ghost-btn" data-vehicle-driver="self">让她载我出去</button>' +
        '</div></div>';
      if (fuel < 100) {
        html += '<div class="vehicle-actions"><button type="button" class="ghost-btn" id="vehicle-refuel">加油 ' +
          Number(garage.refuel_cost || 60) + ' 元</button></div>';
      }
      if (key === 'white') {
        html += '<div class="vehicle-actions"><button type="button" class="ghost-btn" id="vehicle-manage">打开车库管理</button></div>';
      }
    }
    body.innerHTML = html;
  }

  function vehicleRefresh(result, message) {
    if (result && result.garage) state.garageData = result.garage;
    if (message) showToast(message);
    renderVehicle();
    fetchState();
  }

  function vehicleStart(driver) {
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var info = VEHICLE_CARS[key];
    var select = $('vehicle-destination');
    var destination = select ? select.value : '';
    if (!destination) {
      showToast('先选一个目的地');
      return;
    }
    fetch('/api/garage/drive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: garagePersona(),
        destination: destination,
        driver: driver,
        vehicle_id: info.id
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '开不出去');
        vehicleRefresh(data, info.name + '出发去' + destination);
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '开不出去');
      });
  }

  function vehicleReturn() {
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var info = VEHICLE_CARS[key];
    fetch('/api/garage/return', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona(), vehicle_id: info.id })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '车还没回来');
        vehicleRefresh(data, info.name + '已回库');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '车还没回来');
      });
  }

  function vehicleRefuel() {
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var info = VEHICLE_CARS[key];
    fetch('/api/garage/refuel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona(), vehicle_id: info.id })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '加不了油');
        vehicleRefresh(data, info.name + '已加满油');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '加不了油');
      });
  }

  function garagePersona() {
    return (state.data && state.data.persona) || '';
  }

  function garageTime(value) {
    var text = String(value || '');
    return text.length >= 16 ? text.slice(11, 16) : text;
  }

  function garageEtaText(value) {
    var target = new Date(String(value || '')).getTime();
    if (!isFinite(target)) return '';
    var minutes = Math.round((target - Date.now()) / 60000);
    if (minutes <= 0) return '马上回来';
    if (minutes < 60) return '约 ' + minutes + ' 分钟后回来';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return '约 ' + hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '') + '后回来';
  }

  function loadGarage() {
    var body = $('garage-body');
    body.innerHTML = '<p class="inventory-empty">正在开车库门...</p>';
    fetch('/api/garage?persona=' + encodeURIComponent(garagePersona()), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '车库打不开');
        state.garageData = data.garage || {};
        renderGarage(data.garage || {});
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '车库打不开') +
          '</p>';
      });
  }

  function exportGarage() {
    var garage = state.garageData || {};
    var vehicle = garage.vehicle || {};
    if (!vehicle.name && !(garage.history || []).length) {
      showToast('车库数据还没加载好');
      return;
    }
    var filter = state.garageHistoryFilter || 'all';
    var filterLabels = { all: '全部', returned: '已回家', active: '在路上' };
    var history = (garage.history || []).filter(function (item) {
      if (filter === 'returned') return item.status === 'returned';
      if (filter === 'active') return item.status !== 'returned';
      return true;
    });
    var lines = ['记录类型,目的地或项目,状态,时间'];
    lines.push([
      '车辆', csvCell(vehicle.name || '白色小车'),
      csvCell(vehicle.status === 'out' ? '出车中' : '已停好'),
      '油量 ' + Number(vehicle.fuel || 0) + '%'
    ].join(','));
    history.forEach(function (item) {
      lines.push([
        '出车',
        csvCell(item.destination || ''),
        csvCell(item.status === 'returned' ? '已回家' : '在路上'),
        csvCell(String(item.started_at || '').replace('T', ' ').slice(0, 16))
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '车库记录-' + day +
      (filter === 'all' ? '' : '-' + filterLabels[filter]) + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('车库记录已导出');
  }

  function garageTripPercent(trip) {
    var start = new Date(trip.started_at || '').getTime();
    var eta = new Date(trip.eta || '').getTime();
    if (!start || !eta || eta <= start) return 0;
    var percent = (Date.now() - start) / (eta - start) * 100;
    return Math.max(0, Math.min(100, Math.round(percent)));
  }

  // 3D garage at the top of the garage panel; falls back to the 2D strip artwork when WebGL is unavailable.
  function garage3dMarkup(isOut, vehicle, fuel) {
    var art = document.querySelector('#garage-room .garage-room-art');
    var fallback = art ? '<div class="garage-3d-fallback">' + art.outerHTML.replace(/ id="[^"]*"/g, '') + '</div>' : '';
    if (!use3DWorld() || !window.Room3D || !Room3D.destinationMarkup || !Room3D.supportsDestination('garage', 'indoor')) return fallback;
    var status = isOut ? '车不在' : ((vehicle.name || '白色小车') + ' · 油量 ' + fuel + '%');
    var labelHtml = '<div class="scene-label">1F · 车库<small>' + escapeHtml(status) + '</small></div>';
    var mode = (isOut ? 'out' : 'parked') + (vehicle.plate ? '|' + String(vehicle.plate).replace(/\|/g, '') : '');
    return '<div class="garage-3d">' + Room3D.destinationMarkup({ key: 'garage', view: 'indoor', mode: mode, env: sceneEnvironment(), labelHtml: labelHtml, fallback: fallback, look: { none: true } }) + '</div>';
  }

  function renderGarage(garage) {
    var body = $('garage-body');
    var vehicle = garage.vehicle || {};
    var trip = garage.trip || {};
    var destinations = garage.destinations || [];
    var history = garage.history || [];
    var isOut = vehicle.status === 'out';
    var fuel = Number(vehicle.fuel || 0);
    var refuelButton = (!isOut && fuel < 100)
      ? '<button type="button" class="garage-refuel" id="garage-refuel">加油 ' +
        Number(garage.refuel_cost || 60) + ' 元</button>'
      : '';
    var fuelWarning = fuel <= 20
      ? '<small class="garage-fuel-warning">油量偏低，记得加油</small>'
      : '';
    var html = garage3dMarkup(isOut, vehicle, fuel) +
      '<div class="garage-car ' + (isOut ? 'is-out' : '') + '">' +
      '<div class="garage-car-icon">' + VehicleArt.preview() + '</div>' +
      '<div class="garage-car-copy"><b>' + escapeHtml(vehicle.name || '白色小车') +
      '</b><span>' + escapeHtml(vehicle.plate || '') +
      ' · 油量 ' + fuel + '%</span>' +
      '<div class="garage-fuel-bar"><span style="width:' + fuel + '%"></span></div>' +
      '<small>' + (isOut ? '不在车库' : '已停好') + '</small>' +
      fuelWarning +
      refuelButton + '</div></div>' +
      '<div class="garage-destination-preview" id="garage-destination-preview"></div>';
    if (isOut && trip) {
      var driver = trip.driver === 'master' ? '主人开车' : '月月载你';
      var tripPercent = garageTripPercent(trip);
      html += '<div class="garage-trip"><h4>正在路上</h4>' +
        '<p><b>' + escapeHtml(driver) + '</b> · ' +
        escapeHtml(trip.destination || '') + '</p>' +
        '<small>出发 ' + escapeHtml(garageTime(trip.started_at)) +
        ' · 预计 ' + escapeHtml(garageTime(trip.eta)) + ' 回来 · ' +
        escapeHtml(garageEtaText(trip.eta) || '') + '</small>' +
        '<div class="garage-trip-progress"><span style="width:' +
        tripPercent + '%"></span></div>' +
        '<small>行程进度 ' + tripPercent + '%</small>' +
        '<button type="button" class="ghost-btn" id="garage-return">已经回来了</button>' +
        '</div>';
    } else {
      html += '<div class="garage-choice"><label>去哪里</label>' +
        '<select id="garage-destination">' +
        destinations.map(function (destination) {
          return '<option value="' + escapeHtml(destination) + '">' +
            escapeHtml(destination) + '</option>';
        }).join('') +
        '</select>' +
        '<div class="garage-actions">' +
        '<button type="button" class="ghost-btn" data-garage-driver="master">我带她出去</button>' +
        '<button type="button" class="ghost-btn" data-garage-driver="self">让她载我出去</button>' +
        '</div></div>';
    }
    if (history.length) {
      var garageHistoryFilter = state.garageHistoryFilter || 'all';
      var filteredHistory = history.filter(function (item) {
        if (garageHistoryFilter === 'returned') return item.status === 'returned';
        if (garageHistoryFilter === 'active') return item.status !== 'returned';
        return true;
      });
      var shownHistory = state.garageHistoryExpanded
        ? filteredHistory
        : filteredHistory.slice(0, 5);
      var garageReturnedCount = history.filter(function (item) {
        return item.status === 'returned';
      }).length;
      var garageFilterCounts = {
        all: history.length,
        returned: garageReturnedCount,
        active: Math.max(0, history.length - garageReturnedCount)
      };
      html += '<div class="garage-history"><h4>最近出车</h4>' +
        '<div class="garage-history-filters">' + [
          ['all', '全部'], ['returned', '已回家'], ['active', '在路上']
        ].map(function (item) {
          return '<button type="button" data-garage-history-filter="' + item[0] + '"' +
            (garageHistoryFilter === item[0] ? ' class="active"' : '') + '>' +
            item[1] + ' <b>' + garageFilterCounts[item[0]] + '</b></button>';
        }).join('') + '</div>';
      if (!shownHistory.length) {
        html += '<p class="inventory-empty">这个分类下还没有出车记录。</p>';
      }
      shownHistory.forEach(function (item) {
        html += '<div class="garage-history-item"><span>' +
          escapeHtml(garageTime(item.started_at)) + '</span><b>' +
          escapeHtml(item.destination || '') + '</b><small>' +
          (item.driver === 'master' ? '主人带' : '自己开') +
          (item.status === 'returned' ? ' · 已回家' : ' · 在路上') +
          '</small></div>';
      });
      if (history.length > 5) {
        html += '<button type="button" class="garage-history-toggle" ' +
          'id="garage-history-toggle">' +
          (state.garageHistoryExpanded
            ? '收起记录'
            : '查看全部 ' + filteredHistory.length + ' 条') +
          '</button>';
      }
      html += '</div>';
    }
    body.innerHTML = html;
    if (isOut) {
      renderGarageDestinationPreview(trip.destination || '');
    } else {
      var select = $('garage-destination');
      if (select) {
        renderGarageDestinationPreview(select.value);
        select.addEventListener('change', function () {
          renderGarageDestinationPreview(select.value);
        });
      }
    }
    body.querySelectorAll('[data-garage-driver]').forEach(function (button) {
      button.addEventListener('click', function () {
        startGarageTrip(button.getAttribute('data-garage-driver'));
      });
    });
    var returnButton = $('garage-return');
    if (returnButton) {
      returnButton.addEventListener('click', returnGarage);
    }
    var refuelButtonEl = $('garage-refuel');
    if (refuelButtonEl) {
      refuelButtonEl.addEventListener('click', refuelGarage);
    }
    var historyToggle = $('garage-history-toggle');
    if (historyToggle) {
      historyToggle.addEventListener('click', function () {
        state.garageHistoryExpanded = !state.garageHistoryExpanded;
        renderGarage(garage);
      });
    }
    body.querySelectorAll('[data-garage-history-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.garageHistoryFilter =
          button.getAttribute('data-garage-history-filter') || 'all';
        saveSort('garage-history-filter', state.garageHistoryFilter);
        renderGarage(garage);
      });
    });
  }

  function renderGarageDestinationPreview(destination) {
    var box = $('garage-destination-preview');
    if (!box) return;
    if (!destination) {
      box.innerHTML = '';
      return;
    }
    if (!window.GarageDestinations) {
      box.innerHTML = '<p class="inventory-empty">地点内部造型加载中...</p>';
      return;
    }
    if (!GarageDestinations.hasInterior(destination)) {
      box.innerHTML = '<div class="garage-destination-fallback">' +
        escapeHtml(destination) + ' 是户外地点，没有室内场景。</div>';
      return;
    }
    var description = GarageDestinations.description(destination) || '';
    box.innerHTML = '<div class="garage-destination-label"><b>' +
      escapeHtml(destination) + '</b><small>地点内部</small></div>' +
      GarageDestinations.interior(destination) +
      (description
        ? '<p class="garage-destination-desc">' + escapeHtml(description) + '</p>'
        : '');
  }

  function refuelGarage() {
    var button = $('garage-refuel');
    if (button) {
      button.disabled = true;
      button.textContent = '加油中...';
    }
    fetch('/api/garage/refuel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona() })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '加不了油');
        showToast('车已加满油');
        renderGarage(data.garage || {});
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '加不了油');
        if (button) {
          button.disabled = false;
          button.textContent = '加油';
        }
      });
  }

  function openSystem() {
    $('system-modal').classList.remove('hidden');
    renderSystem();
  }

  function closeSystem() {
    $('system-modal').classList.add('hidden');
  }

  function backupAllData() {
    var persona = (state.data && state.data.persona) || '';
    fetch('/api/backup?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '备份失败');
        var day = new Date().toISOString().slice(0, 10);
        var payload = JSON.stringify({
          exported_at: data.exported_at || new Date().toISOString(),
          files: data.files || {}
        }, null, 2);
        var blob = new Blob([payload], {
          type: 'application/json;charset=utf-8'
        });
        var url = URL.createObjectURL(blob);
        var link = document.createElement('a');
        link.href = url;
        link.download = '虚拟人生-数据备份-' + day + '.json';
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
        showToast('数据备份已下载');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '备份失败');
      });
  }

  function restoreBackupFile(file) {
    if (!file) return;
    if (Number(file.size || 0) > 7500000) {
      showToast('备份文件过大，无法恢复');
      return;
    }
    var reader = new FileReader();
    reader.onload = function () {
      var parsed = null;
      try {
        parsed = JSON.parse(String(reader.result || ''));
      } catch (error) {
        showToast('备份文件不是有效 JSON');
        return;
      }
      var files = parsed && parsed.files ? parsed.files : parsed;
      if (!files || typeof files !== 'object' || Array.isArray(files)) {
        showToast('备份文件里没有数据');
        return;
      }
      var names = Object.keys(files);
      if (!names.length) {
        showToast('备份文件里没有数据');
        return;
      }
      var preview = names.slice(0, 6).join('、') +
        (names.length > 6 ? ' 等' : '');
      if (!window.confirm('将恢复 ' + names.length +
                         ' 个数据文件：\n' + preview +
                         '\n\n同名文件会被覆盖，确定继续吗？')) return;
      fetch('/api/backup/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: files,
          persona: (state.data && state.data.persona) || ''
        })
      })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          if (!data.ok) throw new Error(data.error || '恢复失败');
          showToast('已恢复 ' + Number(data.restored || 0) + ' 个数据文件');
          window.setTimeout(function () { window.location.reload(); }, 900);
        })
        .catch(function (error) {
          showToast(error && error.message ? error.message : '恢复失败');
        });
    };
    reader.onerror = function () { showToast('读取备份文件失败'); };
    reader.readAsText(file, 'utf-8');
  }

  function resetViewPreferences() {
    if (!window.confirm('重置所有界面偏好吗？会恢复默认排序和筛选，不会删除日记、照片或笔记。')) {
      return;
    }
    var keys = [
      'vl-anim', 'vl-render', 'vl-book-font', 'vl-book-theme', 'vl-shop-favorites',
      'vl-shelf-sort', 'vl-shop-sort', 'vl-weekly-days',
      'vl-weekly-metric', 'vl-weekly-theme', 'vl-trips-filter',
      'vl-status-trend-metric', 'vl-status-trend-range',
      'vl-wallet-filter', 'vl-garage-history-filter', 'vl-memory-filter',
      'vl-activity-filter', 'vl-diary-filter', 'vl-shelf-filter', 'vl-day-schedule-filter', 'vl-reading-goal'
    ];
    keys.forEach(function (key) {
      try {
        localStorage.removeItem(key);
      } catch (error) {
        /* 忽略本地存储异常 */
      }
    });
    window.location.reload();
  }

  function exportDiagnostics() {
    if (!state.systemData) {
      showToast('还没有可导出的诊断');
      return;
    }
    var day = new Date().toISOString().slice(0, 10);
    var payload = JSON.stringify({
      exported_at: new Date().toISOString(),
      diagnostics: state.systemData
    }, null, 2);
    var blob = new Blob([payload], { type: 'application/json;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '虚拟人生-系统诊断-' + day + '.json';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('系统诊断已导出');
  }

  function renderSystem() {
    var body = $('system-body');
    var persona = (state.data && state.data.persona) || '';
    body.innerHTML = '<p class="inventory-empty">正在检查系统...</p>';
    fetch('/api/diagnostics?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '系统检查失败');
        var d = data.diagnostics || {};
        state.systemData = d;
        var counts = d.counts || {};
        var checks = d.checks || [];
        var wallet = d.wallet || {};
        var garage = d.garage || {};
        var vehicle = garage.vehicle || {};
        var html = '<div class="system-version">' +
          '<div><small>插件</small><b>' + escapeHtml(d.plugin_version || '未知') +
          '</b></div><div><small>前端</small><b>' +
          escapeHtml(d.frontend_version || '未知') + '</b></div></div>';
        var failedChecks = checks.filter(function (check) {
          return !check.ok;
        }).length;
        var allOk = d.all_ok === undefined ? failedChecks === 0 : Boolean(d.all_ok);
        html += '<div class="system-overall ' + (allOk ? 'ok' : 'warn') + '">' +
          '<span>' + (allOk ? '✅' : '⚠️') + '</span><b>' +
          (allOk ? '系统正常' : '有 ' + failedChecks + ' 项需要检查') +
          '</b><small>共 ' + checks.length + ' 项检查</small></div>';
        html += '<div class="system-checks"><h4>检查项</h4>';
        var checkTargets = {
          books: 'inventory-toggle',
          book_txt: 'inventory-toggle',
          goods: 'shop-toggle',
          garage: 'garage-toggle',
          wallet: 'wallet-toggle',
          cooking: 'cook-open',
          health: 'health-open'
        };
        checks.forEach(function (check) {
          var target = checkTargets[check.id] || '';
          html += '<div class="system-check ' + (check.ok ? 'ok' : 'warn') +
            (target ? ' clickable' : '') + '"' +
            (target ? ' data-system-target="' + target + '"' : '') + '>' +
            '<span>' + (check.ok ? '✅' : '⚠️') + '</span><b>' +
            escapeHtml(check.label || '') + '</b><small>' +
            escapeHtml(check.detail || '') + '</small></div>';
        });
        html += '</div>';
        html += '<div class="system-counts"><h4>系统内容</h4><div class="system-count-grid">' + [
          ['书籍', counts.books],
          ['样例章节', counts.sample_chapters],
          ['商品', counts.goods],
          ['家具', counts.home_items],
          ['目的地', counts.destinations],
          ['日记', counts.diary],
          ['心情天数', counts.mood_days],
          ['待处理', counts.pending],
          ['下厨', counts.cooking],
          ['采购', counts.shopping],
        ].map(function (item) {
          return '<div><small>' + escapeHtml(item[0]) + '</small><b>' +
            escapeHtml(String(item[1] == null ? 0 : item[1])) + '</b></div>';
        }).join('') + '</div></div>';
        html += '<div class="system-summary"><div><small>钱包</small><b>' +
          escapeHtml(String(wallet.balance == null ? 0 : wallet.balance)) +
          ' 元</b></div><div><small>车库</small><b>' +
          escapeHtml(vehicle.name || '白色小车') + ' · ' +
          Number(vehicle.fuel || 0) + '% · ' +
          escapeHtml(vehicle.status === 'out' ? '出车中' : '已停好') +
          '</b></div></div>';
        body.innerHTML = html;
        var stamp = new Date();
        $('system-sub').textContent = '检查于 ' + [
          stamp.getHours(), stamp.getMinutes(), stamp.getSeconds()
        ].map(function (part) {
          return String(part).padStart(2, '0');
        }).join(':');
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '系统检查失败') +
          '</p>';
      });
  }

  function startGarageTrip(driver) {
    var select = $('garage-destination');
    var destination = select ? select.value : '';
    if (!destination) {
      showToast('先选一个目的地');
      return;
    }
    var body = $('garage-body');
    body.querySelectorAll('button').forEach(function (button) {
      button.disabled = true;
    });
    fetch('/api/garage/drive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: garagePersona(),
        destination: destination,
        driver: driver
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '车开不出去');
        showToast(driver === 'master'
          ? '你带月月去' + destination + '了'
          : '月月载你去' + destination + '了');
        renderGarage(data.garage || {});
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '车开不出去');
        loadGarage();
      });
  }

  function returnGarage() {
    fetch('/api/garage/return', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona() })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '还回不来');
        showToast('车已经停回车库');
        state.lastGarageStatus = 'parked';
        renderGarage(data.garage || {});
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '还回不来');
      });
  }

  function loadShop() {
    var category = $('shop-category').value;
    var data = state.data || {};
    var balance = Number((data.money || {}).balance);
    $('shop-balance').textContent = isNaN(balance)
      ? '钱包余额 --'
      : '钱包余额 ' + (Number.isInteger(balance) ? balance : balance.toFixed(2)) + ' 元';
    fetch('/api/shop?category=' + encodeURIComponent(category), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '商店没开门');
        var select = $('shop-category');
        var current = select.value;
        var categories = data.categories || [];
        if (!select.getAttribute('data-filled')) {
          select.innerHTML = '<option value="">全部分类</option>' +
            categories.map(function (category) {
              return '<option value="' + escapeHtml(category) + '">' +
                escapeHtml(category) + '</option>';
            }).join('');
          select.value = current || '';
          select.setAttribute('data-filled', '1');
        }
        renderShop(data.items || []);
      })
      .catch(function (error) {
        $('shop-body').innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '商店没开门') +
          '</p>';
      });
  }

  function shopFavorites() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-shop-favorites') || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  }

  function toggleShopFavorite(id) {
    if (!id) return;
    var favorites = shopFavorites();
    var index = favorites.indexOf(id);
    if (index >= 0) {
      favorites.splice(index, 1);
    } else {
      favorites.push(id);
    }
    try {
      localStorage.setItem('vl-shop-favorites', JSON.stringify(favorites));
    } catch (error) {
      showToast('收藏保存失败');
      return;
    }
    renderShop(state.shopItems || []);
  }

  function renderShop(items) {
    var body = $('shop-body');
    if (!body) return;
    state.shopItems = items;
    syncShopControls();
    var query = String(state.shopQuery || '').trim().toLowerCase();
    var filtered = query
      ? items.filter(function (item) {
          return [item.name, item.description, item.category]
            .join(' ').toLowerCase().indexOf(query) >= 0;
        })
      : items;
    var sort = state.shopSort || 'default';
    if (sort !== 'default') {
      filtered = filtered.slice().sort(function (a, b) {
        if (sort === 'name') {
          return String(a.name || '').localeCompare(String(b.name || ''), 'zh');
        }
        var diff = Number(a.price || 0) - Number(b.price || 0);
        if (sort === 'price_asc') return diff;
        if (sort === 'price_desc') return -diff;
        return 0;
      });
    }
    if (!filtered.length) {
      body.innerHTML = '<p class="inventory-empty">' +
        (state.shopOnlyFavorites
          ? '还没有符合条件的收藏商品。'
          : query ? '没有匹配的商品。' : '这个分类暂时没有商品。') + '</p>';
      return;
    }
    var favorites = shopFavorites();
    if (state.shopOnlyFavorites) {
      filtered = filtered.filter(function (item) {
        return favorites.indexOf(String(item.id || '')) >= 0;
      });
    }
    if (!filtered.length) {
      body.innerHTML = '<p class="inventory-empty">' +
        (state.shopOnlyFavorites
          ? '还没有符合条件的收藏商品。'
          : '没有匹配的商品。') + '</p>';
      return;
    }
    var money = (state.data && state.data.money) || {};
    var balance = Number(money.balance);
    body.innerHTML = filtered.map(function (item) {
      var isFavorite = favorites.indexOf(String(item.id || '')) >= 0;
      var price = Number(item.price || 0);
      var affordable = isNaN(balance) || price <= balance;
      return '<div class="shop-item' + (affordable ? '' : ' unaffordable') + '">' +
        '<span class="shop-icon">' + ItemArtwork.draw(item) + '</span>' +
        '<div class="shop-copy">' +
        '<div class="shop-name">' +
        '<button type="button" class="shop-fav' + (isFavorite ? ' active' : '') +
        '" data-shop-fav="' + escapeHtml(item.id || '') + '">' +
        (isFavorite ? '★' : '☆') + '</button>' +
        escapeHtml(item.name || '商品') +
        '<small>' + escapeHtml(item.category || '') + '</small></div>' +
        '<div class="shop-desc">' + escapeHtml(item.description || '') + '</div>' +
        '</div>' +
        '<div class="shop-buy-box">' +
        '<span class="shop-price">' + price + ' 元</span>' +
        '<button type="button" class="mini-btn shop-buy" data-shop-buy="' +
        escapeHtml(item.id || '') + '"' +
        (affordable ? '' : ' disabled title="余额不足"') + '>' +
        (affordable ? '下单' : '余额不足') + '</button>' +
        '</div>' +
        '</div>';
    }).join('');
    body.querySelectorAll('[data-shop-fav]').forEach(function (button) {
      button.addEventListener('click', function () {
        toggleShopFavorite(button.getAttribute('data-shop-fav'));
      });
    });
    body.querySelectorAll('[data-shop-buy]').forEach(function (button) {
      button.addEventListener('click', function () {
        buyShopItem(button.getAttribute('data-shop-buy'), button);
      });
    });
  }

  function buyShopItem(id, button) {
    if (!id) return;
    var item = null;
    (state.shopItems || []).forEach(function (entry) {
      if (String(entry.id || '') === String(id)) item = entry;
    });
    var price = Number((item || {}).price || 0);
    if (price >= 100 && !window.confirm(
      '确认花 ' + price + ' 元购买「' + String((item || {}).name || '商品') + '」吗？'
    )) {
      if (button) button.disabled = false;
      return;
    }
    if (button) button.disabled = true;
    fetch('/api/shop/buy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id, quantity: 1 })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '买不了');
        showToast(
          data.delivery
            ? '下单成功，预计 ' + String((data.order || {}).deliver_at || '').slice(11, 16) + ' 送到'
            : '买到了'
        );
        loadShop();
        fetchState();
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '买不了');
      });
  }

  function openRelations() {
    renderRelations();
    $('relations-modal').classList.remove('hidden');
  }

  function closeRelations() {
    $('relations-modal').classList.add('hidden');
  }

  function renderRelations() {
    var body = $('relations-body');
    var data = state.data || {};
    var info = data.affection || {};
    var score = Number(info.score || 0);
    var actions = [
      { id: 'headpat', label: '摸摸头', text: '（你摸了摸月月的头）', need: 100, points: 2 },
      { id: 'handhold', label: '牵手', text: '（你伸手牵住月月）', need: 250, points: 3 },
      { id: 'hug', label: '抱抱', text: '（你抱了抱月月）', need: 450, points: 4 },
      { id: 'kiss', label: '亲一下', text: '（你凑近亲了亲月月）', need: 650, points: 6 }
    ];
    var next = info.next_score
      ? '距离下一阶段还差 ' + Math.max(0, Number(info.next_score) - score) + ' 点'
      : '已经是最亲近的阶段';
    var relationPercent = Math.max(0, Math.min(100, score / 1000 * 100));
    var html = '<div class="relations-score">' +
      '<strong>' + escapeHtml(info.level || '陌生') + '</strong>' +
      '<span>' + score + ' / 1000</span></div>' +
      '<div class="relations-progress"><span style="width:' +
      relationPercent.toFixed(1) + '%"></span></div>' +
      '<div class="relations-meta">认识第 ' + Number(info.days_known || 1) + ' 天 · ' +
      escapeHtml(next) + ' · 称呼：' +
      escapeHtml(info.nickname || '主人') + '</div>';
    if (info.daily_cap) {
      var dailyLeft = Number(info.daily_remaining || 0);
      html += '<div class="relations-daily' + (dailyLeft <= 0 ? ' full' : '') +
        '">今日好感 +' + Number(info.daily_points || 0) + ' / ' +
        Number(info.daily_cap) +
        (dailyLeft > 0 ? ' · 还能加 ' + dailyLeft : ' · 今天的好感已满') + '</div>';
    }
    html += '<div class="relations-nickname"><label>怎么称呼她</label>' +
      '<input id="relations-nickname" maxlength="12" value="' +
      escapeHtml(info.nickname || '主人') + '">' +
      '<button type="button" class="mini-btn" id="relations-nickname-save">保存</button>' +
      '</div>';
    var anniversary = '';
    if (info.is_anniversary) {
      anniversary = '今天是认识第 ' + Number(info.days_known || 1) + ' 天纪念日。';
    } else if (info.next_anniversary) {
      anniversary = '下一个纪念日：认识第 ' + Number(info.next_anniversary) + ' 天。';
    }
    if (anniversary) {
      html += '<div class="relations-note">' + escapeHtml(anniversary) + '</div>';
    }
    var milestones = info.milestones || [];
    if (milestones.length) {
      html += '<div class="relations-note">最近关系变化：进入「' +
        escapeHtml(milestones[milestones.length - 1].level || '') + '」</div>';
    }
    html += '<div class="relations-actions">';
    var dailyFull = info.daily_cap != null && Number(info.daily_remaining || 0) <= 0;
    actions.forEach(function (action) {
      var unlocked = score >= action.need && !dailyFull;
      html += '<button type="button" class="relations-action" ' +
        'data-affection-action="' + action.id + '" ' +
        'data-affection-text="' + escapeHtml(action.text) + '" ' +
        'data-affection-label="' + escapeHtml(action.label) + '" ' +
        (unlocked ? '' : 'disabled ') +
        'title="' + (dailyFull
          ? '今天的好感已满，明天再来'
          : unlocked ? '好感 ' + action.need + ' 已解锁' : '需要好感 ' + action.need) + '">' +
        '<span>' + escapeHtml(action.label) + '</span>' +
        '<small>' + (dailyFull
          ? '今日已满'
          : unlocked ? '+' + action.points + ' 好感' : '需好感 ' + action.need) + '</small>' +
        '</button>';
    });
    html += '</div>';
    var events = info.events || [];
    var milestones = info.milestones || [];
    var timeline = [];
    events.forEach(function (event) {
      if (event && event.at) {
        timeline.push({
          at: String(event.at),
          text: '互动 +' + Number(event.points || 0) +
            ' · ' + String(event.reason || ''),
          kind: 'event'
        });
      }
    });
    milestones.forEach(function (item) {
      if (item && item.at) {
        timeline.push({
          at: String(item.at),
          text: '关系进入「' + String(item.level || '') + '」',
          kind: 'milestone'
        });
      }
    });
    timeline.sort(function (a, b) { return a.at < b.at ? -1 : 1; });
    if (timeline.length) {
      var shownTimeline = state.relationsTimelineExpanded
        ? timeline
        : timeline.slice(-10);
      html += '<div class="relations-section"><h4>关系年表' +
        '<button type="button" class="relations-export" id="relations-export">导出</button></h4>' +
        '<div class="relations-timeline">';
      shownTimeline.forEach(function (item) {
        html += '<div class="relation-event ' + item.kind + '">' +
          '<span>' + escapeHtml(item.at.slice(5, 16)) + '</span>' +
          '<b>' + escapeHtml(item.text) + '</b></div>';
      });
      html += '</div>';
      if (timeline.length > 10) {
        html += '<button type="button" class="relations-timeline-toggle" ' +
          'id="relations-timeline-toggle">' +
          (state.relationsTimelineExpanded
            ? '收起年表'
            : '查看全部 ' + timeline.length + ' 条') +
          '</button>';
      }
      html += '</div>';
    }
    body.innerHTML = html;
    body.querySelectorAll('[data-affection-action]').forEach(function (button) {
      button.addEventListener('click', function () {
        doAffectionAction(
          button.getAttribute('data-affection-action'),
          button.getAttribute('data-affection-text'),
          button.getAttribute('data-affection-label')
        );
      });
    });
    var nicknameSave = $('relations-nickname-save');
    if (nicknameSave) {
      nicknameSave.addEventListener('click', saveRelationsNickname);
    }
    var timelineToggle = $('relations-timeline-toggle');
    if (timelineToggle) {
      timelineToggle.addEventListener('click', function () {
        state.relationsTimelineExpanded = !state.relationsTimelineExpanded;
        renderRelations();
      });
    }
    var exportButton = $('relations-export');
    if (exportButton) {
      exportButton.addEventListener('click', exportRelationsTimeline);
    }
  }

  function exportRelationsTimeline() {
    var info = (state.data || {}).affection || {};
    var lines = [['时间', '类型', '内容'].join(',')];
    (info.events || []).forEach(function (event) {
      if (!event || !event.at) return;
      lines.push([
        csvCell(event.at),
        csvCell('互动'),
        csvCell('+' + Number(event.points || 0) + ' · ' + String(event.reason || ''))
      ].join(','));
    });
    (info.milestones || []).forEach(function (item) {
      if (!item || !item.at) return;
      lines.push([
        csvCell(item.at),
        csvCell('阶段'),
        csvCell('关系进入「' + String(item.level || '') + '」')
      ].join(','));
    });
    if (lines.length <= 1) {
      showToast('还没有关系记录可以导出');
      return;
    }
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '虚拟人生-关系年表-' + day + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('关系年表已导出');
  }

  function saveRelationsNickname() {
    var input = $('relations-nickname');
    var nickname = String(input && input.value || '').trim();
    if (!nickname) {
      showToast('称呼不能为空');
      return;
    }
    var button = $('relations-nickname-save');
    if (button) button.disabled = true;
    fetch('/api/affection/nickname', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        nickname: nickname
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '称呼没保存');
        showToast('称呼已改为「' + data.nickname + '」');
        renderRelations();
        fetchState();
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '称呼没保存');
      });
  }

  function doAffectionAction(action, text, label) {
    closeRelations();
    startInteraction({
      kind: 'chat',
      text: text,
      action: 'affection',
      affection_action: action
    }, label || '她正在靠近');
  }

  function openWeekly() {
    if (!state.weeklyDays) state.weeklyDays = 7;
    if (!state.weeklyMetric) state.weeklyMetric = 'mood';
    $('weekly-modal').classList.remove('hidden');
    updateWeeklyRangeButtons();
    updateWeeklyMetricButtons();
    updateWeeklyChartThemeButtons();
    renderWeekly();
  }

  function closeWeekly() {
    $('weekly-modal').classList.add('hidden');
  }

  function updateWeeklyRangeButtons() {
    document.querySelectorAll('[data-weekly-days]').forEach(function (button) {
      button.classList.toggle(
        'active',
        Number(button.getAttribute('data-weekly-days')) === Number(state.weeklyDays)
      );
    });
  }

  function updateWeeklyMetricButtons() {
    document.querySelectorAll('[data-weekly-metric]').forEach(function (button) {
      button.classList.toggle(
        'active',
        button.getAttribute('data-weekly-metric') === state.weeklyMetric
      );
    });
  }

  function updateWeeklyChartThemeButtons() {
    document.querySelectorAll('[data-chart-theme]').forEach(function (button) {
      button.classList.toggle(
        'active',
        button.getAttribute('data-chart-theme') === state.weeklyChartTheme
      );
    });
  }

  function setWeeklyChartTheme(theme) {
    state.weeklyChartTheme = ['dark', 'warm', 'light'].indexOf(theme) >= 0
      ? theme : 'dark';
    saveSort('weekly-theme', state.weeklyChartTheme);
    updateWeeklyChartThemeButtons();
    showToast('图表主题：' + (
      state.weeklyChartTheme === 'warm' ? '暖色'
        : state.weeklyChartTheme === 'light' ? '浅色' : '暗色'
    ));
  }

  function setWeeklyRange(days) {
    var value = Number(days);
    state.weeklyDays = value >= 300 ? 365 : value >= 28 ? 30 : 7;
    saveSort('weekly-days', String(state.weeklyDays));
    updateWeeklyRangeButtons();
    renderWeekly();
  }

  function setWeeklyMetric(metric) {
    state.weeklyMetric = ['mood', 'energy', 'satiety'].indexOf(metric) >= 0
      ? metric
      : 'mood';
    saveSort('weekly-metric', state.weeklyMetric);
    updateWeeklyMetricButtons();
    renderWeekly();
  }

  function exportWeeklyChart() {
    var report = state.weeklyReport;
    if (!report) {
      showToast('周报还没加载好');
      return;
    }
    var moods = (report.moods || []).slice(-14);
    if (!moods.length) {
      showToast('还没有可导出的图表');
      return;
    }
    var metric = state.weeklyMetric || 'mood';
    var labels = { mood: '心情', energy: '精力', satiety: '饱腹' };
    var colors = { mood: '#8fd3e8', energy: '#e9c46a', satiety: '#b9d48f' };
    var palettes = {
      dark: {
        bg: '#111722', title: '#f0d4a4', sub: '#8e9caf',
        grid: 'rgba(255,255,255,.08)', value: '#aebdcc',
        date: '#77879a', summary: '#c7d3df'
      },
      warm: {
        bg: '#f3e7d3', title: '#5a3d24', sub: '#8a6a4b',
        grid: 'rgba(90,61,36,.12)', value: '#6f5136',
        date: '#9a7a5a', summary: '#5a3d24'
      },
      light: {
        bg: '#f6f8fb', title: '#26303c', sub: '#6c7a89',
        grid: 'rgba(38,48,60,.1)', value: '#4c5a68',
        date: '#8593a1', summary: '#26303c'
      }
    };
    var palette = palettes[state.weeklyChartTheme] || palettes.dark;
    var canvas = document.createElement('canvas');
    canvas.width = 1000;
    canvas.height = 520;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = palette.bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = palette.title;
    ctx.font = '600 30px "Microsoft YaHei", sans-serif';
    ctx.fillText('虚拟人生 · 生活周报', 56, 68);
    ctx.fillStyle = palette.sub;
    ctx.font = '18px "Microsoft YaHei", sans-serif';
    ctx.fillText(
      String(report.start || '') + ' → ' + String(report.end || '') +
      ' · ' + labels[metric] + '曲线', 56, 104
    );
    var chartX = 56;
    var chartY = 150;
    var chartW = 888;
    var chartH = 250;
    ctx.strokeStyle = palette.grid;
    ctx.lineWidth = 1;
    for (var grid = 0; grid <= 4; grid++) {
      var gy = chartY + chartH / 4 * grid;
      ctx.beginPath();
      ctx.moveTo(chartX, gy);
      ctx.lineTo(chartX + chartW, gy);
      ctx.stroke();
    }
    var barW = Math.min(46, chartW / moods.length * 0.62);
    var step = chartW / moods.length;
    moods.forEach(function (entry, index) {
      var value = Math.max(0, Math.min(100, Number(entry[metric] || 0)));
      var height = Math.max(4, value / 100 * chartH);
      var x = chartX + step * index + (step - barW) / 2;
      var y = chartY + chartH - height;
      ctx.fillStyle = colors[metric];
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(x, y, barW, height, 6);
      } else {
        ctx.rect(x, y, barW, height);
      }
      ctx.fill();
      ctx.fillStyle = palette.value;
      ctx.font = '14px "Microsoft YaHei", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(Math.round(value), x + barW / 2, y - 8);
      ctx.fillStyle = palette.date;
      ctx.font = '12px "Microsoft YaHei", sans-serif';
      ctx.fillText(String(entry.date || '').slice(5), x + barW / 2, chartY + chartH + 24);
      ctx.textAlign = 'left';
    });
    ctx.fillStyle = palette.summary;
    ctx.font = '18px "Microsoft YaHei", sans-serif';
    ctx.fillText('收入 ' + Number(report.income || 0) + ' 元', 56, 462);
    ctx.fillText('支出 ' + Number(report.expense || 0) + ' 元', 300, 462);
    ctx.fillText('余额 ' + Number(report.balance || 0) + ' 元', 544, 462);
    ctx.fillText('关系 ' + String(report.affection_level || '陌生'), 788, 462);
    var day = new Date().toISOString().slice(0, 10);
    var download = function (href) {
      var link = document.createElement('a');
      link.href = href;
      link.download = '虚拟人生-周报图表-' + day + '.png';
      document.body.appendChild(link);
      link.click();
      link.remove();
    };
    if (canvas.toBlob) {
      canvas.toBlob(function (blob) {
        if (!blob) {
          download(canvas.toDataURL('image/png'));
          return;
        }
        var url = URL.createObjectURL(blob);
        download(url);
        window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      }, 'image/png');
    } else {
      download(canvas.toDataURL('image/png'));
    }
    showToast('周报图表已导出');
  }

  function weeklyHasData(report) {
    return Number(report.diary_count || 0) > 0 ||
      Number(report.expense || 0) > 0 ||
      Number(report.income || 0) > 0 ||
      Number(report.work_minutes || 0) > 0 ||
      Number(report.mood_average || 0) > 0;
  }

  function exportWeekly() {
    var report = state.weeklyReport;
    if (!report) {
      showToast('周报还没加载好');
      return;
    }
    var metric = state.weeklyMetric || 'mood';
    var metricLabel = metric === 'energy' ? '精力'
      : metric === 'satiety' ? '饱腹' : '心情';
    var bestEntry = null;
    var worstEntry = null;
    (report.moods || []).forEach(function (entry) {
      if (entry[metric] == null) return;
      var score = Number(entry[metric]);
      if (!bestEntry || score > Number(bestEntry[metric])) bestEntry = entry;
      if (!worstEntry || score < Number(worstEntry[metric])) worstEntry = entry;
    });
    var lines = [
      '项目,数值',
      '开始,' + String(report.start || ''),
      '结束,' + String(report.end || ''),
      '指标,' + metricLabel,
      '最高,' + (bestEntry
        ? String(bestEntry.date || '') + ' ' +
          Math.round(Number(bestEntry[metric]))
        : ''),
      '最低,' + (worstEntry
        ? String(worstEntry.date || '') + ' ' +
          Math.round(Number(worstEntry[metric]))
        : ''),
      '收入,' + Number(report.income || 0),
      '支出,' + Number(report.expense || 0),
      '余额,' + Number(report.balance || 0),
      '结余,' + Number(report.net == null
        ? Number(report.income || 0) - Number(report.expense || 0)
        : report.net),
      '日均支出,' + Number(report.average_expense == null
        ? Number(report.expense || 0) / Math.max(1, Number(report.days || 7))
        : report.average_expense),
      '工作分钟,' + Number(report.work_minutes || 0),
      '关系阶段,' + String(report.affection_level || ''),
      '关系增加,' + Number(report.affection_gained || 0),
      '日记篇数,' + Number(report.diary_count || 0),
      '阅读,' + String(
        periodBookReadingLabel(state.weeklyDays || 7) || ''
      ),
      '阅读天数,' + periodBookReadingDays(state.weeklyDays || 7)
    ];
    var previous = state.weeklyPrevious || {};
    if (previous.start && weeklyHasData(previous)) {
      var prevExpense = Number(previous.expense || 0);
      var prevWork = Number(previous.work_minutes || 0);
      var prevMood = Number(previous.mood_average || 0);
      var moodAverage = Number(report.mood_average || 0);
      lines.push(
        '上期开始,' + String(previous.start || ''),
        '上期结束,' + String(previous.end || ''),
        '上期支出,' + prevExpense,
        '支出变化,' + Math.round((Number(report.expense || 0) - prevExpense) * 100) / 100,
        '上期工作分钟,' + prevWork,
        '工作时间变化,' + Math.round(Number(report.work_minutes || 0) - prevWork),
        '上期心情均值,' + prevMood,
        '心情均值变化,' + Math.round((moodAverage - prevMood) * 10) / 10,
        '上期日记篇数,' + Number(previous.diary_count || 0),
        '日记篇数变化,' + (
          Number(report.diary_count || 0) - Number(previous.diary_count || 0)
        ),
        '上期关系增加,' + Number(previous.affection_gained || 0),
        '关系增加变化,' + (
          Number(report.affection_gained || 0) -
          Number(previous.affection_gained || 0)
        )
      );
    }
    lines.push('', '日期,心情,精力,饱腹');
    (report.moods || []).forEach(function (entry) {
      lines.push([
        String(entry.date || ''),
        entry.mood == null ? '' : entry.mood,
        entry.energy == null ? '' : entry.energy,
        entry.satiety == null ? '' : entry.satiety
      ].join(','));
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '虚拟人生-周报-' + String(report.end || new Date().toISOString().slice(0, 10)) + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('周报已导出');
  }

  function renderWeekly() {
    var body = $('weekly-body');
    var persona = (state.data && state.data.persona) || '';
    var days = Number(state.weeklyDays || 7);
    $('weekly-title').textContent = days >= 300
      ? '年度总结'
      : days >= 28
        ? '生活月报'
        : '生活周报';
    $('weekly-sub').textContent = days >= 300
      ? '最近三百六十五天'
      : days >= 28
        ? '最近三十天'
        : '最近七天';
    body.innerHTML = '<p class="inventory-empty">整理这一段时间...</p>';
    fetch('/api/weekly?persona=' + encodeURIComponent(persona) +
      '&days=' + days, {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '周报打不开');
        var report = data.report || {};
        var previous = data.previous || {};
        state.weeklyReport = report;
        state.weeklyPrevious = previous;
        var income = Number(report.income || 0);
        var expense = Number(report.expense || 0);
        var balance = Number(report.balance || 0);
        var affinity = Number(report.affection_gained || 0);
        var net = report.net == null ? income - expense : Number(report.net);
        var averageExpense = report.average_expense == null
          ? expense / Math.max(1, days)
          : Number(report.average_expense);
        var purchases = report.purchases || [];
        var entries = report.entries || [];
        var readingLabel = periodBookReadingLabel(days);
        var readingDays = periodBookReadingDays(days);
        var html = '<div class="weekly-range">' +
          escapeHtml(report.start || '') + ' → ' + escapeHtml(report.end || '') +
          '</div><div class="weekly-grid">' +
          '<div class="weekly-card"><small>收入</small><strong>+' + income + ' 元</strong></div>' +
          '<div class="weekly-card"><small>支出</small><strong>-' + expense + ' 元</strong></div>' +
          '<div class="weekly-card"><small>余额</small><strong>' + balance + ' 元</strong></div>' +
          '<div class="weekly-card"><small>结余</small><strong class="weekly-net ' +
          (net >= 0 ? 'positive' : 'negative') + '">' +
          (net >= 0 ? '+' : '') + Math.round(net * 100) / 100 +
          ' 元</strong></div>' +
          '<div class="weekly-card"><small>日均支出</small><strong>' +
          Math.round(averageExpense * 10) / 10 + ' 元</strong></div>' +
          '<div class="weekly-card"><small>工作</small><strong>' + Number(report.work_minutes || 0) + ' 分钟</strong></div>' +
          '<div class="weekly-card"><small>关系</small><strong>' +
          escapeHtml(report.affection_level || '陌生') + ' +' + affinity + '</strong></div>' +
          '<div class="weekly-card"><small>日记</small><strong>' +
          Number(report.diary_count || 0) + ' 篇</strong></div>' +
          (readingLabel
            ? '<div class="weekly-card"><small>阅读</small><strong>' +
              (readingDays > 0 ? readingDays + ' 天 · ' : '') +
              escapeHtml(readingLabel) + '</strong></div>'
            : '') +
          '</div>';
        if (previous.start && weeklyHasData(previous)) {
          var prevExpense = Number(previous.expense || 0);
          var prevWork = Number(previous.work_minutes || 0);
          var prevMood = Number(previous.mood_average || 0);
          var compareMood = Number(report.mood_average || 0);
          var expenseDiff = Math.round((expense - prevExpense) * 100) / 100;
          var workDiff = Math.round(
            Number(report.work_minutes || 0) - prevWork
          );
          var moodDiff = Math.round((compareMood - prevMood) * 10) / 10;
          var prevDiary = Number(previous.diary_count || 0);
          var diaryDiff = Number(report.diary_count || 0) - prevDiary;
          var prevAffection = Number(previous.affection_gained || 0);
          var affectionDiff = affinity - prevAffection;
          function compareText(value, unit, showSign) {
            var sign = value > 0 ? '+' : '';
            return sign + value + unit;
          }
          html += '<div class="weekly-section weekly-compare">' +
            '<h4>对比上期 · ' +
            escapeHtml(String(previous.start || '').slice(5)) + ' → ' +
            escapeHtml(String(previous.end || '').slice(5)) +
            '</h4><div class="weekly-compare-grid">' +
            '<div><small>支出</small><b class="' +
            (expenseDiff > 0 ? 'negative' : 'positive') + '">' +
            escapeHtml(compareText(expenseDiff, ' 元')) + '</b></div>' +
            '<div><small>工作</small><b>' +
            escapeHtml(compareText(workDiff, ' 分钟')) + '</b></div>' +
            '<div><small>心情均值</small><b class="' +
            (moodDiff < 0 ? 'negative' : 'positive') + '">' +
            escapeHtml(compareText(moodDiff, '')) + '</b></div>' +
            '<div><small>日记</small><b>' +
            escapeHtml(compareText(diaryDiff, ' 篇')) + '</b></div>' +
            '<div><small>关系</small><b class="' +
            (affectionDiff < 0 ? 'negative' : 'positive') + '">' +
            escapeHtml(compareText(affectionDiff, '')) + '</b></div>' +
            '</div></div>';
        }
        var moods = report.moods || [];
        var metric = state.weeklyMetric || 'mood';
        var metricLabel = metric === 'energy' ? '精力' : metric === 'satiety' ? '饱腹' : '心情';
        if (moods.length) {
          html += '<div class="weekly-section"><h4>' + metricLabel + '曲线 · 平均 ' +
            Number(report[metric + '_average'] || report.mood_average || 0) +
            ' / 100</h4>' +
            '<div class="mood-bars">';
          moods.slice(-14).forEach(function (entry) {
            var value = Math.max(0, Math.min(100, Number(entry[metric] || 0)));
            var height = Math.max(8, Math.round(value));
            html += '<div class="mood-bar" title="' +
              escapeHtml(entry.date || '') + ' · ' + metricLabel + ' ' +
              Math.round(value) + '">' +
              '<span style="height:' + height + '%"></span>' +
              '<small>' + escapeHtml(String(entry.date || '').slice(5)) + '</small>' +
              '</div>';
          });
          var bestEntry = null;
          var worstEntry = null;
          moods.slice(-14).forEach(function (entry) {
            if (entry[metric] == null) return;
            var score = Number(entry[metric]);
            if (!bestEntry || score > Number(bestEntry[metric])) bestEntry = entry;
            if (!worstEntry || score < Number(worstEntry[metric])) worstEntry = entry;
          });
          var extremes = bestEntry
            ? '<div class="weekly-extremes"><span>最高 ' +
              escapeHtml(String(bestEntry.date || '').slice(5)) + ' · ' +
              Math.round(Number(bestEntry[metric])) + '</span><span>最低 ' +
              escapeHtml(String(worstEntry.date || '').slice(5)) + ' · ' +
              Math.round(Number(worstEntry[metric])) + '</span></div>'
            : '';
          html += '</div>' + extremes + '</div>';
        }
        var expenseCategories = report.expense_categories || [];
        if (expenseCategories.length) {
          html += '<div class="weekly-section"><h4>支出分类</h4>';
          expenseCategories.slice(0, 6).forEach(function (item) {
            html += '<div class="weekly-category"><span>' +
              escapeHtml(item.label || '其他') + '</span><b>' +
              Number(item.amount || 0) + ' 元</b></div>';
          });
          html += '</div>';
        }
        var incomeCategories = report.income_categories || [];
        if (incomeCategories.length) {
          html += '<div class="weekly-section"><h4>收入分类</h4>';
          incomeCategories.slice(0, 5).forEach(function (item) {
            html += '<div class="weekly-category"><span>' +
              escapeHtml(item.label || '其他') + '</span><b>+' +
              Number(item.amount || 0) + ' 元</b></div>';
          });
          html += '</div>';
        }
        if (purchases.length) {
          html += '<div class="weekly-section"><h4>新物品</h4><p>' +
            escapeHtml(purchases.map(function (item) {
              return item.name || '物品';
            }).join('、')) + '</p></div>';
        }
        var topGoods = report.top_goods || [];
        if (topGoods.length) {
          html += '<div class="weekly-section"><h4>购买排行</h4>';
          topGoods.slice(0, 5).forEach(function (item) {
            html += '<div class="weekly-category"><span>' +
              escapeHtml(item.name || '物品') + ' ×' +
              Number(item.count || 0) + '</span><b>' +
              Number(item.amount || 0) + ' 元</b></div>';
          });
          html += '</div>';
        }
        if (entries.length) {
          html += '<div class="weekly-section"><h4>这一周</h4>';
          entries.slice(-5).forEach(function (entry) {
            html += '<div class="weekly-entry">' +
              '<span>' + escapeHtml(entry.date || '') + '</span>' +
              '<b>' + escapeHtml(entry.title || '') + '</b></div>';
          });
          html += '</div>';
        }
        body.innerHTML = html;
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '周报打不开') +
          '</p>';
      });
  }

  function openDiary() {
    state.diaryQuery = '';
    $('diary-search').value = '';
    document.querySelectorAll('[data-diary-filter]').forEach(function (button) {
      button.classList.toggle(
        'active',
        button.getAttribute('data-diary-filter') === (state.diaryFilter || 'all')
      );
    });
    $('diary-modal').classList.remove('hidden');
    renderDiary();
  }

  function closeDiary() {
    $('diary-modal').classList.add('hidden');
  }

  function openMemory() {
    $('memory-modal').classList.remove('hidden');
    renderMemory();
  }

  function closeMemory() {
    $('memory-modal').classList.add('hidden');
  }

  function openTrips(preserve) {
    if (!preserve) {
      state.tripsExpanded = {};
    }
    $('trips-title').textContent = '旅行计划';
    $('trips-sub').textContent = '正在翻她的旅行手账...';
    $('trips-body').innerHTML = '<p class="inventory-empty">正在翻旅行手账...</p>';
    $('trips-modal').classList.remove('hidden');
    fetch('/api/trips?persona=' + encodeURIComponent(
      (state.data && state.data.persona) || ''
    ), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '旅行计划打不开');
        state.tripsData = data;
        renderTrips();
      })
      .catch(function (error) {
        $('trips-body').innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '旅行计划打不开') +
          '</p>';
      });
  }

  function closeTrips() {
    $('trips-modal').classList.add('hidden');
  }

  function outfitCategoryLabel(category) {
    var labels = {
      hairstyle: '发型', headwear: '帽子与发饰', underwear: '内衣与打底',
      underpants: '内裤', top: '上装', bottom: '下装',
      dress: '连衣身着装', legwear: '袜子与腿部穿搭', outerwear: '外套',
      shoes: '鞋履', accessory: '配饰', bag: '包具',
      makeup: '妆容', fragrance: '香氛', other: '其他'
    };
    return labels[String(category || '')] || String(category || '');
  }

  function openOutfit() {
    var outfit = (state.data && state.data.outfit) || {};
    var items = outfit.items || [];
    if (!items.length) {
      showToast('今天还没有穿搭明细');
      return;
    }
    $('outfit-sub').textContent = outfit.style || outfit.summary || '她今天穿什么';
    $('outfit-body').innerHTML =
      (outfit.summary
        ? '<p class="outfit-summary">' + escapeHtml(outfit.summary) + '</p>'
        : '') +
      items.map(function (entry) {
        return '<div class="outfit-row"><span>' +
          escapeHtml(outfitCategoryLabel(entry.category)) + '</span><b>' +
          escapeHtml(entry.name) + '</b>' +
          (entry.details ? '<small>' + escapeHtml(entry.details) + '</small>' : '') +
          '</div>';
      }).join('');
    $('outfit-modal').classList.remove('hidden');
  }

  function exportOutfit() {
    var outfit = (state.data && state.data.outfit) || {};
    var items = outfit.items || [];
    if (!items.length) {
      showToast('今天还没有穿搭明细');
      return;
    }
    var day = String((state.data && state.data.plan_date) || '') ||
      new Date().toISOString().slice(0, 10);
    var lines = [
      '今日穿搭 · ' + day,
      '风格：' + String(outfit.style || ''),
      '总结：' + String(outfit.summary || '')
    ];
    items.forEach(function (entry) {
      lines.push('');
      lines.push('【' + outfitCategoryLabel(entry.category) + '】' +
        String(entry.name || ''));
      if (entry.details) lines.push('  ' + entry.details);
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/plain;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '今日穿搭-' + day + '.txt';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('穿搭详情已导出');
  }

  function closeOutfit() {
    $('outfit-modal').classList.add('hidden');
  }

  function openHealth() {
    var health = (state.data && state.data.health) || {};
    var status = String(health.status || '');
    var statusLabels = {
      healthy: '身体状态良好', sick: '生病中', recovering: '恢复中'
    };
    $('health-sub').textContent = statusLabels[status] || '她最近的身体状况';
    var parts = [];
    if (status === 'sick') {
      parts.push('<div class="health-row"><span>当前状态</span><b>生病中 · 第 ' +
        Math.max(1, Number(health.sick_days || 1)) + ' 天</b></div>');
    } else if (status === 'recovering') {
      parts.push('<div class="health-row"><span>当前状态</span><b>恢复中</b></div>');
    } else {
      parts.push('<div class="health-row"><span>当前状态</span><b>良好</b></div>');
    }
    if (Number(health.recovery_required_days || 0) > 0) {
      parts.push('<div class="health-row"><span>需要恢复</span><b>' +
        Number(health.recovery_required_days) + ' 天</b></div>');
    }
    if (Number(health.recent_illness_days || 0) > 0) {
      parts.push('<div class="health-row"><span>最近 30 天</span><b>生病 ' +
        Number(health.recent_illness_days) + ' 天</b></div>');
    }
    if (health.weak_constitution) {
      parts.push('<div class="health-row"><span>体质</span><b>偏弱</b></div>');
    }
    var recoveryLog = Array.isArray(health.recovery_log)
      ? health.recovery_log : [];
    var latestRecovery = recoveryLog.length &&
      recoveryLog[recoveryLog.length - 1] &&
      typeof recoveryLog[recoveryLog.length - 1] === 'object'
      ? recoveryLog[recoveryLog.length - 1] : null;
    if (latestRecovery) {
      var recoveryActions = Array.isArray(latestRecovery.actions)
        ? latestRecovery.actions : [];
      var harmfulActions = Array.isArray(latestRecovery.harmful)
        ? latestRecovery.harmful : [];
      if (recoveryActions.length || harmfulActions.length) {
        parts.push('<div class="health-section"><h4>今天的恢复</h4>' +
          '<div class="health-tags">' +
          recoveryActions.map(function (item) {
            return '<em>' + escapeHtml(item) + '</em>';
          }).join('') +
          harmfulActions.map(function (item) {
            return '<em class="warn">' + escapeHtml(item) + '</em>';
          }).join('') + '</div></div>');
      }
    }
    var episodes = health.episodes || [];
    if (episodes.length) {
      parts.push('<div class="health-section"><h4>生病记录</h4>' +
        episodes.slice(-8).reverse().map(function (item) {
          return '<div class="health-entry"><b>' +
            escapeHtml(item.onset || '') + ' → ' +
            escapeHtml(item.recovered || '仍在恢复') + '</b><small>' +
            Number(item.days || 0) + ' 天' +
            (item.note ? ' · ' + escapeHtml(item.note) : '') +
            '</small></div>';
        }).join('') + '</div>');
    }
    if (!episodes.length && status === 'healthy') {
      parts.push('<p class="inventory-empty">目前没有生病记录。</p>');
    }
    $('health-body').innerHTML = parts.join('');
    $('health-modal').classList.remove('hidden');
  }

  function exportHealth() {
    var health = (state.data && state.data.health) || {};
    var statusLabels = {
      healthy: '身体状态良好', sick: '生病中', recovering: '恢复中'
    };
    var day = new Date().toISOString().slice(0, 10);
    var lines = [
      '健康记录 · ' + day,
      '当前状态：' + (statusLabels[health.status] || '未知'),
      '已生病天数：' + Number(health.sick_days || 0),
      '预计恢复天数：' + Number(health.recovery_required_days || 0),
      '最近 30 天生病：' + Number(health.recent_illness_days || 0) + ' 天',
      '体质偏弱：' + (health.weak_constitution ? '是' : '否')
    ];
    var episodes = health.episodes || [];
    if (episodes.length) {
      lines.push('', '生病记录');
      episodes.forEach(function (item) {
        lines.push(String(item.onset || '') + ' → ' +
          String(item.recovered || '仍在恢复') + ' · ' +
          Number(item.days || 0) + ' 天' +
          (item.note ? ' · ' + item.note : ''));
      });
    }
    var recoveryLog = Array.isArray(health.recovery_log)
      ? health.recovery_log : [];
    var latestRecovery = recoveryLog.length &&
      recoveryLog[recoveryLog.length - 1] &&
      typeof recoveryLog[recoveryLog.length - 1] === 'object'
      ? recoveryLog[recoveryLog.length - 1] : null;
    if (latestRecovery) {
      var recoveryActions = Array.isArray(latestRecovery.actions)
        ? latestRecovery.actions : [];
      var harmfulActions = Array.isArray(latestRecovery.harmful)
        ? latestRecovery.harmful : [];
      if (recoveryActions.length || harmfulActions.length) {
        lines.push('', '今天的恢复');
        recoveryActions.forEach(function (item) {
          lines.push('✓ ' + item);
        });
        harmfulActions.forEach(function (item) {
          lines.push('! ' + item);
        });
      }
    }
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/plain;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '健康记录-' + day + '.txt';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('健康记录已导出');
  }

  function closeHealth() {
    $('health-modal').classList.add('hidden');
  }

  function activityTimeText(value) {
    var text = String(value || '');
    if (text.length >= 16) return text.slice(11, 16);
    return '';
  }

  function dateKeyFromDate(value) {
    return value.getFullYear() + '-' +
      String(value.getMonth() + 1).padStart(2, '0') + '-' +
      String(value.getDate()).padStart(2, '0');
  }

  function activityDayLabel(day) {
    if (!day || day === '未知日期') return '未知日期';
    var base = String((state.data && state.data.plan_date) || '') ||
      dateKeyFromDate(new Date());
    if (day === base) return '今天';
    var previous = new Date(base + 'T00:00:00');
    if (isFinite(previous.getTime())) {
      previous.setDate(previous.getDate() - 1);
      if (day === dateKeyFromDate(previous)) return '昨天';
    }
    return String(day || '').slice(5);
  }

  function openActivity(preserve) {
    state.activityEvents = [];
    if (!preserve) {
      state.activityQuery = '';
      $('activity-search').value = '';
    }
    $('activity-sub').textContent = '最近发生的小事';
    $('activity-body').innerHTML =
      '<p class="inventory-empty">正在整理最近的生活...</p>';
    $('activity-modal').classList.remove('hidden');
    fetch('/api/recent_activity?persona=' + encodeURIComponent(
      (state.data && state.data.persona) || ''
    ), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '动态打不开');
        state.activityEvents = data.events || [];
        renderActivity();
      })
      .catch(function (error) {
        $('activity-sub').textContent = '最近发生的小事';
        $('activity-body').innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '动态打不开') +
          '</p>';
      });
  }

  function resetActivityFilters() {
    state.activityFilter = 'all';
    saveSort('activity-filter', 'all');
    state.activityQuery = '';
    $('activity-search').value = '';
    renderActivity();
  }

  function renderActivity() {
    var events = state.activityEvents || [];
    var filters = [
      ['all', '全部'], ['diary', '日记'], ['world', '小世界'],
      ['cooking', '下厨'], ['money', '钱包'],
      ['garage', '出车'], ['health', '健康']
    ];
    var kindCounts = { all: events.length };
    events.forEach(function (event) {
      var kind = String(event.kind || '');
      kindCounts[kind] = (kindCounts[kind] || 0) + 1;
    });
    var filter = state.activityFilter || 'all';
    var query = String(state.activityQuery || '').trim().toLowerCase();
    var filtered = events.filter(function (event) {
      if (filter !== 'all' && event.kind !== filter) return false;
      if (!query) return true;
      return [event.title, event.detail, event.kind]
        .join(' ').toLowerCase().indexOf(query) >= 0;
    });
    $('activity-sub').textContent = events.length
      ? '共 ' + events.length + ' 条动态' +
        (filter === 'all' && !query ? '' : ' · 当前 ' + filtered.length + ' 条')
      : '最近发生的小事';
    var filtersHtml = '<div class="activity-filters">' +
      filters.map(function (item) {
        var count = kindCounts[item[0]] || 0;
        return '<button type="button" data-activity-filter="' + item[0] + '"' +
          (filter === item[0] ? ' class="active"' : '') + '>' +
          item[1] + (count ? ' <b>' + count + '</b>' : '') + '</button>';
      }).join('') + '</div>';
    if (!events.length) {
      $('activity-body').innerHTML =
        '<p class="inventory-empty">最近还没有生活动态。</p>';
      return;
    }
    if (!filtered.length) {
      var resetHtml = (filter !== 'all' || query)
        ? '<button type="button" class="mini-btn activity-reset" ' +
          'data-activity-reset="1">清除筛选</button>'
        : '';
      $('activity-body').innerHTML = filtersHtml +
        '<p class="inventory-empty">' +
        (query ? '没有匹配的动态。' : '这个分类还没有动态。') +
        '</p>' + resetHtml;
      return;
    }
    var groups = [];
    var groupMap = {};
    filtered.forEach(function (event) {
      var day = String(event.at || '').slice(0, 10) || '未知日期';
      if (!groupMap[day]) {
        groupMap[day] = [];
        groups.push(day);
      }
      groupMap[day].push(event);
    });
    $('activity-body').innerHTML = filtersHtml + groups.map(function (day) {
      return '<div class="activity-date">' +
        escapeHtml(activityDayLabel(day)) + '</div>' +
        groupMap[day].map(function (event) {
          return '<div class="activity-row clickable" data-activity-kind="' +
            escapeHtml(event.kind || '') + '" role="button" tabindex="0" ' +
            'title="查看详情"><span class="activity-icon">' +
            escapeHtml(event.icon || '·') + '</span><div class="activity-copy"><b>' +
            escapeHtml(event.title || '一件小事') + '</b><small>' +
            escapeHtml(event.detail || '') + '</small></div><em>' +
            escapeHtml(activityTimeText(event.at)) + '</em></div>';
        }).join('');
    }).join('');
  }

  function exportActivity() {
    var filter = state.activityFilter || 'all';
    var events = (state.activityEvents || []).filter(function (event) {
      return filter === 'all' || event.kind === filter;
    });
    if (!events.length) {
      showToast('当前分类还没有可导出的动态');
      return;
    }
    var kindLabels = {
      diary: '日记', world: '小世界', cooking: '下厨',
      money: '钱包', garage: '出车', health: '健康'
    };
    var lines = [['时间', '类型', '标题', '详情']
      .map(csvCell).join(',')];
    events.forEach(function (event) {
      lines.push([
        String(event.at || ''),
        kindLabels[event.kind] || String(event.kind || ''),
        String(event.title || ''),
        String(event.detail || '')
      ].map(csvCell).join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '生活动态-' + day + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('生活动态已导出');
  }

  function closeActivity() {
    $('activity-modal').classList.add('hidden');
  }

  function openActivityTarget(kind) {
    var actions = {
      diary: openDiary,
      world: openMemory,
      cooking: openCookModal,
      money: openWallet,
      garage: openGarage,
      health: openHealth
    };
    var action = actions[String(kind || '')];
    closeActivity();
    if (typeof action === 'function') {
      action();
    }
  }

  function tripRelativeText(trip, today) {
    var depart = new Date(String(trip.depart || '')).getTime();
    var back = new Date(String(trip.back || '')).getTime();
    var current = new Date(String(today || '')).getTime();
    if (!isFinite(depart) || !isFinite(back) || !isFinite(current)) return '';
    var day = 86400000;
    var before = Math.round((depart - current) / day);
    if (before > 0) return '还有 ' + before + ' 天出发';
    if (before === 0) return '今天出发';
    var after = Math.round((current - back) / day);
    if (after < 0) {
      return '旅行中第 ' + (Math.floor((current - depart) / day) + 1) + ' 天';
    }
    if (after === 0) return '今天返程';
    return '已结束 ' + after + ' 天';
  }

  function tripBucket(trip, today) {
    var phase = String(trip.phase || '');
    if (['depart', 'away', 'return'].indexOf(phase) >= 0 ||
        trip.status === 'active') {
      return 'ongoing';
    }
    var todayMs = new Date(String(today || '') + 'T00:00:00').getTime();
    var backMs = new Date(String(trip.back || '') + 'T00:00:00').getTime();
    if (trip.status === 'returned' || phase === 'afterglow' ||
        (isFinite(backMs) && isFinite(todayMs) && backMs < todayMs)) {
      return 'past';
    }
    return 'upcoming';
  }

  function exportTrips() {
    var data = state.tripsData || {};
    var filter = state.tripsFilter || 'all';
    var filterLabels = {
      all: '全部', upcoming: '即将出发',
      ongoing: '旅行中', past: '已结束'
    };
    var trips = (data.trips || []).filter(function (trip) {
      return filter === 'all' || tripBucket(trip, data.today) === filter;
    });
    if (!trips.length) {
      showToast(filter === 'all'
        ? '还没有可导出的旅行计划'
        : '当前分类没有可导出的旅程');
      return;
    }
    var lines = ['旅行计划 · ' + String(data.today || '') +
      (filter === 'all' ? '' : ' · ' + filterLabels[filter])];
    trips.forEach(function (trip) {
      lines.push('');
      lines.push('【' + String(trip.city || '远方') + '】' +
        String(trip.depart || '') + ' → ' + String(trip.back || '') +
        ' · ' + Number(trip.length || trip.days || 0) + ' 天 · ' +
        String(trip.transport || '') + ' · ' + String(trip.status || ''));
      lines.push('住宿：' + String(trip.lodging || '待定') +
        ' · 风格：' + String(trip.style || '随心'));
      (trip.itinerary || []).forEach(function (day) {
        lines.push(String(day.date || '') + ' ' + String(day.title || ''));
        (day.highlights || []).forEach(function (item) {
          lines.push('  - ' + item);
        });
      });
      if ((trip.packing || []).length) {
        lines.push('行李：' + trip.packing.join('、'));
      }
      if ((trip.foods || []).length) {
        lines.push('想吃：' + trip.foods.join('、'));
      }
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/plain;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '旅行计划-' + String(data.today || '') +
      (filter === 'all' ? '' : '-' + filterLabels[filter]) + '.txt';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('旅行计划已导出');
  }

  function renderTrips() {
    var body = $('trips-body');
    var data = state.tripsData || {};
    var trips = data.trips || [];
    var filter = state.tripsFilter || 'all';
    var filtered = trips.filter(function (trip) {
      return filter === 'all' || tripBucket(trip, data.today) === filter;
    });
    $('trips-sub').textContent = trips.length
      ? '共 ' + trips.length + ' 段旅程' +
        (filter === 'all' ? '' : ' · 当前 ' + filtered.length + ' 段')
      : '她还没有安排旅行';
    if (!trips.length) {
      body.innerHTML = '<p class="inventory-empty">她还没有安排旅行。</p>';
      return;
    }
    var filters = [
      ['all', '全部'], ['upcoming', '即将出发'],
      ['ongoing', '旅行中'], ['past', '已结束']
    ];
    var tripCounts = { all: trips.length, upcoming: 0, ongoing: 0, past: 0 };
    trips.forEach(function (trip) {
      var bucket = tripBucket(trip, data.today);
      if (tripCounts[bucket] != null) tripCounts[bucket] += 1;
    });
    var filtersHtml = '<div class="trips-filters">' +
      filters.map(function (item) {
        return '<button type="button" data-trips-filter="' + item[0] + '"' +
          (filter === item[0] ? ' class="active"' : '') + '>' +
          item[1] + ' <b>' + (tripCounts[item[0]] || 0) +
          '</b></button>';
      }).join('') + '</div>';
    if (!filtered.length) {
      body.innerHTML = filtersHtml +
        '<p class="inventory-empty">这个分类还没有旅程。</p>';
      return;
    }
    var statusLabels = {
      planned: '计划中', active: '旅行中',
      returned: '已结束', cancelled: '已取消'
    };
    var phaseLabels = {
      eve: '明天出发', countdown: '出发倒计时',
      depart: '今天出发', away: '旅行中',
      return: '今天返程', afterglow: '旅行余韵'
    };
    body.innerHTML = filtersHtml + filtered.map(function (trip, index) {
      var key = String(trip.id || index);
      var expanded = Boolean(state.tripsExpanded[key]);
      var itinerary = trip.itinerary || [];
      var packing = trip.packing || [];
      var foods = trip.foods || [];
      var phase = phaseLabels[trip.phase] || '';
      var status = phase || statusLabels[trip.status] || '计划中';
      var detail = '';
      if (expanded) {
        detail = '<div class="trips-detail">' +
          itinerary.map(function (day) {
            return '<div class="trips-day"><b>' +
              escapeHtml(String(day.date || '').slice(5)) + ' · ' +
              escapeHtml(day.title || '') + '</b><small>' +
              escapeHtml((day.highlights || []).join('、')) +
              '</small></div>';
          }).join('') +
          (packing.length
            ? '<div class="trips-tags"><span>行李</span>' +
              packing.map(function (item) {
                return '<em>' + escapeHtml(item) + '</em>';
              }).join('') + '</div>'
            : '') +
          (foods.length
            ? '<div class="trips-tags"><span>想吃</span>' +
              foods.map(function (item) {
                return '<em>' + escapeHtml(item) + '</em>';
              }).join('') + '</div>'
            : '') +
          '</div>';
      }
      return '<div class="trips-card"><div class="trips-card-head"><b>' +
        escapeHtml(trip.city || '远方') + '</b><span>' +
        escapeHtml(status) + '</span></div>' +
        '<small>' + escapeHtml(trip.depart || '') + ' → ' +
        escapeHtml(trip.back || '') + ' · ' +
        Number(trip.length || trip.days || 0) + ' 天 · ' +
        escapeHtml(trip.transport || '出发') + '</small>' +
        '<small class="trips-relative">' +
        escapeHtml(tripRelativeText(trip, data.today)) + '</small>' +
        '<p>' + escapeHtml(trip.lodging || '住处待定') +
        (trip.style ? ' · ' + escapeHtml(trip.style) : '') + '</p>' +
        '<button type="button" class="mini-btn" data-trips-toggle="' +
        escapeHtml(key) + '">' +
        (expanded ? '收起行程' : '展开行程') + '</button>' +
        detail + '</div>';
    }).join('');
  }

  function memoryEntry(entry, showDate) {
    var source = String(entry.source || '');
    var label = source === 'weekly' ? '周记'
      : source === 'monthly' ? '月记'
        : source === 'yearly' ? '年记'
          : source === 'anniversary' ? '纪念日'
            : source === 'outing' ? '兜风'
              : '日记';
    return '<div class="memory-entry"><div class="memory-entry-head">' +
      (showDate === false ? '' : '<span>' +
        escapeHtml(String(entry.date || '')) + '</span>') + '<b>' +
      escapeHtml(entry.title || label) + '</b><small>' + label + '</small></div>' +
      '<p>' + escapeHtml(String(entry.summary || '').slice(0, 220)) + '</p></div>';
  }

  function memoryEntriesGrouped(entries, limit) {
    var sorted = entries.slice().reverse();
    if (limit) sorted = sorted.slice(0, limit);
    var groups = {};
    var order = [];
    sorted.forEach(function (entry) {
      var day = String(entry.date || '未知日期');
      if (!groups[day]) {
        groups[day] = [];
        order.push(day);
      }
      groups[day].push(entry);
    });
    return order.map(function (day) {
      return '<div class="memory-date-group"><h5>' + escapeHtml(day) +
        '</h5>' + groups[day].map(function (entry) {
          return memoryEntry(entry, false);
        }).join('') + '</div>';
    }).join('');
  }

  function memorySearchText(entry) {
    return [
      entry.date, entry.title, entry.summary, entry.source
    ].join(' ').toLowerCase();
  }

  function memoryEntryMatches(entry, query) {
    if (!query) return true;
    return memorySearchText(entry).indexOf(query) >= 0;
  }

  function renderMemoryLists() {
    var lists = $('memory-lists');
    if (!lists) return;
    var memory = state.memoryData || {};
    var filter = state.memoryFilter || 'all';
    var query = String(state.memoryQuery || '').trim().toLowerCase();
    var longTerm = (memory.long_term || []).filter(function (entry) {
      return memoryEntryMatches(entry, query);
    });
    var recent = (memory.recent || []).filter(function (entry) {
      return memoryEntryMatches(entry, query);
    });
    var milestones = (memory.milestones || []).filter(function (item) {
      return !query || String(item.level || '').toLowerCase().indexOf(query) >= 0;
    });
    var sections = [];
    if (filter === 'all' || filter === 'long') {
      var longHtml = '<div class="memory-section"><h4>长期记忆</h4>';
      if (!longTerm.length) {
        longHtml += '<p class="memory-empty">没有匹配的周记/月记/年记。</p>';
      } else {
        longHtml += memoryEntriesGrouped(longTerm);
      }
      sections.push(longHtml + '</div>');
    }
    if (filter === 'all' || filter === 'recent') {
      var recentHtml = '<div class="memory-section"><h4>最近的日子</h4>';
      if (!recent.length) {
        recentHtml += '<p class="memory-empty">没有匹配的日记。</p>';
      } else {
        recentHtml += memoryEntriesGrouped(recent, 8);
      }
      sections.push(recentHtml + '</div>');
    }
    if (filter === 'all' || filter === 'relation') {
      var relationHtml = '<div class="memory-section"><h4>关系年表</h4>';
      if (!milestones.length) {
        relationHtml += '<p class="memory-empty">没有匹配的关系里程碑。</p>';
      } else {
        milestones.slice().reverse().forEach(function (item) {
          relationHtml += '<div class="memory-milestone"><span>' +
            escapeHtml(String(item.at || '').slice(0, 10)) + '</span><b>' +
            escapeHtml(item.level || '') + '</b></div>';
        });
      }
      sections.push(relationHtml + '</div>');
    }
    lists.innerHTML = sections.join('') ||
      '<p class="memory-empty">没有匹配的记忆。</p>';
  }

  function csvCell(value) {
    var text = value == null ? '' : String(value);
    return '"' + text.replace(/"/g, '""') + '"';
  }

  function exportMemory() {
    var memory = state.memoryData || {};
    var filter = state.memoryFilter || 'all';
    var query = String(state.memoryQuery || '').trim().toLowerCase();
    var lines = [];
    if (filter === 'relation') {
      lines.push('日期,关系阶段');
      (memory.milestones || []).forEach(function (item) {
        if (query && String(item.level || '').toLowerCase().indexOf(query) < 0) return;
        lines.push(csvCell(String(item.at || '').slice(0, 10)) + ',' +
          csvCell(item.level || ''));
      });
    } else {
      var entries = [];
      if (filter === 'all' || filter === 'long') {
        entries = entries.concat(memory.long_term || []);
      }
      if (filter === 'all' || filter === 'recent') {
        entries = entries.concat(memory.recent || []);
      }
      entries = entries.filter(function (entry) {
        return memoryEntryMatches(entry, query);
      });
      var sourceLabels = {
        weekly: '周记', monthly: '月记', yearly: '年记',
        anniversary: '纪念日', outing: '兜风'
      };
      lines.push('日期,类型,标题,内容');
      entries.forEach(function (entry) {
        var source = String(entry.source || '');
        lines.push([
          csvCell(entry.date || ''),
          csvCell(sourceLabels[source] || '日记'),
          csvCell(entry.title || ''),
          csvCell(entry.summary || '')
        ].join(','));
      });
    }
    if (lines.length <= 1) {
      showToast('没有可导出的记忆');
      return;
    }
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '虚拟人生-记忆-' + day + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('记忆已导出');
  }

  function renderMemory() {
    var body = $('memory-body');
    var persona = (state.data && state.data.persona) || '';
    body.innerHTML = '<p class="inventory-empty">正在翻记忆...</p>';
    fetch('/api/memory?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '记忆打不开');
        var memory = data.memory || {};
        state.memoryData = memory;
        var relation = memory.relationship || {};
        var world = memory.world_event || {};
        var memoryCounts = {
          all: (memory.long_term || []).length +
            (memory.recent || []).length +
            (memory.milestones || []).length,
          long: (memory.long_term || []).length,
          recent: (memory.recent || []).length,
          relation: (memory.milestones || []).length
        };
        var html = '<div class="memory-summary">' +
          '<div><small>关系</small><b>' + escapeHtml(relation.level || '陌生') +
          ' · ' + Number(relation.score || 0) + '</b></div>' +
          '<div><small>认识</small><b>' + Number(relation.days_known || 0) +
          ' 天</b></div>' +
          '<div><small>称呼</small><b>' + escapeHtml(relation.nickname || '主人') +
          '</b></div></div>';
        if (world && world.summary) {
          html += '<div class="memory-world"><small>今天的小世界</small>' +
            (world.title ? '<b>' + escapeHtml(world.title) + '</b>' : '') +
            '<p>' + escapeHtml(world.summary) + '</p></div>';
        }
        var worldHistory = (memory.world_history || []).filter(function (item) {
          return String(item.date || '') !== String(world.date || '');
        }).slice(0, 5);
        if (worldHistory.length) {
          html += '<div class="memory-world-history"><small>最近的小世界</small>' +
            worldHistory.map(function (item) {
              return '<div class="memory-world-row" title="' +
                escapeHtml(item.summary || '') + '"><span>' +
                escapeHtml(String(item.date || '').slice(5)) + '</span><b>' +
                escapeHtml(item.title || '小事') + '</b></div>';
            }).join('') + '</div>';
        }
        html += '<div class="memory-tools">' +
          '<input id="memory-search" type="search" placeholder="搜索日期、标题或内容">' +
          '<div class="memory-filters">' + [
            ['all', '全部'], ['long', '长期'], ['recent', '最近'], ['relation', '关系']
          ].map(function (item) {
            return '<button type="button" data-memory-filter="' + item[0] + '"' +
              (state.memoryFilter === item[0] ? ' class="active"' : '') + '>' +
              item[1] + ' <b>' + (memoryCounts[item[0]] || 0) +
              '</b></button>';
          }).join('') + '</div>' +
          '<button type="button" class="memory-export" id="memory-export">导出</button>' +
          '</div>' +
          '<div id="memory-lists"></div>';
        body.innerHTML = html;
        var search = $('memory-search');
        if (search) {
          search.value = state.memoryQuery || '';
          search.addEventListener('input', function () {
            state.memoryQuery = search.value;
            renderMemoryLists();
          });
        }
        body.querySelectorAll('[data-memory-filter]').forEach(function (button) {
          button.addEventListener('click', function () {
            state.memoryFilter = button.getAttribute('data-memory-filter') || 'all';
            saveSort('memory-filter', state.memoryFilter);
            body.querySelectorAll('[data-memory-filter]').forEach(function (item) {
              item.classList.toggle(
                'active',
                item.getAttribute('data-memory-filter') === state.memoryFilter
              );
            });
            renderMemoryLists();
          });
        });
        var exportButton = $('memory-export');
        if (exportButton) exportButton.addEventListener('click', exportMemory);
        renderMemoryLists();
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '记忆打不开') +
          '</p>';
      });
  }

  function exportDiary() {
    var persona = (state.data && state.data.persona) || '';
    fetch('/api/diary?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '日记打不开');
        var entries = filterDiaryEntries(
          data.entries || [],
          state.diaryQuery,
          state.diaryFilter
        );
        if (!entries.length) {
          showToast('当前筛选没有可导出的日记');
          return;
        }
        var labels = {
          ai: 'AI 日记', weekly: '周记', monthly: '月记', yearly: '年记',
          anniversary: '纪念日', outing: '兜风'
        };
        var lines = ['日期,来源,标题,内容'];
        entries.forEach(function (entry) {
          lines.push([
            csvCell(entry.date || ''),
            csvCell(labels[entry.source] || '日记'),
            csvCell(entry.title || ''),
            csvCell(entry.summary || '')
          ].join(','));
        });
        var day = new Date().toISOString().slice(0, 10);
        var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
          type: 'text/csv;charset=utf-8'
        });
        var url = URL.createObjectURL(blob);
        var link = document.createElement('a');
        link.href = url;
        link.download = '虚拟人生-日记-' + day + '.csv';
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
        showToast('日记已导出');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '导出失败');
      });
  }

  function diaryMatches(entry, query) {
    if (!query) return true;
    return [
      entry.date, entry.title, entry.summary, entry.source
    ].join(' ').toLowerCase().indexOf(query) >= 0;
  }

  function filterDiaryEntries(entries, query, diaryFilter) {
    var text = String(query || '').trim().toLowerCase();
    var filter = diaryFilter || 'all';
    return (entries || []).filter(function (entry) {
      var source = String(entry.source || '');
      if (filter === 'ai' && ['ai', 'auto'].indexOf(source) < 0) return false;
      if (
        filter === 'weekly' &&
        ['weekly', 'monthly', 'yearly'].indexOf(source) < 0
      ) return false;
      if (
        filter === 'special' &&
        ['anniversary', 'outing'].indexOf(source) < 0
      ) return false;
      return diaryMatches(entry, text);
    });
  }

  function updateDiaryFilterCounts() {
    var entries = state.diaryEntries || [];
    var labels = {
      all: '全部', ai: '她写的',
      weekly: '周记/月记', special: '纪念/兜风'
    };
    document.querySelectorAll('[data-diary-filter]').forEach(function (button) {
      var key = button.getAttribute('data-diary-filter') || 'all';
      var count = filterDiaryEntries(entries, '', key).length;
      button.textContent = labels[key] || key;
      var badge = document.createElement('b');
      badge.textContent = String(count);
      button.appendChild(document.createTextNode(' '));
      button.appendChild(badge);
    });
  }

  function renderDiaryList() {
    var body = $('diary-body');
    var sub = $('diary-sub');
    var entries = state.diaryEntries || [];
    updateDiaryFilterCounts();
    var query = String(state.diaryQuery || '').trim().toLowerCase();
    var diaryFilter = state.diaryFilter || 'all';
    var filtered = filterDiaryEntries(entries, query, diaryFilter);
    if (sub) {
      sub.textContent = query || diaryFilter !== 'all'
        ? '筛选出 ' + filtered.length + ' / ' + entries.length + ' 篇'
        : '她记住的日子 · 共 ' + entries.length + ' 篇';
    }
    if (!entries.length) {
      body.innerHTML = '<p class="inventory-empty">还没有写日记。</p>';
      return;
    }
    if (!filtered.length) {
      body.innerHTML = '<p class="inventory-empty">没有匹配的日记。</p>';
      return;
    }
    var groups = {};
    var order = [];
    filtered.forEach(function (entry) {
      var day = String(entry.date || '未知日期');
      if (!groups[day]) {
        groups[day] = [];
        order.push(day);
      }
      groups[day].push(entry);
    });
    var sourceLabels = {
      ai: '她写的', auto: '每日手记', weekly: '周记', monthly: '月记', yearly: '年记',
      anniversary: '纪念日', outing: '兜风'
    };
    body.innerHTML = order.map(function (day) {
      return '<div class="diary-day-group"><div class="diary-day-head">' +
        escapeHtml(day) + '</div>' + groups[day].map(function (entry) {
          return '<article class="diary-entry">' +
            '<div class="diary-date">' +
            escapeHtml(sourceLabels[entry.source] || '日记') + '</div>' +
            '<div class="diary-entry-title">' + escapeHtml(entry.title || '') + '</div>' +
            '<div class="diary-text">' + escapeHtml(entry.summary || '') + '</div>' +
            '</article>';
        }).join('') + '</div>';
    }).join('');
  }

  function renderDiary() {
    var body = $('diary-body');
    var persona = (state.data && state.data.persona) || '';
    body.innerHTML = '<p class="inventory-empty">翻日记中...</p>';
    fetch('/api/diary?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '日记打不开');
        state.diaryEntries = (data.entries || []).slice().reverse();
        renderDiaryList();
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '日记打不开') +
          '</p>';
      });
  }

  function exportShelf() {
    var books = state.visibleShelf || [];
    if (!books.length) {
      showToast('当前筛选没有可导出的书');
      return;
    }
    var reading = bookReadingStore();
    var lines = [[
      '书名', '类型', '状态', '当前章', '总章', '进度', '笔记', '累计阅读'
    ].map(csvCell).join(',')];
    books.forEach(function (book) {
      var total = Math.max(1, Number(book.total_chapters) || 1);
      var chapter = Math.max(0, Number(book.chapter) || 0);
      var percent = book.finished
        ? 100
        : Math.min(100, Math.round(chapter / total * 100));
      var status = book.finished ? '读完' : (chapter > 0 ? '在读' : '未读');
      var seconds = Number(reading[String(book.id || '')] || 0);
      lines.push([
        book.title || '', book.genre || '', status, chapter, total,
        percent + '%', Number(book.notes || 0), formatReadingSeconds(seconds)
      ].map(csvCell).join(','));
    });
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '书架-' + dateKeyFromDate(new Date()) + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('书架已导出');
  }

  function openInventory(anchor) {
    var search = $('inventory-search');
    if (search) search.value = state.inventoryQuery || '';
    renderInventory();
    $('inventory-modal').classList.remove('hidden');
    if (anchor) {
      var target = $(anchor);
      if (target && target.scrollIntoView) {
        target.scrollIntoView({ block: 'start', behavior: 'auto' });
      }
    }
  }

  function closeInventory() {
    $('inventory-modal').classList.add('hidden');
  }

  function exportInventory() {
    var data = state.data || {};
    var query = String(state.inventoryQuery || '').trim().toLowerCase();
    var match = function (parts) {
      return !query || parts.join(' ').toLowerCase().indexOf(query) >= 0;
    };
    var shelf = (data.bookshelf || []).filter(function (book) {
      var filter = state.shelfFilter || 'all';
      if (filter === 'finished' && !book.finished) return false;
      if (filter === 'reading' &&
          (book.finished || Number(book.chapter || 0) <= 0)) return false;
      if (filter === 'unread' &&
          (book.finished || Number(book.chapter || 0) > 0)) return false;
      return match([book.title, book.genre, book.author]);
    });
    var possessions = ((data.money && data.money.possessions) || [])
      .filter(function (item) {
        return match([item.name, item.category, item.room]);
      });
    if (!shelf.length && !possessions.length) {
      showToast(query || (state.shelfFilter || 'all') !== 'all'
        ? '当前筛选没有可导出的物品'
        : '还没有物品可以导出');
      return;
    }
    var lines = ['类型,名称,分类,房间或进度,价格'];
    possessions.forEach(function (item) {
      lines.push([
        csvCell('物品'),
        csvCell(item.name || ''),
        csvCell(item.category || ''),
        csvCell(item.room || ''),
        Number.isFinite(Number(item.price)) ? Number(item.price) : ''
      ].join(','));
    });
    shelf.forEach(function (book) {
      var total = Math.max(1, Number(book.total_chapters) || 1);
      var progress = book.finished
        ? '读完'
        : '第 ' + Number(book.chapter || 0) + '/' + total + ' 章';
      lines.push([
        csvCell('书籍'),
        csvCell(book.title || ''),
        csvCell(book.genre || ''),
        csvCell(progress),
        ''
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var filtered = Boolean(query) || (state.shelfFilter || 'all') !== 'all';
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '物品清单-' + day + (filtered ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('物品清单已导出');
  }

  function onRoom3DItemDrop(info) {
    if (!info || !info.id) return;
    var item = (state.homeItems || []).find(function (entry) {
      return String(entry.id) === String(info.id);
    }) || info.item || null;
    var placed = Boolean(item && item.placed);
    var url = placed ? '/api/place_item' : '/api/decor/place';
    var payload = placed
      ? {
          item: (item && (item.possession_id || item.name)) || info.id,
          room: info.room,
          x: info.x,
          y: info.y,
          z_cm: info.z_cm || 0,
          surface_id: info.surface_id || ''
        }
      : {
          persona: (state.data && state.data.persona) || '',
          item_id: info.id,
          room: info.room,
          x: info.x,
          y: info.y
        };
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '移不动');
        showToast('已调整位置');
        fetchHomeItems();
        fetchState();
        if (state.decorMode) fetchDecorItems(false);
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '移不动');
      });
  }

  // 3D 脚本按需加载（见 05a-render-mode.js），加载完成后才接上拖放与点击回调。
  function wire3D() {
    if (window.Room3D) {
      window.Room3D.onItemDrop = onRoom3DItemDrop;
      window.Room3D.onPropClick = function (info) {
        if (!info || !info.id) return;
        if (/^(home_car|garage_jeep|garage_sports)$/.test(String(info.id))) {
          openVehicle(vehicleKeyFromCar(String(info.id)));
          return;
        }
        var hitItem = (state.homeItems || []).find(function (entry) {
          return String(entry.id) === String(info.id);
        });
        if (hitItem) {
          openItem(hitItem.id);
          return;
        }
        openGenericProp(info);
      };
    }
  }

  function init() {
    wire3D();
    try {
      state.animations = localStorage.getItem('vl-anim') !== 'off';
    } catch (e) {
      state.animations = true;
    }
    try {
      var savedBookFont = parseFloat(localStorage.getItem('vl-book-font'));
      if (savedBookFont >= 0.8 && savedBookFont <= 1.8) {
        state.bookFontScale = savedBookFont;
      }
    } catch (e) {
      state.bookFontScale = 1;
    }
    applyBookFontScale();
    try {
      var savedBookTheme = localStorage.getItem('vl-book-theme');
      if (['dark', 'sepia', 'light'].indexOf(savedBookTheme) >= 0) {
        state.bookTheme = savedBookTheme;
      }
    } catch (e) {
      state.bookTheme = 'dark';
    }
    applyBookTheme();
    var pageParams = new URLSearchParams(window.location.search);
    if (pageParams.get('scene') && SCENES.some(function(s) { return s.key === pageParams.get('scene'); })) state.previewScene = pageParams.get('scene');
    if (/^[12]$/.test(pageParams.get('floor') || '')) state.previewFloor = Number(pageParams.get('floor'));
    document.querySelectorAll('.floor-tab').forEach(function(b) { b.addEventListener('click', function() { state.previewFloor = Number(b.dataset.floor); renderHome(); }); });
    $('floor-follow').addEventListener('click', function() { state.previewFloor = null; renderHome(); });
    $('home-stage').addEventListener('click', function(event) {
      if (cameraMode) return;
      var stairNode = event.target.closest('[data-stair-floor]');
      if (stairNode) {
        event.preventDefault();
        state.previewFloor = Number(stairNode.getAttribute('data-stair-floor')) || 2;
        renderHome();
        showToast('顺着楼梯上到 ' + state.previewFloor + 'F');
        return;
      }
      var roomNode = event.target.closest('.studio-room');
      if (!roomNode) return;
      var roomName = roomNode.getAttribute('data-room');
      if (!roomName || !window.SceneStudio) return;
      state.previewRoom = roomName;
      state.previewFloor = SceneStudio.floorFor(roomName);
      renderHome();
      renderScene(true);
      showToast('查看 ' + roomName);
    });
    $('home-stage').addEventListener('keydown', function(event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var stairNode = event.target.closest('[data-stair-floor]');
      if (!stairNode) return;
      event.preventDefault();
      state.previewFloor = Number(stairNode.getAttribute('data-stair-floor')) || 2;
      renderHome();
      showToast('顺着楼梯上到 ' + state.previewFloor + 'F');
    });
    $('scene-stage').addEventListener('click', function(event) {
      var car = event.target.closest('.garage-car-hit');
      if (!car) return;
      event.preventDefault();
      openVehicle(vehicleKeyFromCar(car.getAttribute('data-car')));
    });
    ['click', 'keydown'].forEach(function(type) { $('scene-stage').addEventListener(type, function(event) { if (type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return; if (state.decorSuppressClick) { state.decorSuppressClick = false; event.preventDefault(); event.stopPropagation(); return; } var hit = event.target.closest('.furniture-hit'); if (hit) { event.preventDefault(); openItem(hit.getAttribute('data-id')); } }); });
    if (pageParams.get('item')) state.pendingItem = pageParams.get('item');
    applyAnimations();
    applyRenderMode();
    if (want3D()) ensure3DScripts('core');
    if ($('render-toggle')) $('render-toggle').addEventListener('click', cycleRenderMode);
    $('anim-toggle').addEventListener('click', function () {
      state.animations = !state.animations;
      try { localStorage.setItem('vl-anim', state.animations ? 'on' : 'off'); } catch (e) {}
      applyAnimations();
      render();
    });
    $('decor-toggle').addEventListener('click', function () {
      if (state.decorMode) {
        exitDecorMode();
        return;
      }
      openDecorDrawer();
    });
    $('items-toggle').addEventListener('click', function () {
      if (state.decorMode) exitDecorMode();
      toggleItemDrawer();
    });
    $('item-search').addEventListener('input', function () {
      state.itemQuery = $('item-search').value;
      renderItemDrawer();
    });
    $('fridge-toggle').addEventListener('click', function () {
      if (state.homeItems && state.homeItems.length) {
        openItem('fridge');
        return;
      }
      state.pendingItem = 'fridge';
      fetchHomeItems();
    });
    $('drawer-close').addEventListener('click', function () {
      toggleItemDrawer(false);
    });
    $('item-close').addEventListener('click', function () {
      closeItem();
    });
    $('home-svg').addEventListener('click', function (event) {
      var stair = event.target.closest('[data-stair-floor]');
      if (stair) {
        event.preventDefault();
        state.previewFloor = Number(stair.getAttribute('data-stair-floor')) || 1;
        renderHome();
        showToast('顺着楼梯到 ' + state.previewFloor + 'F');
        return;
      }
      var car = event.target.closest('.garage-car-hit');
      if (car) {
        event.preventDefault();
        openVehicle(vehicleKeyFromCar(car.getAttribute('data-car')));
        return;
      }
      var hit = event.target.closest('.furniture-hit');
      if (!hit) return;
      openItem(hit.getAttribute('data-id'));
    });
    $('home-svg').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var stair = event.target.closest('[data-stair-floor]');
      if (stair) {
        event.preventDefault();
        state.previewFloor = Number(stair.getAttribute('data-stair-floor')) || 1;
        renderHome();
        showToast('顺着楼梯到 ' + state.previewFloor + 'F');
        return;
      }
      var car = event.target.closest('.garage-car-hit');
      if (car) {
        event.preventDefault();
        openVehicle(vehicleKeyFromCar(car.getAttribute('data-car')));
        return;
      }
      var hit = event.target.closest('.furniture-hit');
      if (!hit) return;
      event.preventDefault();
      openItem(hit.getAttribute('data-id'));
    });
    $('item-groups').addEventListener('click', function (event) {
      var button = event.target.closest('.item-chip');
      if (!button) return;
      openItem(button.getAttribute('data-id'));
    });
    $('item-actions').addEventListener('click', function (event) {
      var button = event.target.closest('.pop-action');
      if (!button || !state.selectedItem) return;
      interactItemAction(
        state.selectedItem,
        button.getAttribute('data-action'),
        button
      );
    });
    $('interact-action').addEventListener('click', function () {
      var item = state.selectedItem;
      if (!item) return;
      if (item.generic_prop) {
        var genericAction = Array.isArray(item.actions) && item.actions.length
          ? item.actions[0] : '看看';
        interactItemAction(item, genericAction, null);
        return;
      }
      if (String(item.id) === 'bed') {
        var waking = Boolean(state.userSleeping);
        startInteraction({
          kind: 'chat',
          item_id: 'bed',
          action: waking ? '起床' : '睡觉',
          text: waking ? '我醒了，起床了。' : '我上床睡觉了，晚安。'
        }, waking ? '她抬起头' : '她放轻声音');
        showToast(waking ? '已告诉她你醒了' : '已告诉她你上床睡了');
        state.userSleeping = !waking;
        var button = $('interact-action');
        if (button) button.textContent = waking ? '我上床睡了' : '我醒了，起床';
        return;
      }
      if (isGameItem(item)) {
        openGameModal();
        return;
      }
      var isDish = String(item.id) === 'dining_table' ||
        String(item.name || '').indexOf('餐桌') >= 0;
      var action = Array.isArray(item.actions) && item.actions.length ? item.actions[0] : '';
      if (item.placed && ['吃掉', '喝掉', '使用'].indexOf(action) >= 0) {
        useInventoryItem(item.name);
        closeItem();
        return;
      }
      startInteraction({
        kind: 'chat',
        item_id: item.id,
        item_name: item.name || '',
        room: item.room || '',
        action: action,
        text: '我在' + (item.room || '') + '的' + (item.name || '这里') +
          '，想' + (action || '待一会儿') + '，你在干嘛？'
      }, isDish ? '她坐下来' : '她抬起头');
    });
    $('talk-send').addEventListener('click', sendChat);
    $('talk-input').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        sendChat();
      }
    });
    $('fridge-random').addEventListener('click', function () {
      randomFridgeRecipe();
    });
    $('fridge-refresh').addEventListener('click', function () {
      loadFridge();
    });
    $('fridge-export').addEventListener('click', exportFridge);
    $('fridge-search').addEventListener('input', function () {
      state.fridgeQuery = $('fridge-search').value;
      renderFridge();
    });
    $('persona-cycle').addEventListener('click', function () {
      var list = (state.data && state.data.personas) || [];
      if (list.length < 2) return;
      var index = -1;
      for (var i = 0; i < list.length; i++) {
        if (list[i].id === state.persona) index = i;
      }
      state.persona = list[(index + 1) % list.length].id;
      state.previewScene = null;
      fetchState();
    });
    $('follow-btn').addEventListener('click', function () {
      state.previewScene = null;
      renderScene(true);
      renderScenePicker(true);
    });
    $('preview-return').addEventListener('click', function () {
      if (cancelPlacement()) return;
      state.previewScene = null;
      state.previewRoom = null;
      renderScene(true);
      renderScenePicker(true);
      showToast('已回到当前日程');
    });
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) fetchState();
    });
    $('cook-open').addEventListener('click', openCookModal);
    $('cook-close').addEventListener('click', closeCookModal);
    document.querySelectorAll('[data-cook-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.cookFilter = button.getAttribute('data-cook-filter') || 'all';
        document.querySelectorAll('[data-cook-filter]').forEach(function (item) {
          item.classList.toggle(
            'active',
            item.getAttribute('data-cook-filter') === state.cookFilter
          );
        });
        renderCookDishes();
      });
    });
    $('cook-stop').addEventListener('click', stopCookRound);
    $('cook-serve').addEventListener('click', serveCookedDish);
    $('cook-dishes').addEventListener('click', function (event) {
      var button = event.target.closest('.cook-dish');
      if (button) startCookGame(button.getAttribute('data-name'));
    });
    $('game-open').addEventListener('click', openGameModal);
    $('game-close').addEventListener('click', closeGameModal);
    $('game-back').addEventListener('click', leaveGame);
    $('game-restart').addEventListener('click', restartCurrentGame);
    $('game-select-step').addEventListener('click', function (event) {
      var button = event.target.closest('.game-pick');
      if (button) startGame(button.getAttribute('data-game'));
    });
    $('game-battle-step').addEventListener('click', function (event) {
      var button = event.target.closest('[data-move]');
      if (button) chooseBattleMove(button.getAttribute('data-move'));
    });
    $('game-rps-step').addEventListener('click', function (event) {
      var button = event.target.closest('[data-rps]');
      if (button) chooseRps(button.getAttribute('data-rps'));
    });
    $('game-mole-start').addEventListener('click', startMoleRound);
    $('game-mole-grid').addEventListener('click', hitMole);
    $('game-ttt-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-ttt-cell');
      if (!cell) return;
      tttPlayerMove(Number(cell.getAttribute('data-cell')));
    });
    $('game-memory-grid').addEventListener('click', function (event) {
      var card = event.target.closest('.game-memory-card');
      if (card) memoryClick(Number(card.getAttribute('data-index')));
    });
    $('game-guess-submit').addEventListener('click', submitGuess);
    $('game-guess-input').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        submitGuess();
      }
    });
    $('game-dice-roll').addEventListener('click', rollDice);
    $('game-gomoku-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-gomoku-cell');
      if (cell) gomokuPlayerMove(Number(cell.getAttribute('data-index')));
    });
    $('game-connect4-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-connect4-cell');
      if (cell) connect4PlayerMove(Number(cell.getAttribute('data-col')));
    });
    $('game-reversi-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-reversi-cell');
      if (cell) reversiPlayerMove(Number(cell.getAttribute('data-index')));
    });
    $('camera-toggle').addEventListener('click', enterCameraMode);
    $('camera-cancel').addEventListener('click', exitCameraMode);
    $('camera-character').addEventListener('click', function () {
      if (cameraMode) takeCameraPhoto({ target: 'character' }, '拍一张月月');
    });
    $('camera-room').addEventListener('click', function () {
      if (cameraMode) takeCameraPhoto({ target: 'room' }, '拍下这个房间');
    });
    document.addEventListener('mousemove', onCameraHover);
    $('photo-close').addEventListener('click', closePhotoModal);
    $('photo-save').addEventListener('click', saveCameraPhoto);
    $('schedule-close').addEventListener('click', closeScheduleDetail);
    $('schedule-modal').addEventListener('click', function (event) {
      if (event.target === $('schedule-modal')) closeScheduleDetail();
    });
    $('schedule-body').addEventListener('click', function (event) {
      if (event.target.closest('#schedule-preview')) {
        previewScheduleScene();
        return;
      }
      if (event.target.closest('[data-day-export]')) {
        exportDaySchedule();
        return;
      }
      var dayFilterButton = event.target.closest('[data-day-filter]');
      if (dayFilterButton) {
        state.dayScheduleFilter =
          dayFilterButton.getAttribute('data-day-filter') || 'all';
        saveSort('day-schedule-filter', state.dayScheduleFilter);
        openDaySchedule();
        return;
      }
      var dayRow = event.target.closest('[data-day-index]');
      if (dayRow) {
        var timeline = (state.data && state.data.timeline) || [];
        openScheduleDetail(timeline[Number(dayRow.getAttribute('data-day-index'))]);
      }
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        flushBookReadingTime();
      } else if (state.bookId &&
                 !$('book-modal').classList.contains('hidden')) {
        state.bookOpenedAt = Date.now();
      }
    });
    $('day-schedule-toggle').addEventListener('click', function () {
      closeFunctionMenu();
      openDaySchedule();
    });
    $('now-line').addEventListener('click', openDaySchedule);
    $('now-line').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      openDaySchedule();
    });
    $('trips-open').addEventListener('click', function () {
      closeFunctionMenu();
      openTrips();
    });
    $('trips-close').addEventListener('click', closeTrips);
    $('trips-refresh').addEventListener('click', function () {
      openTrips(true);
    });
    $('trips-export').addEventListener('click', exportTrips);
    $('outfit-open').addEventListener('click', function () {
      closeFunctionMenu();
      openOutfit();
    });
    $('outfit-close').addEventListener('click', closeOutfit);
    $('outfit-export').addEventListener('click', exportOutfit);
    $('outfit-modal').addEventListener('click', function (event) {
      if (event.target === $('outfit-modal')) closeOutfit();
    });
    $('health-open').addEventListener('click', function () {
      closeFunctionMenu();
      openHealth();
    });
    $('health-close').addEventListener('click', closeHealth);
    $('health-export').addEventListener('click', exportHealth);
    $('health-modal').addEventListener('click', function (event) {
      if (event.target === $('health-modal')) closeHealth();
    });
    $('activity-open').addEventListener('click', function () {
      closeFunctionMenu();
      openActivity();
    });
    $('activity-close').addEventListener('click', closeActivity);
    $('activity-refresh').addEventListener('click', function () {
      openActivity(true);
    });
    $('activity-export').addEventListener('click', exportActivity);
    $('activity-modal').addEventListener('click', function (event) {
      if (event.target === $('activity-modal')) closeActivity();
    });
    $('activity-body').addEventListener('click', function (event) {
      if (event.target.closest('[data-activity-reset]')) {
        resetActivityFilters();
        return;
      }
      var filterButton = event.target.closest('[data-activity-filter]');
      if (filterButton) {
        state.activityFilter =
          filterButton.getAttribute('data-activity-filter') || 'all';
        saveSort('activity-filter', state.activityFilter);
        renderActivity();
        return;
      }
      var row = event.target.closest('[data-activity-kind]');
      if (row) {
        openActivityTarget(row.getAttribute('data-activity-kind'));
      }
    });
    $('activity-body').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var row = event.target.closest('[data-activity-kind]');
      if (!row) return;
      event.preventDefault();
      openActivityTarget(row.getAttribute('data-activity-kind'));
    });
    $('activity-search').addEventListener('input', function () {
      state.activityQuery = $('activity-search').value || '';
      renderActivity();
    });
    $('trips-body').addEventListener('click', function (event) {
      var filterButton = event.target.closest('[data-trips-filter]');
      if (filterButton) {
        state.tripsFilter =
          filterButton.getAttribute('data-trips-filter') || 'all';
        saveSort('trips-filter', state.tripsFilter);
        renderTrips();
        return;
      }
      var button = event.target.closest('[data-trips-toggle]');
      if (!button) return;
      var key = button.getAttribute('data-trips-toggle');
      state.tripsExpanded[key] = !state.tripsExpanded[key];
      renderTrips();
    });
    $('trips-modal').addEventListener('click', function (event) {
      if (event.target === $('trips-modal')) closeTrips();
    });
    $('next-list').addEventListener('click', function (event) {
      var row = event.target.closest('[data-next-index]');
      if (!row) return;
      var items = (state.data && state.data.next) || [];
      openScheduleDetail(items[Number(row.getAttribute('data-next-index'))]);
    });
    $('timeline').addEventListener('click', function (event) {
      var segment = event.target.closest('[data-schedule-index]');
      if (!segment) return;
      var items = (state.data && state.data.timeline) || [];
      openScheduleDetail(items[Number(segment.getAttribute('data-schedule-index'))]);
    });
    $('inventory-toggle').addEventListener('click', openInventory);
    $('inventory-close').addEventListener('click', closeInventory);
    $('inventory-export').addEventListener('click', exportInventory);
    $('wish-count').addEventListener('click', openWishes);
    $('wish-count').addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openWishes();
      }
    });
    $('wish-close').addEventListener('click', closeWishes);
    $('wish-modal').addEventListener('click', function (event) {
      if (event.target === $('wish-modal')) closeWishes();
    });
    $('inventory-search').addEventListener('input', function () {
      state.inventoryQuery = $('inventory-search').value;
      renderInventory();
    });
    $('shop-toggle').addEventListener('click', openShop);
    $('shop-close').addEventListener('click', closeShop);
    $('shop-category').addEventListener('change', loadShop);
    $('shop-search').addEventListener('input', function () {
      state.shopQuery = $('shop-search').value;
      renderShop(state.shopItems || []);
    });
    $('shop-sort').addEventListener('change', function () {
      state.shopSort = $('shop-sort').value || 'default';
      saveSort('shop-sort', state.shopSort);
      renderShop(state.shopItems || []);
    });
    $('shop-fav-filter').addEventListener('click', function () {
      state.shopOnlyFavorites = !state.shopOnlyFavorites;
      saveSort('shop-favorites', state.shopOnlyFavorites ? '1' : '0');
      $('shop-fav-filter').classList.toggle('active', state.shopOnlyFavorites);
      renderShop(state.shopItems || []);
    });
    $('shop-modal').addEventListener('click', function (event) {
      if (event.target === $('shop-modal')) closeShop();
    });
    $('wallet-toggle').addEventListener('click', openWallet);
    $('wallet-close').addEventListener('click', closeWallet);
    $('wallet-export').addEventListener('click', exportWalletTransactions);
    $('wallet-modal').addEventListener('click', function (event) {
      if (event.target === $('wallet-modal')) closeWallet();
    });
    $('money-pill').addEventListener('click', openWallet);
    $('garage-toggle').addEventListener('click', openGarage);
    $('garage-close').addEventListener('click', closeGarage);
    $('garage-export').addEventListener('click', exportGarage);
    $('garage-modal').addEventListener('click', function (event) {
      if (event.target === $('garage-modal')) closeGarage();
    });
    $('garage-room').addEventListener('click', openGarage);
    $('garage-room').addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') openGarage();
    });
    $('vehicle-close').addEventListener('click', closeVehicle);
    $('vehicle-modal').addEventListener('click', function (event) {
      if (event.target === $('vehicle-modal')) closeVehicle();
    });
    $('vehicle-body').addEventListener('click', function (event) {
      var tab = event.target.closest('[data-vehicle-key]');
      if (tab) {
        state.vehicleKey = vehicleKeyFromCar(tab.getAttribute('data-vehicle-key'));
        renderVehicle();
        return;
      }
      var driver = event.target.closest('[data-vehicle-driver]');
      if (driver) {
        vehicleStart(driver.getAttribute('data-vehicle-driver'));
        return;
      }
      if (event.target.closest('#vehicle-return')) {
        vehicleReturn();
        return;
      }
      if (event.target.closest('#vehicle-refuel')) {
        vehicleRefuel();
        return;
      }
      if (event.target.closest('#vehicle-manage')) {
        closeVehicle();
        openGarage();
      }
    });
    $('system-toggle').addEventListener('click', openSystem);
    $('system-close').addEventListener('click', closeSystem);
    $('system-refresh').addEventListener('click', renderSystem);
    $('system-export').addEventListener('click', exportDiagnostics);
    $('system-reset-prefs').addEventListener('click', resetViewPreferences);
    $('system-backup').addEventListener('click', backupAllData);
    $('system-restore').addEventListener('click', function () {
      $('backup-file').click();
    });
    $('backup-file').addEventListener('change', function () {
      restoreBackupFile($('backup-file').files && $('backup-file').files[0]);
      $('backup-file').value = '';
    });
    $('system-body').addEventListener('click', function (event) {
      var row = event.target.closest('[data-system-target]');
      if (!row) return;
      var target = $(row.getAttribute('data-system-target'));
      closeSystem();
      if (target) target.click();
    });
    $('system-modal').addEventListener('click', function (event) {
      if (event.target === $('system-modal')) closeSystem();
    });
    $('status-open').addEventListener('click', openStatus);
    $('status-close').addEventListener('click', closeStatus);
    $('status-modal').addEventListener('click', function (event) {
      if (event.target === $('status-modal')) closeStatus();
    });
    $('status-modal-body').addEventListener('click', function (event) {
      var activityRow = event.target.closest('[data-status-activity-kind]');
      if (activityRow) {
        var activityKind = activityRow.getAttribute('data-status-activity-kind');
        closeStatus();
        openActivityTarget(activityKind);
        return;
      }
      if (event.target.closest('[data-status-activity-refresh]')) {
        loadStatusActivity();
        return;
      }
      if (event.target.closest('[data-status-activity]')) {
        closeStatus();
        openActivity();
        return;
      }
      if (event.target.closest('[data-status-plan]')) {
        closeStatus();
        openDaySchedule();
        return;
      }
      if (event.target.closest('[data-status-wallet]')) {
        closeStatus();
        openWallet();
        return;
      }
      if (event.target.closest('[data-status-reading]')) {
        closeStatus();
        openInventory('bookshelf-section');
        return;
      }
      if (event.target.closest('[data-status-health]')) {
        closeStatus();
        openHealth();
        return;
      }
      if (event.target.closest('[data-status-outfit]')) {
        closeStatus();
        openOutfit();
        return;
      }
      if (event.target.closest('[data-status-travel]')) {
        closeStatus();
        openTrips();
        return;
      }
      if (event.target.closest('[data-status-world]')) {
        closeStatus();
        openMemory();
        return;
      }
      if (event.target.closest('[data-status-export]')) {
        exportStatusTrend();
        return;
      }
      var rangeButton = event.target.closest('[data-status-range]');
      if (rangeButton) {
        var pickedRange = Number(rangeButton.getAttribute('data-status-range'));
        state.statusTrendRange = [7, 14, 30].indexOf(pickedRange) >= 0
          ? pickedRange : 7;
        saveSort('status-trend-range', String(state.statusTrendRange));
        renderStatusModal();
        return;
      }
      var metric = event.target.closest('[data-status-metric]');
      if (metric) {
        state.statusTrendMetric = metric.getAttribute('data-status-metric') || 'mood';
        saveSort('status-trend-metric', state.statusTrendMetric);
        renderStatusModal();
        return;
      }
      var quick = event.target.closest('[data-status-target]');
      if (!quick) return;
      var target = $(quick.getAttribute('data-status-target'));
      closeStatus();
      if (target) target.click();
    });
    $('status-modal-body').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var activityRow = event.target.closest('[data-status-activity-kind]');
      if (activityRow) {
        event.preventDefault();
        var activityKind = activityRow.getAttribute('data-status-activity-kind');
        closeStatus();
        openActivityTarget(activityKind);
        return;
      }
      if (event.target.closest('[data-status-activity-refresh]')) {
        event.preventDefault();
        loadStatusActivity();
        return;
      }
      if (event.target.closest('[data-status-activity]')) {
        event.preventDefault();
        closeStatus();
        openActivity();
        return;
      }
      if (event.target.closest('[data-status-plan]')) {
        event.preventDefault();
        closeStatus();
        openDaySchedule();
        return;
      }
      if (event.target.closest('[data-status-wallet]')) {
        event.preventDefault();
        closeStatus();
        openWallet();
        return;
      }
      if (event.target.closest('[data-status-reading]')) {
        event.preventDefault();
        closeStatus();
        openInventory('bookshelf-section');
        return;
      }
      if (event.target.closest('[data-status-health]')) {
        event.preventDefault();
        closeStatus();
        openHealth();
        return;
      }
      if (event.target.closest('[data-status-outfit]')) {
        event.preventDefault();
        closeStatus();
        openOutfit();
        return;
      }
      if (event.target.closest('[data-status-travel]')) {
        event.preventDefault();
        closeStatus();
        openTrips();
        return;
      }
      if (event.target.closest('[data-status-world]')) {
        event.preventDefault();
        closeStatus();
        openMemory();
      }
    });
    $('menu-toggle').addEventListener('click', openFunctionMenu);
    $('function-close').addEventListener('click', closeFunctionMenu);
    $('function-menu').addEventListener('click', function (event) {
      if (event.target === $('function-menu')) closeFunctionMenu();
    });
    $('integrations-open').addEventListener('click', openIntegrations);
    $('integration-close').addEventListener('click', closeIntegrations);
    $('integration-refresh').addEventListener('click', loadIntegrations);
    $('integration-modal').addEventListener('click', function (event) {
      if (event.target === $('integration-modal')) closeIntegrations();
    });
    document.querySelectorAll('[data-menu-target]').forEach(function (button) {
      button.addEventListener('click', function () {
        var target = $(button.getAttribute('data-menu-target'));
        closeFunctionMenu();
        if (target) target.click();
      });
    });
    $('diary-toggle').addEventListener('click', openDiary);
    $('diary-close').addEventListener('click', closeDiary);
    $('diary-export').addEventListener('click', exportDiary);
    $('diary-search').addEventListener('input', function () {
      state.diaryQuery = $('diary-search').value;
      renderDiaryList();
    });
    document.querySelectorAll('[data-diary-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.diaryFilter = button.getAttribute('data-diary-filter') || 'all';
        saveSort('diary-filter', state.diaryFilter);
        document.querySelectorAll('[data-diary-filter]').forEach(function (item) {
          item.classList.toggle(
            'active',
            item.getAttribute('data-diary-filter') === state.diaryFilter
          );
        });
        renderDiaryList();
      });
    });
    $('diary-modal').addEventListener('click', function (event) {
      if (event.target === $('diary-modal')) closeDiary();
    });
    $('memory-toggle').addEventListener('click', openMemory);
    $('memory-close').addEventListener('click', closeMemory);
    $('memory-modal').addEventListener('click', function (event) {
      if (event.target === $('memory-modal')) closeMemory();
    });
    $('weekly-toggle').addEventListener('click', openWeekly);
    $('weekly-close').addEventListener('click', closeWeekly);
    $('weekly-export').addEventListener('click', exportWeekly);
    $('weekly-export-chart').addEventListener('click', exportWeeklyChart);
    $('weekly-modal').addEventListener('click', function (event) {
      if (event.target === $('weekly-modal')) closeWeekly();
    });
    document.querySelectorAll('[data-weekly-days]').forEach(function (button) {
      button.addEventListener('click', function () {
        setWeeklyRange(button.getAttribute('data-weekly-days'));
      });
    });
    document.querySelectorAll('[data-weekly-metric]').forEach(function (button) {
      button.addEventListener('click', function () {
        setWeeklyMetric(button.getAttribute('data-weekly-metric'));
      });
    });
    document.querySelectorAll('[data-chart-theme]').forEach(function (button) {
      button.addEventListener('click', function () {
        setWeeklyChartTheme(button.getAttribute('data-chart-theme'));
      });
    });
    $('affection-pill').addEventListener('click', openRelations);
    $('relations-close').addEventListener('click', closeRelations);
    $('relations-modal').addEventListener('click', function (event) {
      if (event.target === $('relations-modal')) closeRelations();
    });
    $('book-close').addEventListener('click', closeBook);
    $('book-font-up').addEventListener('click', function () { changeBookFont(0.1); });
    $('book-font-down').addEventListener('click', function () { changeBookFont(-0.1); });
    $('book-theme').addEventListener('click', cycleBookTheme);
    $('book-prev').addEventListener('click', function () { changeBookChapter(-1); });
    $('book-chapter-select').addEventListener('change', function () {
      var chapter = Number($('book-chapter-select').value) || 1;
      if (state.bookId) openBook(state.bookId, chapter);
    });
    $('book-next').addEventListener('click', function () { changeBookChapter(1); });
    document.addEventListener('keydown', function (event) {
      if ($('book-modal').classList.contains('hidden') || !state.bookId) return;
      var tag = String((event.target && event.target.tagName) || '').toLowerCase();
      if (['input', 'textarea', 'select'].indexOf(tag) >= 0) return;
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        changeBookChapter(-1);
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        changeBookChapter(1);
      }
    });
    $('book-bookmark-save').addEventListener('click', saveBookBookmark);
    $('book-bookmark-restore').addEventListener('click', restoreBookBookmark);
    $('book-note-save').addEventListener('click', saveBookNote);
    $('book-note-export').addEventListener('click', exportBookNotes);
    $('book-note-search').addEventListener('input', function () {
      state.bookNoteQuery = $('book-note-search').value;
      renderBookNotes();
    });
    $('book-modal').addEventListener('click', function (event) {
      if (event.target === $('book-modal')) closeBook();
    });
    $('inventory-modal').addEventListener('click', function (event) {
      if (event.target === $('inventory-modal')) closeInventory();
    });
    $('photo-again').addEventListener('click', function () {
      closePhotoModal();
      enterCameraMode();
    });
    $('home-stage').addEventListener('click', onCameraStageClick, true);
    $('scene-stage').addEventListener('click', function (event) {
      var toggle = event.target.closest('[data-scene-mode]');
      if (!toggle) return;
      event.preventDefault();
      state.indoorView = toggle.getAttribute('data-scene-mode') === 'indoor';
      renderScene(true);
      flashSceneMode(state.indoorView ? '进入室内' : '回到室外');
    }, true);
    $('scene-stage').addEventListener('click', onPlacementStageClick, true);
    $('scene-stage').addEventListener('pointerdown', onDecorPointerDown, true);
    $('scene-stage').addEventListener('pointermove', onDecorPointerMove, true);
    $('scene-stage').addEventListener('pointerup', onDecorPointerUp, true);
    $('scene-stage').addEventListener('pointercancel', onDecorPointerUp, true);
    $('scene-stage').addEventListener('click', onCameraStageClick, true);
    document.addEventListener('keydown', function (event) {
      if (
        (event.key === 'ArrowLeft' || event.key === 'ArrowRight') &&
        !$('photo-modal').classList.contains('hidden') &&
        (state.photos || []).length > 1
      ) {
        event.preventDefault();
        var current = Number(state.photoIndex);
        if (!isFinite(current) || current < 0) current = 0;
        showPhotoAt(current + (event.key === 'ArrowLeft' ? -1 : 1));
        return;
      }
      if (event.key !== 'Escape') return;
      if (!$('cook-modal').classList.contains('hidden')) closeCookModal();
      if (!$('photo-modal').classList.contains('hidden')) closePhotoModal();
      if (!$('item-popover').classList.contains('hidden')) closeItem();
      if (!$('item-drawer').classList.contains('hidden')) toggleItemDrawer(false);
      if (!$('inventory-modal').classList.contains('hidden')) closeInventory();
      if (!$('shop-modal').classList.contains('hidden')) closeShop();
      if (!$('wallet-modal').classList.contains('hidden')) closeWallet();
      if (!$('diary-modal').classList.contains('hidden')) closeDiary();
      if (!$('weekly-modal').classList.contains('hidden')) closeWeekly();
      if (!$('trips-modal').classList.contains('hidden')) closeTrips();
      if (!$('outfit-modal').classList.contains('hidden')) closeOutfit();
      if (!$('health-modal').classList.contains('hidden')) closeHealth();
      if (!$('activity-modal').classList.contains('hidden')) closeActivity();
      if (!$('relations-modal').classList.contains('hidden')) closeRelations();
      if (!$('memory-modal').classList.contains('hidden')) closeMemory();
      if (!$('garage-modal').classList.contains('hidden')) closeGarage();
      if (!$('vehicle-modal').classList.contains('hidden')) closeVehicle();
      if (!$('system-modal').classList.contains('hidden')) closeSystem();
      if (!$('book-modal').classList.contains('hidden')) closeBook();
      if (!$('game-modal').classList.contains('hidden')) closeGameModal();
      if (!$('status-modal').classList.contains('hidden')) closeStatus();
      if (!$('integration-modal').classList.contains('hidden')) closeIntegrations();
      if (!$('schedule-modal').classList.contains('hidden')) closeScheduleDetail();
      if (!$('wish-modal').classList.contains('hidden')) closeWishes();
      if (!$('function-menu').classList.contains('hidden')) closeFunctionMenu();
      if (cameraMode) exitCameraMode();
    });
    fetchHomeItems();
    fetchWishes();
    if (pageParams.get('items') === '1') toggleItemDrawer(true);
    fetchState();
    setInterval(function () {
      if (!document.hidden) fetchState();
    }, 2000);
    setInterval(updateClock, 1000);
  }

  function applyAnimations() {
    document.body.classList.toggle('no-anim', !state.animations);
    var button = $('anim-toggle');
    if (button) {
      button.textContent = state.animations ? '动画：开' : '动画：关';
      button.setAttribute('aria-pressed', state.animations ? 'true' : 'false');
      button.title = '开启或关闭人物行走、路景滚动与天气动画';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
