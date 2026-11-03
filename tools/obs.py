# -*- coding: utf-8 -*-
"""连接带调试端口的 Obsidian(--remote-debugging-port=9222)，找到本工程示例库的窗口。
两个主题工程的示例库文件夹都叫 demo-vault(窗口标题一样)，按 app.vault.adapter.basePath 认。
用法(模块)：with demo_page() as (browser, page): ...
命令行：python tools/obs.py open   # 示例库没开就从别的窗口打开它
"""
import contextlib
import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "demo-vault"


def _pages(b):
    return [pg for c in b.contexts for pg in c.pages if pg.url.startswith("app://obsidian.md/index.html")]


def find(b):
    for pg in _pages(b):
        try:
            base = pg.evaluate("() => window.app?.vault?.adapter?.basePath || ''")
        except Exception:
            continue
        if Path(base).resolve() == VAULT.resolve():
            return pg
    return None


def connect(p):
    ws = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))["webSocketDebuggerUrl"]
    return p.chromium.connect_over_cdp(ws)


def open_vault(b):
    pg = find(b)
    if pg:
        return pg
    other = _pages(b)[0]
    other.evaluate("(v) => require('electron').ipcRenderer.sendSync('vault-open', v, false)", str(VAULT))
    for _ in range(60):
        time.sleep(0.5)
        pg = find(b)
        if pg:
            pg.wait_for_function("() => window.app?.workspace?.layoutReady", polling=500, timeout=30000)
            return pg
    raise SystemExit("示例库窗口没打开")


@contextlib.contextmanager
def demo_page(open_if_needed=True):
    with sync_playwright() as p:
        b = connect(p)
        pg = open_vault(b) if open_if_needed else find(b)
        if pg is None:
            raise SystemExit("示例库没开")
        unemulate(pg)
        yield b, pg


def unemulate(pg):
    """Playwright 连上已有页面 / 页面重载后默认模拟浅色配色(prefers-color-scheme: light)：外观选「跟随系统」时窗口会被当成浅色
    (2026-11-03 用户选了跟随系统、系统是深色，窗口却一直是浅色)。取消模拟以后真实值若已是深色，媒体查询没有「变化」，
    Obsidian 收不到事件、停在浅色(app.changeTheme('system') 也不重新判断)→ 外观是「跟随系统」、脚本也没临时切外观时，
    先模拟成相反的一种再清掉，逼它触发两次变化，停在真实配色"""
    pg.emulate_media(color_scheme="null")
    cdp = pg.context.new_cdp_session(pg)
    try:
        cdp.send("Emulation.setEmulatedMedia", {"media": "", "features": []})
        pg.wait_for_timeout(300)
        if pg.evaluate("() => !!window.app?.vault && app.vault.getConfig('theme') === 'system' && window.__baTheme == null"):
            dark = pg.evaluate("() => matchMedia('(prefers-color-scheme: dark)').matches")
            cdp.send("Emulation.setEmulatedMedia", {"media": "", "features": [{"name": "prefers-color-scheme", "value": "light" if dark else "dark"}]})
            pg.wait_for_timeout(400)
            cdp.send("Emulation.setEmulatedMedia", {"media": "", "features": []})
            pg.wait_for_timeout(600)
    finally:
        cdp.detach()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    with demo_page() as (b, pg):
        print(pg.title(), pg.evaluate("[innerWidth, innerHeight, devicePixelRatio, document.body.className]"))
