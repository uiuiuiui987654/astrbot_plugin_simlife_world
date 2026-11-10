  function applyBookFontScale() {
    var content = $('book-content');
    if (!content) return;
    var scale = Number(state.bookFontScale) || 1;
    content.style.fontSize = (13 * scale).toFixed(1) + 'px';
  }

  function changeBookFont(delta) {
    state.bookFontScale = Math.max(
      0.8, Math.min(1.8, (Number(state.bookFontScale) || 1) + delta)
    );
    applyBookFontScale();
    try {
      localStorage.setItem('vl-book-font', String(state.bookFontScale));
    } catch (error) {
      // 本地存储不可用时只在当前会话生效。
    }
  }

  function applyBookTheme() {
    var content = $('book-content');
    if (!content) return;
    var theme = ['dark', 'sepia', 'light'].indexOf(state.bookTheme) >= 0
      ? state.bookTheme : 'dark';
    content.className = 'book-content book-theme-' + theme;
  }

  function cycleBookTheme() {
    var order = ['dark', 'sepia', 'light'];
    var current = order.indexOf(state.bookTheme);
    state.bookTheme = order[(current + 1) % order.length];
    applyBookTheme();
    try {
      localStorage.setItem('vl-book-theme', state.bookTheme);
    } catch (error) {
      // 本地存储不可用时只在当前会话生效。
    }
  }

  function bookBookmarks() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-book-bookmarks') || '{}');
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function bookBookmarkKey() {
    return String(state.bookId || '') + '::' + String(state.bookChapter || 1);
  }

  function bookmarkSnapshot(raw) {
    if (raw && typeof raw === 'object') {
      return {
        scroll: Math.max(0, Number(raw.scroll) || 0),
        ratio: raw.ratio == null ? null : Math.max(0, Math.min(1, Number(raw.ratio) || 0)),
        at: raw.at || ''
      };
    }
    return { scroll: Math.max(0, Number(raw) || 0), ratio: null, at: '' };
  }

  function bookmarkScrollFor(panel, data) {
    if (!panel) return 0;
    var max = Math.max(0, (panel.scrollHeight || 0) - (panel.clientHeight || 0));
    if (data && data.ratio != null && max > 0) {
      return Math.round(Math.max(0, Math.min(1, Number(data.ratio))) * max);
    }
    return Math.max(0, Number(data && data.scroll) || 0);
  }

  function applyBookBookmark(panel, data) {
    if (!panel) return;
    panel.scrollTop = bookmarkScrollFor(panel, data);
  }

  function updateBookBookmarkInfo() {
    var info = $('book-bookmark-info');
    if (!info) return;
    var bookmarks = bookBookmarks();
    var has = Object.prototype.hasOwnProperty.call(bookmarks, bookBookmarkKey());
    info.textContent = has ? '本章有书签' : '';
  }

  function updateBookNoteStatus(count) {
    var status = $('book-note-status');
    if (!status) return;
    var number = Number(count) || 0;
    status.textContent = number > 0 ? '已有 ' + number + ' 条笔记' : '';
  }

  function lastBookNotes(notes, limit) {
    var all = notes || [];
    var count = limit ? Math.max(1, limit) : all.length;
    var start = Math.max(0, all.length - count);
    return all.slice(start).map(function (note, offset) {
      return {
        text: note.text || '',
        at: note.at || '',
        chapter: Math.max(0, Number(note.chapter || 0)),
        index: start + offset
      };
    });
  }

  function filterBookNotes(notes, query) {
    var text = String(query || '').trim().toLowerCase();
    if (!text) return notes || [];
    return (notes || []).filter(function (note) {
      return [note.text, note.at, note.chapter ? '第 ' + note.chapter + ' 章' : '']
        .join(' ').toLowerCase().indexOf(text) >= 0;
    });
  }

  function renderBookNotes() {
    var list = $('book-note-list');
    if (!list) return;
    var allNotes = state.bookNotes || [];
    var query = String(state.bookNoteQuery || '').trim().toLowerCase();
    var notes = filterBookNotes(allNotes, query);
    if (!notes.length) {
      list.innerHTML = allNotes.length
        ? '<p class="inventory-empty">没有匹配的笔记。</p>'
        : '';
      return;
    }
    list.innerHTML = notes.map(function (note, index) {
      var absolute = note.index == null ? index : note.index;
      var chapterTag = Number(note.chapter || 0) > 0
        ? '<button type="button" class="book-note-chapter" ' +
          'data-book-note-goto="' + Number(note.chapter) +
          '" title="跳到第 ' + Number(note.chapter) + ' 章">第 ' +
          Number(note.chapter) + ' 章</button>'
        : '';
      return '<div class="book-note-item"><span>' + chapterTag +
        escapeHtml(note.text || '') + '</span>' +
        '<button type="button" data-book-note-delete="' + absolute +
        '" title="删除笔记">×</button></div>';
    }).join('');
    list.querySelectorAll('[data-book-note-goto]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (!state.bookId) return;
        openBook(state.bookId, Number(button.getAttribute('data-book-note-goto')) || 1);
      });
    });
    list.querySelectorAll('[data-book-note-delete]').forEach(function (button) {
      button.addEventListener('click', function () {
        deleteBookNote(Number(button.getAttribute('data-book-note-delete')));
      });
    });
  }

  function deleteBookNote(index) {
    if (!state.bookId) return;
    fetch('/api/book/note/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        id: state.bookId,
        index: index
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '删不掉');
        state.bookNotes = lastBookNotes(data.notes || []);
        state.bookNoteTotal = (data.notes || []).length;
        updateBookNoteStatus(state.bookNoteTotal);
        renderBookNotes();
        showToast('笔记已删除');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '删不掉');
      });
  }

  function exportBookNotes() {
    var notes = filterBookNotes(state.bookNotes || [], state.bookNoteQuery);
    if (!notes.length) {
      showToast(state.bookNoteQuery
        ? '当前筛选没有可导出的笔记'
        : '还没有读书笔记可以导出');
      return;
    }
    var lines = ['章节,时间,笔记'];
    notes.forEach(function (note) {
      lines.push([
        csvCell(note.chapter ? '第 ' + note.chapter + ' 章' : ''),
        csvCell(note.at || ''),
        csvCell(note.text || '')
      ].join(','));
    });
    var title = String(state.bookTitle || '书籍').replace(/[\\/:*?"<>|]/g, '_');
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = title + '-读书笔记' +
      (state.bookNoteQuery ? '-筛选' : '') + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('读书笔记已导出');
  }

  function saveBookNote() {
    if (!state.bookId) return;
    var input = $('book-note-input');
    var text = String(input && input.value || '').trim();
    if (!text) {
      showToast('先写一句笔记');
      return;
    }
    fetch('/api/book/note', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        id: state.bookId,
        text: text,
        chapter: Number(state.bookChapter || 0)
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '笔记没记下');
        if (input) input.value = '';
        state.bookNotes = lastBookNotes(data.notes || []);
        state.bookNoteTotal = (data.notes || []).length;
        updateBookNoteStatus(state.bookNoteTotal);
        renderBookNotes();
        showToast('读书笔记已记下');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '笔记没记下');
      });
  }

  function renderBookBookmarks() {
    var list = $('book-bookmark-list');
    if (!list) return;
    var bookmarks = bookBookmarks();
    var prefix = String(state.bookId || '') + '::';
    var rows = [];
    Object.keys(bookmarks).forEach(function (key) {
      if (key.indexOf(prefix) !== 0) return;
      var chapter = Number(key.slice(prefix.length)) || 1;
      var data = bookmarkSnapshot(bookmarks[key]);
      rows.push({
        chapter: chapter,
        scroll: data.scroll,
        ratio: data.ratio,
        at: data.at
      });
    });
    rows.sort(function (a, b) { return a.chapter - b.chapter; });
    if (!rows.length) {
      list.innerHTML = '';
      return;
    }
    list.innerHTML = rows.map(function (row) {
      var title = String((state.bookChapterTitles || [])[row.chapter - 1] || '');
      var meta = row.ratio != null
        ? '已读 ' + Math.round(row.ratio * 100) + '%'
        : '位置 ' + row.scroll;
      return '<div class="book-bookmark-item">' +
        '<button type="button" class="book-bookmark-jump" ' +
        'data-bookmark-chapter="' + row.chapter + '" ' +
        'data-bookmark-scroll="' + row.scroll + '" ' +
        'data-bookmark-ratio="' + (row.ratio == null ? '' : row.ratio) + '">' +
        '<span>第 ' + row.chapter + ' 章' + (title ? ' · ' + escapeHtml(title) : '') +
        '</span><small>' + meta + '</small></button>' +
        '<button type="button" class="book-bookmark-delete" ' +
        'data-bookmark-delete="' + row.chapter + '" title="删除书签">×</button></div>';
    }).join('');
    list.querySelectorAll('[data-bookmark-chapter]').forEach(function (button) {
      button.addEventListener('click', function () {
        var chapter = Number(button.getAttribute('data-bookmark-chapter')) || 1;
        var ratioText = button.getAttribute('data-bookmark-ratio');
        var data = {
          scroll: Number(button.getAttribute('data-bookmark-scroll')) || 0,
          ratio: ratioText == null || ratioText === '' ? null : Number(ratioText)
        };
        var panel = document.querySelector('.book-panel');
        if (chapter === Number(state.bookChapter) && panel) {
          applyBookBookmark(panel, data);
          return;
        }
        state.bookRestoreScroll = data;
        openBook(state.bookId, chapter);
      });
    });
    list.querySelectorAll('[data-bookmark-delete]').forEach(function (button) {
      button.addEventListener('click', function (event) {
        event.stopPropagation();
        removeBookBookmark(Number(button.getAttribute('data-bookmark-delete')));
      });
    });
  }

  function removeBookBookmark(chapter) {
    if (!state.bookId) return;
    var bookmarks = bookBookmarks();
    delete bookmarks[String(state.bookId) + '::' + chapter];
    try {
      localStorage.setItem('vl-book-bookmarks', JSON.stringify(bookmarks));
    } catch (error) {
      showToast('书签删除失败');
      return;
    }
    updateBookBookmarkInfo();
    renderBookBookmarks();
    showToast('第 ' + chapter + ' 章书签已删除');
  }

  function saveBookBookmark() {
    var panel = document.querySelector('.book-panel');
    if (!panel || !state.bookId) return;
    var bookmarks = bookBookmarks();
    var max = Math.max(0, (panel.scrollHeight || 0) - (panel.clientHeight || 0));
    var scroll = Math.max(0, Math.round(panel.scrollTop || 0));
    bookmarks[bookBookmarkKey()] = {
      scroll: scroll,
      ratio: max > 0 ? Math.round((scroll / max) * 10000) / 10000 : 0,
      at: new Date().toISOString()
    };
    try {
      localStorage.setItem('vl-book-bookmarks', JSON.stringify(bookmarks));
    } catch (error) {
      showToast('书签保存失败');
      return;
    }
    updateBookBookmarkInfo();
    renderBookBookmarks();
    showToast('书签已保存');
  }

  function restoreBookBookmark() {
    var panel = document.querySelector('.book-panel');
    if (!panel || !state.bookId) return;
    var bookmarks = bookBookmarks();
    var key = bookBookmarkKey();
    if (!Object.prototype.hasOwnProperty.call(bookmarks, key)) {
      showToast('本章还没有书签');
      return;
    }
    applyBookBookmark(panel, bookmarkSnapshot(bookmarks[key]));
    showToast('已回到书签位置');
  }

  function updateBookNav() {
    var previous = $('book-prev');
    var next = $('book-next');
    if (previous) previous.disabled = state.bookChapter <= 1;
    if (next) next.disabled = state.bookChapter >= state.bookChapters;
    var select = $('book-chapter-select');
    if (select) {
      var count = Math.max(1, Number(state.bookChapters) || 1);
      var bookKey = String(state.bookId || '');
      if (
        Number(select.getAttribute('data-count') || 0) !== count ||
        String(select.getAttribute('data-book') || '') !== bookKey
      ) {
        var titles = state.bookChapterTitles || [];
        select.innerHTML = Array.from({ length: count }, function (_, index) {
          var chapter = index + 1;
          var title = String(titles[index] || '');
          var label = '第 ' + chapter + ' 章' + (title ? ' · ' + title : '');
          return '<option value="' + chapter + '" title="' + escapeHtml(label) + '">' +
            escapeHtml(label) + '</option>';
        }).join('');
        select.setAttribute('data-count', String(count));
        select.setAttribute('data-book', bookKey);
      }
      select.value = String(state.bookChapter || 1);
    }
  }

  function changeBookChapter(delta) {
    if (!state.bookId) return;
    var target = Number(state.bookChapter) + delta;
    if (target < 1 || target > Number(state.bookChapters)) return;
    openBook(state.bookId, target, null);
  }

  function bookReadingStore() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-book-reading') || '{}');
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function bookReadingLabel(bookId) {
    var seconds = Number(bookReadingStore()[String(bookId || '')] || 0);
    if (!seconds || seconds < 60) return '';
    var minutes = Math.round(seconds / 60);
    if (minutes < 60) return '已读 ' + minutes + ' 分钟';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return '已读 ' + hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '');
  }

  function totalBookReadingLabel() {
    var store = bookReadingStore();
    var total = 0;
    Object.keys(store).forEach(function (key) {
      total += Number(store[key] || 0);
    });
    return formatReadingSeconds(total);
  }

  function formatReadingSeconds(seconds) {
    if (!seconds || seconds < 60) return '';
    var minutes = Math.round(seconds / 60);
    if (minutes < 60) return minutes + ' 分钟';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '');
  }

  function bookReadingDailyStore() {
    try {
      var parsed = JSON.parse(
        localStorage.getItem('vl-book-reading-daily') || '{}'
      );
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function periodBookReadingSeconds(days) {
    var store = bookReadingDailyStore();
    var total = 0;
    var now = new Date();
    var span = Math.max(1, Number(days) || 7);
    for (var i = 0; i < span; i++) {
      var day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
      total += Number(store[dateKeyFromDate(day)] || 0);
    }
    return total;
  }

  function periodBookReadingLabel(days) {
    return formatReadingSeconds(periodBookReadingSeconds(days));
  }

  function periodBookReadingDays(days) {
    var store = bookReadingDailyStore();
    var count = 0;
    var now = new Date();
    var span = Math.max(1, Number(days) || 7);
    for (var i = 0; i < span; i++) {
      var day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
      if (Number(store[dateKeyFromDate(day)] || 0) >= 60) count += 1;
    }
    return count;
  }

  function bookReadingStreak() {
    var store = bookReadingDailyStore();
    var day = new Date();
    var key = dateKeyFromDate(day);
    if (Number(store[key] || 0) < 60) {
      day.setDate(day.getDate() - 1);
    }
    var streak = 0;
    while (streak < 400 && Number(store[dateKeyFromDate(day)] || 0) >= 60) {
      streak += 1;
      day.setDate(day.getDate() - 1);
    }
    return streak;
  }

  function flushBookReadingTime() {
    var startedAt = Number(state.bookOpenedAt || 0);
    var bookId = String(state.bookId || '');
    state.bookOpenedAt = 0;
    if (!startedAt || !bookId) return;
    var seconds = Math.round((Date.now() - startedAt) / 1000);
    if (seconds < 1) return;
    var store = bookReadingStore();
    store[bookId] = Number(store[bookId] || 0) + seconds;
    try {
      localStorage.setItem('vl-book-reading', JSON.stringify(store));
    } catch (error) {
      /* 本地记录失败不影响阅读 */
    }
    var daily = bookReadingDailyStore();
    var todayKey = dateKeyFromDate(new Date());
    var previousTodaySeconds = Number(daily[todayKey] || 0);
    daily[todayKey] = previousTodaySeconds + seconds;
    var cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 400);
    var cutoffKey = dateKeyFromDate(cutoff);
    Object.keys(daily).forEach(function (key) {
      if (key < cutoffKey) delete daily[key];
    });
    try {
      localStorage.setItem('vl-book-reading-daily', JSON.stringify(daily));
    } catch (error) {
      /* 本地记录失败不影响阅读 */
    }
    var goalSeconds = Math.max(1, Number(state.readingGoal) || 30) * 60;
    if (previousTodaySeconds < goalSeconds &&
        previousTodaySeconds + seconds >= goalSeconds) {
      showToast('今日阅读目标已达成');
    }
  }

  function recordBookProgress(bookId, chapter) {
    var id = String(bookId || '');
    var value = Math.max(1, Number(chapter) || 1);
    if (!id) return;
    fetch('/api/book/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: (state.data && state.data.persona) || '',
        id: id,
        chapter: value
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) return;
        var shelf = (state.data && state.data.bookshelf) || [];
        var entry = shelf.find(function (book) {
          return String(book.id) === id;
        });
        if (entry) {
          entry.chapter = Math.max(Number(entry.chapter) || 0, Number(data.chapter) || 0);
          entry.finished = Boolean(data.finished);
        }
        var inventoryModal = $('inventory-modal');
        if (inventoryModal && !inventoryModal.classList.contains('hidden')) {
          renderInventory();
        }
      })
      .catch(function () {
        /* 阅读进度保存失败时不打断当前阅读。 */
      });
  }

  function openBook(id, chapter, button) {
    if (!id) return;
    var sameBook = String(state.bookId || '') === String(id);
    var modalOpen = !$('book-modal').classList.contains('hidden');
    if (!sameBook || !modalOpen) {
      flushBookReadingTime();
      state.bookOpenedAt = Date.now();
    }
    if (button) button.disabled = true;
    fetch('/api/book?persona=' + encodeURIComponent(
      (state.data && state.data.persona) || ''
    ) + '&id=' + encodeURIComponent(id) + '&chapter=' + chapter)
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '读不了');
        $('book-title').textContent = '《' + data.title + '》';
        var chapterNumber = Number(data.chapter || chapter) || 1;
        var chapterTitle = String(
          (data.chapter_titles || [])[chapterNumber - 1] || ''
        );
        $('book-sub').textContent = data.author + ' · ' + data.genre +
          ' · 共 ' + data.chapters + ' 章 · 第 ' + chapterNumber + ' 章' +
          (chapterTitle ? ' ' + chapterTitle : '');
        $('book-content').textContent = data.content;
        state.bookId = data.id || id;
        state.bookChapter = Number(data.chapter || chapter) || 1;
        state.bookChapters = Number(data.chapters) || 1;
        state.bookChapterTitles = data.chapter_titles || [];
        var bookProgress = Math.round(
          state.bookChapter / Math.max(1, state.bookChapters) * 100
        );
        var progressFill = $('book-progress-fill');
        if (progressFill) progressFill.style.width = bookProgress + '%';
        applyBookFontScale();
        applyBookTheme();
        updateBookNav();
        updateBookBookmarkInfo();
        state.bookNotes = data.note_items || [];
        state.bookNoteTotal = Number(data.notes) || 0;
        state.bookTitle = String(data.title || '');
        var noteSearch = $('book-note-search');
        if (noteSearch) noteSearch.value = state.bookNoteQuery || '';
        updateBookNoteStatus(state.bookNoteTotal);
        renderBookNotes();
        renderBookBookmarks();
        recordBookProgress(state.bookId, state.bookChapter);
        $('book-modal').classList.remove('hidden');
        if (state.bookRestoreScroll != null) {
          var restoreData = bookmarkSnapshot(state.bookRestoreScroll);
          state.bookRestoreScroll = null;
          window.setTimeout(function () {
            var panel = document.querySelector('.book-panel');
            if (panel) applyBookBookmark(panel, restoreData);
          }, 0);
        } else {
          var bookPanel = document.querySelector('.book-panel');
          if (bookPanel) bookPanel.scrollTop = 0;
        }
        if (button) button.disabled = false;
      })
      .catch(function (error) {
        if (button) button.disabled = false;
        showToast(error && error.message ? error.message : '读不了');
      });
  }

  function closeBook() {
    flushBookReadingTime();
    $('book-modal').classList.add('hidden');
  }

