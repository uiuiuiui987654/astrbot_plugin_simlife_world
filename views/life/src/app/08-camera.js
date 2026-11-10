  // ---------------------------------------------------------------- 观察窗相机
  var cameraMode = false;

  function enterCameraMode() {
    cameraMode = true;
    closeItem();
    $('camera-target').textContent = '取景：点击画面选择目标';
    $('camera-overlay').classList.remove('hidden');
    showToast('点击画面里的月月 / 家具 / 房间来取景');
  }

  function exitCameraMode() {
    cameraMode = false;
    $('camera-overlay').classList.add('hidden');
  }

  function onCameraStageClick(event) {
    if (!cameraMode) return;
    event.preventDefault();
    event.stopPropagation();
    var room3d = event.target.closest('.bedroom-3d');
    if (room3d && event.target.closest('.bedroom-3d-viewport') && window.Bedroom3D) {
      var engine = Bedroom3D.instances.get(room3d);
      var picked = engine && engine.pick(event);
      if (picked === 'character') takeCameraPhoto({ target: 'character' }, '拍一张月月');
      else if (picked) takeCameraPhoto({ target: 'item', item_id: picked }, '拍一件家具');
      else takeCameraPhoto({ target: 'room' }, '拍下这个房间');
      return;
    }
    var character = event.target.closest('.character-marker');
    if (character) {
      takeCameraPhoto({ target: 'character' }, '拍一张月月');
      return;
    }
    var hit = event.target.closest('.furniture-hit');
    if (hit) {
      takeCameraPhoto(
        { target: 'item', item_id: hit.getAttribute('data-id') },
        '拍一件家具'
      );
      return;
    }
    takeCameraPhoto({ target: 'room' }, '拍下这个房间');
  }

  function onCameraHover(event) {
    if (!cameraMode || !event.target || !event.target.closest) return;
    var label = '当前房间';
    if (event.target.closest('.character-marker')) {
      label = '月月';
    } else {
      var hit = event.target.closest('.furniture-hit');
      if (hit) {
        var id = hit.getAttribute('data-id');
        var items = state.homeItems || [];
        for (var i = 0; i < items.length; i++) {
          if (String(items[i].id) === String(id)) {
            label = items[i].name || id;
            break;
          }
        }
        if (label === '当前房间') label = id;
      }
    }
    var node = $('camera-target');
    if (node) node.textContent = '取景：' + label;
  }

  function loadStoredPhotos() {
    try {
      var parsed = JSON.parse(localStorage.getItem('vl-photo-gallery') || '[]');
      return Array.isArray(parsed)
        ? parsed.filter(function (item) {
            return item && typeof item.src === 'string' && item.src;
          }).slice(-6)
        : [];
    } catch (error) {
      return [];
    }
  }

  function persistPhotos(photos) {
    var chosen = [];
    var total = 0;
    for (var index = (photos || []).length - 1; index >= 0; index -= 1) {
      var item = photos[index];
      if (!item || !item.src) continue;
      var serialized = JSON.stringify(item);
      if (total + serialized.length > 2400000) break;
      chosen.unshift(item);
      total += serialized.length;
    }
    try {
      localStorage.setItem('vl-photo-gallery', JSON.stringify(chosen));
    } catch (error) {
      /* 本地空间不足时仅保留当前会话照片 */
    }
  }

  function photoTimeText(value) {
    var text = String(value || '');
    if (!text) return '';
    return text.slice(5, 16).replace('T', ' ');
  }

  function showPhotoAt(index) {
    var photos = state.photos || [];
    if (!photos.length) return;
    var next = ((Number(index) || 0) % photos.length + photos.length) % photos.length;
    state.photoIndex = next;
    var photo = photos[next];
    if (!photo) return;
    $('photo-image').src = photo.src;
    $('photo-image').classList.remove('hidden');
    $('photo-loading').classList.add('hidden');
    var takenAt = photoTimeText(photo.at);
    $('photo-caption').textContent = ((photo.caption || '') +
      (takenAt ? ' · ' + takenAt : '')).trim();
    var gallery = $('photo-gallery');
    if (gallery) {
      gallery.querySelectorAll('[data-photo-index]').forEach(function (button) {
        button.classList.toggle(
          'active',
          Number(button.getAttribute('data-photo-index')) === next
        );
      });
    }
  }

  function renderPhotoGallery() {
    var gallery = $('photo-gallery');
    if (!gallery) return;
    var photos = state.photos || [];
    if (!photos.length) {
      gallery.innerHTML = '';
      return;
    }
    gallery.innerHTML = '<div class="photo-gallery-head">' +
      '<span class="photo-gallery-label">最近照片</span>' +
      '<button type="button" class="photo-gallery-clear" id="photo-gallery-clear">清空</button>' +
      '</div>' +
      photos.map(function (photo, index) {
        return '<span class="photo-thumb-wrap">' +
          '<button type="button" class="photo-thumb" data-photo-index="' +
          index + '" title="' + escapeHtml(photoTimeText(photo.at)) +
          '"><img src="' + escapeHtml(photo.src) + '" alt="照片 ' +
          (index + 1) + '"></button>' +
          '<button type="button" class="photo-thumb-delete" data-photo-delete="' +
          index + '" aria-label="删除这张照片" title="删除这张照片">×</button>' +
          '</span>';
      }).join('');
    gallery.querySelectorAll('[data-photo-index]').forEach(function (button) {
      button.addEventListener('click', function () {
        showPhotoAt(Number(button.getAttribute('data-photo-index')));
      });
    });
    gallery.querySelectorAll('[data-photo-delete]').forEach(function (button) {
      button.addEventListener('click', function () {
        var index = Number(button.getAttribute('data-photo-delete'));
        state.photos.splice(index, 1);
        if (state.photoIndex >= state.photos.length) {
          state.photoIndex = state.photos.length - 1;
        }
        persistPhotos(state.photos);
        if (!state.photos.length) {
          state.photoIndex = -1;
          $('photo-image').classList.add('hidden');
          $('photo-image').removeAttribute('src');
          $('photo-caption').textContent = '';
          $('photo-loading').classList.add('hidden');
        } else {
          showPhotoAt(Math.min(index, state.photos.length - 1));
        }
        renderPhotoGallery();
        showToast('已删除这张照片');
      });
    });
    var clearButton = $('photo-gallery-clear');
    if (clearButton) {
      clearButton.addEventListener('click', function () {
        state.photos = [];
        try {
          localStorage.removeItem('vl-photo-gallery');
        } catch (error) {
          /* 忽略本地存储异常 */
        }
        state.photoIndex = -1;
        $('photo-image').classList.add('hidden');
        $('photo-image').removeAttribute('src');
        $('photo-caption').textContent = '';
        $('photo-loading').classList.add('hidden');
        renderPhotoGallery();
        showToast('最近照片已清空');
      });
    }
  }

  function takeCameraPhoto(payload, label) {
    exitCameraMode();
    payload.persona = state.persona || '';
    $('photo-modal').classList.remove('hidden');
    $('photo-image').classList.add('hidden');
    $('photo-image').removeAttribute('src');
    renderPhotoGallery();
    $('photo-loading').classList.remove('hidden');
    $('photo-loading').textContent = '显影中...（大约 20-60 秒）';
    $('photo-caption').textContent = label || '';
    $('photo-image').onerror = function () {
      this.classList.add('hidden');
      $('photo-loading').classList.remove('hidden');
      $('photo-loading').textContent = '图片加载失败，请再试一次';
    };
    fetch('/api/camera/photo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '拍照失败');
        $('photo-loading').classList.add('hidden');
        $('photo-image').src = data.image;
        $('photo-image').classList.remove('hidden');
        $('photo-caption').textContent = data.caption || label || '';
        state.photos = (state.photos || []).concat([{
          src: data.image,
          caption: data.caption || label || '',
          at: new Date().toISOString()
        }]).slice(-6);
        state.photoIndex = state.photos.length - 1;
        persistPhotos(state.photos);
        renderPhotoGallery();
      })
      .catch(function (error) {
        $('photo-loading').classList.remove('hidden');
        $('photo-loading').textContent = '没拍成：' + error.message;
      });
  }

  function saveCameraPhoto() {
    var image = $('photo-image');
    if (!image || image.classList.contains('hidden') || !image.getAttribute('src')) {
      showToast('还没有照片可保存');
      return;
    }
    var src = image.getAttribute('src');
    var extension = src.indexOf('image/jpeg') >= 0 ? 'jpg' : 'png';
    var day = new Date().toISOString().slice(0, 10);
    var link = document.createElement('a');
    link.href = src;
    link.download = '虚拟人生-拍立得-' + day + '.' + extension;
    document.body.appendChild(link);
    link.click();
    link.remove();
    showToast('照片已保存');
  }

  function closePhotoModal() {
    $('photo-modal').classList.add('hidden');
  }

