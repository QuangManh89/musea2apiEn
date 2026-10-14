#!/usr/bin/env python3
"""Mail.tm temp inbox: request an address + poll for the OTP code.
Mail.tm 临时邮箱：申请地址 + 轮询取验证码。

Purpose: when muse.ai login asks for an email OTP, run this script to get a
temp address, enter it on the login page, and the script prints the received code.
用途：muse.ai 登录要邮箱验证码时，跑这个脚本拿到一个临时邮箱地址，
      填进登录页，脚本会把收到的验证码打印出来。

Zero deps (stdlib only). Usage / 零依赖（纯标准库）。用法：
    python3 mailtm_otp.py                # request a new address and start polling / 申请新地址并开始轮询
    python3 mailtm_otp.py --addr a@b.c --pass xxx   # reuse an existing address / 复用已有地址
    python3 mailtm_otp.py --timeout 600  # poll duration in seconds, default 900 / 轮询时长（秒），默认 900
"""
import argparse, json, random, re, string, sys, time, urllib.request, urllib.error

API = "https://api.mail.tm"


def req(path, method="GET", token=None, body=None):
    """Send one request, return the parsed JSON. / 发一个请求，返回解析后的 JSON。"""
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    r.add_header("Accept", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        raise SystemExit(f"[!] {method} {path} -> HTTP {e.code}: {detail}")


def new_account():
    """Request a new address, return (address, password, token).
    申请一个新地址，返回 (address, password, token)。"""
    d = req("/domains")
    domains = d["hydra:member"] if isinstance(d, dict) else d  # new API returns an array, old one a hydra wrapper / 新版返回数组，旧版 hydra 包装
    domain = next(x["domain"] for x in domains if x.get("isActive", True))
    user = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    addr, pwd = f"{user}@{domain}", "".join(random.choices(string.ascii_letters + string.digits, k=16))
    req("/accounts", "POST", body={"address": addr, "password": pwd})
    token = req("/token", "POST", body={"address": addr, "password": pwd})["token"]
    return addr, pwd, token


def login(addr, pwd):
    return req("/token", "POST", body={"address": addr, "password": pwd})["token"]


CODE_RE = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")


def poll(token, timeout):
    """Poll for new mail; print the OTP code once found. Return the code or None.
    轮询新邮件，发现验证码就打印。返回验证码或 None。"""
    seen, deadline = set(), time.time() + timeout
    print(f"[*] Start polling inbox (up to {timeout}s, Ctrl-C stops) / 开始轮询收件箱（最多 {timeout}s，Ctrl-C 可停）\n")
    while time.time() < deadline:
        try:
            r = req("/messages?page=1", token=token)
            msgs = r["hydra:member"] if isinstance(r, dict) else r
        except SystemExit:
            time.sleep(3); continue
        for m in msgs:
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            full = req(f"/messages/{m['id']}", token=token)
            frm = (full.get("from") or {}).get("address", "?")
            subj = full.get("subject", "")
            body = full.get("text") or full.get("intro") or ""
            print(f"[+] New mail from {frm} / 新邮件  来自 {frm}\n    Subject / 主题：{subj}")
            codes = CODE_RE.findall(f"{subj}\n{body}")
            print(f"    Body / 正文：{body.strip()[:500]}")
            if codes:
                print(f"\n>>> OTP code / 验证码：{codes[0]}\n")
                return codes[0]
            print("    (No code recognized, keep waiting… / 未识别到验证码，继续等待…）\n")
        left = int(deadline - time.time())
        print(f"    Waiting… {left}s left / 等待中… 剩余 {left}s", end="\r", flush=True)
        time.sleep(3)
    print("\n[!] Timed out, no code received. / 超时，未收到验证码。")
    return None


def main():
    ap = argparse.ArgumentParser(description="Mail.tm temp inbox: request an address + poll for the OTP code / Mail.tm 临时邮箱：申请地址 + 轮询取验证码")
    ap.add_argument("--addr", help="existing address to reuse / 复用的已有地址"); ap.add_argument("--pass", dest="pwd", help="password of the existing address / 已有地址的密码")
    ap.add_argument("--timeout", type=int, default=900, help="poll duration in seconds, default 900 / 轮询时长（秒），默认 900")
    a = ap.parse_args()
    if a.addr and a.pwd:
        addr, pwd, token = a.addr, a.pwd, login(a.addr, a.pwd)
        print(f"[*] Reusing address / 复用已有地址：{addr}")
    else:
        addr, pwd, token = new_account()
        print(f"[*] New address issued / 已申请新地址：{addr}\n    Password / 密码：{pwd} (needed for reuse / 复用需带上）")
    print(f"\n=== Enter this address on the muse.ai login page / 把下面这个地址填进 muse.ai 登录页 ===\n    {addr}\n")
    code = poll(token, a.timeout)
    sys.exit(0 if code else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Stopped. / 已停止。")
