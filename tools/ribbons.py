# -*- coding: utf-8 -*-
"""绶带：用户给的两个绶带 SVG(素材库 Ribbons\\，疑似 frame-illust.com：可加工免费用，禁止当素材再分发——原文件不进仓库，
构建时从素材库读取、重新配色后内嵌)。
  f0208：正面一条宽带 + 两端燕尾飘带 + 卷边。H1 用它的两端(燕尾 + 卷边)，正面宽带改由 CSS 画(见 theme.src.css H1 一节)；
  f0215：中段宽带 + 两端打卷的 S 形环，新标签页题铭用(build.inscription_webp：渲染成位图后复制正中一列像素加长，
         矢量切三块拉伸在 f0215 上会起台阶、露接缝)。
配色(第四版，用户：太生硬、没有羊皮纸的古旧感、正反面颜色不对)：
  f0208 原图所有部件是同一种米色材质、只靠明暗区分 → 全部羊皮纸色，亮面浅、卷到后面背光的部分逐级加深；
  f0215 原图是米色正面 + 绿色里衬 → 照原图的正反面关系：米色部分 = 羊皮纸，绿色里衬 = 暗旧的红(第三版把环的背面也涂红了，正反面错)。
相邻同色部件之间原图留着一丝描边色的细缝，拉宽 / 缩小后像拼接缝：每块再描一道同色细边把缝合上(真正的轮廓线靠垫底的整体剪影 p0)。
"""
import re
from pathlib import Path

SRC = Path(r"E:\AI工作\素材库\Ribbons")
SVG = 'xmlns="http://www.w3.org/2000/svg"'

# 部件编号见 DEVELOPMENT.md(拆解图)。f0208：p0 整体剪影(描边色垫底) / p9 正面宽带 / p2 p6 燕尾 / p4 p8 卷到后面的一段 /
# p1 p5 卷边里侧 / p3 p7 燕尾根部小折角
F0208_ROLES = {0: "outline", 9: "face", 2: "face", 6: "face", 4: "back", 8: "back", 1: "curl", 5: "curl", 3: "fold", 7: "fold"}
# f0215：p0 剪影 / p8 中段宽带 / p2 p10 S 形环正面 / p4 p12 环的后半(米色) / p5 p13 下卷 / p6 p14 尾端 / 绿色里衬 p1 p9 p3 p11 / 小卷芯 p7 p15
F0215_ROLES = {0: "outline", 8: "face", 2: "face", 10: "face", 4: "back", 12: "back", 5: "face2", 13: "face2",
               6: "face2", 14: "face2", 1: "lining", 9: "lining", 3: "lining", 11: "lining", 7: "lining2", 15: "lining2"}

PARCHMENT = {"outline": "#6a4a2c", "face": "#f0e2c2", "face2": "#e6d4ae", "back": "#d9c398", "curl": "#c6aa79",
             "fold": "#a98b5a", "lining": "#8f2c27", "lining2": "#6e1f1c"}
# H1 横幅正面宽带的配色(CSS 用，和上面同一套)
BAND_TOP, BAND_BOTTOM, BAND_LINE = "#f3e7cb", "#e8d5ae", "#6a4a2c"
# 套色印章版(第八版，用户：缎带试试和新标签页徽章一样的色块印章效果，不要实线描边，对比一下)：
# 不画深色整体剪影 p0、也不描同色封缝边——原图各部件之间本来就隔着一道描边宽的缝，去掉 p0 之后缝里透出纸色，
# 正好就是印章套色的留白线；没有了外轮廓线，色块要比纸面深一档才立得住，所以整套颜色压深(偏赭的旧羊皮纸)；
# 纹理换成徽章同一种印刷颗粒(亮度遮罩，颗粒处透出纸色)
STAMP = {"face": "#e2cb98", "face2": "#d8bf8a", "back": "#cdb07a", "curl": "#bf9f68",
         "fold": "#a6844f", "lining": "#9a3330", "lining2": "#7d2626"}
BAND_STAMP = STAMP["face"]


def _paths(name):
    src = (SRC / f"{name}.svg").read_text(encoding="utf-8")
    return [d for _, d in re.findall(r'<path class="(st\d+)" d="([^"]+)"', src, re.S)]


def _body(name, skip=(), pal=PARCHMENT, stamp=False):
    roles = F0208_ROLES if name.startswith("f0208") else F0215_ROLES
    if stamp:
        pal, skip = STAMP, tuple(skip) + (0,)
    out = []
    for i, d in enumerate(_paths(name)):
        if i in skip:
            continue
        r = roles[i]
        col = pal[r]
        seal = "" if r == "outline" or stamp else f' stroke="{col}" stroke-width=".7" stroke-linejoin="round"'
        out.append(f'<path d="{d}" fill="{col}"{seal}/>')
    return "".join(out)


