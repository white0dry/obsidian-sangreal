# -*- coding: utf-8 -*-
"""示例库整窗截图(开发用)：python tools/snap.py <输出.png> [笔记路径] [--edit] [--js=代码]
截图存到给定路径；可先打开指定笔记(阅读视图，--edit = 实时预览)，滚到顶；--scroll=N 往下滚 N px"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from obs import demo_page  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in sys.argv[1:] if a.startswith("--"))
out = Path(args[0])
note = args[1] if len(args) > 1 else None

OPEN = """async ([note, mode, scroll]) => {
  const w = app.workspace;
  let leaf = w.getLeavesOfType('markdown').find(l => l.view.file?.path === note);
  if (!leaf) { leaf = w.getMostRecentLeaf(); await leaf.openFile(app.vault.getAbstractFileByPath(note)); }
  w.setActiveLeaf(leaf, {focus: true});
  const st = leaf.getViewState();
  if (st.state.mode !== mode || (mode === 'source' && st.state.source)) { st.state.mode = mode; st.state.source = false; await leaf.setViewState(st); }
  await new Promise(r => setTimeout(r, 600));
  if (mode === 'preview') leaf.view.previewMode?.applyScroll?.(scroll);
  else leaf.view.editor?.scrollTo(0, scroll);
  await new Promise(r => setTimeout(r, 600));
  return 'ok';
}"""

with demo_page() as (b, pg):
    if note:
        pg.evaluate(OPEN, [note, "source" if "edit" in opts else "preview", int(opts.get("scroll", 0))])
    if "js" in opts:
        print(pg.evaluate(opts["js"]))
    pg.wait_for_timeout(int(opts.get("wait", 800)))
    cdp = pg.context.new_cdp_session(pg)
    r = cdp.send("Page.captureScreenshot", {"format": "png"})
    out.write_bytes(base64.b64decode(r["data"]))
    print(out, pg.evaluate("[innerWidth, innerHeight]"))
