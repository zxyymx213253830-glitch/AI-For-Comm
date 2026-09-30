# -*- coding: utf-8 -*-
"""
hw_agent 空回复问题调试脚本

目标：
  1. 用与 AgentNode 相同的方式调用 hw_agent（createSession → /run stream）
  2. 逐行打印 SSE 原始事件（类型 + 内容摘要），统计事件分布
  3. 复现"空回复"并定位是平台侧问题还是解析侧问题

用法：
  python tests/test_hw_debug.py            # 默认任务
  python tests/test_hw_debug.py simple     # 简单问候任务（对照）
"""
import sys
import os
import json
import urllib.request
import urllib.error
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import OPENTREK_BASE_URL, APP_KEY, REQUEST_TIMEOUT, AGENTS

hw = AGENTS["hw_agent"]
AGENT_CODE, AGENT_VERSION = hw["agentCode"], hw["agentVersion"]

TASK_HW = "编写一个同步 FIFO 的 Verilog 模块，深度 16、位宽 8，请直接输出完整代码。"
TASK_SIMPLE = "你好，请用一句话自我介绍。"


def post(path: str, body: dict) -> dict:
    url = f"{OPENTREK_BASE_URL}/{path}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {APP_KEY}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def run_session(task: str) -> None:
    print("=" * 60)
    print(f"  hw_agent debug   code={AGENT_CODE}  ver={AGENT_VERSION}")
    print(f"  task: {task}")
    print("=" * 60)

    # 1. createSession
    resp = post("createSession", {
        "agentCode": AGENT_CODE,
        "agentVersion": AGENT_VERSION,
    })
    if not resp.get("success"):
        print(f"[FAIL] createSession: {resp}")
        return
    session_id = resp["data"]["uniqueCode"]
    print(f"[OK] sessionId={session_id}")

    # 2. /run stream —— 原始读取，打印每个事件
    url = f"{OPENTREK_BASE_URL}/run"
    body = {
        "sessionId": session_id,
        "stream": True,
        "delta": True,
        "message": {"text": task, "metadata": {}, "attachments": []},
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {APP_KEY}",
                 "Content-Type": "application/json"},
        method="POST",
    )

    stats = collections.Counter()
    answer_parts = []
    raw_lines = 0

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as stream:
            buffer = ""
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    print("[EOF] connection closed")
                    break
                buffer += chunk.decode("utf-8", errors="replace")
                lines = buffer.split("\n")
                buffer = lines.pop()
                for line in lines:
                    raw_lines += 1
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload:
                        continue
                    if payload == "[DONE]":
                        stats["[DONE]"] += 1
                        continue
                    try:
                        obj = json.loads(payload)
                    except json.JSONDecodeError:
                        stats["[unparseable]"] += 1
                        print(f"  [RAW] {payload[:200]}")
                        continue

                    otype = obj.get("object", "?")
                    content = obj.get("content", {})
                    stats[otype] += 1

                    # 打印每个事件的类型 + 内容摘要
                    snippet = json.dumps(content, ensure_ascii=False)[:120]
                    print(f"  [{otype}] {snippet}")

                    if otype == "message.delta" and isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                tv = item.get("text", {}).get("value", "")
                                if tv:
                                    answer_parts.append(tv)
                    elif otype == "text.delta" and isinstance(content, dict):
                        d = content.get("data", "")
                        if d:
                            answer_parts.append(d)
                    elif otype == "complete":
                        print("  [complete] 流结束信号")
                        break
    except urllib.error.HTTPError as e:
        print(f"[FAIL] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:400]}")
        return
    except urllib.error.URLError as e:
        print(f"[FAIL] 网络错误: {e.reason}")
        return

    # 3. 汇总
    answer = "".join(answer_parts)
    print("-" * 60)
    print(f"  原始 SSE 行数: {raw_lines}")
    print(f"  事件统计: {dict(stats)}")
    print(f"  拼接回答长度: {len(answer)} 字符")
    if answer.strip():
        print(f"  回答前 300 字:\n{answer[:300]}")
    else:
        print("  [EMPTY REPLY] Agent 没有任何文本输出")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "hw"
    if mode == "simple":
        run_session(TASK_SIMPLE)
    else:
        run_session(TASK_HW)
