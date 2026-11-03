# -*- coding: utf-8 -*-
"""夜间新标签页的喷溅血渍(位图，build.spatter_webp 调用；第五十二版)。冲击点在圣杯杯口：
中心几团带刺的大血斑(多半被徽章挡住) + 几道放射状血线(越远越小、拖得越长) + 一圈零散的「感叹号」血点(尾巴朝外) + 外围细雾。

画法是「元球」：每个血点 = 几团高斯场叠加——头 = 一团略拉长的 + 一两团偏开的小团(头不对称)，尾巴 = 一串逐渐变细的小团，
场叠起来再取等值线，头和尾巴之间自然长出圆滑的颈。等值线前对坐标做两层低频扭曲(幅度按血点大小缩放，小点不至于扭碎)、
再加一点细噪声(大血斑边缘毛一些)；边缘按到等值线的距离做 ~1px 柔边；干血：边上一圈浓、里面薄一点、带斑驳。
小样一二稿是 SVG(椭圆头 + 三角尾巴)，用户嫌边缘生硬、圆点和尾巴接得突兀、形状太规律，三稿改成这样；
另试过把用户下载的素材里的真实血点切下来当印章贴(更像液体，但素材有许可问题)，用户选了这一版。

构图 = 用户在小样里挑的 A(四面喷溅)：主随机数 rng 按小样的调用顺序一个不差地抽(位置 / 大小 / 拉长 / 颜色 / 浓度 / 大血斑的刺的方向都一样)，
形状细节另用一个随机数 g。单位 = 显示 px，S = 位图倍数"""
import math
import random

import numpy as np

COLS = ("#5e0f13", "#6e1216", "#7d171b", "#8c1c1f")   # 四种深浅的暗血红(叠在夜间纸色上)
T = .5                            # 等值线
K = math.sqrt(math.log(1 / T))    # 单个高斯团：r = R / K 时，等值线半径 = R


def _rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


def _noise(shape, wl, seed):
    """周期边界的平滑噪声(白噪声在频域里低通)，标准差 1；wl = 大致波长(位图 px)"""
    n = np.random.default_rng(seed).standard_normal(shape)
    fy, fx = np.fft.fftfreq(shape[0])[:, None], np.fft.rfftfreq(shape[1])[None, :]
    s = 1 / wl
    f = np.fft.irfft2(np.fft.rfft2(n) * np.exp(-(fx ** 2 + fy ** 2) / (2 * s * s)), s=shape)
    return (f / f.std()).astype(np.float32)


