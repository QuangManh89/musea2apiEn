Muse2API Cookie Import Extension — Install Guide
=================================================
[中文说明见下文 / Chinese version below](#中文说明)

This extension does one thing: sync your browser's muse.ai login Cookies
to your muse2api service. No Python, no terminal needed.


1. Extract
----------
Extract muse2api-extension.zip to a folder you won't delete, e.g.:

    Windows : D:\muse2api-extension
    macOS   : ~/Documents/muse2api-extension

After extracting you should see manifest.json, popup.html, popup.js.


2. Load it in Chrome / Edge
---------------------------
Chrome:
  1. Type chrome://extensions in the address bar, press Enter
  2. Turn on the "Developer mode" switch (top right)
  3. Click "Load unpacked" (top left)
  4. Select the folder from step 1 (the folder itself, not a single file)
  5. A puzzle icon appears in the toolbar; pin it (optional but handy)

Edge:
  1. Type edge://extensions in the address bar, press Enter
  2. Turn on "Developer mode" (bottom left)
  3. Click "Load unpacked"
  4. Same as above

Other Chromium-based browsers (Brave / Vivaldi / 360 Speed, etc.) are similar.


3. Use
------
1. In this browser, open https://muse.ai/ and log in
   until you can see the chat UI.
2. On the muse2api admin page, "Account Pool" section top, copy the BASE URL and API Key.
3. Click the extension icon in the toolbar and fill in both fields (once — it remembers).
4. Click "Read & import". "✓ Import successful" means you're done.


4. FAQ
------
Q: "No muse.ai Cookies found"
A: This browser isn't logged in to muse.ai yet. Open https://muse.ai/ and log in first.

Q: "Missing core keys like hatch_sess"
A: Same as above — login isn't complete. Confirm the chat UI is visible, then click again.

Q: "Wrong API Key (server returned 401)"
A: Re-copy the API Key from the admin page. Keys start with m2a_.

Q: Cross-origin / network error
A: Check whether the service address uses https, and whether the service itself loads
   (try opening <service-address>/admin directly in the browser).

Q: Will it send my Cookies anywhere else?
A: No. The extension only has the cookies and storage permissions, and the code is right
   there in popup.js — audit it yourself: it only POSTs to the service address you entered.


5. Uninstall
------------
chrome://extensions → find "Muse2API Cookie Import" → Remove.

---

<a id="中文说明"></a>
Muse2API Cookie 导入扩展 —— 安装说明
=====================================

这个扩展只做一件事：把你浏览器里 muse.ai 的登录 Cookie
同步到你的 muse2api 服务。不用装 Python、不用开终端。


一、解压
--------
把 muse2api-extension.zip 解压到一个你不会删掉的目录，例如：

    Windows : D:\muse2api-extension
    macOS   : ~/Documents/muse2api-extension

解压后应该能看到 manifest.json、popup.html、popup.js 三个文件。


二、在 Chrome / Edge 里加载
---------------------------
Chrome：
  1. 地址栏输入  chrome://extensions  回车
  2. 打开右上角的「开发者模式」开关
  3. 点左上角「加载已解压的扩展程序」
  4. 选中第 1 步解压出来的那个文件夹（不是里面的单个文件）
  5. 工具栏出现一个拼图图标，把它固定到工具栏（可选但方便）

Edge：
  1. 地址栏输入  edge://extensions  回车
  2. 打开左下角「开发人员模式」
  3. 点「加载解压缩的扩展」
  4. 其余同上

其他 Chromium 内核浏览器（Brave / Vivaldi / 360 极速 等）步骤类似。


三、使用
--------
1. 先在这个浏览器里打开 https://muse.ai/ 并登录，
   登录到能看到聊天界面为止。
2. 到 muse2api 管理页「账号池」页顶部，复制 BASE URL 和 API Key。
3. 点浏览器工具栏上的扩展图标，把这两项填进去（只需要填一次，会记住）。
4. 点「读取并导入」。看到「✓ 导入成功」就完成了。


四、常见问题
------------
Q: 提示「没读到 muse.ai 的 Cookie」
A: 说明这个浏览器里还没登录 muse.ai。先打开 https://muse.ai/ 登录。

Q: 提示「缺核心项 hatch_sess 等」
A: 同上 —— 登录没完成。确认能看到聊天界面再点。

Q: 提示「API Key 不对（服务返回 401）」
A: 到管理页重新复制一次 API Key。注意 Key 以 m2a_ 开头。

Q: 提示跨域 / 网络错误
A: 检查服务地址是不是 https，以及服务本身能不能打开
   （浏览器直接访问 服务地址/admin 试试）。

Q: 会不会把我的 Cookie 传到别的地方？
A: 不会。扩展只有 cookies 和 storage 两个权限，代码就在 popup.js 里，
   你可以自己看：它只往你填的那个服务地址发一个 POST，没有别的请求。


五、卸载
--------
chrome://extensions → 找到「Muse2API Cookie 导入」→ 移除。
