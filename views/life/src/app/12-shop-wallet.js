  function syncShopControls() {
    var filterButton = $('shop-fav-filter');
    if (!filterButton) return;
    var favorites = shopFavorites();
    filterButton.textContent = '⭐ 收藏' + (favorites.length ? ' (' + favorites.length + ')' : '');
    filterButton.classList.toggle('active', Boolean(state.shopOnlyFavorites));
    $('shop-search').value = state.shopQuery || '';
    $('shop-sort').value = state.shopSort || 'default';
  }

  function openShop() {
    $('shop-modal').classList.remove('hidden');
    syncShopControls();
    loadShop();
  }

  function closeShop() {
    $('shop-modal').classList.add('hidden');
  }

  function openWallet() {
    $('wallet-modal').classList.remove('hidden');
    renderWallet();
  }

  function closeWallet() {
    $('wallet-modal').classList.add('hidden');
  }

  function renderWallet() {
    var body = $('wallet-body');
    var persona = (state.data && state.data.persona) || '';
    body.innerHTML = '<p class="inventory-empty">正在翻钱包...</p>';
    fetch('/api/wallet?persona=' + encodeURIComponent(persona), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '钱包打不开');
        var wallet = data.wallet || {};
        var balance = Number(wallet.balance || 0);
        var goal = wallet.goal;
        var transactions = (wallet.transactions || []).slice().reverse();
        state.walletTransactions = transactions;
        var incomeTotal = 0;
        var expenseTotal = 0;
        transactions.forEach(function (tx) {
          var amount = Number(tx.amount || 0);
          if (amount >= 0) incomeTotal += amount;
          else expenseTotal += Math.abs(amount);
        });
        var moneyText = function (value) {
          var number = Number(value) || 0;
          return Number.isInteger(number) ? number : number.toFixed(2);
        };
        var html = '<div class="wallet-summary">' +
          '<div class="wallet-balance-card">' +
          '<small>当前余额</small><strong>' +
          moneyText(balance) + ' 元</strong></div>' +
          '<div class="wallet-total-card"><small>最近流水</small><strong>' +
          transactions.length + ' 条</strong></div>' +
          '<div class="wallet-flow-card income"><small>最近收入</small><strong>+' +
          moneyText(incomeTotal) + '</strong></div>' +
          '<div class="wallet-flow-card expense"><small>最近支出</small><strong>-' +
          moneyText(expenseTotal) + '</strong></div>' +
          '</div>';
        if (goal) {
          var target = Number(goal.target || 0);
          var progress = Number(goal.progress || 0);
          var percent = target > 0
            ? Math.max(0, Math.min(100, Math.round(progress / target * 100)))
            : 0;
          var achieved = Boolean(goal.achieved);
          html += '<div class="wallet-goal' + (achieved ? ' achieved' : '') +
            '"><div class="wallet-goal-head">' +
            '<b>存款目标：' + escapeHtml(goal.name || '') + '</b>' +
            (achieved ? '<em class="wallet-goal-badge">已达成</em>' : '') +
            '<span>' + (Number.isInteger(progress) ? progress : progress.toFixed(2)) +
            ' / ' + target + ' 元</span></div>' +
            '<div class="wallet-goal-bar"><span style="width:' + percent + '%"></span></div>' +
            (goal.wish
              ? '<p class="wallet-goal-wish">' + escapeHtml(goal.wish) + '</p>'
              : '') +
            '</div>';
        }
        var goalName = goal ? String(goal.name || '') : '';
        var goalTarget = goal ? Number(goal.target || 0) : '';
        var goalWish = goal ? String(goal.wish || '') : '';
        html += '<div class="wallet-goal-form"><h4>' +
          (goal ? '更改存款目标' : '设置存款目标') + '</h4>' +
          '<div class="wallet-goal-fields">' +
          '<input id="wallet-goal-name" maxlength="40" placeholder="目标名称" value="' +
          escapeHtml(goalName) + '">' +
          '<input id="wallet-goal-target" type="number" min="1" step="1" ' +
          'placeholder="目标金额" value="' + (goalTarget || '') + '">' +
          '</div>' +
          '<input id="wallet-goal-wish" maxlength="120" placeholder="愿望说明（可选）" value="' +
          escapeHtml(goalWish) + '">' +
          '<button type="button" class="ghost-btn" id="wallet-goal-save">保存目标</button>' +
          (goal
            ? '<button type="button" class="mini-btn" id="wallet-goal-clear">清除目标</button>'
            : '') +
          '</div>';
        html += '<div class="wallet-give">' +
          '<label>直接给月月钱</label>' +
          '<div class="wallet-give-row">' +
          '<input id="wallet-give-amount" type="number" min="1" max="100000" ' +
          'step="1" placeholder="金额">' +
          '<button type="button" id="wallet-give">给</button></div>' +
          '<small>从这里给的钱会记入流水，关系 +2。</small></div>';
        html += '<div class="wallet-section"><h4>最近流水</h4>';
        var walletFilter = state.walletFilter || 'all';
        var walletTransactions = state.walletTransactions || [];
        var walletTxCounts = {
          all: walletTransactions.length,
          income: walletTransactions.filter(function (tx) {
            return Number(tx.amount || 0) >= 0;
          }).length,
          expense: walletTransactions.filter(function (tx) {
            return Number(tx.amount || 0) < 0;
          }).length
        };
        html += '<div class="wallet-tools">' +
          '<input id="wallet-search" type="search" placeholder="搜索流水...">' +
          '<div class="wallet-filters">' + [
            ['all', '全部'], ['income', '收入'], ['expense', '支出']
          ].map(function (item) {
            return '<button type="button" data-wallet-filter="' + item[0] + '"' +
              (walletFilter === item[0] ? ' class="active"' : '') + '>' +
              item[1] + ' <b>' + (walletTxCounts[item[0]] || 0) +
              '</b></button>';
          }).join('') + '</div></div><div id="wallet-tx-list"></div></div>';
        body.innerHTML = html;
        var giveButton = $('wallet-give');
        if (giveButton) {
          giveButton.addEventListener('click', giveWalletMoney);
        }
        var goalButton = $('wallet-goal-save');
        if (goalButton) {
          goalButton.addEventListener('click', saveWalletGoal);
        }
        var clearGoalButton = $('wallet-goal-clear');
        if (clearGoalButton) {
          clearGoalButton.addEventListener('click', clearWalletGoal);
        }
        $('wallet-search').addEventListener('input', function () {
          state.walletQuery = $('wallet-search').value;
          renderWalletTransactions();
        });
        body.querySelectorAll('[data-wallet-filter]').forEach(function (button) {
          button.addEventListener('click', function () {
            state.walletFilter = button.getAttribute('data-wallet-filter') || 'all';
            saveSort('wallet-filter', state.walletFilter);
            body.querySelectorAll('[data-wallet-filter]').forEach(function (item) {
              item.classList.toggle(
                'active',
                item.getAttribute('data-wallet-filter') === state.walletFilter
              );
            });
            renderWalletTransactions();
          });
        });
        renderWalletTransactions();
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '钱包打不开') +
          '</p>';
      });
  }

  function walletKindLabels() {
    return {
      work: '工作收入', living: '生活开销', shop: '商店',
      gift: '主人给的', ask: '向主人要的', goal: '存款目标',
      reward: '愿望奖励', master: '主人给的', other: '其他'
    };
  }

  function filterWalletTransactions(transactions, query, filter) {
    var text = String(query || '').trim().toLowerCase();
    var kind = filter || 'all';
    var labels = walletKindLabels();
    return (transactions || []).filter(function (tx) {
      var amount = Number(tx.amount || 0);
      if (kind === 'income' && amount < 0) return false;
      if (kind === 'expense' && amount >= 0) return false;
      if (!text) return true;
      return [
        labels[tx.kind] || tx.kind || '收支',
        tx.reason || '',
        tx.at || ''
      ].join(' ').toLowerCase().indexOf(text) >= 0;
    });
  }

  function renderWalletTransactions() {
    var list = $('wallet-tx-list');
    if (!list) return;
    var transactions = state.walletTransactions || [];
    var walletFilter = state.walletFilter || 'all';
    var query = String(state.walletQuery || '').trim().toLowerCase();
    var kindLabels = walletKindLabels();
    var visible = filterWalletTransactions(transactions, query, walletFilter);
    if (!visible.length) {
      list.innerHTML = '<p class="inventory-empty">' +
        (query ? '没有匹配的流水。' : '还没有收支记录。') + '</p>';
      return;
    }
    var groups = {};
    var order = [];
    visible.slice(0, 20).forEach(function (tx) {
      var day = String(tx.at || '').slice(0, 10) || '未知日期';
      if (!groups[day]) {
        groups[day] = [];
        order.push(day);
      }
      groups[day].push(tx);
    });
    list.innerHTML = order.map(function (day) {
      return '<div class="wallet-tx-day">' + escapeHtml(day) + '</div>' +
        groups[day].map(function (tx) {
          var amount = Number(tx.amount || 0);
          var time = String(tx.at || '').slice(11, 16);
          return '<div class="wallet-tx">' +
            '<span class="wallet-tx-kind">' +
            escapeHtml(kindLabels[tx.kind] || tx.kind || '收支') + '</span>' +
            '<span class="wallet-tx-reason">' +
            escapeHtml(String(tx.reason || '').slice(0, 40)) + '</span>' +
            (time ? '<small class="wallet-tx-time">' + escapeHtml(time) + '</small>' : '') +
            '<b class="' + (amount >= 0 ? 'positive' : 'negative') + '">' +
            (amount >= 0 ? '+' : '') + amount + ' 元</b></div>';
        }).join('');
    }).join('');
  }

  function exportWalletTransactions() {
    var query = state.walletQuery || '';
    var transactions = filterWalletTransactions(
      state.walletTransactions || [],
      query,
      state.walletFilter
    );
    if (!transactions.length) {
      showToast(query || (state.walletFilter || 'all') !== 'all'
        ? '当前筛选没有可导出的流水'
        : '还没有收支记录可以导出');
      return;
    }
    var labels = walletKindLabels();
    var lines = ['时间,类型,金额,说明'];
    transactions.forEach(function (tx) {
      lines.push([
        csvCell(tx.at || ''),
        csvCell(labels[tx.kind] || tx.kind || '其他'),
        Number(tx.amount || 0),
        csvCell(tx.reason || '')
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var filtered = Boolean(query) || (state.walletFilter || 'all') !== 'all';
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '钱包流水-' + day + (filtered ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('钱包流水已导出');
  }

  function saveWalletGoal() {
    var nameInput = $('wallet-goal-name');
    var targetInput = $('wallet-goal-target');
    var wishInput = $('wallet-goal-wish');
    var name = String(nameInput && nameInput.value || '').trim();
    var target = Number(targetInput && targetInput.value);
    if (!name) {
      showToast('先填写目标名称');
      return;
    }
    if (!target || target <= 0) {
      showToast('目标金额必须大于 0');
      return;
    }
    var button = $('wallet-goal-save');
    if (button) button.disabled = true;
    fetch('/api/wallet/goal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        name: name,
        target: target,
        wish: String(wishInput && wishInput.value || '').trim()
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '目标没保存');
        showToast('存款目标已保存');
        renderWallet();
        fetchState();
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '目标没保存');
      });
  }

  function clearWalletGoal() {
    if (!window.confirm('确定清除当前存款目标吗？')) return;
    fetch('/api/wallet/goal/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || ''
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '目标没清除');
        showToast('存款目标已清除');
        renderWallet();
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '目标没清除');
      });
  }

  function giveWalletMoney() {
    var input = $('wallet-give-amount');
    var button = $('wallet-give');
    var amount = input ? Number(input.value) : 0;
    if (!amount || amount <= 0) {
      showToast('先填写要给月月的金额');
      if (input) input.focus();
      return;
    }
    if (amount > 100000) {
      showToast('一次最多给 100000 元');
      return;
    }
    if (button) {
      button.disabled = true;
      button.textContent = '给...';
    }
    fetch('/api/wallet/give', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: garagePersona(),
        amount: amount
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '给钱失败');
        showToast('已给月月 ' + data.amount + ' 元');
        renderWallet();
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '给钱失败');
        if (button) {
          button.disabled = false;
          button.textContent = '给';
        }
      });
  }

