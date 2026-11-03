# -*- coding: utf-8 -*-
"""套色印章的位图加工(构建时，numpy + PIL；第九版)：
- wear：大尺度、过渡柔和的"印压不匀"磨损场(0 = 墨色饱满，1 = 磨得最薄)。不是斑块——它只调颗粒的轻重，
  第七版那种看得出形状的浅斑会被看成"气泡"
- ink_mask / wear_overlay：颗粒 × 磨损 → 印刷遮罩(位图直接乘 alpha；SVG 徽章用一张低分辨率的叠加图放进亮度遮罩)
- arc_warp：把平的位图整体弯成圆弧(水平线 → 同心圆弧，竖线 → 半径)，题铭绶带连同文字一起弯
- text_alpha：用 Playwright 按显示字号渲染一行字的覆盖率(和主题里同一个字体文件、同一套排版)
"""
import base64
import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "assets" / "cache"


def field(w, h, scale, seed, octaves=3):
    """平滑噪声场 0..1：每一层 = 随机格点放大(双三次)再高斯模糊，scale = 最大一层的特征尺寸(像素)"""
    rng = np.random.RandomState(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = scale / 2 ** o
        gw, gh = max(2, round(w / s) + 2), max(2, round(h / s) + 2)
        g = Image.fromarray((rng.rand(gh, gw) * 255).astype(np.uint8))
        g = g.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(s / 4))
        acc += amp * np.asarray(g, np.float32) / 255
        tot += amp
        amp *= .5
    acc /= tot
    lo, hi = np.percentile(acc, (2, 98))
    return np.clip((acc - lo) / (hi - lo), 0, 1)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def wear(w, h, scale, seed, lo=.42, hi=.9, bias=None):
    """磨损场：平滑噪声过一道很宽的 smoothstep——大约三成面积明显磨薄，过渡带很宽、没有边。
    bias：同尺寸的数组，加在噪声上(比如外圈磨得多一点)"""
    f = field(w, h, scale, seed)
    if bias is not None:
        f = np.clip(f + bias, 0, 1)
    return smoothstep(lo, hi, f)


def ink_mask(g, wv, base=.3, span=.55, deep=.08, gain=1):
    """g：颗粒(1 = 有墨)，wv：磨损场 → 遮罩。墨色饱满处颗粒只显 base 那么多，磨薄处显到 base + span，
    并整体再淡 deep。gain：再乘一道(可以是数组，比如深色墨上减半——深红上漏出纸色比浅色上扎眼得多)"""
    k = (base + span * wv) * gain
    return np.clip(1 - k * (1 - g) - deep * wv * gain, 0, 1)


def dark_gain(rgb, lo=.3, hi=.8, floor=.5):
    """按墨色明度给颗粒减量：明度 ≥ hi 照常，≤ lo 只留 floor"""
    lum = rgb[..., 0] * .3 + rgb[..., 1] * .59 + rgb[..., 2] * .11
    return floor + (1 - floor) * np.clip((lum - lo) / (hi - lo), 0, 1)


def wear_overlay(w, h, scale, seed, res=4, base=.3, span=.55, deep=.08, bias=None):
    """SVG 徽章用：亮度遮罩里先铺颗粒 g，再盖这张图(颜色 c、不透明度 a)，合成 g(1 − a) + c·a = ink_mask(g, 磨损)。
    磨损很缓，res 倍降采样(浏览器放大时双线性插值，看不出)。返回 WebP 无损字节"""
    sw, sh = round(w / res), round(h / res)
    b = None if bias is None else bias(sw, sh)
    wv = wear(sw, sh, scale / res, seed, bias=b)
    k = base + span * wv
    a = 1 - k
    c = np.where(a > 1e-4, (1 - k - deep * wv) / np.maximum(a, 1e-4), 0)
    rgba = np.dstack([np.clip(c, 0, 1)] * 3 + [a]) * 255
    buf = io.BytesIO()
    Image.fromarray(rgba.round().astype(np.uint8), "RGBA").save(buf, "WEBP", lossless=True, method=6)
    return buf.getvalue()


def tile(gray, w, h, offset=(0, 0)):
    """把灰度颗粒图(PIL L)平铺成 w×h 的 0..1 数组，offset 错开起点(两套墨各用一处，颗粒不重合)"""
    t = np.asarray(gray, np.float32) / 255
    th, tw = t.shape
    ox, oy = offset
    ys = (np.arange(h) + oy) % th
    xs = (np.arange(w) + ox) % tw
    return t[np.ix_(ys, xs)]


def _bilinear(a, sx, sy):
    """a：H×W×C(预乘)，按浮点坐标双线性取样，超出范围 = 0"""
    H, W = a.shape[:2]
    p = np.zeros((H + 2, W + 2, a.shape[2]), a.dtype)
    p[1:-1, 1:-1] = a
    sx, sy = sx + 1, sy + 1
    ok = (sx >= 0) & (sx <= W + 1) & (sy >= 0) & (sy <= H + 1)
    sx = np.clip(sx, 0, W + .999)
    sy = np.clip(sy, 0, H + .999)
    x0, y0 = np.floor(sx).astype(int), np.floor(sy).astype(int)
    x1, y1 = np.minimum(x0 + 1, W + 1), np.minimum(y0 + 1, H + 1)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    out = (p[y0, x0] * (1 - fx) * (1 - fy) + p[y0, x1] * fx * (1 - fy)
           + p[y1, x0] * (1 - fx) * fy + p[y1, x1] * fx * fy)
    return out * ok[..., None]


