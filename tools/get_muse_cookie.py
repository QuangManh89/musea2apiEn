#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""muse2api Cookie helper — import your muse.ai login cookies into the account pool in one step.
muse2api Cookie 助手 —— 一键把 muse.ai 的登录 cookie 导入账号池。

Why is this script needed? / 为什么需要这个脚本？
    The 4 core muse.ai cookies (hatch_sess / hatch_gw / hatch_vml /
    hatch_native_auth_device) all carry the httpOnly flag, so
    document.cookie in the page cannot read them. Only the browser
    internals (Chrome DevTools Protocol) can.
    muse.ai 的 4 条核心 cookie（hatch_sess / hatch_gw / hatch_vml /
    hatch_native_auth_device）全部带 httpOnly 标记，网页里的 document.cookie
    读不到它们。只有从浏览器底层（Chrome DevTools Protocol）才能读到。
    So a bookmarklet or a one-liner in the console cannot solve this —
    hence the script drives a browser.
    所以没法用「小书签」或「控制台一行代码」解决，必须让脚本驱动浏览器。

How it works / 它是怎么工作的？
    1. Launch a Chrome window with a separate temp profile (does not touch your daily browser)
       用一个独立的临时配置目录启动一个 Chrome 窗口（不影响你日常用的浏览器）
    2. You log in to muse.ai in that window / 你在那个窗口里登录 muse.ai
    3. The script polls cookies and auto-uploads once complete
       脚本轮询读取 cookie，一拿到就自动上传到 muse2api
    4. Close the window, done / 关掉窗口，完事

Usage / 用法：
    python get_muse_cookie.py --base http://your-server-ip:18610 --key m2a_xxx
    python get_muse_cookie.py --base http://your-server-ip:18610 --key m2a_xxx --label acc-01

Or use env vars to save typing / 也可以先用环境变量，省得每次敲：
    set MUSE2API_BASE=http://your-server-ip:18610     (Windows)
    set MUSE2API_KEY=m2a_xxx
    export MUSE2API_BASE=...                          (macOS / Linux)
    export MUSE2API_KEY=...

Only Python stdlib (Python 3.8+), no pip install needed.
只依赖 Python 标准库（Python 3.8+），不需要 pip install 任何东西.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

SITE = "https://muse.ai/"
CDP_PORT = 9333
ESSENTIAL = ("hatch_sess", "hatch_gw", "hatch_vml", "hatch_native_auth_device")
DOMAIN_HINT = "muse.ai"


# ------------------------------------------------------------- output / 输出
def say(msg=""):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:                     # old Windows console / 老 Windows 控制台
        print(msg.encode("utf-8", "replace").decode("utf-8", "replace"), flush=True)


def init_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")   # Python 3.7+
        except Exception:                          # noqa: BLE001
            pass


