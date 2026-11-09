/* Catalog illustrations reuse the physical furniture renderer. */
(function (root) {
  'use strict';
  var serial = 0;
  function stairIllustration() {
    var steps = '';
    for (var i = 0; i < 6; i++) {
      var x = 8 + i * 14, y = 58 - i * 9, h = 9 + i * 9;
      steps += '<rect x="' + x + '" y="' + y + '" width="16" height="' + h + '" rx="2" fill="' + (i % 2 ? '#d4ae7c' : '#e0bc8b') + '"/>' +
        '<rect x="' + x + '" y="' + y + '" width="16" height="4" rx="1.5" fill="#f1dbb2"/>' +
        '<path d="M' + (x + 16) + ' ' + y + 'v' + h + '" stroke="#a9855d" stroke-width="1" opacity=".65"/>';
    }
    return '<svg class="item-illustration" viewBox="0 0 112 84" aria-hidden="true" focusable="false">' +
      '<ellipse cx="56" cy="72" rx="42" ry="5" fill="#6d573d22"/>' +
      steps +
      '<path d="M8 62L98 12" stroke="#7b5b3d" stroke-width="4" stroke-linecap="round"/>' +
      '<path d="M18 57L98 15M18 57v16M98 15v10" stroke="#a98760" stroke-width="2" stroke-linecap="round" fill="none"/>' +
      '<path d="M77 10l13-5-1 14" fill="none" stroke="#7b5b3d" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' +
      '</svg>';
  }
  function draw(item, type) {
    item = item || {};
    if (/楼梯/.test(String(item.name || '')) || item.id === 'stairs' || item.id === 'stair_flight') return stairIllustration();
    if (!type && root.ProductArtwork) {
      var product = root.ProductArtwork.draw(item);
      if (product) return product;
    }
    if (!type && root.FurnitureIcons) {
      var fixture = root.FurnitureIcons.draw(item);
      if (fixture) return fixture;
    }
    var name = String(item.name || item.category || ''), layout = root.SceneStudio.layout[item.id];
    type = type || (layout && layout[4]);
    if (!type) {
      var choices = [['book', /书|小说|日记|手札|绘本|漫画/], ['plants', /花|植物|绿植/], ['lamp', /灯/], ['sofa', /沙发|椅/], ['tea', /茶|杯|餐具/], ['whale', /鲸鱼/], ['bear', /玩偶|毛绒|公仔/], ['camera', /相机|拍照/], ['headphones', /耳机/], ['towel', /衣|布|毯|围巾/], ['jewelry', /饰|首饰|项链/], ['diffuser', /香|护肤/]];
      type = (choices.find(function (choice) { return choice[1].test(name); }) || ['box'])[0];
    }
    var id = 'catalog-' + (++serial) + '-', w = 96, h = 72;
    if (/bed|cabinet|fridge|bookshelf|jewelry/.test(type)) { w = 65; h = 86; }
    if (/lamp|diffuser|coffee|bear/.test(type)) { w = 46; h = 67; }
    var defs = root.SceneStudio.materialDefs(id, {sky:['#a9ced3','#e9edda']}), art;
    if (type === 'dish') {
      art = '<ellipse cx="48" cy="64" rx="43" ry="5" fill="#5d684b17"/><ellipse cx="48" cy="41" rx="45" ry="28" fill="#d4decc"/><ellipse cx="48" cy="38" rx="44" ry="27" fill="#fffcf1" stroke="#c6d2b6"/><ellipse cx="48" cy="38" rx="34" ry="19" fill="#d9dfc5"/>';
      var greens = /菜|沙拉|蔬/.test(name), soup = /汤|粥/.test(name);
      if (soup) art += '<ellipse cx="48" cy="38" rx="31" ry="17" fill="#e6cb91"/><path d="M25 41q10-14 23-2t24-4" fill="none" stroke="#f8e7b5" stroke-width="3"/>';
      for (var i = 0; i < 9; i++) {
        var x = 29 + i % 4 * 12, y = 29 + Math.floor(i / 4) * 9;
        art += '<ellipse cx="' + x + '" cy="' + y + '" rx="9" ry="5" transform="rotate(' + (i * 29) + ' ' + x + ' ' + y + ')" fill="' + (greens ? ['#9cb579','#bed09b','#7b9a62'][i%3] : ['#dba36d','#e7c192','#b88c61'][i%3]) + '"/>';
      }
      art += '<path d="M48 21q-8-12-13-5 3 9 13 5 3-11 11-8 2 8-11 8" fill="#75996d"/><path d="M36 12q-6-7 0-12M50 10q-6-7 0-12" stroke="#a3ae98" fill="none" opacity=".5" stroke-linecap="round"/>';
    } else if(type==='whale') { art='<ellipse cx="47" cy="65" rx="36" ry="4" fill="#65765d22"/><path d="M14 40C8 10 68 5 76 39q18-22 20-10 6 12-13 21-9 20-42 13-27-3-27-23Z" fill="#c1b9d7" stroke="#a59cbf"/><path d="M17 44q27 10 58-1-7 21-37 17-16-2-21-16Z" fill="#f3efe4"/><circle cx="29" cy="37" r="3" fill="#56637c"/><circle cx="28" cy="36" r="1" fill="white"/><ellipse cx="23" cy="43" rx="5" ry="2" fill="#e1b6c4"/><path d="M52 46q-5 16 13 10" fill="#b2a7cd"/><path d="M45 13q-13-17-15-5 0 5 15 5m0 0q12-20 17-9 4 8-17 9" fill="#c9dce2"/>'; } else { art = root.FurnitureArt.draw(type, w, h, id, {dark:false,band:'day'}, true); }
    return '<svg class="item-illustration" viewBox="-16 -12 ' + (w+32) + ' ' + (h+25) + '" aria-hidden="true" focusable="false">' + defs + art + '</svg>';
  }
  root.ItemArtwork = { draw:draw };
  document.querySelectorAll('[data-life-icon]').forEach(function (node) {
    node.innerHTML = draw({}, node.getAttribute('data-life-icon'));
  });
})(window);
