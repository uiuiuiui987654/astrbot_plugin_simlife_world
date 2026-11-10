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
    link.download = '模拟人生-关系年表-' + day + '.csv';
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
    ctx.fillText('模拟人生 · 生活周报', 56, 68);
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
      link.download = '模拟人生-周报图表-' + day + '.png';
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
    link.download = '模拟人生-周报-' + String(report.end || new Date().toISOString().slice(0, 10)) + '.csv';
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

