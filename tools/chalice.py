# -*- coding: utf-8 -*-
"""大纲「血线」模式的圣杯图标(第四十版)：Lorc 的 chalice-drops(game-icons.net，CC BY 3.0，src/icons/gi/chalice-drops.svg)
改成主题的套色两色(金杯 + 圣血红，色块之间留纸色缝)：
  parent    有子项的标题：金杯 + 正中一滴血(用户：两侧的血滴去掉，只留中间这一滴；血滴和杯子分不清 → 血滴悬在杯口上方、
            中间一道看得出的纸缝，血色压深一档。原大的细长血滴缩小后像烛火，放大加宽到看得出圆底)
  collapsed 折叠起来的父级：杯里盛满血(杯口椭圆填红)，血滴照旧
  leaf      没有子项的标题：同一只杯，去掉血滴，只掏空杯身，杯口内沿补一道弧。杯梗最细处只有 1.5px，两边各 1.1px 的壁放不下，
            杯梗 / 杯脚保持实心(连杯脚一起掏空缩小后像沙漏)。用户问过杯梗为什么不镂空，比过五稿试装了 D(杯梗两侧各加粗 0.45px、
            整只按 0.8px 壁厚掏空)，实机看太淡，退回只掏空杯身
几何用 shapely 在原图 512 坐标里算：path 先展平成多边形(三次贝塞尔按固定步数采样)，原图三个环 =
外轮廓(杯 + 左、中两滴连在一起) / 右边那滴 / 杯口椭圆的镂空。正中那滴和左滴、杯口粘连，取不干净，
改用右边那滴(轮廓最完整的一滴)放大挪到杯的中轴上。
所有图标同宽、同一条中轴，build.py outline_css 用 icons() 给的尺寸定位：图标挂在文字左边，杯的中轴在文字起点左边 13px。
"""
import math
import re
from pathlib import Path

from shapely.affinity import scale as sscale, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import ornaments as O

SRC = Path(__file__).resolve().parent.parent / "src" / "icons" / "gi" / "chalice-drops.svg"
U = 29.0            # 原图单位 / CSS px：杯高约 12.3px(33 时图标比字小)
AX, RIM_CY = 258.0, 195.0               # 杯的中轴、杯口椭圆中心
RIM_OUT = (127, 53)                      # 外杯口(略放大，吞掉杯口边)
RIM_IN = (104, 27)                       # 杯口镂空 = 原图第三个环的外包椭圆
CUP_TOP, CUP_BOTTOM = 141, 498           # 杯(含杯口)的上下沿，留 3 单位边
CUP_CY = (145 + 496) / 2                 # 杯身竖向中点 → 对齐行中线
BOWL_BOTTOM = 330                        # 叶子只掏空这条线以上(杯身)
WALL = 1.1 * U                           # 叶子杯壁厚
GAP = 20                                 # 血滴和杯之间的纸缝(单位，约 0.7px；原来 9 单位 = 0.3px，缩小后看不出缝)
DROP_K, DROP_WX = 1.5, 1.5               # 血滴相对右滴原大的倍数、横向再加宽的倍数(约 4 × 5.5px)
FILL_GAP = 8                             # 折叠时杯口里的血和杯沿之间的缝(杯口只有 1.9px 高，留 GAP 那么宽血就只剩一条线)
# 血滴的红：比主题通用的血色(O.blood_defs，#c2232c → #a8171f)深一档，和缎面金拉开明度
DROP_RED = ("#a91a23", "#850f16")


