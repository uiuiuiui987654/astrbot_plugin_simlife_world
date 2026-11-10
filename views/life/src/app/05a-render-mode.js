  // ---------------------------------------------------------------------------
  // 画面模式（性能模式）：自动 / 3D / 2D
  //
  // 3D 场景脚本（room-3d-models、room-3d-atmosphere、room-3d-outdoor、destination-3d、
  // bedroom-3d，合计约 0.5 MB，另需约 2 MB 的 three.js）不再随页面一起加载。index.html
  // 里把它们写成 <script type="text/x-lazy-3d" data-src="…">，只有需要 3D 时才按顺序注入。
  //
  // “自动”在以下情况默认用 2D：浏览器不支持 WebGL、开启了省流量、内存 ≤ 4 GB、
  // CPU ≤ 4 核，或面板不是在本机 / 局域网打开（远程访问时加载 3D 资源很慢）。
  // 选择保存在 localStorage 的 vl-render 中。
  // ---------------------------------------------------------------------------
  var RENDER_MODES = ['auto', '3d', '2d'];
  var RENDER_MODE_LABEL = { auto: '自动', '3d': '3D', '2d': '2D' };
  var lazy3d = { promise: null, ready: false, failed: false };

  function storedRenderMode() {
    try {
      var value = localStorage.getItem('vl-render');
      return RENDER_MODES.indexOf(value) >= 0 ? value : 'auto';
    } catch (error) {
      return 'auto';
    }
  }

  function webglAvailable() {
    try {
      var canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl2') || canvas.getContext('webgl')));
    } catch (error) {
      return false;
    }
  }

  function isLocalHost(hostname) {
    var host = String(hostname || '').toLowerCase().replace(/^\[|\]$/g, '');
    if (!host || host === 'localhost' || host === '::1' || /\.local$/.test(host)) return true;
    if (/^127\./.test(host) || /^10\./.test(host) || /^192\.168\./.test(host)) return true;
    if (/^172\.(1[6-9]|2\d|3[01])\./.test(host)) return true;
    if (/^169\.254\./.test(host) || /^f[cd][0-9a-f]{2}:/.test(host) || /^fe80:/.test(host)) return true;
    return false;
  }

  // 返回自动模式下选 2D 的原因；空字符串表示可以用 3D。
  function lowPerformanceReason() {
    var nav = window.navigator || {};
    if (!webglAvailable()) return '浏览器不支持 WebGL';
    if (nav.connection && nav.connection.saveData) return '已开启省流量';
    if (typeof nav.deviceMemory === 'number' && nav.deviceMemory > 0 && nav.deviceMemory <= 4) return '设备内存较小';
    if (typeof nav.hardwareConcurrency === 'number' && nav.hardwareConcurrency > 0 && nav.hardwareConcurrency <= 4) return 'CPU 核心较少';
    if (!isLocalHost(window.location && window.location.hostname)) return '远程访问';
    return '';
  }

  function renderMode() {
    if (!state.renderMode) state.renderMode = storedRenderMode();
    return state.renderMode;
  }

  // 当前是否应当显示 3D（不管脚本是否已经加载）。
  function want3D() {
    var mode = renderMode();
    if (mode === '2d') return false;
    if (mode === '3d') return true;
    if (state.autoRenderReason == null) state.autoRenderReason = lowPerformanceReason();
    return !state.autoRenderReason;
  }

  // 渲染时使用：想要 3D 且 3D 脚本已经就绪。未就绪时顺便开始加载，加载完会重新渲染。
  function use3D() {
    if (!want3D() || lazy3d.failed) return false;
    if (lazy3d.ready) return true;
    ensure3DScripts();
    return false;
  }

  function loadScriptInOrder(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = src;
      script.async = false;
      script.onload = function () { resolve(); };
      script.onerror = function () { reject(new Error('加载失败：' + src)); };
      document.body.appendChild(script);
    });
  }

  function ensure3DScripts() {
    if (lazy3d.promise) return lazy3d.promise;
    var placeholders = Array.prototype.slice.call(document.querySelectorAll('script[type="text/x-lazy-3d"][data-src]'));
    lazy3d.promise = placeholders.reduce(function (chain, node) {
      return chain.then(function () { return loadScriptInOrder(node.getAttribute('data-src')); });
    }, Promise.resolve()).then(function () {
      lazy3d.ready = !!window.Room3D;
      if (!lazy3d.ready) throw new Error('3D 模块未注册');
      wire3D();
      render();
    }).catch(function (error) {
      lazy3d.failed = true;
      console.warn('[VirtualLife UI] 3D 场景加载失败，改用 2D', error);
      showToast('3D 场景加载失败，已改用 2D');
      render();
    });
    return lazy3d.promise;
  }

  function renderModeLabel() {
    var mode = renderMode();
    if (mode !== 'auto') return '画面：' + RENDER_MODE_LABEL[mode];
    return '画面：自动（' + (want3D() ? '3D' : '2D') + '）';
  }

  function applyRenderMode() {
    var button = $('render-toggle');
    if (!button) return;
    button.textContent = renderModeLabel();
    var reason = renderMode() === 'auto' && !want3D() ? state.autoRenderReason : '';
    button.title = reason ? '自动选择了 2D：' + reason + '。点击切换' : '点击在 自动 / 3D / 2D 之间切换';
  }

  function cycleRenderMode() {
    var next = RENDER_MODES[(RENDER_MODES.indexOf(renderMode()) + 1) % RENDER_MODES.length];
    state.renderMode = next;
    try { localStorage.setItem('vl-render', next); } catch (error) { /* 忽略本地存储异常 */ }
    applyRenderMode();
    if (want3D()) ensure3DScripts();
    showToast(renderModeLabel() + (next === '2d' ? '，更省电、加载更快' : ''));
    render();
  }

