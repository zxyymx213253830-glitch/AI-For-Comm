# -*- coding: utf-8 -*-
"""
sim_agent gateway 探针 —— 验证不同提示词下终答是否携带完整四章节
用法: .venv\\Scripts\\python.exe tests/debug_sim_sse.py [问题文本]
不传参则使用默认测试问题。
"""
import sys, os, json, urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import OPENTREK_BASE_URL, APP_KEY, AGENTS

cfg = AGENTS["sim_agent"]

DEFAULT_Q = "仿真 BPSK 在 AWGN 下 Eb/N0=6dB 的误码率"
question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_Q


def post(path, body, timeout=300):
    req = urllib.request.Request(
        f"{OPENTREK_BASE_URL}/{path}",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {APP_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=timeout)


resp = post("createSession", {"agentCode": cfg["agentCode"], "agentVersion": cfg["agentVersion"]})
sid = json.loads(resp.read().decode())["data"]["uniqueCode"]
print("session:", sid)
print("question:", question[:80])

resp = post("run", {
    "sessionId": sid,
    "stream": True,
    "delta": True,
    "message": {"text": question, "metadata": {}, "attachments": []},
})

buf = ""
types = {}
answer = []          # 终答累计（message.delta/text.delta）
while True:
    chunk = resp.read(8192)
    if not chunk:
        break
    buf += chunk.decode("utf-8", errors="replace")
    lines = buf.split("\n")
    buf = lines.pop()
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("data:"):
            continue
        s = ln[5:].strip()
        if s == "[DONE]":
            continue
        try:
            o = json.loads(s)
        except json.JSONDecodeError:
            continue
        t = o.get("object", "?")
        types[t] = types.get(t, 0) + 1
        c = o.get("content")
        if t == "text.delta" and isinstance(c, dict):
            answer.append(c.get("data", ""))
        elif t == "message.delta" and isinstance(c, list) and c:
            f = c[0]
            if isinstance(f, dict):
                txt = f.get("text", {})
                if isinstance(txt, dict):
                    answer.append(txt.get("value", ""))

full = "".join(answer)
print("\nevent summary:", types)
print(f"ANSWER LEN = {len(full)}")
for h in ["【仿真方案】", "【代码】", "【理论对照】", "【运行说明】"]:
    print(f"  {'HAS' if h in full else 'MISS'} {h}  (pos={full.find(h)})")
has_code = "import numpy" in full or "import math" in full
print(f"  {'HAS' if has_code else 'MISS'} import 语句")
print(f"fences={full.count(chr(96)*3)}")
print("--- head 300 ---")
print(full[:300])
print("--- tail 200 ---")
print(full[-200:])