class Field:
    def __init__(self, W, H, S, seed):
        self.S = S
        self.h, self.w = round(H * S), round(W * S)
        sh = (self.h, self.w)
        self.Y, self.X = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        # 坐标扭曲(显示 px)：波长 14 / 振幅 .9 + 波长 5 / 振幅 .35，每团按大小缩放(固定幅度时一两 px 的小点被扭成碎片、月牙)
        self.NX = S * (.9 * _noise(sh, 14 * S, seed) + .35 * _noise(sh, 5 * S, seed + 1))
        self.NY = S * (.9 * _noise(sh, 14 * S, seed + 2) + .35 * _noise(sh, 5 * S, seed + 3))
        self.fine = _noise(sh, 2.2 * S, seed + 4)
        self.mott = _noise(sh, 9 * S, seed + 5)
        self.F = np.zeros(sh, np.float32)
        self.C = np.zeros(sh + (3,), np.float32)
        self.O = np.zeros(sh, np.float32)

    def blob(self, x, y, R, col, op, ang=0.0, a=1.0, w=1.0, warp=None):
        """一团：等值线半径 R(显示 px)，沿 ang 方向拉长 a 倍；w = 权重(串成线的小团要按间距压低，不然叠起来变粗)；
        warp = 坐标扭曲的倍数(默认按大小：半径 6px 以上满幅，小点按比例减到 .12)"""
        S = self.S
        kw = min(1.0, max(.12, R / 6)) if warp is None else warp
        r = max(R, .28) / K * S
        cx, cy = x * S, y * S
        ext = 3.2 * r * max(a, 1)
        x0, x1 = max(0, int(cx - ext)), min(self.w, int(cx + ext) + 2)
        y0, y1 = max(0, int(cy - ext)), min(self.h, int(cy + ext) + 2)
        if x0 >= x1 or y0 >= y1:
            return
        dx = self.X[y0:y1, x0:x1] + kw * self.NX[y0:y1, x0:x1] - cx
        dy = self.Y[y0:y1, x0:x1] + kw * self.NY[y0:y1, x0:x1] - cy
        ux, uy = math.cos(ang), math.sin(ang)
        al, pe = dx * ux + dy * uy, -dx * uy + dy * ux
        k = w * np.exp(-((al / (r * a)) ** 2 + (pe / r) ** 2))
        self.F[y0:y1, x0:x1] += k
        self.C[y0:y1, x0:x1] += k[..., None] * _rgb(col)
        self.O[y0:y1, x0:x1] += k * op

    def chain(self, pts, col, op, warp=None):
        """一串小团连成一条渐细的线：pts = [(x, y, R)]，相邻间距 ≈ .6R；权重 = 间距 / (r·√π)，连续时线中心的场 = 1，粗细 = R。
        warp：整串用同一个扭曲倍数(和头一致，接口处不错位)"""
        for i, (x, y, R) in enumerate(pts):
            if i + 1 < len(pts):
                st = math.hypot(pts[i + 1][0] - x, pts[i + 1][1] - y)
            else:
                st = math.hypot(x - pts[i - 1][0], y - pts[i - 1][1]) if i else R
            r = max(R, .28) / K
            self.blob(x, y, R, col, op, w=min(1.0, st / (r * math.sqrt(math.pi))), warp=warp)

    def render(self, ink=None, feather=1.1, rough=.05, ring=.2, grad=None, local=None):
        """等值线 → 柔边(按到等值线的距离，feather = 柔边宽度 显示 px)；干血：边上一圈浓、往里薄 ring、带斑驳；
        ink = 印刷颗粒(0..1，乘到不透明度上，同全主题的印章套色)。返回 RGBA uint8(非预乘)。
        grad = 整体渐变(按离冲击点的远近)：c 冲击点、sy 纵向压缩(椭圆分布 rx / ry)、r0 / r1 渐变起止(显示 px)、
        near / near_amt 近处往哪个颜色靠多少、far / far_amt 远处、far_op 远处不透明度倍数；
        local = 每块血迹自己的深浅：rim / rim_amt / rim_w 边上一圈(宽 rim_w px)往深色靠、core / core_amt 里面往亮色靠(带斑驳)"""
        from scipy.ndimage import distance_transform_edt
        S = self.S
        F = self.F + rough * self.fine * np.minimum(self.F * 4, 1)
        gy, gx = np.gradient(F)
        g = np.sqrt(gx * gx + gy * gy)
        sd = (F - T) / np.maximum(g, 1e-4)            # ≈ 到等值线的距离(位图 px，里面为正)
        alpha = np.clip(sd / (feather * S) + .5, 0, 1)
        Fs = np.maximum(self.F, 1e-6)
        rgb = self.C / Fs[..., None]
        op = self.O / Fs
        depth = distance_transform_edt(F > T) / S       # 离边多远(显示 px)
        core = np.clip((depth - 1.0) / 3.5, 0, 1)
        core = core * core * (3 - 2 * core)
        op = op * (1 - ring * core * (.75 + .25 * self.mott))
        rgb = rgb * (1 - .06 * (1 - core))[..., None]  # 边那一圈颜色也深一点
        if local:
            rim = local["rim_amt"] * np.clip(1 - depth / local.get("rim_w", 1.4), 0, 1)[..., None]
            rgb = rgb * (1 - rim) + _rgb(local["rim"]) * rim
            cm = local["core_amt"] * (core * (.55 + .45 * np.clip(.5 + .5 * self.mott, 0, 1)))[..., None]
            rgb = rgb * (1 - cm) + _rgb(local["core"]) * cm
            if "patch" in local:                         # 大尺度的颜色起伏：一片偏鲜红、一片偏暗褐(相邻血点不同色，大斑里有色差)
                ca, cb, amt, wl = local["patch"]
                n = np.clip(.5 + .5 * _noise(self.F.shape, wl * S, 77), 0, 1)[..., None]
                col = _rgb(ca) * n + _rgb(cb) * (1 - n)
                rgb = rgb * (1 - amt) + col * amt
        if grad:
            d = np.hypot(self.X / S - grad["c"][0], (self.Y / S - grad["c"][1]) * grad.get("sy", 1))
            t = np.clip((d - grad["r0"]) / (grad["r1"] - grad["r0"]), 0, 1)
            t = t * t * (3 - 2 * t)
            tn, tf = grad["near_amt"] * (1 - t)[..., None], grad["far_amt"] * t[..., None]
            rgb = rgb * (1 - tn) + _rgb(grad["near"]) * tn
            rgb = rgb * (1 - tf) + _rgb(grad["far"]) * tf
            op = op * (1 - (1 - grad["far_op"]) * t)
        a = alpha * op
        if ink is not None:
            a = a * ink
        out = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])
        return (out * 255).round().astype(np.uint8)