# ------------------------------------------------------------- minimal WebSocket / 极简 WebSocket
class WS:
    """Minimal WebSocket client just for CDP (RFC6455, text frames).
    只为 CDP 用的最小 WebSocket 客户端（RFC6455，文本帧）。"""

    def __init__(self, url: str, timeout: float = 15.0):
        assert url.startswith("ws://"), url
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        path = "/" + path
        host, _, port = hostport.partition(":")
        port = int(port or 80)

        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET {path} HTTP/1.1\r\n"
               f"Host: {host}:{port}\r\n"
               "Upgrade: websocket\r\n"
               "Connection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake interrupted / WebSocket 握手被断开")
            buf += chunk
        status = buf.split(b"\r\n", 1)[0]
        if b" 101" not in status:
            raise ConnectionError(f"WebSocket handshake failed / WebSocket 握手失败: {status!r}")
        self._id = 0

    # --- send / 发送 ---
    def _frame(self, opcode: int, payload: bytes):
        head = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head.append(0x80 | 126)
            head += struct.pack(">H", n)
        else:
            head.append(0x80 | 127)
            head += struct.pack(">Q", n)
        mask = os.urandom(4)
        head += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(head) + masked)

    def send_text(self, text: str):
        self._frame(0x1, text.encode("utf-8"))

    # --- receive / 接收 ---
    def _read(self, n: int) -> bytes:
        out = b""
        while len(out) < n:
            chunk = self.sock.recv(n - len(out))
            if not chunk:
                raise ConnectionError("connection closed / 连接已关闭")
            out += chunk
        return out

    def recv_text(self) -> str:
        while True:
            h = self._read(2)
            opcode = h[0] & 0x0F
            masked = h[1] & 0x80
            ln = h[1] & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read(8))[0]
            mk = self._read(4) if masked else None
            data = self._read(ln) if ln else b""
            if mk:
                data = bytes(b ^ mk[i % 4] for i, b in enumerate(data))
            if opcode == 0x1:
                return data.decode("utf-8", "replace")
            if opcode == 0x9:                       # ping -> pong
                self._frame(0xA, data)
            elif opcode == 0x8:
                raise ConnectionError("server closed the connection / 服务端关闭了连接")
            # others (pong / binary / fragments) ignored / 其它（pong / 二进制 / 分片）直接忽略

    def call(self, method: str, params: dict | None = None,
             timeout: float = 20.0) -> dict:
        self._id += 1
        mid = self._id
        self.send_text(json.dumps({"id": mid, "method": method,
                                   "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = json.loads(self.recv_text())
            except socket.timeout:
                continue
            except ConnectionError:
                raise
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(f"CDP {method} timed out / 超时")

    def close(self):
        try:
            self.sock.close()
        except Exception:                              # noqa: BLE001
            pass


# ------------------------------------------------------------- find browser / 找浏览器
CHROME_EXES = ("chrome.exe", "msedge.exe", "brave.exe", "chromium.exe")


def _win_registry_paths() -> list[str]:
    """Find browsers via registry App Paths.
    从注册表 App Paths 找浏览器。

    Cannot rely on the %ProgramFiles% env var — it may not exist in some
    shells / minimal environments (measured None for both ProgramFiles and
    PROGRAMFILES on this machine).
    不能靠 %ProgramFiles% 环境变量 —— 它在某些 shell / 精简环境下并不存在
    （本机实测 ProgramFiles 和 PROGRAMFILES 都是 None）。
    """
    out: list[str] = []
    try:
        import winreg
    except ImportError:
        return out
    sub = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for exe in CHROME_EXES:
            for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                try:
                    with winreg.OpenKey(root, sub + "\\" + exe, 0,
                                        winreg.KEY_READ | view) as k:
                        val = winreg.QueryValueEx(k, "")[0]
                        if val:
                            out.append(os.path.expandvars(val))
                except OSError:
                    continue
    return out


def _win_common_paths() -> list[str]:
    roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
             os.environ.get("LOCALAPPDATA"), r"C:\Program Files",
             r"C:\Program Files (x86)"]
    rel = [
        r"Google\Chrome\Application\chrome.exe",
        r"Microsoft\Edge\Application\msedge.exe",
        r"BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    return [os.path.join(r, p) for r in roots if r for p in rel]


def find_chrome() -> str | None:
    if sys.platform == "win32":
        cands = _win_registry_paths() + _win_common_paths()
    elif sys.platform == "darwin":
        cands = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
    else:
        cands = ["google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "microsoft-edge", "brave-browser"]
    seen = set()
    for c in cands:
        if not c or c in seen:
            continue
        seen.add(c)
        if os.path.isfile(c):
            return c
        if not os.path.isabs(c):
            w = shutil.which(c)
            if w:
                return w
    return None


def wait_cdp(port: int, timeout: float = 30.0) -> str:
    """Wait for the DevTools port, return the browser-level WebSocket URL.
    等 DevTools 端口起来，返回浏览器级 WebSocket 地址。"""
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return json.load(r)["webSocketDebuggerUrl"]
        except Exception as exc:                       # noqa: BLE001
            last = exc
            time.sleep(0.5)
    raise RuntimeError(f"browser debug port never came up ({port}): {last} / 浏览器调试端口没起来（{port}）：{last}")


# ------------------------------------------------------------- read cookies / 读 cookie
def read_cookies(ws: WS) -> dict[str, dict]:
    """Grab all cookies via browser-level Storage.getCookies, then filter muse.ai.
    用浏览器级 Storage.getCookies 拿全部 cookie，再筛 muse.ai。

    This is the key: CDP can read httpOnly cookies, page JS cannot.
    这是关键：CDP 能读到 httpOnly 的 cookie，网页 JS 读不到。
    """
    res = ws.call("Storage.getCookies", {}, timeout=20)
    out: dict[str, dict] = {}
    for c in res.get("cookies", []):
        domain = (c.get("domain") or "").lstrip(".")
        if DOMAIN_HINT not in domain:
            continue
        name = c.get("name")
        if not name:
            continue
        try:
            exp = int(float(c.get("expires", -1)))
        except (TypeError, ValueError):
            exp = -1
        out[name] = {"value": c.get("value", ""), "expires": exp,
                     "httpOnly": bool(c.get("httpOnly"))}
    return out


# ------------------------------------------------------------- upload / 上传
def upload(base: str, key: str, label: str, cookies: dict[str, dict]) -> dict:
    payload = {
        "label": label,
        "cookies": {k: v["value"] for k, v in cookies.items()},
        "expires": {k: v["expires"] for k, v in cookies.items() if v["expires"] > 0},
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/admin/accounts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"upload failed HTTP {e.code}: {detail} / 上传失败 HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"cannot reach {base}: {e.reason} / 连不上 {base}：{e.reason}") from None


def fmt_ts(ts: int) -> str:
    if ts <= 0:
        return "session / 会话级"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ------------------------------------------------------------- main flow / 主流程
def main() -> int:
    init_console()
    ap = argparse.ArgumentParser(
        description="Import muse.ai login cookies into the muse2api account pool in one step / 把 muse.ai 的登录 cookie 一键导入 muse2api 账号池")
    ap.add_argument("--base", default=os.environ.get("MUSE2API_BASE", ""),
                    help="muse2api URL, e.g. http://your-server-ip:18610 / muse2api 地址，如 http://your-server-ip:18610")
    ap.add_argument("--key", default=os.environ.get("MUSE2API_KEY", ""),
                    help="API Key (starts with m2a_) / API Key（m2a_ 开头）")
    ap.add_argument("--label", default="", help="account label, e.g. acc-01 / 账号标签，如 acc-01")
    ap.add_argument("--timeout", type=int, default=300,
                    help="max seconds to wait for login, default 300 / 等待登录的最长秒数，默认 300")
    ap.add_argument("--keep-open", action="store_true",
                    help="keep the browser window open after a successful upload / 上传成功后不关闭浏览器窗口")
    ap.add_argument("--port", type=int, default=CDP_PORT,
                    help=f"debug port, default {CDP_PORT} / 调试端口，默认 {CDP_PORT}")
    ap.add_argument("--chrome", default="", help="manually specify the browser executable path / 手动指定浏览器可执行文件路径")
    args = ap.parse_args()

    say("=" * 66)
    say("  muse2api Cookie Helper / muse2api Cookie 助手")
    say("=" * 66)
    say()

    if not args.base or not args.key:
        say("✗ Missing arguments. Run like this / 缺少参数。请这样运行：")
        say("    python get_muse_cookie.py --base https://your-domain / --base https://你的域名 --key m2a_xxx")
        say()
        say("  (Copy both values from 'Access Info' on the muse2api admin page / 这两个值可以在 muse2api 管理页面的「接入信息」里复制）")
        return 2
    if not args.label:
        args.label = "muse-" + time.strftime("%m%d-%H%M")

    chrome = args.chrome or find_chrome()
    if not chrome:
        say("✗ No Chrome / Edge browser found. / 没找到 Chrome / Edge 浏览器。")
        say("  Install Chrome first, or pass --chrome \"full path\" to specify one manually.")
        say("  请先安装 Chrome，或用 --chrome \"完整路径\" 手动指定。")
        return 3
    say(f"Browser / 浏览器：{chrome}")

    profile = os.path.join(tempfile.gettempdir(), "muse2api-cookie-profile")
    shutil.rmtree(profile, ignore_errors=True)
    os.makedirs(profile, exist_ok=True)

    args_cmd = [
        chrome,
        f"--remote-debugging-port={args.port}",
        f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check",
        # In restricted environments (containers / sandboxes / CI) Chrome's own
        # sandbox fails to init:
        #   "sandbox initialization failed: Operation not permitted"
        # -> GPU/network child processes crash -> Chrome exits at once, the debug
        #   port never listens, and the WebSocket dies on handshake with
        #   "connection closed / Broken pipe".
        # These two flags work around it. Harmless on normal desktops (they just
        # disable Chrome's own sandbox).
        # 受限环境（容器 / 沙箱 / CI）里 Chrome 自带的沙箱会初始化失败：
        #   "sandbox initialization failed: Operation not permitted"
        # → GPU/网络子进程崩掉 → Chrome 直接退出，调试端口从未监听起来，
        #   表现是 WebSocket 一握手就 "连接已关闭 / Broken pipe"。
        # Add the two flags below to work around it. No side effects on normal
        # desktops (they just skip Chrome's own sandbox).
        # 加下面两个开关可绕过。日常桌面环境无副作用（只是不启用 Chrome 自带沙箱）。
        "--no-sandbox", "--disable-gpu",
        "--new-window", SITE,
    ]
    say("Opening a separate browser window (your daily browser is untouched)…")
    say("正在打开一个独立的浏览器窗口（不会动你日常用的浏览器）…")
    proc = subprocess.Popen(args_cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    ws = None
    try:
        try:
            ws_url = wait_cdp(args.port, 30)
        except RuntimeError as exc:
            say(f"✗ {exc}")
            say("  Tip: if a browser is already running, quit it fully and retry.")
            say("  提示：如果浏览器已经开着，请先完全退出再试一次。")
            say("  (While your daily Chrome runs, it hijacks the new window and the debug port never comes up.)")
            say("  （日常 Chrome 在跑时，新窗口会被它接管，调试端口起不来。）")
            return 4
        ws = WS(ws_url)

        say()
        say("┌" + "─" * 64 + "┐")
        say("│  Log in to muse.ai in the popup browser window (any usual way)  │")
        say("│  请在弹出的浏览器窗口里登录 muse.ai（用你平时的方式登录即可）  │")
        say("│  Once logged in with the chat UI visible, capture is automatic.  │")
        say("│  登录成功、能看到聊天界面后，脚本会自动抓取，无需其它操作。    │")
        say("└" + "─" * 64 + "┘")
        say()

        deadline = time.time() + args.timeout
        got: dict[str, dict] = {}
        last_note = 0.0
        while time.time() < deadline:
            try:
                got = read_cookies(ws)
            except Exception as exc:                    # noqa: BLE001
                say(f"  Cookie read error, retrying… / 读取 cookie 出错，重试中…（{exc}）")
                time.sleep(2)
                continue

            have = [n for n in ESSENTIAL if n in got]
            if len(have) == len(ESSENTIAL):
                break

            now = time.time()
            if now - last_note > 5:
                last_note = now
                left = int(deadline - now)
                say(f"  Waiting for login… got {len(have)}/{len(ESSENTIAL)} core cookies"
                    f" ({', '.join(have) or 'none'}) {left}s left")
                say(f"  等待登录… 已拿到 {len(have)}/{len(ESSENTIAL)} 条核心 cookie"
                    f"（{', '.join(have) or '无'}）剩余 {left}s")
            time.sleep(2)
        else:
            say()
            say("✗ Timed out waiting for login. / 等待超时，还没登录成功。")
            say("  Re-run the script and finish logging in inside the window.")
            say("  请重跑一次脚本，并在窗口里完成登录。")
            return 5

        say()
        say("✓ Full session cookies captured: / 已拿到完整会话 cookie：")
        say()
        say(f"  {'cookie name / 名':<30}{'httpOnly':<10}{'expires / 有效期'}")
        say("  " + "-" * 62)
        for name in ESSENTIAL:
            c = got.get(name, {})
            say(f"  {name:<30}{('yes / 是' if c.get('httpOnly') else 'no / 否'):<10}"
                f"{fmt_ts(c.get('expires', -1))}")
        say()

        say("Uploading to muse2api… / 正在上传到 muse2api…")
        try:
            r = upload(args.base, args.key, args.label, got)
        except RuntimeError as exc:
            say(f"✗ {exc}")
            say()
            say("  Cookies captured but upload failed. Copy the line below manually")
            say("  cookie 已经抓到了，但上传失败。你可以手动复制下面这行，")
            say("  and paste it into the admin page 'Import account' box:")
            say("  粘贴到管理页面的「导入账号」输入框：")
            say()
            say("  " + "; ".join(f"{k}={v['value']}" for k, v in got.items()))
            return 6

        say()
        say("=" * 66)
        say(f"✓ Import succeeded! Label: {r['added'][0]['label']} / 导入成功！账号标签：{r['added'][0]['label']}")
        say(f"  Account ID: {r['added'][0]['id']} / 账号 ID：{r['added'][0]['id']}")
        say(f"  {r['added'][0]['cookie_count']} cookies total / 共 {r['added'][0]['cookie_count']} 条 cookie")
        if r.get("warning"):
            say(f"  ⚠ {r['warning']}")
        say()
        say(f"  Open {args.base.rstrip('/')}/ to see it in the pool. / 打开 {args.base.rstrip('/')}/ 就能在账号池里看到它。")
        say("=" * 66)
        return 0

    finally:
        if ws:
            ws.close()
        if not args.keep_open:
            try:
                proc.terminate()
            except Exception:                           # noqa: BLE001
                pass
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say()
        say("Cancelled. / 已取消。")
        sys.exit(130)
