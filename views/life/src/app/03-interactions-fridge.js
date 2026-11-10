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

