# -*- coding: utf-8 -*-
"""在真 Obsidian 里截 README 用图(示例库 demo-vault/)，每张都日夜各截一遍。
准备：Obsidian 带调试端口启动(--remote-debugging-port=9222)，示例库开着、窗口在前台(被挡住时不出帧，脚本会停下)。
    python tools/readme_shots.py                      # 全部截图 + 拼图
    python tools/readme_shots.py ribbon anim-folder   # 只重截这几样(名字见 SHOTS)，再拼全部
    python tools/readme_shots.py compose              # 只用上次截下的原图重新拼(preview/_readme/)
- 英文图用英文界面 + The Dark Wood，中文图用中文界面 + 幽林札记。切界面语言要重载示例库窗口：先把布局读进内存并存盘，
  重载后原样写回；结束时还原语言和一开始的布局(当前标签、各标签的阅读 / 编辑模式)。
- 日夜：临时切外观(Moonstone / Obsidian)，结束还原(只在设置仍是脚本自己设的值时)。
- 截整篇笔记时临时把视口加高(宽度、缩放不变，排版和窗口里一样)，按段裁。
- 输出 docs/images/：cover(斜切拼图，左日右夜)、full-day / full-night(整窗)，其余是日夜并排的局部特写(左日右夜)；
  英文图 <名>.webp，中文图 <名>-zh.webp；screenshot.png = 商店缩略图(英文封面 512×288)。
- 动图(anim-*，动态 WebP)：CSS 动画按 Animation.setPlaybackRate 放慢录，日夜各录一遍、走同一条鼠标路线，按动画时间对齐后左右拼，
  鼠标指针画上去。大纲血线 / 侧栏按钮行 / 文件列表动态装饰 / 展开文件夹 + 悬停当前文件。
脚本只悬停、不点击；鼠标停回正文右侧空白。"""
import base64
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image                                     # noqa: E402
from obs import connect, find, unemulate                  # noqa: E402
from playwright.sync_api import sync_playwright           # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "images"
RAW = ROOT / "preview" / "_readme"
LANGS = ("en", "zh")
MODES = ("light", "dark")
NOTE = {"zh": "幽林札记.md", "en": "The Dark Wood.md"}
DEEP = {"zh": "附注：三韵体", "en": "Note: Terza Rima"}          # 大纲里悬停的深层标题(血线亮出)
GOLD = (194, 149, 99)                                           # 拼图接缝 = 夜间金
GUTTER = (58, 50, 46)

# 只切到那篇笔记(根区已有标签就激活它)，阅读视图、滚到顶
OPEN_JS = """async (note) => {
  const w = app.workspace; const leaves = [];
  const walk = n => n.children ? n.children.forEach(walk) : leaves.push(n);
  walk(w.rootSplit);
  let leaf = leaves.find(l => l.getViewState().state?.file === note);
  if (!leaf) { leaf = leaves.find(l => l.view?.getViewType() === 'markdown') || leaves[0]; await leaf.openFile(app.vault.getAbstractFileByPath(note)); }
  w.setActiveLeaf(leaf, {focus: false});
  await leaf.loadIfDeferred?.();
  const st = leaf.getViewState();
  if (st.state.mode !== 'preview') { st.state.mode = 'preview'; await leaf.setViewState(st); }
  await new Promise(r => setTimeout(r, 300));
  leaf.view.previewMode?.applyScroll?.(0);
  return 'ok';
}"""
EMPTY_JS = """async () => { const w = app.workspace; const leaves = []; const walk = n => n.children ? n.children.forEach(walk) : leaves.push(n);
  walk(w.rootSplit); const e = leaves.find(l => l.view.getViewType() === 'empty'); if (!e) return false;
  w.setActiveLeaf(e, {focus: false}); await new Promise(r => setTimeout(r, 600)); return true; }"""
MODE_JS = """async (m) => { const want = m === 'dark' ? 'obsidian' : 'moonstone';
  if (!document.body.classList.contains('theme-' + m)) {
    if (window.__baTheme == null) window.__baTheme = app.vault.getConfig('theme');
    app.changeTheme(want); window.__baThemeSet = want;
  }
  await new Promise(r => setTimeout(r, 900)); await document.fonts.ready; await new Promise(r => setTimeout(r, 600));
  return document.body.className.match(/theme-\\w+/)[0]; }"""
MODE_RESTORE_JS = """async () => { let note = 'untouched';
  if (window.__baTheme != null) {
    if (app.vault.getConfig('theme') === window.__baThemeSet) { app.changeTheme(window.__baTheme); note = 'restored'; }
    else note = 'user changed it, left alone';
    delete window.__baTheme; delete window.__baThemeSet;
  }
  await new Promise(r => setTimeout(r, 600)); return note; }"""
FPS_JS = """async () => Promise.race([(async () => { const t = []; let last = performance.now();
  for (let i = 0; i < 40; i++) { await new Promise(r => requestAnimationFrame(r)); const n = performance.now(); t.push(n - last); last = n; }
  t.sort((a, b) => a - b); return 1000 / t[20]; })(), new Promise(r => setTimeout(() => r(0), 4000))])"""
BLOCKS_JS = """() => {
  const v = document.querySelector('.workspace-leaf.mod-active .markdown-reading-view .markdown-preview-sizer');
  const r0 = v.getBoundingClientRect();
  const blocks = [...v.children].map(e => { const r = e.getBoundingClientRect();
    return {cls: e.className, top: r.top, bottom: r.bottom, img: !!e.querySelector('img')}; });
  const callouts = [...v.querySelectorAll(':scope > .el-div > .callout')].map(e => { const r = e.getBoundingClientRect();
    return [r.x, r.y, r.width, r.height, e.dataset.calloutFold || '']; });
  const vh = document.querySelector('.workspace-leaf.mod-active .view-header').getBoundingClientRect();
  return {left: r0.left, width: r0.width, blocks, callouts, viewHeaderBottom: vh.bottom,
          scrollH: v.closest('.markdown-preview-view').scrollHeight};
}"""


