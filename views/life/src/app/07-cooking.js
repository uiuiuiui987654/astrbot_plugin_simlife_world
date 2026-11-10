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

