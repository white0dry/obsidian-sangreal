# -*- coding: utf-8 -*-
"""组装 Sangreal · 圣杯主题(圣血天使风格；原工作名 Blood Angels)：src/theme.src.css + 内嵌字体 + SVG 装饰 → 仓库根目录 theme.css + manifest.json
用法:
  python build.py              # 只构建到仓库根目录
  python build.py --install    # 构建并复制到示例库 demo-vault/.obsidian/themes/<THEME_NAME>/
构建工具链沿用 Nox Aeterna(E:\\AI工作\\obsidian-night-lords)：字体分片内嵌、SVG 装饰 data URI、SVG 滤镜构建时栅格化、
Style Settings 双语。
"""
import base64
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import dark as DK  # noqa: E402
import ornaments as O  # noqa: E402
import ribbons as RB  # noqa: E402

THEME_NAME = "Sangreal"      # 2026-11-02 定名(原工作名 Blood Angels)；Style Settings id blood-angels、类名 / 变量前缀 ba- 不改，免得用户存的设置丢
VERSION = "1.0.1"
DIST = ROOT
# 缎带画法(第八版对比用)：True = 套色印章版(色块 + 纸色留白缝 + 印刷颗粒，见 ribbons.STAMP)；False = 第七版的深色描边版。
# 环境变量 BA_RIBBON=line / stamp 可临时切换(截对比图用)
import os  # noqa: E402
RIBBON_STAMP = os.environ.get("BA_RIBBON", "stamp") == "stamp"

# 内嵌字体: (Google family, 主题内别名, size-adjust, 只收这些子集, 只收这些字重)
FONT_MAP = {
    # 第五十三版(上架体积)：希腊字母两个分片(greek / greek-ext，约 84 KB)不再内嵌，希腊文落到后备字体
    "EB Garamond": ("BA Garamond", "112%", ("latin", "latin-ext"), None),
    "Cormorant Garamond": ("BA Cormorant", "116%", None, None),
    # 第十八版：标题西文(替换第十五版的 Cormorant SC)。92% = 大写 H 和 Cormorant SC 等高(标题字号是按它调的)
    "IM Fell English SC": ("BA Heading Latin", "92%", None, None),
}
# 同一个字体文件再起几个别名(不同 size-adjust)。第二十五版(用户：英文 H4–H6 还是很小)：小型大写除了首字母都只有大写一半高，
# 小一号的标题看着和正文小写差不多大；整体加大字号又会让中文过大 → H4–H6 用放大的西文别名，中文(寒蝉)不变
FONT_EXTRA_ALIAS = {"IM Fell English SC": [("BA Heading Latin L", "116%")]}
# 只有一个文件的家族：声明成 400–900，标题和拉丁小标签要几号字重都用它，也不会触发合成加粗
FONT_WEIGHT_DECL = {"IM Fell English SC": "400 900"}
# 构建时轮廓加粗(tools/embolden.py，字体单位；第十八版选了 +64，第二十版用户觉得 +36 更精致)。IM Fell 声明了保留字体名
# 'IM FELL English SC'，加粗版是修改版，内部名字改成别名
EMBOLDEN = {"IM Fell English SC": 36}


def font_bytes(f: dict) -> bytes:
    src = ROOT / "fonts" / f["file"]
    strength = EMBOLDEN.get(f["family"])
    if not strength:
        return src.read_bytes()
    import embolden
    out = ROOT / "assets" / "cache" / f"bold{strength}-{f['file']}"
    tool = ROOT / "tools" / "embolden.py"
    if not out.exists() or out.stat().st_mtime < max(src.stat().st_mtime, tool.stat().st_mtime):
        out.parent.mkdir(parents=True, exist_ok=True)
        embolden.embolden(src, out, strength, FONT_MAP[f["family"]][0])
    return out.read_bytes()
CJK_PUNCT_RANGE = "U+00B7, U+2014-2015, U+201C-201D, U+2026, U+2E3A"
CJK_PUNCT_RANGE_LITE = "U+00B7, U+2014-2015, U+2026, U+2E3A"


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


# SVG 内嵌不用 base64(第五十三版，上架体积：社区目录自动审查 theme.css 超过约 5 MiB 报错)：base64 比原文大三分之一，
# 里面再套的 base64 位图还会被编码第二遍。改成 URL 编码，只转义 % # " < > \ 和控制字符 / 非 ASCII，解出来就是原 SVG
SVG_SAFE = "".join(chr(c) for c in range(0x20, 0x7f) if chr(c) not in '%#"<>\\')
# 浮点误差拖出来的长小数(12.300000000000001)：6 位以上小数四舍五入到 4 位(SVG 单位里差不到万分之一)
FLOAT_NOISE = re.compile(r"-?\d+\.\d{6,}")


def _round4(m: re.Match) -> str:
    t = f"{float(m.group(0)):.4f}".rstrip("0").rstrip(".")
    return "0" if t in ("-0", "") else t


def svg_uri(svg: str) -> str:
    if DK.ON:      # 夜间那一遍(dark.mode)：装饰图里的颜色换成夜间色
        svg = DK.recolor_svg(svg)
    svg = FLOAT_NOISE.sub(_round4, svg)
    return f'url("data:image/svg+xml,{urllib.parse.quote(svg, safe=SVG_SAFE)}")'


def webp_uri(data: bytes) -> str:
    return f'url("data:image/webp;base64,{b64(data)}")'


def tone_webp(svg: str) -> bytes:
    """纸面色调(第五十三版，上架体积)：照旧按 1024 渲染，缩成 512 存，CSS 里照旧铺 1024px(浏览器放大回去)。
    低频斑驳、不透明度最高 9% / 18%，叠到页面上和 1024 原图最多差 3~4 级(0–255)，日夜两张各省一半多"""
    import io
    import raster as R
    from PIL import Image
    im = Image.open(io.BytesIO(R.render_webp(svg, 1024, 1024, lossless=True))).resize((512, 512), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=70, alpha_quality=70, method=6)
    return buf.getvalue()


def font_faces() -> str:
    faces = json.loads((ROOT / "fonts" / "faces.json").read_text(encoding="utf-8"))
    out = []
    for f in faces:
        if f["family"] not in FONT_MAP:
            continue
        alias, adjust, subsets, weights = FONT_MAP[f["family"]]
        if subsets and f["subset"] not in subsets:
            continue
        if weights and f["weight"] not in weights:
            continue
        data = font_bytes(f)
        for name, adj in [(alias, adjust)] + FONT_EXTRA_ALIAS.get(f["family"], []):
            out.append(
                "@font-face {\n"
                f'  font-family: "{name}";\n'
                f'  font-style: {f["style"]};\n'
                f'  font-weight: {FONT_WEIGHT_DECL.get(f["family"], f["weight"])};\n'
                "  font-display: block;\n"
                f"  size-adjust: {adj};\n"
                f'  src: url("data:font/woff2;base64,{b64(data)}") format("woff2");\n'
                f'  unicode-range: {f["unicode_range"]};\n'
                "}")
    # 中文标点(“”…—·)强制用思源宋体字形(子集来自 Nox Aeterna 的 tools/make_cjk_punct.py)
    punct = (ROOT / "fonts" / "NLCJKPunct-VF.woff2").read_bytes()
    out.append(
        "@font-face {\n"
        '  font-family: "BA CJK Punct";\n'
        "  font-style: normal;\n"
        "  font-weight: 200 900;\n"
        "  font-display: block;\n"
        f'  src: url("data:font/woff2;base64,{b64(punct)}") format("woff2");\n'
        f"  unicode-range: {CJK_PUNCT_RANGE};\n"
        "}")
    out.append(out[-1].replace('"BA CJK Punct"', '"BA CJK Punct Lite"').replace(CJK_PUNCT_RANGE, CJK_PUNCT_RANGE_LITE))
    # 中文正文：思源宋体 GB2312 子集同样不再内嵌(第五十二版发布前，3.5 MB)——字体栈先找本机装的思源宋体，
    # 再找可选片段 body_snippet 里的子集("BA Noto Serif SC")，都没有就是系统宋体
    # 中文标题(第五十二版，发布前减体积)：寒蝉活宋体不再内嵌(GB2312 子集 10 MB，占整个主题一半)，改用本机安装的——
    # 按全名 / PostScript 名只取 Regular 那一款，声明 100–900：标题几号字重都用它(本机装了 Bold 也不换，也不合成加粗)。
    # 不想装字体的用户打开附带的可选 CSS 片段(heading_snippet，字体名 "BA Heading Song"，字体栈里排在本机字体后面)。
    # 华文宋体同样取个别名(Style Settings「标题中文字体」)：它没有粗体，标题 600 / 700 字重时不让浏览器合成加粗
    for name, srcs in (("BA Chill", ("ChillHuoSong_F_Regular",)),
                       ("BA STSong", ("STSong", "STSongti-SC-Regular", "Songti SC Regular"))):
        src = ", ".join(f'local("{s}")' for s in srcs)
        out.append(
            "@font-face {\n"
            f'  font-family: "{name}";\n'
            "  font-style: normal;\n"
            "  font-weight: 100 900;\n"
            "  font-display: block;\n"
            f"  src: {src};\n"
            "}")
    # 新标签页题铭的哥特体 Manufacturing Consent 不再内嵌：第九版起文字烘进题铭位图(见 inscription_webp)
    return "/* ---- embedded fonts (OFL 1.1) ---- */\n" + "\n".join(out)


SNIPPET = ROOT / "snippets" / "sangreal-chinese-heading-font.css"
SNIPPET_BODY = ROOT / "snippets" / "sangreal-chinese-body-font.css"
SNIPPET_BODY_HEAD = """/* Sangreal · 圣杯 — optional Chinese body font / 可选的中文正文字体

   思源宋体 (Noto Serif SC), GB2312 subset (6,763 common characters, all weights). Use it if you would rather not
   install the font; if Noto Serif SC / Source Han Serif is installed, the theme uses the installed copy instead.
   不想安装字体时用它；本机已经装了思源宋体的话，主题直接用本机的，不需要这个片段。

   Install: put this file in <your vault>/.obsidian/snippets/, then go to
   Settings → Appearance → CSS snippets, reload the list and turn it on.
   安装：把这个文件放进 <你的库>/.obsidian/snippets/，再到「设置 → 外观 → CSS 代码片段」刷新列表并打开它。

   Font licence: SIL Open Font License 1.1 (https://openfontlicense.org). © 2017-2023 Adobe (http://www.adobe.com/).
   Named "BA Noto Serif SC" so it never hides a full copy installed on your system.
   Generated by build.py (tools/make_cjk_serif.py). */
"""
SNIPPET_HEAD = """/* Sangreal · 圣杯 — optional Chinese heading font / 可选的中文标题字体

   寒蝉活宋体 (ChillHuoSong) Regular, GB2312 subset. Use it if you would rather not install the font;
   if the font is installed, the theme uses the installed copy and this snippet is not needed.
   不想安装字体时用它；本机已经装了寒蝉活宋体的话，主题直接用本机的，不需要这个片段。

   Install: put this file in <your vault>/.obsidian/snippets/, then go to
   Settings → Appearance → CSS snippets, reload the list and turn it on.
   安装：把这个文件放进 <你的库>/.obsidian/snippets/，再到「设置 → 外观 → CSS 代码片段」刷新列表并打开它。

   Font licence: SIL Open Font License 1.1 (https://openfontlicense.org).
   © 2023 ChillType (https://github.com/Warren2060/ChillMovableType), with Reserved Font Name 'ChillHuoSong'.
   © 2017-2022 Adobe (http://www.adobe.com/), with Reserved Font Name 'Source'.
   This subset is a Modified Version and is named "BA Heading Song"; it does not use the Reserved Font Names.
   Generated by build.py (tools/make_cjk_heading.py). */
"""


def body_snippet() -> str:
    """可选 CSS 片段：思源宋体可变字体的 GB2312 子集(tools/make_cjk_serif.py，字重 200–900 全保留)"""
    song = (ROOT / "fonts" / "NLNotoSerifSC-GB2312-VF.woff2").read_bytes()
    return (SNIPPET_BODY_HEAD + "@font-face {\n"
            '  font-family: "BA Noto Serif SC";\n'
            "  font-style: normal;\n"
            "  font-weight: 200 900;\n"
            "  font-display: block;\n"
            f'  src: url("data:font/woff2;base64,{b64(song)}") format("woff2");\n'
            "}\n")


def heading_snippet() -> str:
    """可选 CSS 片段：寒蝉活宋体 Regular 的 GB2312 子集，按 unicode-range 切成几十片(tools/make_cjk_heading.py)——
    浏览器只解码页面上出现的字所在的那几片。声明 100–900：标题要几号字重都用这一个文件(不合成加粗)"""
    out = [SNIPPET_HEAD]
    for f in json.loads((ROOT / "fonts" / "heading-song" / "ranges.json").read_text(encoding="utf-8")):
        data = (ROOT / "fonts" / "heading-song" / f["file"]).read_bytes()
        out.append(
            "@font-face {\n"
            '  font-family: "BA Heading Song";\n'
            "  font-style: normal;\n"
            "  font-weight: 100 900;\n"
            "  font-display: block;\n"
            f'  src: url("data:font/woff2;base64,{b64(data)}") format("woff2");\n'
            f'  unicode-range: {f["unicode_range"]};\n'
            "}")
    return "\n".join(out) + "\n"


def ribbon_tex() -> tuple:
    """缎带的羊皮纸斑驳：(大块污斑 256 图 → 用的时候 512 一格, 细碎斑点 96 图)，WebP 字节"""
    import raster as R
    return (R.render_webp(O.tex_ribbon(), 256, 256, quality=60),
            R.render_webp(O.tex_ribbon_speck(), 96, 96, quality=70))


def ink_tex(size=256, **kw) -> bytes:
    """套色印章的印刷颗粒(灰度，当亮度遮罩用)：新标签页徽章、题铭、引用封印、印章版缎带共用"""
    import raster as R
    return R.render_webp(O.tex_ink(size, **kw), size, size, quality=80)


# 第九版(用户：新标签页颗粒太明显太粗糙，要减淡、做出柔和的区域磨损)：新标签页的徽章和题铭用原浓度的颗粒，
# 再乘磨损场(墨色饱满处颗粒显三成多，磨薄处九成、墨色也淡一点；一稿饱满处只有两成，用户嫌右侧绶带和血滴没纹理了)；没有磨损场的 H1 缎带和引用封印直接用淡一档的颗粒(约原来六成)
INK_LIGHT = dict(light=.26, fine=.12, dense=.035)


def turb_tile(size, freq, octaves, seed):
    """可无缝平铺的平滑噪声(feTurbulence stitchTiles)，灰度 0..1(两端各截 2% 再拉满)"""
    import io
    import numpy as np
    from PIL import Image
    import raster as R
    svg = (f'<svg {O.SVG} width="{size}" height="{size}"><filter id="t" x="0" y="0" width="100%" height="100%">'
           f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="{octaves}" seed="{seed}" stitchTiles="stitch"/>'
           '<feColorMatrix values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1"/></filter>'
           '<rect width="100%" height="100%" filter="url(#t)"/></svg>')
    g = np.asarray(Image.open(io.BytesIO(R.render_webp(svg, size, size, lossless=True))).convert("L"), np.float32) / 255
    lo, hi = np.percentile(g, (2, 98))
    return np.clip((g - lo) / (hi - lo), 0, 1)


def tag_grain(size=256, cream=(244, 230, 201)) -> bytes:
    """标签底色上的印刷质感(奶油色半透明小图，叠在红底上)。第十四版是整片均匀的漏白颗粒，
    第十五版(用户：颗粒太明显，让人不适、影响可读性)改成新标签页那套「区域磨损」：大尺度、过渡柔和的磨损场决定哪里磨薄，
    磨薄处才漏出稀疏的细颗粒(淡一档的印章颗粒)，再加一层很淡的浓淡；墨色饱满处几乎是干净的平涂"""
    import io
    import numpy as np
    import stamp as S
    from PIL import Image
    g = np.asarray(Image.open(io.BytesIO(ink_tex(size, **INK_LIGHT))).convert("L"), np.float32) / 255
    wv = S.smoothstep(.35, .85, turb_tile(size, .012, 2, 23))
    a = np.clip(.02 + .06 * wv + (1 - g) * (.12 + .55 * wv), 0, 1)
    rgba = np.dstack([np.full_like(a, c / 255) for c in cream] + [a])
    buf = io.BytesIO()
    Image.fromarray((rgba * 255).round().astype(np.uint8), "RGBA").save(buf, "WEBP", lossless=True, method=6)
    return buf.getvalue()


