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
    $('activity-sub').textContent = '最近一周发生的事';
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
      ['all', '全部'], ['meal', '吃饭'], ['way', '路上'],
      ['together', '和主人'], ['life', '日常'], ['diary', '日记'],
      ['world', '小世界'], ['cooking', '下厨'], ['money', '钱包'],
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
          var copy = event.detail
            ? '<b>' + escapeHtml(event.title || '一件小事') + '</b><small>' + escapeHtml(event.detail) + '</small>'
            : '<b class="activity-plain">' + escapeHtml(event.title || '一件小事') + '</b>';
          return '<div class="activity-row clickable" data-activity-kind="' +
            escapeHtml(event.kind || '') + '" role="button" tabindex="0" ' +
            'title="查看详情"><span class="activity-icon">' +
            escapeHtml(event.icon || '·') + '</span><div class="activity-copy">' +
            copy + '</div><em>' +
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
      meal: '吃饭', way: '路上', together: '和主人', life: '日常',
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
    link.download = '模拟人生-记忆-' + day + '.csv';
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
        link.download = '模拟人生-日记-' + day + '.csv';
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

