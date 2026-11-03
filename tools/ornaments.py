# -*- coding: utf-8 -*-
"""Sangreal · 圣杯主题(圣血天使风格；原工作名 Blood Angels)的装饰图案：都输出 SVG 字符串，build.py 转成 data URI 内嵌。
剪影来自 game-icons.net(Lorc / Delapouite / sbed，CC BY 3.0，src/icons/gi/，主题头部署名)；其余几何自绘。
第二版(2026-10-25 用户反馈)：金色改成有质感的金箔(多段明暗渐变，原来的 #b48a3c 像铜)；
光环 = 战锤 40K 的铁光环(不是天使光环)；绶带横幅参照无畏机甲石棺(白色卷轴 + 深色描边)；
菱形全部去掉，改用血滴 / 铁光环 / 石棺式镶框血滴。
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GI = ROOT / "src" / "icons" / "gi"
SVG = 'xmlns="http://www.w3.org/2000/svg"'

# ---- 色板(和 theme.src.css 的 --ba-* 对应；SVG 背景图不能用 CSS 变量，改色要两边同步) ----
C_CRIMSON = "#a3161f"
C_BLOOD = "#6e0c12"
C_GOLD = "#c9a23a"          # 金箔中间调(平涂处用)
C_GOLD_LIGHT = "#ecd27f"
C_GOLD_DEEP = "#8f6a14"     # 金色文字 / 暗部
C_IVORY = "#fbf7ee"
C_BONE = "#f6efdf"          # 卷轴、纯洁封印纸条(石棺卷轴的骨白)
C_UMBER = "#5b3f26"         # 卷轴描边
C_SANGUINE = "#a4442e"      # 红粉笔(sanguine)


# ---- 金箔 / 血色渐变：每张 SVG 自带 defs(data URI 各自独立，id 可以重复) ----
# 第三版(用户：金属质感廉价、不要拟物 UI)：现代界面里金属多是"一个颜色 + 极轻的明暗过渡"(扁平 / 缎面)，
# 层次交给形状和阴影，不做多段高光反光。这里金只留一道很缓的明度过渡(差约 6%)，看着是平涂金色
GOLD_STOPS = ((0, "#d2ae55"), (1, "#c09a40"))


def gold_defs(gid="gold", mirror=False, angle=(0, 0, 0, 1)):
    """缎面金：从上到下极缓的明度过渡。mirror 保留参数(对称的徽记两边用同一种)"""
    x1, y1, x2, y2 = angle
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def iron_defs(iid="iron"):
    """铁：平涂冷灰(同样只留极缓的明度过渡)"""
    return (f'<linearGradient id="{iid}" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#8a9099"/><stop offset="1" stop-color="#737a84"/></linearGradient>')


def blood_defs(bid="blood"):
    """血：平涂圣血红(极缓的明度过渡)。第七版(用户：血滴和宝石太暗沉)整体提亮一档"""
    return (f'<linearGradient id="{bid}" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#c2232c"/><stop offset="1" stop-color="#a8171f"/></linearGradient>')


GEM_RED = ("#cc4b44", "#9e3d38")   # 第十版(用户：宝石颜色太鲜艳)：原来 #d83236 → #ad1720，降饱和成和血滴、缎带里衬一路的砖红


def gem_defs(gid="gem"):
    """宝石红：左上亮、右下深，猫眼缝和高光压在上面"""
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2=".6" y2="1">'
            f'<stop offset="0" stop-color="{GEM_RED[0]}"/><stop offset="1" stop-color="{GEM_RED[1]}"/></linearGradient>')


def gi_paths(name):
    src = (GI / f"{name}.svg").read_text(encoding="utf-8")
    return re.findall(r'<path[^>]*\sd="([^"]+)"', src)


def gi_bbox(name):
    """[x, y, w, h, 重心x, 重心y]，tools/icon_bbox.py 量的"""
    return json.loads((GI / "bbox.json").read_text(encoding="utf-8"))[name]


def place(name, x, y, h, fill, anchor=(0.5, 0.5)):
    """剪影按外框缩放到高 h，外框 anchor 点(0..1)对齐 (x, y)"""
    bx, by, bw, bh, _, _ = gi_bbox(name)
    s = h / bh
    ax, ay = bx + bw * anchor[0], by + bh * anchor[1]
    return (f'<g transform="translate({x - ax * s:.2f} {y - ay * s:.2f}) scale({s:.4f})" fill="{fill}">'
            + "".join(f'<path d="{d}"/>' for d in gi_paths(name)) + "</g>")


def drop_path(cx, top, h, w=None):
    """自绘血滴：尖头朝上的泪滴，底部圆。h 总高，w 宽(默认 0.62h)"""
    w = w or h * 0.62
    r = w / 2
    by = top + h - r
    k = 0.5523 * r
    return (f"M{cx:.2f},{top:.2f}"
            f"C{cx + r * 0.18:.2f},{top + h * 0.22:.2f} {cx + r:.2f},{by - r * 0.95:.2f} {cx + r:.2f},{by:.2f}"
            f"C{cx + r:.2f},{by + k:.2f} {cx + k:.2f},{by + r:.2f} {cx:.2f},{by + r:.2f}"
            f"C{cx - k:.2f},{by + r:.2f} {cx - r:.2f},{by + k:.2f} {cx - r:.2f},{by:.2f}"
            f"C{cx - r:.2f},{by - r * 0.95:.2f} {cx - r * 0.18:.2f},{top + h * 0.22:.2f} {cx:.2f},{top:.2f}Z")


def drop_glint(cx, top, h, w=None):
    """血滴左上一道弯月形高光"""
    w = w or h * 0.62
    r = w / 2
    by = top + h - r
    x0, y0 = cx - r * 0.5, by - r * 0.55
    return (f"M{x0:.2f},{y0:.2f}C{x0 - r * .12:.2f},{y0 + r * .5:.2f} {cx - r * .4:.2f},{by + r * .45:.2f} {cx - r * .05:.2f},{by + r * .62:.2f}"
            f"C{cx - r * .55:.2f},{by + r * .42:.2f} {cx - r * .72:.2f},{y0 + r * .4:.2f} {x0:.2f},{y0:.2f}Z")


# ---- 战团徽：照用户给的参考图(Bloodangelsymbol.webp)描的矢量(tools/trace_emblem.py → src/icons/ba-emblem.svg)。
# 用户要求标题下直接用完整徽记、不要拼(第一版 Heritage 版画双翼 + 自绘血滴 + 光环被否)；
# 第二版用 wh_icons 的版本，血滴往右偏了 33/956、比例也不对，改描参考图(严格左右对称)。
# 三条 path：drop 血滴 / wing-l / wing-r，翅膀金箔(左右镜像的渐变，明暗对称)、血滴宝石红
def _logo_parts():
    src = (ROOT / "src" / "icons" / "ba-emblem.svg").read_text(encoding="utf-8")
    vb = tuple(map(float, re.search(r'viewBox="([^"]+)"', src).group(1).split()))
    parts = {m.group(1): m.group(2) for m in re.finditer(r'<path id="([\w-]+)" d="([^"]+)"', src)}
    return vb, parts


LOGO_DEFS = gold_defs("lg") + gold_defs("lgm", mirror=True) + blood_defs("lb")


def _logo_body(wing_l="url(#lg)", wing_r="url(#lgm)", drop="url(#lb)"):
    _, p = _logo_parts()
    return (f'<path d="{p["wing-l"]}" fill="{wing_l}"/><path d="{p["wing-r"]}" fill="{wing_r}"/>'
            f'<path d="{p["drop"]}" fill="{drop}"/>')


def logo_at(cx, top, h, **kw):
    """徽记按高 h、顶部中点 (cx, top) 摆进别的 SVG(那张图的 defs 里要有 LOGO_DEFS)"""
    vb, _ = _logo_parts()
    s = h / vb[3]
    return f'<g transform="translate({cx - vb[2] / 2 * s:.2f} {top:.2f}) scale({s:.4f})">{_logo_body(**kw)}</g>'


def logo_size(h):
    vb, _ = _logo_parts()
    return vb[2] / vb[3] * h, h


DROP_GRAD = ('<stop offset="0" stop-color="#e04a46"/><stop offset=".35" stop-color="#cd2f34"/>'
             '<stop offset=".72" stop-color="#bd3a39"/><stop offset="1" stop-color="#a8423d"/>')


def emblem_stamp(tf, s, mu, full, gold=None, shade="#b08a34", shift=(-2.6, -1.8), gap=1.6, ink_dark=None,
                 region=(0, 0, 100, 100), p=""):
    """战团徽的套色画法(标题徽记、分隔线共用)：双翼缎面金 + 右下一道深一档的第二套色(翼减去往左上挪一点的自己)、
    血滴同新标签页的斜向渐变、血滴和双翼之间抠一道纸色空隙(gap 显示 px)、双翼上稀疏的深色墨粒。
    tf / s：徽记的 transform 和缩放；mu / full：遮罩的 maskUnits 属性串和满幅白底；region：深色墨粒铺的范围；
    p：id 前缀(同一张图里放两枚时不撞)。返回 (defs, art)"""
    _, parts = _logo_parts()
    wl, wr, dr = (f'<path d="{parts[k]}"/>' for k in ("wing-l", "wing-r", "drop"))
    k = f'fill="#000" stroke="#000" stroke-width="{2 * gap / s:.1f}" stroke-linejoin="round"'
    g = gold or [c for _, c in GOLD_STOPS]
    defs = (f'<linearGradient id="{p}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{g[0]}"/>'
            f'<stop offset="1" stop-color="{g[1]}"/></linearGradient>'
            f'<linearGradient id="{p}db" x1=".2" y1=".1" x2=".8" y2=".95">{DROP_GRAD}</linearGradient>'
            f'<mask id="{p}mw" {mu}>{full}<g transform="{tf}" {k}>{dr}</g></mask>'
            f'<mask id="{p}ms" {mu}>{full}<g transform="translate({shift[0]} {shift[1]}) {tf}" fill="#000">{wl}{wr}</g></mask>')
    wings = (f'<g mask="url(#{p}mw)"><g transform="{tf}" fill="url(#{p}g)">{wl}{wr}</g>'
             f'<g mask="url(#{p}ms)"><g transform="{tf}" fill="{shade}">{wl}{wr}</g></g></g>')
    art = f'<g id="{p}wg">{wings}</g><g transform="{tf}" fill="url(#{p}db)">{dr}</g>'
    if ink_dark:
        x, y, w, h = region
        defs += (f'<pattern id="{p}dp" patternUnits="userSpaceOnUse" width="256" height="256" x="61" y="17">'
                 f'<image href="{ink_dark}" width="256" height="256"/></pattern>'
                 f'<mask id="{p}ma" {mu} style="mask-type:alpha"><use href="#{p}wg"/></mask>')
        art += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{p}dp)" mask="url(#{p}ma)"/>'
    return defs, art


def title_crest(ribbon, rib_w, rib_h, rib_mid, W=420, eh=84, band=.7, ink=None, ink_dark=None, wear=None,
                gap=1.6, rgap=2.2, shade="#b08a34", shift=(-2.6, -1.8), gold=None):
    """笔记标题下的徽记(第十版，用户：原来的战团徽太简陋，要配新标签页的美术风格和配色，可以把新标签页的缎带放在两边)：
    战团徽(照用户参考图描的完整徽记)按新标签页徽章的套色画法(emblem_stamp)，整枚叠颗粒 × 磨损；
    身后横穿新标签页那条绶带(不带字，build.ribbon_arc 的位图 ribbon，显示尺寸 rib_w × rib_h、宽带中线在 rib_mid)，
    宽带中线落在徽记高度的 band 处，被双翼和血滴挡住正中、两端在左右翘起；绶带在徽记周围让出 rgap 宽的纸色空隙。
    单位 = 显示 px(CSS 里按 eh 原样大小放)，徽记底边贴图底"""
    vb, parts = _logo_parts()
    s = eh / vb[3]
    ew = vb[2] * s
    rib_y0 = eh * band - rib_mid                 # 绶带图顶在徽记顶下多少(可能是负的)
    top = max(0.0, -rib_y0)                      # 图顶到徽记顶
    H = top + max(eh, rib_y0 + rib_h)
    ex, ey = (W - ew) / 2, top
    tf = f"translate({ex:.2f} {ey:.2f}) scale({s:.5f})"
    mu = f'maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H:.2f}"'
    full = f'<rect width="{W}" height="{H:.2f}" fill="#fff"/>'
    sil = "".join(f'<path d="{parts[k]}"/>' for k in ("wing-l", "wing-r", "drop"))
    defs, art = emblem_stamp(tf, s, mu, full, gold, shade, shift, gap, ink_dark, (0, 0, W, f"{H:.2f}"))
    # 绶带：徽记外扩 rgap 让出空隙
    defs += (f'<mask id="mr" {mu}>{full}<g transform="{tf}" fill="#000" stroke="#000" stroke-width="{2 * rgap / s:.1f}" '
             f'stroke-linejoin="round">{sil}</g></mask>')
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="256" height="256">'
                 f'<image href="{ink}" width="256" height="256"/></pattern>'
                 f'<mask id="mk" {mu}><rect width="{W}" height="{H:.2f}" fill="url(#ip)"/>'
                 + (f'<image href="{wear}" width="{W}" height="{H:.2f}" preserveAspectRatio="none"/>' if wear else "")
                 + '</mask>')
        art = f'<g mask="url(#mk)">{art}</g>'
    rib = (f'<g mask="url(#mr)"><image href="{ribbon}" x="0" y="{top + rib_y0:.2f}" width="{rib_w:.2f}" height="{rib_h:.2f}" '
           'preserveAspectRatio="none"/></g>')
    return f'<svg {SVG} viewBox="0 0 {W} {H:.2f}"><defs>{defs}</defs>{rib}{art}</svg>', H


# ---- 巴洛克花纹素材(第十二版二稿，用户：花纹不用自己画，从下载的 SVG 里选合适的改造融入)：
# 素材库 Flourishes 文件夹(frame-illust.com 风格的黑色线稿，Illustrator 导出，只有 path、没有 transform)。按序号取部件
# (序号 = 文件里 path 出现的顺序，scratchpad ba_svgparts.py 出带编号的总览图)，重新上主题的金色、叠颗粒
FLOURISH_SRC = Path(r"E:\AI工作\素材库\Flourishes")


def _asset_paths(name):
    src = (FLOURISH_SRC / f"{name}.svg").read_text(encoding="utf-8")
    return re.findall(r'<path\b[^>]*?\sd="([^"]+)"', src, re.S)


# f0640_2(一对莨苕叶，左右镜像)：每片 = 前层主叶(4 / 9) + 后层外沿一道窄边(1 / 6)，中间本来就隔着空隙；根部一个小结(0 / 5)、
# 两片小叶(2、3 / 7、8)。第十三版(用户：标题花纹不满意，用 f0640_2 试试，颜色纹理要和谐)：
# 主叶 = 标题徽记双翼同一套金，后层窄边 = 深一档的金(新标签页那种第二套色)，小结、小叶同主叶；颗粒和徽记同一张图
F0640_LEAF = {"left": {"front": [4], "back": [1], "small": [0, 2, 3], "pivot": (200, 400)},
              "right": {"front": [9], "back": [6], "small": [5, 7, 8], "pivot": (600, 400)}}
TITLE_FL_H = 44                                  # 显示高度(px)，宽按比例


def _bbox_rot(pts, ang, c):
    """一组点绕 c 转 ang 度后的包围盒"""
    a = math.radians(ang)
    xs, ys = [], []
    for x, y in pts:
        dx, dy = x - c[0], y - c[1]
        xs.append(c[0] + dx * math.cos(a) - dy * math.sin(a))
        ys.append(c[1] + dx * math.sin(a) + dy * math.cos(a))
    return min(xs), min(ys), max(xs), max(ys)


def _path_points(d):
    """粗略取 path 里的坐标点(Illustrator 导出：绝对 M/C/S/L 和相对 c/s/l 混用)，只用来估包围盒——
    相对坐标按累加处理，曲线控制点也算进去(包围盒会稍大一点，够用)"""
    toks = re.findall(r"[MmCcSsLlHhVvZzQqTtAa]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pts, cmd, i, cur, start = [], "M", 0, (0.0, 0.0), (0.0, 0.0)
    nums = []
    out = []
    for t in toks:
        if t.isalpha():
            if nums:
                out.append((cmd, nums))
            cmd, nums = t, []
        else:
            nums.append(float(t))
    out.append((cmd, nums))
    for cmd, n in out:
        rel = cmd.islower()
        C = cmd.upper()
        step = {"M": 2, "L": 2, "C": 6, "S": 4, "Q": 4, "T": 2, "H": 1, "V": 1, "A": 7, "Z": 0}[C]
        if C == "Z":
            cur = start
            continue
        for k in range(0, len(n), step):
            g = n[k:k + step]
            if len(g) < step:
                break
            if C == "H":
                cur = (g[0] + (cur[0] if rel else 0), cur[1])
                pts.append(cur)
                continue
            if C == "V":
                cur = (cur[0], g[0] + (cur[1] if rel else 0))
                pts.append(cur)
                continue
            if C == "A":
                cur = (g[5] + (cur[0] if rel else 0), g[6] + (cur[1] if rel else 0))
                pts.append(cur)
                continue
            base = cur if rel else (0.0, 0.0)
            pp = [(g[j] + base[0], g[j + 1] + base[1]) for j in range(0, step, 2)]
            pts += pp
            cur = pp[-1]
            if C == "M" and k == 0:
                start = cur
    return pts


def title_flourish(side="right", gold=("#d6b46a", "#bf9a52"), shade="#a3814a", ink=None, ang=None, h=TITLE_FL_H, flip=False):
    """笔记标题两侧的花边：f0640_2 的莨苕叶，转 ang 度(左片默认 −90°：根部朝标题、叶尖朝外；右片镜像)，
    主叶缎面金、后层窄边深一档的金、颗粒。返回 (SVG, 显示宽, 显示高)"""
    L = F0640_LEAF[side]
    if ang is None:
        ang = -90
    if side == "right":
        ang = -ang
    paths = _asset_paths("f0640_2")
    idx = L["front"] + L["back"] + L["small"]
    pts = [p for i in idx for p in _path_points(paths[i])]
    py = L["pivot"][1]
    if flip:                                     # 先上下翻转(绕支点所在水平线)，再旋转
        pts = [(x, 2 * py - y) for x, y in pts]
    x0, y0, x1, y1 = _bbox_rot(pts, ang, L["pivot"])
    pad = 2
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    w, hh = x1 - x0, y1 - y0
    rot = f'rotate({ang} {L["pivot"][0]} {L["pivot"][1]})' + (f' translate(0 {2 * py}) scale(1 -1)' if flip else "")
    g = lambda ids: "".join(f'<path d="{paths[i]}"/>' for i in ids)
    defs = (f'<linearGradient id="fg" gradientUnits="userSpaceOnUse" x1="0" y1="{y0:.1f}" x2="0" y2="{y1:.1f}">'
            f'<stop offset="0" stop-color="{gold[0]}"/><stop offset="1" stop-color="{gold[1]}"/></linearGradient>')
    body = (f'<g transform="{rot}"><g fill="{shade}">{g(L["back"])}</g>'
            f'<g fill="url(#fg)">{g(L["front"])}{g(L["small"])}</g></g>')
    if ink:
        c = 256 * hh / h                         # 颗粒一格 = 256 显示 px
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="{c:.1f}" height="{c:.1f}">'
                 f'<image href="{ink}" width="{c:.1f}" height="{c:.1f}"/></pattern>'
                 f'<mask id="mk" maskUnits="userSpaceOnUse" x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{hh:.1f}">'
                 f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{hh:.1f}" fill="url(#ip)"/></mask>')
        body = f'<g mask="url(#mk)">{body}</g>'
    return (f'<svg {SVG} viewBox="{x0:.1f} {y0:.1f} {w:.1f} {hh:.1f}"><defs>{defs}</defs>{body}</svg>',
            h * w / hh, h)


F1090_ARM_CUT = 55.0                           # 素材臂上箭头—菱形那段直线的中间
F1090_ARM_LINE = (28.7, 32.6)                  # 直线的上下沿


def title_rule_arm(side="left", style="rule", sh=19, length=92, ink=None, line=1.3, extend=0):
    """笔记标题两端的花边(第十五版，用户：叶子躺平不够，或者用分割线的样式放在文字两端)。返回 (SVG, 显示宽, 显示高)，
    图的竖直中线 = 金线所在高度(CSS 里 center 对齐就落在文字块中间)。左片：卷草在右端(贴着标题)、线往左伸
    style = "rule"：分割线同款——f1090_1 的「∞」卷草组(高 sh) + 金线向外渐隐(长 length) + 下面 3.5px 一道更短的细浅金线
    style = "asset"：素材原样的整只臂(外端箭头 + 菱形 + 横线 + 「∞」卷草)，没有自己画的线。
    extend(显示 px，第十六版用户：F 的横线稍微加长——只加长菱形外面那段，菱形还贴着卷草)：在箭头—菱形那段直线中间切一刀，
    箭头往外平移 extend，空出来的地方补同样粗细的直线——箭头、菱形的形状不变"""
    paths = _asset_paths("f1090_1")
    idx, x0, _ = F1090_SCROLL["left"]
    k = sh / 58.2
    ly = F1090_LINE_Y
    e = extend / k if style == "asset" else 0     # 素材单位
    if style == "asset":
        idx, x0 = [i for i in range(8) if i != 3 or not e], 4.0 - e     # 3 = 箭头 + 菱形 + 横线
    x1 = 294.1                                     # 卷草组内端(含小卷)的外沿
    W = (x1 - x0) * k + (length if style == "rule" else 0) + 2
    half = max(ly, 64 - ly) * k + 2
    H = 2 * half
    tx, ty = W - 1 - x1 * k, half - ly * k
    defs = ('<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
            + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS) + '</linearGradient>')
    arm = ""
    if e:
        ca, (y0, y1) = F1090_ARM_CUT, F1090_ARM_LINE
        p3 = paths[3]
        clip = lambda i, a, b: (f'<clipPath id="c{i}" clipPathUnits="userSpaceOnUse">'
                                f'<rect x="{a}" y="0" width="{b - a}" height="64"/></clipPath>')
        # 切开的两段用 path 3 自己的包围盒做渐变(和没切时一样)，补的直线也用同一套坐标
        defs += (clip("a", -1000, ca) + clip("b", ca, 1000)
                 + f'<linearGradient id="sg3" gradientUnits="userSpaceOnUse" x1="0" y1="20.4" x2="0" y2="40.9">'
                 + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS) + '</linearGradient>')
        arm = (f'<g transform="translate({-e:.2f} 0)"><path d="{p3}" clip-path="url(#ca)"/></g>'
               f'<path d="{p3}" clip-path="url(#cb)"/>'
               f'<path fill="url(#sg3)" d="M{ca - e - .3:.2f},{y0}H{ca + .3:.2f}V{y1}H{ca - e - .3:.2f}Z"/>')
    body = (f'<g fill="url(#sg)" transform="translate({tx:.2f} {ty:.2f}) scale({k:.5f})">'
            + "".join(f'<path d="{paths[i]}"/>' for i in idx) + arm + '</g>')
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="256" height="256">'
                 f'<image href="{ink}" width="256" height="256"/></pattern>'
                 f'<mask id="mk" maskUnits="userSpaceOnUse" x="0" y="0" width="{W:.1f}" height="{H:.1f}">'
                 f'<rect width="{W:.1f}" height="{H:.1f}" fill="url(#ip)"/></mask>')
        body = f'<g mask="url(#mk)">{body}</g>'
    if style == "rule":
        sx = tx + x0 * k                           # 卷草外端大卷的外沿，金线从这里接出去
        defs += (f'<linearGradient id="f" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{sx:.1f}" y2="0">'
                 '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".55" stop-color="#fff"/></linearGradient>'
                 f'<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W:.1f}" height="{H:.1f}">'
                 f'<rect width="{W:.1f}" height="{H:.1f}" fill="url(#f)"/></mask>'
                 f'<linearGradient id="f2" gradientUnits="userSpaceOnUse" x1="{sx * .25:.1f}" y1="0" x2="{sx:.1f}" y2="0">'
                 '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".6" stop-color="#fff"/></linearGradient>'
                 f'<mask id="m2" maskUnits="userSpaceOnUse" x="0" y="0" width="{W:.1f}" height="{H:.1f}">'
                 f'<rect width="{W:.1f}" height="{H:.1f}" fill="url(#f2)"/></mask>')
        body = (f'<path d="M{sx + .3:.2f},{half:.2f} L0,{half:.2f}" stroke="{C_GOLD}" stroke-width="{line}" mask="url(#m)"/>'
                f'<path d="M{sx - 4:.2f},{half + 3.5:.2f} L0,{half + 3.5:.2f}" stroke="{C_GOLD}" stroke-opacity=".6" '
                f'stroke-width=".8" mask="url(#m2)"/>' + body)
    if side == "right":
        body = f'<g transform="translate({W:.2f} 0) scale(-1 1)">{body}</g>'
    return f'<svg {SVG} viewBox="0 0 {W:.1f} {H:.1f}"><defs>{defs}</defs>{body}</svg>', W, H


def emblem():
    """只有战团徽(不衬铁光环)"""
    vb, _ = _logo_parts()
    return f'<svg {SVG} viewBox="{" ".join(f"{v:g}" for v in vb)}"><defs>{LOGO_DEFS}</defs>{_logo_body()}</svg>'


# ---- 铁光环(战锤 40K 的 Iron Halo)：一圈金环带 + 环上铆钉 + 向外的长短光刃，四正向的光刃加长成十字 ----
def iron_halo_body(cx, cy, r, fill="url(#hg)", rivet=C_GOLD_DEEP, n=24, band=.17, long_=.62, short=.34, cross=.82):
    """r = 环带外半径；光刃从环带外缘伸出 long_ / short 倍 r(交替)，0/90/180/270° 的四刃伸到 cross 倍"""
    r_in = r * (1 - band)
    blades = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        main = i % (n // 4) == 0
        ln = cross if main else (long_ if i % 2 == 0 else short)
        half = math.radians(5.2 if main else (4.4 if i % 2 == 0 else 3.6))
        tip = (cx + (r + r * ln) * math.cos(a), cy + (r + r * ln) * math.sin(a))
        b1 = (cx + (r - 1) * math.cos(a - half), cy + (r - 1) * math.sin(a - half))
        b2 = (cx + (r - 1) * math.cos(a + half), cy + (r - 1) * math.sin(a + half))
        blades.append(f"M{b1[0]:.2f},{b1[1]:.2f} L{tip[0]:.2f},{tip[1]:.2f} L{b2[0]:.2f},{b2[1]:.2f}Z")
    ring = (f"M{cx - r:.2f},{cy:.2f} A{r:.2f},{r:.2f} 0 1 0 {cx + r:.2f},{cy:.2f} A{r:.2f},{r:.2f} 0 1 0 {cx - r:.2f},{cy:.2f}Z "
            f"M{cx - r_in:.2f},{cy:.2f} A{r_in:.2f},{r_in:.2f} 0 1 1 {cx + r_in:.2f},{cy:.2f} A{r_in:.2f},{r_in:.2f} 0 1 1 {cx - r_in:.2f},{cy:.2f}Z")
    rm = (r + r_in) / 2
    rivets = "".join(f'<circle cx="{cx + rm * math.cos(2 * math.pi * k / 12):.2f}" cy="{cy + rm * math.sin(2 * math.pi * k / 12):.2f}" '
                     f'r="{r * band * .2:.2f}" fill="{rivet}"/>' for k in range(12))
    return (f'<path d="{" ".join(blades)}" fill="{fill}"/><path d="{ring}" fill="{fill}" fill-rule="evenodd"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r_in:.2f}" fill="none" stroke="{C_GOLD_DEEP}" stroke-width="{r * .025:.2f}" stroke-opacity=".6"/>'
            + rivets)


def iron_halo_small(size=32):
    """小尺寸(标题 / 列表符号 12–16px)：光刃减到 12 条、加粗，环带加厚，铆钉去掉，才认得出是光环"""
    c = size / 2
    r = size / 2 / 1.7
    return (f'<svg {SVG} viewBox="0 0 {size} {size}"><defs>{gold_defs("hg")}</defs>'
            f'{iron_halo_body(c, c, r, n=12, band=.3, long_=.62, short=.38, cross=.7, rivet="none")}</svg>')


def iron_halo(size=64):
    c = size / 2
    r = size / 2 / 1.82
    return (f'<svg {SVG} viewBox="0 0 {size} {size}"><defs>{gold_defs("hg", angle=(0, 0, 1, 1))}</defs>'
            f'{iron_halo_body(c, c, r)}</svg>')


# ---- 分隔线：整条一张不定宽 SVG(CSS background-size: 100% RULE_H)。中央战团徽，两侧两道金线一路画到头、两端渐隐。
# 根 svg 不写宽高 / viewBox，用户单位 = CSS px；中心内容放进 x=50% 的嵌套 svg(线和徽在同一张图里，125% 缩放下接口不错位)
RULE_H = 36
# f1090_1(一对分隔花饰：外端箭头 + 菱形的横线，内端一个「∞」形大卷 + 几个小卷和叶)：只取内端的卷草组，横线自己画
F1090_SCROLL = {"left": ([0, 1, 2, 4, 5, 6, 7], 161.1, 291.5), "right": ([8, 9, 10, 12, 13, 14, 15], 508.0, 638.9)}
F1090_LINE_Y = 30.7                          # 原图横线(接进「∞」大卷)的高度


def _rule_asset(ink, ew, gap, k, cy, R, mu, edefs, emb, paths, extend, fluid):
    """分割线的素材臂版(第十七版对比用，用户：分割线试一下 F 和加长款)：徽记两侧各一只 f1090_1 整臂(外端箭头 + 菱形 + 横线 +
    「∞」卷草)，右侧 = 左侧镜像。extend：箭头—菱形那段直线加长(px，菱形仍贴着卷草)；fluid(px)：箭头放到整条线两端往里 fluid 处，
    中间的直线随宽度伸缩(rect 的 x / width 用 CSS calc)"""
    ca, (y0, y1) = F1090_ARM_CUT, F1090_ARM_LINE
    x1 = F1090_SCROLL["left"][2]
    e = 0 if fluid is not None else extend / k
    tx, oy = -ew / 2 - gap - x1 * k, cy - F1090_LINE_Y * k
    p3 = paths[3]
    cut = bool(e) or fluid is not None
    clip = (f'<clipPath id="ra" clipPathUnits="userSpaceOnUse"><rect x="-1000" y="0" width="{1000 + ca}" height="64"/></clipPath>'
            f'<clipPath id="rb" clipPathUnits="userSpaceOnUse"><rect x="{ca}" y="0" width="1000" height="64"/></clipPath>')
    arm = "".join(f'<path d="{paths[i]}"/>' for i in range(8) if i != 3)
    if not cut:
        arm += f'<path d="{p3}"/>'
    else:
        arm += f'<path d="{p3}" clip-path="url(#rb)"/>'
        if e:
            arm += (f'<g transform="translate({-e:.2f} 0)"><path d="{p3}" clip-path="url(#ra)"/></g>'
                    f'<path d="M{ca - e - .3:.2f},{y0}H{ca + .3:.2f}V{y1}H{ca - e - .3:.2f}Z"/>')
    left = f'<g transform="translate({tx:.2f} {oy:.2f}) scale({k:.5f})">{arm}</g>'
    groups = left + f'<g transform="scale(-1 1)">{left}</g>'
    gold = ('<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
            + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS) + '</linearGradient>')
    center = f'<g fill="url(#sg)">{groups}</g>{emb}'
    defs = clip + gold + edefs
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="256" height="256">'
                 f'<image href="{ink}" width="256" height="256"/></pattern>'
                 f'<mask id="mk" {mu}><rect x="{-R:.1f}" y="0" width="{2 * R:.1f}" height="{RULE_H}" fill="url(#ip)"/></mask>')
        center = f'<g mask="url(#mk)">{center}</g>'
    edge = ""
    if fluid is not None:
        tip = f'<g transform="translate({fluid - 4 * k:.2f} {oy:.2f}) scale({k:.5f})"><path d="{p3}" clip-path="url(#ra)"/></g>'
        a = fluid + (ca - 4) * k - .3                    # 箭头段内端(离边)
        b = -(tx + ca * k) - .3                          # 中段切口离中心
        ry, rh = oy + y0 * k, (y1 - y0) * k
        w = f"calc(50% - {a + b - .6:.2f}px)"
        edge = (f'<g fill="url(#sg)"><svg x="0" overflow="visible">{tip}</svg>'
                f'<svg x="100%" overflow="visible"><g transform="scale(-1 1)">{tip}</g></svg>'
                f'<rect y="{ry:.2f}" height="{rh:.2f}" style="x: {a:.2f}px; width: {w}"/>'
                f'<rect y="{ry:.2f}" height="{rh:.2f}" style="x: calc(50% + {b:.2f}px); width: {w}"/></g>')
    return f'<svg {SVG}><defs>{defs}</defs>{edge}<svg x="50%" overflow="visible">{center}</svg></svg>'


def rule_center(ink=None, eh=31, sh=17, gap=3, line=1.3, arm="scroll", extend=0, fluid=None):
    """第十二版二稿(用户：两边的两个血滴和中间主次不分、弧度也不一致，要改构图；两边的横线也可以用巴洛克花纹)：
    中央只留一个主角——套色画法的战团徽(emblem_stamp，高 eh)；紧挨着两侧是 f1090_1 的「∞」卷草组(高 sh，小一号作陪衬)，
    金线从卷草外端的大卷接出去，一路画到头、两端渐隐。去掉了原来线头的两枚小血滴(和徽记的血滴抢、形状也不统一)。
    中央部分叠印刷颗粒"""
    far = 8000
    cy = RULE_H / 2
    fade = ('<linearGradient id="f" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="100%" y2="0">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".3" stop-color="#fff"/>'
            '<stop offset=".7" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            '<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%">'
            '<rect width="100%" height="100%" fill="url(#f)"/></mask>')
    vb, _ = _logo_parts()
    s = eh / vb[3]
    ew = vb[2] * s
    tf = f"translate({-ew / 2:.2f} {cy - eh / 2:.2f}) scale({s:.5f})"
    k = sh / 58.2
    R = 200
    if arm == "asset" and fluid is None:
        R = max(R, ew / 2 + gap + (F1090_SCROLL["left"][2] - 4) * k + extend + 10)
    mu = f'maskUnits="userSpaceOnUse" x="{-R:.1f}" y="0" width="{2 * R:.1f}" height="{RULE_H}"'
    full = f'<rect x="{-R:.1f}" y="0" width="{2 * R:.1f}" height="{RULE_H}" fill="#fff"/>'
    edefs, emb = emblem_stamp(tf, s, mu, full, gap=1.2, shift=(-1.2, -.9), p="e")
    paths = _asset_paths("f1090_1")
    if arm == "asset":
        return _rule_asset(ink, ew, gap, k, cy, R, mu, edefs, emb, paths, extend, fluid)
    # 卷草组：内端贴着徽记翼尖外 gap，原图横线高度对准中线
    groups, starts = "", {}
    for side, (idx, x0, x1) in F1090_SCROLL.items():
        tx = (-ew / 2 - gap - x1 * k) if side == "left" else (ew / 2 + gap - x0 * k)
        starts[side] = tx + (x0 if side == "left" else x1) * k        # 外端大卷的外沿
        groups += (f'<g transform="translate({tx:.2f} {cy - F1090_LINE_Y * k:.2f}) scale({k:.5f})">'
                   + "".join(f'<path d="{paths[i]}"/>' for i in idx) + '</g>')
    gold = ('<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
            + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS) + '</linearGradient>')
    lines = (f'<path d="M{starts["left"] + .3:.2f},{cy} L{-far},{cy} M{starts["right"] - .3:.2f},{cy} L{far},{cy}" '
             f'stroke="{C_GOLD}" stroke-width="{line}"/>')
    # 第十四版(用户：再加一条和第一版一样、更短的双线)：主线下方 3.5px 一道细浅金线，从卷草外端稍往外起，渐隐得更早(自己的遮罩 m2)
    fade += ('<linearGradient id="f2" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="100%" y2="0">'
             '<stop offset=".14" stop-color="#fff" stop-opacity="0"/><stop offset=".36" stop-color="#fff"/>'
             '<stop offset=".64" stop-color="#fff"/><stop offset=".86" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             '<mask id="m2" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%">'
             '<rect width="100%" height="100%" fill="url(#f2)"/></mask>')
    y2 = cy + 3.5
    lines2 = (f'<path d="M{starts["left"] - 4:.2f},{y2} L{-far},{y2} M{starts["right"] + 4:.2f},{y2} L{far},{y2}" '
              f'stroke="{C_GOLD}" stroke-opacity=".6" stroke-width=".8"/>')
    center = f'<g fill="url(#sg)">{groups}</g>{emb}'
    defs = fade + gold + edefs
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="256" height="256">'
                 f'<image href="{ink}" width="256" height="256"/></pattern>'
                 f'<mask id="mk" {mu}><rect x="{-R}" y="0" width="{2 * R}" height="{RULE_H}" fill="url(#ip)"/></mask>')
        center = f'<g mask="url(#mk)">{center}</g>'
    return (f'<svg {SVG}><defs>{defs}</defs>'
            f'<g mask="url(#m)"><svg x="50%" overflow="visible">{lines}</svg></g>'
            f'<g mask="url(#m2)"><svg x="50%" overflow="visible">{lines2}</svg></g>'
            f'<svg x="50%" overflow="visible">{center}</svg></svg>')


# ---- H1：无畏石棺式卷轴横幅(border-image 九宫格：左右两端固定，中段拉伸)。
# 正面一条直的骨白宽带(上下各一道金线)，两端后面各一截燕尾飘带，正面和飘带之间一块暗色折角。
# 中段必须是一条直带，拉伸才不变形。设计坐标高 BANNER_H，两端各 BANNER_SLICE 宽
BANNER_H, BANNER_SLICE, BANNER_MID = 60, 40, 120


def banner(W=None, stretch=True):
    """W = 总宽(默认九宫格设计宽；新标签页题铭用定宽)；stretch = 给 border-image 用(preserveAspectRatio none)"""
    W = W or BANNER_SLICE * 2 + BANNER_MID
    H, S = BANNER_H, BANNER_SLICE
    f_top, f_bot = 6, 46           # 正面宽带
    t_top, t_bot = 16, 56          # 飘带
    fx = 26                        # 正面宽带左端 x(右端对称)
    out = []

    def tail(side):
        # 燕尾飘带：从正面后方伸出，外端 V 形缺口，缺口两尖微微上卷
        if side < 0:
            p = f"M{fx + 12},{t_top} L4,{t_top} C9,{t_top + 6} 13,{(t_top + t_bot) / 2 - 4} 15,{(t_top + t_bot) / 2} " \
                f"C13,{(t_top + t_bot) / 2 + 4} 9,{t_bot - 6} 4,{t_bot} L{fx + 12},{t_bot}Z"
        else:
            p = f"M{W - fx - 12},{t_top} L{W - 4},{t_top} C{W - 9},{t_top + 6} {W - 13},{(t_top + t_bot) / 2 - 4} {W - 15},{(t_top + t_bot) / 2} " \
                f"C{W - 13},{(t_top + t_bot) / 2 + 4} {W - 9},{t_bot - 6} {W - 4},{t_bot} L{W - fx - 12},{t_bot}Z"
        return f'<path d="{p}" fill="url(#back)" stroke="{C_UMBER}" stroke-width="1.3" stroke-linejoin="round"/>'

    def fold(side):
        x0 = fx if side < 0 else W - fx
        x1 = x0 + 12 * (-side if side > 0 else 1)
        return f'<path d="M{x0},{f_bot} L{x1},{t_bot} L{x1},{f_bot}Z" fill="#b9a27a" stroke="{C_UMBER}" stroke-width="1.1" stroke-linejoin="round"/>'

    defs = ('<linearGradient id="front" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffdf7"/>'
            '<stop offset=".55" stop-color="#f7efdd"/><stop offset="1" stop-color="#e9dcc0"/></linearGradient>'
            '<linearGradient id="back" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#efe4cc"/>'
            '<stop offset="1" stop-color="#d9c8a4"/></linearGradient>'
            + gold_defs("gl", angle=(0, 0, 1, 0)))
    out += [tail(-1), tail(1), fold(-1), fold(1)]
    out.append(f'<rect x="{fx}" y="{f_top}" width="{W - 2 * fx}" height="{f_bot - f_top}" fill="url(#front)" stroke="{C_UMBER}" stroke-width="1.3"/>')
    for y in (f_top + 3.5, f_bot - 3.5):
        out.append(f'<path d="M{fx + 4},{y} H{W - fx - 4}" stroke="{C_GOLD}" stroke-width="1"/>')
    par = ' preserveAspectRatio="none"' if stretch else ""
    return f'<svg {SVG} viewBox="0 0 {W} {H}"{par}><defs>{defs}</defs>{"".join(out)}</svg>'


# ---- 石棺式镶框血滴(H2)：金箔外框 + 宝石红血滴 + 高光 ----
def framed_drop():
    return (f'<svg {SVG} viewBox="0 0 16 24"><defs>{gold_defs("g")}{blood_defs("b")}</defs>'
            f'<path d="{drop_path(8, .4, 23.2)}" fill="url(#g)"/>'
            f'<path d="{drop_path(8, 4.6, 17.2)}" fill="url(#b)"/></svg>')


# ---- 列表符号：一级 = 宝石红小血滴；二级 = 金箔空心血滴；三级 = 金箔小铁光环 ----
def bullet_drop():
    return (f'<svg {SVG} viewBox="0 0 10 15"><defs>{blood_defs("b")}</defs>'
            f'<path d="{drop_path(5, .3, 14.4)}" fill="url(#b)"/></svg>')


def bullet_drop_hollow():
    d_out, d_in = drop_path(5, .3, 14.4), drop_path(5, 4.4, 8.4)
    return (f'<svg {SVG} viewBox="0 0 10 15"><defs>{gold_defs("g")}</defs>'
            f'<path d="{d_out} {d_in}" fill="url(#g)" fill-rule="evenodd"/></svg>')


# ---- 纯洁封印(引用块)：红蜡封 + 压印的战团徽 + 两条垂下的羊皮纸条(上面几行看不清的小字) ----
# 第七版(用户：印记颜色太深看不清、蜡边太崎岖、纸条和横线太直，要像别的缎带那样弯；引文左边竖线被封印挡住像 bug)：
#  · 蜡封提亮一档，边缘只留几个很缓的起伏(平滑曲线，不再是锯齿)；压印的战团徽改成浅金色，压在略深的圆形印面里，一眼看得清；
#  · 纸条 = 两条弯曲的小缎带：中心线是 S 形三次曲线，宽度不变、下端燕尾；纸条上的字行跟着纸条转向，每行再微微弯成弧
#    (纸面卷曲，同 H1 横幅上下沿的画法)，长短不齐像一行行小字；配色同绶带的羊皮纸；
#  · 封印整体缩短到 62 高(单行引文也装得下，不再伸进下一段)；竖线挪到封印左边，不再从封印底下穿过(见 theme.src.css 引用块)
# 第八版(用户：印记颜色太刺眼、左边纸条翻转处像打了个结，要和新标签页统一风格)：改成和新标签页徽章同一套"套色印章"画法——
#  · 不要深色描边：蜡、印面、两条纸条都是平涂色块，彼此之间留一道纸色细缝(遮罩抠出来，透出引用块的底色)；
#  · 蜡色降饱和、压暗一点(旧封蜡的砖红)，印面再深一档；战团徽不再涂金，直接在印面上抠空(透出纸色)，像参考图里的米白星芒；
#  · 纸条不再翻转，两条都只是缓缓弯开、下端燕尾；字行用深一档的羊皮纸色；
#  · 整枚叠同一种印刷颗粒(tex_ink 的小图)
SEAL_W, SEAL_H = 38, 62


def _smooth_closed(pts):
    """闭合折线 → 平滑闭合曲线(Catmull-Rom 转三次贝塞尔)"""
    n = len(pts)
    d = f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}"
    return d + "Z"


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * e for a, b, c, e in zip(p0, p1, p2, p3))


def _seal_strip(p0, p1, p2, p3, w, notch=4.2, rows=(), twist=None, n=40, w0=None, t1=.35):
    """一条弯曲的纸条：中心线三次曲线 p0→p3(p0 压在蜡下)，宽 w，下端燕尾；rows = [(t, 长度比例)] 字行位置。
    twist = (t1, t2)：纸条在这一段翻转一次(同绶带的画法)——看到的宽度 = w·cos θ，θ 从 0 转到 π，正中掐成一点，
    之后露出背面。返回 (正面 path, 背面 path 或 "", 字行 path)"""
    cen = [_bez(p0, p1, p2, p3, i / n) for i in range(n + 1)]
    nor = []
    for i in range(n + 1):
        a, b = cen[max(i - 1, 0)], cen[min(i + 1, n)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nor.append((-dy / L, dx / L))

    def width(t):
        if w0 is not None and t < t1:                       # 根部收窄(压在蜡下面的那一截)，到 t1 放到全宽
            k = t / t1
            return w0 + (w - w0) * k * k * (3 - 2 * k)
        if not twist or t <= twist[0]:
            return w
        if t >= twist[1]:
            return -w
        return w * math.cos(math.pi * (t - twist[0]) / (twist[1] - twist[0]))
    ws = [width(i / n) for i in range(n + 1)]
    left = [(x + nx * s / 2, y + ny * s / 2) for (x, y), (nx, ny), s in zip(cen, nor, ws)]
    right = [(x - nx * s / 2, y - ny * s / 2) for (x, y), (nx, ny), s in zip(cen, nor, ws)]
    ex, ey = cen[-1]
    tx, ty = nor[-1][1], -nor[-1][0]                      # 末端的走向(向下)
    tip = (ex - tx * notch, ey - ty * notch)
    poly = lambda pts: "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"
    if twist:
        im = round((twist[0] + twist[1]) / 2 * n)          # 掐成一点的位置
        body = poly(left[:im + 1] + right[im::-1])
        back = poly(left[im:] + [tip] + right[:im - 1:-1])
    else:
        body, back = poly(left + [tip] + right[::-1]), ""
    lines = []
    for t, k in rows:
        x, y = _bez(p0, p1, p2, p3, t)
        i = round(t * n)
        nx, ny = nor[i]
        m = w / 2 - 1.5                                    # 字行从纸条一侧起笔，长度 = 可写宽度 × k
        b = (x - nx * m, y - ny * m)
        a = (b[0] + nx * 2 * m * k, b[1] + ny * 2 * m * k)
        tx_, ty_ = nor[i][1], -nor[i][0]
        mx, my = (a[0] + b[0]) / 2 + tx_ * .9, (a[1] + b[1]) / 2 + ty_ * .9   # 往下弯一点(纸面卷曲)
        lines.append(f"M{a[0]:.2f},{a[1]:.2f} Q{mx:.2f},{my:.2f} {b[0]:.2f},{b[1]:.2f}")
    return body, back, " ".join(lines)


# 纸条中心线(相对蜡封圆心)。第九版(用户：两条纸条往两边扒开，没有美感；稍微改一下弧度，但不要变成直线)：
# 基本竖直垂下，先往外摆一点再收回、末端微微分开(很缓的 S 形)；比过收拢 S 形(实际尺寸两条挨在一起)、同向飘(交叠)、括号内收(像夹住)
# 第十版(用户：只有一行的引文也被撑成两行高，想一行时只露封蜡、不要纸条)：引文块的高度裁掉纸条(见 CSS)，
# 所以纸条根部要收窄、贴着蜡的正中往下走，一直藏在蜡底下，直到一行的高度以下才露出来(否则一行时蜡边会露出一点纸条茬)；
# 整体缩短到两行(59px)装得下，不再需要给引文撑最小高度
SEAL_STRIPS = (((-2.3, 4), (-2.5, 15), (-7.5, 23), (-5.5, 38.5)),
               ((2.3, 4), (2.5, 14), (7.5, 20), (5.5, 33.5)))
SEAL_TAPER = (4.2, .4)                       # 纸条根部宽度、放到全宽的位置


# ---- callout 的花角(第十九版，用户：callout 太现代，重新设计，可以自由运用边框花纹)：素材库 Flourishes 里三套花角边框，
# 每套四个角各是一组 path(左上角那组的序号)。只取左上角，其余三个角镜像出来，保证四角一致
FRAME_CORNERS = {"f1527_0": range(0, 25), "f1502_2": range(18, 36)}
# 第二十版(用户：花角和边线的连接处错位)：按原图的坐标来——角图 = 原图左上 U × U 的一块(原图的外角点就是图的角)，
# 边线 = 原图里那几条 rect 的位置(中心线、粗细，原图单位)：上 / 下边 h，左 / 右边 v；细线正好接在卷草末端那道卷须上
FRAME_LINES = {"f1527_0": dict(U=110.0, h=((3.6, 2.2), (8.45, .5)), v=((5.1, 2.2), (9.95, .5))),
               "f1502_2": dict(U=96.0, h=((7.1, 4.2), (13.75, 2.1)), v=((8.3, 4.2), (15.05, 2.1)))}


# ---- 书签卡片的卡片花边(第四十二版，侧栏花边样稿 H，用户先实装看看)：f1509_4 整副边框(800 × 566.4)按九宫格切开——
# 四角各取原图 U × U(镂空线描花角)，四边取两角之间的中段(双线)，主题里角 24px、边拉长。
# 原图 121 条 path，0–4 号是贯穿整副的框线(各只有一两条子路径)，整条嵌进每一块要 ~190KB：
# 边的中段在任何位置截下去都是同样四道细线(两组双线)，按原图截出的位置画成四条矩形；
# 角 = 落在角里的小 path(原样) + 0–4 号框线裁到这一角(曲线拆成折线，shapely 求交)
CARD_FRAME_ASSET, CARD_FRAME_U, CARD_FRAME_BIG = "f1509_4", 140.0, 5


def _rings(d, n=12):
    """path 的每条子路径拆成折线(曲线各取 n 段)"""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.svgLib.path import parse_path
    rp = RecordingPen()
    parse_path(d, rp)
    out, cur = [], []
    for op, args in rp.value:
        if op == "moveTo":
            if len(cur) > 2:
                out.append(cur)
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op in ("curveTo", "qCurveTo"):
            pts = [cur[-1], *args]
            for i in range(1, n + 1):
                t, q = i / n, pts
                while len(q) > 1:                   # de Casteljau
                    q = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(q, q[1:])]
                cur.append(q[0])
        elif op in ("closePath", "endPath"):
            if len(cur) > 2:
                out.append(cur)
            cur = []
    if len(cur) > 2:
        out.append(cur)
    return out


def _card_frame_big():
    """0–4 号框线的填充区域(奇偶规则，同一条 path 的两条子路径之间是线身)"""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    shapes = []
    for d in _asset_paths(CARD_FRAME_ASSET)[:CARD_FRAME_BIG]:
        g = None
        for r in _rings(d):
            p = Polygon(r).buffer(0)
            g = p if g is None else g.symmetric_difference(p)
        shapes.append(g)
    return unary_union(shapes)


def card_frame(part, color="#c9a548", weight=0.0):
    """part = tl / tr / bl / br(角，原图 U × U) 或 top / bottom / left / right(两角之间的中段，主题里拉长，preserveAspectRatio none)。
    weight：线条加粗(原图单位；角 = 同色描边，边 = 每道线上下各加 weight / 2)，原图缩到 24px 时细线只有 0.1~0.3px"""
    src = (FLOURISH_SRC / f"{CARD_FRAME_ASSET}.svg").read_text(encoding="utf-8")
    W, H = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', src).groups())
    U = CARD_FRAME_U
    x, y, w, h = {"tl": (0, 0, U, U), "tr": (W - U, 0, U, U), "bl": (0, H - U, U, U), "br": (W - U, H - U, U, U),
                  "top": (U, 0, W - 2 * U, U), "bottom": (U, H - U, W - 2 * U, U),
                  "left": (0, U, U, H - 2 * U), "right": (W - U, U, U, H - 2 * U)}[part]
    from shapely.geometry import LineString, box
    big = _card_frame_big()
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    if part in ("top", "bottom", "left", "right"):
        horiz = part in ("top", "bottom")
        mid = (x + w / 2) if horiz else (y + h / 2)
        cut = LineString([(mid, y), (mid, y + h)] if horiz else [(x, mid), (x + w, mid)])
        seg = big.intersection(cut)
        bands = sorted((min(c) - weight / 2, max(c) + weight / 2) for g in getattr(seg, "geoms", [seg]) if not g.is_empty
                       for c in [[pt[1 if horiz else 0] for pt in g.coords]])
        rects = "".join(f'<rect x="{f(x)}" y="{f(a)}" width="{f(w)}" height="{f(b - a)}"/>' if horiz else
                        f'<rect x="{f(a)}" y="{f(y)}" width="{f(b - a)}" height="{f(h)}"/>' for a, b in bands)
        return (f'<svg {SVG} viewBox="{x:g} {y:g} {w:g} {h:g}" preserveAspectRatio="none"><g fill="{color}">'
                + rects + "</g></svg>")
    clip = big.intersection(box(x - 1, y - 1, x + w + 1, y + h + 1)).simplify(.1)
    ring = lambda cs: "M" + "L".join(f"{f(a)} {f(b)}" for a, b in list(cs)[:-1]) + "Z"
    polys = getattr(clip, "geoms", [clip])
    body = '<path fill-rule="evenodd" d="' + "".join(ring(p.exterior.coords) + "".join(ring(i.coords) for i in p.interiors)
                                                   for p in polys if p.geom_type == "Polygon") + '"/>'
    hit = lambda b: b[2] > x - 1 and b[0] < x + w + 1 and b[3] > y - 1 and b[1] < y + h + 1
    for d in _asset_paths(CARD_FRAME_ASSET)[CARD_FRAME_BIG:]:
        xs, ys = zip(*[pt for r in _rings(d, 4) for pt in r])
        if hit((min(xs), min(ys), max(xs), max(ys))):
            body += f'<path d="{d}"/>'
    stroke = f' stroke="{color}" stroke-width="{weight:g}" stroke-linejoin="round"' if weight else ""
    return (f'<svg {SVG} viewBox="{x:g} {y:g} {w:g} {h:g}" preserveAspectRatio="none"><g fill="{color}"{stroke}>'
            + body + "</g></svg>")


# ---- 图片外框(第四十六版，外框二稿 D、宽度用二稿 C1 的)：书签卡片花边整副缩小套在图外，框里不铺底(用户：不要一圈白边) ----
IMG_FRAME_E = 14.6                        # 图片边到外框外缘(px) = 二稿 C1 哥特窗棂的版面宽度
IMG_FRAME_C = 32 * IMG_FRAME_E / 20.5     # 角花大小：二稿 D 是角 32px、图边 20.5px(角花最深处 0.568 C 再让 2.3px)，整副等比缩小
IMG_FRAME_W = 0.5                         # 线条加粗(原图单位)：缩到 22.8px 后不加粗太淡太虚；1.5(初版)双线糊成一条 ~2.5px 金带，
                                          # 比分割线、H2 底线显重(用户：颜色好像有点深)；试过 0.75，用户定 0.5
IMG_SHADOW = ((1, 1, .10), (4, 5, .14))   # 图片投影：(下移, 模糊 σ, 不透明度)，颜色 = --ba-shadow


def image_frame(e=IMG_FRAME_E, C=IMG_FRAME_C, color="#c9a548", weight=IMG_FRAME_W):
    """→ (svg, 切片)：border-image 九宫格，1 单位 = 1 CSS px。四角 = card_frame 的角(C × C)，四边中段拉长。
    图片投影画在 SVG 里、贴着图边(纸底没有底色，box-shadow 会投出一个空盒子的影子)，被图盖住的部分看不见。
    切片 = 图边 + 投影下移 + 3σ：投影的圆角那段要整个落在角块里，否则四边中段拉伸时会把角上的渐隐拉长；
    角花外面多切进角块的那截是四边的直线，拉不坏"""
    Cs = math.ceil(e + max(dy + 3 * s for dy, s, _ in IMG_SHADOW))
    S = 2 * Cs + 20
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    geo = {"tl": (0, 0, C, C), "tr": (S - C, 0, C, C), "bl": (0, S - C, C, C), "br": (S - C, S - C, C, C),
           "top": (C, 0, S - 2 * C, C), "bottom": (C, S - C, S - 2 * C, C), "left": (0, C, C, S - 2 * C), "right": (S - C, C, C, S - 2 * C)}
    body = "".join(re.sub(r"^<svg ", f'<svg x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" ', card_frame(p, color, weight))
                   for p, (x, y, w, h) in geo.items())
    # 投影只留图外那圈：角块、边块伸进图里 Cs - e，透明底的 PNG 会透出图边一圈暗带
    sh = (f'<clipPath id="pc"><path clip-rule="evenodd" d="M0,0H{S}V{S}H0Z M{f(e)},{f(e)}V{f(S - e)}H{f(S - e)}V{f(e)}Z"/></clipPath><g clip-path="url(#pc)">'
          + "".join(f'<filter id="ps{i}" filterUnits="userSpaceOnUse" x="0" y="0" width="{S}" height="{S}"><feGaussianBlur stdDeviation="{s:g}"/></filter>'
                    f'<rect x="{f(e)}" y="{f(e + dy)}" width="{f(S - 2 * e)}" height="{f(S - 2 * e)}" fill="rgba(43,29,22,{a:g})" filter="url(#ps{i})"/>'
                    for i, (dy, s, a) in enumerate(IMG_SHADOW)) + "</g>")
    return f'<svg {SVG} width="{S}" height="{S}" viewBox="0 0 {S} {S}">{sh}{body}</svg>', Cs


# ---- 图片样式「印痕毛边」(第四十六版，晕边样稿 V3；同永夜「夜色晕边」的日间版)：不加框，四边按噪点颗粒渐隐进纸 ----
# 二稿(用户：太生硬、颗粒有点粗，要过渡柔和)：样稿 S1「细颗粒」——圈宽不变，颗粒细一半、边上带半透明过渡，留着印章毛边的味道
# (先装过 S3「平滑细砂」：圈 36、锐度 1.15、颗粒 2.5，用户看过实机改选 S1)
IMG_GRAIN_I = 24                        # 渐隐那圈的宽(px)
IMG_GRAIN_D = 20                        # 其中外侧 d px 是 ramp(最外 1px 全透，再 0 → 1)，里面 I - d 实心
IMG_GRAIN = (2.5, 4, .9, 1, 11)         # 颗粒：(锐度 S, 颗粒强度 G, 噪点频率, 八度, 种子)


def _grain_filter(fid, S, Ge, freq, octaves, seed):
    """ramp(SourceGraphic 的 alpha)+ 噪点 n → alpha = ramp + G·ramp(1 - ramp)·(n - .5)，再按锐度 S 拉对比
    (S = 1 完全平滑，越大越像印痕)。ramp = 0 / 1 两端噪点项为 0：外缘全透、里面实心，颗粒只扰动渐隐中段。
    一稿 alpha = K (1.3 ramp + n - 1.1)、K = 7 把每个像素阈值化成非全显即全透，看着生硬。
    滤镜链：u = ramp - ramp²(SourceGraphic 自乘)；v = .5 + G·u·(n - .5)(中间结果会被截到 [0, 1]，所以先加 .5、G 封顶 4，
    多出的倍数 M 放到下一步)；w = M (v - .5) + ramp；feFuncA 线性拉对比"""
    G = min(4.0, Ge)
    M = Ge / G
    return (f'<filter id="{fid}" filterUnits="objectBoundingBox" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{freq:g}" numOctaves="{octaves}" seed="{seed}" result="t"/>'
            f'<feColorMatrix in="t" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0" result="n"/>'
            f'<feComposite in="SourceGraphic" in2="SourceGraphic" operator="arithmetic" k1="-1" k2="1" k3="0" k4="0" result="u"/>'
            f'<feComposite in="u" in2="n" operator="arithmetic" k1="{G:g}" k2="{-G / 2:g}" k3="0" k4="0.5" result="v"/>'
            f'<feComposite in="v" in2="SourceGraphic" operator="arithmetic" k1="0" k2="{M:g}" k3="1" k4="{-M / 2:g}" result="w"/>'
            f'<feComponentTransfer in="w"><feFuncA type="linear" slope="{S:g}" intercept="{0.5 - 0.5 * S:g}"/></feComponentTransfer></filter>')


def _grain_axis(vertical, I, d, grain):
    """一个方向的遮罩(没有 viewBox，按遮罩尺寸 1:1 渲染，颗粒不随图片大小拉伸)：两侧各一条 I px 的渐隐条 + 中间实心。
    远侧那条用 <svg x="100%" overflow="visible"> 贴到右 / 下边；中间实心用 SVG mask 挖掉两侧 d px，
    只和渐隐条已经实心的 [d, I] 段重叠(两层半透明叠在一起会比单层实，显出一道暗线)"""
    S, Ge, freq, octaves, seed = grain
    a, z = d / I, 1 / I
    v = lambda x, y, w, h: (f'x="{y}" y="{x}" width="{h}" height="{w}"' if vertical else f'x="{x}" y="{y}" width="{w}" height="{h}"')
    nest = 'y="100%"' if vertical else 'x="100%"'
    x2, y2 = ("0", "1") if vertical else ("1", "0")
    g1 = (f'<linearGradient id="g1" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0" stop-opacity="0"/><stop offset="{z:.4f}" stop-opacity="0"/>'
          f'<stop offset="{a:.4f}"/><stop offset="1"/></linearGradient>')
    g2 = (f'<linearGradient id="g2" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0"/>'
          f'<stop offset="{1 - a:.4f}"/><stop offset="{1 - z:.4f}" stop-opacity="0"/><stop offset="1" stop-opacity="0"/></linearGradient>')
    mask = (f'<mask id="c" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"><rect width="100%" height="100%" fill="#fff"/>'
            f'<rect {v(0, 0, d, "100%")} fill="#000"/><svg {nest} overflow="visible"><rect {v(-d, 0, d, "100%")} fill="#000"/></svg></mask>')
    s0 = seed + (2 if vertical else 0)
    return (f'<svg {SVG}><defs>{g1}{g2}{_grain_filter("f1", S, Ge, freq, octaves, s0)}{_grain_filter("f2", S, Ge, freq, octaves, s0 + 1)}{mask}</defs>'
            f'<rect width="100%" height="100%" mask="url(#c)"/>'
            f'<rect {v(0, 0, I, "100%")} fill="url(#g1)" filter="url(#f1)"/>'
            f'<svg {nest} overflow="visible"><rect {v(-I, 0, I, "100%")} fill="url(#g2)" filter="url(#f2)"/></svg></svg>')


def image_grain(I=IMG_GRAIN_I, d=IMG_GRAIN_D, grain=IMG_GRAIN):
    """→ [(遮罩 SVG, 位置, 尺寸)]：两层 -webkit-mask，上层 Y(上下渐隐)与下层 X(左右渐隐)相乘(mask-composite: intersect)，
    四角 = X·Y 自然成软角；滤镜只挂在渐隐条上，不在整张图上算噪点。
    一稿拆成九块(四边 + 四角 + 中间)互相压住 2~3px：颗粒非全显即全透时看不出，柔和以后半透明叠加在四角附近显出横竖暗线；
    再早一版用九宫格遮罩(-webkit-mask-box-image)，切片之间的抗锯齿边透出细亮线。
    下层 X 上下各让 1px：Chromium 做 intersect 时只在上层遮罩取整后的范围里乘，图片边上那半个设备像素盖不到，
    那一排会只剩下层的值(实测漏 14%)"""
    return [(_grain_axis(True, I, d, grain), "0 0", "100% 100%"),
            (_grain_axis(False, I, d, grain), "0 1px", "100% calc(100% - 2px)")]


def callout_corner(asset="f1527_0", corner="tl", size=44):
    """一个角的剪影 SVG(黑色，CSS 当遮罩用、颜色 = callout 主色)。取原图左上角 U × U(FRAME_LINES)，宽高 = size px，
    其余三角镜像"""
    paths = _asset_paths(asset)
    idx = list(FRAME_CORNERS[asset])
    k = size / FRAME_LINES[asset]["U"]
    sx, sy = (-1 if corner[1] == "r" else 1), (-1 if corner[0] == "b" else 1)
    tf = f"translate({size if sx < 0 else 0} {size if sy < 0 else 0}) scale({sx * k:.5f} {sy * k:.5f})"
    return (f'<svg {SVG} width="{size}" height="{size}" viewBox="0 0 {size} {size}"><g transform="{tf}">'
            + "".join(f'<path d="{paths[i]}"/>' for i in idx) + "</g></svg>")


SEAL_WAX = (19, 15.5, 13.2)                  # 蜡封圆心、半径(封印视框单位)


def _wax_blob():
    """蜡封：近乎圆，只有几个很缓的起伏(引用块封印、功能栏蜡封共用)"""
    cx, cy, r = SEAL_WAX
    pts = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        rr = r * (1 + .045 * math.sin(3 * a + .7) + .03 * math.sin(5 * a + 2.3) + .015 * math.sin(7 * a + 1.1))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return _smooth_closed(pts)


def purity_seal(ink=None, wax="#a4413b", face="#8f3331", strip="#e4cf9f", strip2="#dcc390", line="#a98758",
                gap=1.1, knock=.8, strips=SEAL_STRIPS, taper=SEAL_TAPER, part="all", logo=None):
    """ink：印刷颗粒小图(tex_ink 渲染，128 一格)的 data URI；strips：左、右纸条中心线的四个控制点(相对蜡封圆心)；
    part：all 整枚 / wax 只画蜡 / strips 只画纸条(引文块里分两层：纸条一层被引文高度裁切，蜡一层盖在上面——
    两层合起来和整枚一模一样；不能用"整枚裁切 + 蜡"，蜡画两遍颗粒会互相填满、颜色变深)
    logo：战团徽抠空处填的颜色(夜间：抠空透出的纸是黑的，用户要徽记保持亮色)；None = 抠空透出纸色"""
    cx, cy, r = SEAL_WAX
    blob = _wax_blob()
    rows = [(.4, 1), (.52, .7), (.64, 1), (.76, .55)]
    # 两条纸条从蜡下面伸出来，各自缓缓弯开(左长右短)
    pt = lambda k: [(cx + dx, cy + dy) for dx, dy in strips[k]]
    s1, _, l1 = _seal_strip(*pt(0), 8, rows=rows[:3], w0=taper[0], t1=taper[1])
    s2, _, l2 = _seal_strip(*pt(1), 8, rows=rows, w0=taper[0], t1=taper[1])
    vb, parts = _logo_parts()
    s = 15 / vb[2]
    emblem = "".join(f'<path d="{parts[k]}"/>' for k in ("wing-l", "wing-r", "drop"))
    tf = f"translate({cx - 7.5:.2f} {cy - vb[3] * s / 2 + .3:.2f}) scale({s:.4f})"
    ri = r * .74
    mu = f'maskUnits="userSpaceOnUse" x="0" y="0" width="{SEAL_W}" height="{SEAL_H}"'
    full = f'<rect width="{SEAL_W}" height="{SEAL_H}" fill="#fff"/>'
    defs = (  # 左条在右条下面：右条外扩一圈空隙；两条都在蜡下面：蜡外扩一圈空隙
        f'<mask id="m1" {mu}>{full}<path d="{s2}" fill="#000" stroke="#000" stroke-width="{2 * gap}"/>'
        f'<path d="{blob}" fill="#000" stroke="#000" stroke-width="{2 * gap}"/></mask>'
        f'<mask id="m2" {mu}>{full}<path d="{blob}" fill="#000" stroke="#000" stroke-width="{2 * gap}"/></mask>'
        # 蜡：印面外一圈留白线 + 战团徽抠空
        f'<mask id="mw" {mu}>{full}<circle cx="{cx}" cy="{cy}" r="{ri:.2f}" fill="none" stroke="#000" stroke-width="{knock}"/>'
        f'<g fill="#000" transform="{tf}">{emblem}</g></mask>')
    body = ("" if part == "wax" else
            f'<g mask="url(#m1)"><path d="{s1}" fill="{strip2}"/>'
            f'<path d="{l1}" fill="none" stroke="{line}" stroke-width=".6" stroke-linecap="round"/></g>'
            f'<g mask="url(#m2)"><path d="{s2}" fill="{strip}"/>'
            f'<path d="{l2}" fill="none" stroke="{line}" stroke-width=".6" stroke-linecap="round"/></g>'
            ) + ("" if part == "strips" else
                 f'<g mask="url(#mw)"><path d="{blob}" fill="{wax}"/><circle cx="{cx}" cy="{cy}" r="{ri:.2f}" fill="{face}"/></g>'
                 + (f'<g fill="{logo}" transform="{tf}">{emblem}</g>' if logo else ""))
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="128" height="128">'
                 f'<image href="{ink}" width="128" height="128"/></pattern>'
                 f'<mask id="mk" {mu}><rect width="{SEAL_W}" height="{SEAL_H}" fill="url(#ip)"/></mask>')
        body = f'<g mask="url(#mk)">{body}</g>'
    return f'<svg {SVG} viewBox="0 0 {SEAL_W} {SEAL_H}"><defs>{defs}</defs>{body}</svg>'


# ---- 左侧功能栏「纯洁印记」(第四十八版，Style Settings「功能栏样式」默认)：顶上一枚战团徽蜡封(= 引用块封印的蜡那一层)，
# 下面垂一张纸条(纸 = 侧栏卡片的纸，CSS 铺)，图标排在纸条上 ----
RB_SEAL_D = 34          # 蜡封显示直径(px)；视框 = 蜡的外框：圆心 (19, 15.5)、半径 13.2 × 起伏 ≤ 1.09 → 30 单位见方
RB_STRIP_W = 24         # 纸条宽
RB_NOTCH = 5            # 下端燕尾缺口深


def ribbon_seal(ink=None, logo=None):
    """功能栏顶上的蜡封：purity_seal 的蜡那一层，视框裁到蜡，按 RB_SEAL_D 显示"""
    return purity_seal(ink=ink, part="wax", logo=logo).replace(f'viewBox="0 0 {SEAL_W} {SEAL_H}"',
                                                     f'width="{RB_SEAL_D}" height="{RB_SEAL_D}" viewBox="4 .5 30 30"')


def ribbon_strip(fill="#000"):
    """功能栏纸条的整张形状 = 蜡的轮廓 ∪ 纸条身子，宽 RB_SEAL_D、高 = 按钮组的高(CSS 里 100%)。
    不设 viewBox，1:1 按 px 画：身子从蜡的圆心往下、高 100%(多出的被图片底边裁掉)，燕尾缺口用 <svg y="100%" overflow="visible">
    钉在底边——图标多了只是身子变长，蜡和燕尾不变形(用户问过；7 / 16 个图标逐像素比过尾部，一致)。
    一稿身子 / 燕尾分两段遮罩拼，接缝有一道很淡的线。
    fill = #000 当纸条那层的遮罩；fill = 投影色 当投影那层(遮罩会把 filter 投影一起裁掉，投影只能另垫一层)"""
    D, W, N = RB_SEAL_D, RB_STRIP_W, RB_NOTCH
    bx = (D - W) / 2
    return (f'<svg {SVG} width="100%" height="100%"><defs>'
            f'<mask id="n" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"><rect width="100%" height="100%" fill="#fff"/>'
            f'<svg y="100%" overflow="visible"><path d="M{bx - 1:g},1 L{D / 2:g},{-N} L{bx + W + 1:g},1 Z" fill="#000"/></svg></mask></defs>'
            f'<rect x="{bx:g}" y="{D / 2:g}" width="{W}" height="100%" fill="{fill}" mask="url(#n)"/>'
            f'<path transform="scale({D / 30:.5f}) translate(-4 -.5)" d="{_wax_blob()}" fill="{fill}"/></svg>')


