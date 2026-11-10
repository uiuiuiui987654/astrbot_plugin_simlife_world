  function loadShop() {
    var category = $('shop-category').value;
    var data = state.data || {};
    var balance = Number((data.money || {}).balance);
    $('shop-balance').textContent = isNaN(balance)
      ? '钱包余额 --'
      : '钱包余额 ' + (Number.isInteger(balance) ? balance : balance.toFixed(2)) + ' 元';
    fetch('/api/shop?category=' + encodeURIComponent(category), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '商店没开门');
        var select = $('shop-category');
        var current = select.value;
        var categories = data.categories || [];
        if (!select.getAttribute('data-filled')) {
          select.innerHTML = '<option value="">全部分类</option>' +
            categories.map(function (category) {
              return '<option value="' + escapeHtml(category) + '">' +
                escapeHtml(category) + '</option>';
            }).join('');
          select.value = current || '';
          select.setAttribute('data-filled', '1');
        }
        renderShop(data.items || []);
      })
      .catch(function (error) {
        $('shop-body').innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '商店没开门') +
          '</p>';
      });
  }

  function shopFavorites() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-shop-favorites') || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  }

  function toggleShopFavorite(id) {
    if (!id) return;
    var favorites = shopFavorites();
    var index = favorites.indexOf(id);
    if (index >= 0) {
      favorites.splice(index, 1);
    } else {
      favorites.push(id);
    }
    try {
      localStorage.setItem('vl-shop-favorites', JSON.stringify(favorites));
    } catch (error) {
      showToast('收藏保存失败');
      return;
    }
    renderShop(state.shopItems || []);
  }

  function renderShop(items) {
    var body = $('shop-body');
    if (!body) return;
    state.shopItems = items;
    syncShopControls();
    var query = String(state.shopQuery || '').trim().toLowerCase();
    var filtered = query
      ? items.filter(function (item) {
          return [item.name, item.description, item.category]
            .join(' ').toLowerCase().indexOf(query) >= 0;
        })
      : items;
    var sort = state.shopSort || 'default';
    if (sort !== 'default') {
      filtered = filtered.slice().sort(function (a, b) {
        if (sort === 'name') {
          return String(a.name || '').localeCompare(String(b.name || ''), 'zh');
        }
        var diff = Number(a.price || 0) - Number(b.price || 0);
        if (sort === 'price_asc') return diff;
        if (sort === 'price_desc') return -diff;
        return 0;
      });
    }
    if (!filtered.length) {
      body.innerHTML = '<p class="inventory-empty">' +
        (state.shopOnlyFavorites
          ? '还没有符合条件的收藏商品。'
          : query ? '没有匹配的商品。' : '这个分类暂时没有商品。') + '</p>';
      return;
    }
    var favorites = shopFavorites();
    if (state.shopOnlyFavorites) {
      filtered = filtered.filter(function (item) {
        return favorites.indexOf(String(item.id || '')) >= 0;
      });
    }
    if (!filtered.length) {
      body.innerHTML = '<p class="inventory-empty">' +
        (state.shopOnlyFavorites
          ? '还没有符合条件的收藏商品。'
          : '没有匹配的商品。') + '</p>';
      return;
    }
    var money = (state.data && state.data.money) || {};
    var balance = Number(money.balance);
    body.innerHTML = filtered.map(function (item) {
      var isFavorite = favorites.indexOf(String(item.id || '')) >= 0;
      var price = Number(item.price || 0);
      var affordable = isNaN(balance) || price <= balance;
      return '<div class="shop-item' + (affordable ? '' : ' unaffordable') + '">' +
        '<span class="shop-icon">' + ItemArtwork.draw(item) + '</span>' +
        '<div class="shop-copy">' +
        '<div class="shop-name">' +
        '<button type="button" class="shop-fav' + (isFavorite ? ' active' : '') +
        '" data-shop-fav="' + escapeHtml(item.id || '') + '">' +
        (isFavorite ? '★' : '☆') + '</button>' +
        escapeHtml(item.name || '商品') +
        '<small>' + escapeHtml(item.category || '') + '</small></div>' +
        '<div class="shop-desc">' + escapeHtml(item.description || '') + '</div>' +
        '</div>' +
        '<div class="shop-buy-box">' +
        '<span class="shop-price">' + price + ' 元</span>' +
        '<button type="button" class="mini-btn shop-buy" data-shop-buy="' +
        escapeHtml(item.id || '') + '"' +
        (affordable ? '' : ' disabled title="余额不足"') + '>' +
        (affordable ? '下单' : '余额不足') + '</button>' +
        '</div>' +
        '</div>';
    }).join('');
    body.querySelectorAll('[data-shop-fav]').forEach(function (button) {
      button.addEventListener('click', function () {
        toggleShopFavorite(button.getAttribute('data-shop-fav'));
      });
    });
    body.querySelectorAll('[data-shop-buy]').forEach(function (button) {
      button.addEventListener('click', function () {
        buyShopItem(button.getAttribute('data-shop-buy'), button);
      });
    });
  }

  function buyShopItem(id, button) {
    if (!id) return;
    var item = null;
    (state.shopItems || []).forEach(function (entry) {
      if (String(entry.id || '') === String(id)) item = entry;
    });
    var price = Number((item || {}).price || 0);
    if (price >= 100 && !window.confirm(
      '确认花 ' + price + ' 元购买「' + String((item || {}).name || '商品') + '」吗？'
    )) {
      if (button) button.disabled = false;
      return;
    }
    if (button) button.disabled = true;
    fetch('/api/shop/buy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id, quantity: 1 })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '买不了');
        showToast(
          data.delivery
            ? '下单成功，预计 ' + String((data.order || {}).deliver_at || '').slice(11, 16) + ' 送到'
            : '买到了'
        );
        loadShop();
        fetchState();
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '买不了');
      });
  }

