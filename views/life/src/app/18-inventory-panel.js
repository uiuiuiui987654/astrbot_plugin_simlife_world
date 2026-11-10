  function openInventory(anchor) {
    var search = $('inventory-search');
    if (search) search.value = state.inventoryQuery || '';
    renderInventory();
    $('inventory-modal').classList.remove('hidden');
    if (anchor) {
      var target = $(anchor);
      if (target && target.scrollIntoView) {
        target.scrollIntoView({ block: 'start', behavior: 'auto' });
      }
    }
  }

  function closeInventory() {
    $('inventory-modal').classList.add('hidden');
  }

  function exportInventory() {
    var data = state.data || {};
    var query = String(state.inventoryQuery || '').trim().toLowerCase();
    var match = function (parts) {
      return !query || parts.join(' ').toLowerCase().indexOf(query) >= 0;
    };
    var shelf = (data.bookshelf || []).filter(function (book) {
      var filter = state.shelfFilter || 'all';
      if (filter === 'finished' && !book.finished) return false;
      if (filter === 'reading' &&
          (book.finished || Number(book.chapter || 0) <= 0)) return false;
      if (filter === 'unread' &&
          (book.finished || Number(book.chapter || 0) > 0)) return false;
      return match([book.title, book.genre, book.author]);
    });
    var possessions = ((data.money && data.money.possessions) || [])
      .filter(function (item) {
        return match([item.name, item.category, item.room]);
      });
    if (!shelf.length && !possessions.length) {
      showToast(query || (state.shelfFilter || 'all') !== 'all'
        ? '当前筛选没有可导出的物品'
        : '还没有物品可以导出');
      return;
    }
    var lines = ['类型,名称,分类,房间或进度,价格'];
    possessions.forEach(function (item) {
      lines.push([
        csvCell('物品'),
        csvCell(item.name || ''),
        csvCell(item.category || ''),
        csvCell(item.room || ''),
        Number.isFinite(Number(item.price)) ? Number(item.price) : ''
      ].join(','));
    });
    shelf.forEach(function (book) {
      var total = Math.max(1, Number(book.total_chapters) || 1);
      var progress = book.finished
        ? '读完'
        : '第 ' + Number(book.chapter || 0) + '/' + total + ' 章';
      lines.push([
        csvCell('书籍'),
        csvCell(book.title || ''),
        csvCell(book.genre || ''),
        csvCell(progress),
        ''
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var filtered = Boolean(query) || (state.shelfFilter || 'all') !== 'all';
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '物品清单-' + day + (filtered ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('物品清单已导出');
  }

  function onRoom3DItemDrop(info) {
    if (!info || !info.id) return;
    var item = (state.homeItems || []).find(function (entry) {
      return String(entry.id) === String(info.id);
    }) || info.item || null;
    var placed = Boolean(item && item.placed);
    var url = placed ? '/api/place_item' : '/api/decor/place';
    var payload = placed
      ? {
          item: (item && (item.possession_id || item.name)) || info.id,
          room: info.room,
          x: info.x,
          y: info.y,
          z_cm: info.z_cm || 0,
          surface_id: info.surface_id || ''
        }
      : {
          persona: (state.data && state.data.persona) || '',
          item_id: info.id,
          room: info.room,
          x: info.x,
          y: info.y
        };
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '移不动');
        showToast('已调整位置');
        fetchHomeItems();
        fetchState();
        if (state.decorMode) fetchDecorItems(false);
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '移不动');
      });
  }

