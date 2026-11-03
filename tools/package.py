# -*- coding: utf-8 -*-
"""手动安装包：给连不上官方主题商店的用户，把主题、可选中文字体片段、安装说明和许可证打成一个 zip。
用法：先 python build.py，再 python tools/package.py → dist/Sangreal-<版本>.zip(不挂 release，单独发给连不上商店的用户)
安装说明的底稿是 tools/install-guide.zh-CN.txt({version} / {min_app} 打包时替换)，写进 zip 时转成 UTF-8 BOM + CRLF，
旧版 Windows 记事本双击也能正常显示。zip 里不套顶层文件夹：Windows「全部解压缩」会自己建一个以压缩包命名的文件夹。
"""
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "tools" / "install-guide.zh-CN.txt"


def main():
    m = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    name, ver = m["name"], m["version"]
    guide = GUIDE.read_text(encoding="utf-8").replace("{version}", ver).replace("{min_app}", m["minAppVersion"])
    guide = "﻿" + guide.replace("\r\n", "\n").replace("\n", "\r\n")
    files = [(f"{name}/manifest.json", ROOT / "manifest.json"),
             (f"{name}/theme.css", ROOT / "theme.css"),
             *((f"snippets/{p.name}", p) for p in sorted((ROOT / "snippets").glob("*.css"))),
             ("licenses/LICENSE.txt", ROOT / "LICENSE"),
             ("licenses/THIRD-PARTY-NOTICES.md", ROOT / "THIRD-PARTY-NOTICES.md"),
             ("licenses/OFL.txt", ROOT / "fonts" / "OFL.txt")]
    out = ROOT / "dist" / f"{name}-{ver}.zip"
    out.parent.mkdir(exist_ok=True)
    # 非 ASCII 文件名(安装说明.txt)由 zipfile 自动打上 UTF-8 标记，Windows 资源管理器 / macOS / 7-Zip 都认
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("安装说明.txt", guide.encode("utf-8"))
        for arc, src in files:
            z.write(src, arc)
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