# ---- 新标签页：一整枚徽章 ----
# 第六版(用户：几个图案糊成一团；血滴应该在杯口前后的正中)：
#  · 圣杯改成自绘(原来的 game-icons 剪影分不出杯口前后沿)：杯口是一个椭圆，后沿 → 杯里 → 血滴 → 前沿和杯身，
#    血滴下半截落在杯口里、被前沿挡住；杯身正面嵌一组巴尔宝石，杯柄的节上三颗小宝石；
#  · 层次靠"抠空隙"分开：每一层在压在它上面的东西周围留出一圈 3.5 单位的空隙(遮罩)，再加上明度分层——
#    光环最淡(浅金)、双翼中金、圣杯金 + 深金细节、血滴圣血红
CREST_W, CREST_H = 360, 350


def _chalice(cx, ry_c):
    """圣杯各部件(画布坐标)。ry_c = 杯口椭圆中心 y。返回 dict：rim / mouth / lip / bowl / band / stem / knop / foot / foot_line"""
    o_rx, o_ry, i_rx, i_ry = 52, 12, 45, 8.5
    y = ry_c
    bowl = (f"M{cx - o_rx},{y} A{o_rx},{o_ry} 0 0 0 {cx + o_rx},{y} "
            f"C{cx + o_rx - 1},{y + 33} {cx + 34},{y + 62} {cx},{y + 66} C{cx - 34},{y + 62} {cx - o_rx + 1},{y + 33} {cx - o_rx},{y}Z")
    lip = (f"M{cx - o_rx},{y} A{o_rx},{o_ry} 0 0 0 {cx + o_rx},{y} L{cx + i_rx},{y - 1} "
           f"A{i_rx},{i_ry} 0 0 1 {cx - i_rx},{y - 1}Z")
    yb = y + 66
    stem = f"M{cx - 6},{yb - 3} L{cx + 6},{yb - 3} L{cx + 5},{yb + 10} L{cx - 5},{yb + 10}Z"
    yk = yb + 17
    foot = (f"M{cx - 5},{yk + 7} C{cx - 5},{yk + 22} {cx - 9},{yk + 37} {cx - 22},{yk + 52} "
            f"C{cx - 30},{yk + 60} {cx - 42},{yk + 63} {cx - 46},{yk + 68} A46,8.5 0 0 0 {cx + 46},{yk + 68} "
            f"C{cx + 42},{yk + 63} {cx + 30},{yk + 60} {cx + 22},{yk + 52} C{cx + 9},{yk + 37} {cx + 5},{yk + 22} {cx + 5},{yk + 7}Z")
    # 节(knop)：第七版(用户：节上三颗小点很突兀)去掉小宝石，改成瓜棱形的节——几道经线把它分成一瓣瓣，上下各一道细颈圈
    gad = " ".join(f"M{cx},{yk - 9} A{abs(x):g},9 0 0 {1 if x > 0 else 0} {cx},{yk + 9}" if x else f"M{cx},{yk - 9} V{yk + 9}"
                   for x in (-10.5, -5.2, 0, 5.2, 10.5))
    return dict(
        knop_lines=f'<path d="{gad}" fill="none"/>',
        collars="".join(f'<ellipse cx="{cx}" cy="{yk + dy}" rx="7.2" ry="2.1"/>' for dy in (-8.6, 8.6)),
        rim=f'<ellipse cx="{cx}" cy="{y}" rx="{o_rx}" ry="{o_ry}"/>',
        mouth=f'<ellipse cx="{cx}" cy="{y - 1}" rx="{i_rx}" ry="{i_ry}"/>',
        lip=f'<path d="{lip}"/>', bowl=f'<path d="{bowl}"/>',
        front_arc=f'<path d="M{cx - o_rx},{y} A{o_rx},{o_ry} 0 0 0 {cx + o_rx},{y}"/>',
        band=f'<path d="M{cx - 50},{y + 15} C{cx - 25},{y + 29} {cx + 25},{y + 29} {cx + 50},{y + 15}" fill="none"/>',
        stem=f'<path d="{stem}"/>', knop=f'<ellipse cx="{cx}" cy="{yk}" rx="15" ry="9"/>',
        foot=f'<path d="{foot}"/>',
        foot_line=f'<path d="M{cx - 40},{yk + 64} C{cx - 20},{yk + 72} {cx + 20},{yk + 72} {cx + 40},{yk + 64}" fill="none"/>',
        knop_y=yk, bowl_bottom=yb)


