# -*- coding: utf-8 -*-
"""字体对比：把候选字体临时放进示例库 _fonttest/，注入 @font-face + 覆盖 --ba-font-* 变量，
在真笔记里截同一段(H1 横幅 / H2 / 引用 / H3 / 列表)，拼成对比图。截完删掉临时文件夹和注入的样式"""
import base64
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"E:\AI工作\obsidian-blood-angels\tools")
from obs import demo_page  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "preview" / "fonttest"      # 候选字体(gitignore；LXGW 文楷 / 朱雀仿宋 GitHub release，西文 Google Fonts)
VAULT = ROOT / "demo-vault"
TMP = VAULT / "_fonttest"
OUT = ROOT / "preview" / "字体对比"
OUT.mkdir(parents=True, exist_ok=True)

PUNCT = '"BA CJK Punct"'
NOTO = '"Noto Serif SC", "BA Noto Serif SC"'
CJK = {
    "noto": NOTO,
    "huiwen": '"Huiwen-mincho", "汇文明朝体", ' + NOTO,
    "wenkai": '"FT WenKai", ' + NOTO,
    "zhuque": '"FT Zhuque", ' + NOTO,
}
LAT = {
    "ebg": '"BA Garamond"', "cormorant": '"BA Cormorant"', "cinzel": '"BA Cinzel"',
    "fell": '"FT Fell"', "playfair": '"FT Playfair"', "cardo": '"FT Cardo"', "crimson": '"FT Crimson"',
    "spectral": '"FT Spectral"', "fraktur": '"FT Fraktur"',
}
# (文件名, 标题, 正文西文, 标题西文, 正文中文, 标题中文, 笔记, 只给 H1 用的字体)
COMBOS = {
    "zh": [
        ("zh1", "思源宋体(现在)", "ebg", "cormorant", "noto", "noto"),
        ("zh2", "汇文明朝体(本机已装)", "ebg", "cormorant", "huiwen", "huiwen"),
        ("zh3", "霞鹜文楷", "ebg", "cormorant", "wenkai", "wenkai"),
        ("zh4", "朱雀仿宋正文 + 思源宋体标题", "ebg", "cormorant", "zhuque", "noto"),
    ],
    "head": [
        ("h1", "Cormorant Garamond(现在)", "ebg", "cormorant", "noto", "noto"),
        ("h2", "Cinzel 罗马碑刻大写", "ebg", "cinzel", "noto", "noto"),
        ("h3", "IM Fell English 巴洛克印本", "ebg", "fell", "noto", "noto"),
        ("h4", "Playfair Display", "ebg", "playfair", "noto", "noto"),
        ("h5", "UnifrakturCook 哥特体(只用于 H1 横幅)", "ebg", "cormorant", "noto", "noto", "fraktur"),
    ],
    "body": [
        ("b1", "EB Garamond(现在)", "ebg", "cormorant", "noto", "noto"),
        ("b2", "Cardo", "cardo", "cormorant", "noto", "noto"),
        ("b3", "Crimson Pro", "crimson", "cormorant", "noto", "noto"),
        ("b4", "Spectral", "spectral", "cormorant", "noto", "noto"),
    ],
}
NOTES = {"zh": "幽林札记.md", "head": "The Dark Wood.md", "body": "The Dark Wood.md"}
FACES = [  # (family, file, weight, style)
    ("FT WenKai", "LXGWWenKai-Regular.ttf", "400", "normal"), ("FT WenKai", "LXGWWenKai-Medium.ttf", "500 900", "normal"),
    ("FT Zhuque", "ZhuqueFangsong-Regular.ttf", "100 900", "normal"),
]
for f in json.loads((SRC / "faces.json").read_text()):
    fam = {"IM Fell English": "FT Fell", "IM Fell English SC": None, "Playfair Display": "FT Playfair", "Cardo": "FT Cardo",
           "Crimson Pro": "FT Crimson", "UnifrakturCook": "FT Fraktur", "Spectral": "FT Spectral"}.get(f["family"])
    if fam:
        FACES.append((fam, f["file"], f["weight"], f["style"]))

if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir()
for _, fn, _, _ in FACES:
    shutil.copy2(SRC / fn, TMP / fn)