def _flatten(d, steps=24):
    """path → 子路径点列(M L H V C S Q T A Z，绝对 / 相对都行；曲线按固定步数采样)。
    圆弧的两个标志位 game-icons 常常和后面的数连写(「a9 9 0 011.5 2」= 0、1、1.5)，读标志时只取一个字符"""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", d)
    rings, ring = [], []
    cur = start = (0.0, 0.0)
    prev_c = None            # 上一段三次 / 二次曲线的第二控制点(S / T 反射用)
    cmd, i = None, 0

    def num():
        nonlocal i
        i += 1
        return float(toks[i - 1])

    def flag():
        nonlocal i
        t = toks[i]
        if len(t) == 1:
            i += 1
        else:
            toks[i] = t[1:]
        return t[0] == "1"

    def arc(p0, rx, ry, phi, large, sweep, p1):
        """SVG 端点式圆弧 → 圆心式(规范 F.6.5)，按角度采样"""
        if p0 == p1:
            return []
        if rx == 0 or ry == 0:
            return [p1]
        rx, ry = abs(rx), abs(ry)
        c, s_ = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
        x1, y1 = c * dx + s_ * dy, -s_ * dx + c * dy
        lam = (x1 / rx) ** 2 + (y1 / ry) ** 2
        if lam > 1:
            rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
        num_ = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
        k = math.sqrt(max(0.0, num_ / (rx * rx * y1 * y1 + ry * ry * x1 * x1))) * (-1 if large == sweep else 1)
        cx1, cy1 = k * rx * y1 / ry, -k * ry * x1 / rx
        cx, cy = c * cx1 - s_ * cy1 + (p0[0] + p1[0]) / 2, s_ * cx1 + c * cy1 + (p0[1] + p1[1]) / 2
        ang = lambda ux, uy: math.atan2(uy, ux)
        t0 = ang((x1 - cx1) / rx, (y1 - cy1) / ry)
        dt = ang((-x1 - cx1) / rx, (-y1 - cy1) / ry) - t0
        if sweep and dt < 0:
            dt += 2 * math.pi
        elif not sweep and dt > 0:
            dt -= 2 * math.pi
        out = []
        for j in range(1, steps + 1):
            t = t0 + dt * j / steps
            out.append((cx + rx * math.cos(t) * c - ry * math.sin(t) * s_, cy + rx * math.cos(t) * s_ + ry * math.sin(t) * c))
        return out

    def bez(pts):
        n = len(pts) - 1
        out = []
        for k in range(1, steps + 1):
            t = k / steps
            q = list(pts)
            for r in range(n):
                q = [(q[j][0] + (q[j + 1][0] - q[j][0]) * t, q[j][1] + (q[j + 1][1] - q[j][1]) * t) for j in range(len(q) - 1)]
            out.append(q[0])
        return out

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if ring:
                    rings.append(ring)
                ring, cur, prev_c = [], start, None
                continue
        rel = cmd.islower()
        C = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if C == "M":
            if ring:
                rings.append(ring)
            cur = start = (ox + num(), oy + num())
            ring, prev_c = [cur], None
            cmd = "l" if rel else "L"          # M 后面接着的坐标对按 L 处理
        elif C == "L":
            cur = (ox + num(), oy + num())
            ring.append(cur)
            prev_c = None
        elif C == "H":
            cur = ((cur[0] if rel else 0) + num(), cur[1])
            ring.append(cur)
            prev_c = None
        elif C == "V":
            cur = (cur[0], (cur[1] if rel else 0) + num())
            ring.append(cur)
            prev_c = None
        elif C in "CS":
            if C == "C":
                c1 = (ox + num(), oy + num())
            else:
                c1 = (2 * cur[0] - prev_c[0], 2 * cur[1] - prev_c[1]) if prev_c else cur
            c2 = (ox + num(), oy + num())
            end = (ox + num(), oy + num())
            ring += bez([cur, c1, c2, end])
            cur, prev_c = end, c2
        elif C in "QT":
            if C == "Q":
                c1 = (ox + num(), oy + num())
            else:
                c1 = (2 * cur[0] - prev_c[0], 2 * cur[1] - prev_c[1]) if prev_c else cur
            end = (ox + num(), oy + num())
            ring += bez([cur, c1, end])
            cur, prev_c = end, c1
        elif C == "A":
            rx, ry, phi = num(), num(), num()
            large, sweep = flag(), flag()
            end = (ox + num(), oy + num())
            ring += arc(cur, rx, ry, phi, large, sweep, end)
            cur, prev_c = end, None
    if ring:
        rings.append(ring)
    return [r for r in rings if len(r) > 6]


def _ellipse(c, ab):
    return sscale(Point(c).buffer(1, 64), ab[0], ab[1])


def _left_at(g, y):
    ln = LineString([(-10, y), (600, y)]).intersection(g)
    return min(s.bounds[0] for s in getattr(ln, "geoms", [ln]) if not s.is_empty)


