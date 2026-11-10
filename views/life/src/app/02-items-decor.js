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