def _ink_mask(ink, x, y, w, h, cell):
    """印刷颗粒的亮度遮罩(cell = 一格颗粒图在这张图里的单位数)"""
    return (f'<pattern id="ip" patternUnits="userSpaceOnUse" width="{cell:g}" height="{cell:g}">'
            f'<image href="{ink}" width="{cell:g}" height="{cell:g}"/></pattern>'
            f'<mask id="mk" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#ip)"/></mask>')


# ---- H1 两端：f0208 去掉正面宽带(p9)，左端取 x 0–200、右端取 x 600–800(原图左右对称)。
# 原图正面宽带左端在 x≈151、下沿在 y≈83.5(卷边从这里往下卷到 y≈121)；CSS 宽带的左边贴在 TAIL_BAND_X、下沿贴在 TAIL_BAND_Y
F0208_H = 123.8
TAIL_W = 200          # 端头图宽(原图单位)
TAIL_BAND_X = 151     # 宽带左端在端头图里的 x
TAIL_BAND_Y = 83.5    # 宽带下沿
TAIL_OVERLAP = 1      # 下段卷边往上多带的高度(CSS px)，和 theme.src.css 里 tail-*-bot 的 + 1px 一致


def _tex_defs(tex, speck, k=1.0):
    """斑驳纹理的两个 pattern(tex 512 一格、speck 96 一格；k = 这张图 1 个单位对应几 px 的倒数，按图里的单位放大)"""
    if not tex:
        return ""
    out = (f'<pattern id="tx" patternUnits="userSpaceOnUse" width="{512 * k:g}" height="{512 * k:g}">'
           f'<image href="{tex}" width="{512 * k:g}" height="{512 * k:g}"/></pattern>')
    if speck:
        out += (f'<pattern id="sp" patternUnits="userSpaceOnUse" width="{96 * k:g}" height="{96 * k:g}">'
                f'<image href="{speck}" width="{96 * k:g}" height="{96 * k:g}"/></pattern>')
    return out


def _tex_fill(speck):
    return '<rect width="100%" height="100%" fill="url(#tx)"/>' + ('<rect width="100%" height="100%" fill="url(#sp)"/>' if speck else "")


