(function () {
  'use strict';

  window.__VIRTUAL_LIFE_UI_VERSION = '20261110-perf2';
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

