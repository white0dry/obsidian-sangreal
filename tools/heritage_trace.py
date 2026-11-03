# -*- coding: utf-8 -*-
"""把 Heritage Library 版画线稿(3000px 黑线透明底 PNG)描成矢量 path，存素材库 Heritage Library\_描线\<名>.svg。
两种描法：
  ink  = 墨线本身(内部留白保留成窟窿 → 扁平但带版画刻线感)，适合本来就是粗墨块的对象(纹章双翼)
  fill = 外轮廓漫水填实的剪影(内部细节全丢)，适合小尺寸
平滑(高斯阈值)去掉版画锯齿，再按容差折线化。
授权(License_HeritageLibrary.pdf)：允许修改后用于作品，不允许单独再分发素材文件——描出来的矢量也不进公开仓库，
放在素材库里、构建时读(ornaments.HERITAGE)，公开的只有内嵌进 theme.css 的成品。
重描不保证和现有文件逐字节相同(2026-11-03 换 OpenCV 5.0 重跑，path 有出入)，没必要别覆盖已经定稿的描线。
用法(模块)：trace(png路径或 PIL 图, mode, smooth, eps, close) → (path d, viewBox)
命令行：python tools/heritage_trace.py <PNG> <输出名> [ink|fill]
       python tools/heritage_trace.py --wing-pair      # 属性栏花框的一对翅膀(见 wing_pair)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
LIB = Path(r"E:\AI工作\素材库\Heritage Library")


def ell(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def trace(png, mode="ink", smooth=4.0, eps=2.0, close=14, min_area=400, scale=0.04, max_side=None):
    im = png if isinstance(png, Image.Image) else Image.open(png)
    a = np.asarray(im.convert("RGBA"))[:, :, 3]
    if max_side and max(a.shape) > max_side:           # 超长图(竖幅 11000px)先缩，免得内存 / 时间爆
        k = max_side / max(a.shape)
        a = cv2.resize(a, (int(a.shape[1] * k), int(a.shape[0] * k)), interpolation=cv2.INTER_AREA)
        scale /= k
    ys, xs = np.nonzero(a > 100)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    a = cv2.copyMakeBorder(a, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=0)
    ink = (a > 100).astype(np.uint8)
    H, W = ink.shape
    if mode == "fill":
        closed = cv2.dilate(ink, ell(close))
        ff = (1 - closed).astype(np.uint8)
        cv2.floodFill(ff, np.zeros((H + 2, W + 2), np.uint8), (0, 0), 2)
        m = cv2.erode((ff != 2).astype(np.uint8), ell(close))
    else:
        m = ink
    m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), smooth) > 0.5).astype(np.uint8)
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    parts = []
    for c in cs:
        if abs(cv2.contourArea(c)) < min_area:
            continue
        c = cv2.approxPolyDP(c, eps, True)[:, 0, :]
        if len(c) < 3:
            continue
        parts.append("M" + " L".join(f"{x * scale:.1f},{y * scale:.1f}" for x, y in c) + "Z")
    vb = (0, 0, round(W * scale, 1), round(H * scale, 1))
    return " ".join(parts), vb


def save(name, d, vb):
    out = LIB / "_描线"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"{name}.svg"
    f.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(map(str, vb))}">\n'
                 f'<path fill-rule="evenodd" d="{d}"/>\n</svg>\n', encoding="utf-8")
    return f


# 属性栏花框四角那一对翅膀(第二十七版八稿 A)：Angels _ Fairies 02 Element 7 飞翔天使原画的两只翅膀(原样一对，不镜像拼接)，
# 两个多边形遮罩去掉人物和飘带(原图 3000px 坐标)；先把墨线膨胀 9px 再描——缩到角上 90px 宽时版画细线才不会断。
# wing-pair = 墨线(ink)，wing-pair-fill = 实心外形(给下面几层抠留白缝、算内细线在哪收住)。
# ornaments.PROPS_WING 里的翼根中点 / 翼尖坐标按这次描出来的 viewBox(123.2 × 39.6)量的，改遮罩或膨胀要重量
WING_PAIR_SRC = ("Angels _ Fairies 02", "*Element 7.png")
WING_PAIR_MASK = (
    [(1590, 360), (1700, 250), (2300, 90), (2960, 5), (3000, 25), (3000, 135), (2760, 300), (2420, 560), (2160, 800),
     (1960, 905), (1700, 905), (1640, 760), (1600, 600), (1575, 450)],
    [(1400, 330), (1300, 250), (700, 90), (40, -5), (0, 25), (0, 135), (240, 300), (560, 600), (640, 700), (800, 800),
     (1000, 860), (1150, 860), (1200, 700), (1230, 560), (1300, 420)])


def wing_pair():
    src = next((LIB / WING_PAIR_SRC[0] / "PNG").glob(WING_PAIR_SRC[1]))
    im = Image.open(src).convert("RGBA")
    m = Image.new("L", im.size, 0)
    for poly in WING_PAIR_MASK:
        ImageDraw.Draw(m).polygon(poly, fill=255)
    a = np.asarray(Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), m))
    a = cv2.dilate(a, ell(4))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.putalpha(Image.fromarray(a))
    for mode, name, kw in (("ink", "wing-pair", dict(smooth=4, eps=1.6, min_area=300)),
                           ("fill", "wing-pair-fill", dict(smooth=6, eps=2.2, close=14))):
        d, vb = trace(out, mode, scale=.04, **kw)
        print(save(name, d, vb), vb, len(d))


if __name__ == "__main__":
    # python tools/heritage_trace.py <PNG> <输出名> [ink|fill]
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "--wing-pair":
        wing_pair()
        sys.exit()
    png, name = Path(sys.argv[1]), sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "ink"
    d, vb = trace(png, mode, smooth=5 if mode == "ink" else 6, eps=2.2, close=10)
    print(save(name, d, vb), vb, len(d))