# ---- 新标签页四个按钮的「哥特窗」外框(第四十五版，用户：原版胶囊外框换掉，两头是哥特花窗那种尖头、尖头里要有玫瑰窗；
# 比过金线双框 / 燕尾签条 / 印章框 / 标签页式 / 素材分隔花饰 / 燕尾横幅 / 带台阶的尖头 / B‴双(各道线独立套着)…… 定 E2，
# preview/新标签页按钮/外框10/)。花窗本来就是圆规作图，素材库里也没有窗棂，这里按几何精确构造。
# 「石条」画法：每道双线 = 一条带(外框带、竖梁带、圆窗环、四叶带、中心小环)，shapely 求并集，只画并集的轮廓——外缘 = 外线、
# 窗洞的边 = 内线；相切的带在切点处融成一体，没有交叉(真实窗棂线描图的画法)。
# 单位 CSS px，一个按钮一张 SVG(不设 viewBox、宽高 100%)：左端画好用 clipPath 截在竖梁右边一点，右端放进 <svg x="100%"> 里镜像；
# 中段上下线从截口画到 100% 外、右端那截用遮罩抹掉——一张矢量图，没有拼接缝。CSS 当 mask-image 用(颜色跟原版胶囊的边框色走、悬停换色)。
NTB_H, NTB_YO, NTB_RATIO, NTB_APEX, NTB_GAP = 46, 1.5, 1.45, 2.0, 3.0