def _d(g, tol=0.6):
    out = []
    for p in getattr(g.simplify(tol), "geoms", [g.simplify(tol)]):
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            out.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in list(ring.coords)[:-1]) + "Z")
    return "".join(out)


def _geometry(gap=GAP, drop_k=DROP_K, drop_wx=DROP_WX, drop_bottom=None):
    d = re.findall(r'<path[^>]*\sd="([^"]+)"', SRC.read_text(encoding="utf-8"))[0]
    r0, r1, _ = (Polygon(r).buffer(0) for r in _flatten(d))
    cup_solid = unary_union([r0.intersection(box(0, RIM_CY, 512, 512)), _ellipse((AX, RIM_CY), RIM_OUT)])
    opening = _ellipse((AX, RIM_CY), RIM_IN)
    # 右滴放大、挪到中轴上，圆底悬在外杯口上方一道缝(drop_bottom 给了就落在那里，比如落进杯口)
    x0, y0, x1, y1 = r1.bounds
    drop = sscale(r1, drop_k * drop_wx, drop_k, origin=((x0 + x1) / 2, y1))
    if drop_bottom is None:
        drop_bottom = RIM_CY - RIM_OUT[1] - gap
    drop = translate(drop, AX - (x0 + x1) / 2, drop_bottom - y1)
    gold = cup_solid.difference(opening).difference(drop.buffer(gap))
    red_fill = opening.buffer(-FILL_GAP).difference(drop.buffer(gap))   # 折叠：杯口里盛满的血
    # 叶子：杯口用干净的椭圆，只掏空杯身
    leaf_cup = unary_union([r0.intersection(box(0, RIM_CY, 512, 512)), _ellipse((AX, RIM_CY), (123, 50))])
    hollow = leaf_cup.difference(leaf_cup.buffer(-WALL, join_style=1).intersection(box(0, 0, 512, BOWL_BOTTOM)))
    rim_low = _ellipse((AX, RIM_CY), RIM_IN).exterior.intersection(box(0, RIM_CY, 512, 512)).buffer(WALL * 0.42, cap_style=2)
    leaf = unary_union([hollow, rim_low.intersection(leaf_cup)])
    return dict(gold=gold, red_fill=red_fill, drop=drop, leaf=leaf, cup=cup_solid)


def _svg(vb, layers):
    defs = O.gold_defs("g") + (f'<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{DROP_RED[0]}"/>'
                               f'<stop offset="1" stop-color="{DROP_RED[1]}"/></linearGradient>')
    body = "".join(f'<path d="{_d(g)}" fill="url(#{f})"/>' for g, f in layers if not g.is_empty)
    return f'<svg {O.SVG} viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}"><defs>{defs}</defs>{body}</svg>'


def icons(**kw):
    """{名字: {svg, w, h, axis, mid, bottom}} + 公共的 contact。单位 CSS px：
    w / h 盒子宽高；axis 杯中轴离盒子左缘；mid 行中线(杯身竖向中点)离盒子顶；bottom 盒子底离行中线；
    contact = 行中线高度上杯身左缘离盒子左缘(血线拐角停在这里，所有图标同一个值)"""
    g = _geometry(**kw)
    cx0 = g["cup"].bounds[0] - 4
    w = 2 * (AX - cx0)
    top = min(CUP_TOP, g["drop"].bounds[1] - 3)
    out = {}

    def put(name, layers, y0):
        vb = (cx0, y0, w, CUP_BOTTOM - y0)
        out[name] = {"svg": _svg(vb, layers), "w": vb[2] / U, "h": vb[3] / U, "axis": (AX - cx0) / U,
                     "mid": (CUP_CY - y0) / U, "bottom": (CUP_BOTTOM - CUP_CY) / U}
    put("parent", [(g["gold"], "g"), (g["drop"], "b")], top)
    put("collapsed", [(g["gold"], "g"), (g["red_fill"], "b"), (g["drop"], "b")], top)
    put("leaf", [(g["leaf"], "g")], CUP_TOP)
    out["contact"] = (_left_at(g["cup"], CUP_CY) - cx0) / U
    return out