def tail(side="left", tex=None, speck=None, ts=0.55, ink=None, part=None):
    """tex / speck：斑驳纹理的 data URI(build.py 传进来)；ts = CSS 里端头图的缩放(纹理按它换算，和宽带上的纹理一样大)。
    纹理只铺在剪影(p0)里面；剪影边缘再压几道很淡的深色描边，边缘旧一点。
    ink：给了就画套色印章版(见 STAMP)，颗粒一格 = 256 CSS px
    part(第三十七版，用户：一级标题占了多行，两边的缎带也要一起加高；只做套色印章版)：在宽带下沿 TAIL_BAND_Y 横切成两段——
      "top"：燕尾旗面 + 折到宽带后面的一段，CSS 里纵向拉到宽带下角那么高。外层 SVG 不设 viewBox(单位 = CSS px，颗粒按 256px 一格铺，
             不跟着拉长)，里面套一层 viewBox + preserveAspectRatio="none" 只拉伸图形；
      "bottom"：宽带下沿往下垂的卷边，原尺寸，CSS 里贴在框底(高 = 卷边区 --ba-td)"""
    x0 = 0 if side == "left" else 800 - TAIL_W
    if ink and part == "top":
        return (f'<svg {SVG} width="100%" height="100%"><defs>{_ink_mask(ink, 0, 0, "100%", "100%", 256)}</defs>'
                f'<g mask="url(#mk)"><svg width="100%" height="100%" viewBox="{x0} 0 {TAIL_W} {TAIL_BAND_Y}" preserveAspectRatio="none">'
                f'{_body("f0208_0", skip=(9,), stamp=True)}</svg></g></svg>')
    if ink and part == "bottom":
        # 接缝(1.0.2，用户：一级标题缎带左右两边有横线裂缝)：上下两段正好在宽带下沿碰头，125% 缩放下接缝落在半个物理像素上时
        # 两段边缘各画一半透明，透出底色成一道横线。下段往上多带 TAIL_OVERLAP 个 CSS px 的图形(CSS 里高度同样加这么多，比例不变)，
        # 垫在上段后面(背景叠放上段在上)，接缝处有缝也透不出底色
        h = round(F0208_H - TAIL_BAND_Y, 2)
        ov = round(TAIL_OVERLAP / ts, 3)
        y0, hh = round(TAIL_BAND_Y - ov, 3), round(h + ov, 3)
        return (f'<svg {SVG} viewBox="{x0} {y0} {TAIL_W} {hh}"><defs>'
                f'<clipPath id="c"><rect x="{x0}" y="{y0}" width="{TAIL_W}" height="{hh}"/></clipPath>'
                f'{_ink_mask(ink, x0, 0, TAIL_W, F0208_H, 256 / ts)}</defs>'
                f'<g clip-path="url(#c)"><g mask="url(#mk)">{_body("f0208_0", skip=(9,), stamp=True)}</g></g></svg>')
    if ink:
        return (f'<svg {SVG} viewBox="{x0} 0 {TAIL_W} {F0208_H}"><defs>'
                f'<clipPath id="c"><rect x="{x0}" y="0" width="{TAIL_W}" height="{F0208_H}"/></clipPath>'
                f'{_ink_mask(ink, x0, 0, TAIL_W, F0208_H, 256 / ts)}</defs>'
                f'<g clip-path="url(#c)"><g mask="url(#mk)">{_body("f0208_0", skip=(9,), stamp=True)}</g></g></svg>')
    body = _body("f0208_0", skip=(9,))
    sil = _paths("f0208_0")[0]
    k = 1 / ts
    edge = "".join(f'<path d="{sil}" fill="none" stroke="#5b3f26" stroke-width="{w * k:.2f}" stroke-opacity="{o}"/>'
                   for w, o in ((9, .035), (5, .04), (2.6, .05)))
    tex_layer = (f'<g clip-path="url(#s)"><rect x="{x0}" y="0" width="{TAIL_W}" height="{F0208_H}" fill="url(#tx)"/>'
                 + (f'<rect x="{x0}" y="0" width="{TAIL_W}" height="{F0208_H}" fill="url(#sp)"/>' if speck else "")
                 + edge + "</g>") if tex else ""
    return (f'<svg {SVG} viewBox="{x0} 0 {TAIL_W} {F0208_H}">'
            f'<defs><clipPath id="c"><rect x="{x0}" y="0" width="{TAIL_W}" height="{F0208_H}"/></clipPath>'
            f'<clipPath id="s"><path d="{sil}"/></clipPath>{_tex_defs(tex, speck, k)}</defs>'
            f'<g clip-path="url(#c)">{body}{tex_layer}</g></svg>')


def ribbon(name="f0215_0", stamp=False):
    vb_h = F0208_H if name.startswith("f0208") else 164.3
    return f'<svg {SVG} viewBox="0 0 800 {vb_h}">{_body(name, stamp=stamp)}</svg>'


