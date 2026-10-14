/* Muse2API Cookie Import — read muse.ai cookies and POST them to the muse2api service.
 * Muse2API Cookie 导入 —— 读取 muse.ai 的 cookie 并 POST 到 muse2api 服务。
 *
 * Key point: use chrome.cookies instead of document.cookie.
 * 关键点：用 chrome.cookies 而不是 document.cookie。
 * The 4 core muse.ai cookies (hatch_sess / hatch_gw / hatch_vml /
 * hatch_native_auth_device) all carry the httpOnly flag, so page JS cannot
 * read them — only the extension cookies API can.
 * muse.ai 的 4 条核心 cookie（hatch_sess / hatch_gw / hatch_vml /
 * hatch_native_auth_device）都带 httpOnly，网页 JS 读不到，
 * 只有浏览器扩展的 cookies 接口能拿到。
 */

const $ = (id) => document.getElementById(id);
const STORE = 'muse2api_ext_cfg';
const LANG_KEY = 'muse2api_ext_lang';

/* UI + log strings, English default with Chinese toggle.
 * 界面与日志文案，默认英文，可切换中文。 */
const STRINGS = {
  en: {
    title: 'Muse2API Cookie Import',
    sub: 'Sync the muse.ai login session from this browser to your muse2api service in one click.',
    labelBase: 'Service URL (BASE URL)',
    labelKey: 'API Key',
    labelLabel: 'Account label (optional)',
    phBase: 'http://your-server-ip:18610',
    phLabel: 'e.g. muse-main',
    go: 'Read & Import',
    toggle: '中文',
    steps: '<b>Before use, confirm two things:</b><br>'
      + '1. You are logged in to <a href="https://muse.ai/" target="_blank"'
      + ' style="color:#4f8cff">muse.ai</a> in <b>this browser</b> (chat UI visible).<br>'
      + '2. Service URL and API Key above are filled in (copy them from the top of the "Accounts" page in the muse2api admin panel).',
    foot: 'This extension does one thing: it reads muse.ai cookies via the browser <code>chrome.cookies</code> API'
      + ' (including httpOnly ones) and POSTs them to the service URL you entered.'
      + ' Nothing is collected or uploaded to any third-party server.',
    errNoBase: 'Please fill in the service URL first',
    errNoKey: 'Please fill in the API Key first',
    reading: 'Reading muse.ai cookies…',
    errNoCookies: 'No muse.ai cookies found.\nPlease open and log in at https://muse.ai/ in this browser, then try again.',
    warnMissing: (n, missing) => `Got ${n} cookies but missing core items: ${missing.join(', ')}\n`
      + 'This browser is not logged in yet. Log in until the chat UI is visible, then retry.',
    uploading: (n, base) => `Got ${n} cookies, uploading to ${base} …`,
    err401: 'API Key is wrong (server returned 401).\nPlease copy the correct API Key from the top of the "Accounts" page in the admin panel.',
    errHttp: (status, text) => `Import failed: HTTP ${status}\n${text.slice(0, 300)}`,
    okSuccess: (tag, id, count, exp, warning) => `✓ Import succeeded\nAccount label: ${tag}\n`
      + `Account ID: ${id}\nCookie count: ${count}\n`
      + `Valid until: ${exp}\n`
      + (warning ? `\nNote: ${warning}` : ''),
    unknownExpiry: 'unknown',
    autoLabel: '(auto)',
    errGeneric: (msg) => 'Error: ' + msg
      + '\n\nCommon causes:\n'
      + '· Wrong service URL or service not running\n'
      + '· URL is not https (or cert not trusted)\n'
      + '· Browser blocked the cross-origin request',
  },
  zh: {
    title: 'Muse2API Cookie 导入',
    sub: '把当前浏览器里 muse.ai 的登录态，一键同步到你的 muse2api 服务。',
    labelBase: '服务地址（BASE URL）',
    labelKey: 'API Key',
    labelLabel: '账号标签（可留空）',
    phBase: 'http://your-server-ip:18610',
    phLabel: '例如 muse-main',
    go: '读取并导入',
    toggle: 'EN',
    steps: '<b>用之前先确认两件事：</b><br>'
      + '1. 你已经在<b>这个浏览器</b>里登录了 <a href="https://muse.ai/" target="_blank"'
      + ' style="color:#4f8cff">muse.ai</a>（能看到聊天界面）。<br>'
      + '2. 上面的服务地址和 API Key 已填好（在 muse2api 管理页「账号池」页顶部可以复制）。',
    foot: '本扩展只做一件事：用浏览器的 <code>chrome.cookies</code> 接口读取 muse.ai 的'
      + 'Cookie（能读到 httpOnly 的那些），POST 到你填的服务地址。'
      + '不收集、不上传到任何第三方服务器。',
    errNoBase: '请先填服务地址',
    errNoKey: '请先填 API Key',
    reading: '正在读取 muse.ai 的 Cookie…',
    errNoCookies: '没读到 muse.ai 的 Cookie。\n请先在这个浏览器里打开并登录 https://muse.ai/ ，再回来点一次。',
    warnMissing: (n, missing) => `读到 ${n} 条 Cookie，但缺核心项：${missing.join('、')}\n`
      + '说明这个浏览器还没登录成功。请登录到能看到聊天界面再试。',
    uploading: (n, base) => `读到 ${n} 条 Cookie，正在上传到 ${base} …`,
    err401: 'API Key 不对（服务返回 401）。\n请到管理页「账号池」页顶部复制正确的 API Key。',
    errHttp: (status, text) => `导入失败：HTTP ${status}\n${text.slice(0, 300)}`,
    okSuccess: (tag, id, count, exp, warning) => `✓ 导入成功\n账号标签：${tag}\n`
      + `账号 ID：${id}\nCookie 条数：${count}\n`
      + `有效期到：${exp}\n`
      + (warning ? `\n注意：${warning}` : ''),
    unknownExpiry: '未知',
    autoLabel: '(自动)',
    errGeneric: (msg) => '出错了：' + msg
      + '\n\n常见原因：\n'
      + '· 服务地址填错或服务没启动\n'
      + '· 这个地址不是 https（或证书不被信任）\n'
      + '· 浏览器拦截了跨域请求',
  },
};

