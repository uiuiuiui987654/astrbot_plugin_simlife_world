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

