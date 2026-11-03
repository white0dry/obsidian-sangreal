# -*- coding: utf-8 -*-
"""Mermaid 配色检查(同 Nox Aeterna tools/mermaid_check.py)：在示例库新标签里打开「Mermaid 测试.md」(13 种图)，
视口临时加高截下每张图，拼成 preview/mermaid_check.png；结束时关掉自己开的标签、还原视口和原来的活动标签。
笔记只读不写(用户要求检查笔记常驻库里)。需要带调试端口启动的 Obsidian(tools/obs.py)。
用法: python tools/mermaid_check.py [--css 测试样式.css] [--only 0,1,2] [--out 文件名] [--dump]
--css 把样式注入页面(不用重建主题就能试)；--dump 把每张图里各类元素的计算颜色写到 preview/mermaid_dump.json"""
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "preview"
sys.path.insert(0, str(HERE))
from obs import demo_page  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
args = sys.argv[1:]


def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default


PATH = "Mermaid 测试.md"

OPEN = """async (path) => {
  const w = app.workspace;
  const f = app.vault.getAbstractFileByPath(path);
  if (!f) throw new Error('missing note: ' + path);
  window.__baMmPrev = w.getMostRecentLeaf();
  let leaf = w.getLeavesOfType('markdown').find(l => l.view.file?.path === path);
  window.__baMmOwn = !leaf;
  if (!leaf) { leaf = w.getLeaf('tab'); await leaf.openFile(f, {state: {mode: 'preview'}}); }
  window.__baMmLeaf = leaf;
  window.__baMmMode = leaf.getViewState().state.mode;
  w.setActiveLeaf(leaf, {focus: true});
  const st = leaf.getViewState();
  if (st.state.mode !== 'preview') { st.state.mode = 'preview'; await leaf.setViewState(st); }
  leaf.view.previewMode.rerender(true);
  await new Promise(r => setTimeout(r, 2500));
  leaf.view.previewMode.applyScroll(0);
  return 'ok';
}"""

CLEANUP = """async () => {
  const w = app.workspace, leaf = window.__baMmLeaf;
  if (leaf && window.__baMmOwn) leaf.detach();
  else if (leaf && window.__baMmMode !== 'preview') { const st = leaf.getViewState(); st.state.mode = window.__baMmMode; await leaf.setViewState(st); }
  if (window.__baMmPrev) w.setActiveLeaf(window.__baMmPrev, {focus: false});
  document.getElementById('ba-mt')?.remove();
  return w.rootSplit.children[0].children.map(l => l.view.getViewType() + ':' + (l.view.file?.basename || '')).join(' | ');
}"""

BOXES = """(path) => { const l = app.workspace.getLeavesOfType('markdown').find(l => l.view.file?.path === path);
  return [...l.view.containerEl.querySelectorAll('.markdown-reading-view .mermaid')].map(m => {
    const r = m.getBoundingClientRect(); const s = m.querySelector('svg');
    return [r.x, r.y, r.width, r.height, s?.getAttribute('aria-roledescription') || '?']; }); }"""

DUMP = r"""(path) => { const l = app.workspace.getLeavesOfType('markdown').find(l => l.view.file?.path === path);
  return [...l.view.containerEl.querySelectorAll('.markdown-reading-view .mermaid > svg')].map(s => {
  const seen = {};
  for (const e of s.querySelectorAll('*')) {
    const c = e.getAttribute('class'); const k = e.tagName + (c ? '.' + c.trim().split(/\s+/).join('.') : '');
    if (seen[k]) continue;
    const cs = getComputedStyle(e);
    seen[k] = [cs.fill, cs.stroke, ['text', 'tspan', 'SPAN', 'P'].includes(e.tagName) ? cs.color : '',
               e.getAttribute('fill') || '', e.getAttribute('style') || ''].join(' | ');
  }
  return [s.getAttribute('aria-roledescription'), seen]; }); }"""

INJECT = ("(c) => { let e = document.getElementById('ba-mt'); if (!c) { e?.remove(); return; }"
          " if (!e) { e = document.createElement('style'); e.id = 'ba-mt'; document.head.append(e); } e.textContent = c; }")

css = opt("--css")
with demo_page() as (b, pg):
    cdp = pg.context.new_cdp_session(pg)
    w, dpr = pg.evaluate("[innerWidth, devicePixelRatio]")

    def grab():
        r = cdp.send("Page.captureScreenshot", {"format": "png"})
        return Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")
    try:
        pg.evaluate(INJECT, Path(css).read_text(encoding="utf-8") if css else None)
        # 阅读视图是虚拟列表，视口加高才会把所有图都渲染出来
        cdp.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": 9000, "deviceScaleFactor": dpr, "mobile": False})
        pg.wait_for_timeout(1500)
        pg.evaluate(OPEN, PATH)
        pg.mouse.move(2, 8990)
        pg.wait_for_timeout(2500)
        if "--dump" in args:
            OUT.mkdir(exist_ok=True)
            (OUT / "mermaid_dump.json").write_text(json.dumps(pg.evaluate(DUMP, PATH), ensure_ascii=False, indent=1), encoding="utf-8")
        for _ in range(10):             # 版面还在变(图陆续渲染、虚拟列表重算高度)就等它稳定
            boxes = pg.evaluate(BOXES, PATH)
            full = grab()
            if pg.evaluate(BOXES, PATH) == boxes:
                break
            pg.wait_for_timeout(1000)
        d = full.width / w
        only = [int(i) for i in (opt("--only", "") or "").split(",") if i != ""]
        tiles = []
        for i, bx in enumerate(boxes):
            if only and i not in only:
                continue
            print(i, bx[4], [round(v) for v in bx[:4]])
            x, y, bw, bh = bx[0] - 12, bx[1] - 12, bx[2] + 24, bx[3] + 24
            tiles.append(full.crop((round(x * d), round(y * d), round((x + bw) * d), round((y + bh) * d))))
    finally:
        cdp.send("Emulation.clearDeviceMetricsOverride")
        pg.wait_for_timeout(800)
        print(pg.evaluate(CLEANUP))
if not tiles:
    raise SystemExit("没有截到 Mermaid 图(新库要先信任 Mermaid？)")
cols = 2 if len(tiles) > 2 else len(tiles)
cw = max(t.width for t in tiles)
rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
H = sum(max(t.height for t in r) + 8 for r in rows)
sheet = Image.new("RGB", (cw * cols + 8 * (cols - 1), H), (120, 90, 60))
y = 0
for r in rows:
    for c, t in enumerate(r):
        sheet.paste(t, (c * (cw + 8), y))
    y += max(t.height for t in r) + 8
OUT.mkdir(exist_ok=True)
out = OUT / (opt("--out", "mermaid_check") + ".png")
sheet.save(out)
print(out, sheet.size)