def _ntb_arc(c, r, a0, a1, n=64):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _ntb_d(pts, close=False):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + (" Z" if close else "")


def newtab_btn_frame(w_out=1.1, w_in=0.8, b_ring=1.8, b_q=1.8, rf_k=0.44, c_band=1.3, fill_a=0.0, band_a=1.0):
    """→ (外框遮罩 SVG, 悬停层遮罩 SVG(石条中间；fill_a > 0 时框里再铺淡底), 内容区左右各要让出的宽度, 高)。
    尖拱：圆心在起拱线(x = A 的竖线)上，上段弧圆心 (A, yo + r)、下段 (A, H - yo - r)；起拱点处切线水平，平行线顺着进拱，接口光滑。
      r = 跨度 × NTB_RATIO(1.45，比等边尖拱修长)。外框带 = 外线和内线(同圆心、半径减 gap)之间。
    竖梁带：和外框带同宽，以起拱线为中线(xL = A - gap/2、xR = A + gap/2)，和外框带丁字相接。
    圆窗环(细一档，b_ring；用户：圆窗、四叶的双线要比外框细)：内缘同时切两段内拱和竖梁左线，
      Ri = (ri² - k² - δ²) / (2 (ri + δ))，δ = gap/2；环往外长 b_ring——切点附近被更宽的外框带 / 竖梁带吞进去，从带里出来处融合，环洞保持整圆。
    四叶带(b_q)：四个等圆外缘切环外缘、一叶朝尖顶(+ 字)，叶带和环带在切点重合，叶洞恰好切环内缘；中间填满(不要菱形)，往里缩 b_q 成叶洞。
    中心细双环(c_band)：内圈和四叶外缘四个圆挤出的菱形空隙一样大(用户：圆洞要和四个圆自己挤出来的差不多大)。
    文字区在远端用一道竖带封上成为窗洞(否则它和外面连通，竖梁右线会被当成外线画粗)"""
    from shapely.geometry import MultiPolygon, Point, Polygon, box
    from shapely.ops import unary_union
    H, yo, gap = NTB_H, NTB_YO, NTB_GAP
    s = H - 2 * yo
    r = s * NTB_RATIO
    k = r - s / 2                                        # 弧心到中线的竖直距离
    A = NTB_APEX + math.sqrt(r * r - k * k)              # 起拱线 x
    cy = H / 2
    ct, cb = (A, yo + r), (A, H - yo - r)
    ang = lambda c, p: math.atan2(p[1] - c[1], p[0] - c[0])

    def arch(rr):
        """半径 rr(同圆心)的尖拱：上起拱点 → 尖顶 → 下起拱点"""
        ax = A - math.sqrt(rr * rr - k * k)
        top, bot = (A, cy - (rr - k)), (A, cy + (rr - k))
        return _ntb_arc(ct, rr, ang(ct, top), ang(ct, (ax, cy))) + _ntb_arc(cb, rr, ang(cb, (ax, cy)), ang(cb, bot))[1:]

    ri = r - gap
    yi = cy - (ri - k)                                   # 内线(上)
    d = gap / 2
    xL, xR = A - d, A + d
    XF = A + 300
    outer = Polygon([(XF, yo)] + arch(r) + [(XF, H - yo)])
    inner = Polygon([(XF, yi)] + arch(ri) + [(XF, H - yi)])
    disk = lambda c, rad: Point(c).buffer(rad, 256)
    bands = [outer.difference(inner), box(xL, yo, xR, H - yo).intersection(outer), box(XF - 2, yo, XF, H - yo)]
    Ri = (ri * ri - k * k - d * d) / (2 * (ri + d))
    Ro = Ri + b_ring
    c = (xL - Ri, cy)
    bands.append(disk(c, Ro).difference(disk(c, Ri)))
    rf = Ro * rf_k
    cr = Ro - rf
    Q = unary_union([disk((c[0] + cr * math.cos(math.pi / 2 * i), c[1] + cr * math.sin(math.pi / 2 * i)), rf) for i in range(4)])
    Qf = Polygon(Q.exterior.coords)
    bands.append(Qf.difference(Qf.buffer(-b_q, 128)))
    hr = cr * math.cos(math.pi / 4) - math.sqrt(rf * rf - (cr * math.sin(math.pi / 4)) ** 2)
    bands.append(disk(c, hr + c_band).difference(disk(c, hr)))
    # 圆按 256 段离散、并集后点很密：按 0.02px 化简(远小于一个物理像素，看不出)，SVG 从约 100KB 降下来
    U = unary_union(bands).intersection(outer).simplify(0.02, preserve_topology=True)
    polys = list(U.geoms) if isinstance(U, MultiPolygon) else [U]
    main = max(polys, key=lambda p: p.area)
    lines = [(list(main.exterior.coords), w_out)]
    for p in polys:
        if p is not main:
            lines.append((list(p.exterior.coords), w_in))
        lines += [(list(h.coords), w_in) for h in p.interiors]
    Xc = xR + 4                                          # 端头截口
    cap = "".join(f'<path d="{_ntb_d(pts, True)}" fill="none" stroke="#000" stroke-width="{w}" stroke-linejoin="round"/>' for pts, w in lines)
    mask = lambda i, x: (f'<mask id="{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"><rect width="100%" height="100%" fill="#fff"/>'
                         f'<svg x="100%" overflow="visible"><rect x="{-x:.2f}" y="0" width="{x + 10:.2f}" height="{H}" fill="#000"/></svg></mask>')
    mid = "".join(f'<rect x="{Xc - 0.6:.2f}" y="{y - w / 2:.2f}" width="100%" height="{w}"/>'
                  for y, w in ((yo, w_out), (H - yo, w_out), (yi, w_in), (H - yi, w_in)))
    frame = (f'<svg {SVG} width="100%" height="100%"><defs><clipPath id="k"><rect x="-10" y="-10" width="{Xc + 10:.2f}" height="{H + 20}"/></clipPath>'
             f'<g id="c" clip-path="url(#k)">{cap}</g>{mask("m", Xc)}</defs>'
             f'<g mask="url(#m)">{mid}</g><use href="#c"/><svg x="100%" overflow="visible"><use href="#c" transform="scale(-1 1)"/></svg></svg>')
    # 悬停层(用户：Hover 时给双线中间上一层更深的颜色；比过只铺细双线 50% / 80% 和连外框一起铺，定连外框 H3；
    # 颜色比过主题金 / 缎带色，定 R3 缎带正面色，双线以外的地方悬停不改色 → 默认 fill_a = 0、band_a = 1)：
    # 一层 mask，CSS 给颜色、整层淡入——所有石条(外框带、竖梁带、圆窗环、四叶带、中心小环)中间铺 band_a，像整块窗棂亮起来；
    # fill_a > 0 时框里(剪影)再铺一层淡底
    sil = [(A + 1, yo)] + arch(r) + [(A + 1, H - yo)]
    stone = U.intersection(box(-10, -10, Xc, H + 10))
    stone_d = " ".join(_ntb_d(list(ring.coords), True) for p in (list(stone.geoms) if isinstance(stone, MultiPolygon) else [stone])
                       for ring in [p.exterior, *p.interiors])
    sil_g = (f'<g fill-opacity="{fill_a}"><rect x="{A:.2f}" y="{yo}" width="100%" height="{H - 2 * yo}" mask="url(#mo)"/><use href="#s"/>'
             f'<svg x="100%" overflow="visible"><use href="#s" transform="scale(-1 1)"/></svg></g>') if fill_a else ""
    fill = (f'<svg {SVG} width="100%" height="100%"><defs><path id="s" d="{_ntb_d(sil, True)}"/><path id="b" fill-rule="evenodd" d="{stone_d}"/>'
            f'{mask("mo", A + 0.5)}{mask("mb", Xc)}</defs>{sil_g}'
            f'<g fill-opacity="{band_a}"><use href="#b"/><svg x="100%" overflow="visible"><use href="#b" transform="scale(-1 1)"/></svg>'
            f'<g mask="url(#mb)"><rect x="{Xc - 0.6:.2f}" y="{yo}" width="100%" height="{yi - yo:.2f}"/>'
            f'<rect x="{Xc - 0.6:.2f}" y="{H - yi:.2f}" width="100%" height="{yi - yo:.2f}"/></g></g></svg>')
    return frame, fill, xR + 6, H


