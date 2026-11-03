# -*- coding: utf-8 -*-
"""给只有常规体的 TrueType 字体做一个加粗版(第十七版，用户很喜欢 IM Fell English SC 的质感，问有没有粗体——
Fell Types 复刻本来就只有常规 / 斜体 / 小型大写)。算法照 FreeType 的 FT_Outline_EmboldenXY：每个轮廓点沿两条邻边的
角平分线往外推 strength / 2(转角太尖时按邻边长度限幅，免得细笔画塌缩)，相当于把笔画整体加宽 strength。
加宽后字形右移 strength / 2、步进宽度 + strength，左右字距不变；竖直方向上下各长 strength / 2。
和浏览器的 -webkit-text-stroke(渲染时描一圈边，小字号发糊)不同，这是直接改字形轮廓，渲染和原字一样清楚。
用法: python tools/embolden.py 源.woff2 输出.woff2 strength(字体单位) [新家族名]
"""
import sys
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont


def _shift(c, s, tt):
    """一个闭合轮廓的点 → 每点的位移(FreeType 的公式，s = 半宽)"""
    prev, nxt = np.roll(c, 1, axis=0), np.roll(c, -1, axis=0)
    vin, vout = c - prev, nxt - c
    lin, lout = np.hypot(*vin.T), np.hypot(*vout.T)
    ok = (lin > 0) & (lout > 0)
    vin = np.where(ok[:, None], vin / np.maximum(lin, 1e-9)[:, None], 0)
    vout = np.where(ok[:, None], vout / np.maximum(lout, 1e-9)[:, None], 0)
    d = (vin * vout).sum(1)
    sh = np.stack([vin[:, 1] + vout[:, 1], vin[:, 0] + vout[:, 0]], 1)
    q = vout[:, 0] * vin[:, 1] - vout[:, 1] * vin[:, 0]
    if tt:
        sh[:, 0] = -sh[:, 0]
        q = -q
    else:
        sh[:, 1] = -sh[:, 1]
    d1 = d + 1
    l = np.minimum(lin, lout)
    k = np.where(s * q <= l * d1, s / np.maximum(d1, 1e-9), l / np.where(q == 0, 1e-9, q))
    sh = sh * k[:, None]
    sh[(d <= -0.9375) | ~ok] = 0
    return sh


def embolden(src, dst, strength, family=None):
    f = TTFont(src)
    glyf, hmtx = f["glyf"], f["hmtx"]
    s = strength / 2
    w = int(round(strength))
    for name in f.getGlyphOrder():
        g = glyf[name]
        adv, lsb = hmtx[name]
        if g.isComposite() or g.numberOfContours <= 0:   # 组合字形的部件各自已经右移过 s，只加步进
            hmtx[name] = (adv + w, lsb)
            continue
        pts = np.array(g.coordinates, float)
        ends = list(g.endPtsOfContours)
        area, start = 0.0, 0
        for e in ends:                          # 整个字形的有向面积：负 = 外轮廓顺时针 = TrueType 方向
            c = pts[start:e + 1]
            area += (c[:, 0] * np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1) * c[:, 1]).sum()
            start = e + 1
        tt = area < 0
        out, start = pts.copy(), 0
        for e in ends:
            c = pts[start:e + 1]
            out[start:e + 1] = c + _shift(c, s, tt)
            start = e + 1
        out[:, 0] += s
        g.coordinates = type(g.coordinates)([(int(round(x)), int(round(y))) for x, y in out])
        g.recalcBounds(glyf)
        hmtx[name] = (adv + w, g.xMin)
    f["OS/2"].usWeightClass = 700
    if family:
        for r in f["name"].names:
            if r.nameID in (1, 16):
                r.string = family
            elif r.nameID == 2:
                r.string = "Bold"
            elif r.nameID == 3:
                r.string = f"{family} Bold; emboldened +{strength:g}"
            elif r.nameID == 4:
                r.string = f"{family} Bold"
            elif r.nameID == 6:
                r.string = family.replace(" ", "") + "-Bold"
    f.flavor = "woff2" if str(dst).endswith(".woff2") else None
    f.save(dst)
    return Path(dst).stat().st_size


if __name__ == "__main__":
    a = sys.argv[1:]
    print(embolden(a[0], a[1], float(a[2]), a[3] if len(a) > 3 else None))
