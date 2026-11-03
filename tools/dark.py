# -*- coding: utf-8 -*-
"""夜间模式(2026-11-03，B2 底色 + b 血色横幅)：装饰图换色、规则里写死颜色的夜间对应、夜间纸纹，以及按日间规则自动生成夜间规则。

构建分两遍(build.build)：日间照旧；夜间在 mode() 里再跑一遍装饰图 / 生成的 CSS——build.svg_uri 和 raster.render_webp 先把 SVG 里的颜色
换成夜间色(svg_color)再编码 / 渲染，所以从 SVG 渲染出来的位图(标题徽记的绶带、新标签页题铭、飘落羽毛)也一起换色。
两遍拼出来的 CSS 结构完全相同、只有值不同，twins() 逐条对照：
- 选择器里有 .theme-light 的规则(纸纹、代码块铭板、羽毛……日间专用)整条复制一份 .theme-dark 版，值用夜间那遍的；
- 其他规则只复制「夜间值不同」的那几条声明(装饰图、写死的颜色)，选择器加 :where(.theme-dark)——:where() 不加优先级，
  夜间版紧跟在原规则后面，原来盖得住它的后续规则照样盖得住夜间版；
- 选择器里已经有 .theme-dark 的(两种模式共用的变量块、手写的夜间规则)、规则体里写了 dark-twin: skip 的(日间色板)跳过。
规则里写死的 hex / rgb() 必须在 RULE_HEX / _rgb() 里有夜间值，没有就报错(日间每个颜色都要有夜间版)。
装饰 SVG 里的颜色按色系公式换(金失光、红略压、羊皮纸压暗)，SVG_FIXED 里的逐个指定；公式外的新颜色构建时列出来。
"""
import math
import re
from contextlib import contextmanager

SVG_NS = 'xmlns="http://www.w3.org/2000/svg"'


# ---------- 颜色 ----------
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in rgb)


