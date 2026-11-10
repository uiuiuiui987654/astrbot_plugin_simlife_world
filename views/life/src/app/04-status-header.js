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
    link.download = '模拟人生-' + labels[metric] + '-' + day + '.csv';
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