def newtab_crest(halo_r=70, wing_h=150, drop_h=104, gap=3.5, ink=None, ink_dark=None, knock=1.7, shade="#b08a34",
                 wear=None, drop_hi="#e04a46", drop_mid="#bd3a39", drop_low="#a8423d", drop_clean=.4, halo=None):
    """ink：印刷颗粒(tex_ink 渲染的灰度图 data URI)，整枚徽章用它做亮度遮罩；ink_dark：深色墨粒(tex_ink_dark，透明底)，
    只叠在有墨的地方(alpha 遮罩 = 徽章自己)。
    wear：磨损叠加图(stamp.wear_overlay，低分辨率，拉满整枚徽章)，在亮度遮罩里盖在颗粒上面——墨色饱满的地方
    把颗粒压淡，磨薄的地方颗粒照显(第九版，用户：颗粒太明显太粗糙，要减淡，做出柔和的区域磨损过渡)。
    第八版(用户：要像参考图那种套色印章——色块平涂、颜色之间留一道纸色细线，不要深色实线描边)：
    杯身上原来的深金描线(腰线、节的轮廓和瓜棱、颈圈、杯脚线、杯口前沿)全改成"留白线"(knock 宽，遮罩抠出来、透出纸色)；
    巴尔宝石周围、血滴和杯口接触的地方也各留一圈空隙"""
    W, H = CREST_W, CREST_H
    cx = W / 2
    halo_cy = 4 + halo_r * 2.1
    drop_top = halo_cy - halo_r + 4
    ry_c = drop_top + drop_h - 3             # 血滴底端落在杯口正中(前后沿之间)，圆底露在杯口里，前沿只挡住最底下一点
    c = _chalice(cx, ry_c)
    vb, parts = _logo_parts()
    pale = ('<linearGradient id="hp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eddaa8"/>'
            '<stop offset="1" stop-color="#e0c88e"/></linearGradient>')
    # 血滴(第七版，用户：太暗沉、加一点微妙的渐变)：亮一档的圣血红。
    # 第九版(用户：渐变更明显一点，加一点缎带那样饱和度低的红)：斜向线性渐变——左上鲜红 → 右下降饱和的砖红，
    # 和杯身右侧的深金第二套色同一个光向；比过径向(像立体高光，不像套色)和竖向。
    # 四稿(用户：太脏太灰)：右下端原来 #8a2f2b 又暗又偏褐，叠上颗粒发灰——改成亮一档、干净的砖红 drop_low
    drop_grad = ('<linearGradient id="db" x1=".2" y1=".1" x2=".8" y2=".95">'
                 f'<stop offset="0" stop-color="{drop_hi}"/><stop offset=".35" stop-color="#cd2f34"/>'
                 f'<stop offset=".72" stop-color="{drop_mid}"/><stop offset="1" stop-color="{drop_low}"/></linearGradient>')
    defs = (gold_defs("g") + gold_defs("cg") + drop_grad + gem_defs("b") + pale
            + '<linearGradient id="in" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6b4a14"/>'
              '<stop offset="1" stop-color="#94702a"/></linearGradient>')
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="256" height="256">'
                 f'<image href="{ink}" width="256" height="256"/></pattern>')
    if ink_dark:
        defs += (f'<pattern id="dp" patternUnits="userSpaceOnUse" width="256" height="256" x="97" y="61">'
                 f'<image href="{ink_dark}" width="256" height="256"/></pattern>'
                 f'<mask id="ma" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}" style="mask-type:alpha">'
                 '<use href="#a1"/><use href="#a3"/></mask>')     # 深色墨粒不撒在血滴上(四稿：血滴太脏)
    # 双翼：翼根(外框内侧下角 366,586)贴在杯身两侧上部，压在杯后面
    ws = wing_h / 582.2
    root_y, root_dx = ry_c + 26, 36
    wl_tf = f"translate({cx - root_dx - 366 * ws:.2f} {root_y - 586 * ws:.2f}) scale({ws:.4f})"
    wr_tf = f"translate({cx + root_dx + 366 * ws:.2f} {root_y - 586 * ws:.2f}) scale({-ws:.4f} {ws:.4f})"
    wing = parts["wing-l"]
    ds = drop_h / 472.2
    d_tf = f"translate({cx - 450.2 * ds:.2f} {drop_top - 275 * ds:.2f}) scale({ds:.4f})"
    drop = parts["drop"]
    if ink:
        # 颗粒 × 磨损的亮度遮罩；血滴上再盖一层半透明白，漏白颗粒减 drop_clean(四稿：红底上漏出的纸色发灰发粉，显脏)
        defs += (f'<mask id="mk" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                 f'<rect width="{W}" height="{H}" fill="url(#ip)"/>'
                 + (f'<image href="{wear}" width="{W}" height="{H}" preserveAspectRatio="none"/>' if wear else "")
                 + f'<path d="{drop}" transform="{d_tf}" fill="#fff" opacity="{drop_clean}"/></mask>')

    def sil(cup=True, drp=True, wings=False):
        """遮罩里抠掉的剪影(黑，外扩 gap)"""
        k = f'fill="#000" stroke="#000" stroke-width="{gap * 2}" stroke-linejoin="round"'
        out = ""
        if cup:
            out += f'<g {k}>{c["rim"]}{c["bowl"]}{c["stem"]}{c["knop"]}{c["foot"]}</g>'
        if drp:
            out += f'<path d="{drop}" transform="{d_tf}" fill="#000" stroke="#000" stroke-width="{gap * 2 / ds:.1f}"/>'
        if wings:
            for tf in (wl_tf, wr_tf):
                out += (f'<path d="{wing}" transform="{tf}" fill="#000" stroke="#000" stroke-width="{gap * 2 / ws:.1f}" '
                        'stroke-linejoin="round"/>')
        return out

    mu = f'maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"'
    full = f'<rect width="{W}" height="{H}" fill="#fff"/>'
    # 光环在杯身以下渐隐(杯脚周围不再有一截截零碎的光芒)
    fade = (f'<linearGradient id="hf" gradientUnits="userSpaceOnUse" x1="0" y1="{ry_c + 25:.0f}" x2="0" y2="{ry_c + 105:.0f}">'
            '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>')
    defs += (f'{fade}<mask id="mh" {mu}><rect width="{W}" height="{H}" fill="url(#hf)"/>{sil(wings=True)}</mask>'
             f'<mask id="mw" {mu}>{full}{sil()}</mask>'
             f'<clipPath id="cb">{c["bowl"]}</clipPath>')
    # 光环(第七版：大小光芒都是 S 形火焰；第八版：全朝一个旋转方向，末端卷回收到六七十度——第七版卷回 160° 太多)
    # halo：换一种光环(同样的位置、光芒参数，函数自带配色)——夜间新标签页的「黑日」(dark.eclipse_halo，第五十二版)
    flame = (-.45, 1.1, -.35, .85)
    if halo:
        halo = halo(cx, halo_cy, halo_r, n=20, wavy_len=1.35, straight_len=.8, flame=flame)
    else:
        halo = sun_halo_body(cx, halo_cy, halo_r, fill="url(#hp)", n=20, ring=.1, wavy_len=1.35, straight_len=.8, flame=flame)
    wings = (f'<g fill="url(#g)"><path d="{wing}" transform="{wl_tf}"/><path d="{wing}" transform="{wr_tf}"/></g>')
    deep = C_GOLD_DEEP
    dg = 2.2                                 # 血滴 / 宝石周围的空隙
    gem_top, gem_h = ry_c + 21, 38
    gs = gem_h / GEM_BOX[3]
    pad = 2 * dg / gs                        # 换算到宝石组自己的单位
    mount_sil = baal_cluster_at(cx, gem_top, gem_h, mount="#000", gem="#000", slit="#000", glint=False, grow=pad)
    kn = f'fill="none" stroke="#000" stroke-width="{knock}"'
    defs += (f'<clipPath id="ck">{c["knop"]}</clipPath>'
             # 杯身前面的留白线
             f'<mask id="mf" {mu}>{full}<g clip-path="url(#cb)" {kn}>{c["band"]}</g>'
             f'<g {kn}>{c["front_arc"]}{c["foot_line"]}{c["knop"]}{c["collars"]}</g>'
             f'<g clip-path="url(#ck)" fill="none" stroke="#000" stroke-width="{knock * .7:.2f}">{c["knop_lines"]}</g>'
             f'{mount_sil}</mask>'
             # 血滴底部被杯口前沿挡住的地方 / 杯口后沿和杯里在血滴周围各留一圈空隙
             f'<mask id="md" {mu}>{full}<g fill="#000" stroke="#000" stroke-width="{2 * dg}" stroke-linejoin="round">'
             f'{c["lip"]}{c["bowl"]}</g></mask>'
             f'<mask id="mb" {mu}>{full}<path d="{drop}" transform="{d_tf}" fill="#000" stroke="#000" '
             f'stroke-width="{2 * dg / ds:.1f}"/></mask>')
    cup_back = (f'<g mask="url(#mb)"><g fill="url(#cg)">{c["rim"]}</g><g fill="url(#in)">{c["mouth"]}</g></g>')
    # 第二套色：杯身、杯脚右侧压一道深一档的金(整块平涂，像套印的第二版)——形状 = 部件减去往左上挪一点的自己
    defs += (f'<mask id="sb" {mu}>{full}<g fill="#000" transform="translate(-9 -6)">{c["bowl"]}</g></mask>'
             f'<mask id="sf" {mu}>{full}<g fill="#000" transform="translate(-4.5 -2)">{c["stem"]}{c["foot"]}</g></mask>')
    cup_front = (f'<g mask="url(#mf)"><g fill="url(#cg)">{c["bowl"]}{c["stem"]}{c["foot"]}</g>'
                 f'<g fill="{shade}"><g mask="url(#sb)">{c["bowl"]}</g><g mask="url(#sf)">{c["stem"]}{c["foot"]}</g></g>'
                 f'<g fill="#e3c97c">{c["lip"]}</g>'
                 f'<g fill="url(#cg)">{c["knop"]}{c["collars"]}</g></g>'
                 + baal_cluster_at(cx, gem_top, gem_h, mount=deep))
    art = (f'<g id="art"><g id="a1"><g mask="url(#mh)">{halo}</g><g mask="url(#mw)">{wings}</g>{cup_back}</g>'
           f'<g mask="url(#md)"><path d="{drop}" transform="{d_tf}" fill="url(#db)"/></g><g id="a3">{cup_front}</g></g>')
    body = art + (f'<rect width="{W}" height="{H}" fill="url(#dp)" mask="url(#ma)"/>' if ink_dark else "")
    if ink:
        body = f'<g mask="url(#mk)">{body}</g>'
    return f'<svg {SVG} viewBox="0 0 {W} {H}"><defs>{defs}</defs>{body}</svg>'


def inscription_banner(w=560):
    """新标签页题铭的卷轴横幅(定宽，和 H1 横幅同一画法)"""
    return banner(w, stretch=False)


def highlight_brush():
    """高亮的金色刷痕(第十九版，用户：高亮不明显，可以有渐变、质感)：一条两端收圆的色带，左右缎面渐变，
    feTurbulence + feDisplacementMap 把边缘揉毛。CSS 里拉伸到每段字的宽度(preserveAspectRatio none)，
    拉长后的噪声正好像横向的刷痕；上面再叠标签同款的磨损颗粒"""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 40" preserveAspectRatio="none">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e9bd4f"/>'
            '<stop offset=".5" stop-color="#f3d77c"/><stop offset="1" stop-color="#e3b347"/></linearGradient>'
            '<filter id="r" x="-5%" y="-20%" width="110%" height="140%">'
            '<feTurbulence type="fractalNoise" baseFrequency=".9 .25" numOctaves="2" seed="4"/>'
            '<feDisplacementMap in="SourceGraphic" scale="7"/></filter></defs>'
            '<path d="M6,9 C40,6 160,7 194,9 C199,15 199,27 194,32 C150,34 50,35 6,33 C1,27 1,15 6,9Z" '
            'fill="url(#g)" fill-opacity=".82" filter="url(#r)"/></svg>')


HL_CAP, HL_TILE = 18, 160                     # 高亮刷痕：两端笔头宽、中段宽(图里的单位，CSS 里 2 单位 = 1px)


def highlight_brush2(color=("#e9cd7a", "#f3e3a8"), opacity=.58, rough=4):
    """高亮的刷痕，给 CSS border-image 用的九宫格：左右 HL_CAP 宽是两端的笔头(固定宽度，不随文字长短变)，中间一段色带。
    第二十版：中段平铺(round)，颜色竖直渐变。第二十三版(用户：两端太圆了；渐变要左右，不要上下)：
    - 中段改成拉伸(stretch)，左右渐变贯穿整段字——落笔处(左)墨浓一点、收笔处(右)淡一点，像一笔刷过去；
      两端笔头分别是渐变两头的颜色。拉伸时中段毛边的起伏跟着拉长，长段的边缘更缓，不会出现重复花纹
    - 笔头从半椭圆改成圆角方头：竖直的端面 + 两个圆角，毛边再轻一点
    毛边只做竖直方向的位移(水平通道换成常数 .5)，整组一个不透明度(笔头和色带重叠处不叠深)"""
    W, H = 2 * HL_CAP + HL_TILE, 40
    x0, x1 = HL_CAP, HL_CAP + HL_TILE
    flt = (f'<filter id="r" filterUnits="userSpaceOnUse" x="{x0}" y="0" width="{HL_TILE}" height="{H}">'
           f'<feTurbulence type="fractalNoise" baseFrequency="{5 / HL_TILE:.4f} .22" numOctaves="2" seed="4"/>'
           '<feComponentTransfer><feFuncR type="linear" slope="0" intercept=".5"/></feComponentTransfer>'
           f'<feDisplacementMap in="SourceGraphic" scale="{rough}" xChannelSelector="R" yChannelSelector="G"/></filter>'
           f'<filter id="c" x="-10%" y="-20%" width="120%" height="140%">'
           '<feTurbulence type="fractalNoise" baseFrequency=".35 .2" numOctaves="2" seed="7"/>'
           f'<feDisplacementMap in="SourceGraphic" scale="{rough * .5}"/></filter>')
    band = f'<rect x="{x0 - 30}" y="9" width="{HL_TILE + 60}" height="23"/>'
    r = 6                                          # 笔头圆角
    left = f'M{x0 + 4},9 H{4 + r} Q3,9 3,{9 + r} V{32 - r} Q3,32 {4 + r},32 H{x0 + 4}Z'
    right = f'M{x1 - 4},9 H{W - 4 - r} Q{W - 3},9 {W - 3},{9 + r} V{32 - r} Q{W - 3},32 {W - 4 - r},32 H{x1 - 4}Z'
    grad = (f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x1}" y2="0">'
            f'<stop offset="0" stop-color="{color[0]}"/><stop offset="1" stop-color="{color[1]}"/></linearGradient>')
    return (f'<svg {SVG} width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{flt}{grad}</defs>'
            f'<g fill="url(#g)" opacity="{opacity}">'
            f'<g filter="url(#r)">{band}</g>'
            f'<path d="{left} {right}" filter="url(#c)"/></g></svg>')


SB_STYLE = "ribbon"                            # 滚动条滑块两头：brush 笔锋 / ribbon 燕尾绶带(第二十六版用户定缎带)
SB_CAP_LEN = {"brush": "min(36px, 50%)", "ribbon": "8px"}


def scrollbar_cap(end="top", color="#a32a35", alpha=.75, style=None):
    """滚动条滑块的一头。CSS 里拉伸到滑块宽 × SB_CAP_LEN(preserveAspectRatio none)；end = top / bottom / left / right
    - brush(第二十五版，用户在对比里选了「笔锋 B 更饱满」)：饱满的尖拱——先保持宽度、再外凸地收成尖，同时从 alpha 渐隐到 0。
      第二十三版是更瘦的尖拱(A)，颜色只有 45%(用户：常态太淡)
    - ribbon(第二十四版)：燕尾绶带的端头，V 形缺口(同标签)，平涂"""
    style = style or SB_STYLE
    if style == "ribbon":
        body = f'<path d="M0,0 L5,26 L10,0 L10,40 L0,40Z" fill="{color}" fill-opacity="{alpha}"/>'
        defs = ""
    else:
        defs = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
                f'<stop offset=".7" stop-color="{color}" stop-opacity="{alpha}"/><stop offset="1" stop-color="{color}" stop-opacity="{alpha}"/>'
                '</linearGradient></defs>')
        body = '<path d="M5,0 C7,4 10,10 10,24 L10,40 L0,40 L0,24 C0,10 3,4 5,0Z" fill="url(#g)"/>'
    tf = {"top": "", "bottom": "translate(0 40) scale(1 -1)",
          "left": "translate(0 10) rotate(-90)", "right": "translate(40 0) rotate(90)"}[end]
    vb = "0 0 10 40" if end in ("top", "bottom") else "0 0 40 10"
    return f'<svg {SVG} viewBox="{vb}" preserveAspectRatio="none">{defs}<g transform="{tf}">{body}</g></svg>'


# ---- 代码块(第二十七版：去掉 neumorphism，红头铭板 / 沉思者两套，Style Settings 切换) ----
MECH_SRC = Path(r"E:\AI工作\素材库\wh_icons\wh40k\Imperium\Adeptus Mechanicus [Imperium].svg")


def mechanicus(color):
    """机械教徽(素材库 wh_icons；GW 商标、同人用途，构建时读、素材文件不进仓库)。
    原图右半是实心半圆 + 齿轮、左半只有一圈齿，单独看像缺了半边：左半补一道同半径的半圆细线(第二十七版，用户)。
    viewBox 取补线后的外框(约正方形)"""
    src = MECH_SRC.read_text(encoding="utf-8")
    ds = re.findall(r'\sd="([^"]+)"', src)
    tf = re.search(r'<g[^>]*transform="([^"]+)"', src).group(1)
    ring_w, cx, cy, rr = 46, 332, 400, 400        # 右半实心半圆：竖边 x≈332、上下 0–800 → 圆心 (332, 400)、半径 400
    r = rr - ring_w / 2
    return (f'<svg {SVG} viewBox="{cx - rr - 2} -2 {rr + 736.6 - cx + 4} 804">'
            f'<g fill="{color}" transform="{tf}">' + "".join(f'<path d="{d}"/>' for d in ds) + '</g>'
            f'<path d="M{cx},{cy - r} A{r},{r} 0 0 0 {cx},{cy + r}" fill="none" stroke="{color}" stroke-width="{ring_w}"/></svg>')


AQUILA_SRC = Path(r"E:\AI工作\素材库\wh_icons\wh40k\Imperium\Imperium of Man 02 [Imperium, Aquila].svg")


def aquila():
    """帝国双头鹰(素材库 wh_icons「Imperium of Man 02」实心版；GW 商标、同人用途，构建时读、素材文件不进仓库)。
    锁定标签的图标用(第三十六版，用户从双头鹰 / 钉 / 剑 / 矛十个候选里选的)，只当遮罩用，不上色"""
    src = AQUILA_SRC.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    return f'<svg {SVG} viewBox="{vb}">' + "".join(f'<path d="{d}"/>' for d in re.findall(r'\sd="([^"]+)"', src)) + "</svg>"


def nav_wings(gap=-10):
    """侧栏各面板顶上的按钮行收起时留下的一对翅膀(第四十版，照永夜 nav_wings 的用法：只当遮罩，颜色由 CSS 铺)。
    用户比过六种(战团徽双翼 ± 血滴 / liberty / feathered / curly / 属性栏版画双翼)选 Lorc 的 curly-wing，
    要「左右反一下」：原图翼尖朝左上、卷草在右下，原图放左边、镜像放右边，卷草根部在中间相接、翼尖朝外；
    gap = 两片往中间挤多少(原图单位)：-10 两个卷草并排相切；一稿 -35 看着相接，放大看两个卷草叠在一起交错(用户发现)，0 中间露缝、像两片分开的。
    返回 (svg, 宽高比)；视框贴合剪影外框(展平 path 量)"""
    import chalice as CH
    d = gi_paths("curly-wing")[0]
    pts = [p for ring in CH._flatten(d) for p in ring]
    xs = [x - gap for x, _ in pts] + [1024 + gap - x for x, _ in pts]
    ys = [y for _, y in pts]
    pad = 4
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    svg = (f'<svg {SVG} viewBox="{x0:.1f} {y0:.1f} {x1 - x0:.1f} {y1 - y0:.1f}">'
           f'<path transform="translate({-gap} 0)" d="{d}"/><path transform="translate({1024 + gap} 0) scale(-1 1)" d="{d}"/></svg>')
    return svg, (x1 - x0) / (y1 - y0)


TAB_RIBBON_W, TAB_RIBBON_H, TAB_RIBBON_RISE = 22, 40, 2


def tab_ribbon():
    """侧栏「书签卡片」布局的当前标签 = 从卡片顶边垂下的一条红色书签丝带(第四十一版，用户比过战旗 / 书签丝带 / 纯洁封印 / 拱龛 / 挂盾，选丝带)。
    单位 = CSS px，22 × 40。顶边比卡片的纸高出 RISE = 4px(用户：书签顶部要突出外框一些)，燕尾末端 39.5、缺口顶 34；
    图标中心在图里 18.6(= 卡片内容顶下 14.6)，落在丝带顶到燕尾的正中。
    改过三稿：一稿顶边齐卡片、图标中心离丝带顶 22.6，用户：图标在书签上没有垂直居中；二稿顶边伸出 4px、下端也加长 4px(48 长)，
    用户：丝带太长，永夜的战旗短(约 39，图标中心离旗顶 21)，是图标离上边太远——标签整排上移 4px，丝带回到 40。
    第四十二版(用户：燕尾改盾形下摆，选 R1c；伸出外框少一点，像永夜的战旗)：下摆 = 哥特尖盾，两侧各一段半径 22 的圆弧
    (圆心在对边的同一高度)，从 20.45 处开始收、在 39.5 交成约 120° 的尖(preview/侧栏一级标签/丝带盾形下摆_二轮/：
    一稿弧线从 29 起太平，R1b 半径 16 偏钝)；伸出 RISE 4 → 2px(主题 --ba-rb-rise)。金线沿着轮廓往里 1.6px 绕过下摆。
    返回 (遮罩, 光泽)：遮罩 = 丝带剪影；光泽 = 横向明暗(两侧暗、偏左一道淡高光，像缎面) + 一道金线，叠在红底颗粒上面、同一个遮罩裁"""
    w, h, tip, r = TAB_RIBBON_W, TAB_RIBBON_H, 39.5, 22.0
    ys = tip - (r * r - (r - w / 2) ** 2) ** .5          # 圆弧起点
    edge = f"M0,0 V{ys:.2f} A{r:g},{r:g} 0 0 0 {w / 2:g},{tip} A{r:g},{r:g} 0 0 0 {w},{ys:.2f} V0"
    i = 1.6
    mask = f'<svg {SVG} width="{w}" height="{h}" viewBox="0 0 {w} {h}"><path d="{edge}Z"/></svg>'
    sheen = (f'<svg {SVG} width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>'
             f'<linearGradient id="s" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity=".16"/>'
             f'<stop offset=".35" stop-color="#fff" stop-opacity=".1"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="#000" stop-opacity=".2"/></linearGradient></defs>'
             f'<rect width="{w}" height="{h}" fill="url(#s)"/>'
             f'<path d="{edge}" transform="translate({i} {-i}) scale({(w - 2 * i) / w:.4f} 1)" fill="none" stroke="{GOLD_STOPS[0][1]}" '
             f'stroke-width=".6" opacity=".75" vector-effect="non-scaling-stroke"/></svg>')
    return mask, sheen


def _teardrop(cx, bottom, w, h):
    """水滴形(尖朝上)：圆底半径 w/2 落在 bottom，总高 h"""
    r = w / 2
    cy = bottom - r
    tip = cy - (h - r)
    return (f'M{cx:.2f},{tip:.2f} C{cx + r * .3:.2f},{tip + (cy - tip) * .45:.2f} {cx + r:.2f},{cy - r * .45:.2f} {cx + r:.2f},{cy:.2f} '
            f'A{r:.2f},{r:.2f} 0 0 1 {cx - r:.2f},{cy:.2f} C{cx - r:.2f},{cy - r * .45:.2f} {cx - r * .3:.2f},{tip + (cy - tip) * .45:.2f} {cx:.2f},{tip:.2f} Z')


COG_CANDLE_DRIPS = ((-1, 3.8), (1, 5.0), (-1, 3.0))     # 每根蜡烛顶上淌下来的一道蜡：(哪一侧, 长)


