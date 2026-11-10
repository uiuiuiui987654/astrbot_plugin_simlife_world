  // 3D 脚本按需加载（见 05a-render-mode.js），加载完成后才接上拖放与点击回调。
  function wire3D() {
    if (window.Room3D) {
      window.Room3D.onItemDrop = onRoom3DItemDrop;
      window.Room3D.onPropClick = function (info) {
        if (!info || !info.id) return;
        if (/^(home_car|garage_jeep|garage_sports)$/.test(String(info.id))) {
          openVehicle(vehicleKeyFromCar(String(info.id)));
          return;
        }
        var hitItem = (state.homeItems || []).find(function (entry) {
          return String(entry.id) === String(info.id);
        });
        if (hitItem) {
          openItem(hitItem.id);
          return;
        }
        openGenericProp(info);
      };
    }
  }

  function init() {
    wire3D();
    try {
      state.animations = localStorage.getItem('vl-anim') !== 'off';
    } catch (e) {
      state.animations = true;
    }
    try {
      var savedBookFont = parseFloat(localStorage.getItem('vl-book-font'));
      if (savedBookFont >= 0.8 && savedBookFont <= 1.8) {
        state.bookFontScale = savedBookFont;
      }
    } catch (e) {
      state.bookFontScale = 1;
    }
    applyBookFontScale();
    try {
      var savedBookTheme = localStorage.getItem('vl-book-theme');
      if (['dark', 'sepia', 'light'].indexOf(savedBookTheme) >= 0) {
        state.bookTheme = savedBookTheme;
      }
    } catch (e) {
      state.bookTheme = 'dark';
    }
    applyBookTheme();
    var pageParams = new URLSearchParams(window.location.search);
    if (pageParams.get('scene') && SCENES.some(function(s) { return s.key === pageParams.get('scene'); })) state.previewScene = pageParams.get('scene');
    if (/^[12]$/.test(pageParams.get('floor') || '')) state.previewFloor = Number(pageParams.get('floor'));
    document.querySelectorAll('.floor-tab').forEach(function(b) { b.addEventListener('click', function() { state.previewFloor = Number(b.dataset.floor); renderHome(); }); });
    $('floor-follow').addEventListener('click', function() { state.previewFloor = null; renderHome(); });
    $('home-stage').addEventListener('click', function(event) {
      if (cameraMode) return;
      var stairNode = event.target.closest('[data-stair-floor]');
      if (stairNode) {
        event.preventDefault();
        state.previewFloor = Number(stairNode.getAttribute('data-stair-floor')) || 2;
        renderHome();
        showToast('顺着楼梯上到 ' + state.previewFloor + 'F');
        return;
      }
      var roomNode = event.target.closest('.studio-room');
      if (!roomNode) return;
      var roomName = roomNode.getAttribute('data-room');
      if (!roomName || !window.SceneStudio) return;
      state.previewRoom = roomName;
      state.previewFloor = SceneStudio.floorFor(roomName);
      renderHome();
      renderScene(true);
      showToast('查看 ' + roomName);
    });
    $('home-stage').addEventListener('keydown', function(event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var stairNode = event.target.closest('[data-stair-floor]');
      if (!stairNode) return;
      event.preventDefault();
      state.previewFloor = Number(stairNode.getAttribute('data-stair-floor')) || 2;
      renderHome();
      showToast('顺着楼梯上到 ' + state.previewFloor + 'F');
    });
    $('scene-stage').addEventListener('click', function(event) {
      var car = event.target.closest('.garage-car-hit');
      if (!car) return;
      event.preventDefault();
      openVehicle(vehicleKeyFromCar(car.getAttribute('data-car')));
    });
    ['click', 'keydown'].forEach(function(type) { $('scene-stage').addEventListener(type, function(event) { if (type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return; if (state.decorSuppressClick) { state.decorSuppressClick = false; event.preventDefault(); event.stopPropagation(); return; } var hit = event.target.closest('.furniture-hit'); if (hit) { event.preventDefault(); openItem(hit.getAttribute('data-id')); } }); });
    if (pageParams.get('item')) state.pendingItem = pageParams.get('item');
    applyAnimations();
    applyRenderMode();
    if (want3D()) ensure3DScripts('core');
    if ($('render-toggle')) $('render-toggle').addEventListener('click', cycleRenderMode);
    $('anim-toggle').addEventListener('click', function () {
      state.animations = !state.animations;
      try { localStorage.setItem('vl-anim', state.animations ? 'on' : 'off'); } catch (e) {}
      applyAnimations();
      render();
    });
    $('decor-toggle').addEventListener('click', function () {
      if (state.decorMode) {
        exitDecorMode();
        return;
      }
      openDecorDrawer();
    });
    $('items-toggle').addEventListener('click', function () {
      if (state.decorMode) exitDecorMode();
      toggleItemDrawer();
    });
    $('item-search').addEventListener('input', function () {
      state.itemQuery = $('item-search').value;
      renderItemDrawer();
    });
    $('fridge-toggle').addEventListener('click', function () {
      if (state.homeItems && state.homeItems.length) {
        openItem('fridge');
        return;
      }
      state.pendingItem = 'fridge';
      fetchHomeItems();
    });
    $('drawer-close').addEventListener('click', function () {
      toggleItemDrawer(false);
    });
    $('item-close').addEventListener('click', function () {
      closeItem();
    });
    $('home-svg').addEventListener('click', function (event) {
      var stair = event.target.closest('[data-stair-floor]');
      if (stair) {
        event.preventDefault();
        state.previewFloor = Number(stair.getAttribute('data-stair-floor')) || 1;
        renderHome();
        showToast('顺着楼梯到 ' + state.previewFloor + 'F');
        return;
      }
      var car = event.target.closest('.garage-car-hit');
      if (car) {
        event.preventDefault();
        openVehicle(vehicleKeyFromCar(car.getAttribute('data-car')));
        return;
      }
      var hit = event.target.closest('.furniture-hit');
      if (!hit) return;
      openItem(hit.getAttribute('data-id'));
    });
    $('home-svg').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var stair = event.target.closest('[data-stair-floor]');
      if (stair) {
        event.preventDefault();
        state.previewFloor = Number(stair.getAttribute('data-stair-floor')) || 1;
        renderHome();
        showToast('顺着楼梯到 ' + state.previewFloor + 'F');
        return;
      }
      var car = event.target.closest('.garage-car-hit');
      if (car) {
        event.preventDefault();
        openVehicle(vehicleKeyFromCar(car.getAttribute('data-car')));
        return;
      }
      var hit = event.target.closest('.furniture-hit');
      if (!hit) return;
      event.preventDefault();
      openItem(hit.getAttribute('data-id'));
    });
    $('item-groups').addEventListener('click', function (event) {
      var button = event.target.closest('.item-chip');
      if (!button) return;
      openItem(button.getAttribute('data-id'));
    });
    $('item-actions').addEventListener('click', function (event) {
      var button = event.target.closest('.pop-action');
      if (!button || !state.selectedItem) return;
      interactItemAction(
        state.selectedItem,
        button.getAttribute('data-action'),
        button
      );
    });
    $('interact-action').addEventListener('click', function () {
      var item = state.selectedItem;
      if (!item) return;
      if (item.generic_prop) {
        var genericAction = Array.isArray(item.actions) && item.actions.length
          ? item.actions[0] : '看看';
        interactItemAction(item, genericAction, null);
        return;
      }
      if (String(item.id) === 'bed') {
        var waking = Boolean(state.userSleeping);
        startInteraction({
          kind: 'chat',
          item_id: 'bed',
          action: waking ? '起床' : '睡觉',
          text: waking ? '我醒了，起床了。' : '我上床睡觉了，晚安。'
        }, waking ? '她抬起头' : '她放轻声音');
        showToast(waking ? '已告诉她你醒了' : '已告诉她你上床睡了');
        state.userSleeping = !waking;
        var button = $('interact-action');
        if (button) button.textContent = waking ? '我上床睡了' : '我醒了，起床';
        return;
      }
      if (isGameItem(item)) {
        openGameModal();
        return;
      }
      var isDish = String(item.id) === 'dining_table' ||
        String(item.name || '').indexOf('餐桌') >= 0;
      var action = Array.isArray(item.actions) && item.actions.length ? item.actions[0] : '';
      if (item.placed && ['吃掉', '喝掉', '使用'].indexOf(action) >= 0) {
        useInventoryItem(item.name);
        closeItem();
        return;
      }
      startInteraction({
        kind: 'chat',
        item_id: item.id,
        item_name: item.name || '',
        room: item.room || '',
        action: action,
        text: '我在' + (item.room || '') + '的' + (item.name || '这里') +
          '，想' + (action || '待一会儿') + '，你在干嘛？'
      }, isDish ? '她坐下来' : '她抬起头');
    });
    $('talk-send').addEventListener('click', sendChat);
    $('talk-input').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        sendChat();
      }
    });
    $('fridge-random').addEventListener('click', function () {
      randomFridgeRecipe();
    });
    $('fridge-refresh').addEventListener('click', function () {
      loadFridge();
    });
    $('fridge-export').addEventListener('click', exportFridge);
    $('fridge-search').addEventListener('input', function () {
      state.fridgeQuery = $('fridge-search').value;
      renderFridge();
    });
    $('persona-cycle').addEventListener('click', function () {
      var list = (state.data && state.data.personas) || [];
      if (list.length < 2) return;
      var index = -1;
      for (var i = 0; i < list.length; i++) {
        if (list[i].id === state.persona) index = i;
      }
      state.persona = list[(index + 1) % list.length].id;
      state.previewScene = null;
      fetchState();
    });
    $('follow-btn').addEventListener('click', function () {
      state.previewScene = null;
      renderScene(true);
      renderScenePicker(true);
    });
    $('preview-return').addEventListener('click', function () {
      if (cancelPlacement()) return;
      state.previewScene = null;
      state.previewRoom = null;
      renderScene(true);
      renderScenePicker(true);
      showToast('已回到当前日程');
    });
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) fetchState();
    });
    $('cook-open').addEventListener('click', openCookModal);
    $('cook-close').addEventListener('click', closeCookModal);
    document.querySelectorAll('[data-cook-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.cookFilter = button.getAttribute('data-cook-filter') || 'all';
        document.querySelectorAll('[data-cook-filter]').forEach(function (item) {
          item.classList.toggle(
            'active',
            item.getAttribute('data-cook-filter') === state.cookFilter
          );
        });
        renderCookDishes();
      });
    });
    $('cook-stop').addEventListener('click', stopCookRound);
    $('cook-serve').addEventListener('click', serveCookedDish);
    $('cook-dishes').addEventListener('click', function (event) {
      var button = event.target.closest('.cook-dish');
      if (button) startCookGame(button.getAttribute('data-name'));
    });
    $('game-open').addEventListener('click', openGameModal);
    $('game-close').addEventListener('click', closeGameModal);
    $('game-back').addEventListener('click', leaveGame);
    $('game-restart').addEventListener('click', restartCurrentGame);
    $('game-select-step').addEventListener('click', function (event) {
      var button = event.target.closest('.game-pick');
      if (button) startGame(button.getAttribute('data-game'));
    });
    $('game-battle-step').addEventListener('click', function (event) {
      var button = event.target.closest('[data-move]');
      if (button) chooseBattleMove(button.getAttribute('data-move'));
    });
    $('game-rps-step').addEventListener('click', function (event) {
      var button = event.target.closest('[data-rps]');
      if (button) chooseRps(button.getAttribute('data-rps'));
    });
    $('game-mole-start').addEventListener('click', startMoleRound);
    $('game-mole-grid').addEventListener('click', hitMole);
    $('game-ttt-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-ttt-cell');
      if (!cell) return;
      tttPlayerMove(Number(cell.getAttribute('data-cell')));
    });
    $('game-memory-grid').addEventListener('click', function (event) {
      var card = event.target.closest('.game-memory-card');
      if (card) memoryClick(Number(card.getAttribute('data-index')));
    });
    $('game-guess-submit').addEventListener('click', submitGuess);
    $('game-guess-input').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        submitGuess();
      }
    });
    $('game-dice-roll').addEventListener('click', rollDice);
    $('game-gomoku-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-gomoku-cell');
      if (cell) gomokuPlayerMove(Number(cell.getAttribute('data-index')));
    });
    $('game-connect4-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-connect4-cell');
      if (cell) connect4PlayerMove(Number(cell.getAttribute('data-col')));
    });
    $('game-reversi-board').addEventListener('click', function (event) {
      var cell = event.target.closest('.game-reversi-cell');
      if (cell) reversiPlayerMove(Number(cell.getAttribute('data-index')));
    });
    $('camera-toggle').addEventListener('click', enterCameraMode);
    $('camera-cancel').addEventListener('click', exitCameraMode);
    $('camera-character').addEventListener('click', function () {
      if (cameraMode) takeCameraPhoto({ target: 'character' }, '拍一张月月');
    });
    $('camera-room').addEventListener('click', function () {
      if (cameraMode) takeCameraPhoto({ target: 'room' }, '拍下这个房间');
    });
    document.addEventListener('mousemove', onCameraHover);
    $('photo-close').addEventListener('click', closePhotoModal);
    $('photo-save').addEventListener('click', saveCameraPhoto);
    $('schedule-close').addEventListener('click', closeScheduleDetail);
    $('schedule-modal').addEventListener('click', function (event) {
      if (event.target === $('schedule-modal')) closeScheduleDetail();
    });
    $('schedule-body').addEventListener('click', function (event) {
      if (event.target.closest('#schedule-preview')) {
        previewScheduleScene();
        return;
      }
      if (event.target.closest('[data-day-export]')) {
        exportDaySchedule();
        return;
      }
      var dayFilterButton = event.target.closest('[data-day-filter]');
      if (dayFilterButton) {
        state.dayScheduleFilter =
          dayFilterButton.getAttribute('data-day-filter') || 'all';
        saveSort('day-schedule-filter', state.dayScheduleFilter);
        openDaySchedule();
        return;
      }
      var dayRow = event.target.closest('[data-day-index]');
      if (dayRow) {
        var timeline = (state.data && state.data.timeline) || [];
        openScheduleDetail(timeline[Number(dayRow.getAttribute('data-day-index'))]);
      }
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        flushBookReadingTime();
      } else if (state.bookId &&
                 !$('book-modal').classList.contains('hidden')) {
        state.bookOpenedAt = Date.now();
      }
    });
    $('day-schedule-toggle').addEventListener('click', function () {
      closeFunctionMenu();
      openDaySchedule();
    });
    $('now-line').addEventListener('click', openDaySchedule);
    $('now-line').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      openDaySchedule();
    });
    $('trips-open').addEventListener('click', function () {
      closeFunctionMenu();
      openTrips();
    });
    $('trips-close').addEventListener('click', closeTrips);
    $('trips-refresh').addEventListener('click', function () {
      openTrips(true);
    });
    $('trips-export').addEventListener('click', exportTrips);
    $('outfit-open').addEventListener('click', function () {
      closeFunctionMenu();
      openOutfit();
    });
    $('outfit-close').addEventListener('click', closeOutfit);
    $('outfit-export').addEventListener('click', exportOutfit);
    $('outfit-modal').addEventListener('click', function (event) {
      if (event.target === $('outfit-modal')) closeOutfit();
    });
    $('health-open').addEventListener('click', function () {
      closeFunctionMenu();
      openHealth();
    });
    $('health-close').addEventListener('click', closeHealth);
    $('health-export').addEventListener('click', exportHealth);
    $('health-modal').addEventListener('click', function (event) {
      if (event.target === $('health-modal')) closeHealth();
    });
    $('activity-open').addEventListener('click', function () {
      closeFunctionMenu();
      openActivity();
    });
    $('activity-close').addEventListener('click', closeActivity);
    $('activity-refresh').addEventListener('click', function () {
      openActivity(true);
    });
    $('activity-export').addEventListener('click', exportActivity);
    $('activity-modal').addEventListener('click', function (event) {
      if (event.target === $('activity-modal')) closeActivity();
    });
    $('activity-body').addEventListener('click', function (event) {
      if (event.target.closest('[data-activity-reset]')) {
        resetActivityFilters();
        return;
      }
      var filterButton = event.target.closest('[data-activity-filter]');
      if (filterButton) {
        state.activityFilter =
          filterButton.getAttribute('data-activity-filter') || 'all';
        saveSort('activity-filter', state.activityFilter);
        renderActivity();
        return;
      }
      var row = event.target.closest('[data-activity-kind]');
      if (row) {
        openActivityTarget(row.getAttribute('data-activity-kind'));
      }
    });
    $('activity-body').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var row = event.target.closest('[data-activity-kind]');
      if (!row) return;
      event.preventDefault();
      openActivityTarget(row.getAttribute('data-activity-kind'));
    });
    $('activity-search').addEventListener('input', function () {
      state.activityQuery = $('activity-search').value || '';
      renderActivity();
    });
    $('trips-body').addEventListener('click', function (event) {
      var filterButton = event.target.closest('[data-trips-filter]');
      if (filterButton) {
        state.tripsFilter =
          filterButton.getAttribute('data-trips-filter') || 'all';
        saveSort('trips-filter', state.tripsFilter);
        renderTrips();
        return;
      }
      var button = event.target.closest('[data-trips-toggle]');
      if (!button) return;
      var key = button.getAttribute('data-trips-toggle');
      state.tripsExpanded[key] = !state.tripsExpanded[key];
      renderTrips();
    });
    $('trips-modal').addEventListener('click', function (event) {
      if (event.target === $('trips-modal')) closeTrips();
    });
    $('next-list').addEventListener('click', function (event) {
      var row = event.target.closest('[data-next-index]');
      if (!row) return;
      var items = (state.data && state.data.next) || [];
      openScheduleDetail(items[Number(row.getAttribute('data-next-index'))]);
    });
    $('timeline').addEventListener('click', function (event) {
      var segment = event.target.closest('[data-schedule-index]');
      if (!segment) return;
      var items = (state.data && state.data.timeline) || [];
      openScheduleDetail(items[Number(segment.getAttribute('data-schedule-index'))]);
    });
    $('inventory-toggle').addEventListener('click', openInventory);
    $('inventory-close').addEventListener('click', closeInventory);
    $('inventory-export').addEventListener('click', exportInventory);
    $('wish-count').addEventListener('click', openWishes);
    $('wish-count').addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openWishes();
      }
    });
    $('wish-close').addEventListener('click', closeWishes);
    $('wish-modal').addEventListener('click', function (event) {
      if (event.target === $('wish-modal')) closeWishes();
    });
    $('inventory-search').addEventListener('input', function () {
      state.inventoryQuery = $('inventory-search').value;
      renderInventory();
    });
    $('shop-toggle').addEventListener('click', openShop);
    $('shop-close').addEventListener('click', closeShop);
    $('shop-category').addEventListener('change', loadShop);
    $('shop-search').addEventListener('input', function () {
      state.shopQuery = $('shop-search').value;
      renderShop(state.shopItems || []);
    });
    $('shop-sort').addEventListener('change', function () {
      state.shopSort = $('shop-sort').value || 'default';
      saveSort('shop-sort', state.shopSort);
      renderShop(state.shopItems || []);
    });
    $('shop-fav-filter').addEventListener('click', function () {
      state.shopOnlyFavorites = !state.shopOnlyFavorites;
      saveSort('shop-favorites', state.shopOnlyFavorites ? '1' : '0');
      $('shop-fav-filter').classList.toggle('active', state.shopOnlyFavorites);
      renderShop(state.shopItems || []);
    });
    $('shop-modal').addEventListener('click', function (event) {
      if (event.target === $('shop-modal')) closeShop();
    });
    $('wallet-toggle').addEventListener('click', openWallet);
    $('wallet-close').addEventListener('click', closeWallet);
    $('wallet-export').addEventListener('click', exportWalletTransactions);
    $('wallet-modal').addEventListener('click', function (event) {
      if (event.target === $('wallet-modal')) closeWallet();
    });
    $('money-pill').addEventListener('click', openWallet);
    $('garage-toggle').addEventListener('click', openGarage);
    $('garage-close').addEventListener('click', closeGarage);
    $('garage-export').addEventListener('click', exportGarage);
    $('garage-modal').addEventListener('click', function (event) {
      if (event.target === $('garage-modal')) closeGarage();
    });
    $('garage-room').addEventListener('click', openGarage);
    $('garage-room').addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') openGarage();
    });
    $('vehicle-close').addEventListener('click', closeVehicle);
    $('vehicle-modal').addEventListener('click', function (event) {
      if (event.target === $('vehicle-modal')) closeVehicle();
    });
    $('vehicle-body').addEventListener('click', function (event) {
      var tab = event.target.closest('[data-vehicle-key]');
      if (tab) {
        state.vehicleKey = vehicleKeyFromCar(tab.getAttribute('data-vehicle-key'));
        renderVehicle();
        return;
      }
      var driver = event.target.closest('[data-vehicle-driver]');
      if (driver) {
        vehicleStart(driver.getAttribute('data-vehicle-driver'));
        return;
      }
      if (event.target.closest('#vehicle-return')) {
        vehicleReturn();
        return;
      }
      if (event.target.closest('#vehicle-refuel')) {
        vehicleRefuel();
        return;
      }
      if (event.target.closest('#vehicle-manage')) {
        closeVehicle();
        openGarage();
      }
    });
    $('system-toggle').addEventListener('click', openSystem);
    $('system-close').addEventListener('click', closeSystem);
    $('system-refresh').addEventListener('click', renderSystem);
    $('system-export').addEventListener('click', exportDiagnostics);
    $('system-reset-prefs').addEventListener('click', resetViewPreferences);
    $('system-backup').addEventListener('click', function () { backupAllData(false); });
    if ($('system-backup-safe')) $('system-backup-safe').addEventListener('click', function () { backupAllData(true); });
    $('system-restore').addEventListener('click', function () {
      $('backup-file').click();
    });
    $('backup-file').addEventListener('change', function () {
      restoreBackupFile($('backup-file').files && $('backup-file').files[0]);
      $('backup-file').value = '';
    });
    $('system-body').addEventListener('click', function (event) {
      var row = event.target.closest('[data-system-target]');
      if (!row) return;
      var target = $(row.getAttribute('data-system-target'));
      closeSystem();
      if (target) target.click();
    });
    $('system-modal').addEventListener('click', function (event) {
      if (event.target === $('system-modal')) closeSystem();
    });
    $('status-open').addEventListener('click', openStatus);
    $('status-close').addEventListener('click', closeStatus);
    $('status-modal').addEventListener('click', function (event) {
      if (event.target === $('status-modal')) closeStatus();
    });
    $('status-modal-body').addEventListener('click', function (event) {
      var activityRow = event.target.closest('[data-status-activity-kind]');
      if (activityRow) {
        var activityKind = activityRow.getAttribute('data-status-activity-kind');
        closeStatus();
        openActivityTarget(activityKind);
        return;
      }
      if (event.target.closest('[data-status-activity-refresh]')) {
        loadStatusActivity();
        return;
      }
      if (event.target.closest('[data-status-activity]')) {
        closeStatus();
        openActivity();
        return;
      }
      if (event.target.closest('[data-status-plan]')) {
        closeStatus();
        openDaySchedule();
        return;
      }
      if (event.target.closest('[data-status-wallet]')) {
        closeStatus();
        openWallet();
        return;
      }
      if (event.target.closest('[data-status-reading]')) {
        closeStatus();
        openInventory('bookshelf-section');
        return;
      }
      if (event.target.closest('[data-status-health]')) {
        closeStatus();
        openHealth();
        return;
      }
      if (event.target.closest('[data-status-outfit]')) {
        closeStatus();
        openOutfit();
        return;
      }
      if (event.target.closest('[data-status-travel]')) {
        closeStatus();
        openTrips();
        return;
      }
      if (event.target.closest('[data-status-world]')) {
        closeStatus();
        openMemory();
        return;
      }
      if (event.target.closest('[data-status-export]')) {
        exportStatusTrend();
        return;
      }
      var rangeButton = event.target.closest('[data-status-range]');
      if (rangeButton) {
        var pickedRange = Number(rangeButton.getAttribute('data-status-range'));
        state.statusTrendRange = [7, 14, 30].indexOf(pickedRange) >= 0
          ? pickedRange : 7;
        saveSort('status-trend-range', String(state.statusTrendRange));
        renderStatusModal();
        return;
      }
      var metric = event.target.closest('[data-status-metric]');
      if (metric) {
        state.statusTrendMetric = metric.getAttribute('data-status-metric') || 'mood';
        saveSort('status-trend-metric', state.statusTrendMetric);
        renderStatusModal();
        return;
      }
      var quick = event.target.closest('[data-status-target]');
      if (!quick) return;
      var target = $(quick.getAttribute('data-status-target'));
      closeStatus();
      if (target) target.click();
    });
    $('status-modal-body').addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var activityRow = event.target.closest('[data-status-activity-kind]');
      if (activityRow) {
        event.preventDefault();
        var activityKind = activityRow.getAttribute('data-status-activity-kind');
        closeStatus();
        openActivityTarget(activityKind);
        return;
      }
      if (event.target.closest('[data-status-activity-refresh]')) {
        event.preventDefault();
        loadStatusActivity();
        return;
      }
      if (event.target.closest('[data-status-activity]')) {
        event.preventDefault();
        closeStatus();
        openActivity();
        return;
      }
      if (event.target.closest('[data-status-plan]')) {
        event.preventDefault();
        closeStatus();
        openDaySchedule();
        return;
      }
      if (event.target.closest('[data-status-wallet]')) {
        event.preventDefault();
        closeStatus();
        openWallet();
        return;
      }
      if (event.target.closest('[data-status-reading]')) {
        event.preventDefault();
        closeStatus();
        openInventory('bookshelf-section');
        return;
      }
      if (event.target.closest('[data-status-health]')) {
        event.preventDefault();
        closeStatus();
        openHealth();
        return;
      }
      if (event.target.closest('[data-status-outfit]')) {
        event.preventDefault();
        closeStatus();
        openOutfit();
        return;
      }
      if (event.target.closest('[data-status-travel]')) {
        event.preventDefault();
        closeStatus();
        openTrips();
        return;
      }
      if (event.target.closest('[data-status-world]')) {
        event.preventDefault();
        closeStatus();
        openMemory();
      }
    });
    $('menu-toggle').addEventListener('click', openFunctionMenu);
    $('function-close').addEventListener('click', closeFunctionMenu);
    $('function-menu').addEventListener('click', function (event) {
      if (event.target === $('function-menu')) closeFunctionMenu();
    });
    $('integrations-open').addEventListener('click', openIntegrations);
    $('integration-close').addEventListener('click', closeIntegrations);
    $('integration-refresh').addEventListener('click', loadIntegrations);
    $('integration-modal').addEventListener('click', function (event) {
      if (event.target === $('integration-modal')) closeIntegrations();
    });
    document.querySelectorAll('[data-menu-target]').forEach(function (button) {
      button.addEventListener('click', function () {
        var target = $(button.getAttribute('data-menu-target'));
        closeFunctionMenu();
        if (target) target.click();
      });
    });
    $('diary-toggle').addEventListener('click', openDiary);
    $('diary-close').addEventListener('click', closeDiary);
    $('diary-export').addEventListener('click', exportDiary);
    $('diary-search').addEventListener('input', function () {
      state.diaryQuery = $('diary-search').value;
      renderDiaryList();
    });
    document.querySelectorAll('[data-diary-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.diaryFilter = button.getAttribute('data-diary-filter') || 'all';
        saveSort('diary-filter', state.diaryFilter);
        document.querySelectorAll('[data-diary-filter]').forEach(function (item) {
          item.classList.toggle(
            'active',
            item.getAttribute('data-diary-filter') === state.diaryFilter
          );
        });
        renderDiaryList();
      });
    });
    $('diary-modal').addEventListener('click', function (event) {
      if (event.target === $('diary-modal')) closeDiary();
    });
    $('memory-toggle').addEventListener('click', openMemory);
    $('memory-close').addEventListener('click', closeMemory);
    $('memory-modal').addEventListener('click', function (event) {
      if (event.target === $('memory-modal')) closeMemory();
    });
    $('weekly-toggle').addEventListener('click', openWeekly);
    $('weekly-close').addEventListener('click', closeWeekly);
    $('weekly-export').addEventListener('click', exportWeekly);
    $('weekly-export-chart').addEventListener('click', exportWeeklyChart);
    $('weekly-modal').addEventListener('click', function (event) {
      if (event.target === $('weekly-modal')) closeWeekly();
    });
    document.querySelectorAll('[data-weekly-days]').forEach(function (button) {
      button.addEventListener('click', function () {
        setWeeklyRange(button.getAttribute('data-weekly-days'));
      });
    });
    document.querySelectorAll('[data-weekly-metric]').forEach(function (button) {
      button.addEventListener('click', function () {
        setWeeklyMetric(button.getAttribute('data-weekly-metric'));
      });
    });
    document.querySelectorAll('[data-chart-theme]').forEach(function (button) {
      button.addEventListener('click', function () {
        setWeeklyChartTheme(button.getAttribute('data-chart-theme'));
      });
    });
    $('affection-pill').addEventListener('click', openRelations);
    $('relations-close').addEventListener('click', closeRelations);
    $('relations-modal').addEventListener('click', function (event) {
      if (event.target === $('relations-modal')) closeRelations();
    });
    $('book-close').addEventListener('click', closeBook);
    $('book-font-up').addEventListener('click', function () { changeBookFont(0.1); });
    $('book-font-down').addEventListener('click', function () { changeBookFont(-0.1); });
    $('book-theme').addEventListener('click', cycleBookTheme);
    $('book-prev').addEventListener('click', function () { changeBookChapter(-1); });
    $('book-chapter-select').addEventListener('change', function () {
      var chapter = Number($('book-chapter-select').value) || 1;
      if (state.bookId) openBook(state.bookId, chapter);
    });
    $('book-next').addEventListener('click', function () { changeBookChapter(1); });
    document.addEventListener('keydown', function (event) {
      if ($('book-modal').classList.contains('hidden') || !state.bookId) return;
      var tag = String((event.target && event.target.tagName) || '').toLowerCase();
      if (['input', 'textarea', 'select'].indexOf(tag) >= 0) return;
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        changeBookChapter(-1);
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        changeBookChapter(1);
      }
    });
    $('book-bookmark-save').addEventListener('click', saveBookBookmark);
    $('book-bookmark-restore').addEventListener('click', restoreBookBookmark);
    $('book-note-save').addEventListener('click', saveBookNote);
    $('book-note-export').addEventListener('click', exportBookNotes);
    $('book-note-search').addEventListener('input', function () {
      state.bookNoteQuery = $('book-note-search').value;
      renderBookNotes();
    });
    $('book-modal').addEventListener('click', function (event) {
      if (event.target === $('book-modal')) closeBook();
    });
    $('inventory-modal').addEventListener('click', function (event) {
      if (event.target === $('inventory-modal')) closeInventory();
    });
    $('photo-again').addEventListener('click', function () {
      closePhotoModal();
      enterCameraMode();
    });
    $('home-stage').addEventListener('click', onCameraStageClick, true);
    $('scene-stage').addEventListener('click', function (event) {
      var toggle = event.target.closest('[data-scene-mode]');
      if (!toggle) return;
      event.preventDefault();
      state.indoorView = toggle.getAttribute('data-scene-mode') === 'indoor';
      renderScene(true);
      flashSceneMode(state.indoorView ? '进入室内' : '回到室外');
    }, true);
    $('scene-stage').addEventListener('click', onPlacementStageClick, true);
    $('scene-stage').addEventListener('pointerdown', onDecorPointerDown, true);
    $('scene-stage').addEventListener('pointermove', onDecorPointerMove, true);
    $('scene-stage').addEventListener('pointerup', onDecorPointerUp, true);
    $('scene-stage').addEventListener('pointercancel', onDecorPointerUp, true);
    $('scene-stage').addEventListener('click', onCameraStageClick, true);
    document.addEventListener('keydown', function (event) {
      if (
        (event.key === 'ArrowLeft' || event.key === 'ArrowRight') &&
        !$('photo-modal').classList.contains('hidden') &&
        (state.photos || []).length > 1
      ) {
        event.preventDefault();
        var current = Number(state.photoIndex);
        if (!isFinite(current) || current < 0) current = 0;
        showPhotoAt(current + (event.key === 'ArrowLeft' ? -1 : 1));
        return;
      }
      if (event.key !== 'Escape') return;
      if (!$('cook-modal').classList.contains('hidden')) closeCookModal();
      if (!$('photo-modal').classList.contains('hidden')) closePhotoModal();
      if (!$('item-popover').classList.contains('hidden')) closeItem();
      if (!$('item-drawer').classList.contains('hidden')) toggleItemDrawer(false);
      if (!$('inventory-modal').classList.contains('hidden')) closeInventory();
      if (!$('shop-modal').classList.contains('hidden')) closeShop();
      if (!$('wallet-modal').classList.contains('hidden')) closeWallet();
      if (!$('diary-modal').classList.contains('hidden')) closeDiary();
      if (!$('weekly-modal').classList.contains('hidden')) closeWeekly();
      if (!$('trips-modal').classList.contains('hidden')) closeTrips();
      if (!$('outfit-modal').classList.contains('hidden')) closeOutfit();
      if (!$('health-modal').classList.contains('hidden')) closeHealth();
      if (!$('activity-modal').classList.contains('hidden')) closeActivity();
      if (!$('relations-modal').classList.contains('hidden')) closeRelations();
      if (!$('memory-modal').classList.contains('hidden')) closeMemory();
      if (!$('garage-modal').classList.contains('hidden')) closeGarage();
      if (!$('vehicle-modal').classList.contains('hidden')) closeVehicle();
      if (!$('system-modal').classList.contains('hidden')) closeSystem();
      if (!$('book-modal').classList.contains('hidden')) closeBook();
      if (!$('game-modal').classList.contains('hidden')) closeGameModal();
      if (!$('status-modal').classList.contains('hidden')) closeStatus();
      if (!$('integration-modal').classList.contains('hidden')) closeIntegrations();
      if (!$('schedule-modal').classList.contains('hidden')) closeScheduleDetail();
      if (!$('wish-modal').classList.contains('hidden')) closeWishes();
      if (!$('function-menu').classList.contains('hidden')) closeFunctionMenu();
      if (cameraMode) exitCameraMode();
    });
    fetchHomeItems();
    fetchWishes();
    if (pageParams.get('items') === '1') toggleItemDrawer(true);
    fetchState();
    setInterval(function () {
      if (!document.hidden) fetchState();
    }, 2000);
    setInterval(updateClock, 1000);
  }

  function applyAnimations() {
    document.body.classList.toggle('no-anim', !state.animations);
    var button = $('anim-toggle');
    if (button) {
      button.textContent = state.animations ? '动画：开' : '动画：关';
      button.setAttribute('aria-pressed', state.animations ? 'true' : 'false');
      button.title = '开启或关闭人物行走、路景滚动与天气动画';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
