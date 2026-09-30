"""Open a given Obsidian layout via workspace.json, then capture ONLY the Obsidian window."""
import json, secrets, subprocess, sys, time, re
import os
VAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vault")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence", "obsidian")
rid = lambda: secrets.token_hex(8)

def leaf(kind, file=None):
    if kind == "graph":
        return {"id": rid(), "type": "leaf", "state": {"type": "graph", "state": {}, "title": "Graph view"}}
    if kind == "localgraph":
        return {"id": rid(), "type": "leaf", "state": {"type": "localgraph", "state": {"file": file, "options": {"localJumps": 1, "localBacklinks": True, "localForelinks": True, "showTags": False, "showAttachments": False, "hideUnresolved": True, "search": "path:wiki/"}}}}
    if kind == "backlink":
        return {"id": rid(), "type": "leaf", "state": {"type": "backlink", "state": {"file": file, "collapseAll": False, "extraContext": False, "sortOrder": "alphabetical", "showSearch": False, "searchQuery": "", "backlinkCollapsed": False, "unlinkedCollapsed": True}}}
    return {"id": rid(), "type": "leaf", "state": {"type": "markdown", "state": {"file": file, "mode": "preview", "source": False}}}

def workspace(main_leaves, right_leaves=None):
    tabs = [{"id": rid(), "type": "tabs", "children": [l]} for l in main_leaves]
    ws = {
      "main": {"id": rid(), "type": "split", "children": tabs, "direction": "vertical"},
      "left": {"id": rid(), "type": "split", "children": [{"id": rid(), "type": "tabs", "children": [
          {"id": rid(), "type": "leaf", "state": {"type": "file-explorer", "state": {"sortOrder": "alphabetical", "autoReveal": True}}}]}],
          "direction": "horizontal", "width": 240},
      "right": {"id": rid(), "type": "split", "children": [{"id": rid(), "type": "tabs", "children": right_leaves or [leaf("backlink", "index.md")]}],
          "direction": "horizontal", "width": 300, "collapsed": not right_leaves},
      "active": main_leaves[0]["id"], "lastOpenFiles": []}
    return ws

layouts = {
  "1b-note-ms-pac-man-dqn": ([leaf("md", "wiki/Projects/Ms Pac-Man DQN.md")], None),
  "2-index": ([leaf("md", "index.md")], None),
  "3-graph": ([leaf("graph")], None),
  "4-source-catalog": ([leaf("md", "Source Catalog.md")], None),
  "5-concept-learning-rate-with-local-graph": ([leaf("md", "wiki/Concepts/Learning Rate.md")], [leaf("localgraph", "wiki/Concepts/Learning Rate.md")]),
}
names = sys.argv[1:] or list(layouts)
for name in names:
    main, right = layouts[name]
    subprocess.run(["osascript", "-e", 'quit app "Obsidian"']); time.sleep(2.5)
    json.dump(workspace(main, right), open(f"{VAULT}/.obsidian/workspace.json", "w"), indent=1)
    import os
    json.dump({"x": 40, "y": 30, "width": 1440, "height": 940, "isMaximized": False, "devTools": False, "zoom": 0},
              open(os.path.expanduser("~/Library/Application Support/obsidian/71fb9a2940a3042a.json"), "w"))
    subprocess.run(["open", "-a", "Obsidian"]); time.sleep(6 if "graph" in name else 4)
    wins = subprocess.run(["osascript", "-l", "JavaScript", "-e",
        'ObjC.import("CoreGraphics");var l=ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo($.kCGWindowListOptionAll,0)));'
        'JSON.stringify(l.filter(w=>w.kCGWindowOwnerName=="Obsidian"&&w.kCGWindowLayer==0&&w.kCGWindowBounds.Height>300).map(w=>w.kCGWindowNumber))'],
        capture_output=True, text=True).stdout
    wid = json.loads(wins)[0]
    subprocess.run(["screencapture", "-x", "-o", f"-l{wid}", f"{OUT}/{name}.png"])
    print(name, "window", wid, "saved")