class Obs:
    def __init__(self, p):
        self.b = connect(p)
        self.pg = find(self.b)
        if self.pg is None:
            raise SystemExit("示例库没开")
        self.cdp = self.pg.context.new_cdp_session(self.pg)
        self.unemulate()
        self.lang0 = self.js("localStorage.getItem('language') || 'en'")
        self.layout0 = self.js("() => app.workspace.getLayout()")
        self.native = self.js("[innerWidth, innerHeight, devicePixelRatio]")
        self.mouse_pt = None

    def js(self, code, arg=None):
        return self.pg.evaluate(code, arg)

    def tall(self, h):
        w, _, dpr = self.native
        self.cdp.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": dpr, "mobile": False})
        self.pg.wait_for_timeout(1500)

    def normal(self):
        self.cdp.send("Emulation.clearDeviceMetricsOverride")
        self.pg.wait_for_timeout(800)

    def grab(self, clip=None):
        """整窗截图后在本地裁(带 clip 截图时 Chromium 会临时改视口、重排，悬停状态会被清掉)"""
        if self.mouse_pt:
            self.cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": self.mouse_pt[0], "y": self.mouse_pt[1], "button": "none"})
        r = self.cdp.send("Page.captureScreenshot", {"format": "png"})
        im = Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")
        return im if clip is None else self.crop(im, clip)

    def crop(self, im, clip):
        d = im.width / self.js("innerWidth")
        x, y, w, h = clip
        return im.crop((max(0, round(x * d)), max(0, round(y * d)), min(im.width, round((x + w) * d)), min(im.height, round((y + h) * d))))

    def move(self, x, y):
        self.mouse_pt = (x, y)
        self.cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none"})

    def hold(self, ms):
        for _ in range(max(1, ms // 50)):
            self.cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": self.mouse_pt[0], "y": self.mouse_pt[1], "button": "none"})
            self.pg.wait_for_timeout(50)

    def box(self, sel, nth=0):
        b = self.js("([s, n]) => { const e = [...document.querySelectorAll(s)].filter(x => x.offsetParent)[n]; if (!e) return null; "
                    "const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }", [sel, nth])
        if b is None:
            raise RuntimeError(f"找不到 {sel} #{nth}")
        return b

    def rest(self):
        """鼠标停在正文右侧空白(不触发任何悬停)"""
        x, y, w, h = self.js("() => { const r = app.workspace.rootSplit.containerEl.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }")
        self.move(x + w - 60, y + h / 2)

    def fps_ok(self):
        f = self.js(FPS_JS)
        if f < 30:
            raise SystemExit(f"帧率 {f:.0f}：示例库窗口可能被挡住了，请把它放到前台再跑")

    def set_lang(self, lang):
        """Obsidian 界面语言(localStorage language)。改完重载示例库窗口：布局先读进内存并存盘、等写完再重载
        (重载时正好在写 workspace.json 会被截断，Obsidian 就换成默认布局)，重载后用内存里这份写回去"""
        cur = self.js("localStorage.getItem('language') || 'en'")
        if cur == lang:
            return
        layout = self.js("""async (l) => { const w = app.workspace; const lay = w.getLayout(); await w.saveLayout();
                             await new Promise(r => setTimeout(r, 1500)); localStorage.setItem('language', l); return lay; }""", lang)
        self.pg.reload()
        self.pg.wait_for_function("window.app && app.workspace && app.workspace.layoutReady", polling=500, timeout=30000)
        self.pg.wait_for_timeout(1500)
        self.js("async (lay) => { await app.workspace.changeLayout(lay); }", layout)
        self.pg.wait_for_timeout(2500)
        self.unemulate()

    def unemulate(self):
        """取消 Playwright 的浅色配色模拟(同 obs.unemulate；外观是「跟随系统」时逼 Obsidian 按真实系统配色重新套)"""
        unemulate(self.pg)


def save_raw(im, lang, mode, name):
    p = RAW / lang / mode / f"{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)


def save_rect(rect, lang, mode, name):
    """日夜裁切框不一样大的图(功能栏：夜间纸带末端烧边多 24px)存整窗 + 裁切框，拼图时取两种模式的并集一起裁"""
    p = RAW / lang / mode / f"{name}.json"
    p.write_text(json.dumps(rect), encoding="utf-8")


def heading_box(o, text):
    return o.js("""(t) => { const e = [...document.querySelectorAll('.workspace-leaf-content[data-type="outline"] .tree-item-self')]
                  .find(x => x.querySelector('.tree-item-inner')?.textContent.trim() === t);
                  if (!e) return null; const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }""", text)


# ---------------------------------------------------------------- 静态图(一种语言、一种模式)
def shot_full(o, lang, mode):
    save_raw(o.grab(), lang, mode, "full")


def shot_full_plain(o, lang, mode):
    """「简洁」侧栏布局的整窗(默认是书签卡片)：临时换 body 类，局部关系图跟着重建一遍，截完还原"""
    keep = o.js("() => [...document.body.classList].filter(c => c === 'ba-sidebar-ribbon' || c === 'ba-sidebar-plain')")
    try:
        o.js("() => { document.body.classList.remove('ba-sidebar-ribbon'); document.body.classList.add('ba-sidebar-plain'); }")
        o.js("""async () => { for (const l of app.workspace.getLeavesOfType('localgraph')) await l.rebuildView();
                              await new Promise(r => setTimeout(r, 500)); app.workspace.trigger('file-open', app.workspace.getActiveFile()); }""")
        o.rest()
        o.pg.wait_for_timeout(4500)
        save_raw(o.grab(), lang, mode, "full-plain")
    finally:
        o.js("(k) => { document.body.classList.remove('ba-sidebar-ribbon', 'ba-sidebar-plain'); document.body.classList.add(...k); }", keep)
        o.js("""async () => { for (const l of app.workspace.getLeavesOfType('localgraph')) await l.rebuildView();
                              await new Promise(r => setTimeout(r, 500)); app.workspace.trigger('file-open', app.workspace.getActiveFile()); }""")
        o.pg.wait_for_timeout(3000)


def shot_note(o, lang, mode):
    """整篇笔记：视口加高到放得下全文，按段裁；Callout 整段裁"""
    h = o.js(BLOCKS_JS)["scrollH"]
    o.tall(int(h + 400))
    o.js(OPEN_JS, NOTE[lang])
    o.rest()
    o.pg.wait_for_timeout(3500)                         # 等 Mermaid、公式、图片渲染完
    d = o.js(BLOCKS_JS)
    bl = d["blocks"]
    x, w = d["left"] - 40, d["width"] + 80
    cls = [b["cls"].split()[0] if b["cls"] else "" for b in bl]

    def idx(c, start=0):
        return next(i for i in range(start, len(bl)) if cls[i] == c)
    h1, h2, h4, h6, hr = idx("el-h1"), idx("el-h2"), idx("el-h4"), idx("el-h6"), idx("el-hr")
    img = next(i for i, b in enumerate(bl) if b["img"])
    img_h = max(i for i in range(img) if cls[i] == "el-h2")
    foot = max(i for i, c in enumerate(cls) if c == "el-section")
    header = next(i for i, b in enumerate(bl) if "mod-header" in b["cls"])
    tasks = max(i for i in range(h2, h4) if cls[i] == "el-p")     # 「This week:」那段，后面是全部状态的任务清单
    cuts = [("note-title", max(bl[header]["top"] - 24, d["viewHeaderBottom"] + 1), bl[h1 + 1]["bottom"] + 24),
            ("note-lists", bl[h2]["top"] - 24, bl[tasks - 1]["bottom"] + 24),
            ("note-tasks", bl[tasks]["top"] - 16, bl[h4 - 1]["bottom"] + 24),
            ("note-table", bl[h4]["top"] - 24, bl[h6 + 1]["bottom"] + 24),
            ("note-code", bl[hr]["top"] - 10, bl[img_h - 1]["bottom"] + 24),
            ("note-media", bl[img_h]["top"] - 24, bl[foot]["bottom"] + 24)]
    full = o.grab()
    for name, y0, y1 in cuts:
        save_raw(o.crop(full, (x, y0, min(w, 760) if name == "note-tasks" else w, y1 - y0)), lang, mode, name)
    # Callout：前 14 个(不含最后那个可折叠的)在笔记里本来就是连着的，整段裁下来(间距、底色都是笔记里原样)
    cs = [c for c in d["callouts"] if not c[4]][:14]
    pad = 14
    cx0, cx1 = min(c[0] for c in cs) - pad, max(c[0] + c[2] for c in cs) + pad
    save_raw(o.crop(full, (cx0, cs[0][1] - pad, cx1 - cx0, cs[-1][1] + cs[-1][3] + pad - (cs[0][1] - pad))), lang, mode, "callouts")
    o.normal()
    o.js(OPEN_JS, NOTE[lang])
    o.rest()
    o.pg.wait_for_timeout(1500)


def shot_sidebar(o, lang, mode):
    ls = o.box(".workspace-split.mod-left-split")
    save_raw(o.grab((ls[0], 0, ls[2], o.native[1])), lang, mode, "sidebar")


def shot_ribbon(o, lang, mode):
    """功能栏：鼠标贴左边让它滑出来，停在第一个图标上等提示框。存整窗 + 裁切框(日夜框不一样高，拼图时取并集)"""
    o.move(3, o.native[1] / 2)
    o.hold(900)
    bx, by, bw, bh = o.box(".workspace-ribbon.mod-primary .side-dock-ribbon-action")
    o.move(bx + bw / 2, by + bh / 2)
    o.hold(1600)
    rb = o.box(".workspace-ribbon.mod-primary .side-dock-actions")
    tip = o.js("(() => { const t = document.querySelector('.tooltip'); if (!t) return null; const r = t.getBoundingClientRect(); return [r.right, r.bottom]; })()")
    right = max(rb[0] + rb[2] + 60, (tip[0] + 16) if tip else 0)
    save_raw(o.grab(), lang, mode, "ribbon_full")
    save_rect([0, 0, right, rb[1] + rb[3] + 24], lang, mode, "ribbon")
    o.rest()
    o.hold(800)


def shot_outline(o, lang, mode):
    """大纲：悬停深层标题，血线亮出"""
    b = heading_box(o, DEEP[lang])
    if b is None:
        raise RuntimeError("大纲里没有 " + DEEP[lang])
    o.move(b[0] + min(b[2] / 2, 60), b[1] + b[3] / 2)
    o.hold(1500)
    vx, vy, vw, vh = o.box('.workspace-leaf-content[data-type="outline"]')
    save_raw(o.grab((vx - 10, vy - 46, vw + 20, vh + 56)), lang, mode, "outline")
    o.rest()


def shot_empty(o, lang, mode):
    if o.js(EMPTY_JS):
        o.rest()
        o.pg.wait_for_timeout(1200)
        lx, ly, lw, lh = o.box(".workspace-leaf.mod-active .workspace-leaf-content")
        x0, y0, w0, h0 = o.box(".workspace-leaf.mod-active .empty-state-container")
        save_raw(o.grab((lx, ly, lw, min(lh, y0 + h0 + 70 - ly))), lang, mode, "empty")   # 只裁新标签页本身(左右不带侧栏)
        o.js(OPEN_JS, NOTE[lang])
        o.rest()


def shot_settings(o, lang, mode):
    """Style Settings 设置页(本主题那一节展开)。1.14 的设置是单独弹出的窗口，连到新出来的那个窗口去截"""
    before = {id(x) for c in o.b.contexts for x in c.pages}
    o.js("() => { app.setting.open(); app.setting.openTabById('obsidian-style-settings'); }")
    o.pg.wait_for_timeout(1800)
    pops = [x for c in o.b.contexts for x in c.pages if id(x) not in before and x.url == "about:blank"]
    pop = pops[0] if pops else None
    if pop is None:   # 老版本：设置是同一窗口里的弹窗
        x0, y0, w0, h0 = o.box(".modal.mod-settings")
        save_raw(o.grab((x0 - 1, y0 - 1, w0 + 2, h0 + 2)), lang, mode, "settings")
    else:
        pcdp = pop.context.new_cdp_session(pop)
        dpr = pop.evaluate("devicePixelRatio")
        pcdp.send("Emulation.setDeviceMetricsOverride", {"width": 960, "height": 1040, "deviceScaleFactor": dpr, "mobile": False})
        pop.wait_for_timeout(800)
        was = pop.evaluate("""() => { const h = document.querySelector('.style-settings-heading[data-id="blood-angels"]');
                               if (!h) return null; const c = h.classList.contains('is-collapsed'); if (c) h.click(); return c; }""")
        pop.wait_for_timeout(1200)
        r = pcdp.send("Page.captureScreenshot", {"format": "png"})
        save_raw(Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB"), lang, mode, "settings")
        if was:   # 原来是收起的，收回去
            pop.evaluate("""() => document.querySelector('.style-settings-heading[data-id="blood-angels"]')?.click()""")
        pcdp.send("Emulation.clearDeviceMetricsOverride")
    o.js("() => app.setting.close()")
    o.pg.wait_for_timeout(800)


# ---------------------------------------------------------------- 动图(真 Obsidian 里放慢动画录，日夜各录一遍、同一条鼠标路线)
class Rec:
    """录帧：每帧整窗 JPEG 截图后本地裁 clip(带 clip 截图会清掉悬停)；CSS 动画 / 过渡按 rate 放慢，
    帧时间 = 实际经过时间 × rate(= 动画时间)，拼图时日夜两份按动画时间对齐重采样"""

    def __init__(self, o, clip, rate):
        self.o, self.clip, self.rate = o, clip, rate
        self.d = o.native[2]
        self.frames = []          # (动画时间 ms, 图, 鼠标 CSS 坐标或 None)

    def __enter__(self):
        self.o.cdp.send("Animation.enable")
        self.o.cdp.send("Animation.setPlaybackRate", {"playbackRate": self.rate})
        self.t, self.last = 0.0, time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.o.cdp.send("Animation.setPlaybackRate", {"playbackRate": 1})

    def snap(self, cursor=True):
        o = self.o
        if o.mouse_pt:      # 每帧补发一次鼠标事件，顶住真实鼠标对悬停状态的干扰
            o.cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": o.mouse_pt[0], "y": o.mouse_pt[1], "button": "none"})
        r = o.cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92})
        im = Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")
        x, y, w, h = self.clip
        d = self.d
        im = im.crop((round(x * d), round(y * d), round((x + w) * d), round((y + h) * d)))
        now = time.perf_counter()
        self.t += (now - self.last) * 1000 * self.rate
        self.last = now
        self.frames.append((self.t, im, o.mouse_pt if cursor else None))

    def hold(self, sec, cursor=True):
        end = time.perf_counter() + sec
        while time.perf_counter() < end:
            self.snap(cursor)

    def move_to(self, pt, steps=6, cursor=True):
        p0 = self.o.mouse_pt or pt
        for k in range(1, steps + 1):
            self.o.move(p0[0] + (pt[0] - p0[0]) * k / steps, p0[1] + (pt[1] - p0[1]) * k / steps)
            self.snap(cursor)


def save_anim_raw(rec, lang, mode, name):
    d = RAW / lang / mode / name
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.jpg"):
        f.unlink()
    meta = {"clip": rec.clip, "d": rec.d, "frames": []}
    for i, (t, im, cur) in enumerate(rec.frames):
        im.save(d / f"{i:04d}.jpg", quality=92)
        meta["frames"].append([t, cur])
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    print(f"  {name}: {len(rec.frames)} 帧，动画时间 {rec.frames[-1][0] / 1000:.1f}s")


THREAD = {"en": ["I. The Dark Wood", "The Gate of Hell", "The Three Beasts", "Who's Who in Cantos I–V", "Note: Terza Rima", "The Second Circle"],
          "zh": ["一、幽林", "地狱之门", "三兽", "前五曲人物", "附注：三韵体", "第二层"]}


def anim_thread(o, lang, mode):
    """大纲血线：鼠标在标题间移动，血线从父级流向悬停的标题"""
    vx, vy, vw, vh = o.box('.workspace-leaf-content[data-type="outline"]')
    clip = (vx - 10, vy - 46, vw + 20, min(vh, 400) + 56)
    pts = []
    for t in THREAD[lang]:
        b = heading_box(o, t)
        if b is None:
            raise RuntimeError("大纲里没有 " + t)
        pts.append((min(b[0] + b[2] - 50, vx + vw - 40), b[1] + b[3] / 2))
    start = (pts[0][0] + 30, vy + min(vh, 400) - 14)
    o.move(*start)
    o.hold(600)
    with Rec(o, clip, .35) as rec:
        rec.hold(2.0)
        for pt in pts:
            rec.move_to(pt, 3)
            rec.hold(1.6)
        rec.move_to(start, 3)
        rec.hold(2.6)
    save_anim_raw(rec, lang, mode, "anim-thread")
    o.rest()


def anim_wings(o, lang, mode):
    """侧栏按钮行：平时收成一对卷翼，悬停展开成按钮"""
    scroll0 = o.js("() => { const n = document.querySelector('.workspace-leaf-content[data-type=\"file-explorer\"] .nav-files-container'); const s = n.scrollTop; n.scrollTop = 0; return s; }")
    o.pg.wait_for_timeout(400)
    fx, fy, fw, _ = o.box('.workspace-leaf-content[data-type="file-explorer"] .nav-files-container')
    clip = (fx - 8, 0, fw + 16, fy + 170)
    rest = (fx + fw * .62, fy + 170 + 40)          # 从画面下面进来(悬停的那一行在画面外)
    nx, ny, nw, nh = o.box('.workspace-leaf-content[data-type="file-explorer"] > .nav-header')
    target = (nx + nw / 2 + 6, ny + nh / 2)
    o.move(*rest)
    o.hold(600)
    with Rec(o, clip, .2) as rec:
        rec.hold(2.5)
        rec.move_to(target, 6)
        rec.hold(7.0)
        rec.move_to(rest, 6)
        rec.hold(7.0)
    save_anim_raw(rec, lang, mode, "anim-wings")
    o.rest()
    o.js("(s) => { document.querySelector('.workspace-leaf-content[data-type=\"file-explorer\"] .nav-files-container').scrollTop = s; }", scroll0)


def anim_fall(o, lang, mode):
    """文件列表动态装饰：日间飘落羽毛、夜间灰烬与火星(鼠标不进画面)"""
    gx, gy, gw, gh = o.box(".workspace-split.mod-left-split .workspace-tabs")
    clip = (gx, gy, gw, min(gh, 470))
    o.rest()
    o.hold(400)
    with Rec(o, clip, .5) as rec:
        rec.hold(16.0, cursor=False)
    save_anim_raw(rec, lang, mode, "anim-fall")


FOLDER = "Journal"


def anim_folder(o, lang, mode):
    """文件夹展开时空心血滴灌满红色 + 悬停当前文件盖红蜡封。文件夹用文件列表的接口收起 / 展开(不点击)，录完还原折叠和滚动"""
    st = o.js("""(f) => { const fe = app.workspace.getLeavesOfType('file-explorer')[0].view; const nav = fe.containerEl.querySelector('.nav-files-container');
                 const it = fe.fileItems[f]; const s = {collapsed: it.collapsed, scroll: nav.scrollTop};
                 it.setCollapsed(true); return s; }""", FOLDER)
    o.pg.wait_for_timeout(700)
    # 把这个文件夹滚到列表顶上
    o.js("""(f) => { const fe = app.workspace.getLeavesOfType('file-explorer')[0].view; const nav = fe.containerEl.querySelector('.nav-files-container');
            const t = fe.fileItems[f].selfEl.getBoundingClientRect(); nav.scrollTop += t.top - nav.getBoundingClientRect().top - 6; }""", FOLDER)
    o.pg.wait_for_timeout(600)
    try:
        nx, ny, nw, nh = o.box('.workspace-leaf-content[data-type="file-explorer"] .nav-files-container')
        clip = (nx - 8, ny - 8, nw + 16, min(nh, 470) + 8)
        fb = o.js("(f) => { const r = app.workspace.getLeavesOfType('file-explorer')[0].view.fileItems[f].selfEl.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }", FOLDER)
        start = (nx + nw * .82, ny + min(nh, 470) - 24)
        folder_pt = (fb[0] + 70, fb[1] + fb[3] / 2)
        o.move(*start)
        o.hold(500)
        with Rec(o, clip, .4) as rec:
            rec.hold(1.5)
            rec.move_to(folder_pt, 6)
            rec.hold(1.2)
            o.js("(f) => app.workspace.getLeavesOfType('file-explorer')[0].view.fileItems[f].setCollapsed(false)", FOLDER)
            rec.hold(3.5)
            # 展开后当前文件被挤到画面下面：平滑滚到能看见它(像滚了一下滚轮)
            o.js("() => document.querySelector('.nav-file-title.is-active').scrollIntoView({block: 'nearest', behavior: 'smooth'})")
            rec.hold(1.6)
            ab = o.box(".nav-file-title.is-active")
            rec.move_to((ab[0] + 70, ab[1] + ab[3] / 2), 6)
            rec.hold(4.5)
            rec.move_to(start, 6)
            rec.hold(3.0)
        save_anim_raw(rec, lang, mode, "anim-folder")
    finally:
        o.js("""([f, s]) => { const fe = app.workspace.getLeavesOfType('file-explorer')[0].view;
                fe.fileItems[f].setCollapsed(s.collapsed); fe.containerEl.querySelector('.nav-files-container').scrollTop = s.scroll; }""", [FOLDER, st])
        o.rest()


# ---------------------------------------------------------------- 可选样式对比(Style Settings 里能切换的样式)
# 每组：key、截哪里(kind / crop)、各样式要挂的 body 类、这一组所有可能的类(切换前先摘掉)、列头文字。
# 用户：只拍有多种主题样式的组；「普通 / 一种美化」二选一的(朴素样式、粗体、标题装饰、徽记花边、侧栏布局、功能栏、Callout 图标)不拍
# 只临时改 body 类(和 Style Settings 挂的是同一批类)，不动插件存的设置；截完按原样还原
GROUPS = [
    dict(key="code", kind="note", crop="code", all=["ba-code-plate", "ba-code-cogitator"],
         opts=[["ba-code-plate"], ["ba-code-cogitator"]],
         labels={"zh": ["红头铭板", "沉思者"], "en": ["Red plate", "Cogitator"]}),
    dict(key="image", kind="note", crop="image", all=["ba-img-frame", "ba-img-vignette", "ba-img-native"],
         opts=[["ba-img-frame"], ["ba-img-vignette"], ["ba-img-native"]],
         labels={"zh": ["卡片花边", "印痕毛边", "原版"], "en": ["Flourish frame", "Grain fade", "Native"]}),
    dict(key="task", kind="note", crop="tasks", all=["ba-task-gem", "ba-task-seal", "ba-task-native"],
         opts=[["ba-task-gem"], ["ba-task-seal"], ["ba-task-native"]],
         labels={"zh": ["巴尔宝石", "蜡封", "原版"], "en": ["Baal gem", "Wax seal", "Native"]}),
    dict(key="outline", kind="outline", all=["ba-outline-thread", "ba-outline-marker", "ba-outline-native"],
         opts=[["ba-outline-thread"], ["ba-outline-marker"], ["ba-outline-native"]],
         labels={"zh": ["血线", "金线导轨", "原版"], "en": ["Blood thread", "Gold rail", "Native"]}),
]
GROUP_TITLES = {
    "code": ("代码块样式", "Code block style"), "image": ("图片边框", "Image frame"), "task": ("任务复选框", "Task checkboxes"),
    "callout-icons": ("Callout 图标与铭牌", "Callout icons and labels"), "properties": ("属性栏", "Properties box"),
    "title": ("标题下的战团徽与两侧花边", "Emblem and flourishes around the title"), "headings": ("标题装饰", "Heading ornaments"),
    "rule": ("分隔线", "Horizontal rule"), "bold": ("粗体颜色", "Bold colour"), "outline": ("大纲样式", "Outline style"),
    "sidebar": ("侧栏布局", "Sidebar layout"), "ribbon": ("功能栏样式", "Ribbon style"),
}

VAR_BOXES_JS = """() => {
  const v = document.querySelector('.workspace-leaf.mod-active .markdown-reading-view .markdown-preview-sizer');
  const box = e => { if (!e) return null; const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; };
  const kids = [...v.children];
  const first = sel => kids.find(e => e.matches(sel));
  const cs = [...v.querySelectorAll(':scope > .el-div > .callout')].slice(0, 3).map(box);
  const img = v.querySelector('img');
  return {sizer: box(v), code: box(kids.find(e => e.matches('.el-pre:not(.mod-frontmatter)') && e.querySelector('code[class*="language-"]'))),
          image: box(img), imgReady: !!img && img.complete && img.naturalHeight > 0,
          tasks: box(v.querySelector('ul.contains-task-list')), callouts: cs, props: box(v.querySelector('.metadata-container')),
          header: box(first('.mod-header')), hr: box(first('.el-hr')), intro: box(kids.find(e => e.matches('.el-p'))),
          h1: box(first('.el-h1')), h2: box(first('.el-h2')), h3: box(first('.el-h3')),
          scrollH: v.closest('.markdown-preview-view').scrollHeight};
}"""


def set_classes(o, group, k):
    o.js("([rm, add]) => { document.body.classList.remove(...rm); document.body.classList.add(...add); }", [group["all"], group["opts"][k]])


def var_tile(o, full, b, crop):
    """从加高视口的整篇笔记截图里裁一组样式要看的地方"""
    sx, _, sw, _ = b["sizer"]
    x, w = sx - 40, sw + 80
    if crop == "code":
        c = b["code"]
        return o.crop(full, (x, c[1] - 12, w, c[3] + 26))
    if crop == "image":
        c = b["image"]                                   # 图片本身，上下给花边 / 毛边留出地方(不带上一段和图注)
        return o.crop(full, (x, c[1] - 22, w, c[3] + 44))
    if crop == "tasks":
        c = b["tasks"]
        return o.crop(full, (x, c[1] - 16, min(w, 760), c[3] + 32))
    if crop == "callouts":
        cs = b["callouts"]
        return o.crop(full, (cs[0][0] - 14, cs[0][1] - 14, cs[0][2] + 28, cs[-1][1] + cs[-1][3] - cs[0][1] + 28))
    if crop == "props":
        c = b["props"]
        return o.crop(full, (x, c[1] - 50, w, c[3] + 100))
    if crop == "title":
        h, c = b["header"], b["props"]
        return o.crop(full, (x, h[1] - 10, w, c[1] - h[1] - 10))
    if crop == "hr":
        c = b["hr"]
        return o.crop(full, (x, c[1] - 30, w, c[3] + 60))
    if crop == "intro":
        c = b["intro"]
        return o.crop(full, (x, c[1] - 16, w, c[3] + 32))
    if crop == "headings":   # 一到三级标题各裁一条，竖着拼
        parts = [o.crop(full, (x, c[1] - 14, w, c[3] + 28)) for c in (b["h1"], b["h2"], b["h3"])]
        out = Image.new("RGB", (parts[0].width, sum(t.height for t in parts)), parts[0].getpixel((4, 4)))
        y = 0
        for t in parts:
            out.paste(t, (0, y))
            y += t.height
        return out
    raise ValueError(crop)


def shot_variants(o, lang, mode):
    keep = o.js("() => [...document.body.classList]")
    every = sorted({c for g in GROUPS for c in g["all"]})
    try:
        notes = [g for g in GROUPS if g["kind"] == "note"]
        for k in range(max(len(g["opts"]) for g in notes)):
            for g in notes:
                set_classes(o, g, min(k, len(g["opts"]) - 1))
            o.pg.wait_for_timeout(600)
            h = o.js(VAR_BOXES_JS)["scrollH"]
            o.tall(int(h + 400))
            o.js(OPEN_JS, NOTE[lang])
            o.rest()
            o.pg.wait_for_timeout(3500)
            for _ in range(20):                      # 图片懒加载：等它载完再量
                b = o.js(VAR_BOXES_JS)
                if b["imgReady"]:
                    break
                o.pg.wait_for_timeout(500)
            o.pg.wait_for_timeout(600)
            b = o.js(VAR_BOXES_JS)
            full = o.grab()
            for g in notes:
                if k < len(g["opts"]):
                    save_raw(var_tile(o, full, b, g["crop"]), lang, mode, f"var-{g['key']}-{k}")
            o.normal()
        o.js("([rm, add]) => { document.body.classList.remove(...rm); document.body.classList.add(...add); }",
             [every, [c for c in keep if c in every]])
        o.js(OPEN_JS, NOTE[lang])
        o.rest()
        o.pg.wait_for_timeout(1500)
        for g in GROUPS:
            if g["kind"] == "note":
                continue
            for k in range(len(g["opts"])):
                set_classes(o, g, k)
                o.pg.wait_for_timeout(900)
                name = f"var-{g['key']}-{k}"
                if g["kind"] == "outline":
                    hb = heading_box(o, DEEP[lang])
                    o.move(hb[0] + min(hb[2] / 2, 60), hb[1] + hb[3] / 2)
                    o.hold(1500)
                    vx, vy, vw, vh = o.box('.workspace-leaf-content[data-type="outline"]')
                    save_raw(o.grab((vx - 10, vy - 46, vw + 20, vh + 56)), lang, mode, name)
                elif g["kind"] == "sidebar":
                    o.rest()
                    o.hold(600)
                    ls = o.box(".workspace-split.mod-left-split")
                    save_raw(o.grab((ls[0], 0, ls[2], o.native[1])), lang, mode, name)
                elif g["kind"] == "ribbon":
                    o.move(3, o.native[1] / 2)
                    o.hold(900)
                    bx, by, bw, bh = o.box(".workspace-ribbon.mod-primary .side-dock-ribbon-action")
                    o.move(bx + bw / 2, by + bh / 2)
                    o.hold(1600)
                    rb = o.box(".workspace-ribbon.mod-primary .side-dock-actions")
                    save_raw(o.grab(), lang, mode, name + "_full")
                    save_rect([0, 0, rb[0] + rb[2] + 150, rb[1] + rb[3] + 24], lang, mode, name)
                o.rest()
            o.js("([rm, add]) => { document.body.classList.remove(...rm); document.body.classList.add(...add); }",
                 [g["all"], [c for c in keep if c in g["all"]]])
    finally:
        o.normal()
        o.js("([rm, add]) => { document.body.classList.remove(...rm); document.body.classList.add(...add); }",
             [every, [c for c in keep if c in every]])
        o.pg.wait_for_timeout(800)


SHOTS = {"full": shot_full, "full-plain": shot_full_plain, "note": shot_note, "sidebar": shot_sidebar, "ribbon": shot_ribbon, "outline": shot_outline,
         "anim-fall": anim_fall, "anim-wings": anim_wings, "anim-folder": anim_folder, "anim-thread": anim_thread,
         "empty": shot_empty, "settings": shot_settings, "variants": shot_variants}


def capture(o, lang, mode, only):
    o.js(OPEN_JS, NOTE[lang])
    # 局部关系图：切外观以后不一定重读颜色(会留着上一种模式的颜色)→ 重建视图；但重建 / 窗口重载以后，Obsidian 要等下一次
    # file-open 才把当前笔记标成 focused(之前画成普通笔记的棕色，不是红色)→ 补发一次 file-open。等力导向排稳
    o.js("""async () => { for (const l of app.workspace.getLeavesOfType('localgraph')) await l.rebuildView();
                          await new Promise(r => setTimeout(r, 500)); app.workspace.trigger('file-open', app.workspace.getActiveFile()); }""")
    o.rest()
    o.pg.wait_for_timeout(4500)
    o.fps_ok()
    for name, fn in SHOTS.items():
        if not only or name in only:
            fn(o, lang, mode)


# ---------------------------------------------------------------- 拼图
def load(lang, mode, name):
    return Image.open(RAW / lang / mode / f"{name}.png").convert("RGB")


def save_webp(im, name, quality=88):
    path = IMG / f"{name}.webp"
    im.save(path, "WEBP", quality=quality, method=6)
    print(f"{path.relative_to(ROOT)}  {im.width}x{im.height}  {path.stat().st_size // 1024} KB")


def diagonal(day, night, top=.60, bottom=.40, seam=2.0):
    """左日右夜，斜线分割(上端 x = top·W、下端 bottom·W)，接缝一道金线(两侧各 seam px 过渡)"""
    import numpy as np
    W, H = day.size
    y, x = np.mgrid[0:H, 0:W]
    d = x - (top * W + (bottom - top) * W * y / (H - 1))
    a = np.clip(d + .5, 0, 1)[..., None]
    out = np.asarray(day, np.float32) * (1 - a) + np.asarray(night, np.float32) * a
    line = np.clip(1 - np.abs(d) / seam, 0, 1)[..., None]
    out = out * (1 - line) + np.array(GOLD, np.float32) * line
    return Image.fromarray(out.round().astype(np.uint8))


def pair(day, night, gap=0):
    """左日右夜直接拼在一起(用户：不要中间的分隔条)"""
    h = max(day.height, night.height)
    out = Image.new("RGB", (day.width + night.width + gap, h), GUTTER)
    out.paste(day, (0, 0))
    out.paste(night, (day.width + gap, 0))
    return out


def union_pair(lang, name):
    """日夜裁切框不一样大：两张整窗按两个框的并集裁，拼出来一样高(缩放取截图时记下的窗口 devicePixelRatio)"""
    r = [json.loads((RAW / lang / m / f"{name}.json").read_text(encoding="utf-8")) for m in MODES]
    x0, y0 = min(a[0] for a in r), min(a[1] for a in r)
    x1, y1 = max(a[0] + a[2] for a in r), max(a[1] + a[3] for a in r)
    dpr = json.loads((RAW / "window.json").read_text(encoding="utf-8"))[2]
    box = (round(x0 * dpr), round(y0 * dpr), round(x1 * dpr), round(y1 * dpr))
    return pair(*(load(lang, m, f"{name}_full").crop(box) for m in MODES))


CURSOR = [(0, 0), (0, 17), (4.2, 13.2), (7, 19.6), (9.6, 18.5), (6.9, 12.2), (12.4, 12.2)]


def draw_cursor(im, x, y, s):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.polygon([(x + px * s, y + py * s) for px, py in CURSOR], fill=(250, 250, 250), outline=(0, 0, 0), width=max(1, round(s)))


def load_anim(lang, mode, name):
    d = RAW / lang / mode / name
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    return meta, [(t, d / f"{i:04d}.jpg", cur) for i, (t, cur) in enumerate(meta["frames"])]


def compose_anim(lang, name, step=50, quality=80):
    """日夜两份按动画时间对齐：每 step ms 取各自最近一帧，画上鼠标、左右拼；相邻相同的帧合并"""
    import bisect
    (ma, fa), (mb, fb) = load_anim(lang, "light", name), load_anim(lang, "dark", name)
    T = min(fa[-1][0], fb[-1][0])
    ta, tb = [f[0] for f in fa], [f[0] for f in fb]
    cache = {}

    def frame(meta, frames, i):
        key = (id(frames), i)
        if key not in cache:
            t, path, cur = frames[i]
            im = Image.open(path).convert("RGB")
            if cur:
                x, y, _, _ = meta["clip"]
                draw_cursor(im, (cur[0] - x) * meta["d"], (cur[1] - y) * meta["d"], meta["d"])
            cache[key] = im
        return cache[key]

    out = []
    t = 0.0
    while t <= T:
        ia, ib = max(0, bisect.bisect_right(ta, t) - 1), max(0, bisect.bisect_right(tb, t) - 1)
        if out and out[-1][0] == (ia, ib):
            out[-1][2] += step
        else:
            out.append([(ia, ib), pair(frame(ma, fa, ia), frame(mb, fb, ib)), step])
        t += step
    sfx = "" if lang == "en" else "-zh"
    path = IMG / f"{name}{sfx}.webp"
    out[0][1].save(path, "WEBP", save_all=True, append_images=[o[1] for o in out[1:]], duration=[round(o[2]) for o in out],
                   loop=0, quality=quality, method=4)
    print(f"{path.relative_to(ROOT)}  {out[0][1].width}x{out[0][1].height}  {len(out)} 帧  {path.stat().st_size // 1024} KB")


PAIRS = ("note-title", "note-lists", "note-tasks", "note-table", "note-code", "note-media", "callouts",
         "sidebar", "outline", "empty", "settings")
ANIMS = {"anim-thread": 50, "anim-wings": 50, "anim-fall": 80, "anim-folder": 50}     # 名字: 输出帧间隔 ms


_label_font = {}


def label_font(size, lang):
    """列头文字：中文用思源宋体子集(子集里没有西文字母)，英文用 EB Garamond(woff2 → 内存里转 ttf 给 PIL)"""
    key = (size, lang)
    if key not in _label_font:
        from fontTools.ttLib import TTFont
        from PIL import ImageFont
        f = TTFont(ROOT / "fonts" / ("NLNotoSerifSC-GB2312-VF.woff2" if lang == "zh" else "EBGaramond-normal-400_800-latin.woff2"))
        f.flavor = None
        buf = io.BytesIO()
        f.save(buf)
        _label_font[key] = ImageFont.truetype(io.BytesIO(buf.getvalue()), size)
    return _label_font[key]


LABEL_BG, LABEL_INK = (240, 231, 212), (61, 42, 31)


def compose_variants(lang):
    """每组一张：列 = 各样式(列头写名字)，上行日间、下行夜间，图块之间不留缝；同一行里矮的图块下面用它自己的底色补齐"""
    from PIL import ImageDraw
    dpr = json.loads((RAW / "window.json").read_text(encoding="utf-8"))[2]
    sfx = "" if lang == "en" else "-zh"
    for g in GROUPS:
        n = len(g["opts"])
        tiles = {}
        if g["kind"] == "ribbon":
            rects = [json.loads((RAW / lang / m / f"var-{g['key']}-{k}.json").read_text(encoding="utf-8"))
                     for m in MODES for k in range(n) if (RAW / lang / m / f"var-{g['key']}-{k}.json").exists()]
            if len(rects) < 2 * n:
                continue
            x1, y1 = max(a[0] + a[2] for a in rects), max(a[1] + a[3] for a in rects)
            box = (0, 0, round(x1 * dpr), round(y1 * dpr))
            for m in MODES:
                tiles[m] = [load(lang, m, f"var-{g['key']}-{k}_full").crop(box) for k in range(n)]
        else:
            if not all((RAW / lang / m / f"var-{g['key']}-{k}.png").exists() for m in MODES for k in range(n)):
                continue
            for m in MODES:
                tiles[m] = [load(lang, m, f"var-{g['key']}-{k}") for k in range(n)]
        W = max(t.width for m in MODES for t in tiles[m])
        L = round(44 * dpr)
        rows = []
        for m in MODES:
            H = max(t.height for t in tiles[m])
            row = Image.new("RGB", (W * n, H))
            for k, t in enumerate(tiles[m]):
                cell = Image.new("RGB", (W, H), t.getpixel((3, t.height - 3)))
                cell.paste(t, ((W - t.width) // 2, 0))
                row.paste(cell, (k * W, 0))
            rows.append(row)
        out = Image.new("RGB", (W * n, L + sum(r.height for r in rows)), LABEL_BG)
        d = ImageDraw.Draw(out)
        f = label_font(round((17 if lang == "zh" else 19) * dpr), lang)
        for k, text in enumerate(g["labels"][lang]):
            tw = d.textlength(text, font=f)
            d.text((k * W + (W - tw) / 2, L * .22), text, fill=LABEL_INK, font=f)
        y = L
        for r in rows:
            out.paste(r, (0, y))
            y += r.height
        save_webp(out, f"var-{g['key']}{sfx}")


def compose():
    IMG.mkdir(parents=True, exist_ok=True)
    for lang in LANGS:
        sfx = "" if lang == "en" else "-zh"
        if (RAW / lang / "dark" / "full.png").exists():
            day, night = load(lang, "light", "full"), load(lang, "dark", "full")
            cover = diagonal(day, night)
            save_webp(cover, "cover" + sfx)
            if lang == "en":
                cover.resize((512, 288), Image.LANCZOS).save(ROOT / "screenshot.png", optimize=True)
                print("screenshot.png  512x288")
            save_webp(day, "full-day" + sfx)
            save_webp(night, "full-night" + sfx)
        if (RAW / lang / "dark" / "full-plain.png").exists():
            save_webp(load(lang, "light", "full-plain"), "full-plain-day" + sfx)
            save_webp(load(lang, "dark", "full-plain"), "full-plain-night" + sfx)
        for name in PAIRS:
            if all((RAW / lang / m / f"{name}.png").exists() for m in MODES):
                save_webp(pair(load(lang, "light", name), load(lang, "dark", name)), name + sfx)
        if all((RAW / lang / m / "ribbon.json").exists() for m in MODES):
            save_webp(union_pair(lang, "ribbon"), "ribbon" + sfx)
        for name, step in ANIMS.items():
            if all((RAW / lang / m / name / "meta.json").exists() for m in MODES):
                compose_anim(lang, name, step)
        compose_variants(lang)


def main():
    args = set(sys.argv[1:])
    if "compose" in args:
        compose()
        return
    unknown = args - set(SHOTS)
    if unknown:
        raise SystemExit(f"不认识的图名：{sorted(unknown)}；可选 {list(SHOTS)}")
    with sync_playwright() as p:
        o = Obs(p)
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "window.json").write_text(json.dumps(o.native), encoding="utf-8")
        try:
            for lang in LANGS:
                o.set_lang(lang)
                try:
                    for mode in MODES:
                        print(lang, mode, o.js(MODE_JS, mode))
                        capture(o, lang, mode, args)
                finally:
                    print("mode", o.js(MODE_RESTORE_JS))
        finally:
            o.normal()
            o.set_lang(o.lang0)
            o.js("async (lay) => { await app.workspace.changeLayout(lay); }", o.layout0)
            o.pg.wait_for_timeout(1500)
            o.js("() => app.workspace.trigger('file-open', app.workspace.getActiveFile())")   # 局部关系图把当前笔记标回红色
            o.unemulate()
            o.rest()
    compose()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
