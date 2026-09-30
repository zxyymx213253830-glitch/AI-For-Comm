# -*- coding: utf-8 -*-
"""将 knowledge/sim/*.md 打包为 OpenTrek 知识库 JSON 导入格式"""
import json, uuid, os

ROOT = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.join(ROOT, "knowledge", "sim")

files = sorted(f for f in os.listdir(SIM_DIR) if f.endswith(".md"))
records = []
for name in files:
    path = os.path.join(SIM_DIR, name)
    with open(path, encoding="utf-8") as fp:
        text = fp.read()
    records.append({"sys_data_id": str(uuid.uuid4()), "content": text})
    print(f"已读取 {name} ({len(text)} 字符)")

out = os.path.join(ROOT, "outputs", "sim_kb_import.json")
with open(out, "w", encoding="utf-8") as fp:
    json.dump(records, fp, ensure_ascii=False)
print(f"输出: {out} 共 {len(records)} 条记录")
