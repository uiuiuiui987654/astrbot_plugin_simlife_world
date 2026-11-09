/* Keep the established scene UI behind AstrBot's authenticated view bridge. */
(function () {
  'use strict';
  var nativeFetch = window.fetch.bind(window);
  var selectedPersona = '';
  var previewMode = false;
  window.fetch = async function (input, options) {
    var url = new URL(typeof input === 'string' ? input : input.url, document.baseURI);
    if (url.origin !== location.origin || url.pathname.indexOf('/api/') !== 0) {
      return nativeFetch(input, options);
    }
    var endpoint = url.pathname.slice(5);
    var bridge = window.AstrBotPluginView || window.AstrBotPluginPage;
    if (!bridge) throw new Error('请从 AstrBot 的虚拟人生插件视图打开此页');
    await bridge.ready();
    var params = Object.fromEntries(url.searchParams.entries());
    if (selectedPersona && !params.persona) params.persona = selectedPersona;
    var method = String(options && options.method || 'GET').toUpperCase();
    var result;
    if (method === 'POST') {
      var body = JSON.parse(options && options.body || '{}');
      if (previewMode) {
        result = {ok: false, error: '时间预览只供查看，请回到当前时间再互动'};
      } else {
        if (selectedPersona) body.persona = selectedPersona;
        result = await bridge.apiPost('view/' + endpoint, body);
      }
    } else {
      result = await bridge.apiGet('view/' + endpoint, params);
    }
    if (result && result.status === 'error') throw new Error(result.message || '视图请求失败');
    if (endpoint === 'state' && result) {
      if (result.persona && result.ok) selectedPersona = result.persona;
      previewMode = Boolean(result.preview);
      if (result.appearance) {
        ['src', 'avatar_src'].forEach(function (key) {
          var value = result.appearance[key];
          if (!value || typeof value !== 'string') return;
          if (value.charAt(0) === '/') value = value.slice(1);
          result.appearance[key] = new URL(value, document.baseURI).href;
        });
      }
    }
    return new Response(JSON.stringify(result), {status: 200, headers: {'Content-Type': 'application/json'}});
  };
})();
