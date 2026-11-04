# -*- coding: utf-8 -*-
"""内嵌中文标题字体(第十五版)：寒蝉活宋体 Regular(ChillType，OFL 1.1)，GB2312 全部 6763 个汉字 + GB2312 符号区 +
常用标点 / 全角符号 + 战锤译文常用的几个 GB2312 外汉字(GB2312 符号区只取标点、数字、全角字母、拼音；
假名、希腊 / 俄文字母、制表符标题用不到，落到正文的思源宋体)，输出一组按 unicode-range 切开的 woff2 分片 + ranges.json。
- 切片：浏览器只下载(解码)页面上真正出现的字所在的分片——标题字少，一篇笔记通常只碰到十几片，
  不用每次把整套 6 MB 的字体解开(和 Google Fonts 的中文分片一个道理)。符号一片，汉字按 GB2312 顺序每 CHUNK 字一片
- 改名：这套字体声明了保留字体名 'ChillHuoSong'，按 OFL 第 3 条，子集(修改版)不能再用这个名字——
  name 表里的家族名 / 全名 / PostScript 名都换成 "BA Heading Song"，版权(0)、授权(13、14)原样保留
用法: python tools/make_cjk_heading.py [源字体路径]
"""
import io
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"E:\AI工作\素材库\字体\寒蝉活宋体\ChillHuoSong_F_Regular.otf")
DST = ROOT / "fonts" / "heading-song"
FAMILY, PS = "BA Heading Song", "BAHeadingSong-Regular"
EXTRA = "祂牠祇菈瞭祕"                # 和 make_cjk_serif.py 同一组
CHUNK = 120


def gb2312(lo, hi):
    out = []
    for b1 in range(lo, hi + 1):
        for b2 in range(0xA1, 0xFF):
            try:
                out.append(ord(bytes([b1, b2]).decode("gb2312")))
            except UnicodeDecodeError:
                pass
    return out


def options():
    o = subset.Options()
    o.flavor = "woff2"
    o.layout_features = ["kern", "locl", "vert", "vrt2"]
    o.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14, 16, 17]
    o.name_languages = [0x409, 0x804]
    return o


def rename(font):
    names = {1: FAMILY, 3: f"1.000;BA;{PS}", 4: f"{FAMILY} Regular", 6: PS, 16: FAMILY}
    for r in font["name"].names:
        if r.nameID in names:
            r.string = names[r.nameID]
    if "CFF " in font:
        cff = font["CFF "].cff
        cff.fontNames = [PS]
        top = cff.topDictIndex[0]
        for k in ("FullName", "FamilyName"):
            if hasattr(top, k):
                setattr(top, k, FAMILY if k == "FamilyName" else f"{FAMILY} Regular")


def cut(args):
    base, cps, out = args
    f = TTFont(io.BytesIO(base))
    s = subset.Subsetter(options())
    s.populate(unicodes=cps)
    s.subset(f)
    f.flavor = "woff2"
    f.save(out)
    return out.stat().st_size


def ranges(cps):
    cps = sorted(cps)
    out, a = [], cps[0]
    for p, q in zip(cps, cps[1:] + [None]):
        if q != p + 1:
            out.append(f"U+{a:04X}" if a == p else f"U+{a:04X}-{p:04X}")
            a = q
    return ", ".join(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    t = time.time()
    src = TTFont(SRC)
    have = set(src.getBestCmap())
    sym = [c for c in gb2312(0xA1, 0xA3) + gb2312(0xA8, 0xA8) + list(range(0x2000, 0x2070)) + list(range(0x3000, 0x3040)) + list(range(0xFF00, 0xFFF0))
           if c in have and c > 0x7F]
    han = [c for c in gb2312(0xB0, 0xF7) + [ord(ch) for ch in EXTRA] if c in have]
    sym = sorted(set(sym) - set(han))
    seen, han_u = set(), []
    for c in han:
        if c not in seen:
            seen.add(c)
            han_u.append(c)
    # 先整体抽一遍(13k 字 → 6.8k 字)，再从这份小一点的字体里切片，省得每片都读 30 MB 的原字体
    o = options()
    o.flavor = None
    s = subset.Subsetter(o)
    s.populate(unicodes=set(sym) | set(han_u))
    s.subset(src)
    rename(src)
    buf = io.BytesIO()
    src.save(buf)
    base = buf.getvalue()
    print(f"整体子集 {len(base) / 1048576:.1f} MB(OTF)  {time.time() - t:.0f}s")
    DST.mkdir(parents=True, exist_ok=True)
    for old in DST.glob("*.woff2"):
        old.unlink()
    groups = [sym] + [han_u[i:i + CHUNK] for i in range(0, len(han_u), CHUNK)]
    jobs = [(base, g, DST / f"{PS}-{i:02d}.woff2") for i, g in enumerate(groups)]
    with ProcessPoolExecutor(max_workers=8) as ex:
        sizes = list(ex.map(cut, jobs))
    meta = [dict(file=j[2].name, unicode_range=ranges(j[1]), chars=len(j[1]), bytes=n) for j, n in zip(jobs, sizes)]
    (DST / "ranges.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(meta)} 片  {len(sym)} 个符号 + {len(han_u)} 个汉字  共 {sum(sizes) / 1048576:.2f} MB  ({time.time() - t:.0f}s)")