let lang = 'en'; // default English / 默认英文
const T = () => STRINGS[lang] || STRINGS.en;

/* Apply language to static UI. English default, toggle persisted.
 * 应用语言到静态界面。默认英文，切换状态持久化。 */
function applyLang(next) {
  lang = next === 'zh' ? 'zh' : 'en';
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  const t = T();
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const k = el.getAttribute('data-i18n');
    if (k && typeof t[k] === 'string') el.textContent = t[k];
  });
  document.querySelectorAll('[data-i18n-ph]').forEach((el) => {
    const k = el.getAttribute('data-i18n-ph');
    if (k && typeof t[k] === 'string') el.placeholder = t[k];
  });
  document.querySelectorAll('[data-i18n-html]').forEach((el) => {
    const k = el.getAttribute('data-i18n-html');
    if (k && typeof t[k] === 'string') el.innerHTML = t[k];
  });
  const btn = $('lang');
  if (btn) btn.textContent = t.toggle;
  try {
    chrome.storage.local.set({ [LANG_KEY]: lang });
  } catch (e) { /* ignore / 忽略 */ }
}

async function loadLang() {
  // Load persisted language, default en / 读取持久化的语言，默认 en
  try {
    const o = await chrome.storage.local.get(LANG_KEY);
    applyLang(o && o[LANG_KEY] === 'zh' ? 'zh' : 'en');
  } catch (e) {
    applyLang('en');
  }
}

const ESSENTIAL = ['hatch_sess', 'hatch_gw', 'hatch_vml', 'hatch_native_auth_device'];

function log(html, cls) {
  const el = $('log');
  el.className = 'show';
  el.innerHTML = cls ? `<span class="${cls}">${html}</span>` : html;
}

/* Normalize service URL: strip trailing slashes and /v1 suffix.
 * 规范化服务地址：去掉结尾斜杠和 /v1 后缀 */
function normBase(v) {
  let s = (v || '').trim();
  if (!s) return '';
  if (!/^https?:\/\//i.test(s)) s = 'https://' + s;
  s = s.replace(/\/+$/, '');
  s = s.replace(/\/v1$/i, '');
  return s;
}

async function loadCfg() {
  const o = await chrome.storage.local.get(STORE);
  const c = o[STORE] || {};
  if (c.base) $('base').value = c.base;
  if (c.key) $('key').value = c.key;
  if (c.label) $('label').value = c.label;
  // Guess from current tab if never configured (user is on admin page).
  // 没有配置过就尝试从当前标签页猜一个（用户在管理页上时）
  if (!c.base) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const u = tab && tab.url ? new URL(tab.url) : null;
      if (u && /\/admin/.test(u.pathname)) {
        $('base').value = u.origin;
        const k = new URLSearchParams(u.search).get('key');
        if (k) $('key').value = k;
      }
    } catch (e) { /* ignore / 忽略 */ }
  }
}

async function saveCfg() {
  await chrome.storage.local.set({
    [STORE]: {
      base: normBase($('base').value),
      key: $('key').value.trim(),
      label: $('label').value.trim(),
    },
  });
}

async function grabCookies() {
  const all = await chrome.cookies.getAll({ domain: 'muse.ai' });
  const out = {}, exp = {};
  for (const c of all) {
    const dom = (c.domain || '').replace(/^\./, '');
    if (!dom.endsWith('muse.ai')) continue;
    out[c.name] = c.value;
    if (c.expirationDate) exp[c.name] = Math.floor(c.expirationDate);
  }
  return { cookies: out, expires: exp };
}

async function run() {
  const base = normBase($('base').value);
  const key = $('key').value.trim();
  const label = $('label').value.trim();

  if (!base) return log(T().errNoBase, 'bad');
  if (!key) return log(T().errNoKey, 'bad');

  $('go').disabled = true;
  log(T().reading);

  try {
    const { cookies, expires } = await grabCookies();
    const names = Object.keys(cookies);
    if (!names.length) {
      return log(T().errNoCookies, 'bad');
    }
    const missing = ESSENTIAL.filter((n) => !(n in cookies));
    if (missing.length) {
      log(T().warnMissing(names.length, missing), 'warn');
      return;
    }

    log(T().uploading(names.length, base));

    const r = await fetch(base + '/admin/accounts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
      },
      body: JSON.stringify({ label, cookies, expires }),
    });

    const text = await r.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { raw: text }; }

    if (r.status === 401) {
      return log(T().err401, 'bad');
    }
    if (!r.ok) {
      return log(T().errHttp(r.status, text), 'bad');
    }

    const a = (data.added && data.added[0]) || {};
    await saveCfg();
    log(T().okSuccess(
      a.label || label || T().autoLabel,
      a.id || '?',
      a.cookie_count || names.length,
      a.expires_at ? new Date(a.expires_at * 1000).toLocaleString() : T().unknownExpiry,
      data.warning || ''
    ), 'ok');
  } catch (e) {
    log(T().errGeneric(e && e.message ? e.message : String(e)), 'bad');
  } finally {
    $('go').disabled = false;
  }
}

$('go').addEventListener('click', run);
$('lang').addEventListener('click', () => applyLang(lang === 'en' ? 'zh' : 'en'));
loadLang();
loadCfg();