def avoid(alpha, S, thr=.3, close=4, grow=2.5, feather=1.0):
    """血渍让开一个图案：alpha = 图案在同一张图里的不透明度(同为 S 倍)。轮廓 = 不透明度 > thr，闭运算(半径 close 显示 px)
    把各层之间的留白缝填上、再填封闭的小洞；轮廓里和往外 grow px 以内清空，再 feather px 过渡到全显。返回 0..1 的保留系数"""
    from scipy.ndimage import binary_closing, binary_fill_holes, distance_transform_edt
    r = int(round(close * S))
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    m = np.pad(alpha > thr, r + 2)                # 四周留空，免得贴着图边被腐蚀掉
    m = binary_closing(m, structure=x * x + y * y <= r * r)[r + 2:-(r + 2), r + 2:-(r + 2)]
    d = distance_transform_edt(~binary_fill_holes(m)) / S
    return np.clip((d - grow) / feather, 0, 1)


def _blob_draws(rng, spikes):
    """小样里中心血斑是带刺的多边形：照它的顺序把随机数抽掉(后面的构图才和 A 一样)，返回尖刺的角度和长度倍数"""
    n = 28
    sp = sorted(rng.sample(range(n), spikes))
    out = []
    for i in range(n):
        rng.random()
        rng.random()
        if i in sp:
            out.append((2 * math.pi * i / n, 1.5 + rng.random() * .9))
    return out


