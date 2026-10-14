"""Hit the live page with engine.py's real-world JS snippet to verify / fix selectors.
直接用 engine.py 的现网 JS 片段打真页面，验证 / 修正选择器。

Usage / 用法：
  python3 tools/verify_engine_selectors.py
It will / 会：
  1) connect to the live muse.ai page / 连到现网 muse.ai 页面
  2) run engine._ATT_JS -> print captured attachments / 跑 engine._ATT_JS -> 打印抓到的附件
  3) run engine's inject + wait-confirm logic to test whether the "remove attachment" button shows up
     跑 engine 的注入 + 等待确认逻辑，测「移除附件」按钮是否出现
  4) print all button[aria-label] in the current composer / 打印当前 composer 里所有 button[aria-label]
"""
from __future__ import annotations

import json
import sys
import time
from types import SimpleNamespace

HERE = __file__.rsplit("/", 2)[0]
sys.path.insert(0, HERE)

from cdp import CDP, http_json  # noqa: E402
import engine as E  # noqa: E402

CDP_PORT = 19210
PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
           "IQAAAABJRU5ErkJggg==")


def find_page_ws():
    pages = http_json(f"http://127.0.0.1:{CDP_PORT}/json")
    for p in pages:
        if p.get("type") == "page" and "muse.ai" in (p.get("url") or ""):
            return p.get("webSocketDebuggerUrl"), p.get("url")
    raise SystemExit("no muse.ai page found / 没找到 muse.ai 页面")


class FakeEngine:
    """Tiny shell carrying only a page, reusing engine's JS / logic.
    只带 page 的小壳，复用 engine 的 JS / 逻辑。"""
    def __init__(self, page):
        self.page = page
        self.cfg = SimpleNamespace(media_dir="/tmp", profile_dir="/tmp")

    # borrow real methods / 借用真方法
    attachments = E.MuseEngine.attachments
    _clear_attachments = E.MuseEngine._clear_attachments


def main():
    ws, url = find_page_ws()
    print(f"[verify] page = {url}\n")
    c = CDP(ws)
    e = FakeEngine(c)
    try:
        # 0) all aria-labels in composer / composer 所有 aria-label
        labels = c.js("""JSON.stringify(Array.from(document.querySelectorAll('button[aria-label]'))
            .map(function(b){return b.getAttribute('aria-label');}))""")
        print("=== button[aria-label] on page ===")
        print(labels)

        # 1) engine._ATT_JS
        atts = e.attachments()
        print(f"\n=== engine.attachments() -> {len(atts)} ===")
        for a in atts[:8]:
            print("  ", json.dumps({k: (str(v)[:70] if k.endswith('Src') or k == 'src' else v)
                                    for k, v in a.items()}, ensure_ascii=False))

        # 2) inject + both confirm criteria / 注入 + 两种确认判据
        print("\n=== inject 1x1 PNG / 注入 1x1 PNG ===")
        res = c.js(E.MuseEngine._attach_image.__doc__ and
                   "0" or "0")  # noop placeholder
        # reuse engine's inject JS directly / 直接搬 engine 的注入 JS
        inject = """(function(b64, mime){
            var bin=atob(b64); var arr=new Uint8Array(bin.length);
            for(var i=0;i<bin.length;i++) arr[i]=bin.charCodeAt(i);
            var blob=new Blob([arr],{type:mime});
            var file=new File([blob],'reference_image.png',{type:mime});
            var input=document.querySelectorAll('input[type="file"]')[0];
            if(!input) return JSON.stringify({ok:false,err:'no-file-input'});
            input.setAttribute('accept','image/*');
            var dt=new DataTransfer(); dt.items.add(file);
            input.files=dt.files;
            input.dispatchEvent(new Event('change',{bubbles:true}));
            input.dispatchEvent(new Event('input',{bubbles:true}));
            return JSON.stringify({ok:true});
        })(%s, %s)""" % (json.dumps(PNG_B64), json.dumps("image/png"))
        print("inject:", c.js(inject))

        for i in range(12):
            time.sleep(0.5)
            old = c.js("""(function(){return Boolean(document.querySelector('button[aria-label*="Remove attachment" i]'));})()""")
            zh = c.js("""(function(){return Boolean(document.querySelector('button[aria-label*="移除附件"]'));})()""")
            img = c.js("""(function(){var ov=document.querySelector('[data-testid="hatch-composer-placeholder-overlay"]');
                var comp=ov?ov.closest('form')||ov.parentElement.parentElement.parentElement:null;
                return comp?comp.querySelectorAll('img').length:-1;})()""")
            if old or zh or img:
                print(f"  [t={i*0.5+0.5}s] OLD(Remove attachment EN)={old}  NEW(移除附件 ZH)={zh}  composerImgs={img}")
                if old or zh:
                    break
        # cleanup / 清理
        print("clear:", e._clear_attachments())
    finally:
        c.close()


if __name__ == "__main__":
    main()
