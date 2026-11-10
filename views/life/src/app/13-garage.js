  function openGarage() {
    $('garage-modal').classList.remove('hidden');
    loadGarage();
  }

  function closeGarage() {
    $('garage-modal').classList.add('hidden');
  }

  var VEHICLE_CARS = {
    jeep: { key: 'jeep', id: 'car_jeep', bay: 'A1', name: '吉普', type: 'jeep', paint: '#6f7f5c', plate: '沪A·J4X4' },
    white: { key: 'white', id: 'car_white', bay: 'A2', name: '白色小车', type: 'sedan', paint: '#eef2ef', plate: '沪A·M320' },
    sports: { key: 'sports', id: 'car_sports', bay: 'A3', name: '跑车', type: 'sports', paint: '#c8423a', plate: '沪A·GT886' }
  };

  function vehicleKeyFromCar(value) {
    var text = String(value || '').trim();
    if (text === 'home' || text === 'home_car' || text === 'white' || text === 'sedan') return 'white';
    if (text === 'jeep' || text === 'garage_jeep') return 'jeep';
    if (text === 'sports' || text === 'garage_sports') return 'sports';
    return 'white';
  }

  function vehicleGarageData() {
    return state.garageData || (state.data && state.data.garage) || {};
  }

  function openVehicle(key) {
    state.vehicleKey = vehicleKeyFromCar(key || state.vehicleKey || 'white');
    $('vehicle-modal').classList.remove('hidden');
    renderVehicle();
  }

  function closeVehicle() {
    $('vehicle-modal').classList.add('hidden');
  }

  function renderVehicle() {
    var body = $('vehicle-body');
    if (!body) return;
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var garage = vehicleGarageData();
    var list = garage.vehicles || [];
    var staticInfo = VEHICLE_CARS[key];
    var live = list.find(function (item) {
      return item && String(item.id) === staticInfo.id;
    }) || (key === 'white' ? (garage.vehicle || {}) : {});
    var info = {
      key: key,
      id: staticInfo.id,
      bay: staticInfo.bay,
      name: String(live.name || staticInfo.name),
      type: staticInfo.type,
      paint: staticInfo.paint,
      plate: String(live.plate || staticInfo.plate)
    };
    var isOut = live.status === 'out';
    var fuel = Number(live.fuel || 0);
    var trip = live.trip || (key === 'white' ? (garage.trip || {}) : {});
    var art = (window.VehicleArt && VehicleArt.preview)
      ? VehicleArt.preview(info.type, info.paint, info.name)
      : '';
    var tabs = ['jeep', 'white', 'sports'].map(function (carKey) {
      var car = VEHICLE_CARS[carKey];
      var tabLive = list.find(function (item) {
        return item && String(item.id) === car.id;
      }) || {};
      var tabState = tabLive.status === 'out' ? '出车中' : '在库';
      return '<button type="button" class="vehicle-tab' + (carKey === key ? ' active' : '') +
        '" data-vehicle-key="' + carKey + '"><b>' + escapeHtml(car.bay) + ' · ' +
        escapeHtml(car.name) + '</b><small>' + escapeHtml(tabState) + ' · ' +
        escapeHtml(car.plate) + '</small></button>';
    }).join('');
    var status = isOut
      ? ('出车中 · ' + escapeHtml(trip.destination || ''))
      : '已停好';
    var html = '<div class="vehicle-tabs">' + tabs + '</div>' +
      '<div class="vehicle-hero">' + art + '</div>' +
      '<div class="vehicle-meta"><div><h4>' + escapeHtml(info.name) + '</h4>' +
      '<small>' + escapeHtml(info.bay) + ' 车位 · ' + status + '</small></div>' +
      '<span class="vehicle-plate">' + escapeHtml(info.plate) + '</span></div>' +
      '<div class="vehicle-fuel">油量 ' + fuel + '%' +
      '<div class="vehicle-fuel-bar"><span style="width:' + Math.max(0, Math.min(100, fuel)) + '%"></span></div></div>';
    if (isOut) {
      var percent = trip && trip.started_at ? garageTripPercent(trip) : 0;
      html += '<div class="garage-trip"><h4>正在路上</h4><p><b>' +
        escapeHtml(trip.driver === 'master' ? '主人开车' : '月月载你') + '</b> · ' +
        escapeHtml(trip.destination || '') + '</p><small>出发 ' +
        escapeHtml(garageTime(trip.started_at)) + ' · 预计 ' +
        escapeHtml(garageTime(trip.eta)) + ' 回来 · ' +
        escapeHtml(garageEtaText(trip.eta) || '') + '</small>' +
        '<div class="garage-trip-progress"><span style="width:' + percent + '%"></span></div>' +
        '<small>行程进度 ' + percent + '%</small>' +
        '<button type="button" class="ghost-btn" id="vehicle-return">已经回来了</button></div>';
    } else {
      var destinations = garage.destinations || [];
      html += '<div class="garage-choice"><label>去哪里</label><select id="vehicle-destination">' +
        destinations.map(function (destination) {
          return '<option value="' + escapeHtml(destination) + '">' + escapeHtml(destination) + '</option>';
        }).join('') + '</select><div class="garage-actions">' +
        '<button type="button" class="ghost-btn" data-vehicle-driver="master">我带她出去</button>' +
        '<button type="button" class="ghost-btn" data-vehicle-driver="self">让她载我出去</button>' +
        '</div></div>';
      if (fuel < 100) {
        html += '<div class="vehicle-actions"><button type="button" class="ghost-btn" id="vehicle-refuel">加油 ' +
          Number(garage.refuel_cost || 60) + ' 元</button></div>';
      }
      if (key === 'white') {
        html += '<div class="vehicle-actions"><button type="button" class="ghost-btn" id="vehicle-manage">打开车库管理</button></div>';
      }
    }
    body.innerHTML = html;
  }

  function vehicleRefresh(result, message) {
    if (result && result.garage) state.garageData = result.garage;
    if (message) showToast(message);
    renderVehicle();
    fetchState();
  }

  function vehicleStart(driver) {
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var info = VEHICLE_CARS[key];
    var select = $('vehicle-destination');
    var destination = select ? select.value : '';
    if (!destination) {
      showToast('先选一个目的地');
      return;
    }
    fetch('/api/garage/drive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona: garagePersona(),
        destination: destination,
        driver: driver,
        vehicle_id: info.id
      })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '开不出去');
        vehicleRefresh(data, info.name + '出发去' + destination);
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '开不出去');
      });
  }

  function vehicleReturn() {
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var info = VEHICLE_CARS[key];
    fetch('/api/garage/return', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona(), vehicle_id: info.id })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '车还没回来');
        vehicleRefresh(data, info.name + '已回库');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '车还没回来');
      });
  }

  function vehicleRefuel() {
    var key = vehicleKeyFromCar(state.vehicleKey || 'white');
    var info = VEHICLE_CARS[key];
    fetch('/api/garage/refuel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona(), vehicle_id: info.id })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '加不了油');
        vehicleRefresh(data, info.name + '已加满油');
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '加不了油');
      });
  }

  function garagePersona() {
    return (state.data && state.data.persona) || '';
  }

  function garageTime(value) {
    var text = String(value || '');
    return text.length >= 16 ? text.slice(11, 16) : text;
  }

  function garageEtaText(value) {
    var target = new Date(String(value || '')).getTime();
    if (!isFinite(target)) return '';
    var minutes = Math.round((target - Date.now()) / 60000);
    if (minutes <= 0) return '马上回来';
    if (minutes < 60) return '约 ' + minutes + ' 分钟后回来';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return '约 ' + hours + ' 小时' + (rest ? ' ' + rest + ' 分钟' : '') + '后回来';
  }

  function loadGarage() {
    var body = $('garage-body');
    body.innerHTML = '<p class="inventory-empty">正在开车库门...</p>';
    fetch('/api/garage?persona=' + encodeURIComponent(garagePersona()), {
      cache: 'no-store'
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '车库打不开');
        state.garageData = data.garage || {};
        renderGarage(data.garage || {});
      })
      .catch(function (error) {
        body.innerHTML = '<p class="inventory-empty">' +
          escapeHtml(error && error.message ? error.message : '车库打不开') +
          '</p>';
      });
  }

  function exportGarage() {
    var garage = state.garageData || {};
    var vehicle = garage.vehicle || {};
    if (!vehicle.name && !(garage.history || []).length) {
      showToast('车库数据还没加载好');
      return;
    }
    var filter = state.garageHistoryFilter || 'all';
    var filterLabels = { all: '全部', returned: '已回家', active: '在路上' };
    var history = (garage.history || []).filter(function (item) {
      if (filter === 'returned') return item.status === 'returned';
      if (filter === 'active') return item.status !== 'returned';
      return true;
    });
    var lines = ['记录类型,目的地或项目,状态,时间'];
    lines.push([
      '车辆', csvCell(vehicle.name || '白色小车'),
      csvCell(vehicle.status === 'out' ? '出车中' : '已停好'),
      '油量 ' + Number(vehicle.fuel || 0) + '%'
    ].join(','));
    history.forEach(function (item) {
      lines.push([
        '出车',
        csvCell(item.destination || ''),
        csvCell(item.status === 'returned' ? '已回家' : '在路上'),
        csvCell(String(item.started_at || '').replace('T', ' ').slice(0, 16))
      ].join(','));
    });
    var day = new Date().toISOString().slice(0, 10);
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], {
      type: 'text/csv;charset=utf-8'
    });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = '车库记录-' + day +
      (filter === 'all' ? '' : '-' + filterLabels[filter]) + '.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    showToast('车库记录已导出');
  }

  function garageTripPercent(trip) {
    var start = new Date(trip.started_at || '').getTime();
    var eta = new Date(trip.eta || '').getTime();
    if (!start || !eta || eta <= start) return 0;
    var percent = (Date.now() - start) / (eta - start) * 100;
    return Math.max(0, Math.min(100, Math.round(percent)));
  }

  // 3D garage at the top of the garage panel; falls back to the 2D strip artwork when WebGL is unavailable.
  function garage3dMarkup(isOut, vehicle, fuel) {
    var art = document.querySelector('#garage-room .garage-room-art');
    var fallback = art ? '<div class="garage-3d-fallback">' + art.outerHTML.replace(/ id="[^"]*"/g, '') + '</div>' : '';
    if (!use3D() || !window.Room3D || !Room3D.destinationMarkup || !Room3D.supportsDestination('garage', 'indoor')) return fallback;
    var status = isOut ? '车不在' : ((vehicle.name || '白色小车') + ' · 油量 ' + fuel + '%');
    var labelHtml = '<div class="scene-label">1F · 车库<small>' + escapeHtml(status) + '</small></div>';
    var mode = (isOut ? 'out' : 'parked') + (vehicle.plate ? '|' + String(vehicle.plate).replace(/\|/g, '') : '');
    return '<div class="garage-3d">' + Room3D.destinationMarkup({ key: 'garage', view: 'indoor', mode: mode, env: sceneEnvironment(), labelHtml: labelHtml, fallback: fallback, look: { none: true } }) + '</div>';
  }

  function renderGarage(garage) {
    var body = $('garage-body');
    var vehicle = garage.vehicle || {};
    var trip = garage.trip || {};
    var destinations = garage.destinations || [];
    var history = garage.history || [];
    var isOut = vehicle.status === 'out';
    var fuel = Number(vehicle.fuel || 0);
    var refuelButton = (!isOut && fuel < 100)
      ? '<button type="button" class="garage-refuel" id="garage-refuel">加油 ' +
        Number(garage.refuel_cost || 60) + ' 元</button>'
      : '';
    var fuelWarning = fuel <= 20
      ? '<small class="garage-fuel-warning">油量偏低，记得加油</small>'
      : '';
    var html = garage3dMarkup(isOut, vehicle, fuel) +
      '<div class="garage-car ' + (isOut ? 'is-out' : '') + '">' +
      '<div class="garage-car-icon">' + VehicleArt.preview() + '</div>' +
      '<div class="garage-car-copy"><b>' + escapeHtml(vehicle.name || '白色小车') +
      '</b><span>' + escapeHtml(vehicle.plate || '') +
      ' · 油量 ' + fuel + '%</span>' +
      '<div class="garage-fuel-bar"><span style="width:' + fuel + '%"></span></div>' +
      '<small>' + (isOut ? '不在车库' : '已停好') + '</small>' +
      fuelWarning +
      refuelButton + '</div></div>' +
      '<div class="garage-destination-preview" id="garage-destination-preview"></div>';
    if (isOut && trip) {
      var driver = trip.driver === 'master' ? '主人开车' : '月月载你';
      var tripPercent = garageTripPercent(trip);
      html += '<div class="garage-trip"><h4>正在路上</h4>' +
        '<p><b>' + escapeHtml(driver) + '</b> · ' +
        escapeHtml(trip.destination || '') + '</p>' +
        '<small>出发 ' + escapeHtml(garageTime(trip.started_at)) +
        ' · 预计 ' + escapeHtml(garageTime(trip.eta)) + ' 回来 · ' +
        escapeHtml(garageEtaText(trip.eta) || '') + '</small>' +
        '<div class="garage-trip-progress"><span style="width:' +
        tripPercent + '%"></span></div>' +
        '<small>行程进度 ' + tripPercent + '%</small>' +
        '<button type="button" class="ghost-btn" id="garage-return">已经回来了</button>' +
        '</div>';
    } else {
      html += '<div class="garage-choice"><label>去哪里</label>' +
        '<select id="garage-destination">' +
        destinations.map(function (destination) {
          return '<option value="' + escapeHtml(destination) + '">' +
            escapeHtml(destination) + '</option>';
        }).join('') +
        '</select>' +
        '<div class="garage-actions">' +
        '<button type="button" class="ghost-btn" data-garage-driver="master">我带她出去</button>' +
        '<button type="button" class="ghost-btn" data-garage-driver="self">让她载我出去</button>' +
        '</div></div>';
    }
    if (history.length) {
      var garageHistoryFilter = state.garageHistoryFilter || 'all';
      var filteredHistory = history.filter(function (item) {
        if (garageHistoryFilter === 'returned') return item.status === 'returned';
        if (garageHistoryFilter === 'active') return item.status !== 'returned';
        return true;
      });
      var shownHistory = state.garageHistoryExpanded
        ? filteredHistory
        : filteredHistory.slice(0, 5);
      var garageReturnedCount = history.filter(function (item) {
        return item.status === 'returned';
      }).length;
      var garageFilterCounts = {
        all: history.length,
        returned: garageReturnedCount,
        active: Math.max(0, history.length - garageReturnedCount)
      };
      html += '<div class="garage-history"><h4>最近出车</h4>' +
        '<div class="garage-history-filters">' + [
          ['all', '全部'], ['returned', '已回家'], ['active', '在路上']
        ].map(function (item) {
          return '<button type="button" data-garage-history-filter="' + item[0] + '"' +
            (garageHistoryFilter === item[0] ? ' class="active"' : '') + '>' +
            item[1] + ' <b>' + garageFilterCounts[item[0]] + '</b></button>';
        }).join('') + '</div>';
      if (!shownHistory.length) {
        html += '<p class="inventory-empty">这个分类下还没有出车记录。</p>';
      }
      shownHistory.forEach(function (item) {
        html += '<div class="garage-history-item"><span>' +
          escapeHtml(garageTime(item.started_at)) + '</span><b>' +
          escapeHtml(item.destination || '') + '</b><small>' +
          (item.driver === 'master' ? '主人带' : '自己开') +
          (item.status === 'returned' ? ' · 已回家' : ' · 在路上') +
          '</small></div>';
      });
      if (history.length > 5) {
        html += '<button type="button" class="garage-history-toggle" ' +
          'id="garage-history-toggle">' +
          (state.garageHistoryExpanded
            ? '收起记录'
            : '查看全部 ' + filteredHistory.length + ' 条') +
          '</button>';
      }
      html += '</div>';
    }
    body.innerHTML = html;
    if (isOut) {
      renderGarageDestinationPreview(trip.destination || '');
    } else {
      var select = $('garage-destination');
      if (select) {
        renderGarageDestinationPreview(select.value);
        select.addEventListener('change', function () {
          renderGarageDestinationPreview(select.value);
        });
      }
    }
    body.querySelectorAll('[data-garage-driver]').forEach(function (button) {
      button.addEventListener('click', function () {
        startGarageTrip(button.getAttribute('data-garage-driver'));
      });
    });
    var returnButton = $('garage-return');
    if (returnButton) {
      returnButton.addEventListener('click', returnGarage);
    }
    var refuelButtonEl = $('garage-refuel');
    if (refuelButtonEl) {
      refuelButtonEl.addEventListener('click', refuelGarage);
    }
    var historyToggle = $('garage-history-toggle');
    if (historyToggle) {
      historyToggle.addEventListener('click', function () {
        state.garageHistoryExpanded = !state.garageHistoryExpanded;
        renderGarage(garage);
      });
    }
    body.querySelectorAll('[data-garage-history-filter]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.garageHistoryFilter =
          button.getAttribute('data-garage-history-filter') || 'all';
        saveSort('garage-history-filter', state.garageHistoryFilter);
        renderGarage(garage);
      });
    });
  }

  function renderGarageDestinationPreview(destination) {
    var box = $('garage-destination-preview');
    if (!box) return;
    if (!destination) {
      box.innerHTML = '';
      return;
    }
    if (!window.GarageDestinations) {
      box.innerHTML = '<p class="inventory-empty">地点内部造型加载中...</p>';
      return;
    }
    if (!GarageDestinations.hasInterior(destination)) {
      box.innerHTML = '<div class="garage-destination-fallback">' +
        escapeHtml(destination) + ' 是户外地点，没有室内场景。</div>';
      return;
    }
    var description = GarageDestinations.description(destination) || '';
    box.innerHTML = '<div class="garage-destination-label"><b>' +
      escapeHtml(destination) + '</b><small>地点内部</small></div>' +
      GarageDestinations.interior(destination) +
      (description
        ? '<p class="garage-destination-desc">' + escapeHtml(description) + '</p>'
        : '');
  }

  function refuelGarage() {
    var button = $('garage-refuel');
    if (button) {
      button.disabled = true;
      button.textContent = '加油中...';
    }
    fetch('/api/garage/refuel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: garagePersona() })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '加不了油');
        showToast('车已加满油');
        renderGarage(data.garage || {});
        fetchState();
      })
      .catch(function (error) {
        showToast(error && error.message ? error.message : '加不了油');
        if (button) {
          button.disabled = false;
          button.textContent = '加油';
        }
      });
  }