# 夜间新标签页的喷溅血渍(第五十二版)：画布大小(显示 px)、冲击点 = 杯口(::after 顶在徽章顶上 150px，杯口在徽章顶下约 175px)、
# 横 / 纵最远距离、构图种子和各部分数量 = 用户在小样里挑的 A(四面喷溅)
SPATTER = dict(W=1100, H=800, ox=550, oy=325, rx=520, ry=330, seed=7, rays=9, drops=150, mist=500, big=4,
               # 局部颜色渐变(用户比过整体 / 局部 / 两者，选局部；preview/夜间配色/血渍样本/血迹渐变_*.png)：每块边上一圈往深色靠、里面往亮色靠，
               # 再铺一层大尺度颜色起伏(一片鲜红一片暗褐，相邻血点不同色、大斑里有色差)
               local=dict(rim="#2a0306", rim_amt=.6, rim_w=1.2, core="#c8363c", core_amt=.5, patch=("#d43038", "#4a0a0e", .6, 40)))
SPATTER_TOP = 150          # 血渍 ::after 的顶比徽章 ::before 高多少(CSS 用 SIZE:spatter-top)
# 新标签页徽章 ::before 的两层背景：徽章显示高、题铭宽带正中上沿离 ::before 顶多远(CSS 用 SIZE:newtab-crest-h / inscr-band-top，
# 血渍按同样的位置排徽章算轮廓)
NEWTAB_CREST_H = 300
INSCR_BAND_TOP = 318.5
# 血渍让开徽章(第五十二版，用户：避开图案的精确范围，包括描边；外扩要和徽章最外一圈描边一样宽)：
# 描边 = 徽章各层之间的留白缝(newtab_crest gap 3.5 单位 × 300 / 350 = 3.0px)；清空到 2.5、3.5 处全显，过渡正中 3.0
SPATTER_AVOID = 2.5


def newtab_crest_alpha(crest, inscr, inscr_w, inscr_top, W, H, S):
    """新标签页徽章 ::before 的两层背景(徽章 + 题铭，位置和大小同 CSS)排进 W × H 的血渍框(::before 在框顶下 SPATTER_TOP、水平居中)，
    浏览器截透明底，返回不透明度(S 倍)。徽章有印刷磨损(大部分 0.5–0.95 不透明)、各层之间的留白缝全透明，血渍会从底下透出来"""
    import io
    import numpy as np
    import raster as R
    from PIL import Image
    html = ('<html><head><style>body { margin: 0; background: transparent; } '
            f'#c {{ position: absolute; left: {(W - inscr_w) / 2:g}px; top: {SPATTER_TOP}px; width: {inscr_w:g}px; height: {H - SPATTER_TOP}px; '
            f'background: {crest} center top / auto {NEWTAB_CREST_H}px no-repeat, {inscr} center top {inscr_top:g}px / {inscr_w:g}px auto no-repeat; }}'
            '</style></head><body><div id="c"></div></body></html>')
    png = R.render_html(html, W, H, S)
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"), np.float32)[..., 3] / 255


def spatter_webp(crest, inscr, inscr_w, inscr_top, S=2) -> bytes:
    """tools/spatter.py 画的血渍，2 倍位图(~75KB)；叠新标签页那套淡一档的印刷颗粒(256px 一格)，颗粒在 DK.raw() 里出
    (夜间那遍不给灰度颗粒换色)。crest / inscr = 夜间版徽章、题铭的 url()：血渍在徽章轮廓里和外扩 3px 以内抠掉(spatter.avoid)"""
    import io
    import numpy as np
    import spatter as SP
    from PIL import Image
    kw = dict(SPATTER)
    W, H = kw.pop("W"), kw.pop("H")
    with DK.raw():
        g = Image.open(io.BytesIO(ink_tex(256, **INK_LIGHT))).convert("L").resize((256 * S, 256 * S), Image.LANCZOS)
    g = np.asarray(g, np.float32) / 255
    ink = np.tile(g, (H * S // g.shape[0] + 1, W * S // g.shape[1] + 1))[:H * S, :W * S]
    rgba = SP.spatter(W, H, S=S, ink=ink, **kw)
    keep = SP.avoid(newtab_crest_alpha(crest, inscr, inscr_w, inscr_top, W, H, S), S, grow=SPATTER_AVOID)
    rgba[..., 3] = np.round(rgba[..., 3] * keep).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "WEBP", quality=82, alpha_quality=90, method=6)
    return buf.getvalue()


def ornaments() -> dict:
    import raster as R
    import stamp as S
    tx, sp = (f"data:image/webp;base64,{b64(d)}" for d in ribbon_tex())
    ink = "data:image/webp;base64," + b64(ink_tex())
    ink_l = "data:image/webp;base64," + b64(ink_tex(**INK_LIGHT))
    rk = ink_l if RIBBON_STAMP else None
    with DK.raw(DK.RIBBON_DAY):     # 夜间：新标签页题铭、标题徽记的绶带位图可以保持日间配色(dark.RIBBON_DAY)
        ins, iw, ih, iband = inscription_webp(text_ink=DK.INSCR_INK) if DK.ON and not DK.RIBBON_DAY else inscription_webp()
    cand, cand_w, cand_h = O.cog_candles(C_TAG, COG_FLAME)
    seal_ink = "data:image/webp;base64," + b64(ink_tex(128, **INK_LIGHT))
    ink_dark = "data:image/webp;base64," + b64(R.render_webp(O.tex_ink_dark(), 256, 256, quality=80))
    with DK.raw(DK.RIBBON_DAY):
        crest, crest_h = title_crest_svg(ink, ink_dark)
    # 标题两侧的花边(第十五版)：分割线同款的「∞」卷草 + 渐隐金线。第十三版的竖叶括号见 git 历史；
    # 叶子平躺的几种摆法(O.title_flourish ang=±72 / ±108)留着备选
    fl_l, fl_w, fl_h = O.title_rule_arm("left", "rule", ink=ink)
    fl_r, _, _ = O.title_rule_arm("right", "rule", ink=ink)
    d_gem = "data:image/webp;base64," + b64(R.render_webp(O.tex_ink_dark(op=.2), 256, 256, quality=80))
    props, props_c = O.props_frame()
    arm, arm_w, arm_h, _ = O.props_heading_arm()
    ntb_frame, ntb_fill, ntb_cap, ntb_h = O.newtab_btn_frame()
    img_frame, img_c = O.image_frame()
    img_grain = O.image_grain()
    t = {
        # 笔记标题下的徽记(第十版)：套色画法的战团徽 + 身后横穿的新标签页绶带(不带字)
        "ORN:emblem": svg_uri(crest),
        "SIZE:crest-h": f"{crest_h:.1f}px",
        "SIZE:crest-w": f"{TITLE_CREST['W']}px",
        # 标题两侧的卷草花边(第十二版)
        "ORN:flourish-l": svg_uri(fl_l),
        "ORN:flourish-r": svg_uri(fl_r),
        "SIZE:fl-w": f"{fl_w:.1f}px",
        "SIZE:fl-h": f"{fl_h:.1f}px",
        # H1 横幅：正面宽带(一张拉伸的 SVG) + 两端(用户给的 f0208 绶带的燕尾 + 卷边)，都叠斑驳纹理(印章版叠印刷颗粒)
        # 两端燕尾在宽带下沿切成两段(第三十七版)：上段随宽带纵向拉高，下段卷边原尺寸
        "ORN:tail-l-top": svg_uri(RB.tail("left", tx, sp, ink=rk, part="top")),
        "ORN:tail-l-bot": svg_uri(RB.tail("left", tx, sp, ink=rk, part="bottom")),
        "ORN:tail-r-top": svg_uri(RB.tail("right", tx, sp, ink=rk, part="top")),
        "ORN:tail-r-bot": svg_uri(RB.tail("right", tx, sp, ink=rk, part="bottom")),
        "ORN:band": svg_uri(RB.band_svg(sag=7, tex=tx, speck=sp, ink=rk)),
        "ORN:rule": svg_uri(O.rule_center(ink=ink_l)),
        "ORN:h2": svg_uri(O.baal_gem(ink=ink, ink_dark=d_gem, glint=DK.GEM_GLINT if DK.ON else None)),
        "ORN:h3": svg_uri(O.sun_halo_small()),
        # 滚动条滑块两头(第二十五版：笔锋 B；ornaments.SB_STYLE 可换回燕尾)：平时 75%、悬停 / 拖动 92% 的标签红
        "SIZE:sb-cap": O.SB_CAP_LEN[O.SB_STYLE],
        **{f"ORN:sb-{e}": svg_uri(O.scrollbar_cap(e)) for e in ("top", "bottom", "left", "right")},
        **{f"ORN:sb-{e}-h": svg_uri(O.scrollbar_cap(e, alpha=.92)) for e in ("top", "bottom", "left", "right")},
        # 代码块(第二十七版)：铭牌上的机械教徽(红头铭板 / 沉思者同一种奶白 = --tag-color)、沉思者的蜡烛、
        # 沉思者黑屏幕里的羊皮纸色滚动条两头(平时 85%、悬停 / 拖动 97%)、阅读视图行号栏的数字串
        "ORN:mech": svg_uri(O.mechanicus(C_TAG)),
        "ORN:cog-candles": svg_uri(cand),
        "SIZE:cog-candles-w": f"{cand_w:.2f}px",
        "SIZE:cog-candles-h": f"{cand_h:.2f}px",
        **{f"ORN:sb-{e}-p": svg_uri(O.scrollbar_cap(e, C_PARCH, .85)) for e in ("top", "bottom", "left", "right")},
        **{f"ORN:sb-{e}-ph": svg_uri(O.scrollbar_cap(e, C_PARCH, .97)) for e in ("top", "bottom", "left", "right")},
        "SIZE:code-nums": '"' + "\\A ".join(str(i) for i in range(1, CODE_NUMS + 1)) + '"',
        "ORN:hl-brush": svg_uri(O.highlight_brush2()),   # 高亮的金色刷痕(第二十版：九宫格，两端定宽、中段平铺)
        # callout 四角(第十九版)：f1527_0 的卷草花角，左上角镜像出四个，CSS 当遮罩、铺类型颜色
        **{f"ORN:co-{c}": svg_uri(O.callout_corner("f1527_0", c, 50)) for c in ("tl", "tr", "bl", "br")},
        "ORN:bul1": svg_uri(O.bullet_drop()),
        "ORN:bul2": svg_uri(O.bullet_drop_hollow()),
        "ORN:pin-aquila": svg_uri(O.aquila()),     # 锁定标签的图标
        # 侧栏按钮行收起后的一对翅膀(第四十版，Lorc curly-wing 左右翻转相接；遮罩)，CSS 里 contain 进 32×16 的盒子
        "ORN:nav-wings": svg_uri(O.nav_wings()[0]),
        # 侧栏「书签卡片」布局的当前标签丝带(第四十一版)：遮罩 + 光泽(两边金线)
        "ORN:tab-ribbon": svg_uri(O.tab_ribbon()[0]),
        "ORN:tab-ribbon-sheen": svg_uri(O.tab_ribbon()[1]),
        "ORN:seal-emblem": svg_uri(O.task_seal(O.TASK_SEAL_DONE)),   # 文件列表悬停当前文件时盖的蜡封(同复选框打勾那枚)
        # 引文封印分两层：蜡 / 纸条(纸条被引文高度裁切，一行时只露蜡，见 CSS 引用块)
        "ORN:seal-wax": svg_uri(O.purity_seal(ink=seal_ink, part="wax", logo=DK.SEAL_LOGO if DK.ON else None)),
        "ORN:seal-strips": svg_uri(O.purity_seal(ink=seal_ink, part="strips")),
        # 左侧功能栏「纯洁印记」(第四十八版)：蜡封 + 纸条整张形状(遮罩 / 投影剪影，投影色同设计稿)
        "ORN:rb-seal": svg_uri(O.ribbon_seal(seal_ink, logo=DK.SEAL_LOGO if DK.ON else None)),
        "ORN:rb-strip": svg_uri(O.ribbon_strip()),
        "ORN:rb-strip-shadow": svg_uri(O.ribbon_strip("#5c3a1a")),
        "SIZE:rb-seal-d": f"{O.RB_SEAL_D}px",
        # 夜间功能栏纸带末端的烧痕(只有夜间规则用)：烧边形状的遮罩 / 投影剪影 + 烧痕位图(钉在底边)
        "ORN:rb-strip-burnt": svg_uri(DK.rb_strip_burnt()),
        "ORN:rb-strip-burnt-shadow": svg_uri(DK.rb_strip_burnt("#000")),
        "RASTER:rb-char": webp_uri(DK.rb_char_webp()),
        "SIZE:rb-char": f"{O.RB_SEAL_D}px {DK.RB_CHAR_H}px",
        "ORN:ext": svg_uri(O.ext_arrow()),
        # 属性栏花框(第二十七版十稿 A)：九宫格切片 = 角上整组装饰的范围；右侧栏属性面板里整套缩到 PROPS_SIDE；
        # 折叠时上下留白加大(框矮于 2C 时四角会按比例缩小)；标题「笔记属性」两侧的卷草花边(窄的时候 CSS 里缩短)
        "ORN:props-frame": svg_uri(props),
        "SIZE:props-slice": f"{props_c}",
        "SIZE:props-c": f"{props_c}px",
        "SIZE:props-c-side": f"{props_c * PROPS_SIDE:.1f}px",
        "SIZE:props-side-pad": f"{42 * PROPS_SIDE + 6:.0f}px 20px {36 * PROPS_SIDE + 6:.0f}px",
        "SIZE:props-coll": f"{props_c * .9 - 13.6:.0f}px",
        "ORN:props-arm": svg_uri(arm),
        "SIZE:props-arm-w": f"{arm_w:.1f}px",
        "SIZE:props-arm-h": f"{arm_h:.2f}px",
        # 书签卡片的卡片花边(第四十二版，样稿 H)：f1509_4 九宫格，四角 + 四边中段(主题里拉长)
        **{f"ORN:card-frame-{p}": svg_uri(O.card_frame(p)) for p in ("tl", "tr", "bl", "br", "top", "bottom", "left", "right")},
        # 图片外框(第四十六版)：同一副卡片花边缩小 + 贴着图边的投影，九宫格切片 = img-slice；图片边离外框外缘 IMG_FRAME_E
        "ORN:img-frame": svg_uri(img_frame),
        "SIZE:img-slice": f"{img_c}",
        "SIZE:img-pad": f"{O.IMG_FRAME_E - 1:g}px",
        "SIZE:img-x": f"{2 * O.IMG_FRAME_E:g}px",
        # 图片样式「印痕毛边」：两层遮罩(上下渐隐 × 左右渐隐)的图片、位置、尺寸
        "ORN:img-grain": ", ".join(svg_uri(s) for s, _, _ in img_grain),
        "SIZE:img-grain-pos": ", ".join(p for _, p, _ in img_grain),
        "SIZE:img-grain-size": ", ".join(z for _, _, z in img_grain),
        "ORN:newtab": svg_uri(O.newtab_crest(
            ink=ink, ink_dark=ink_dark,
            wear="data:image/webp;base64," + b64(S.wear_overlay(O.CREST_W, O.CREST_H, 160, seed=7, base=.34, span=.56, deep=.16)),
            halo=(lambda *a, **k: DK.eclipse_halo(*a, pal=DK.ECLIPSE_BONE, **k)) if DK.ON else None)),   # 夜间：太阳光环换成「黑日」(骨白日冕)
        # 题铭位图 2 倍显示清晰度(第二十七版三段式：显示宽 700)；CSS 按宽带正中上沿对齐原来的位置
        "RASTER:inscription": webp_uri(ins),
        "SIZE:inscr-w": f"{iw / 2:g}px",
        "SIZE:inscr-h": f"{ih / 2:g}px",
        "SIZE:inscr-band": f"{iband:g}px",
        # 新标签页四个按钮的哥特窗外框(第四十五版 E2，石条并集画法)：外框线遮罩 + 悬停底剪影，内容区左右让出 cap
        "ORN:newtab-btn-frame": svg_uri(ntb_frame),
        "ORN:newtab-btn-fill": svg_uri(ntb_fill),
        "SIZE:newtab-btn-pad": f"{ntb_cap + 6:.0f}px",
        "SIZE:newtab-btn-h": f"{ntb_h}px",
        "RASTER:grain": webp_uri(DK.grain_webp(*(DK.GRAIN_DARK if DK.ON else DK.GRAIN_DAY))),   # 不用 SVG 滤镜：摩尔纹(dark.grain_webp)
        "RASTER:tag-grain": webp_uri(tag_grain()),
        "RASTER:tone": webp_uri(tone_webp(DK.tex_tone() if DK.ON else O.tex_tone(1024))),
        "SIZE:spatter-w": f"{SPATTER['W']}px",
        "SIZE:spatter-h": f"{SPATTER['H']}px",
        "SIZE:spatter-top": f"{SPATTER_TOP}px",
        "SIZE:newtab-crest-h": f"{NEWTAB_CREST_H}px",
        "SIZE:inscr-band-top": f"{INSCR_BAND_TOP:g}px",
    }
    # 夜间新标签页的血渍：只在夜间那遍出(手写的夜间规则引 RASTER:spatter-dk)，要抠掉的是夜间版徽章 + 题铭的轮廓
    if DK.ON:
        t["RASTER:spatter"] = webp_uri(spatter_webp(t["ORN:newtab"], t["RASTER:inscription"], iw / 2, INSCR_BAND_TOP - iband))
    return t


# 题铭「Fraternitas · Legio · Pater · Imperator」。第二十七版三段式(用户：左边一个词、中间两个词、右边一个词，缎带缩短、更自然地环绕圣杯，字弧度完全贴合、完全落在缎带内)：
# 左右两个词排在 f0215 两端 S 形环的正面(部件 2 / 10)，中间两个词排在中段宽带(部件 8)，两侧各一只分割线同款的卷草臂
INSCR_WORDS = ("Fraternitas", "Legio · Pater", "Imperator")
GOTHIC = ROOT / "fonts" / "ManufacturingConsent-normal-400-latin.woff2"
INSCR_SAG = 90          # 题铭绶带两端比正中抬起多少(显示 px)；第九版一稿 40 被嫌不够弯，要有环绕圣杯的感觉

# 代码块(第二十七版)：SVG 背景图不能用 CSS 变量，颜色在这里定、和 theme.src.css 同步
C_TAG = "#f4e6c9"       # = --tag-color：铭牌上的语言名、机械教徽、沉思者的蜡烛和铭牌下沿那道线(用户：三样颜色不一样看着杂乱)
C_PARCH = "#f3e8d0"     # 沉思者黑屏幕里的滚动条(用户：改成类似背景色的羊皮纸色)
COG_FLAME = "#f1d27f"   # 蜡烛火苗：淡金(用户：原来的琥珀太橙、饱和度太高太暗沉)
CODE_NUMS = 500         # 阅读视图行号栏写到多少行(更长的代码块后面的行没有行号)
PROPS_SIDE = .75        # 右侧栏属性面板里属性栏花框的缩放(栏窄，左右留白超过 20px 原版就会把属性名和值上下排；十稿用户：角花放大，0.6 → 0.75)


def ribbon_arc(base_w=1100, extra=420, sag=INSCR_SAG, scale=2, wear=(.34, .52, .12), seed=11):
    """新标签页那条绶带(f0215)的位图：渲染 → 宽带正中那一列像素复制 extra 次加长 → 弯成圆弧(两端抬起 sag 显示 px)。
    scale = 位图 / 显示 倍数。返回 (预乘 RGBA 数组(还没乘颗粒), 颗粒 × 磨损遮罩(印章版；描边版 None), pad, 宽带中线 y)。
    加长：原图左右对称，正中这一列的上下沿是水平切线，复制出来完全无缝(矢量切三块拉伸会在 f0215 上起台阶、露接缝)。
    颗粒要在弯曲之后乘(先乘再弯，一两个像素的颗粒会被插值抹糊)，所以单独返回遮罩，由调用方在量完宽带中线之后乘"""
    import io
    import math
    import numpy as np
    import raster as R
    import stamp as S
    from PIL import Image
    h = round(base_w * 164.3 / 800)
    im = Image.open(io.BytesIO(R.render_webp(RB.ribbon("f0215_0", stamp=RIBBON_STAMP), base_w, h, lossless=True))).convert("RGBA")
    cx = base_w // 2
    col = im.crop((cx, 0, cx + 1, h))
    out = Image.new("RGBA", (base_w + extra, h), (0, 0, 0, 0))
    out.paste(im.crop((0, 0, cx, h)), (0, 0))
    for i in range(extra + 1):
        out.paste(col, (cx + i, 0))
    out.paste(im.crop((cx + 1, 0, base_w, h)), (cx + extra + 1, 0))
    if not RIBBON_STAMP:
        # 描边版：加长之后再叠斑驳纹理(先叠的话正中那一列的纹理会被复制成一道道竖纹)。
        # 污斑 512 显示 px 一格、细斑 96，按 scale 换成位图尺寸；纹理只留在绶带不透明的地方
        tex = Image.new("RGBA", out.size, (0, 0, 0, 0))
        for data, cell in zip(ribbon_tex(), (round(512 * scale), round(96 * scale))):
            t = Image.open(io.BytesIO(data)).convert("RGBA").resize((cell, cell), Image.BICUBIC)
            layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
            for x in range(0, out.width, cell):
                for y in range(0, out.height, cell):
                    layer.paste(t, (x, y))
            tex = Image.alpha_composite(tex, layer)
        a = tex.getchannel("A")
        tex.putalpha(Image.composite(a, Image.new("L", out.size, 0), out.getchannel("A")))
        out = Image.alpha_composite(out, tex)
    W = out.width
    rib = np.asarray(out, np.float32) / 255
    rib[..., :3] *= rib[..., 3:4]                       # 预乘，弯曲时插值才不会在边缘渗出黑边
    s2, y_ref = sag * scale, 192.4 * base_w / 1100      # 以宽带中线为准弯，正中那一段不动(原图宽带中线：1100 宽时 192.4)
    pad = math.ceil(s2 + 4 * scale)
    rib = S.arc_warp(rib, s2, y_ref, pad)
    Ho = rib.shape[0]
    m = None
    if RIBBON_STAMP:
        # 颗粒图放大 scale 倍铺(一粒 = 1 显示 px，同徽章)；暗红里衬上颗粒减三成
        g = Image.open(io.BytesIO(ink_tex())).convert("L").resize((round(256 * scale),) * 2, Image.BICUBIC)
        b, sp, dp = wear
        al = rib[..., 3:4]
        gain = S.dark_gain(np.where(al > 1e-4, rib[..., :3] / np.maximum(al, 1e-4), 1), floor=.7)
        m = S.ink_mask(S.tile(g, W, Ho), S.wear(W, Ho, 160 * scale, seed=seed), b, sp, dp, gain)
    return rib, m, pad, y_ref + pad


# 第十二版(用户：翅膀颜色又太显眼)：#e8c36a → #d09a3e / #b07a2e 收成 #d6b46a → #bf9a52 / #a3814a(比过一档中间值 #dcb866)
TITLE_CREST = dict(W=360, eh=104, band=.72, sag=12, scale=2.5, gold=("#d6b46a", "#bf9a52"), shade="#a3814a")


def title_crest_svg(ink, ink_dark) -> tuple:
    """笔记标题下的徽记(ornaments.title_crest)：先做绶带位图(新标签页那条，不带字，2.5 倍清晰度)，裁掉上下透明的行，再拼进徽记 SVG。
    一稿(380 宽、徽记 96 高、宽带在徽记一半高度、两端抬 22px)用户嫌和标题之间空白太多、构图割裂、翅膀像黄铜：
    f0215 两端的卷边比宽带高出约 40px，宽带放在徽记半高时卷边远高过翼尖，徽记正上方空出一大块。
    现在绶带几乎拉平(两端抬 12px)、宽带压低到徽记 0.72 高处，卷边顶和翼尖差不多平齐，整枚轮廓收紧；
    双翼换偏暖的金(gold / shade)。比过：380 宽两端抬 8、400 宽两端抬 6(更扁)、暖金 #e2b552 / 偏红金 #e0b04e(scratchpad ba_title.py)。
    返回 (SVG, 图高)"""
    import numpy as np
    import stamp as S
    c = TITLE_CREST
    rib, m, pad, ymid = ribbon_arc(round(c["W"] * c["scale"]), 0, c["sag"], c["scale"], seed=29)
    if m is not None:
        rib *= m[..., None]
    rows = np.nonzero(rib[..., 3].max(1) > .01)[0]          # 裁掉上下透明的行(弯弧留出的余量)
    rib, ymid = rib[rows[0]:rows[-1] + 1], ymid - rows[0]
    Ho, Wb = rib.shape[:2]
    uri = "data:image/webp;base64," + b64(rgba_webp(rib))
    kw = dict(W=c["W"], eh=c["eh"], band=c["band"], ink=ink, ink_dark=ink_dark, gold=c["gold"], shade=c["shade"])
    _, H = O.title_crest(uri, Wb / c["scale"], Ho / c["scale"], ymid / c["scale"], **kw)
    wear = "data:image/webp;base64," + b64(S.wear_overlay(c["W"], round(H), 70, seed=13, base=.34, span=.56, deep=.16, res=2))
    return O.title_crest(uri, Wb / c["scale"], Ho / c["scale"], ymid / c["scale"], wear=wear, **kw)


def rgba_webp(pm, quality=88) -> bytes:
    """预乘 RGBA 浮点数组 → WebP 字节"""
    import io
    import numpy as np
    from PIL import Image
    al = pm[..., 3]
    rgb = np.where(al[..., None] > 1e-4, pm[..., :3] / np.maximum(al, 1e-4)[..., None], 0)
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), al]) * 255).round().astype(np.uint8), "RGBA")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality, alpha_quality=90, method=6)
    return buf.getvalue()