def cog_candles(body="#f4e6c9", flame="#f1d27f", heights=(7, 10.5, 5), w=5.2, gap=2.4, fw=3.6, fh=5.4, fgap=1.0,
                rt=1.7, rb=.9, tilt=1.2, drips=COG_CANDLE_DRIPS):
    """沉思者铭牌右端的一组蜡烛(第二十七版五轮，用户：蜡烛放进边框、周围留一圈空、矩形加圆角、头上画一点融化的蜡，
    火焰不要太橙太暗)：两种颜色平涂、不描边、没有颗粒和明暗——烛身奶白(同铭牌上的字)、火苗淡金；
    烛身是圆角矩形，烛口歪着化下去一点(一侧低 tilt)、正中烛芯周围凹一点，低的那一侧挂一道往下淌的蜡泪(凸出烛身、末端一颗小圆珠，
    剪影上看得出——太小的凸起在实际尺寸下只像缺口，比过)；
    火苗是水滴形，和烛身之间空一道缝(透出铭牌红)。返回 (svg, W, H)，图底 = 烛底"""
    n = len(heights)
    H = max(heights) + fgap + fh + .3
    pad = 1.4                                       # 蜡泪凸出烛身的余量
    W = n * w + (n - 1) * gap + 2 * pad
    out = ""
    for i, bh in enumerate(heights):
        cx = pad + i * (w + gap) + w / 2
        l, r, top, bot = cx - w / 2, cx + w / 2, H - bh, H
        side, ln = drips[i]
        # 化开的烛口：靠蜡泪那一侧低 tilt(歪着化下去)，正中烛芯周围再凹一点；高的那一侧留圆角，低的那一侧被漫出来的蜡盖住
        y_lo, y_hi = top + tilt, top
        yl, yr = (y_lo, y_hi) if side < 0 else (y_hi, y_lo)
        at = lambda x: yl + (yr - yl) * (x - l) / w
        dw, dd = w * .26, .8                        # 顶面凹下去的宽、深
        rl, rr = (.5, rt) if side < 0 else (rt, .5)
        yc = at(cx) + dd
        body_d = (f'M{l + rb:.2f},{bot:.2f} H{r - rb:.2f} Q{r:.2f},{bot:.2f} {r:.2f},{bot - rb:.2f} V{yr + rr:.2f} '
                  f'Q{r:.2f},{yr:.2f} {r - rr:.2f},{at(r - rr):.2f} L{cx + dw:.2f},{at(cx + dw):.2f} '
                  f'C{cx + dw * .45:.2f},{at(cx + dw * .45):.2f} {cx + dw * .35:.2f},{yc:.2f} {cx:.2f},{yc:.2f} '
                  f'C{cx - dw * .35:.2f},{yc:.2f} {cx - dw * .45:.2f},{at(cx - dw * .45):.2f} {cx - dw:.2f},{at(cx - dw):.2f} '
                  f'L{l + rl:.2f},{at(l + rl):.2f} Q{l:.2f},{yl:.2f} {l:.2f},{yl + rl:.2f} V{bot - rb:.2f} Q{l:.2f},{bot:.2f} {l + rb:.2f},{bot:.2f} Z')
        # 蜡泪：从低的那一侧烛口漫出来，贴着烛身往下淌、越往下越细，末端一颗小圆珠；凸出烛身约 1
        ln = min(ln, bh - tilt - 1.5)
        e, sg = (r, 1) if side > 0 else (l, -1)
        X = lambda dx: f"{e + sg * dx:.2f}"
        drip = (f'<path d="M{X(-1.4)},{y_lo:.2f} L{X(-.1)},{y_lo:.2f} C{X(.55)},{y_lo:.2f} {X(.85)},{y_lo + .6:.2f} {X(.8)},{y_lo + 1.4:.2f} '
                f'L{X(.55)},{y_lo + ln - 1.2:.2f} L{X(-.4)},{y_lo + ln - 1.2:.2f} L{X(-.4)},{y_lo + 1:.2f} L{X(-1.4)},{y_lo + 1:.2f} Z"/>'
                f'<circle cx="{X(.42)}" cy="{y_lo + ln - .8:.2f}" r=".78"/>')
        out += f'<path d="{body_d}"/>{drip}'
        out += f'<path d="{_teardrop(cx, at(cx) - fgap, fw, fh)}" fill="{flame}"/>'
    return f'<svg {SVG} width="{W:.2f}" height="{H:.2f}" viewBox="0 0 {W:.2f} {H:.2f}"><g fill="{body}">{out}</g></svg>', W, H


def rule_arm_fade(sh=15, length=40):
    """新标签页题铭中段两侧的花饰(第二十七版五轮，用户：末端的箭头突兀，换成渐变消失，像分割线那样)：
    f1090_1 左臂去掉外端箭头——「∞」卷草组 + 菱形 + 菱形外侧一段横线(length 显示 px)往外渐隐到 0。
    白色剪影(题铭把它当覆盖率，和字同一套墨)。返回 (svg, 显示宽, 显示高)，竖直中线 = 横线"""
    k = sh / 58.2
    paths = _asset_paths("f1090_1")
    lu = length / k
    x0, x1 = 80.0 - lu, 294.1                       # 80 = 菱形外端；294.1 = 卷草组内端(含小卷)的外沿
    y0, y1 = F1090_ARM_LINE
    vb_y, vb_h = F1090_LINE_Y - 33.4, 66.8
    svg = (f'<svg {SVG} viewBox="{x0 - 1:.1f} {vb_y:.1f} {x1 - x0 + 2:.1f} {vb_h}"><defs>'
           f'<linearGradient id="fd" gradientUnits="userSpaceOnUse" x1="{x0:.1f}" y1="0" x2="80" y2="0">'
           '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".75" stop-color="#fff"/></linearGradient>'
           '<clipPath id="cd" clipPathUnits="userSpaceOnUse"><rect x="79" y="0" width="300" height="64"/></clipPath></defs>'
           + "".join(f'<path d="{paths[i]}" fill="#fff"/>' for i in F1090_SCROLL["left"][0])
           + f'<path d="{paths[3]}" fill="#fff" clip-path="url(#cd)"/>'
           f'<rect x="{x0:.1f}" y="{y0}" width="{80.5 - x0:.1f}" height="{y1 - y0:.2f}" fill="url(#fd)"/></svg>')
    return svg, (x1 - x0 + 2) * k, vb_h * k


def ext_arrow():
    """外部链接后的金色小箭头(↗)"""
    return (f'<svg {SVG} viewBox="0 0 12 12"><path d="M3.5,2 H10 V8.5 M10,2 L2.2,9.8" fill="none" stroke="{C_GOLD_DEEP}" '
            'stroke-width="1.5" stroke-linecap="square"/></svg>')


# ---- 纸张纹理(构建时栅格化成 WebP，SVG 滤镜不进主题) ----
def tex_grain(size=320):
    """纸面细颗粒(第三版，参考 PaperK 的思路：一层很细很淡的纸纹为主，不要大块斑驳和长纤维——那样像木纹、像脏)：
    深褐暗点 + 暖白亮点两层，频率略错开"""
    return (f'<svg {SVG} width="{size}" height="{size}">'
            '<filter id="a" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".78" numOctaves="3" seed="4" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .40  0 0 0 0 .28  0 0 0 0 .14  1.9 0 0 0 -1.02"/></filter>'
            '<filter id="b" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".92" numOctaves="2" seed="13" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 1  0 0 0 0 .99  0 0 0 0 .95  2 0 0 0 -1.15"/></filter>'
            '<rect width="100%" height="100%" filter="url(#a)" opacity=".42"/>'
            '<rect width="100%" height="100%" filter="url(#b)" opacity=".38"/></svg>')


def tex_tone(size=1024):
    """大尺度的浓淡：很缓、很淡的暖褐云斑(看得出纸张不均匀，但不成块)"""
    return (f'<svg {SVG} width="{size}" height="{size}">'
            '<filter id="t" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".0034" numOctaves="4" seed="9" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .55  0 0 0 0 .40  0 0 0 0 .22  1.5 0 0 0 -.72"/></filter>'
            '<filter id="u" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".009" numOctaves="3" seed="27" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .5  0 0 0 0 .36  0 0 0 0 .2  1.5 0 0 0 -.8"/></filter>'
            '<rect width="100%" height="100%" filter="url(#t)" opacity=".16"/>'
            '<rect width="100%" height="100%" filter="url(#u)" opacity=".07"/></svg>')


def tex_ribbon(size=256, dark=.17, light=.16):
    """缎带上的羊皮纸斑驳(第六版，用户：缎带要叠羊皮纸斑驳纹理)：透明底，铺在缎带底色上面——暖褐的大小污斑 + 磨旧发白的浅斑。
    尺度比纸面纹理大；浓淡要轻(第一稿 .36 / .30 / .34，用户嫌太明显太脏，减到一半)。只有低频成分，大块平滑、压缩后很小；
    细碎斑点另做一张小图(tex_ribbon_speck)叠上去，小图重复看不出来。渲染成 256 的图、用的时候放大到 512 一格(低频放大不糊)"""
    return (f'<svg {SVG} width="{size}" height="{size}">'
            '<filter id="a" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".038" numOctaves="3" seed="31" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .42  0 0 0 0 .28  0 0 0 0 .13  2.6 0 0 0 -1.2"/></filter>'
            '<filter id="b" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".06" numOctaves="2" seed="8" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 1  0 0 0 0 .98  0 0 0 0 .92  2.4 0 0 0 -1.25"/></filter>'
            f'<rect width="100%" height="100%" filter="url(#a)" opacity="{dark}"/>'
            f'<rect width="100%" height="100%" filter="url(#b)" opacity="{light}"/></svg>')


def tex_ink(size=256, light=.42, fine=.2, dense=.06):
    """套色印章的颗粒(第八版，用户：第七版全是大大小小的气泡，不像印章套色——参考图是胶印 / 孔版插画：
    细密均匀的颗粒、像水粉干刷在冷压纸上)。不透明灰度图，当亮度遮罩用：白 = 墨色照印，越暗越透出纸色。
    三层：一两个像素大的漏白颗粒(主体，密而浅) + 更细的墨粒 + 很淡的中尺度浓淡(手按印章的轻重)。
    第七版的低频大斑和硬阈值白点(就是"气泡")都去掉了"""
    return (f'<svg {SVG} width="{size}" height="{size}"><rect width="100%" height="100%" fill="#fff"/>'
            '<filter id="a" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".62" numOctaves="2" seed="41" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  4.2 0 0 0 -2.15"/></filter>'
            '<filter id="b" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".95" numOctaves="1" seed="17" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3 0 0 0 -1.35"/></filter>'
            '<filter id="c" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="2" seed="3" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.2 0 0 0 -.9"/></filter>'
            f'<rect width="100%" height="100%" filter="url(#a)" opacity="{light}"/>'
            f'<rect width="100%" height="100%" filter="url(#b)" opacity="{fine}"/>'
            f'<rect width="100%" height="100%" filter="url(#c)" opacity="{dense}"/></svg>')


def tex_ink_dark(size=256, op=.12):
    """套色印章的深色墨粒(透明底)：颜料堆积的小深点，比漏白的颗粒稀。叠在图案上面(只叠在有墨的地方)。
    第九版减淡(.3 → .18，用户嫌颗粒粗糙；四稿再减到 .12，用户嫌脏)"""
    return (f'<svg {SVG} width="{size}" height="{size}">'
            '<filter id="a" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="88" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .2  0 0 0 0 .1  0 0 0 0 .04  5 0 0 0 -2.9"/></filter>'
            f'<rect width="100%" height="100%" filter="url(#a)" opacity="{op}"/></svg>')


def tex_ribbon_speck(size=96, op=.14):
    """缎带上细碎的深色斑点(稀疏)"""
    return (f'<svg {SVG} width="{size}" height="{size}">'
            '<filter id="c" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".6" numOctaves="2" seed="5" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .36  0 0 0 0 .22  0 0 0 0 .1  3.4 0 0 0 -2.0"/></filter>'
            f'<rect width="100%" height="100%" filter="url(#c)" opacity="{op}"/></svg>')


# ---- Callout 图标：game-icons 剪影遮罩(颜色跟 callout 类型色)；"@" 开头 = 自绘 ----
CALLOUT_ICONS = (
    (("note",), "quill"),
    (("abstract", "summary", "tldr"), "scroll-unfurled"),
    (("info",), "book"),                              # 第二十版：圆圈 i → 智库的书；第二十一版去掉两侧的光(太小看不清书)
    (("todo",), "hourglass"),                        # 第十九版(用户：太现代)：清单 → 沙漏；第二十版换敦实的一款(原来那款细，看着比别的小)
    (("important",), "holy-grail"),                    # 圣杯
    (("tip", "hint"), "candle-light"),
    (("success", "check", "done"), "laurels"),         # 桂冠
    (("question", "help", "faq"), "question-winged"),  # 第二十二版：面具不好看不清晰 → 问号；第二十四版(用户：还是单调)：圆点换成战团徽(双翼 + 血滴)
    (("warning", "caution", "attention"), "bell"),    # 警示三角 → 警钟(ringing-bell 去掉声波线，第十九版看不出是钟)
    (("failure", "fail", "missing"), "icooon:悲しみのアイコン"),   # 第二十四版：用户找的 ICOOON MONO「悲しみ」(闭眼、上下睫毛、空心泪滴)，替换第二十三版自拼的闭眼流泪
    (("danger", "error"), "bleeding-heart"),
    (("bug",), "winged-sword"),
    (("example",), "notebook"),
    (("quote", "cite"), "@quote"),
)
CALLOUT_LATIN = {
    "note": "NOTA", "abstract": "SUMMA", "info": "NOTITIA", "todo": "AGENDA", "important": "MEMENTO",
    "tip": "CONSILIUM", "success": "VICTORIA", "question": "QUAESTIO", "warning": "CAVE", "failure": "DEFECTUS",
    "danger": "PERICULUM", "bug": "VITIUM", "example": "EXEMPLUM", "quote": "DICTUM",
}


def callout_glyph(name):
    """→ 遮罩用 SVG(黑色剪影)，按 bbox.json 取正方形 viewBox 居中(水平往视觉重心挪一半)"""
    if name == "@quote":
        mark = "M{x},38 C{a},38 {b},34 {b},29.5 C{b},22 {c},14 {d},9 L{e},11.5 C{f},15 {g},19.5 {g},22 C{h},21.5 {i},25 {i},29.5 C{i},34.5 {j},38 {x},38Z"

        def one(o):
            v = dict(x=12 + o, a=7.5 + o, b=4 + o, c=8 + o, d=17 + o, e=18.5 + o, f=13.5 + o, g=11 + o, h=16.5 + o, i=20 + o, j=16.5 + o)
            return mark.format(**{k: f"{w:.1f}" for k, w in v.items()})
        return f'<svg {SVG} viewBox="0 0 48 48"><path d="{one(0)} {one(22)}"/></svg>'
    x, y, w, h, gx, _ = gi_bbox(name)
    cx, cy = x + w / 2 + (gx - (x + w / 2)) * .5, y + h / 2
    side = max(2 * max(cx - x, x + w - cx), h) * 1.04
    vb = f"{cx - side / 2:.1f} {cy - side / 2:.1f} {side:.1f} {side:.1f}"
    return f'<svg {SVG} viewBox="{vb}">' + "".join(f'<path d="{d}"/>' for d in gi_paths(name)) + "</svg>"


ICOOON_SRC = Path(r"E:\AI工作\素材库\ICOOON MONO")


ICOOON_FILL = {"悲しみのアイコン": [(1, 1)]}   # 要填实的孔：(第几条 path, 第几个子路径)。第二十四版用户：血泪改实心


def icooon_paths(name):
    src = (ICOOON_SRC / f"{name}.svg").read_text(encoding="utf-8")
    paths = [re.sub(r"\s+", " ", d) for d in re.findall(r'<path[^>]*\sd="([^"]+)"', src, re.S)]
    holes = ICOOON_FILL.get(name)
    if holes:
        from fontTools.pens.recordingPen import RecordingPen
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.svgLib.path import parse_path
        for pi in {h[0] for h in holes}:
            rec = RecordingPen()
            parse_path(paths[pi], rec)
            subs, cur = [], []
            for op, args in rec.value:
                if op == "moveTo" and cur:
                    subs.append(cur)
                    cur = []
                cur.append((op, args))
            subs.append(cur)
            sp = SVGPathPen(None)
            for si, sub in enumerate(subs):
                if (pi, si) not in holes:
                    for op, args in sub:
                        getattr(sp, op)(*args)
            paths[pi] = sp.getCommands()
    return paths


def _glyph_geom(name):
    """callout_glyph 同样的取景：(path 列表, 取景中心 x, y, 正方形边长)"""
    if name == "@quote":
        svg = callout_glyph(name)
        return re.findall(r'\sd="([^"]+)"', svg), 23, 23.5, 40
    if name.startswith("icooon:"):                 # 素材库里的 ICOOON MONO 图标(不能放进公开仓库，构建时从素材库读)
        paths = icooon_paths(name[7:])
        from fontTools.pens.boundsPen import BoundsPen
        from fontTools.svgLib.path import parse_path
        bp = BoundsPen(None)
        for d in paths:
            parse_path(d, bp)
        x0, y0, x1, y1 = bp.bounds
        return paths, (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) * 1.04
    x, y, w, h, gx, _ = gi_bbox(name)
    cx, cy = x + w / 2 + (gx - (x + w / 2)) * .5, y + h / 2
    return gi_paths(name), cx, cy, max(2 * max(cx - x, x + w - cx), h) * 1.04


SEAL_GLYPH_SCALE = {"@quote": .8, "bell": .88}  # 个别剪影看着偏大时单独缩(第二十一版：引号、钟；第二十三版：问号)


SEAL_GLYPH_SHIFT = {}                          # 个别剪影的中心再挪一点(剪影坐标)


def _glyph_circle(paths, center=None):
    """剪影轮廓(曲线按 12 段采样)的外接圆：(圆心 x, y, 半径)。给了 center 就以它为圆心求半径；
    否则在外框中心附近网格上找最大半径最小的点"""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.svgLib.path import parse_path
    pts = []
    for d in paths:
        rec = RecordingPen()
        parse_path(d, rec)
        cur = start = (0.0, 0.0)
        for op, args in rec.value:
            if op == "moveTo":
                cur = start = args[0]
                pts.append(cur)
            elif op == "lineTo":
                cur = args[0]
                pts.append(cur)
            elif op in ("curveTo", "qCurveTo"):
                ctrl = (cur,) + tuple(args)
                for t in (i / 12 for i in range(1, 13)):
                    q = list(ctrl)
                    while len(q) > 1:                  # de Casteljau
                        q = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(q, q[1:])]
                    pts.append(q[0])
                cur = args[-1]
            elif op == "closePath":
                cur = start
    if center:
        return center[0], center[1], max(math.hypot(x - center[0], y - center[1]) for x, y in pts)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    bx, by = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys)) * .08
    best = None
    for i in range(-6, 7):
        for j in range(-6, 7):
            cx, cy = bx + i * span / 6, by + j * span / 6
            r = max(math.hypot(x - cx, y - cy) for x, y in pts[::3])
            if best is None or r < best[2]:
                best = (cx, cy, r)
    cx, cy, _ = best
    return cx, cy, max(math.hypot(x - cx, y - cy) for x, y in pts)


def callout_seal(name, r=14.4, ring=1.0, gap=1.5):
    """callout 图标做成一枚蜡封(第二十版，用户：现在没有体现印章元素，如何整合；沙漏看着比别的图标小)。
    遮罩用 SVG(黑 = 有蜡)：近乎圆的蜡(同引文纯洁封印的画法) + 印面外一圈留白细环 + 图标镂空露出底色——
    纯色 + 纸色留白，和标签、表头同一套套色印章。所有图标都装在同样大小的印面里(边长 = 印面直径 × fit)，大小一致"""
    S, c = 32, 16
    pts = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        rr = r * (1 + .045 * math.sin(3 * a + .7) + .03 * math.sin(5 * a + 2.3) + .015 * math.sin(7 * a + 1.1))
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    blob = _smooth_closed(pts)
    ri = r * .8
    paths, gx, gy, _ = _glyph_geom(name)
    # 第二十版二稿(用户：有些图标碰到圆环内沿)：一稿按正方形外框缩放，四角饱满的剪影(书、桂冠)角会顶到圆环。
    # 改成按离中心最远的轮廓点缩放：每个图标离圆环都留同样的空隙 gap。
    # 第二十一版(用户：蜡烛往左歪、羽毛笔位置要调)：二稿的中心取最小外接圆圆心，又高又窄的剪影左右怎么挪外接圆都差不多大，
    # 网格搜索随便停在一边——蜡烛、羽毛笔被挤到左边。中心改回外框中心(水平往视觉重心挪一半，和原来的图标位一样)，只拿外接圆定大小
    gx, gy = gx + SEAL_GLYPH_SHIFT.get(name, (0, 0))[0], gy + SEAL_GLYPH_SHIFT.get(name, (0, 0))[1]
    rmax = _glyph_circle(paths, (gx, gy))[2]
    k = (ri - ring / 2 - gap) / rmax * SEAL_GLYPH_SCALE.get(name, 1)
    tf = f"translate({c - gx * k:.3f} {c - gy * k:.3f}) scale({k:.5f})"
    return (f'<svg {SVG} width="{S}" height="{S}" viewBox="0 0 {S} {S}"><defs>'
            f'<mask id="k" maskUnits="userSpaceOnUse" x="0" y="0" width="{S}" height="{S}">'
            f'<rect width="{S}" height="{S}" fill="#fff"/>'
            f'<circle cx="{c}" cy="{c}" r="{ri:.2f}" fill="none" stroke="#000" stroke-width="{ring}"/>'
            f'<g fill="#000" transform="{tf}">' + "".join(f'<path d="{d}"/>' for d in paths) + '</g></mask></defs>'
            f'<path d="{blob}" mask="url(#k)"/></svg>')


# ---- 圣吉列斯的光环(第四版，用户给的原画参考)：太阳式——一圈金环，外面波浪弯曲的火焰光芒与直的尖光芒交替 ----
def _wavy_ray(cx, cy, ang, r0, r1, w0, amp, waves=1.6, n=22):
    """一道弯曲的火焰光芒：沿半径方向，中心线按正弦左右摆，宽度从 w0 收到尖"""
    import math as m
    ca, sa = m.cos(ang), m.sin(ang)
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * t
        off = amp * m.sin(t * m.pi * waves) * t
        w = w0 * (1 - t) ** 0.9 / 2
        for side, out in ((1, left), (-1, right)):
            lat = off + side * w
            out.append((cx + r * ca - lat * sa, cy + r * sa + lat * ca))
    pts = left + right[::-1]
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"


