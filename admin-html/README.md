# admin-html

静态可视化页面（Tailwind + 腾讯地图 JS SDK），通过后端接口拉取数据渲染网格围栏与任务点。

## 页面

- `admin-html/map-dashboard.html`

## Tailwind 本地引入

- 已将 `https://cdn.tailwindcss.com` 下载为 `admin-html/vendor/tailwindcss.js`，页面通过本地脚本引入。
- 如需更新版本：重新下载覆盖该文件即可。

## 本地打开方式（推荐）

1. 先启动后端：确保 `http://localhost:8000` 可访问，并且 `/api/v1/common/map-config/` 已配置 `api_key`（腾讯地图 JS Key）。
2. 用「同域」方式访问页面（避免 CORS）：
   - 如果你有 Nginx/网关：把 `admin-html/` 作为静态目录挂到同一域名下。
   - 或者把该页面集成到后端模板/静态路由中再访问。
3. 打开页面后，如需指定接口地址，在右上角 `API Base` 中填写（例如 `http://localhost:8000`）。

> 直接用 `file://` 打开时，浏览器可能会拦截跨域请求（CORS），页面会提示该问题。