def inscription_webp(sag=INSCR_SAG, base_w=1400, px_mid=27, px_side=26, side=(85, 240), orn=15, orn_len=40, inset=2.5,
                     text_ink=("#6a0b11", "#a02127"), edge=.22, text_wear=(.3, .55, .1)) -> tuple:
    """新标签页题铭：绶带(ribbon_arc，2 倍显示清晰度) + 文字，一张位图。返回 (WebP 字节, 位图宽, 位图高, 宽带正中上沿离图顶的显示 px)。
    第九版(用户：文字没有质感，要一点模仿印章墨水的微妙渐变；绶带太平、曲度加大，文字一起弯)：
    文字不再是 CSS 文本，按同样的字体渲染进来，跟着绶带弯；
    两套墨各乘各的颗粒 × 磨损——文字是叠印的第二套色：字上漏白处透出绶带色，绶带漏白处透出纸色。
    文字颜色 = 暗血红里很缓的浓淡(text_ink 两色之间) + 笔画边缘略深(印章墨水往边上堆，edge)。
    第二十七版三段式(INSCR_WORDS)：绶带不再加长(1400 位图宽 = 显示 700)，三块正面(部件 2 / 8 / 10)各自渲染成遮罩、一起弯弧，
    每块逐列量中线，字沿各自的中线排(S.follow_warp：水平 = 弧长、竖直 = 法线)；
    左右两个词 26px、排在 S 形环正面 side 单位那一段的正中(用户：太靠边 → 往里挪 30px，50–205 改 85–240)；
    中间两个词 27px，两侧各贴一只分割线同款的卷草臂(orn = 卷草组高，显示 px)，和字同一套墨、一起弯；
    五轮(用户：臂外端的箭头突兀，换成像分割线那样渐变消失；比过分割线同款双线、保留菱形两版，选后者)：箭头换成 orn_len 长的渐隐横线。
    曲线外推会在正面外甩出碎点：字只留在正面外扩 16px、该段列范围 ±30px 之内，再清掉完全不碰正面、或小于 5 像素的连通块。
    出界检查：正面往里缩 inset 显示 px 之后，字墨落在外面的最大覆盖率(打印出来，> 0.05 说明字压到了缎带边)"""
    import io
    import numpy as np
    import scipy.ndimage as ndi
    import raster as R
    import stamp as S
    from PIL import Image, ImageFilter
    scale = 2
    rib, m1, pad, y_mid = ribbon_arc(base_w, 0, sag, scale)
    Ho, W = rib.shape[:2]
    h = round(base_w * 164.3 / 800)
    ps = RB._paths("f0215_0")
    s2, y_ref = sag * scale, 192.4 * base_w / 1100

    def face(idx):
        svg = f'<svg {RB.SVG} viewBox="0 0 800 164.3"><path d="{ps[idx]}" fill="#fff"/></svg>'
        a = np.asarray(Image.open(io.BytesIO(R.render_webp(svg, base_w, h, lossless=True))).convert("RGBA"), np.float32)[..., 3:4] / 255
        return S.arc_warp(a, s2, y_ref, pad)[..., 0]
    faces = {"L": face(2), "M": face(8), "R": face(10)}
    k = base_w / 800
    rng = {"M": (W // 2 - int(150 * k), W // 2 + int(150 * k)),
           "L": (int(side[0] * k), int(side[1] * k)), "R": (W - int(side[1] * k), W - int(side[0] * k))}

    def ink_mid(px, lh):
        """哥特体(Manufacturing Consent：hhea 1100 / −340，1200 一个 em)行高 lh 时墨迹中线离盒顶多少显示 px(大写顶到下伸底的中点)"""
        return (lh - 1.2 * px) / 2 + 1100 / 1200 * px - 6.75 / 27 * px

    def scroll_arms(t, ymid, gap=7):
        """字两侧各贴一只卷草臂(ornaments.rule_arm_fade：f1090_1 的 ∞ 卷草 + 菱形 + 往外渐隐的横线，卷草贴着字)"""
        svg, aw, ah = O.rule_arm_fade(sh=orn, length=orn_len)
        a = np.asarray(Image.open(io.BytesIO(R.render_webp(svg, round(aw * scale), round(ah * scale), lossless=True))).convert("RGBA"),
                       np.float32)[..., 3] / 255
        cols = np.nonzero(t.max(0) > .1)[0]
        t = t.copy()
        ht = t.shape[0]
        ah2, aw2 = a.shape
        y0 = int(round(ymid - ah2 / 2))
        for x0, img in ((cols[0] - gap * scale - aw2, a), (cols[-1] + gap * scale, a[:, ::-1])):
            x0 = int(round(x0))
            ys0, ys1 = max(0, y0), min(ht, y0 + ah2)
            t[ys0:ys1, x0:x0 + aw2] = np.maximum(t[ys0:ys1, x0:x0 + aw2], img[ys0 - y0:ys1 - y0])
        return t

    txt = np.zeros((Ho, W), np.float32)
    for key, word, px in (("L", INSCR_WORDS[0], px_side), ("M", INSCR_WORDS[1], px_mid), ("R", INSCR_WORDS[2], px_side)):
        x0, x1 = rng[key]
        f = faces[key]
        lh = round(px * 1.15)
        bw = 600
        t = S.text_alpha(word, GOTHIC, px, bw, lh, scale=scale)
        if key == "M" and orn:
            t = scroll_arms(t, ink_mid(px, lh) * scale)
        r = np.nonzero(f[:, (x0 + x1) // 2] > .5)[0]
        xs, ys = S.centerline(f, x0, x1, (r[0] + r[-1]) / 2)
        part, _ = S.follow_warp(t, xs, ys, (Ho, W), bw * scale / 2, ink_mid(px, lh) * scale, deg=6)
        near = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(16 * scale + 1)), np.float32) / 255
        span = np.zeros_like(f)
        span[:, max(0, x0 - 60):x1 + 60] = 1
        part = part * near * span
        lab, n = ndi.label(part > .02)
        if n:
            hit = ndi.maximum(f, lab, index=np.arange(1, n + 1))
            area = ndi.sum(np.ones_like(f), lab, index=np.arange(1, n + 1))
            part = part * np.isin(lab, np.nonzero((hit > .5) & (area >= 5))[0] + 1)
        er = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(int(2 * inset * scale) + 1)), np.float32) / 255
        out = float((part * (1 - er)).max())
        print(f"  题铭 {word!r}: 缩进 {inset}px 后出界最大覆盖率 {out:.2f}" + ("  ⚠ 压到缎带边" if out > .05 else ""))
        txt = np.maximum(txt, part)
    if m1 is not None:
        rib *= m1[..., None]
    # 文字的颗粒：位图是显示尺寸的 2 倍，颗粒图放大 2 倍铺、和绶带错开；磨损场另用一套
    g = Image.open(io.BytesIO(ink_tex())).convert("L").resize((512, 512), Image.BICUBIC)
    # 文字颜色：两色之间很缓的浓淡 + 笔画边缘略深(边缘 = 覆盖率模糊后不到 0.85 的地方)
    c0, c1 = (np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255 for c in text_ink)
    fld = S.field(W, Ho, 240, seed=5)
    col = c0 + (c1 - c0) * (.1 + .8 * fld)[..., None]
    inner = np.asarray(Image.fromarray((txt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.4)), np.float32) / 255
    col *= (1 - edge * np.clip(1 - inner / .85, 0, 1))[..., None]
    b, sp, dp = text_wear
    ta = txt * S.ink_mask(S.tile(g, W, Ho, (173, 91)), S.wear(W, Ho, 240, seed=23), b, sp, dp)
    pm = np.dstack([col * ta[..., None] + rib[..., :3] * (1 - ta[..., None]), ta + rib[..., 3] * (1 - ta)])
    # 裁掉上下全透明的行(弯弧留出的余量)；量宽带正中上沿离图顶多少，CSS 用它把宽带放回原来的位置
    rows = np.nonzero(pm[..., 3].max(1) > .01)[0]
    pm = pm[rows[0]:rows[-1] + 1]
    band = np.nonzero(faces["M"][rows[0]:, W // 2] > .5)[0][0] / scale
    return rgba_webp(pm), W, pm.shape[0], band


def callout_icon_css() -> str:
    """callout 图标：已知类型(含别名)藏掉内置 Lucide 图标，用 ::before + 遮罩画剪影，颜色 = --callout-color。
    第二十版：剪影装进一枚蜡封(ornaments.callout_seal：类型颜色的蜡 + 留白细环 + 图标镂空)，叠磨损颗粒。
    自定义 callout 类型不受影响；Style Settings 开 ba-native-callout-icons 恢复原版"""
    out = ["/* ---- callout icons (generated from ornaments.CALLOUT_ICONS) ---- */"]
    every = []
    for types, name in O.CALLOUT_ICONS:
        sels = [f'.callout[data-callout="{t}"]' for t in types]
        every += sels
        out.append(f'{", ".join(sels)} {{ --ba-glyph: {svg_uri(O.callout_seal(name))}; --ba-latin: "{O.CALLOUT_LATIN[types[0]]}"; }}')
    g = f"body:not(.ba-native-callout-icons) :is({', '.join(every)}) > .callout-title > .callout-icon"
    out.append(f"{g} {{ position: relative; min-width: var(--ba-seal-size); justify-content: center; margin-inline-end: 0.35em; }}")
    out.append(f"{g} > .svg-icon {{ opacity: 0; }}")
    out.append(
        f'{g}::before {{ content: ""; position: absolute; left: 50%; top: 50%; '
        "width: var(--ba-seal-size); height: var(--ba-seal-size); transform: translate(-50%, -50%); "
        "background: var(--ba-tag-grain) 0 0 / 256px 256px, var(--callout-color); "
        "-webkit-mask: var(--ba-glyph) center / contain no-repeat; mask: var(--ba-glyph) center / contain no-repeat; }")
    return "\n".join(out)


# 文件列表的飘落羽毛(第三十二版)：十二根，分远 / 中 / 近三层做出景深(用户：能不能分辨出羽毛的远近)——
# 越远越小、越模糊(模糊烘进位图)、越淡(透进纸色)、摇得越小，错版那层「影子」也贴得越近；近的盖在远的上面(z-index)。
# 下落速度不按层定死(用户：远处的有些羽毛下落反而更快呢)：透视下屏幕速度 = 真实速度 / 距离，屏幕大小也 / 距离，
# 所以「每秒落几个身长」与远近无关、只看羽毛本身——每根给一个本征速度(宽羽阻力大最慢、弯羽最快，再加个体差异)，
# 落一趟的秒数由它和屏幕大小算出来：平均仍是远的慢，但快的远羽能比慢的近羽先落地。
# (一稿三层各一档 29–36s / 19–23s / 13–15s，等于十二根都是同一根羽毛放在不同远近，每秒都是一个身长左右)
# 第三十三版起不再只挂文件列表，挂在「文件列表所在的那一组侧栏标签」上(用户：和文件树同一行 tab 的窗口都要，别的面板拖进来呢)——
# 跟着标签组走、不看面板类型：拖进来的面板也有，拖出去就没有；文件列表被拖到别的组，羽毛跟过去。
# 纸纹从各面板挪到标签组上(面板透明)，羽毛画在标签组的纸纹之上、面板内容之下。伪元素宿主分两种：
#   持久的(切标签不销毁，动画不断)：标签组自己、内容区外框、标签栏(::before 被 Obsidian 占了——macOS 给红绿灯留位，只用 ::after)、
#   标签按钮区、标签栏空白——九个；面板上的(切标签时重新开始，正赶上整块内容在换，看不出)：叶子、面板内容各两个——四个。
# 三根染血的必须挂持久宿主(否则切一次标签，彩蛋的轮次就从头算)。
# 面板(叶子)自成层叠上下文，挂在面板上的三根总在标签组那九根之上，所以都放中 / 近景、横向避开持久的那根近景。
# (第三十三版二稿试过万神殿式天光——正上方往下张开的扇形，叠加 / 滤色混合，占标签组自己的两个伪元素、羽毛减到十一根；
#  用户看了说效果很差、删掉，羽毛恢复十二根)
FEATHER_GROUP = ('.workspace-split.mod-sidedock .workspace-tabs:has(> .workspace-tab-container > .workspace-leaf > '
                 '.workspace-leaf-content[data-type="file-explorer"])')
FEATHER_DEPTH = {   # 层: (模糊 px, 不透明度, z-index, 错版偏移倍数)
    "far": (0.7, 0.68, -3, 0.6),     # 一稿 0.9px / 0.55：白羽在纸上几乎看不见
    "mid": (0.3, 0.85, -2, 0.85),
    "near": (0.0, 0.96, -1, 1.15),
}
FEATHERS = [   # 层, 形状, 横向位置 %, 大小 px, 血染, 镜像, 基础倾角°, 本征速度(身长/秒), 起始相位 s, 平均摆一下 s, 摇摆相位 s, 摇摆幅度°, 横向漂移 px
    # 本征速度一稿 0.75–1.5、近景摇摆周期 3.0–3.5s：用户嫌最快的几根落得、摇得太快 → 速度压到 0.65–1.3，近 / 中景摇摆放慢
    # 摇摆二稿七根挤在 4.3–5.0s(两根同为 4.6s、相位只差 0.2s)，用户常看到两根同频 → 十二根在 4.3–7.2s 等比排开(相邻约 6%，
    # 同层至少差 10%，宽羽摆得慢、弯羽快)，相位按黄金比错开；摆法见 FEATHER_SWAY(一轮四下、大小不一，三种轮流)
    # 第三十三版：前九根挂持久宿主，后三根挂面板(见上)
    ("far", "curved", 6, 18, None, False, -6, 1.3, -4, 4.30, -0.9, 16, 14),     # 远处最快的一根，仍快过近景的宽羽
    ("far", "broad", 30, 16, "tip", True, 8, 0.85, -19, 7.20, -17.8, 14, -12),
    ("far", "sweep", 56, 20, None, False, 4, 1.0, -11, 5.62, -5.3, 18, 16),
    ("far", "curved", 76, 17, None, True, -4, 1.15, -26, 4.83, -16.5, 15, -14),
    ("far", "sweep", 90, 15, None, False, 10, 0.95, -8, 6.41, -12.1, 14, -10),
    ("mid", "sweep", 14, 26, "root", False, 0, 0.9, -7, 6.15, -2.2, 26, 28),
    ("mid", "curved", 44, 28, None, True, 6, 1.05, -15, 4.56, -12.9, 28, -30),
    ("mid", "broad", 68, 24, None, False, -8, 0.75, -2, 6.94, -9.0, 24, -24),
    ("near", "broad", 20, 36, "side", True, -4, 0.65, -5, 6.67, -15.0, 34, 40),  # 近景一稿 44~52px，用户嫌太大；中景跟着缩一档
    ("mid", "curved", 86, 26, None, False, 4, 1.0, -18, 5.36, -20.2, 26, -34),  # ↓ 挂面板
    ("near", "curved", 60, 38, None, False, 4, 0.95, -11, 5.09, -3.7, 32, -44),  # 现在最快的一根
    ("near", "sweep", 38, 34, None, True, 0, 0.85, -1, 5.88, -18.8, 34, 30),
]
FEATHER_KEEP = 9   # 前几根挂持久宿主
# 摆法(按周期排序后三种轮流)：一轮摆四下、每下幅度不同(单位 = 摇摆幅度)，每下的时长随幅度略增(幅度^0.3)，转折点都是关键帧
# (每段 ease-in-out，到头停一下再回)；一稿是 alternate 的单摆，节奏太整齐，周期接近的两根看着像齐步走
FEATHER_SWAY = {
    "a": [(0, -1), (26, .9), (49.5, -.45), (73.5, 1), (100, -1)],
    "b": [(0, -.7), (26, 1), (53, -1), (77.5, .4), (100, -.7)],
    "c": [(0, 1), (25, -.6), (48, .7), (73.5, -1), (100, 1)],
}
FEATHER_FALL_H = 600   # 估算落一趟的秒数用的标签组高度 px(实际按 100cqh 落，高矮只改快慢，不改相对关系；只挂文件列表时是 500)


def feather_period(px, k):
    """落一趟的秒数：路程(列表高 + 上下各出界一点) / (本征速度 × 屏幕大小)，取到 0.5s"""
    return round((FEATHER_FALL_H + 40 + 2 * px) / (k * px) * 2) / 2


# 血染的三根平时也是白羽，隔 N 趟才有一趟染血(用户：染血羽毛太频繁，要像彩蛋，一分钟左右出现一根)：
# 第三个动画在羽毛落到底、回到顶上(看不见)的那一刻把白羽换成染血版(第三十七版起：两个宿主互换透明度，不再换 background-image，
# 见 feathers_css)。血染方式: (N 趟一轮, 第 j 趟染血)——
# 三根一轮都是三分钟左右，错开出场：打开后约 30 秒羽梢(远)、82 秒根部(中)、117 秒侧面(近)，之后平均一分钟一根
FEATHER_RARE = {"tip": (4, 1), "root": (6, 3), "side": (6, 4)}


def feather_hosts() -> tuple:
    """羽毛的伪元素宿主：(十二根羽毛的宿主, 三根染血版的宿主)；夜间的灰烬和火星(embers_css)用同一批"""
    G = FEATHER_GROUP
    tc, hc, leaf = f"{G} > .workspace-tab-container", f"{G} > .workspace-tab-header-container", f"{G} > .workspace-tab-container > .workspace-leaf"
    slots = ([f"{G}::before", f"{G}::after", f"{tc}::before", f"{tc}::after", f"{hc}::after"]
             + [f"{G} {h}::{p}" for h in (".workspace-tab-header-container-inner", ".workspace-tab-header-spacer") for p in ("before", "after")]
             + [f"{leaf}::before", f"{leaf}::after", f"{leaf} > .workspace-leaf-content::before"])
    stain_hosts = [f"{hc} > .workspace-tab-header-new-tab::before", f"{hc} > .workspace-tab-header-new-tab::after",
                   f"{hc} > .workspace-tab-header-tab-list::before"]
    return slots, stain_hosts


def feathers_css() -> str:
    import raster as R
    G = FEATHER_GROUP
    hc = f"{G} > .workspace-tab-header-container"
    # 持久宿主都是 static(标签栏是 relative，但和标签组左上角对齐、同宽，算出来的位置一样)；标签按钮区是滚动容器，
    # 伪元素的包含块在它外面，不会被它裁掉
    slots, stain_hosts = feather_hosts()
    assert len(slots) == len(FEATHERS) and FEATHER_KEEP == 9
    assert not any(f[4] for f in FEATHERS[FEATHER_KEEP:]), "染血的羽毛要挂持久宿主"
    # 染血版的宿主(第三十七版性能)：标签栏里的新建标签 / 标签列表两个按钮，侧栏里本来就 display: none；
    # 在羽毛组里改成 display: contents(不生成盒子，图标照旧藏起来)，伪元素就能画出来，包含块同上面的标签按钮区(标签栏)
    stained = [i for i, f in enumerate(FEATHERS) if f[4]]
    assert len(stained) <= len(stain_hosts)
    twins = dict(zip(stained, stain_hosts))
    every = slots + list(twins.values())
    ink_l = "data:image/webp;base64," + b64(ink_tex(**INK_LIGHT))
    out = ["/* ---- falling feathers (generated by build.py feathers_css from FEATHERS) ---- */",
           # 藏按钮图标写 > .clickable-icon，不写 > *(第三十七版性能，用户：编辑视图滚动卡)：浏览器把所有「:has() 后面还接着选择器」
           # 的规则合成一套失效范围，只要有一条接的是通配符，页面上任何一个 :has() 状态可能变了的元素(编辑视图滚动时 CodeMirror 不停插行)
           # 底下整棵子树都要重算——实测滚一趟整片正文重算 9 次、每次 28–81ms。Mermaid 那条同理，见 mermaid_css
           f"{hc} > :is(.workspace-tab-header-new-tab, .workspace-tab-header-tab-list) {{\n  display: contents;\n}}\n"
           f"{hc} > :is(.workspace-tab-header-new-tab, .workspace-tab-header-tab-list) > .clickable-icon {{\n  display: none !important;\n}}",
           ",\n".join(every) + " {\n  content: \"\";\n  position: absolute;\n  top: calc(-20px - var(--ba-fl-s));\n  left: var(--ba-fl-x);\n"
           "  width: var(--ba-fl-s);\n  height: var(--ba-fl-s);\n  pointer-events: none;\n  background: center / contain no-repeat;\n"
           "  transform-origin: 50% -140%;\n}"]
    # 关键帧不用 var()、每根羽毛一套定值(第三十七版性能)：动画在合成线程上跑，可主线程每出一帧(编辑视图滚动时每帧都出)
    # 都要把正在动画的元素重算一遍样式，关键帧里有 var() 时每次都得重新代入——十五个宿主每帧 ~1.3ms，定值后 ~0.6ms。
    # 偶尔染血(同版)：原来是第三个动画在关键帧里换 background-image——这个属性只能在主线程上跑，
    # 浏览器为它每帧重算样式、重绘，什么都不动时主线程也有约一半时间耗在这三根羽毛上(实测静止每秒任务 ~500ms，去掉后 ~25ms)。
    # 现在染血版画在另一个宿主上、和白羽同一套下落 / 摇摆(同时长、同延迟，步调一致)，两边只动透明度(合成线程跑)：
    # 染血那一趟白羽透明、染血版显出来，其余各趟反过来；切换的时刻同原来，落到底回到顶上看不见的时候。
    # 两边必须同时起步：主题重载时动画名没变的动画浏览器会接着跑，旧版升上来时白羽的下落还是旧的那一轮、染血版却从头开始，
    # 步调对不上(染血版会在半空冒出来)——所以每次改动画结构都给关键帧换名(ba-feather-fall / sway → drop / swing → 现在的 ba-fl-*)，
    # 换上新版时所有羽毛一起重新开始。以后再改，也要照此换名
    # 摆法按周期排序后轮流分(按序号轮流时 7.20s / 6.94s 两根同用一种)：同一种摆法的周期至少隔三档(约 19%)
    rank = {i: r for r, i in enumerate(sorted(range(len(FEATHERS)), key=lambda i: FEATHERS[i][9]))}
    for i, (sel, (layer, shape, x, px, stain, flip, tilt, k, d, p, sd, a, dx)) in enumerate(zip(slots, FEATHERS)):
        blur, op, z, off_k = FEATHER_DEPTH[layer]
        t = feather_period(px, k)
        st = round(4 * p, 2)   # 一轮四下
        res = round(px * 2.5)
        out.append(f"@keyframes ba-fl-fall-{i} {{\n  from {{ translate: 0 0; }}\n  to {{ translate: {dx}px calc(100cqh + {40 + 2 * px}px); }}\n}}")
        out.append(f"@keyframes ba-fl-sway-{i} {{\n"
                   + "".join(f"  {pc:g}% {{ rotate: {tilt + a * m:g}deg; }}\n" for pc, m in FEATHER_SWAY["abc"[rank[i] % 3]]) + "}")

        def img(s):
            return webp_uri(R.render_webp(O.falling_feather(shape, ink=ink_l, stain=s, blur=blur, px=px, off_k=off_k), res, res, quality=86))

        def img_dark(s):
            # 夜间羽毛版的图(按夜间配色重画)：日间那遍里临时进 DK.mode 渲染；夜间那遍本来就在换色(这几条带 .theme-dark，
            # dark.twins 不比对，最后用的是日间那遍里生成的)
            if DK.ON:
                return img(s)
            with DK.mode():
                return img(s)
        common = f"  z-index: {z}; opacity: {op};" + (" scale: -1 1;" if flip else "") + f" --ba-fl-x: {x}%; --ba-fl-s: {px}px;\n"
        anim = f"  animation:\n    ba-fl-fall-{i} {t}s linear {d}s infinite,\n    ba-fl-sway-{i} {st}s ease-in-out {sd}s infinite"
        swap = lambda name: anim + ";\n"
        if stain:
            # 透明度动画一轮 = N 趟，第 j 趟染血：延迟 = 下落的延迟 + j 趟 − 一整轮(保持为负，打开时已在轮中)
            n, j = FEATHER_RARE[stain]
            cut0, cut1 = f"{100 / n - .01:.2f}%", f"{100 / n:.2f}%"
            out.append(f"@keyframes ba-fl-white-{i} {{\n  0%, {cut0} {{ opacity: 0; }}\n  {cut1}, 100% {{ opacity: {op}; }}\n}}")
            out.append(f"@keyframes ba-fl-blood-{i} {{\n  0%, {cut0} {{ opacity: {op}; }}\n  {cut1}, 100% {{ opacity: 0; }}\n}}")
            swap = lambda name: anim + f",\n    ba-fl-{name}-{i} {n * t}s linear {d + (j - n) * t}s infinite;\n"
        out.append(f"{sel} {{ /* dark-twin: skip(夜间默认换成灰烬和火星，见 embers_css；可选夜间羽毛版，见下面 ba-dark-feathers 那条) ·{layer} · {shape}{' · 偶尔染血(' + stain + ')，染血版在下面另一个宿主上' if stain else ''} */\n"
                   f"  background-image: {img(None)};\n" + common + swap("white") + "}")
        if stain:
            out.append(f"{twins[i]} {{ /* dark-twin: skip · 上面第 {i + 1} 根的染血版({stain})：同一套下落 / 摇摆，只在染血那一趟显出来 */\n"
                       f"  background-image: {img(stain)};\n" + common + swap("blood") + "}")
        # 夜间可选羽毛(Style Settings「夜间文件列表动态装饰」= 羽毛，body.ba-dark-feathers)：灰烬火星的规则让开(见 embers_css)，
        # 这里只换成夜间配色的图，下落 / 摇摆 / 染血的节奏照日间
        out.append(f"body.theme-dark.ba-dark-feathers {sel} {{ /* 夜间羽毛版 */\n  background-image: {img_dark(None)};\n}}")
        if stain:
            out.append(f"body.theme-dark.ba-dark-feathers {twins[i]} {{ /* 夜间羽毛版 · 染血 */\n  background-image: {img_dark(stain)};\n}}")
    # 伪元素不能写进 :is()(整条规则会作废)，只能逐个列出
    out.append("@media (prefers-reduced-motion: reduce) {\n  " + ",\n  ".join(every) + " {\n    display: none;\n  }\n}")
    out.append(",\n".join("body.ba-no-feathers " + x for x in every) + " {\n  display: none;\n}")
    return "\n".join(out)


# 夜间(2026-11-03，用户：黑怒——文件列表的飘落羽毛改成灰烬和火星)：羽毛那十五个伪元素宿主(feather_hosts) + 两个空着的
# (标签列表按钮 ::after、面板内容 ::after)，八片灰烬从顶上飘下(边落边左右飘、忽快忽慢，自转 + 翻面，三片一侧边上还燃着)，
# 九粒火星从底下升起(大中小各三粒；越升越慢、左右飘，忽明忽暗，升到一半左右熄灭)。
# 二稿(用户：火星太少、缺小火星；轨迹拐弯折角明显、不符合空气动力学；两粒火星节奏很像；灰烬掉得太直)：
# 轨迹不再是五个点之间直线插值(每个点上折一下)，改成平滑曲线(两条不同周期的正弦叠加 + 匀速漂移，上升按冷却减速)密集采样 40 个关键帧，
# 折线段很短、看不出拐角；运动都放在 translate 里(独立变换属性里最先应用，不受 rotate / scale 影响)；每粒的周期、路线、闪烁都由种子错开。
# 规则都带 .theme-dark(比羽毛规则多一个类，盖过它；dark.twins 不会再给它们生成夜间版)；只动 translate / rotate / scale / opacity，
# 关键帧定值不用 var()(同羽毛的性能结论)；远近三层同 FEATHER_DEPTH(模糊烘进位图)
# 三稿(用户：为什么最接近顶上的地方也会冒火星；同屏两粒火星不能有同样的左右节奏)：
# ① 宿主伪元素的包含块不一样高——标签组 ::before / ::after、标签区(tab-container)两个 = 整个标签组；叶子、叶子内容 = 标签栏以下到底(底边差 ~10px)；
#    标签栏里那些(标签栏 ::after、按钮组、两个按钮) = 只有标签栏那 38px。火星按 top: 100% 放在包含块底边，二稿九粒里六粒挂在标签栏上，
#    「底边」就在顶上，一出生就往上飞出去。现在火星挂底边对齐的八个宿主 + 标签栏里一个(那一个按 100cqh = 标签组高度放到底)，灰烬挂标签栏那几个(从顶上落正合适)。
#    种子跟着条目走、不跟宿主走(灰烬碎片的形状、闪烁和二稿一样)
# ② 二稿的左右摆周期是种子随机抽的：九粒火星里四粒的大摆周期挤在 4.9–5.3s(两粒 5.29 / 5.31s)、两粒小抖同为 1.93s；灰烬的小抖八片全在 6.3–7.1s、
#    忽快忽慢八片同为每趟三下。现在每粒(片)的周期写死、等比排开：火星大摆 2.4–6.6s(相邻档差 13.5%，大火星摆得慢)、小抖 1.05–2.25s(差 10%，和大摆不重叠)；
#    灰烬大摆 9.5–19s、小抖 3.4–6s、忽快忽慢 6.6–12s 一下(各档差约 9–10%)；横向相邻的两粒周期至少差一档。大摆的幅度随路程渐大(不是一成不变的节拍)
ASH = [   # 宿主序号, 种子, 层, 横向 %, 大小 px, 燃着的边, 下落速度(身长/秒), 起始相位 s, 自转一圈 s(负 = 逆时针), 翻一下面 s, 漂移 px, 左右飘 px,
          # 大摆 s, 小抖 s, 忽快忽慢一下 s
    (4, 0, "far", 8, 13, False, 2.0, -3, 9, 2.6, 18, 12, 11.6, 4.69, 9.28),
    (5, 1, "far", 31, 11, False, 2.3, -14, -11, 3.1, -14, 10, 9.5, 5.52, 7.19),
    (6, 2, "far", 55, 14, True, 1.85, -8, 13, 2.2, 20, 14, 14.1, 3.69, 11.0),
    (7, 3, "far", 82, 11, False, 2.2, -21, -8, 2.9, -16, 11, 10.5, 4.33, 8.52),
    (8, 5, "mid", 17, 19, False, 1.5, -5, -12, 3.8, 30, 20, 15.6, 3.4, 6.6),
    (12, 6, "mid", 46, 18, True, 1.65, -12, 9.5, 2.7, -28, 18, 12.8, 5.98, 10.1),
    (13, 8, "near", 24, 27, False, 1.2, -9, 16, 4.6, 38, 28, 19.0, 5.09, 7.83),
    (14, 10, "near", 66, 26, True, 1.3, -15, -13, 3.9, -40, 26, 17.2, 4.0, 12.0),
]
# 四稿(用户：火星摆得还不自然，是不是晃得太频繁、波长太短)：是。三稿按时间摆(周期固定)，可火星越升越慢——同样的周期，越往上在空间里压得越短，
#    顶上成了蛇形(叠图里看得出)；一趟还要摆一两个大弯外加三五下小抖。现在按高度摆：整段上升只弯 0.8–1.1 个大弯 + 2.4–3.6 个小弯(幅度 .2)，
#    越往上越舒缓(时间上的周期跟着速度变长)；靠近火源时幅度小(刚出火的热气流比较直)，往上渐大。
#    节奏错开照旧：表里写「起步时」大弯 / 小弯摆一下几秒(此时上升最快、摆得最勤)，大弯 3.3–8s、小弯 0.9–2.56s 各自等比排开(档差 12–14%)，两组不重叠，
#    横向相邻的两粒大弯至少差一档
# 五稿(用户：最快的那档太快)：按身长 / 秒算(同羽毛的本征速度)，三档火星每秒升的像素差不多(起步 ~58px/s)，小火星个子小，折合 11–14.5 身长/秒(大火星 6.5)，
#    看着最快。小火星一趟 5.6 / 4.9 / 6.1s → 7.8 / 6.9 / 8.5s，降到 8–10 身长/秒(和中火星相当)；大弯 / 小弯周期跟着重排
EMBERS = [   # 宿主序号, 种子, 横向 %, 辉光大小 px(亮芯约 1/5), 升到组高的几成, 一趟 s, 起始相位 s, 闪一下 s, 左右飘 px, 漂移 px, 起步大弯 s, 起步小弯 s
    # 最大的一粒一稿 12px，用户嫌太大 → 大中两档整体收一号(9 / 8.5 / 8、7 / 6.5 / 6)
    (0, 4, 12, 9, .70, 10.6, -2.0, 1.31, 18, 10, 8.0, 2.25),
    (1, 7, 47, 8.5, .62, 9.1, -6.4, 1.07, 15, -14, 7.15, 2.56),
    (2, 9, 78, 8, .56, 8.3, -3.7, 1.53, 13, 8, 6.40, 1.97),
    (3, 11, 30, 7, .50, 7.4, -1.2, 0.93, 11, 12, 4.12, 1.33),
    (9, 12, 63, 6.5, .46, 6.7, -5.1, 1.19, 10, -10, 3.30, 0.90),
    (10, 13, 88, 6, .42, 7.9, -0.4, 0.81, 9, -16, 5.13, 1.73),
    (11, 14, 22, 5, .38, 7.8, -3.3, 0.67, 7, 6, 4.60, 1.17),     # 小火星
    (15, 15, 56, 4, .32, 6.9, -1.9, 0.59, 6, -8, 3.69, 1.03),
    (16, 16, 71, 4.5, .35, 8.5, -4.6, 0.73, 6, 5, 5.73, 1.52),
]
EMBER_RISE = 1.7   # 上升进度 = 1 − (1 − u)^1.7(越升越慢，起步速度是平均的 1.7 倍)


def _sway_path(seed, trip, dx, amp, p1, p2, pos, grow=.6):
    """平滑的横向偏移 x(u)，u ∈ [0, 1] 是一趟的进度：匀速漂移 dx + 大摆(周期 p1 秒，幅度 amp，随路程从 1 − grow/2 渐大到 1 + grow/2)
    + 小抖(周期 p2 秒，幅度 amp × .3)，起点为 0；pos(u) = 纵向进度。关键帧密度按小抖定(每个小抖周期 10 帧，至少 40 帧)，折线看不出拐角"""
    import math
    import random
    rng = random.Random(seed)
    q1, q2 = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
    n = max(40, math.ceil(trip / p2 * 10))
    f = lambda u: dx * u + amp * ((1 - grow / 2 + grow * u) * math.sin(2 * math.pi * u * trip / p1 + q1)   # noqa: E731
                                  + .3 * math.sin(2 * math.pi * u * trip / p2 + q2))
    return [(round(100 * k / n, 2), f(k / n) - f(0), pos(k / n)) for k in range(n + 1)]


def _rise_path(seed, trip, dx, amp, t1, t2, n=60):
    """火星的路线(四稿)：横向偏移按高度 h ∈ [0, 1] 算，h = 1 − (1 − u)^EMBER_RISE(u = 一趟的时间进度)。
    匀速漂移 dx·h + 大弯(整段 c1 圈) + 小弯(c2 圈，幅度 .2)，幅度从 .45 渐到 1；c = 一趟 / (起步速度倍数 × 起步时摆一下的秒数)"""
    import math
    import random
    rng = random.Random(seed)
    q1, q2 = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
    c1, c2 = trip / (EMBER_RISE * t1), trip / (EMBER_RISE * t2)
    f = lambda h: dx * h + amp * (.45 + .55 * h) * (math.sin(2 * math.pi * c1 * h + q1) + .2 * math.sin(2 * math.pi * c2 * h + q2))   # noqa: E731
    out = []
    for k in range(n + 1):
        h = 1 - (1 - k / n) ** EMBER_RISE
        out.append((round(100 * k / n, 2), f(h) - f(0), h))
    return out


def feather_extra_hosts() -> list:
    """夜间多出来的两个宿主(日间羽毛没用到)"""
    G = FEATHER_GROUP
    hc, leaf = f"{G} > .workspace-tab-header-container", f"{G} > .workspace-tab-container > .workspace-leaf"
    return [f"{hc} > .workspace-tab-header-tab-list::after", f"{leaf} > .workspace-leaf-content::after"]


# 夜间文件列表动态装饰默认灰烬火星；Style Settings 选「羽毛(暗色版)」时 body 加 ba-dark-feathers，这里的规则全部让开、日间那套羽毛接管
# (换夜间配色的图，见 feathers_css)。默认值不写成正向类：没装 Style Settings 时也是灰烬火星
DK_ASH = ".theme-dark:not(.ba-dark-feathers)"


def embers_css() -> str:
    import math
    import random
    import raster as R
    slots, stain_hosts = feather_hosts()
    extra = feather_extra_hosts()
    every = slots + stain_hosts + extra
    assert sorted([a[0] for a in ASH] + [e[0] for e in EMBERS]) == list(range(len(every)))
    out = ["/* ---- 夜间：灰烬和火星(generated by build.py embers_css from ASH / EMBERS) ---- */",
           ",\n".join(f"{DK_ASH} {x}" for x in extra) + " {\n  content: \"\";\n  position: absolute;\n  left: var(--ba-fl-x);\n"
           "  width: var(--ba-fl-s);\n  height: var(--ba-fl-s);\n  pointer-events: none;\n  background: center / contain no-repeat;\n}"]
    # 三稿换了宿主、改了摆法：关键帧换名(ba-ash-* / ba-em-* → ba-cin-* / ba-spk-*)，主题重载时全部重新起步(同羽毛的换名规矩)
    in_bar = lambda h: ".workspace-tab-header" in every[h]   # noqa: E731  包含块只有标签栏那么高的宿主(标签栏、按钮组、空白、两个按钮)
    assert all(in_bar(a[0]) for a in ASH), "灰烬挂标签栏里的宿主(包含块顶边 = 标签组顶边)"
    assert sum(in_bar(e[0]) for e in EMBERS) <= 1
    for h, sd, layer, x, px, burn, k, d, spin, flip, dx, amp, p1, p2, pulse in ASH:
        blur, op, z, _ = FEATHER_DEPTH[layer]
        t, res = feather_period(px, k), round(px * 2.5)
        fall = 40 + 2 * px
        uri = webp_uri(R.render_webp(DK.ash_flake(sd * 7 + 3, burn, blur * 2.5, res), res, res, quality=86))
        # 纵向：匀速里带一点忽快忽慢(进度 = u − b·sin(2π·m·u)/(2π·m)，b < 1 保证一直往下；m = 一趟几下，不必是整数，末尾归一到 1)
        m, b = t / pulse, .3
        g0 = lambda u: u - b * math.sin(2 * math.pi * m * u) / (2 * math.pi * m)   # noqa: E731
        pts = _sway_path(sd * 13 + 1, t, dx, amp, p1, p2, lambda u: g0(u) / g0(1))
        out.append(f"@keyframes ba-cin-fall-{sd} {{\n"
                   + "".join(f"  {pc:g}% {{ translate: {xx:.1f}px calc({100 * g:.2f}cqh + {fall * g:.1f}px); }}\n" for pc, xx, g in pts) + "}")
        out.append(f"@keyframes ba-cin-spin-{sd} {{\n  from {{ rotate: 0deg; }}\n  to {{ rotate: {360 if spin > 0 else -360}deg; }}\n}}")
        out.append(f"@keyframes ba-cin-flip-{sd} {{\n  0%, 100% {{ scale: 1 1; }}\n  50% {{ scale: -1 1; }}\n}}")
        out.append(f"{DK_ASH} {every[h]} {{ /* 灰烬 ·{layer}{' · 边上还燃着' if burn else ''} */\n"
                   f"  background-image: {uri};\n  z-index: {z}; opacity: {op}; scale: 1 1; --ba-fl-x: {x}%; --ba-fl-s: {px}px;\n"
                   f"  top: calc(-20px - {px}px); transform-origin: 50% 50%;\n  animation:\n    ba-cin-fall-{sd} {t}s linear {d}s infinite,\n"
                   f"    ba-cin-spin-{sd} {abs(spin)}s linear {d}s infinite,\n    ba-cin-flip-{sd} {flip}s ease-in-out {d * .7:.1f}s infinite;\n}}")
    for h, sd, x, px, f, t, d, fl, amp, dx, t1, t2 in EMBERS:
        res = max(10, round(px * 2.5))
        uri = webp_uri(R.render_webp(DK.ember(res), res, res, quality=90))
        # 上升：越升越慢(热气流里的火星冷却变重)；四稿起按高度摆(_rise_path)，三个关键帧一起换名(ba-spk-rise / glow / flick → up / glw / flk，只换一个的话重载后上升和明暗对不上)
        pts = _rise_path(sd * 17 + 5, t, dx, amp, t1, t2)
        out.append(f"@keyframes ba-spk-up-{sd} {{\n"
                   + "".join(f"  {pc:g}% {{ translate: {xx:.1f}px {-100 * f * g:.2f}cqh; }}\n" for pc, xx, g in pts) + "}")
        # 透明度：淡入 → 忽明忽暗地慢慢暗下去 → 熄灭；闪烁的起伏按种子随机，每粒不一样
        rng = random.Random(sd * 31 + 7)
        env = lambda u: min(1, u / .08) * (1 - .3 * u) * min(1, (1 - u) / .25)   # noqa: E731
        glow = [(round(100 * kk / 20, 1), env(kk / 20) * (.62 + .38 * rng.random()) * .95) for kk in range(21)]
        out.append(f"@keyframes ba-spk-glw-{sd} {{\n" + "".join(f"  {pc:g}% {{ opacity: {o:.2f}; }}\n" for pc, o in glow) + "}")
        sc = [(0, 1)] + [(round(100 * kk / 6), round(.72 + .42 * rng.random(), 2)) for kk in range(1, 6)] + [(100, 1)]
        out.append(f"@keyframes ba-spk-flk-{sd} {{\n" + "".join(f"  {pc:g}% {{ scale: {v:g}; }}\n" for pc, v in sc) + "}")
        # 起点 = 标签组底边：包含块是整个标签组 / 叶子(底边对齐)的按 100%；标签栏里的那个按 100cqh(标签栏顶边 = 标签组顶边)
        out.append(f"{DK_ASH} {every[h]} {{ /* 火星{'(小)' if px < 6 else ''} */\n"
                   f"  background-image: {uri};\n  z-index: -1; opacity: 0; scale: 1; --ba-fl-x: {x}%; --ba-fl-s: {px}px;\n"
                   f"  top: calc({'100cqh' if in_bar(h) else '100%'} - {px}px); transform-origin: 50% 50%;\n  animation:\n    ba-spk-up-{sd} {t}s linear {d}s infinite,\n"
                   f"    ba-spk-glw-{sd} {t}s linear {d}s infinite,\n    ba-spk-flk-{sd} {fl}s ease-in-out {d}s infinite;\n}}")
    out.append("@media (prefers-reduced-motion: reduce) {\n  " + ",\n  ".join(f".theme-dark {x}" for x in extra) + " {\n    display: none;\n  }\n}")
    out.append(",\n".join(f"body.ba-no-feathers {x}" for x in extra) + " {\n  display: none;\n}")
    return "\n".join(out)


OUTLINE_DEPTH = 6   # 大纲最多几级嵌套(标题 H1–H6)


def outline_css() -> str:
    """大纲血线模式(第四十版)：圣杯图标 + 尺寸、按嵌套深度的血线锚点规则(静态部分见 theme.src.css「大纲面板 · 血线」)。
    图标几何在 tools/chalice.py：三只杯同宽、同一条中轴，只是高矮不同(有血滴的高)，所以各给一套 宽 / 高 / 竖向位置；
    杯的中轴在文字起点左边 13px、杯身竖向中点对行中线。
    --ba-ol-foot：父杯底沿在行中线下多远(血线从这里往上再藏 1px 到杯脚后面)；--ba-ol-reach：血线右端越过杯子盒子左缘多远
    (= 行中线高度上杯身左缘 + 0.5px 藏进杯后)；--ba-ol-arm：旧内核没有锚点时拐角的固定长度(下一级中轴 28px 外)"""
    import chalice as CH
    ic = CH.icons()
    par, leaf, reach = ic["parent"], ic["leaf"], ic["contact"] + 0.5
    p = 'body:not(.ba-outline-marker, .ba-outline-native) .workspace-leaf-content[data-type="outline"]'

    def box(v):
        return (f"width: {v['w']:.3f}px; height: {v['h']:.3f}px; top: calc(var(--ba-ol-row) / 2 - {v['mid']:.3f}px); "
                f"margin-inline-start: calc(-13px - {v['axis']:.3f}px);")
    out = ["/* ---- outline pane: chalice icons & blood thread anchors (generated by build.py outline_css) ---- */",
           f"{p} {{ --ba-ol-cup: {svg_uri(par['svg'])}; --ba-ol-cup-x: {svg_uri(ic['collapsed']['svg'])}; "
           f"--ba-ol-cup-o: {svg_uri(leaf['svg'])}; --ba-ol-foot: {par['bottom'] - 1:.3f}px; --ba-ol-reach: {reach:.3f}px; "
           f"--ba-ol-arm: {28 - par['axis'] + reach:.3f}px; }}",
           f"{p} .tree-item-inner::before {{ {box(leaf)} }}",
           f"{p} .tree-item-self.mod-collapsible > .tree-item-inner::before {{ {box(par)} }}"]
    for d in range(1, OUTLINE_DEPTH + 1):
        out.append(f"{p} {' '.join(['.tree-item'] * d)} {{ --ba-d: {d - 1}; }}")
    # 第四十二版(用户：收起 / 展开某级标题时整根血线跳一下、重新展开)：原来线按父项 .tree-item 定位，下端 bottom 锚到路径项的行中线——
    # bottom 量的是到父项底边的距离，收起 / 展开它下面的子项时父项变矮 / 变高，bottom 的数值跟着变(线的终点其实没动)，
    # transition: bottom 把这个变化播成动画：线先缩短再长回去。现在线按大纲的滚动区 .view-content 定位(面板高度，不随子项收起变化)，
    # 起点、终点都锚到悬停路径上的元素：路径上第 k 级那项的行 --ba-or{k}(中线)、文字 --ba-ot{k}(左缘 = 文字起点，杯的中轴在它左边 13px)、
    # 杯子 --ba-oq{k}(左缘)；第 d 级的线从第 d 级的杯脚流到第 d + 1 级的杯身左缘。选择器从列表根一级级写 :hover，只落在悬停路径上
    root = f"{p} .view-content > div > .tree-item:hover"
    out.append("@supports (anchor-name: --ba-x) {")
    for k in range(OUTLINE_DEPTH):
        s = root + " > .tree-item-children > .tree-item:hover" * k
        out.append(f"  {s} > .tree-item-self {{ anchor-name: --ba-or{k}; }}")
        out.append(f"  {s} > .tree-item-self > .tree-item-inner {{ anchor-name: --ba-ot{k}; }}")
        out.append(f"  {s} > .tree-item-self > .tree-item-inner::before {{ anchor-name: --ba-oq{k}; }}")
    for d in range(OUTLINE_DEPTH - 1):
        s = root + " > .tree-item-children > .tree-item:hover" * d
        out.append(f"  {s} > .tree-item-children::before {{ "
                   f"top: calc(anchor(--ba-or{d} center) + var(--ba-ol-foot)); left: calc(anchor(--ba-ot{d} left) - 13px - var(--ba-thread-w) / 2); "
                   f"bottom: calc(anchor(--ba-or{d + 1} center) - var(--ba-thread-w) / 2); right: calc(anchor(--ba-oq{d + 1} left) - var(--ba-ol-reach)); }}")
    out.append("}")
    return "\n".join(out)


def task_css() -> str:
    """任务复选框(第二十八版)：Style Settings「任务复选框样式」三选一——巴尔宝石(默认)/ 蜡封 / 原版。
    复选框放大到 1.125 倍(18px)；图都画在 ::after 上，按复选框的百分比溢出方框(宝石 1.15 倍、蜡封 1.25 倍)，不影响排版。
    宝石版每个状态是一张多色图(金托 + 着色符号 / 宝石)；蜡封是遮罩 + 蜡色 + 印刷颗粒(同 callout 图标)，未完成的金双圈画在复选框自己的背景上。
    选择器同时认阅读视图(li[data-task] > input，松散列表多一层 p)和实时预览(.HyperMD-task-line[data-task])；
    状态规则的特异性(0,6,2)高过基础的 :checked::after(0,5,2)。其他字符 Obsidian 也算勾选，按已完成画。
    属性栏里复选框类型的属性(archived 之类，正文属性栏和右侧栏属性面板)跟着同一个设置走(用户：要和所选复选框样式一致)：
    基础规则多认一个 .metadata-property-value > input.metadata-input-checkbox(放进 :is，特异性按最高的那个算，和原来一样)，只有未完成 / 完成两态"""
    box = "input.task-list-item-checkbox"
    gem, seal = "body:not(.ba-task-seal, .ba-task-native)", "body.ba-task-seal"
    on = "body:not(.ba-task-native)"

    def base(b, suffix=""):
        return (f"{b} :is(:is(.markdown-rendered, .markdown-source-view.mod-cm6) {box}, "
                f".metadata-property-value > input.metadata-input-checkbox){suffix}")

    def sel(b, ch, suffix=""):
        q = f"[data-task='{ch}']"
        return (f"{b} :is(.markdown-rendered li{q} > {box}, .markdown-rendered li{q} > p > {box}, "
                f".markdown-source-view.mod-cm6 .HyperMD-task-line{q} {box}){suffix}")

    def pos(r):
        o = f"{(1 - r) / 2 * 100:.2f}%"
        return f"top: {o}; inset-inline-start: {o}; width: {r * 100:.0f}%; height: {r * 100:.0f}%;"

    def img(svg):
        return f"background: {svg_uri(svg)} center / contain no-repeat; -webkit-mask: none; mask: none;"

    def wax(svg, kind):
        return (f"background: var(--ba-tag-grain) 0 0 / 256px 256px, {O.TASK_WAX[kind]}; "
                f"-webkit-mask: {svg_uri(svg)} center / contain no-repeat; mask: {svg_uri(svg)} center / contain no-repeat;")
    ring = f"background: {svg_uri(O.task_seal_ring())} center / 100% 100% no-repeat;"
    out = ["/* ---- task checkboxes (generated by build.py task_css from ornaments.TASK_STATES) ---- */",
           f"{base(on)} {{ width: calc(var(--checkbox-size) * 1.125); height: calc(var(--checkbox-size) * 1.125); "
           "border: 0; border-radius: 50%; background: none; overflow: visible; }",
           f"{base(on, ':checked')} {{ background: none; }}",
           f"{base(on, '::after')} {{ content: ''; display: block; position: absolute; pointer-events: none; background-color: transparent; }}",
           f"{base(on, ':hover')} {{ filter: brightness(0.9); }}",
           # 巴尔宝石
           f"{base(gem, '::after')} {{ {pos(1.15)} {img(O.task_bezel())} }}",
           f"{base(gem, ':checked::after')} {{ {img(O.task_gem(DK.GEM_GLINT if DK.ON else None))} }}",
           f"{sel(gem, '/', '::after')} {{ {img(O.task_gem_drop(glint=DK.GEM_GLINT if DK.ON else None))} }}",
           # 蜡封
           f"{base(seal)} {{ {ring} }}",
           f"{base(seal, ':checked')} {{ background: none; }}",
           f"{base(seal, '::after')} {{ display: none; }}",
           f"{base(seal, ':checked::after')} {{ display: block; {pos(1.25)} {wax(O.task_seal(O.TASK_SEAL_DONE), 'red')} }}",
           f"{sel(seal, '/')} {{ {ring} }}",
           f"{sel(seal, '/', '::after')} {{ {wax(O.task_seal_drop(), 'red')} }}"]
    for ch, (g, kind) in O.TASK_STATES.items():
        out.append(f"{sel(gem, ch, '::after')} {{ {img(O.task_bezel(g, kind))} }}")
        out.append(f"{sel(seal, ch, '::after')} {{ {wax(O.task_seal(g), kind)} }}")
    # 只有完成(x 及 Obsidian 认作勾选的其他字符)和取消划线变灰，其余扩展状态保持正文样式；Obsidian 自己只给 x 划线，取消要补上
    done = "text-decoration: var(--checklist-done-decoration); color: var(--checklist-done-color);"
    out.append(f"{on} .markdown-rendered li.task-list-item[data-task='-'], {on} .markdown-source-view.mod-cm6 .HyperMD-task-line[data-task='-'] {{ {done} }}")
    keep = ", ".join(f"[data-task='{ch}']" for ch in ["/"] + [c for c in O.TASK_STATES if c != "-"])
    out.append(f"{on} .markdown-rendered li.task-list-item:is({keep}) {{ text-decoration: none; color: var(--text-normal); }}")
    out.append(f"{on} .markdown-source-view.mod-cm6 .HyperMD-task-line:is({keep}), {on} .markdown-source-view.mod-cm6 .HyperMD-task-line:is({keep}) * "
               "{ text-decoration: none; color: var(--text-normal); }")
    # 实时预览里复选框后面那个空格和正文在同一个 span 里，删除线从空格就开始画，复选框和字之间露一小段横线(原版也这样)。
    # CSS 不能单独不划某个字，改用遮罩把这个 span 开头 0.2em 抹掉(空格本来就是空白，只抹掉那段线；
    # 行内元素的遮罩按各行片段连成一条算，折行后只影响第一行开头)
    struck = ":is([data-task='x'], [data-task='X'], [data-task='-'])"
    first = ", ".join(f"{on} .markdown-source-view.mod-cm6 .HyperMD-task-line{struck} .task-list-label + {x}"
                      for x in ("img.cm-widgetBuffer + span", "span"))
    out.append(f"{first} {{ -webkit-mask: linear-gradient(to right, transparent 0.2em, #000 0.2em); "
               "mask: linear-gradient(to right, transparent 0.2em, #000 0.2em); }")
    return "\n".join(out)


# ---- Mermaid：按图表类型(svg 的 aria-roledescription)改色(第二十九版，照搬 Nox Aeterna build.py mermaid_css 的结构) ----
MM = {"F": "flowchart-v2", "S": "stateDiagram", "Q": "sequence", "C": "class", "E": "er",
      "G": "gantt", "P": "pie", "M": "mindmap", "T": "timeline",
      "J": "journey", "R": "gitGraph", "U": "quadrantChart", "X": "xychart"}
MM_SECTIONS = 6     # theme.src.css 里的分组色 --ba-mm-c0..5


def mermaid_css() -> str:
    """Mermaid 每张图自带一段 `#图id .node rect { … }` 样式。选择器里的 :is(svg, #ba-mermaid) 带一个用不到的 id，
    特异性压过它们又不用 !important：用户在图里写的 classDef / style(Mermaid 输出成内联或 !important)照样优先。
    不在 MM 里的图表类型保留 theme.src.css 里的滤镜"""
    def pre(types: str) -> str:
        roles = ", ".join(f'[aria-roledescription="{MM[t]}"]' for t in types)
        return f".mermaid > :is(svg, #ba-mermaid):is({roles})"

    def tint(c, k):
        return f"color-mix(in srgb, {c} {k}%, var(--ba-mm-fill))"

    ALL, NODE = "".join(MM), "FSCE"
    ivory = "var(--ba-mm-fill)"
    # 用户自定义了填充色的节点(classDef / style)：文字颜色也交给用户。
    # 第三十七版性能(用户：编辑视图滚动卡)：原来写成 :not(:where(.node:has(…) *))——:has() 后面接通配符，见 feathers_css 开头的说明；
    # 后来 :has() 只给这种节点挂个标记，带 own 的文字规则包进样式查询，在标记底下不生效。
    # 第四十二版性能(用户：大纲里拖标题严重卡顿)：标记写成 .node:has(> [style*='fill'])，:has() 参数里有 style 属性——
    # 页面上任何元素的内联 style 一变(拖动时跟着鼠标的提示框、虚拟列表的占位高度、CodeMirror 的光标)，浏览器都要沿祖先查一遍 :has()，
    # 碰上高层锚点就整片重算(_ol_drag.py：去掉它拖动每帧 60 → 38ms，连同主区标签那条 → 20ms)。现在不用 :has()：
    # 经典形状(rect / polygon / circle / path 直接挂在节点下，文字 .label 是它后面的兄弟，流程图、状态图)用兄弟选择器把标记挂到 .label 上；
    # classDef 会给节点加类名(流程图、类图的节点本来是 "node default")，类名多出来就算。
    # 认不出的只有 Mermaid 11 新形状 / 类图只用 style 指令改填充(样式在内层 g 的 path 上)，文字照主题色
    own = "@@OWN@@"
    shape = ":is(rect, circle, ellipse, polygon, path)"
    rules = [
        (ALL, [""], "filter: none;"),
        (ALL, [f":is(text, tspan){own}"], "fill: var(--ba-mm-text);"),
        (ALL, [f":is(span, p){own}"], "color: var(--ba-mm-text);"),
        # 节点：Mermaid 11 的不少形状是一对 path(一条只填色 stroke=none、一条只描边 fill=none)，按属性分开上色
        (NODE, [f".node {shape}:not(:where(.label *, [fill='none']))"], "fill: var(--ba-mm-fill);"),
        (NODE, [f".node {shape}:not(:where(.label *, [stroke='none']))"], "stroke: var(--ba-mm-line);"),
        # 连线与箭头：红粉笔
        (NODE, [":is(.flowchart-link, .transition, .relation, .relationshipLine, .edgePath .path)"], "stroke: var(--ba-mm-edge);"),
        ("FS", ["marker :is(path, circle)"], "fill: var(--ba-mm-edge); stroke: var(--ba-mm-edge);"),
        # 类图箭头的颜色 Mermaid 写在 marker 上(带 !important)，改在里面的 path 上(继承来的值不论 !important)；空心的继承 + 聚合不填色
        ("C", ["marker.marker :is(path, circle)"], "stroke: var(--ba-mm-edge);"),
        ("C", ["marker:is(.composition, .dependency) path"], "fill: var(--ba-mm-edge);"),
        ("E", ["marker path"], "fill: none; stroke: var(--ba-mm-edge);"),
        ("E", ["marker circle"], "fill: var(--ba-mm-bg); stroke: var(--ba-mm-edge);"),
        # 连线上的文字：底色换成页面底色
        (NODE, [":is(.edgeLabel, .edgeLabel p, .labelBkg)"], "background-color: var(--ba-mm-bg);"),
        (NODE, [".edgeLabel rect"], "fill: var(--ba-mm-bg); opacity: 1;"),
        (NODE, [f":is(.edgeLabel, .edgeTerminals) :is(span, p){own}"], "color: var(--ba-mm-label);"),
        # 子图 / 复合状态：淡金底、深一档的细线、圣血红标题
        ("F", [".cluster > rect"], "fill: var(--ba-mm-group); stroke: var(--ba-mm-group-line);"),
        ("S", [".statediagram-cluster rect.outer"], "fill: var(--ba-mm-fill); stroke: var(--ba-mm-line);"),
        ("S", [".statediagram-cluster rect.inner"], "fill: var(--ba-mm-group); stroke: var(--ba-mm-line);"),
        ("FS", [".cluster-label :is(span, p, text, tspan)"], "fill: var(--ba-mm-title); color: var(--ba-mm-title);"),
        # 类名、实体名用标题色；ER 的 PK / FK 用圣血红，属性行隔行淡金
        ("C", [".label-group :is(span, p)"], "color: var(--ba-mm-title);"),
        ("C", [".annotation-group :is(span, p)"], "color: var(--ba-mm-label);"),
        # 类图注释框的颜色被 Mermaid 写成内联 !important，CSS 盖不掉：用滤镜把淡黄底 / 橄榄框映射成淡金 / 金(拟合值，误差 2/255 以内)
        ("C", [".node[id^='note'] > .label-container"],
         "filter: invert(0.067) saturate(1.048) hue-rotate(343.2deg) brightness(1.076) contrast(0.914);"),
        ("E", [".label.name :is(span, p)"], "color: var(--ba-mm-title);"),
        ("E", [".label.attribute-keys :is(span, p)"], "color: var(--ba-mm-accent);"),
        ("E", [":is(.row-rect-odd, .row-rect-even) path:not([fill='none'])"], f"fill: {ivory};"),
        ("E", [".row-rect-even path:not([fill='none'])"], f"fill: {tint('var(--ba-gold-pale)', 45)};"),
        ("E", [":is(.row-rect-odd, .row-rect-even, .divider) path:not([stroke='none'])"], "stroke: var(--ba-mm-line-soft);"),
        # 状态图：起点实心圣血红点、终点靶心、分叉 / 汇合横条用连线色
        ("S", ["circle.state-start"], "fill: var(--ba-mm-accent); stroke: var(--ba-mm-accent);"),
        ("S", [".node[id*='_end-'] > g > path:not([stroke='none'])"], "stroke: var(--ba-mm-accent);"),
        ("S", [".node[id*='_end-'] > g > g > path"], "fill: var(--ba-mm-accent); stroke: var(--ba-mm-accent);"),
        ("S", [".statediagram-state > g > path[fill='#333333']"], "fill: var(--ba-mm-edge);"),
        ("S", [".statediagram-state > g > path[stroke='#333333']"], "stroke: var(--ba-mm-edge);"),
        # 注释：纯洁封印纸条的淡金
        ("S", [".statediagram-note .label-container > path:not([fill='none'])"], "fill: var(--ba-mm-note);"),
        ("S", [".statediagram-note .label-container > path:not([stroke='none'])"], "stroke: var(--ba-mm-note-line);"),
        ("Q", ["rect.note"], "fill: var(--ba-mm-note); stroke: var(--ba-mm-note-line);"),
        ("SC", [".node:is(.statediagram-note, [id^='note']) :is(span, p)"], "color: var(--ba-mm-note-text);"),
        ("Q", [":is(.noteText, .noteText > tspan)"], "fill: var(--ba-mm-note-text);"),
        # 时序图：参与者 = 象牙底金边，生命线细金，编号 = 圣血红圆里象牙字，loop / alt 框 = 群青
        ("Q", ["rect.actor"], "fill: var(--ba-mm-fill); stroke: var(--ba-mm-line);"),
        ("Q", [".actor-man :is(line, circle)"], "fill: var(--ba-mm-fill); stroke: var(--ba-mm-line);"),
        ("Q", [".actor-line"], "stroke: var(--ba-mm-line-soft);"),
        ("Q", [":is(.messageLine0, .messageLine1)"], "stroke: var(--ba-mm-edge);"),
        ("Q", ["marker path"], "fill: var(--ba-mm-edge); stroke: var(--ba-mm-edge);"),
        ("Q", ["marker[id$='crosshead'] path"], "fill: none;"),
        ("Q", ["marker circle"], "fill: var(--ba-mm-accent); stroke: var(--ba-mm-accent);"),
        ("Q", [".sequenceNumber"], f"fill: {ivory};"),
        ("Q", [":is(.activation0, .activation1, .activation2)"], f"fill: {tint('var(--ba-gold-pale)', 70)}; stroke: var(--ba-mm-line);"),
        ("Q", [".loopLine"], "stroke: var(--ba-mm-loop);"),
        ("Q", [".labelBox"], f"fill: {tint('var(--ba-mm-loop)', 12)}; stroke: var(--ba-mm-loop);"),
        ("Q", [":is(.labelText, .labelText > tspan, .loopText, .loopText > tspan)"], "fill: var(--ba-mm-loop);"),
        # 甘特图：分区隔行淡金底；任务 = 淡金 / 进行中 = 金 / 完成 = 旧纸 / 关键 = 淡圣血红
        ("G", [":is(.section0, .section2)"], "fill: color-mix(in srgb, var(--ba-gold-pale) 35%, transparent); opacity: 1;"),
        ("G", [":is(.section1, .section3)"], "fill: transparent;"),
        ("G", [".grid .tick line"], "stroke: var(--ba-rule); opacity: 1;"),
        ("G", [".grid .tick text"], "fill: var(--ba-mm-label);"),
        ("G", [".grid .domain"], "fill: none; stroke: none;"),
        ("G", [".exclude-range"], "fill: var(--ba-paper-3);"),
        ("G", [":is(.task0, .task1, .task2, .task3)"], f"fill: {tint('var(--ba-gold-pale)', 80)}; stroke: var(--ba-mm-line);"),
        ("G", [":is(.active0, .active1, .active2, .active3)"], f"fill: {tint('var(--ba-gold)', 50)}; stroke: var(--ba-gold-deep);"),
        ("G", [":is(.done0, .done1, .done2, .done3)"], "fill: var(--ba-paper-3); stroke: var(--ba-rule-strong);"),
        ("G", [":is(.crit0, .crit1, .crit2, .crit3)"], f"fill: {tint('var(--ba-crimson)', 22)}; stroke: var(--ba-mm-accent);"),
        ("G", [":is(.activeCrit0, .activeCrit1, .activeCrit2, .activeCrit3)"], f"fill: {tint('var(--ba-crimson)', 38)}; stroke: var(--ba-blood);"),
        ("G", [":is(.doneCrit0, .doneCrit1, .doneCrit2, .doneCrit3)"], "fill: var(--ba-paper-3); stroke: color-mix(in srgb, var(--ba-crimson) 55%, transparent);"),
        ("G", [".milestone"], f"fill: {tint('var(--ba-gold)', 50)}; stroke: var(--ba-gold-deep);"),
        # 任务文字的颜色 Mermaid 大多写成 !important(甘特图没有 classDef，用户改不了这些，跟着 !important 不碍事)
        ("G", [":is(.taskText, .taskTextOutsideRight, .taskTextOutsideLeft)"], "fill: var(--ba-mm-text) !important;"),
        ("G", [":is(.doneText0, .doneText1, .doneText2, .doneText3, .doneCritText0, .doneCritText1, .doneCritText2, .doneCritText3)"],
         "fill: var(--ba-mm-label) !important;"),
        ("G", [":is(.taskText, .taskTextOutsideRight, .taskTextOutsideLeft).clickable"], "fill: var(--ba-lapis) !important;"),
        ("G", [".vertText"], "fill: var(--ba-mm-accent) !important;"),
        ("G", [":is(.sectionTitle, .sectionTitle > tspan)"], "fill: var(--ba-mm-title);"),
        ("G", [":is(.today, .vert)"], "stroke: var(--ba-mm-accent);"),
        # 饼图：扇区间用页面底色勾缝，外圈金线
        ("P", [".pieCircle"], "stroke: var(--ba-mm-bg); stroke-width: 2px; opacity: 1;"),
        ("P", [".pieOuterCircle"], "stroke: var(--ba-mm-line); stroke-width: 1px;"),
        ("P", ["text.slice"], f"fill: {ivory};"),
        # 时间线连线
        ("T", [".lineWrapper line"], "stroke: var(--ba-mm-edge);"),
        ("T", ["marker path"], "fill: var(--ba-mm-edge);"),
        # 旅程图：笑脸淡金、任务虚线细金、坐标轴墨色
        ("J", ["> text"], "font-family: var(--font-mermaid);"),     # 标题字体 Mermaid 写在属性上(trebuchet ms)，换回图里的字体
        ("J", ["circle.face"], "fill: var(--ba-gold-pale); stroke: var(--ba-gold-deep);"),
        ("J", [".mouth"], "stroke: var(--ba-mm-label);"),
        ("J", ["line.task-line"], "stroke: var(--ba-rule-strong);"),
        ("J", ["> line", "marker path"], "stroke: var(--ba-mm-label); fill: var(--ba-mm-label);"),
        # git 图：分支泳道细金线，合并点空心，提交说明象牙底，标签淡金
        ("R", ["line.branch"], "stroke: var(--ba-rule-strong);"),
        ("R", [".branchLabel :is(text, tspan)"], f"fill: {ivory};"),
        ("R", ["rect.commit-label-bkg"], "fill: var(--ba-mm-fill); opacity: 0.85;"),
        ("R", ["text.commit-label"], "fill: var(--ba-mm-label);"),
        ("R", ["rect.tag-label-bkg"], "fill: var(--ba-gold-pale); stroke: var(--ba-gold);"),
        ("R", ["text.tag-label"], "fill: var(--ba-mm-text);"),
        ("R", ["circle.tag-hole"], "fill: var(--ba-mm-label);"),
        ("R", [".commit-highlight-inner"], "fill: var(--ba-mm-bg);"),
        # 象限图：对角两格淡金(棋盘)，边框金线(Mermaid 写成内联样式，只能 !important)，默认的点圣血红(用户自定义了颜色的点不动)
        ("U", [".quadrant:nth-child(odd) rect"], f"fill: {tint('var(--ba-gold-pale)', 45)};"),
        ("U", [".quadrant:nth-child(even) rect"], "fill: var(--ba-mm-fill);"),
        ("U", [".quadrant text"], "fill: var(--ba-gold-deep);"),
        ("U", [".border line"], "stroke: var(--ba-mm-line) !important;"),
        ("U", [".data-point circle[fill^='hsl(240']"], "fill: var(--ba-mm-accent); stroke: var(--ba-mm-accent);"),
        ("U", [".labels text"], "fill: var(--ba-mm-label);"),
        # XY 图：去掉白底，坐标轴墨色
        ("X", ["rect.background"], "fill: transparent;"),
        ("X", [":is(.bottom-axis, .left-axis, .top-axis, .right-axis) path"], "stroke: var(--ba-ink-3);"),
        ("X", [":is(.bottom-axis, .left-axis, .top-axis, .right-axis) text"], "fill: var(--ba-mm-label);"),
    ]
    # 分组色循环：思维导图分支、时间线时段(-1 起)、饼图扇区和图例(图例色是内联样式，只能 !important)
    for n in range(-1, 12):
        k = (n + 1) % MM_SECTIONS
        c = f"var(--ba-mm-c{k})"
        rules += [
            ("MT", [f".section-{n} {shape}:not(:where(.label *))"], f"fill: {tint(c, 16)}; stroke: {tint(c, 55)};"),
            ("MT", [f".section-{n} line"], f"stroke: {c};"),
            ("M", [f".section-edge-{n}"], f"stroke: color-mix(in srgb, {c} 70%, transparent);"),
        ]
    # 旅程图分段 / 任务、git 图分支(Mermaid 各有 8 种)、XY 图每组数据：颜料色循环
    for k in range(8):
        c = f"var(--ba-mm-c{k % MM_SECTIONS})"
        rules += [
            ("J", [f"rect.journey-section.section-type-{k}"], f"fill: {tint(c, 22)}; stroke: {tint(c, 55)};"),
            ("J", [f"rect.task.task-type-{k}"], f"fill: {tint(c, 8)}; stroke: {tint(c, 55)};"),
            ("J", [f"circle.actor-{k}"], f"fill: {c}; stroke: var(--ba-mm-fill);"),
            ("R", [f"rect.label{k}", f".commit{k}", f".commit-highlight{k}"], f"fill: {c}; stroke: {c};"),
            ("R", [f".arrow{k}"], f"stroke: {c};"),
            ("X", [f".bar-plot-{k} rect"], f"fill: {tint(c, 60)}; stroke: {tint(c, 60)};"),
            ("X", [f".line-plot-{k} path"], f"stroke: {c};"),
        ]
    rules.append(("R", ["circle.commit-merge"], "fill: var(--ba-mm-bg);"))
    for k in range(MM_SECTIONS):
        fill = tint(f"var(--ba-mm-c{k})", 78)
        rules += [
            ("P", [f"path.pieCircle:nth-of-type({MM_SECTIONS}n + {k + 1})"], f"fill: {fill};"),
            ("P", [f"g.legend:nth-of-type({MM_SECTIONS}n + {k + 1}) rect"], f"fill: {fill} !important; stroke: {fill} !important;"),
        ]
    # 思维导图根节点(同时带 section--1，要排在分组色后面)：圣血红底、象牙字
    rules.append(("M", [f".section-root {shape}:not(:where(.label *))"], "fill: var(--ba-mm-accent); stroke: var(--ba-blood);"))
    rules.append(("M", [".section-root :is(span, p, text, tspan)"], f"color: {ivory}; fill: {ivory};"))
    out = ["/* ---- Mermaid colours (generated by build.py mermaid_css) ---- */",
           f"{pre(ALL)} .node > [style*='fill'] ~ .label,\n{pre('FC')} .node.default:not([class='node default']) {{ --ba-mm-own: 1; }}"]
    for types, inner, decl in rules:
        sels = ",\n".join(f"{pre(types)} {s}".rstrip() for s in inner)
        rule = f"{sels} {{ {decl} }}"
        if own in sels:
            rule = "@container not style(--ba-mm-own: 1) {\n" + rule.replace(own, "") + "\n}"
        out.append(rule)
    return "\n".join(out)


def settings_lang_css(src: str) -> str:
    """Style Settings「设置语言」强制中文 / English(同 Nox Aeterna build.py settings_lang_css，前缀 ba-)：
    按 data-id 把设置项名称、说明换成另一种语言。
    下拉选项的文字插件不支持多语言(只认 label)：照永夜，支持可自定义下拉框的内核上按语言换文字(见下)，旧内核原样显示 label(英文)"""
    import yaml
    m = re.search(r"/\* @settings\s*\n(.*?)\n\*/", src, re.S)
    items = yaml.safe_load(m.group(1))["settings"]
    q = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    scope = ".style-settings-container"
    sel = lambda sid, part: f'{scope} .setting-item[data-id="{sid}"] > .setting-item-info > .setting-item-{part}'
    ids = [s["id"] for s in items if "title.zh" in s]
    desc_ids = [s["id"] for s in items if "description.zh" in s]
    forced = "body:is(.ba-lang-zh, .ba-lang-en)"
    out = [f"{forced} :is({', '.join(sel(i, 'name') for i in ids)}) {{ font-size: 0; }}",
           f"{forced} :is({', '.join(sel(i, 'name') for i in ids)})::after {{ font-size: var(--setting-item-name-size); }}",
           f"{forced} {scope} .setting-item-heading > .setting-item-info > .setting-item-name::after {{ font-size: var(--setting-group-heading-size); }}"]
    if desc_ids:
        out += [f"{forced} :is({', '.join(sel(i, 'description') for i in desc_ids)}) {{ font-size: 0; }}",
                f"{forced} :is({', '.join(sel(i, 'description') for i in desc_ids)})::before {{ font-size: var(--font-ui-smaller); }}"]
    for s in items:
        if "title.zh" not in s:
            continue
        for cls, key in (("ba-lang-en", "title"), ("ba-lang-zh", "title.zh")):
            out.append(f"body.{cls} {sel(s['id'], 'name')}::after {{ content: {q(s[key])}; }}")
        if "description.zh" in s:
            for cls, key in (("ba-lang-en", "description"), ("ba-lang-zh", "description.zh")):
                out.append(f"body.{cls} {sel(s['id'], 'description')}::before {{ content: {q(s[key])}; }}")

    # ---- 下拉框(第五十版，用户：下拉选项不要中英文用点隔开，按「设置语言」只留一种；照永夜 Nox Aeterna 的做法)：
    # 选项文字插件只认 label，原生下拉列表的文字 CSS 也改不了。用可自定义下拉框(appearance: base-select，Chromium 135+；
    # Obsidian 1.14 = Chromium 150)把选项变成普通元素，按 value 换文字；收起时显示的文字用 select::before，
    # 按 body 上的选中值类名挑(class-select 的选中项本来就挂成 body 类，不用 :has)。
    # 跟随语言：强制中文 / English 看 body 类；跟随 Obsidian 时看 <html lang>(Obsidian 把界面语言写在这里)。
    # 清单里 label = 英文、label.zh = 中文(插件忽略 label.zh)；插件给下拉框说明自动加的「默认值：xxx」行显示原始 label，藏掉
    zh = ":is(html:lang(zh) body:not(.ba-lang-en), body.ba-lang-zh)"
    en = ":is(html:not(:lang(zh)) body:not(.ba-lang-zh), body.ba-lang-en)"
    selects = [s for s in items if s.get("type") == "class-select" and all("label.zh" in o for o in s["options"])]
    if selects:
        # 整段包在 @supports 里：旧内核(Chromium < 135)不认 base-select，原文字号压 0 后下拉框会变空白
        out.append("@supports (appearance: base-select) {")
        dd = lambda sid: f'{scope} .setting-item[data-id="{sid}"] > .setting-item-control > select.dropdown'
        allsel = ", ".join(dd(s["id"]) for s in selects)
        out += [
            f":is({allsel}), :is({allsel})::picker(select) {{ appearance: base-select; }}",
            # 原文字号压 0 藏起来；原版下拉框的内边距 / 右侧箭头尺寸和位置都按 em 算(会跟着归零)，改按界面小字号
            # (= 原版下拉框字号)换算回原值；宽度按显示的文字自适应，不用 Obsidian 按原文量出的 --dropdown-fitted-width
            f":is({allsel}) {{ font-size: 0; width: max-content; "
            f"padding: 0 calc(var(--font-ui-small) * 2.4) 0 calc(var(--font-ui-small) * 0.8); "
            f"background-size: var(--font-ui-small) auto, calc(var(--font-ui-small) * 2) calc(var(--font-ui-small) * 2); "
            f"background-position: right calc(var(--font-ui-small) * 0.65) top 50%, right calc(var(--font-ui-small) * 0.15) top 50%; }}",
            f":is({allsel})::picker-icon {{ display: none; }}",
            f":is({allsel}) {{ display: inline-flex; align-items: center; }}",
            f":is({allsel})::before {{ font-size: var(--font-ui-small); line-height: normal; white-space: nowrap; }}",
            # 展开的列表：纸色底 + 淡金细框 + 暖褐柔和投影(同 tooltip / 弹窗的日间调子)，选中项圣血红
            f":is({allsel})::picker(select) {{ margin-block: 4px; padding: 4px; border: 1px solid color-mix(in srgb, var(--ba-gold) 45%, transparent); "
            f"border-radius: var(--radius-m); background-color: var(--background-primary); box-shadow: 0 6px 18px rgba(var(--ba-shadow), 0.18); }}",
            f":is({allsel}) option {{ gap: 6px; padding: 5px 12px 5px 6px; border-radius: var(--radius-s); color: var(--text-normal); background-color: transparent; font-size: 0; }}",
            f":is({allsel}) option:is(:hover, :focus-visible) {{ outline: none; background-color: var(--background-modifier-hover); }}",
            f":is({allsel}) option:checked {{ color: var(--ba-crimson); }}",
            f":is({allsel}) option::after {{ font-size: var(--font-ui-small); }}",
            f":is({allsel}) option::checkmark {{ font-size: var(--font-ui-small); color: var(--ba-crimson); }}",
        ]
        for s in selects:
            sid = s["id"]
            info = f'{scope} .setting-item[data-id="{sid}"] > .setting-item-info > .setting-item-description'
            out.append(f"{info} > div {{ display: none; }}" if "description" in s else f"{info} {{ display: none; }}")
            vals = [o["value"] for o in s["options"]]
            for lang, key in ((zh, "label.zh"), (en, "label")):
                for o in s["options"]:
                    out.append(f"{lang}.{o['value']} {dd(sid)}::before {{ content: {q(o[key])}; }}")
                    out.append(f"{lang} {dd(sid)} option[value=\"{o['value']}\"]::after {{ content: {q(o[key])}; }}")
                default = next((o for o in s["options"] if o["value"] == s.get("default")), s["options"][0])
                not_any = ", ".join("." + v for v in vals)
                out.append(f"{lang}:not({not_any}) {dd(sid)}::before {{ content: {q(default[key])}; }}")
        out.append("}")
    # 滑块下面插件也自动加一行「默认：xxx」(按 Obsidian 界面语言，切成 English 也还是中文)；用户：纹理浓度、暗角浓度、卡片间距下面的小字不要、
    # 正文宽度的「默认 46」去掉——所有滑块都藏掉这行(有说明的只藏这一行)
    for s in items:
        if s.get("type") == "variable-number-slider":
            info = f'{scope} .setting-item[data-id="{s["id"]}"] > .setting-item-info > .setting-item-description'
            out.append(f"{info} > div {{ display: none; }}" if "description" in s else f"{info} {{ display: none; }}")
    return "\n".join(out)


def dedupe_uris(css: str, min_len: int = 2048) -> str:
    """同一张内嵌图在几条规则里重复出现时只嵌一次(第十五版，给中文标题字体腾体积)：挪进 :root 的自定义属性，
    原处换成 var()。字体(@font-face 里不能用 var())本来也不重复，跳过"""
    pat = re.compile(r'url\("data:(?!font/)[^"]+"\)')
    counts = {}
    for m in pat.finditer(css):
        if len(m.group(0)) >= min_len:
            counts[m.group(0)] = counts.get(m.group(0), 0) + 1
    dups = [u for u, n in counts.items() if n > 1]
    if not dups:
        return css
    names = {u: f"--ba-u{i}" for i, u in enumerate(dups)}
    css = pat.sub(lambda m: f"var({names[m.group(0)]})" if m.group(0) in names else m.group(0), css)
    return css + "\n/* 重复用到的内嵌图，只嵌一次(build.dedupe_uris) */\n:root {\n" + "".join(f"  {n}: {u};\n" for u, n in names.items()) + "}\n"


def minify_css(css: str) -> str:
    """第五十三版(上架体积)：去掉注释、缩进和空行。开头的署名 / 许可注释、Style Settings 的 /* @settings */ 块
    (插件按注释读设置，块里是 YAML，缩进不能动)和字符串(含所有 data URI)原样照抄"""
    tok = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|/\*[\s\S]*?\*/')
    pieces, code, pos = [], [], 0          # pieces: 原样照抄的段 / 待压缩的代码段交替
    for m in tok.finditer(css):
        code.append(css[pos:m.start()])
        t = m.group(0)
        if t.startswith("/*") and not (m.start() == 0 or t[2:].lstrip().startswith("@settings")):
            code.append(" ")               # 丢掉的注释留一个空格，免得两边的字粘在一起
        else:
            pieces += ["".join(code), t]
            code = []
        pos = m.end()
    code.append(css[pos:])
    pieces.append("".join(code))

    def squeeze(s):
        s = re.sub(r"[ \t]+", " ", s)
        return re.sub(r" ?\n[\n ]*", "\n", s)
    return "".join(squeeze(p) if i % 2 == 0 else p for i, p in enumerate(pieces))


def build() -> Path:
    src = (ROOT / "src" / "theme.src.css").read_text(encoding="utf-8")
    lit = re.compile(r"@@LIT:([A-Z]+:[a-z0-9-]+)@@")

    def assemble(table):
        def sub(m):
            key = m.group(1)
            if key not in table:
                raise KeyError(f"unknown placeholder @@{key}@@")
            return table[key]
        css = re.sub(r"@@([A-Z]+:[a-z0-9-]+)@@", sub, src)
        css = css.replace("@@FEATHER-GROUP@@", FEATHER_GROUP)
        css = css.replace("/*@@CALLOUT-ICONS@@*/", callout_icon_css())
        css = css.replace("/*@@TASK-CHECKBOX@@*/", task_css())
        css = css.replace("/*@@OUTLINE-THREAD@@*/", outline_css())
        css = css.replace("/*@@FEATHERS@@*/", feathers_css())
        css = css.replace("/*@@EMBERS@@*/", embers_css())
        css = css.replace("/*@@MERMAID@@*/", mermaid_css())
        css = css.replace("/*@@SETTINGS-LANG@@*/", settings_lang_css(src))
        return css
    # 夜间：装饰图和生成的 CSS 换夜间色再出一遍，逐条对照日间那遍，给日间专用 / 值不同的规则插上夜间版(tools/dark.py)；
    # 夜间那遍的 @@LIT@@ 占位符换成 -dk 键，去重之后填夜间的图。手写的 .theme-dark 规则里可以用 @@ORN:键-dk@@ 直接引夜间版的图
    table = ornaments()
    with DK.mode():
        table_dk = ornaments()
    dk = {f"{k}-dk": v for k, v in table_dk.items()}
    css = assemble({**table, **dk})
    with DK.mode():
        css_dk = lit.sub(lambda m: f"@@LIT:{m.group(1)}-dk@@", assemble({**table_dk, **dk}))
    css, n_dk = DK.twins(css, css_dk)
    table.update(dk)
    print(f"夜间：{n_dk} 条夜间规则；装饰图里按公式换色 {len(DK.UNLISTED)} 种")
    if "--dark-report" in sys.argv:
        for k, v in sorted(DK.UNLISTED.items(), key=lambda kv: DK.oklch(kv[0])[2]):
            print(f"  {k} -> {v}")
        for k, v in sorted(DK.REVIEW.items()):
            print(f"  [{v}] {k}")
    css = css.replace("/*@@FONTS@@*/", font_faces())

    def sub(m):
        return table[m.group(1)]
    # @@LIT:键@@：去重之后再填，保持字面 data URI、不换成 var()(第四十八版)——var() 引几百 KB 的图，用到它的元素每次重算样式
    # 都要把整张图重新代入解析一遍(功能栏自动隐藏滑出时功能栏 + 左栏一次 25~45ms)；字面值解析一次、所有匹配的元素共用
    left = [p for p in re.findall(r"@@[^@\s]+@@", css) if not lit.fullmatch(p)]
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    css = dedupe_uris(css)
    css = lit.sub(sub, css)
    css = minify_css(css)
    (DIST / "theme.css").write_text(css, encoding="utf-8")
    manifest = {"name": THEME_NAME, "version": VERSION, "minAppVersion": "1.6.0",
                "author": "whitedry", "authorUrl": "https://github.com/white0dry"}
    (DIST / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"built {DIST / 'theme.css'}  ({(DIST / 'theme.css').stat().st_size // 1024} KB)")
    SNIPPET.parent.mkdir(exist_ok=True)
    for path, text in ((SNIPPET, heading_snippet()), (SNIPPET_BODY, body_snippet())):
        path.write_text(text, encoding="utf-8")
        print(f"built {path}  ({path.stat().st_size // 1024} KB)")
    return DIST


if __name__ == "__main__":
    out = build()
    if "--install" in sys.argv:
        demo = ROOT / "demo-vault" / ".obsidian" / "themes" / THEME_NAME
        demo.mkdir(parents=True, exist_ok=True)
        for f in ("theme.css", "manifest.json"):
            shutil.copy2(out / f, demo / f)
        print("installed ->", demo)