def _flame_ray(cx, cy, ang, r0, length, w0, wave, curl, waves=1.3, n=48):
    """新标签页光环的火焰光芒(第七版，用户：小光芒也要扭曲、光芒末端弯回来的弧度不够)：
    中心线按"走向角"逐段积分出来——走向 = 波浪摆动 wave·sin(π·waves·t) + 末端卷曲 curl·t³(弧度，正负 = 卷的方向)，
    越到末端拐得越急，尖端整个卷回来；宽度从 w0 收到尖。在光芒自己的坐标系里算(u 沿半径向外、v 横向)，再转到画布"""
    ca, sa = math.cos(ang), math.sin(ang)
    ds = length / n
    u = v = 0.0
    center = []
    for i in range(n + 1):
        t = i / n
        center.append((t, u, v, wave * math.sin(math.pi * waves * t) + curl * t ** 3))
        ph = center[-1][3]
        u, v = u + ds * math.cos(ph), v + ds * math.sin(ph)
    left, right = [], []
    for t, u, v, ph in center:
        w = w0 * (1 - t) ** 0.85 / 2
        for side, out in ((1, left), (-1, right)):
            uu, vv = u - side * w * math.sin(ph), v + side * w * math.cos(ph)
            out.append((cx + (r0 + uu) * ca - vv * sa, cy + (r0 + uu) * sa + vv * ca))
    pts = left + right[::-1]
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"


def sun_halo_body(cx, cy, r, fill="url(#hg)", n=16, ring=.16, wavy_len=.95, straight_len=.6, amp=.24, inner_ring=True,
                  flame=None):
    """r = 金环外半径；n 道光芒(偶数位波浪火焰、奇数位直尖)。
    flame = (大光芒摆动, 大光芒卷曲, 小光芒摆动, 小光芒卷曲) 时改用 _flame_ray：大小光芒都是 S 形火焰。
    第八版(用户：光芒应该全朝一个方向，不是左右对称；正中那道也别是直尖)：所有光芒同一个旋转方向——
    根部先往逆时针摆，末端往顺时针卷(像转动的太阳)；卷回的幅度照原画 / 手办，末端只拐过来六七十度"""
    import math as m
    rays = []
    if flame:
        bw, bc, sw, sc = flame
        for i in range(n):
            a = 2 * m.pi * i / n - m.pi / 2
            if i % 2 == 1:
                rays.append(_flame_ray(cx, cy, a, r * .9, r * wavy_len, r * .3, bw, bc))
            else:
                rays.append(_flame_ray(cx, cy, a, r * .92, r * straight_len, r * .17, sw, sc, waves=1.1))
        n = 0
    for i in range(n):
        a = 2 * m.pi * i / n - m.pi / 2
        if i % 2 == 0:
            rays.append(_wavy_ray(cx, cy, a, r * .92, r * (1 + wavy_len), r * .3, r * amp))
        else:
            half = m.radians(180 / n * .42)
            tip = (cx + r * (1 + straight_len) * m.cos(a), cy + r * (1 + straight_len) * m.sin(a))
            b1 = (cx + r * .95 * m.cos(a - half), cy + r * .95 * m.sin(a - half))
            b2 = (cx + r * .95 * m.cos(a + half), cy + r * .95 * m.sin(a + half))
            rays.append(f"M{b1[0]:.2f},{b1[1]:.2f} L{tip[0]:.2f},{tip[1]:.2f} L{b2[0]:.2f},{b2[1]:.2f}Z")
    ri = r * (1 - ring)
    ring_d = (f"M{cx - r:.2f},{cy:.2f} A{r:.2f},{r:.2f} 0 1 0 {cx + r:.2f},{cy:.2f} A{r:.2f},{r:.2f} 0 1 0 {cx - r:.2f},{cy:.2f}Z "
              f"M{cx - ri:.2f},{cy:.2f} A{ri:.2f},{ri:.2f} 0 1 1 {cx + ri:.2f},{cy:.2f} A{ri:.2f},{ri:.2f} 0 1 1 {cx - ri:.2f},{cy:.2f}Z")
    inner = (f'<circle cx="{cx}" cy="{cy}" r="{ri * .82:.2f}" fill="none" stroke="{fill}" stroke-width="{r * .05:.2f}"/>'
             if inner_ring else "")
    return f'<path d="{" ".join(rays)}" fill="{fill}"/><path d="{ring_d}" fill="{fill}" fill-rule="evenodd"/>{inner}'


def sun_halo(size=64, n=16):
    c = size / 2
    r = size / 2 / 2.0
    return (f'<svg {SVG} viewBox="0 0 {size} {size}"><defs>{gold_defs("hg")}</defs>'
            f'{sun_halo_body(c, c, r, n=n)}</svg>')


def sun_halo_small(size=32):
    """小尺寸(H3 / 列表符号)：8 道光芒、环带加厚、去掉内圈"""
    c = size / 2
    r = size / 2 / 1.95
    return (f'<svg {SVG} viewBox="0 0 {size} {size}"><defs>{gold_defs("hg")}</defs>'
            f'{sun_halo_body(c, c, r, n=12, ring=.3, wavy_len=.95, straight_len=.62, amp=.26, inner_ring=False)}</svg>')


# ---- 巴尔宝石(第六版，用户给的圣吉列斯胸甲照片：是好几颗宝石组成的一组)：
# 上面一颗圆宝石(竖直猫眼)、中间三颗小圆宝石(两侧高、正中低)、下面一颗上圆下尖的大宝石(长猫眼)，嵌在一块连成一体的金托上。
# 比例照照片量的：整组 100 × 200 单位
GEM_BOX = (-7, -7, 114, 214)


def _lens(cx, y0, y1, w):
    """竖直的猫眼缝：两头尖、正中最宽 w(半宽)"""
    c, h = w / .75, y1 - y0
    return (f"M{cx:.2f},{y0:.2f} C{cx + c:.2f},{y0 + h * .3:.2f} {cx + c:.2f},{y1 - h * .3:.2f} {cx:.2f},{y1:.2f} "
            f"C{cx - c:.2f},{y1 - h * .3:.2f} {cx - c:.2f},{y0 + h * .3:.2f} {cx:.2f},{y0:.2f}Z")


GEM_HEART = "M50,106 C73,106 97,114 97,138 C97,163 70,184 50,199 C30,184 3,163 3,138 C3,114 27,106 50,106Z"
GEM_ROUND = ((50, 21, 20), (14, 64, 11.5), (86, 64, 11.5), (50, 80, 11.5))


def baal_cluster(mount="url(#g)", gem="url(#b)", slit="#3e050a", glint=True, grow=0):
    """整组宝石(单位见 GEM_BOX)，摆放时外面套 transform。defs 里要有 mount / gem 用到的渐变。
    grow > 0：金托整体外扩 grow(做遮罩里抠空隙用的剪影)"""
    m = (f'<path d="M50,21 L14,64 L50,80 L86,64Z" fill="{mount}" stroke="{mount}" stroke-width="{24 + grow:g}" stroke-linejoin="round"/>'
         f'<rect x="{41 - grow / 2:g}" y="78" width="{18 + grow:g}" height="34" fill="{mount}"/>'
         + "".join(f'<circle cx="{x}" cy="{y}" r="{r + 6 + grow / 2:g}" fill="{mount}"/>' for x, y, r in GEM_ROUND)
         + f'<path d="{GEM_HEART}" fill="{mount}" stroke="{mount}" stroke-width="{12 + grow:g}" stroke-linejoin="round"/>')
    if grow:
        return m
    g = ("".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{gem}"/>' for x, y, r in GEM_ROUND)
         + f'<path d="{GEM_HEART}" fill="{gem}"/>')
    sl = f'<path d="{_lens(50, 5, 37, 3.4)} {_lens(50, 114, 191, 5.2)}" fill="{slit}"/>'
    gl = ""
    if glint:
        gl = ('<g fill="#fff" fill-opacity=".32">'
              '<ellipse cx="40" cy="12" rx="5" ry="2.8" transform="rotate(-35 40 12)"/>'
              + "".join(f'<circle cx="{x - r * .4:.1f}" cy="{y - r * .4:.1f}" r="{r * .26:.1f}"/>' for x, y, r in GEM_ROUND[1:])
              + '<ellipse cx="25" cy="125" rx="9" ry="4.5" transform="rotate(-28 25 125)"/></g>')
    return m + g + sl + gl


def baal_cluster_at(cx, top, h, **kw):
    s = h / GEM_BOX[3]
    return (f'<g transform="translate({cx - (GEM_BOX[0] + GEM_BOX[2] / 2) * s:.2f} {top - GEM_BOX[1] * s:.2f}) scale({s:.4f})">'
            f'{baal_cluster(**kw)}</g>')


def baal_gem(ink=None, cell=1100, grow=10, knock=4.5, gem=GEM_RED, mount="#c2a04a", ink_dark=None, glint=None):
    """H2 标记：整组巴尔宝石。
    第九版(用户：标题里的宝石也要匹配印章质感)：同新标签页徽章的套色画法——金托平涂并整体外扩 grow，
    宝石和金托之间抠一道 knock 宽的纸色留白线(外扩是为了抠完还剩一圈金)，高光改成抠空透出纸色，
    整组叠印刷颗粒(ink；cell = 颗粒图一格在宝石单位里的大小：H2 里整组约 27px 高，1650 单位一格 ≈ 一粒 1 设备像素)。
    第十版(用户：宝石还是太鲜艳、纹理不明显)：宝石改降饱和的砖红(GEM_RED)、金托旧金 #c2a04a、颗粒用原浓度的图并放大一点
    (1100 一格 ≈ 一粒 1.5 设备像素)、加稀疏的深色墨粒(ink_dark)；比过只换颗粒 / 只换颜色。
    glint：高光抠空处填的颜色(夜间：抠空透出的纸是黑的，用户要高光保持亮色)；None = 抠空透出纸色"""
    vb = GEM_BOX
    mu = f'maskUnits="userSpaceOnUse" x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}"'
    full = f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="#fff"/>'
    gems = "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in GEM_ROUND) + f'<path d="{GEM_HEART}"/>'
    glints = ('<ellipse cx="40" cy="12" rx="5.5" ry="3.2" transform="rotate(-35 40 12)"/>'
              '<ellipse cx="25" cy="125" rx="10" ry="5" transform="rotate(-28 25 125)"/>')
    defs = (gold_defs("g")
            + f'<linearGradient id="b" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="{gem[0]}"/>'
              f'<stop offset="1" stop-color="{gem[1]}"/></linearGradient>'
            + f'<mask id="mm" {mu}>{full}<g fill="#000" stroke="#000" stroke-width="{2 * knock}" stroke-linejoin="round">{gems}</g></mask>'
            + f'<mask id="mg" {mu}>{full}<g fill="#000">{glints}</g></mask>')
    body = (f'<g id="gm"><g mask="url(#mm)">{baal_cluster(mount=mount or C_GOLD, grow=grow)}</g>'
            f'<g mask="url(#mg)"><g fill="url(#b)">{gems}</g>'
            f'<path d="{_lens(50, 5, 37, 3.4)} {_lens(50, 114, 191, 5.2)}" fill="#3e050a"/></g>'
            + (f'<g fill="{glint}">{glints}</g>' if glint else "") + '</g>')
    if ink_dark:
        defs += (f'<pattern id="dp" patternUnits="userSpaceOnUse" width="{cell}" height="{cell}" x="37" y="11">'
                 f'<image href="{ink_dark}" width="{cell}" height="{cell}"/></pattern>'
                 f'<mask id="ma" {mu} style="mask-type:alpha"><use href="#gm"/></mask>')
        body += f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="url(#dp)" mask="url(#ma)"/>'
    if ink:
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="{cell}" height="{cell}">'
                 f'<image href="{ink}" width="{cell}" height="{cell}"/></pattern>'
                 f'<mask id="mk" {mu}><rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="url(#ip)"/></mask>')
        body = f'<g mask="url(#mk)">{body}</g>'
    return f'<svg {SVG} viewBox="{" ".join(map(str, vb))}"><defs>{defs}</defs>{body}</svg>'


# ---- 属性栏花框(第二十七版八稿 A)：九宫格 border-image，SVG 1 单位 = 1px，只拉长中段直线、线宽不变。
# 灵感是用户说的「四角像朝外飞、展开翅膀的鸽子」：四角各一对版画翅膀(Heritage Angels _ Fairies 02 E7 原画那一对，
# 描线见 tools/heritage_trace.py wing_pair)，转 135° 让羽毛铺满角上、两道翼前缘朝里；角上不出现直角，角本身就是花纹。
# 描好的矢量放在素材库 Heritage Library\_描线\(Heritage 条款禁止再分发素材文件，描线也不进公开仓库)，构建时读取。
# 外粗线 2px + 内细线 0.9px(文武线)；翼尖之后的外粗线上压一段 f0566 卷草臂(标题花边那件，去掉最靠近翅膀的两撮长叶 16 / 17)；
# 两翼之间垫一枚放大的 H3 小太阳光环，翼根外侧一枚金色空心血滴(同二级列表符号)，尖朝里。
# 十稿(用户：卷草不够厚重大气)：卷草从角上去掉(crest=False，切片 121 → 79)，挪到属性标题两侧(props_heading_arm)；试过浮空阴影，用户嫌脏。
# 层次(下 → 上)：线 → 卷草 → 光环 → 翅膀 → 血滴，每层在上面那层周围抠一道 knock px 的纸色缝(翅膀按实心外形抠)；
# 内细线不在角上绕圆角(会从装饰缝里露出来)，直接伸进翅膀底下 deep px 收住
C_PROPS = "#c9a548"                              # = --ba-gold
HERITAGE = Path(r"E:\AI工作\素材库\Heritage Library\_描线")
PROPS_WING = dict(mid=(59.4, 17.6), tips=((121.6, 2.0), (1.6, 1.0)))    # wing-pair 里两翼根之间的中点、两个翼尖
PROPS_CREST = [7, 8, 9, 10, 11, 12, 13, 14, 15, 22]                      # f0566_0 右臂的花叶(不含 16 / 17 和底下两道线)


def _heritage(name):
    s = (HERITAGE / f"{name}.svg").read_text(encoding="utf-8")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
    return re.search(r' d="([^"]+)"', s).group(1), vb


def _polys(d):
    """描出来的 path(M x,y L … Z) → [[(x, y), …], …]"""
    return [[tuple(map(float, p.split(","))) for p in re.findall(r"-?[\d.]+,-?[\d.]+", seg)]
            for seg in re.findall(r"M([^MZ]+)Z", d)]


def _affine(ops):
    """ops：[("t", x, y) | ("r", 度) | ("s", sx, sy)]，按 SVG transform 的书写顺序(最右边先作用) → 点变换函数"""
    def f(p):
        x, y = p
        for op in reversed(ops):
            if op[0] == "t":
                x, y = x + op[1], y + op[2]
            elif op[0] == "s":
                x, y = x * op[1], y * op[2]
            else:
                a = math.radians(op[1])
                x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return x, y
    return f


def _tf(ops):
    return " ".join({"t": "translate({} {})", "r": "rotate({})", "s": "scale({} {})"}[o[0]].format(*[f"{v:.5f}" for v in o[1:]])
                    for o in ops)


def _inside(polys, x, y):
    hit = False
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
    return hit


def props_frame(W=90, T=14.0, M=30, TH=2.0, th=.9, gap=3.2, col=C_PROPS, halo=26.0, drop_h=15.0, drop_out=3.5, ka=.2,
                crest_back=7.0, crest_dy=3.0, knock=.9, deep=5.0, crest=False):
    """→ (svg, C)：边长 2C + M 的方形 SVG，C = 九宫格切片(角上的东西全在 C 里，否则会被拉伸)。
    W 翼展；T 外粗线离图边；TH / th 外粗 / 内细线宽，gap 两线间距；halo 光环直径；drop_h 血滴高、drop_out 血滴往外角挪多少；
    crest=True：八稿的卷草(ka 缩放，crest_back 起点比翼尖往角上挪多少、藏到翅膀后面，crest_dy 下沉多少、压在外粗线上)"""
    d, vb = _heritage("wing-pair")
    dfill, _ = _heritage("wing-pair-fill")
    mid = PROPS_WING["mid"]
    ops = [("s", W / vb[2], W / vb[2]), ("t", -mid[0], -mid[1])]
    rot = 135
    tips = [_affine([("r", rot)] + ops)(t) for t in PROPS_WING["tips"]]
    up = min(tips, key=lambda p: p[1])                 # 落在上边外粗线上的那个翼尖
    c = T + 1 - up[1]                                  # 翅膀中心(c, c) 在对角线上
    tipx = c + up[0]
    xl = tipx - 2                                      # 外粗线从翼尖底下开始
    yi = T + TH + gap + th / 2                         # 内细线中心
    w_ops = [("t", c, c), ("r", rot)] + ops
    polys = [[_affine(w_ops)(p) for p in poly] for poly in _polys(dfill)]

    def line_end(horiz):
        """内细线从翼尖外侧往外角扫，连续 deep px 都在翅膀实心外形里的地方收住"""
        run, v = 0.0, tipx + 6
        while v > 0:
            run = run + .25 if _inside(polys, *((v, yi) if horiz else (yi, v))) else 0.0
            if run >= deep:
                return v
            v -= .25
        return yi
    xe_t, xe_l = line_end(True), line_end(False)
    ax0, ay0 = 556.0, 190.0                            # f0566_0 右臂：花叶落在线上的 y、线开始的 x
    cx0 = tipx - crest_back
    arm = _asset_paths("f0566_0")
    crest_g = (f'<g transform="translate({cx0 - ax0 * ka:.3f} {T + crest_dy - ay0 * ka:.3f}) scale({ka})">'
               + "".join(f'<path d="{arm[i]}"/>' for i in PROPS_CREST) + "</g>") if crest else ""
    C = math.ceil(max(cx0 + (800 - ax0) * ka + 4 if crest else 0, xl + 6, xe_t + 8, xe_l + 8, c + 40))   # 外粗线起点也要在切片里，否则那截空隙被拉长成缺口
    S = 2 * C + M
    dh = drop_h
    outer = drop_path(0, -dh * .58, dh)
    dpos = f"translate({c - drop_out:.2f} {c - drop_out:.2f}) rotate(135)"
    # 部件只写一次(<use> 引用)：上边一份，左边那份 = 沿对角线翻过去(卷草)；四角 = 左上角镜像
    defs = (f'<g id="cr">{crest_g}<g transform="matrix(0 1 1 0 0 0)">{crest_g}</g></g>'
            f'<g id="ha">{sun_halo_body(c, c, halo / 2 / 1.95, fill="inherit", n=12, ring=.3, wavy_len=.95, straight_len=.62, amp=.26, inner_ring=False)}</g>'
            f'<path id="wi" fill-rule="evenodd" d="{d}" transform="{_tf(w_ops)}"/>'
            f'<path id="ws" d="{dfill}" transform="{_tf(w_ops)}"/>'
            f'<path id="dr" fill-rule="evenodd" d="{outer} {drop_path(0, -dh * .58 + dh * .3, dh * .5)}" transform="{dpos}"/>'
            f'<path id="ds" d="{outer}" transform="{dpos}"/>')
    mirrors = ("", f"translate({S} 0) scale(-1 1)", f"translate(0 {S}) scale(1 -1)", f"translate({S} {S}) scale(-1 -1)")
    every = lambda *ids: "".join(f'<use href="#{i}"' + (f' transform="{m}"' if m else "") + "/>" for i in ids for m in mirrors)
    cut = lambda *ids: f'<g fill="#000" stroke="#000" stroke-width="{2 * knock}" stroke-linejoin="round">{every(*ids)}</g>'
    mu = f'maskUnits="userSpaceOnUse" x="0" y="0" width="{S}" height="{S}"'
    full = f'<rect width="{S}" height="{S}" fill="#fff"/>'
    defs += (f'<mask id="mL" {mu}>{full}{cut("cr", "ha", "ws", "ds")}</mask>'
             f'<mask id="mC" {mu}>{full}{cut("ha", "ws", "ds")}</mask>'
             f'<mask id="mH" {mu}>{full}{cut("ws", "ds")}</mask>'
             f'<mask id="mW" {mu}>{full}{cut("ds")}</mask>')
    r = lambda x, y, w, h: f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}"/>'
    lines = (r(xl, T, S - 2 * xl, TH) + r(xl, S - T - TH, S - 2 * xl, TH) + r(T, xl, TH, S - 2 * xl) + r(S - T - TH, xl, TH, S - 2 * xl)
             + r(xe_t, yi - th / 2, S - 2 * xe_t, th) + r(xe_t, S - yi - th / 2, S - 2 * xe_t, th)
             + r(yi - th / 2, xe_l, th, S - 2 * xe_l) + r(S - yi - th / 2, xe_l, th, S - 2 * xe_l))
    body = (f'<g fill="{col}"><g mask="url(#mL)">{lines}</g><g mask="url(#mC)">{every("cr")}</g>'
            f'<g mask="url(#mH)">{every("ha")}</g><g mask="url(#mW)">{every("wi")}</g>{every("dr")}</g>')
    return f'<svg {SVG} width="{S}" height="{S}" viewBox="0 0 {S} {S}"><defs>{defs}</defs>{body}</svg>', C