def arc_warp(a, sag, y_ref, pad):
    """把平的图弯成"笑"的弧：正中不动，两端抬起 sag(像素)。y_ref = 不变形的那条水平线(宽带中线)；
    水平方向按弧长保持(字距不变)。输出高 = 原高 + pad(上面留出两端抬起的地方)，宽不变。
    a：H×W×C 浮点数组(RGBA 要先预乘)"""
    H, W = a.shape[:2]
    half = W / 2
    R = (half ** 2 + sag ** 2) / (2 * sag)
    Y, X = np.mgrid[0:H + pad, 0:W].astype(np.float64) + .5
    cy = y_ref + pad - R                      # 圆心在上面
    dx, dy = X - half, Y - cy
    sx = half + np.arctan2(dx, dy) * R - .5
    sy = y_ref + (np.hypot(dx, dy) - R) - .5
    return _bilinear(a, sx, sy)


def centerline(alpha, x0, x1, y0, thr=.5):
    """量一条带子每一列的中线：从 (中间那列, y0) 出发，每列从上一列的中线往上下找到 alpha < thr 的边。
    返回 (xs, ys)，从中间往两边各走一遍(带子两端往上卷，从中间出发才不会跳到别的部件上)"""
    H = alpha.shape[0]
    mid = (x0 + x1) // 2
    xs, ys = [], []
    for rng in (range(mid, x1), range(mid - 1, x0 - 1, -1)):
        y = y0
        for x in rng:
            col = alpha[:, x]
            yi = int(round(y))
            if col[yi] < thr:
                break
            t = yi
            while t > 0 and col[t - 1] >= thr:
                t -= 1
            b = yi
            while b < H - 1 and col[b + 1] >= thr:
                b += 1
            y = (t + b) / 2
            xs.append(x)
            ys.append(y)
    o = np.argsort(xs)
    return np.array(xs, np.float64)[o], np.array(ys, np.float64)[o]


def follow_warp(t, xs, ys, out_shape, src_cx, src_cy, deg=8, iters=6):
    """把一行平的字 t(H×W 覆盖率)沿曲线 y = c(x) 排：字的水平方向 → 曲线弧长(字距不变)，竖直方向 → 曲线法线。
    c 由 (xs, ys) 多项式拟合；src_cx / src_cy = 字图里对应曲线中点 / 中线的位置，曲线中点取 xs 的中点。
    反算每个输出像素在曲线上的垂足 s(牛顿迭代 (X − s) + (Y − c(s))·c'(s) = 0)"""
    Ho, Wo = out_shape
    xs, ys = xs + .5, ys + .5                 # 像素下标 → 连续坐标(像素中心)
    xm = (xs[0] + xs[-1]) / 2
    sc = (xs[-1] - xs[0]) / 2
    p = np.polynomial.Polynomial.fit((xs - xm) / sc, ys, deg).convert()
    c = lambda x: p((x - xm) / sc)
    d1 = p.deriv(1)
    d2 = p.deriv(2)
    c1 = lambda x: d1((x - xm) / sc) / sc
    c2 = lambda x: d2((x - xm) / sc) / sc ** 2
    Y, X = np.mgrid[0:Ho, 0:Wo].astype(np.float64) + .5
    s = X.copy()
    for _ in range(iters):
        cs, k1, k2 = c(s), c1(s), c2(s)
        f = (X - s) + (Y - cs) * k1
        fp = -1 - k1 * k1 + (Y - cs) * k2
        s -= f / fp
        s = np.clip(s, xs[0] - 200, xs[-1] + 200)
    k1 = c1(s)
    n = ((Y - c(s)) - (X - s) * k1) / np.sqrt(1 + k1 * k1)
    xg = np.linspace(xs[0] - 200, xs[-1] + 200, 4000)
    L = np.concatenate([[0], np.cumsum(np.sqrt(1 + c1((xg[1:] + xg[:-1]) / 2) ** 2) * np.diff(xg))])
    arc = np.interp(s, xg, L) - np.interp(xm, xg, L)
    out = _bilinear(t[..., None], src_cx + arc - .5, src_cy + n - .5)[..., 0]
    return out, c


def text_alpha(text, font_path, px, box_w, box_h, scale=2):
    """一行字(居中、行高 = box_h)的覆盖率，box_w×box_h 显示像素 × scale → 0..1 数组。结果按内容缓存"""
    font = Path(font_path).read_bytes()
    key = hashlib.sha1(font + f"{text}|{px}|{box_w}|{box_h}|{scale}".encode()).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"text-{key}.png"
    if not out.exists():
        from playwright.sync_api import sync_playwright
        uri = "data:font/woff2;base64," + base64.b64encode(font).decode()
        html = (f'<html><head><style>@font-face{{font-family:T;src:url("{uri}") format("woff2")}}'
                f'body{{margin:0;background:transparent}}'
                f'div{{width:{box_w}px;height:{box_h}px;line-height:{box_h}px;font:{px}px T;color:#fff;'
                f'text-align:center;white-space:nowrap}}</style></head><body><div>{text}</div></body></html>')
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": box_w, "height": box_h}, device_scale_factor=scale)
            pg.set_content(html)
            pg.evaluate("document.fonts.ready.then(() => document.fonts.size)")
            pg.wait_for_timeout(200)
            pg.screenshot(path=str(out), omit_background=True, clip=dict(x=0, y=0, width=box_w, height=box_h))
            b.close()
    return np.asarray(Image.open(out).convert("RGBA"), np.float32)[..., 3] / 255
