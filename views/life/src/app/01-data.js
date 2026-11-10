  function fetchState() {
    var params = new URLSearchParams();
    if (state.persona) params.set('persona', state.persona);
    var pageParams = new URLSearchParams(window.location.search);
    if (pageParams.get('time')) params.set('time', pageParams.get('time'));
    var url = '/api/state' + (params.toString() ? '?' + params.toString() : '');
    fetch(url, { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        state.data = data;
        state.error = !data.ok;
        state.lastData = data;
        state.lastFetchErrorAt = 0;
        if (data.ok && data.persona) state.persona = data.persona;
        try {
          checkDeliveryArrivals(data.deliveries || []);
        } catch (error) {
          console.error('[模拟人生] delivery check failed', error);
        }
        try {
          checkAffectionLevel(data.affection || {});
        } catch (error) {
          console.error('[模拟人生] affection level check failed', error);
        }
        try {
          renderPendingActions(data.pending_actions);
        } catch (error) {
          console.error('[模拟人生] pending actions render failed', error);
        }
        render();
      })
      .catch(function () {
        state.error = true;
        var now = Date.now();
        if (!state.lastFetchErrorAt || now - state.lastFetchErrorAt > 15000) {
          showToast('无法连接本地数据服务，稍后自动重试');
          state.lastFetchErrorAt = now;
        }
        renderHeader();
      });
  }

  function showToast(text) {
    var toast = $('toast');
    if (!toast) return;
    toast.textContent = text;
    toast.classList.remove('hidden');
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(function () { toast.classList.add('hidden'); }, 3200);
  }

  function renderPendingActions(actions) {
    var box = $('pending-actions');
    if (!box) {
      box = document.createElement('div');
      box.id = 'pending-actions';
      box.className = 'pending-actions pending-floating';
      document.body.appendChild(box);
    }
    var items = Array.isArray(actions) ? actions : [];
    var baseTitle = document.title.replace(/^【\d+ 个待处理】/, '');
    document.title = items.length
      ? ('【' + items.length + ' 个待处理】' + baseTitle)
      : baseTitle;
    box.setAttribute('aria-live', 'polite');
    box.classList.toggle('pending-floating', items.length > 0);
    if (!items.length) {
      box.classList.add('hidden');
      box.innerHTML = '';
      return;
    }
    box.classList.remove('hidden');
    box.innerHTML = '<span class="pending-actions-label">待处理</span>' +
      items.map(function (action) {
      var id = escapeHtml(action.id || '');
      var source = String(action.source || '').trim();
      var labelText = action.label || '把东西递给月月';
      var kind = String(action.kind || 'gift');
      var hint = source
        ? ('来自：' + source)
        : (kind === 'money'
          ? '填写金额后给月月钱'
          : kind === 'wish'
            ? '点击实现月月的愿望'
            : '点击把东西递过去');
      var ariaLabel = labelText + '，' + hint;
      var control = '';
      if (kind === 'money') {
        var suggested = Number(action.amount) || 0;
        control =
          '<span class="pending-action-label">' + escapeHtml(labelText) + '</span>' +
          '<input type="number" class="pending-money-input" min="1" step="1" ' +
          'max="100000" value="' + (suggested > 0 ? suggested : '') + '" ' +
          'placeholder="填写金额" aria-label="给月月的金额">' +
          '<button type="button" class="pending-action-btn" data-pending-kind="money" ' +
          'data-pending-id="' + id + '" title="' + escapeHtml(hint) + '" ' +
          'aria-label="' + escapeHtml(ariaLabel) + '">给</button>';
      } else {
        control = '<button type="button" class="pending-action-btn" data-pending-kind="' +
          escapeHtml(kind) + '" data-pending-id="' + id + '" title="' +
          escapeHtml(hint) + '" aria-label="' + escapeHtml(ariaLabel) + '">' +
          escapeHtml(labelText) + '</button>';
      }
      return '<span class="pending-action-item">' +
        '<span class="pending-action-main">' +
        control +
        '<button type="button" class="pending-action-cancel" data-dismiss-id="' +
        id + '" title="取消这个待处理" aria-label="取消这个待处理">×</button>' +
        '</span>' +
        (source
          ? '<span class="pending-action-source" title="' +
            escapeHtml(hint) + '">' + escapeHtml(hint) + '</span>'
          : '') +
        '</span>';
    }).join('');
    box.querySelectorAll('[data-pending-id]').forEach(function (button) {
      button.addEventListener('click', function () {
        var kind = button.getAttribute('data-pending-kind') || 'gift';
        var item = button.closest('.pending-action-item');
        var input = item ? item.querySelector('.pending-money-input') : null;
        var amount = input ? Number(input.value) : 0;
        if (kind === 'money' && (!amount || amount <= 0)) {
          showToast('先填写要给月月的金额');
          if (input) input.focus();
          return;
        }
        acceptPendingAction(
          button.getAttribute('data-pending-id'),
          button,
          kind,
          amount
        );
      });
    });
    box.querySelectorAll('[data-dismiss-id]').forEach(function (button) {
      button.addEventListener('click', function () {
        dismissPendingAction(button.getAttribute('data-dismiss-id'), button);
      });
    });
  }

  function dismissPendingAction(id, button) {
    if (!id) return;
    if (button) {
      button.disabled = true;
      button.textContent = '…';
    }
    fetch('/api/gift/dismiss', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '取消失败');
        showToast('已取消这个待处理');
        fetchState();
      })
      .catch(function (error) {
        if (button) {
          button.disabled = false;
          button.textContent = '×';
        }
        showToast(error && error.message ? error.message : '取消失败');
        fetchState();
      });
  }

  function acceptPendingAction(id, button, kind, amount) {
    if (!id) return;
    kind = kind || 'gift';
    var originalText = button ? button.textContent : '';
    if (button) {
      button.disabled = true;
      button.textContent = kind === 'money'
        ? '正在给钱...'
        : kind === 'wish'
          ? '正在实现...'
          : '正在递过去...';
    }
    var payload = { id: id };
    if (kind === 'money') {
      payload.amount = Number(amount) || 0;
    }
    fetch('/api/gift/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '操作失败');
        if (data.kind === 'money') {
          showToast('已给月月 ' + data.amount + ' 元');
          fetchState();
          return;
        }
        if (data.kind === 'wish') {
          showToast('已实现月月的愿望');
          fetchState();
          return;
        }
        state.interaction.busy = true;
        state.interaction.fromGift = true;
        setInteractionReply('她正在接你递过去的东西...');
        showToast('已经把东西递过去了');
        fetchState();
        pollInteraction(data.id, Date.now());
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '操作失败');
        if (button) {
          button.disabled = false;
          button.textContent = originalText || '把东西递给月月';
        }
        fetchState();
      });
  }

  function todayString() {
    var now = new Date();
    return [
      now.getFullYear(),
      String(now.getMonth() + 1).padStart(2, '0'),
      String(now.getDate()).padStart(2, '0')
    ].join('-');
  }

  function fetchHomeItems() {
    var persona = String((state.data && state.data.persona) || '');
    fetch('/api/home_items?persona=' + encodeURIComponent(persona), { cache: 'no-store' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        state.homeItems = Array.isArray(data.items) ? data.items : [];
        renderState.home = ""; renderState.scene = "";
        render();
        renderItemDrawer();
        updateItemCounts();
        if (state.pendingItem) {
          openItem(state.pendingItem);
          state.pendingItem = null;
        }
      })
      .catch(function () {
        state.homeItems = [];
        updateItemCounts();
      });
  }