def spatter(W, H, ox, oy, rx, ry, seed=7, rays=9, drops=150, mist=500, big=4, up=.0, S=2, ink=None, shape_seed=101, **kw):
    """W × H 的血渍(显示 px)，冲击点 (ox, oy)，rx / ry = 横 / 纵向最远距离(椭圆分布)；up = 往上溅的权重(0 = 四面八方)"""
    rng = random.Random(seed)
    g = random.Random(shape_seed)
    fd = Field(W, H, S, shape_seed)

    def at(theta, r):
        return ox + math.cos(theta) * r * rx, oy + math.sin(theta) * r * ry

    def angle():
        t = rng.uniform(-math.pi, math.pi)
        if up and rng.random() < up:
            t = -math.pi / 2 + rng.gauss(0, .9)
        return t

    def drop(x, y, s, ang, aspect, col, op, tail=True):
        """一个血点：头(略拉长 + 偏开的小团，不对称) + 渐细的尾巴(和头之间场叠出圆滑的颈) + 有时尾端一个小球或分开的卫星点"""
        ang += g.gauss(0, .07)
        ha = min(aspect, 1.7) * g.uniform(.85, 1.1)
        ux, uy = math.cos(ang), math.sin(ang)
        nx, ny = -uy, ux
        kw = min(1.0, max(.12, s / 6))
        fd.blob(x, y, s, col, op, ang, ha, warp=kw)
        for _ in range(g.randint(0 if s < 1.2 else 1, 2)):       # 头上偏开的小团：只让头稍微不对称，不起疙瘩
            o, p = g.uniform(-.35, .2) * s * ha, g.uniform(-.3, .3) * s
            fd.blob(x + ux * o + nx * p, y + uy * o + ny * p, s * g.uniform(.5, .72), col, op, ang + g.gauss(0, .4), g.uniform(1, 1.3), warp=kw)
        if not (tail and aspect > 1.3):
            return
        L = s * (1.2 + 1.6 * (aspect - 1.3)) * g.uniform(.75, 1.45)   # 越斜着落、尾巴越长
        w0, p, bend = g.uniform(.4, .62), g.uniform(.7, 1.6), g.gauss(0, .1)
        x0, y0 = x + ux * s * ha * .45, y + uy * s * ha * .45
        pts, t = [], 0.0
        while t < L:
            R = s * (w0 * (1 - t / L) ** p + .1)
            off = bend * (t / L) ** 2 * L
            pts.append((x0 + ux * t + nx * off, y0 + uy * t + ny * off, R))
            t += max(.3, .6 * R)
        if len(pts) > 1:
            fd.chain(pts, col, op, warp=kw)
        if g.random() < .4:                         # 尾端：贴着的小球，或隔开一点的卫星点
            R = s * g.uniform(.16, .3)
            t = L + R * g.uniform(.6, 3.2)
            off = bend * (t / L) ** 2 * L
            fd.blob(x0 + ux * t + nx * off, y0 + uy * t + ny * off, R, col, op, ang, g.uniform(1, 1.5), warp=kw)

    # 中心大血斑：几团叠成不规则的底 + 几根刺(一串渐细的小团，刺尖常带一粒小球) + 一圈细小的扇贝边
    for _ in range(big):
        t, r = angle(), rng.uniform(.02, .12)
        x, y = at(t, r)
        R = rng.uniform(9, 20)
        col, op = rng.choice(COLS[1:]), rng.uniform(.75, .9)
        spikes = _blob_draws(rng, rng.randint(4, 8))
        fd.blob(x, y, R * .9, col, op, warp=1)
        for _ in range(g.randint(2, 4)):
            a, d = g.uniform(0, 2 * math.pi), g.uniform(.2, .5) * R
            fd.blob(x + math.cos(a) * d, y + math.sin(a) * d, R * g.uniform(.45, .7), col, op, a, g.uniform(1, 1.5), warp=1)
        for a, m in spikes:
            a += g.gauss(0, .08)
            L, w0 = R * (m - .9) * g.uniform(.8, 1.4), R * g.uniform(.16, .26)
            pts, t = [], R * .7
            while t < R * .7 + L:
                f = (t - R * .7) / L
                pts.append((x + math.cos(a) * t, y + math.sin(a) * t, w0 * (1 - f) ** 1.2 + R * .035))
                t += max(.3, .6 * pts[-1][2])
            fd.chain(pts, col, op, warp=.6)
            if g.random() < .55:
                tt = R * .7 + L + R * g.uniform(.03, .18)
                fd.blob(x + math.cos(a) * tt, y + math.sin(a) * tt, R * g.uniform(.06, .11), col, op, warp=.6)
        for _ in range(g.randint(8, 14)):
            a = g.uniform(0, 2 * math.pi)
            fd.blob(x + math.cos(a) * R * .95, y + math.sin(a) * R * .95, R * g.uniform(.12, .22), col, op, a, g.uniform(1, 1.8), warp=1)
    # 放射状血线：沿一条射线一串血点，越远越小越长；间距、大小随机，沿线撒细碎点，拉得长的前面常有一粒卫星点。
    # 实装后试过两处，用户看了都说不如原来、定回这版：① 间距 / 大小改对数正态、偶尔空格 / 并排(有几粒反而更圆)；
    # ② 半径 3px 以下的小血点加凸起、乱转向、短尾，碎点 / 卫星点挂凸起
    for _ in range(rays):
        t0 = angle()
        rr = rng.uniform(.1, .2)
        r_end = rng.uniform(.55, 1.0)
        while rr < r_end:
            f = (rr - .1) / max(.01, r_end - .1)
            t = t0 + rng.gauss(0, .03)
            x, y = at(t, rr)
            s = max(.5, (5.2 - 4.4 * f) * rng.uniform(.35, 1.2))
            aspect = 1 + 2.8 * f * rng.uniform(.4, 1.25)
            ang = math.atan2(math.sin(t) * ry, math.cos(t) * rx)
            col, op = rng.choice(COLS), rng.uniform(.55, .9)
            drop(x, y, s, ang, aspect, col, op)
            if aspect > 2 and rng.random() < .45:
                d = s * rng.uniform(4.5, 7)
                R = s * rng.uniform(.25, .5)
                fd.blob(x + math.cos(ang) * d, y + math.sin(ang) * d, R, rng.choice(COLS), .75, ang, g.uniform(1, 1.5))
            for _ in range(rng.randint(0, 3)):
                tt, r2 = t + rng.gauss(0, .06), rr + rng.uniform(-.03, .05)
                px, py = at(tt, r2)
                fd.blob(px, py, rng.uniform(.35, 1.0), rng.choice(COLS), rng.uniform(.5, .85), g.uniform(0, 6.3), g.uniform(1, 1.5))
            rr += rng.uniform(.02, .09) * (1 + f)
    # 零散血点
    for _ in range(drops):
        t = angle()
        rr = .12 + .9 * rng.random() ** .8
        x, y = at(t, rr)
        s = max(.6, (4.2 * max(0, 1 - rr) ** 1.3 + .5) * rng.uniform(.5, 1.2))
        aspect = 1 + 2.2 * rr * rng.random()
        ang = math.atan2(math.sin(t) * ry, math.cos(t) * rx)
        drop(x, y, s, ang, aspect, rng.choice(COLS), rng.uniform(.5, .85))
    # 细雾
    for _ in range(mist):
        t = angle()
        rr = .15 + 1.0 * rng.random() ** .65
        x, y = at(t, rr)
        fd.blob(x, y, rng.uniform(.35, 1.1), rng.choice(COLS), rng.uniform(.4, .8), g.uniform(0, 6.3), g.uniform(1, 1.6))
    return fd.render(ink, **kw)