def oklch(h):
    r, g, b = (_lin(c) for c in hex2rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def F(L, C, H):
    """OKLCH → hex；超出 sRGB 色域时降色度"""
    for _ in range(40):
        a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
        l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
        m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
        s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
        rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
               -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
               -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
        if all(-0.001 <= x <= 1.001 for x in rgb):
            break
        C *= 0.95
    return rgb2hex(tuple(_gam(min(1, max(0, x))) for x in rgb))


def triple(h):
    return ", ".join(str(round(c * 255)) for c in hex2rgb(h))


# ---------- 夜间色板(和 theme.src.css 的 .theme-dark 同一套；小样见 preview/夜间配色/) ----------
HUE, CH = 22, 0.0105         # 底色：B 方向(血渴，牛血黑)红度减半，二稿 B2
PAPER, PAPER_2, PAPER_4 = "#1a1413", "#140e0e", "#1f1818"
INK = "#e9d4cb"
BONE = "#f1ddce"             # = 夜间 --tag-color：标签字、红底铭牌上的字和徽记、一级标题横幅上的字
TAG_RED, TAG_RED_HOVER = "#a51d2b", "#8f1423"
GOLD, GOLD_LIGHT = "#c29563", "#deb67f"
IVORY = F(0.34, CH * 2 + 0.01, HUE)     # 日间象牙衬底 #fffdf8 的夜间版：比纸面提一点

# 一级标题横幅 / 绶带(ribbons.STAMP 五块：正面 / 燕尾 / 折到后面 / 卷边 / 折角)：三稿 b 血色，明暗次序同日间；
# f0215 的里衬(日间暗旧红)在血色正面下面再深一档
BANNER = {"#e2cb98": "#952327", "#d8bf8a": "#881d22", "#cdb07a": "#77171d", "#bf9f68": "#661119", "#a6844f": "#510b12",
          "#9a3330": F(0.30, 0.085, 21), "#7d2626": F(0.25, 0.07, 21)}
H1_INK = BONE

SVG_FIXED = {
    **BANNER,
    "#f4e6c9": BONE,          # C_TAG：红底铭牌上的机械教徽、沉思者的蜡烛
    "#f3e8d0": "#f3e8d0",     # C_PARCH：沉思者黑屏幕里的羊皮纸色滚动条(屏幕本来就是黑的，不变)
    "#f1d27f": "#f1d27f",     # 沉思者的蜡烛火苗
    "#5c3a1a": "#000000",     # 功能栏纸条的投影
    "#a99784": F(0.50, 0.02, 50),   # 取消的任务：灰托、灰蜡
    "#a32a35": TAG_RED, "#8c2330": TAG_RED_HOVER,   # 标签红(滚动条两头、任务红蜡)：和规则里的标签红同一个值
    # 飘落羽毛：日间是比侧栏纸亮一点的白羽 + 暗一档的背面，夜间同样比纸面亮一点
    "#fffcf3": F(0.40, 0.018, 45), "#dcc596": F(0.31, 0.022, 38),
    # 圣血红(羽毛血迹 FEATHER_BLOOD、任务符号红)：公式会压暗成 #9e0019，叠在同样暗的灰羽上看不出血迹(用户问)；
    # 夜间红要提亮，同 CSS 色板里圣血红的方向
    "#a3161f": F(0.57, 0.19, 25),
}
# 用户(2026-11-03)：这几样夜间要单独保持相对亮色——引用块封蜡下的纸条、功能栏纸条(CSS，见 theme.src.css 功能栏)、
# 封蜡上的战团徽(日间是抠空透出纸色，夜间纸是黑的 → 抠空处填亮色)、二级标题宝石的高光(同样是抠空)
STRIP_PAPER = F(0.74, 0.045, 74)          # 纸条(浅的那条；左条暗一档)
SVG_FIXED.update({"#e4cf9f": STRIP_PAPER, "#dcc390": F(0.70, 0.048, 72), "#a98758": F(0.50, 0.06, 62)})


def keep(h):
    """已经是夜间色、不要再被 recolor_svg 换一遍的颜色(写成 rgb()，recolor_svg 只换 #hex)"""
    return "rgb(" + triple(h) + ")"


SEAL_LOGO = keep(F(0.82, 0.085, 73))        # 一稿 F(.84, .04, 76) 太白 → 二稿 F(.75, .055, 72) 纸条色 → 三稿 F(.77, .10, 78) 偏金但暗、太黄 → 提亮、少黄
GEM_GLINT = keep(F(0.82, 0.035, 55))
# 高亮的刷痕(ornaments.highlight_brush2 的两头颜色)：日间金色荧光笔；夜间(小样里金色压暗后发浑) → 暗金琥珀
HL_BRUSH = (F(0.50, 0.085, 62), F(0.56, 0.08, 70))
SVG_FIXED.update({"#e9cd7a": HL_BRUSH[0], "#f3e3a8": HL_BRUSH[1]})

_KEEP = {"#000", "#000000", "#fff", "#ffffff"}
UNLISTED = {}   # 公式换的颜色(构建时打印，方便核对)


def svg_color(h):
    k = h.lower()
    if k in _KEEP:
        return h
    if k in SVG_FIXED:
        return SVG_FIXED[k]
    L, C, H = oklch(k)
    if C < 0.045 or (L > 0.80 and C < 0.10 and 60 <= H <= 105):
        # 羊皮纸 / 象牙 / 浅金：压暗到纸面附近(保持浓淡次序)；深的褐色描边提成暗金褐，轮廓在黑底上看得见
        out = F(0.17 + (L - 0.55) * 0.62, min(C, 0.03) * 0.6 + CH, HUE) if L > 0.55 else F(0.50, 0.05, 61)
    elif 55 <= H <= 112:
        out = F(L - 0.06, C * 0.80, H - 14)          # 金：失光、往红褐偏
    elif H < 50 or H > 330:
        out = F(L - 0.02, C * 1.08, H + (((23 - H + 180) % 360) - 180) * 0.35)   # 红：略压暗、往血红靠
    else:
        out = h
    UNLISTED[k] = out
    return out


# url(#id) / href="#id" 是引用不是颜色：分割线血滴的渐变 id 叫 edb，一稿被当成颜色 #edb 换掉，引用断了、血滴不见(用户问)
_HEX = re.compile(r"(?<!url\()(?<!href=\")(?<!href=')#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F\w-])")


def recolor_svg(svg):
    return _HEX.sub(lambda m: svg_color(m.group(0)), svg)


# ---------- 规则里写死的颜色 ----------
RULE_HEX = {
    "#000": "#000",                       # 遮罩渐变
    "#fffdf8": IVORY,                     # 象牙衬底(选中行、callout、嵌入、Mermaid 节点，多是 30% 叠在纸上)
    "#fffaf0": PAPER_4,                   # 红头铭板代码区
    "#f4e6c9": BONE,
    "#a32a35": TAG_RED, "#8c2330": TAG_RED_HOVER,
    "#c9a548": GOLD, "#e6c66c": F(0.62, 0.09, 70),          # 高亮里的行内代码
    "#a98758": F(0.50, 0.06, 66),         # 纯洁印记纸条上的分隔短线
    "#a8171f": svg_color("#a8171f"), "#c2232c": svg_color("#c2232c"),   # 文件夹血滴
    "#b08a34": svg_color("#b08a34"), "#a99784": svg_color("#a99784"),   # 任务复选框的金蜡 / 灰蜡(build.task_css，同装饰图)
    "#e2cb98": BANNER["#e2cb98"], "#bf9f68": BANNER["#bf9f68"],         # 新标签页按钮悬停(缎带色)
    # 沉思者代码块：本来就是黑屏幕，夜间不变
    **{c: c for c in ("#31251e", "#93774f", "#a88a60", "#b8915f", "#d9a35c", "#e6aa60", "#e9b96c", "#f0705a",
                      "#f4dca8", "#ffca7c", "#ffd98c", "#f3e8d0")},
}


def _rgb(m):
    s = m.group(0)
    a = re.fullmatch(r"rgb\((\d+) (\d+) (\d+) / ([0-9.]+)\)", s)
    if a and a.group(1, 2, 3) in (("90", "60", "30"), ("92", "58", "26")):
        return f"rgb(0 0 0 / {min(0.8, float(a.group(4)) * 3):.2f})"          # 暖褐投影 → 黑，加深
    if a and a.group(1, 2, 3) == ("0", "0", "0"):
        return s
    b = re.fullmatch(r"rgba\((\d+), (\d+), (\d+), ([0-9.]+)\)", s)
    if b:
        rgb, al = b.group(1, 2, 3), float(b.group(4))
        if rgb == ("0", "0", "0") or rgb in (("255", "168", "64"), ("255", "190", "90"), ("201", "165", "72")):
            return s                                                         # 本来就是黑影 / 沉思者的辉光和行号线
        if rgb in (("130", "92", "46"), ("70", "35", "15")):
            return f"rgba(0, 0, 0, {min(0.8, al * 3.3):.2f})"
        if rgb == ("255", "252", "244"):
            return f"rgba(255, 236, 214, {al * 0.04:.3f})"                  # 浮起卡片左上的亮边：夜间几乎没有
    raise KeyError(f"rgb() 没有夜间值：{s}")


_SHADOW = re.compile(r"rgba\(var\(--ba-shadow\), ([0-9.]+)\)")
_URL = re.compile(r'url\((?:"[^"]*"|\'[^\']*\'|[^)]*)\)')
_RGB = re.compile(r"rgba?\([0-9][^()]*\)")
_VIGNETTE = "rgb(120 82 38 / calc(var(--ba-vignette-opacity, 100%) * 0.13))"


def map_value(v, errors):
    """声明值里写死的颜色换夜间版(url() 里不动：装饰图已经是夜间那遍生成的)"""
    parts = _URL.split(v)
    urls = _URL.findall(v)
    out = []
    for p in parts:
        p = p.replace(_VIGNETTE, "rgb(0 0 0 / calc(var(--ba-vignette-opacity, 100%) * 0.55))")
        p = _SHADOW.sub(lambda m: f"rgba(var(--ba-shadow), {min(0.75, float(m.group(1)) * 2.2):.2f})", p)

        def hx(m):
            k = m.group(0).lower()
            if k not in RULE_HEX:
                errors.append(m.group(0))
                return m.group(0)
            return RULE_HEX[k]
        p = _HEX.sub(hx, p)

        def rg(m):
            try:
                return _rgb(m)
            except KeyError as e:
                errors.append(str(e))
                return m.group(0)
        # _RGB 只认数字开头、括号里不再套括号的 rgb()：上面换好的暗角(套了 calc())和 rgba(var(--ba-shadow), …) 不会再被换一次
        out.append(_RGB.sub(rg, p))
    return "".join(a + (urls[i] if i < len(urls) else "") for i, a in enumerate(out))


# ---------- 夜间纸纹 ----------
def tex_grain(size=320, dark=.55, light=.2, tint=(1, .9, .86)):
    """纸面细颗粒：黑点(在深色纸上几乎看不出，只是压一点) + 带一点血色的浅色亮点(夜间主要靠它看出纸纹)"""
    r, g, b = tint
    return (f'<svg {SVG_NS} width="{size}" height="{size}">'
            '<filter id="a" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".78" numOctaves="3" seed="4" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.9 0 0 0 -1.02"/></filter>'
            '<filter id="b" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".92" numOctaves="2" seed="13" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 {r}  0 0 0 0 {g}  0 0 0 0 {b}  2 0 0 0 -1.15"/></filter>'
            f'<rect width="100%" height="100%" filter="url(#a)" opacity="{dark}"/>'
            f'<rect width="100%" height="100%" filter="url(#b)" opacity="{light}"/></svg>')


def grain_webp(colors, ops, size=320, quality=72):
    """纸纹细颗粒的位图(日间 / 夜间共用；两层：colors / ops = 底下一层、上面一层的颜色(0..1 RGB)和不透明度)。
    用户(2026-11-03)：夜间背景有特别明显的格子感——feTurbulence 的频率接近每像素一格(.78 / .92)时，
    噪声格点和像素网格打出摩尔纹(周期 1 / (1 − 频率)：.92 → 12.3px、.78 → 4.6px)，无损渲染也有；日间纸纹同样有、浅纸上不显眼(用户：一起修，保持统一)。
    改成 numpy 出噪声：白噪声在频域里低通(周期边界，天然无缝)，再按 tex_grain 那两层(滤镜参数日夜相同)渲染出来的不透明度分布
    逐像素排名对齐(直方图匹配)——颗粒的疏密、浓淡和原来一样，只是没有固定周期"""
    import io
    import numpy as np
    from PIL import Image
    import raster as R

    def layer(seed, sigma):
        ref = Image.open(io.BytesIO(R.render_webp(tex_grain(size, dark=1, light=0) if seed == 4 else tex_grain(size, dark=0, light=1),
                                                  size, size, lossless=True))).convert("RGBA")
        target = np.sort(np.asarray(ref, np.float32)[..., 3].ravel() / 255)
        n = np.random.default_rng(seed).standard_normal((size, size))
        fy, fx = np.fft.fftfreq(size)[:, None], np.fft.rfftfreq(size)[None, :]
        f = np.fft.irfft2(np.fft.rfft2(n) * np.exp(-(fx ** 2 + fy ** 2) / (2 * sigma ** 2)), s=(size, size))
        out = np.empty(size * size, np.float32)
        out[np.argsort(f.ravel())] = target
        return out.reshape(size, size)
    # 低通放得很宽(σ = 1 周/像素，接近白噪声)：颗粒细到一两个像素，同原来；σ .2 时颗粒结成两三像素的小团，看着粗
    a1, a2 = layer(4, 1.0) * ops[0], layer(13, 1.0) * ops[1]
    al = a2 + a1 * (1 - a2)
    c1, c2 = (np.array(c, np.float32) for c in colors)
    rgb = (c2 * a2[..., None] + c1 * (a1 * (1 - a2))[..., None]) / np.maximum(al, 1e-6)[..., None]
    buf = io.BytesIO()
    Image.fromarray((np.dstack([rgb, al]) * 255).round().astype(np.uint8), "RGBA").save(buf, "WEBP", quality=quality, alpha_quality=quality, method=6)
    return buf.getvalue()


# 日间 = ornaments.tex_grain 的两层颜色；不透明度 × .6：两层颗粒在 SVG 里不是独立的(暗点亮点常落在一处、互相抵掉一部分)，
# 照搬 .42 / .38 的话纸面明暗起伏(标准差)是原来的 1.7 倍；× .6 后标准差 4.39、均值 235.9(原来 4.36 / 236.0，叠在日间纸色上量)
GRAIN_DAY = (((.40, .28, .14), (1, .99, .95)), (.252, .228))
GRAIN_DARK = (((0, 0, 0), (1, .9, .86)), (.55, .15))            # 黑点 + 带血色的浅点(浅点一稿 .2，用户嫌纹理太明显 → .15)


def tex_tone(size=1024, dark=.34, light=.06, tint=(.82, .62, .56)):
    """大尺度浓淡：黑色云斑 + 很淡的暖色浅斑(一稿 .42 / .08，用户嫌纹理太明显 → 约八成)"""
    r, g, b = tint
    return (f'<svg {SVG_NS} width="{size}" height="{size}">'
            '<filter id="t" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".0034" numOctaves="4" seed="9" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.5 0 0 0 -.72"/></filter>'
            '<filter id="u" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".009" numOctaves="3" seed="27" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 {r}  0 0 0 0 {g}  0 0 0 0 {b}  1.5 0 0 0 -.8"/></filter>'
            f'<rect width="100%" height="100%" filter="url(#t)" opacity="{dark}"/>'
            f'<rect width="100%" height="100%" filter="url(#u)" opacity="{light}"/></svg>')


# 新标签页题铭的字(build.inscription_webp text_ink)：血色绶带上的骨白字，浓淡同日间暗血红两色的差
INSCR_INK = (F(0.82, 0.035, 55), F(0.92, 0.03, 62))


# ---------- 夜间的灰烬和火星(文件列表那组侧栏，代替日间的飘落羽毛；build.embers_css) ----------
ASH_FILL = ("#2e2725", "#8a7f79")     # 烧黑的纸片：中间焦黑、往边上发灰(黑纸上靠灰边看出来；一稿灰边 #5e5450 太暗)
ASH_EDGE = ("#ff4a32", "#b3141c")     # 还燃着的边：亮红 → 暗红(一稿亮橙 #ff8a3a → #c8321a；用户比过红色版：换红)


def ash_flake(seed, burning=False, blur=0.0, res=40, edge=None):
    """一片灰烬：参差的锯齿碎片(15 个顶点，大半径 / 小缺口交替、压扁)，径向渐变焦黑 → 灰边；
    burning = 一侧边上还燃着：橙红火线只烧在一边(沿对角线渐熄)，往碎片里面洇一点、往外一点辉光。
    一稿 9 个顶点、整圈均匀火线，用户看着像几何宝石。viewBox 100 见方，碎片占中间 ~60；res = 渲染边长 px(build 里 2.5 倍显示尺寸)"""
    import random
    rng = random.Random(seed)
    rot = rng.uniform(0, math.pi)
    sq = rng.uniform(.45, .68)
    pts = []
    for i in range(15):
        a = 2 * math.pi * i / 15 + rng.uniform(-.12, .12)
        r = (rng.uniform(.62, 1.0) if i % 2 == 0 else rng.uniform(.38, .8)) * 31
        x, y = r * math.cos(a), r * math.sin(a) * sq
        pts.append((50 + x * math.cos(rot) - y * math.sin(rot), 50 + x * math.sin(rot) + y * math.cos(rot)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    flt = (f'<filter id="b" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="{blur * 100 / res:.2f}"/></filter>'
           if blur else "")
    g = f' filter="url(#b)"' if blur else ""
    fire = ""
    if burning:
        ang = rng.uniform(0, 2 * math.pi)            # 燃着的那一侧
        x1, y1 = .5 + .5 * math.cos(ang), .5 + .5 * math.sin(ang)
        fire = (f'<filter id="gl" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="2.4"/></filter>'
                f'<clipPath id="c"><path d="{d}"/></clipPath>'
                f'<linearGradient id="e" x1="{x1:.2f}" y1="{y1:.2f}" x2="{1 - x1:.2f}" y2="{1 - y1:.2f}">'
                f'<stop offset="0" stop-color="{(edge or ASH_EDGE)[0]}"/><stop offset=".35" stop-color="{(edge or ASH_EDGE)[1]}" stop-opacity=".85"/>'
                f'<stop offset=".62" stop-color="{(edge or ASH_EDGE)[1]}" stop-opacity="0"/></linearGradient>')
    body = f'<path d="{d}" fill="url(#a)"/>'
    if burning:
        body += (f'<path d="{d}" fill="none" stroke="url(#e)" stroke-width="6" opacity=".5" filter="url(#gl)"/>'
                 f'<g clip-path="url(#c)"><path d="{d}" fill="none" stroke="url(#e)" stroke-width="7" stroke-linejoin="round"/></g>')
    return (f'<svg {SVG_NS} width="{res}" height="{res}" viewBox="0 0 100 100"><defs>{flt}{fire}'
            f'<radialGradient id="a" cx="50%" cy="50%" r="55%"><stop offset=".25" stop-color="{ASH_FILL[0]}"/>'
            f'<stop offset="1" stop-color="{ASH_FILL[1]}"/></radialGradient></defs><g{g}>{body}</g></svg>')


# 火星：亮芯 → 红 → 暗红辉光 → 透明。一稿亮芯 → 黄 → 橙(#fff3d2 / #ffc06a / #ff7a26 / #d0301a / #8a1008)，
# 用户(纸带余火换红之后)比过文件树的火星 / 灰烬红色版：换红(preview/夜间配色/功能栏纸带/火星灰烬_*.png)
EMBER_STOPS = ("#ffe9dc", "#ff8466", "#f2321f", "#b3121a", "#600610")


def ember(res=40, stops=EMBER_STOPS):
    """一粒火星：近白的亮芯 + 红 + 往外淡成透明的暗红辉光(viewBox 100，芯约占 1/5)"""
    c = stops
    return (f'<svg {SVG_NS} width="{res}" height="{res}" viewBox="0 0 100 100"><defs><radialGradient id="g">'
            f'<stop offset="0" stop-color="{c[0]}"/><stop offset=".16" stop-color="{c[1]}"/><stop offset=".3" stop-color="{c[2]}" stop-opacity=".85"/>'
            f'<stop offset=".55" stop-color="{c[3]}" stop-opacity=".3"/><stop offset="1" stop-color="{c[4]}" stop-opacity="0"/>'
            '</radialGradient></defs><circle cx="50" cy="50" r="50" fill="url(#g)"/></svg>')


# ---------- 夜间功能栏纸带末端的烧痕(第五十二版) ----------
# 用户：纸带比别的页面元素亮(不要变深色 → 纸降一档、图标加深，见 theme.src.css)，末端要有类似灰烬的燃烧痕迹。
# 燕尾缺口换成一条参差的烧边(rb_strip_burnt，遮罩)，底边垫一张烧痕位图(rb_char_webp)：两者用同一条边线 _rb_edge，钉在纸条底边
# 二稿(用户：烧焦部分再多一些、烧边两端更长、余火要更红不要橙)：中间烧得深、两角往下垂(像烧缺的燕尾)，焦褐蔓延 10 → 15px、炭黑 / 灰烬边加厚，
# 余火换红色 RB_EMBER(原来同灰烬碎片的橙 ASH_EDGE)
RB_CHAR_H, RB_CHAR_K = 44, 3      # 烧痕位图高(px)、倍数
RB_EMBER = ("#ff4030", "#b3141c", "#c42a1e")   # 余火亮 / 暗、往纸里透的暖光


def _rb_edge(x, seed=5):
    """烧边离底边多高(px)，x = 纸条里的横坐标：中间拱起(两角垂得长) + 三条随机相位的正弦 + 两处烧得深的缺口"""
    import numpy as np
    import ornaments as O
    bx, w = (O.RB_SEAL_D - O.RB_STRIP_W) / 2, O.RB_STRIP_W
    rng = np.random.default_rng(seed)
    u = (np.asarray(x, float) - bx) / w
    y = 1.6 + 6.2 * np.sin(np.pi * np.clip(u, 0, 1)) ** 1.4      # 中间烧得深、两角垂下来
    y = y + sum(a * np.sin(2 * np.pi * f * u + p) for a, f, p in zip((1.0, .6, .3), (1.1, 2.7, 6.3), rng.uniform(0, 6.3, 3)))
    for c, cw, dpt in ((rng.uniform(.25, .42), .08, 1.8), (rng.uniform(.58, .78), .06, 1.3)):
        y = y + dpt * np.exp(-((u - c) / cw) ** 2)
    return np.maximum(y, 1.0)


def rb_strip_burnt(fill="#000"):
    """功能栏纸条形状(同 ornaments.ribbon_strip：蜡的轮廓 ∪ 身子，不设 viewBox，1:1 按 px)，下端燕尾缺口换成烧边"""
    import numpy as np
    import ornaments as O
    D, W = O.RB_SEAL_D, O.RB_STRIP_W
    bx = (D - W) / 2
    xs = np.linspace(bx - 1, bx + W + 1, 57)
    pts = " L".join(f"{x:.2f},{-y:.2f}" for x, y in zip(xs, _rb_edge(np.clip(xs, bx, bx + W))))
    return (f'<svg {SVG_NS} width="100%" height="100%"><defs>'
            f'<mask id="n" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"><rect width="100%" height="100%" fill="#fff"/>'
            f'<svg y="100%" overflow="visible"><path d="M{bx - 1:g},2 L{pts} L{bx + W + 1:g},2 Z" fill="#000"/></svg></mask></defs>'
            f'<rect x="{bx:g}" y="{D / 2:g}" width="{W}" height="100%" fill="{fill}" mask="url(#n)"/>'
            f'<path transform="scale({D / 30:.5f}) translate(-4 -.5)" d="{O._wax_blob()}" fill="{fill}"/></svg>')


def rb_char_webp():
    """烧痕位图(RB_SEAL_D × RB_CHAR_H，RB_CHAR_K 倍)：按纸里到烧边的距离 d(px) 上色——
    余火(d < .9，沿边一段亮一段灭，灭的是灰白灰烬；RB_EMBER)、灰烬边(到 2.2)、炭黑(到 4.5 ± 起伏)、
    焦褐(往里渐淡到 ~15px，斑驳)；亮着的余火往纸里透一点暖光"""
    import io
    import numpy as np
    from PIL import Image
    from scipy.ndimage import distance_transform_edt
    import ornaments as O
    D, W, K, Hc = O.RB_SEAL_D, O.RB_STRIP_W, RB_CHAR_K, RB_CHAR_H
    bx = (D - W) / 2
    w, h, pad = D * K, Hc * K, 12 * K

    def noise(shape, wl, seed):
        n = np.random.default_rng(seed).standard_normal(shape)
        fy, fx = np.fft.fftfreq(shape[0])[:, None], np.fft.fftfreq(shape[1])[None, :]
        f = np.real(np.fft.ifft2(np.fft.fft2(n) * np.exp(-(fx ** 2 + fy ** 2) * wl ** 2 / 2)))
        return f / f.std()

    def rgb(hx):
        return np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    xs = (np.arange(-pad, w + pad) + .5) / K
    ye = _rb_edge(np.clip(xs, bx, bx + W))                      # 两边按端点延伸，纸条侧边不算烧边
    yy = (h - (np.arange(h) + .5)[:, None]) / K                 # 离底边多高
    d = distance_transform_edt(yy > ye[None, :])[:, pad:pad + w] / K
    n1, n2 = noise((h, w), 2.2 * K, 3), noise((h, w), 6 * K, 4)
    glow = np.clip((noise((1, w), 4 * K, 9)[0] - .1) * 1.4, 0, 1)[None, :] * np.ones((h, 1))   # 沿边哪几段还燃着
    ember = np.where(n1[..., None] > 0, rgb(RB_EMBER[0]), rgb(RB_EMBER[1]))
    ash, char, scorch = rgb("#7a706a"), rgb("#1c1411"), rgb("#3e2414")
    col = np.zeros((h, w, 3), np.float32)
    a = np.zeros((h, w), np.float32)
    m = d > 0
    reach, lim = 15 + 4 * n2, 4.5 + 1.1 * n2
    t = np.clip((d - 2.2) / np.maximum(reach - 2.2, .1), 0, 1)
    col[m], a[m] = scorch, np.clip((1 - t) ** 1.6 * (.88 + .12 * n1), 0, 1)[m]        # 由外往里一层层盖
    mc = m & (d < lim)
    col[mc], a[mc] = char, np.clip(.92 + .08 * n1, 0, 1)[mc]
    mf = m & (d < 2.2)
    col[mf], a[mf] = ((char * .6 + ash * .4) + (n1[..., None] > .8) * (ash - char) * .5)[mf], 1
    me = m & (d < .9)
    col[me], a[me] = (ember * glow[..., None] + ash * (1 - glow[..., None]))[me], 1
    warm = np.clip(1 - d / 4, 0, 1) * glow * (d >= .9) * m
    col = col * (1 - .35 * warm[..., None]) + rgb(RB_EMBER[2]) * (.35 * warm[..., None])
    buf = io.BytesIO()
    Image.fromarray((np.dstack([np.clip(col, 0, 1), np.clip(a, 0, 1)]) * 255).round().astype(np.uint8), "RGBA").save(buf, "WEBP", lossless=True)
    return buf.getvalue()


# ---------- 夜间新标签页徽章背后的「黑日」(第五十二版) ----------
# 用户在日蚀样本里选 C(火焰 + 光晕)，不要日环上的亮珠(preview/夜间配色/日蚀样本/)。build 在夜间那遍传给 ornaments.newtab_crest(halo=…)，
# 仍在原来光环那层遮罩里(杯身以下渐隐、翅膀 / 杯子周围留缝)；颜色都用 keep 包住，整枚徽章换夜间色时不再改
# 配色：光晕三档(内 → 外，前两档不透明度 glow_op)、光芒三档(根 → 梢)、黑盘(None = 不画、日盘抠空透出底色)、日环外光、日环
ECLIPSE_RED = dict(glow=("#9a1418", "#6e0c10", "#3a0608"), glow_op=(.75, .38), flame=("#b3151c", "#7c1016", "#45080b"),
                   disc="#070404", rim_glow="#ff3a33", rim="#e2343a")
# 用户：红色日冕和血滴混在一起了 → 比过骨白 / 暗金 / 酒红暗紫 / 炭灰(preview/夜间配色/日蚀样本/日蚀配色_对比.png)，定骨白(像真日全食的珍珠白日冕，血滴最醒目)
# 用户：日冕里面的黑盘(#060404)太黑，也改成透出底色(同徽章的留白描边)→ disc=None(preview/夜间配色/日蚀样本/日盘透底/)
ECLIPSE_BONE = dict(glow=("#a89a8e", "#6a5e56", "#2a2220"), glow_op=(.45, .22), flame=("#d8c8b8", "#8f7f72", "#3a302b"),
                    disc=None, rim_glow="#fff2e6", rim="#f1ddce")


def eclipse_halo(cx, cy, r, n=16, wavy_len=.95, straight_len=.6, flame=None, pal=None):
    """光晕(r → 2.3r 渐隐) + 原来那套火焰光芒(填径向渐变：根部亮 → 梢暗，不要环带和内细环) + 比夜色更深的黑盘 + 日环(细环 + 模糊外光)；pal = 配色。
    pal["disc"] = None：不画黑盘，光晕和光芒在日盘处抠一个圆洞(光晕圆的第一档颜色一直铺到圆心、光芒根也伸进日盘，只删黑盘会露出来)，
    透出底色；新标签页血渍按徽章轮廓避让，日盘四周被翅膀、日环、杯口围住，算在轮廓里(build.spatter_webp)"""
    import ornaments as O
    p = pal or ECLIPSE_RED
    g, f = p["glow"], p["flame"]
    defs = (f'<defs><radialGradient id="ecg" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r * 2.3:.1f}">'
            f'<stop offset="{.93 / 2.3:.3f}" stop-color="{keep(g[0])}" stop-opacity="{p["glow_op"][0]}"/>'
            f'<stop offset="{1.25 / 2.3:.3f}" stop-color="{keep(g[1])}" stop-opacity="{p["glow_op"][1]}"/>'
            f'<stop offset="1" stop-color="{keep(g[2])}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="ecf" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r * 2.0:.1f}">'
            f'<stop offset=".42" stop-color="{keep(f[0])}"/><stop offset=".7" stop-color="{keep(f[1])}"/>'
            f'<stop offset="1" stop-color="{keep(f[2])}"/></radialGradient>'
            f'<filter id="ecb" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{r * .03:.2f}"/></filter></defs>')
    halo = O.sun_halo_body(cx, cy, r, "url(#ecf)", n, wavy_len=wavy_len, straight_len=straight_len, inner_ring=False, flame=flame)
    rays = halo[:halo.index("/>") + 2]                 # 第一段 path = 光芒(第二段是环带)
    rr = r * .96
    body = f'<circle cx="{cx}" cy="{cy}" r="{r * 2.3:.1f}" fill="url(#ecg)"/>' + rays
    if p["disc"]:
        body += f'<circle cx="{cx}" cy="{cy}" r="{rr:.2f}" fill="{keep(p["disc"])}"/>'
    else:
        m = 3 * r
        box = f'x="{cx - m:.1f}" y="{cy - m:.1f}" width="{2 * m:.1f}" height="{2 * m:.1f}"'
        defs = defs.replace("</defs>", f'<mask id="ech" maskUnits="userSpaceOnUse" {box}><rect {box} fill="#fff"/>'
                                       f'<circle cx="{cx}" cy="{cy}" r="{rr:.2f}" fill="#000"/></mask></defs>')
        body = f'<g mask="url(#ech)">{body}</g>'
    return (defs + body
            + f'<circle cx="{cx}" cy="{cy}" r="{rr:.2f}" fill="none" stroke="{keep(p["rim_glow"])}" stroke-width="{r * .07:.2f}" opacity=".55" filter="url(#ecb)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{rr:.2f}" fill="none" stroke="{keep(p["rim"])}" stroke-width="{r * .03:.2f}"/>')


# ---------- 夜间那一遍 ----------
ON = False
RAW = False
# True = 笔记标题徽记两侧、新标签页题铭的绶带(f0215，build.ribbon_arc 的位图)夜间也用日间的羊皮纸配色(一级标题横幅仍是血色)；
# False = 跟一级标题横幅一样换成血色(题铭字用 INSCR_INK 骨白)。2026-11-03 用户试过羊皮纸版(preview/夜间配色/实装/绶带对比_左血色_右羊皮纸.png)，定回血色
RIBBON_DAY = False


@contextmanager
def mode():
    global ON
    import raster
    orig = raster.render_webp

    def render(svg, *a, **kw):
        return orig(svg if RAW else recolor_svg(svg), *a, **kw)
    ON, raster.render_webp = True, render
    try:
        yield
    finally:
        ON, raster.render_webp = False, orig


@contextmanager
def raw(on=True):
    """夜间那遍里临时不换色(从 SVG 渲染的位图保持日间颜色)"""
    global RAW
    old, RAW = RAW, on
    try:
        yield
    finally:
        RAW = old


# ---------- 按日间规则生成夜间规则 ----------
GROUPS = ("@media", "@supports", "@container", "@starting-style", "@layer", "@document")
_TOK = re.compile(r'/\*|["\'{};}]')


def _str_end(css, i):
    """css[i] 是引号 → 配对引号之后的位置"""
    q, j = css[i], i + 1
    while True:
        k = css.index(q, j)
        n = 0
        while css[k - 1 - n] == "\\":
            n += 1
        if n % 2 == 0:
            return k + 1
        j = k + 1


def _match(css, i):
    """css[i] == '{' → 配对的 '}' 的位置"""
    depth, j = 0, i
    while True:
        m = _TOK.search(css, j)
        t = m.group(0)
        if t == "/*":
            j = css.index("*/", m.end()) + 2
        elif t in "\"'":
            j = _str_end(css, m.start())
        elif t == "{":
            depth += 1
            j = m.end()
        elif t == "}":
            depth -= 1
            if depth == 0:
                return m.start()
            j = m.end()
        else:
            j = m.end()


def _strip_comments(s):
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


def parse(css, i=0, end=None):
    """→ [(类型, 前缀, '{' 位置, '}' 位置, 子节点)]；类型 rule / group(@media 这类，里面还是规则) / opaque(@keyframes、@font-face……)"""
    end = len(css) if end is None else end
    nodes, seg = [], i
    while True:
        m = _TOK.search(css, i, end)
        if not m:
            return nodes
        t = m.group(0)
        if t == "/*":
            i = css.index("*/", m.end()) + 2
        elif t in "\"'":
            i = _str_end(css, m.start())
        elif t == ";":
            i = seg = m.end()
        elif t == "}":
            raise ValueError(f"多出来的 }} @ {m.start()}")
        else:
            o = m.start()
            c = _match(css, o)
            pre = _strip_comments(css[seg:o]).strip()
            if pre.startswith("@"):
                name = re.match(r"@[\w-]+", pre).group(0)
                kids = parse(css, o + 1, c) if name in GROUPS else None
                nodes.append(("group" if kids is not None else "opaque", pre, o, c, kids))
            else:
                nodes.append(("rule", pre, o, c, None))
            i = seg = c + 1


_SPLIT = {",": re.compile(r"[\"'()\[\],]"), ";": re.compile(r"[\"'()\[\];]")}


def _split_top(s, sep):
    """按括号外、引号外的 sep 切开"""
    out, depth, start, i = [], 0, 0, 0
    while True:
        m = _SPLIT[sep].search(s, i)
        if not m:
            break
        t = m.group(0)
        if t in "\"'":
            i = _str_end(s, m.start())
            continue
        if t in "([":
            depth += 1
        elif t in ")]":
            depth -= 1
        elif depth == 0:
            out.append(s[start:m.start()])
            start = m.end()
        i = m.end()
    out.append(s[start:])
    return out


def decls(body):
    """规则体 → [(属性, 值)]"""
    body = _strip_comments(body)
    out = []
    for d in _split_top(body, ";"):
        d = d.strip()
        if not d:
            continue
        if "{" in d:
            raise ValueError(f"规则里嵌套了规则：{d[:80]}")
        p, _, v = d.partition(":")
        out.append((p.strip(), v.strip()))
    return out


# body 自己身上的类(选择器第一段是这些 → 夜间类挂在同一段上，不是当祖先)
_BODY_CLS = re.compile(r"\.(?:ba-[\w-]+|theme-(?:light|dark)|css-settings-manager|is-mobile|is-phone|is-tablet|styled-scrollbars|"
                       r"mod-(?:windows|macos|linux)|is-frameless|is-hidden-frameless|is-translucent|is-focused|native-scrollbars|"
                       r"show-[\w-]+|is-fullscreen)(?![\w-])")
REVIEW = {}     # 第一段 → 归类(打印核对用)


def _first_end(s):
    depth = 0
    for i, ch in enumerate(s):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif depth == 0 and ch in " >+~\n\t":
            return i
    return len(s)


def darkify(sel):
    out = []
    for s in _split_top(sel, ","):
        s = " ".join(s.split())
        if ".theme-light" in s:
            out.append(s.replace(".theme-light", ".theme-dark"))
            continue
        e = _first_end(s)
        head = s[:e]
        if head.startswith(("html", ":root")):
            raise ValueError(f"夜间版没法挂在 {head} 上：{s}")
        if head.startswith("body"):
            REVIEW[head] = "body"
            out.append("body:where(.theme-dark)" + s[4:])
        elif _BODY_CLS.search(head):
            REVIEW[head] = "body"
            k = head.find("::")
            k = e if k < 0 else k
            out.append(s[:k] + ":where(.theme-dark)" + s[k:])
        else:
            REVIEW[head] = "desc"
            out.append(":where(.theme-dark) " + s)
    return ",\n".join(out)


def twins(css_l, css_d):
    """日间 CSS + 夜间那遍(结构相同) → 插好夜间规则的 CSS。返回 (CSS, 夜间规则数)"""
    errors, ins = [], []

    def walk(nl, nd):
        if len(nl) != len(nd):
            raise ValueError("两遍 CSS 结构不同")
        for a, b in zip(nl, nd):
            kind, pre, o, c, kids = a
            if kind != b[0] or pre != b[1]:
                raise ValueError(f"两遍 CSS 结构不同：{pre[:80]} / {b[1][:80]}")
            if kind == "group":
                walk(kids, b[4])
                continue
            bl, bd = css_l[o + 1:c], css_d[b[2] + 1:b[3]]
            if kind == "opaque":
                if bl != bd:
                    raise ValueError(f"{pre[:60]} 里的值夜间不同，没法自动生成夜间版")
                continue
            if ".theme-dark" in pre or "dark-twin: skip" in bl:
                continue
            whole = ".theme-light" in pre
            dl, dd = decls(bl), decls(bd)
            if [p for p, _ in dl] != [p for p, _ in dd]:
                raise ValueError(f"两遍声明不同：{pre[:80]}")
            vals = [map_value(vd, errors) for _, vd in dd]
            diff = [whole or vd != vl for (_, vl), vd in zip(dl, vals)]
            # 同一族的属性要连带复制(2026-11-03 一级标题横幅燕尾满条平铺)：原规则先写 background 简写、后面单写 background-repeat 等子属性，
            # 夜间版只复制换了图的简写的话，简写把子属性重置成初始值(repeat)，又排在原规则后面，盖掉了原规则里的子属性。
            # 所以差异声明后面、和它同族(一个是另一个的前缀 + "-")的声明也照原顺序带上
            fam = lambda a, b: a == b or a.startswith(b + "-") or b.startswith(a + "-")   # noqa: E731
            for i in range(len(dl)):
                if diff[i] and not whole:
                    for j in range(i + 1, len(dl)):
                        if fam(dl[i][0], dl[j][0]):
                            diff[j] = True
            out = [(p, v) for (p, _), v, d in zip(dl, vals, diff) if d]
            if out:
                ins.append((c + 1, "\n" + darkify(pre) + " {\n" + "".join(f"  {p}: {v};\n" for p, v in out) + "}"))

    walk(parse(css_l), parse(css_d))
    if errors:
        raise SystemExit("规则里的颜色没有夜间值：" + ", ".join(sorted(set(errors))))
    parts, last = [], 0
    for pos, text in sorted(ins, key=lambda x: x[0]):
        parts += [css_l[last:pos], text]
        last = pos
    parts.append(css_l[last:])
    return "".join(parts), len(ins)
