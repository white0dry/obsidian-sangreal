# -*- coding: utf-8 -*-
"""圣血天使战团徽：照用户给的参考图(红底黑徽，1080px)描成矢量，存 src/icons/ba-emblem.svg。
第一版用的 wh_icons 版本血滴往右偏了 33/956、比例也和标准徽记不同，用户指出后改成描参考图。
三块按连通域分开：wing-l / wing-r / drop；右翼直接用左翼镜像(保证严格对称)，血滴按自身中线左右对称化，
再整体以双翼的中线居中。
用法: python tools/trace_emblem.py [参考图路径]
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"E:\AI工作\素材库\参考图\Bloodangelsymbol.webp")
UP = 4            # 放大后再描，曲线更顺
EPS = 1.2         # 折线容差(放大后的像素)

rgb = np.asarray(Image.open(SRC).convert("RGB")).astype(np.int32)
ink = ((rgb[:, :, 0] < 100) & (rgb[:, :, 1] < 100)).astype(np.uint8)       # 黑徽(底色是红)
ink = cv2.resize(ink * 255, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
ink = (cv2.GaussianBlur(ink.astype(np.float32), (0, 0), UP * 0.9) > 127).astype(np.uint8)
n, lab, st, ce = cv2.connectedComponentsWithStats(ink)
parts = sorted([i for i in range(1, n) if st[i, 4] > 1000 * UP * UP], key=lambda i: ce[i][0])
assert len(parts) == 3, f"应有 3 块，找到 {len(parts)}"
left, drop, right = parts
H, W = ink.shape
x_l0 = st[left, 0]
x_r1 = st[right, 0] + st[right, 2]
axis = (x_l0 + x_r1) / 2                                   # 双翼外缘的中线
print(f"双翼中线 {axis / UP:.1f}，血滴中心 {ce[drop][0] / UP:.1f}，右翼外缘对称差 {((x_r1 - axis) - (axis - x_l0)) / UP:.1f}px")


def contour_d(mask, mirror_about=None):
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, EPS, True)[:, 0, :].astype(float)
    if mirror_about is not None:
        c[:, 0] = 2 * mirror_about - c[:, 0]
        c = c[::-1]
    return c


wl = contour_d((lab == left).astype(np.uint8))
wr = contour_d((lab == left).astype(np.uint8), mirror_about=axis)
# 血滴：左半边镜像拼成严格对称(按双翼中线)
dm = (lab == drop).astype(np.uint8)
xs = np.arange(W)[None, :]
half = dm * (xs <= axis)
# 手工镜像：把左半边按 axis 翻到右边
flip = np.zeros_like(dm)
ys_, xs_ = np.nonzero(half)
xm = np.round(2 * axis - xs_).astype(int)
ok = (xm >= 0) & (xm < W)
flip[ys_[ok], xm[ok]] = 1
dsym = cv2.morphologyEx(np.maximum(half, flip), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
dd = contour_d(dsym)

allpts = np.vstack([wl, wr, dd])
x0, y0 = allpts.min(0)
x1, y1 = allpts.max(0)
pad = 4 * UP
S = 1 / UP


def fmt(c):
    return "M" + " L".join(f"{(x - x0 + pad) * S:.1f},{(y - y0 + pad) * S:.1f}" for x, y in c) + "Z"


vw, vh = (x1 - x0 + 2 * pad) * S, (y1 - y0 + 2 * pad) * S
out = ROOT / "src" / "icons" / "ba-emblem.svg"
out.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.1f} {vh:.1f}">\n<g transform="">\n'
               f'<path id="drop" d="{fmt(dd)}"/>\n<path id="wing-l" d="{fmt(wl)}"/>\n<path id="wing-r" d="{fmt(wr)}"/>\n</g>\n</svg>\n',
               encoding="utf-8")
print(out, f"viewBox 0 0 {vw:.1f} {vh:.1f}", "points", len(wl), len(wr), len(dd))