OPEN = """async ([note, y]) => {
  const w = app.workspace;
  let leaf = w.getLeavesOfType('markdown').find(l => l.view.file?.path === note);
  if (!leaf) { leaf = w.getMostRecentLeaf(); await leaf.openFile(app.vault.getAbstractFileByPath(note)); }
  w.setActiveLeaf(leaf, {focus: true});
  const st = leaf.getViewState(); st.state.mode = 'preview'; await leaf.setViewState(st);
  await new Promise(r => setTimeout(r, 500));
  const el = leaf.view.containerEl.querySelector('.markdown-preview-view');
  const h1 = [...el.querySelectorAll('h1')][0];
  el.scrollTop = h1 ? h1.offsetTop - 40 : y;
  await new Promise(r => setTimeout(r, 900));
  return el.scrollTop;
}"""


def css_for(c):
    _, _, lat, head, cjk, hcjk, *rest = c
    h1 = f'body.theme-light.ba-ft .markdown-rendered h1 {{ font-family: {PUNCT}, {LAT[rest[0]]}, {CJK[hcjk]}, serif; }}' if rest else ""
    faces = "\n".join(f'@font-face {{ font-family: "{fam}"; src: url("{{url:{fn}}}"); font-weight: {wt}; font-style: {sty}; font-display: block; }}'
                      for fam, fn, wt, sty in FACES)
    return (faces + f"\nbody.theme-light.ba-ft {{ --ba-font-latin: {LAT[lat]}; --ba-font-display-latin: {LAT[head]}; "
            f"--ba-font-cjk: {CJK[cjk]}; --ba-font-display: {PUNCT}, {LAT[head]}, {CJK[hcjk]}, serif; }}\n" + h1)


INJECT = """async (css) => {
  css = css.replace(/\\{url:([^}]+)\\}/g, (m, f) => app.vault.adapter.getResourcePath('_fonttest/' + f));
  let s = document.getElementById('ba-ft'); if (!s) { s = document.createElement('style'); s.id = 'ba-ft'; document.head.appendChild(s); }
  s.textContent = css; document.body.classList.add('ba-ft');
  await document.fonts.ready; await new Promise(r => setTimeout(r, 1200)); await document.fonts.ready;
  return [...document.fonts].filter(f => f.family.startsWith('"FT') || f.family.startsWith('FT')).map(f => f.family + ':' + f.status).slice(0, 4).join(',');
}"""
CLEAN = "() => { document.getElementById('ba-ft')?.remove(); document.body.classList.remove('ba-ft'); }"

LABEL = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 30)
try:
    with demo_page() as (b, pg):
        cdp = pg.context.new_cdp_session(pg)
        for group, combos in COMBOS.items():
            tiles = []
            for c in combos:
                pg.evaluate(OPEN, [NOTES[group], 0])
                print(c[0], pg.evaluate(INJECT, css_for(c)))
                pg.evaluate(OPEN, [NOTES[group], 0])          # 字体加载完再滚到 H1(先滚的话换字体后排版变了)
                box = pg.evaluate("""() => { const el = document.querySelector('.workspace-leaf.mod-active .markdown-preview-view');
                    const r = el.getBoundingClientRect(); return [r.x, r.y, r.width, r.height, devicePixelRatio]; }""")
                r = cdp.send("Page.captureScreenshot", {"format": "png"})
                im = Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")
                x, y, w, h, k = box
                im = im.crop((int((x + 40) * k), int(y * k), int((x + w - 40) * k), int((y + min(h, 760)) * k)))
                im.save(OUT / f"{c[0]}.png")
                tiles.append((c[1], im))
            cols = 2
            w, h = tiles[0][1].size
            rows = (len(tiles) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * w + (cols - 1) * 24, rows * (h + 56)), "white")
            dr = ImageDraw.Draw(sheet)
            for i, (name, im) in enumerate(tiles):
                x, y = (i % cols) * (w + 24), (i // cols) * (h + 56)
                dr.text((x + 6, y + 8), name, fill=(140, 20, 30), font=LABEL)
                sheet.paste(im, (x, y + 50))
            sheet.save(OUT / f"对比-{group}.png")
            print("sheet", group, sheet.size)
        pg.evaluate(CLEAN)
        pg.evaluate(OPEN, ["幽林札记.md", 0])
finally:
    shutil.rmtree(TMP, ignore_errors=True)