def props_heading_arm(k=.17, ids=(16, 17, 15, 14, 13, 12, 10, 11, 7, 9, 8, 22), mid=152.0, line_from=556.0, k2=.32, extra=8.0,
                      knock=.7, mirror=False, col=C_PROPS):
    """属性栏标题「笔记属性」右侧的花边(第二十七版十稿起，用户：标题居中、左右要有装饰横线，花框上去掉的卷草可以用到这里)。
    f0566_0 右臂的花叶(ids，素材坐标) + 一根金线：线从 line_from(素材 x，藏在花叶底下)往外，出了花叶再接 f1090_1 右臂的「直线 + 菱形 + 箭头」
    (部件 11，用户：横线换成 f1090 的箭头菱形样式；缩放 k2，线粗 = 素材线粗 3.9 × k2)，中间补 extra px 直线。花叶周围抠 knock px 纸色缝。
    mid：线的中心在 f0566 素材里的 y。193 = 花叶坐在线上(原画的线就在这里，十三稿 a：衔接最像原画，但花叶全在线上方、整组偏高，像标题错位；
    去掉了最高的两片长叶 16 / 17)；152 = 花叶墨迹重心(线从卷叶中间穿过，十三稿 c，要留长叶)。
    图的上下以线为中线对称，CSS 里竖直居中线就落在文字行的正中(用户：横线要在行高里垂直居中)。
    mirror：花叶沿线(对称轴)上下镜像一份(十四稿，用户：a 的卷草沿横线轴对称；a + 镜像，线就是对称轴，整组自然居中)。
    定稿 = c(默认参数：线穿花叶、留长叶、不镜像。用户说「用现状」指的是镜像之前装的 c，十四稿镜像版曾误提交为 a00786e)。
    返回 (svg, 宽, 高, 花叶宽)；左侧 = CSS 水平翻转"""
    arm = _asset_paths("f0566_0")
    f10 = _asset_paths("f1090_1")
    box = {7: (671, 128, 52, 64), 8: (719, 166, 16, 24), 9: (684, 153, 69, 42), 10: (623, 161, 8, 27), 11: (622, 149, 44, 37),
           12: (569, 131, 48, 56), 13: (555, 145, 35, 52), 14: (535, 164, 39, 32), 15: (521, 132, 24, 16), 16: (447, 112, 33, 14),
           17: (456, 92, 99, 73), 22: (756, 153, 40, 44)}             # f0566_0 各片包围盒(x, y, w, h)，量过
    x0 = min(box[i][0] for i in ids) - .5
    top = min(box[i][1] for i in ids)
    bottom = max(box[i][1] + box[i][3] for i in ids)
    x_end = max(box[i][0] + box[i][2] for i in ids)                  # 花叶外端
    TH = 3.9 * k2                                                    # f1090 直线粗(素材 28.7–32.6)
    up, down = (mid - top) * k, (bottom - mid) * k
    if mirror:
        up = down = max(up, down)
    half = max(up, down, (41.0 - 30.65) * k2, TH / 2) + 1
    H = round(2 * half, 2)
    ox, oy = 1 - x0 * k, half - mid * k
    lx = 1 + (line_from - x0) * k
    jx = 1 + (x_end - x0) * k + extra                                # f1090 臂的内端
    W = jx + (796.0 - 640.5) * k2 + 1
    leaf_w = 1 + (x_end - x0) * k
    leaves = f'<g transform="translate({ox:.3f} {oy:.3f}) scale({k})">' + "".join(f'<path d="{arm[i]}"/>' for i in ids) + "</g>"
    leaves = f'<g id="lv">{leaves}' + (f'<g transform="translate(0 {2 * half:.3f}) scale(1 -1)">{leaves}</g>' if mirror else "") + "</g>"
    mu = f'maskUnits="userSpaceOnUse" x="0" y="0" width="{W:.1f}" height="{H}"'
    defs = (f'{leaves}<mask id="m" {mu}><rect width="{W:.1f}" height="{H}" fill="#fff"/>'
            f'<use href="#lv" fill="#000" stroke="#000" stroke-width="{2 * knock / k:.2f}" stroke-linejoin="round"/></mask>')
    line = f'<rect x="{lx:.2f}" y="{half - TH / 2:.3f}" width="{jx - lx + .3:.2f}" height="{TH:.3f}"/>'
    tip = f'<path transform="translate({jx - 640.5 * k2:.3f} {half - 30.65 * k2:.3f}) scale({k2})" d="{f10[11]}"/>'
    body = f'<g fill="{col}"><g mask="url(#m)">{line}{tip}</g><use href="#lv"/></g>'
    return f'<svg {SVG} width="{W:.1f}" height="{H}" viewBox="0 0 {W:.1f} {H}"><defs>{defs}</defs>{body}</svg>', W, H, leaf_w


# ---- 任务复选框(第二十八版)：默认 = 巴尔宝石(空金托 → 嵌一颗砖红宝石，同 H2 宝石的竖直猫眼)；
# Style Settings 可换蜡封(金双圈 → 红蜡封，同 callout 图标的蜡封)或原版。扩展状态字符同 Nox Aeterna / Minimal。
# 符号是用户从候选表里挑的：取消 = 碎颅骨(碎剑缩小后只剩一道斜线，换掉)，重要 / 疑问 / 推迟 = callout 同款(圣杯 / 徽记问号 / 沙漏)，信息 = 卷轴，
# 地点 = 插旗塔楼，排期 = 日晷；星标 / 引语 / 书签 / 想法是一稿的几何和 EB Garamond 字形。蜡封的已完成 = 红蜡镂空战团徽。
# 颜色只三类：红(重要、书签)、金(其余)、灰(取消)。宝石版画在 16 单位里、显示 1.15 倍(金托 ≈ 蜡封大小)；蜡封 20 单位
TASK_STATES = {   # 字符 -> (符号, 颜色类别)。符号：src/icons/gi 的文件名，"@" 开头 = TASK_GEOM，"emblem" = 战团徽
    "-": ("broken-skull", "ash"), ">": ("hourglass", "gold"), "<": ("sundial", "gold"), "!": ("holy-grail", "red"),
    "?": ("question-winged", "gold"), "*": ("@star", "gold"), '"': ("@ldquo", "gold"), "i": ("scroll-unfurled", "gold"),
    "b": ("@bookmark", "red"), "l": ("tower-flag", "gold"), "I": ("@flame", "gold"),
}
TASK_SEAL_DONE = "emblem"
TASK_WAX = {"red": "#a32a35", "gold": "#b08a34", "ash": "#a99784"}      # 蜡色(红 = --tag-background)
TASK_INK = {"red": C_CRIMSON, "gold": "#9c7a2a", "ash": "#a99784"}       # 金托里的符号色
TASK_MOUNT = "#c2a04a"                                                   # 金托(取消用灰托)


def _task_star(cx=8, cy=8, r1=5.2, r2=2.3, r3=1.35, n=8):
    """八芒星：四道长芒(r1) + 四道短芒(r2)，芒间凹进 r3"""
    pts = []
    for i in range(2 * n):
        a = -math.pi / 2 + math.pi * i / n
        r = (r1 if i % 4 == 0 else r2) if i % 2 == 0 else r3
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return "M" + " L".join(pts) + "Z"


TASK_GEOM = {   # (path, 包围盒缩放微调)
    "@star": (_task_star(), 1.06),
    "@bookmark": ("M5.2,3.2 H10.8 V12.8 L8,10.4 L5.2,12.8 Z", .92),       # 燕尾书签
    "@flame": ("M8,3.2 C10.2,5.6 11.1,7.4 11.1,9.3 A3.1,3.1 0 0 1 4.9,9.3 C4.9,7.7 5.9,6.4 6.7,5.3 "
               "C6.9,6.7 7.4,7.3 8,7.6 C8.4,6.2 8.4,4.8 8,3.2 Z", .96),
    # EB Garamond 700 的左双引号“(fontTools 取字形、y 翻转，坐标取一位小数)
    "@ldquo": ("M395.4 -699Q420.8 -699 420.8 -683.1Q420.8 -675.8 414.9 -672.8Q408.9 -669.8 398.6 -667Q372.7 -660.5 353.1 -648"
               "Q333.4 -635.5 323 -618.4Q312.5 -601.2 312.5 -578.5Q312.5 -560.8 325.2 -549.9Q337.9 -539 353.9 -534.5Q371.8 -530 384.3 -515.7"
               "Q396.8 -501.3 396.8 -476.9Q396.8 -451.2 375.4 -433.3Q354 -415.3 327.1 -415.3Q282 -415.3 254 -444.5Q226 -473.6 226 -518.9"
               "Q226 -559.4 241 -592.3Q256 -625.3 280.7 -649.3Q305.3 -673.4 335.1 -686.2Q365 -699 395.4 -699Z"
               "M194.8 -699Q220.2 -699 220.2 -683.1Q220.2 -675.8 214.3 -672.8Q208.3 -669.8 198 -667Q172.1 -660.5 152.5 -648"
               "Q132.8 -635.5 122.4 -618.4Q111.9 -601.2 111.9 -578.5Q111.9 -560.8 124.6 -549.9Q137.3 -539 153.3 -534.5Q171.2 -530 183.7 -515.7"
               "Q196.2 -501.3 196.2 -476.9Q196.2 -451.2 174.8 -433.3Q153.4 -415.3 126.5 -415.3Q81.4 -415.3 53.4 -444.5Q25.4 -473.6 25.4 -518.9"
               "Q25.4 -559.4 40.4 -592.3Q55.4 -625.3 80.1 -649.3Q104.7 -673.4 134.5 -686.2Q164.4 -699 194.8 -699Z", .82),
}


_TASK_GLYPHS = {}


def _task_glyph(name):
    """→ (path 列表, 包围盒 x0 y0 x1 y1, 外接圆半径(以包围盒中心为圆心))"""
    if name not in _TASK_GLYPHS:
        from fontTools.pens.boundsPen import BoundsPen
        from fontTools.svgLib.path import parse_path
        if name in TASK_GEOM:
            paths = [TASK_GEOM[name][0]]
        elif name == "emblem":
            paths = list(_logo_parts()[1].values())
        else:
            paths = gi_paths(name)
        bp = BoundsPen(None)
        for d in paths:
            parse_path(d, bp)
        x0, y0, x1, y1 = bp.bounds
        _TASK_GLYPHS[name] = paths, (x0, y0, x1, y1), _glyph_circle(paths, ((x0 + x1) / 2, (y0 + y1) / 2))[2]
    return _TASK_GLYPHS[name]


def _task_place(name, c, size, fill, bold):
    """符号放在 (c, c)：剪影按外接圆缩放(直径 = size，四角饱满的剪影也不碰圈)；几何 / 字形按包围盒长边 = size。
    bold = 用同色描边加粗(单位同画布)"""
    paths, (x0, y0, x1, y1), rad = _task_glyph(name)
    k = size / max(x1 - x0, y1 - y0) * TASK_GEOM[name][1] if name in TASK_GEOM else size / 2 / rad
    tf = f"translate({c - (x0 + x1) / 2 * k:.3f} {c - (y0 + y1) / 2 * k:.3f}) scale({k:.5f})"
    rule = "evenodd" if name in TASK_GEOM else "nonzero"
    return (f'<g transform="{tf}" fill="{fill}" fill-rule="{rule}" stroke="{fill}" stroke-width="{bold / k:.2f}" stroke-linejoin="round">'
            + "".join(f'<path d="{d}"/>' for d in paths) + "</g>")


def task_seal(name=None):
    """蜡封遮罩(黑 = 蜡，20 单位)：近乎圆的蜡 + 印面一圈留白细环 + 符号镂空"""
    S, r = 20, 8.9
    c, ri = S / 2, r * .8
    pts = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        rr = r * (1 + .045 * math.sin(3 * a + .7) + .03 * math.sin(5 * a + 2.3) + .015 * math.sin(7 * a + 1.1))
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    if not name:
        g = ""
    elif name in TASK_GEOM:
        g = _task_place(name, c, ri * 1.42, "#000", .3)
    else:
        g = _task_place(name, c, 11.4, "#000", .15)
    return (f'<svg {SVG} width="{S}" height="{S}" viewBox="0 0 {S} {S}"><defs>'
            f'<mask id="k" maskUnits="userSpaceOnUse" x="0" y="0" width="{S}" height="{S}"><rect width="{S}" height="{S}" fill="#fff"/>'
            f'<circle cx="{c}" cy="{c}" r="{ri:.2f}" fill="none" stroke="#000" stroke-width=".8"/>{g}</mask></defs>'
            f'<path d="{_smooth_closed(pts)}" mask="url(#k)"/></svg>')


def task_seal_drop():
    """蜡封版的进行中：金双圈(同未完成)里一滴红蜡(蜡刚滴下、还没盖印)，遮罩，20 单位；蜡滴收在内圈里(内圈内沿 4.63)。
    一稿是左半枚蜡封(用户：有点怪)；比过圈心一小团蜡、整枚空印，用户定这滴。
    二稿只留外圈、蜡滴大一号(压到内圈)，用户：外框要和未完成一样是双线；
    三稿用户觉得进行中整体比未完成小一圈(实测一样大，是红蜡把视线往里拉)→ 蜡滴再缩一档(高 7.9 → 6.7)；
    再往下挪 0.45(用户：稍微往下)，包围盒中心 10.15，比圈心略低"""
    return f'<svg {SVG} width="20" height="20" viewBox="0 0 20 20"><path d="{drop_path(10, 6.8, 6.7, 4.15)}"/></svg>'


def task_seal_ring(col=C_PROPS):
    """蜡封版的未完成 / 进行中：金色双圈(16 单位，铺满复选框)"""
    return (f'<svg {SVG} width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="{col}">'
            f'<circle cx="8" cy="8" r="7.15" stroke-width="1.1"/><circle cx="8" cy="8" r="4.9" stroke-width=".55"/></svg>')


def _task_mount(col):
    prongs = "".join(f'<circle cx="{8 + 6.95 * math.cos(a):.2f}" cy="{8 + 6.95 * math.sin(a):.2f}" r=".95"/>'
                     for a in (math.pi / 4 * k for k in (1, 3, 5, 7)))
    return f'<circle cx="8" cy="8" r="6.2" fill="none" stroke="{col}" stroke-width="1.6"/><g fill="{col}">{prongs}</g>'


def task_bezel(name=None, kind="gold"):
    """宝石版的未完成 / 扩展状态：空金托(圆托 + 四个斜爪，16 单位)，扩展状态托里一枚着色符号(取消用灰托)"""
    g = ""
    if name:
        g = _task_place(name, 8, 7.9, TASK_INK[kind], .35) if name in TASK_GEOM else _task_place(name, 8, 9.5, TASK_INK[kind], .12)
    return f'<svg {SVG} width="16" height="16" viewBox="0 0 16 16">{_task_mount(TASK_INK["ash"] if kind == "ash" else TASK_MOUNT)}{g}</svg>'


def task_gem(glint=None):
    """宝石版的已完成：金托 + 留一道纸色缝 + 砖红宝石(斜向渐变) + 竖直猫眼缝 + 左上抠空的高光。
    glint：高光抠空处填的颜色(夜间：抠空透出的纸是黑的，用户要高光保持亮色，同二级标题宝石)；None = 抠空透出纸色"""
    r = 6.2 - .8 - .75
    hl = '<ellipse cx="6.1" cy="5.6" rx="1.25" ry=".7" transform="rotate(-38 6.1 5.6)"'
    return (f'<svg {SVG} width="16" height="16" viewBox="0 0 16 16"><defs>{gem_defs("b")}'
            f'<mask id="g" maskUnits="userSpaceOnUse" x="0" y="0" width="16" height="16"><rect width="16" height="16" fill="#fff"/>'
            f'{hl} fill="#000"/></mask></defs>'
            f'{_task_mount(TASK_MOUNT)}<g mask="url(#g)">'
            f'<circle cx="8" cy="8" r="{r:.2f}" fill="url(#b)"/><path d="{_lens(8, 8 - r * .78, 8 + r * .78, .62)}" fill="#3e050a"/></g>'
            + (f'{hl} fill="{glint}"/>' if glint else "") + '</svg>')


def task_gem_drop(top=3.8, h=8.0, w=5.0, glint=None):
    """宝石版的进行中：金托里一滴血(还没凝成宝石；同宝石的渐变，左上抠空弯月高光)。
    一稿是左半颗宝石(用户：像碎了一半)；比过小宝石、下半颗、暗淡整颗，用户定这滴，和蜡封的一滴蜡同一个意思。glint 同 task_gem"""
    return (f'<svg {SVG} width="16" height="16" viewBox="0 0 16 16"><defs>{gem_defs("b")}'
            f'<mask id="g" maskUnits="userSpaceOnUse" x="0" y="0" width="16" height="16"><rect width="16" height="16" fill="#fff"/>'
            f'<path d="{drop_glint(8, top, h, w)}" fill="#000"/></mask></defs>'
            f'{_task_mount(TASK_MOUNT)}<path d="{drop_path(8, top, h, w)}" fill="url(#b)" mask="url(#g)"/>'
            + (f'<path d="{drop_glint(8, top, h, w)}" fill="{glint}"/>' if glint else "") + '</svg>')


# ---- 文件列表的飘落羽毛(第三十二版)：game-icons 剪影，印章套色——平涂骨白 + 右下错版一层淡金 + 印刷颗粒。
# 羽毛转平：羽根(笔管)在左、羽梢在右，CSS 再让它像钟摆一样左右摇。build.py feathers_css 按每根的远近栅格化成 WebP，CSS 只做位移 / 旋转。
# 用户：羽毛只要白色(一稿还有金色、整根红色)；红的改成白羽被血晕染，而且不要都在羽梢——羽梢 / 侧面 / 根部都有；
# 一种形状太死板 → 用户从八种候选(preview/羽毛形状候选.png)里挑了 F1 / F3 / F4
FEATHER_WHITE = ("#fffcf3", "#dcc596")
FEATHER_BLOOD = "#a3161f"
FEATHER_SHAPES = {   # 名字: (src/icons/gi 文件, 第几个子路径, 转平的角度, 转轴)——角度 = 像素主轴(PCA)转到水平、细的一头(羽根)朝左
    "curved": ("feather", 0, 39.8, (254.2, 201.7)),        # F1 弯羽，一侧缺刻(lorc feather)
    "broad": ("two-feathers", 0, 132.9, (334.5, 227.1)),    # F3 宽羽，一侧缺刻(lorc two-feathers 右边那根)
    "sweep": ("two-feathers", 1, 142.7, (171.6, 317.4)),    # F4 弯羽，只在根部缺刻(左边那根)
}


def feather_path(shape):
    name, i, _, _ = FEATHER_SHAPES[shape]
    subs = [t.strip() for t in re.split(r"(?=M)", " ".join(gi_paths(name))) if t.strip()]
    return subs[i]


def _feather_box(d, rot, c, off):
    """转平后的外框(取路径的端点和控制点，比实际曲线略大一点，够用)，再算上错版那一层的偏移"""
    import wings as W
    f = W.affine(rot, origin=c, to=c)
    pts = [f(q) for _, ps in W.parse(d) for q in ps]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return min(xs), min(ys), max(xs) + max(off[0], 0), max(ys) + max(off[1], 0)


def falling_feather(shape="curved", ink=None, stain=None, blur=0.0, px=40, off_k=1.0,
                    front=FEATHER_WHITE[0], back=FEATHER_WHITE[1], grain_px=22):
    """stain：None / "tip" 羽梢 / "root" 根部 / "side" 侧面一块——血从那里渗开，湍流位移把浓淡边界扭成水彩的毛边。
    blur：远处的羽毛烘进去的模糊(显示 px，按显示大小 px 换算)；off_k：错版那层偏移的倍数(近大远小，远处的「影子」贴得更近)。
    grain_px：颗粒按羽毛显示成多大来定粗细(一格颗粒 = 256 显示 px)，设计稿里 22 看着合适。
    viewBox 按转平后的外框取正方形(一稿固定 −20..532，转平后羽毛比框长，两头被裁)"""
    _, _, rot, c = FEATHER_SHAPES[shape]
    d = feather_path(shape)
    off = (14 * off_k, 10 * off_k)
    x0, y0, x1, y1 = _feather_box(d, rot, c, off)
    w, h = x1 - x0, y1 - y0
    L = max(w, h) * 1.04 + 4 * blur * max(w, h) / px
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    vx, vy = cx - L / 2, cy - L / 2
    tf = f"rotate({rot} {c[0]} {c[1]})"
    body = (f'<g transform="{tf}"><path transform="translate({off[0]:.1f} {off[1]:.1f})" d="{d}" fill="{back}"/>'
            f'<path d="{d}" fill="{front}"/></g>')
    defs = ""
    if stain:
        col = FEATHER_BLOOD
        stops = (f'<stop offset="0" stop-color="{col}" stop-opacity=".75"/><stop offset=".45" stop-color="{col}" stop-opacity=".4"/>'
                 f'<stop offset="1" stop-color="{col}" stop-opacity="0"/>')
        if stain == "tip":      # 从羽梢往里，到羽长一半淡到没有
            grad = f'<linearGradient id="st" gradientUnits="userSpaceOnUse" x1="{x1:.0f}" y1="0" x2="{x1 - w * .55:.0f}" y2="0">{stops}</linearGradient>'
        elif stain == "root":   # 从羽根往外
            grad = f'<linearGradient id="st" gradientUnits="userSpaceOnUse" x1="{x0:.0f}" y1="0" x2="{x0 + w * .5:.0f}" y2="0">{stops}</linearGradient>'
        else:                   # 侧面：上沿偏羽梢处洇开一块
            grad = (f'<radialGradient id="st" gradientUnits="userSpaceOnUse" cx="{x0 + w * .6:.0f}" cy="{y0 + h * .12:.0f}" r="{w * .38:.0f}">'
                    f'{stops}</radialGradient>')
        defs += (grad + f'<filter id="bl" x="-20%" y="-20%" width="140%" height="140%">'
                 f'<feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="3" seed="5"/>'
                 f'<feDisplacementMap in="SourceGraphic" scale="{L * .16:.0f}" xChannelSelector="R" yChannelSelector="G"/></filter>'
                 f'<clipPath id="fc"><path transform="{tf}" d="{d}"/></clipPath>')
        body += (f'<g clip-path="url(#fc)"><rect x="{vx - L * .1:.0f}" y="{vy - L * .1:.0f}" width="{L * 1.2:.0f}" height="{L * 1.2:.0f}" '
                 f'fill="url(#st)" filter="url(#bl)"/></g>')
    if ink:
        g = 256 * 512 / grain_px
        defs += (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="{g:.0f}" height="{g:.0f}">'
                 f'<image href="{ink}" width="{g:.0f}" height="{g:.0f}"/></pattern>'
                 f'<mask id="mk" maskUnits="userSpaceOnUse" x="{vx:.0f}" y="{vy:.0f}" width="{L:.0f}" height="{L:.0f}">'
                 f'<rect x="{vx:.0f}" y="{vy:.0f}" width="{L:.0f}" height="{L:.0f}" fill="url(#ip)"/></mask>')
        body = f'<g mask="url(#mk)">{body}</g>'
    if blur:
        defs += (f'<filter id="df" x="-10%" y="-10%" width="120%" height="120%">'
                 f'<feGaussianBlur stdDeviation="{blur * L / px:.1f}"/></filter>')
        body = f'<g filter="url(#df)">{body}</g>'
    return f'<svg {SVG} viewBox="{vx:.1f} {vy:.1f} {L:.1f} {L:.1f}"><defs>{defs}</defs>{body}</svg>'
