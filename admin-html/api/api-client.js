(function (global) {
  function joinUrl(base, path) {
    var b = String(base || "").replace(/\/+$/, "");
    var p = String(path || "");
    if (!p) return b;
    if (/^https?:\/\//i.test(p)) return p;
    if (p.charAt(0) !== "/") p = "/" + p;
    return b + p;
  }

  function isSameOrigin(url) {
    try {
      var u = new URL(url, global.location.href);
      return u.origin === global.location.origin;
    } catch (e) {
      return false;
    }
  }

  function getCookie(name) {
    try {
      var m = global.document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
      return m ? decodeURIComponent(m[2]) : "";
    } catch (e) {
      return "";
    }
  }

  async function apiRequest(apiBase, path, options) {
    var url = joinUrl(apiBase, path);
    var headers = Object.assign({ Accept: "application/json" }, (options && options.headers) || {});
    var body = options && options.body;
    var method = (options && options.method) || (body ? "POST" : "GET");
    if (body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";

    var csrf = getCookie("csrftoken");
    if (csrf && !headers["X-CSRFToken"]) headers["X-CSRFToken"] = csrf;

    var controller = new AbortController();
    var timeout = setTimeout(function () {
      controller.abort();
    }, 15000);
    var creds = isSameOrigin(url) ? "same-origin" : "omit";

    try {
      var res = await fetch(url, {
        method: method,
        headers: headers,
        body: body,
        credentials: creds,
        signal: controller.signal
      });
      var text = await res.text();
      var json = null;
      try {
        json = text ? JSON.parse(text) : null;
      } catch (e) {
        json = null;
      }

      if (!res.ok) {
        var msg = (json && json.message) || (text ? text.slice(0, 160) : "") || ("HTTP " + res.status);
        throw new Error(msg);
      }
      if (json && typeof json === "object" && "code" in json) {
        var code = Number(json.code);
        if (code !== 200 && code !== 0) {
          throw new Error(json.message || "请求失败");
        }
        return json.data;
      }
      return json;
    } finally {
      clearTimeout(timeout);
    }
  }

  function createClient(apiBase) {
    return {
      request: function (path, options) {
        return apiRequest(apiBase, path, options);
      }
    };
  }

  global.AdminApi = global.AdminApi || {};
  global.AdminApi.createClient = createClient;
})(window);