# ---- H1 正面宽带(第六版)。一张不定尺寸的 SVG(CSS background-size 拉到宽带盒大小)，没有切块拼接：
# 上下沿 = 往下垂的平缓弧线(第五版，用户嫌纯长方形突兀)；两端 = 弧线(第六版，用户：两边还是直线)；
# 第五版的描边比两端燕尾粗一倍、上沿描边在斜切的角上戳出去一截——现在所有描边都用宽带形状做遮罩，只留宽带里面那一半，
# 粗细 = bw(和燕尾的描边一样细)，也不会戳出去。
# 每条边都是一个椭圆，几何属性写成 CSS(cx/cy/rx/ry 支持 % 和 calc)，弧线的深浅按固定像素算，宽带拉多长、多高都一样：
#   上沿 T：横半径 62.5% 宽(只取中段)，圆心在盒子上方 1.5×sag、纵半径 2.5×sag → 两端在 y=0，正中垂到 y=sag；
#   下沿 B：同理，两角在 100%−sag，正中贴底；
#   两端 L / R：外凸的弧线，往上收进 end px 到上角。第七版(用户：两端弧线和下面卷边的弧度对不上)：
#   第六版椭圆最外侧(竖直切线)正好在下角，下面的卷边却是斜着往外再卷回来，接口处折了一下。现在椭圆最外侧挪到下角下面
#   (圆心在下角往下 drop × 宽带高)，下角处的弧线已经斜着往外走(单行标题约 0.16)，顺势接进卷边的圆角，
#   宽带端头 + 卷边连成一道弧；越往上越弯，收进 end px 到上角。纵半径 = k × 圆心到上沿的距离，横半径由 end 算出。
#   参数的限制：端头图(f0208 去掉正面宽带)在原宽带的位置垫着深色整体剪影 p0，原图宽带端头是斜度 0.23 的直线、高 29px(单行时)；
#   弧线在下角往上 29px 以内必须在这条斜线左边(盖住它)，否则露出一条深色细缝——end 12 / k 1.06 / drop 2 时 29px 处收进 6.2px(原斜线 6.6)。
#   标题越高、弧线越直，越盖得住
# 宽带形状 = 三个遮罩相交(上下沿一个、左端一个、右端一个；分开做是因为宽带很窄时左右两端的椭圆会互相盖到对方那边)。
# 边缘做旧：几道越来越宽、越来越淡的深褐描边(同样只留里面一半)；最上面铺斑驳纹理
def band_svg(sag=7, end=12, bw=.95, tex=None, speck=None, line=None, top=BAND_TOP, bottom=BAND_BOTTOM, k=1.06, drop=2.0,
             ink=None):
    """ink：给了就画套色印章版——平涂 BAND_STAMP、不描边，叠印刷颗粒"""
    import math
    line = line or BAND_LINE
    s = sag
    uc, ut = drop / (k * (1 + drop)), 1 / k        # 下角 / 上角在椭圆上的纵向位置(占纵半径的比例，都在圆心上方)
    erx = end / (math.sqrt(1 - uc ** 2) - math.sqrt(1 - ut ** 2))
    ecx = erx * math.sqrt(1 - uc ** 2)             # 圆心横坐标：让下角正好落在宽带盒左边
    T = f"cx:50%;cy:{-1.5 * s}px;rx:62.5%;ry:{2.5 * s}px"
    B = f"cx:50%;cy:calc(100% - {2.5 * s}px);rx:62.5%;ry:{2.5 * s}px"
    f = 1 + drop
    ecy = f"calc({f * 100:g}% - {f * s:g}px)"
    ery = f"calc({k * f * 100:g}% - {k * f * s:g}px)"
    L = f"cx:{ecx:.2f}px;cy:{ecy};rx:{erx:.2f}px;ry:{ery}"
    R = f"cx:calc(100% - {ecx:.2f}px);cy:{ecy};rx:{erx:.2f}px;ry:{ery}"
    sw = ecx                                       # 遮罩 / 裁剪用的端头条带宽度(下角到圆心)
    full = '<rect width="100%" height="100%" fill="#fff"/>'
    mu = 'maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"'

    def edges(w, op):
        st = f'fill="none" stroke="{line}" stroke-width="{w:g}"' + (f' stroke-opacity="{op}"' if op < 1 else "")
        return (f'<ellipse style="{T}" {st}/>'
                f'<ellipse style="{B}" {st} clip-path="url(#kb)"/>'
                f'<ellipse style="{L}" {st} clip-path="url(#kl)"/>'
                f'<ellipse style="{R}" {st} clip-path="url(#kr)"/>')

    return (f'<svg {SVG}><defs>'
            f'<linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset=".55" stop-color="#ecdcba"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
            f'<mask id="mtb" {mu}>{full}<ellipse style="{T}" fill="#000"/>'
            f'<rect style="x:0;y:calc(100% - {s}px);width:100%;height:{s}px" fill="#000"/><ellipse style="{B}" fill="#fff"/></mask>'
            f'<mask id="ml" {mu}>{full}<rect style="x:0;y:0;width:{sw:.2f}px;height:100%" fill="#000"/><ellipse style="{L}" fill="#fff"/></mask>'
            f'<mask id="mr" {mu}>{full}<rect style="x:calc(100% - {sw:.2f}px);y:0;width:{sw:.2f}px;height:100%" fill="#000"/>'
            f'<ellipse style="{R}" fill="#fff"/></mask>'
            # 描边的取舍：下沿椭圆的上半圈、两端椭圆的内侧半圈都落在宽带里面，只留贴边的那一段
            f'<clipPath id="kb"><rect style="x:0;y:calc(100% - {s + 9}px);width:100%;height:{s + 9}px"/></clipPath>'
            f'<clipPath id="kl"><rect style="x:0;y:0;width:{sw:.2f}px;height:100%"/></clipPath>'
            f'<clipPath id="kr"><rect style="x:calc(100% - {sw:.2f}px);y:0;width:{sw:.2f}px;height:100%"/></clipPath>'
            f'{_tex_defs(tex, speck)}'
            + (_ink_mask(ink, 0, 0, "100%", "100%", 256) if ink else "")
            + '</defs>'
            f'<g mask="url(#ml)"><g mask="url(#mr)"><g mask="url(#mtb)">'
            + (f'<rect width="100%" height="100%" fill="{BAND_STAMP}" mask="url(#mk)"/>' if ink else
               '<rect width="100%" height="100%" fill="url(#f)"/>'
               + (_tex_fill(speck) if tex else "")
               + edges(14, .035) + edges(8, .04) + edges(4, .05)
               + edges(bw * 2, 1))
            + '</g></g></g></svg>')
