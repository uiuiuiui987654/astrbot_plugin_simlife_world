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

