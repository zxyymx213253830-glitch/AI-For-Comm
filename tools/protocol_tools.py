# -*- coding: utf-8 -*-
"""
协议查询工具 —— 本地知识库优先 + 公网文献兜底的通信协议检索

查询顺序：
1) 本地 knowledge/ 与 prompts/ 目录的 Markdown 资料（毫秒级，离线可用）
2) 本地无命中时走公网学术检索（arXiv/semantic Scholar，命中标准相关论文与提案）
"""
import os
import re

from tools.registry import tool

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIRS = [os.path.join(_ROOT, "knowledge"), os.path.join(_ROOT, "prompts")]

_MD_CACHE = {}  # 文件路径 -> (mtime, 段落列表)


def _load_sections():
    """加载并缓存所有 Markdown 的段落（按二级标题切分）。"""
    global _MD_CACHE
    sections = []
    for d in _DIRS:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                path = os.path.join(root, fn)
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if path not in _MD_CACHE or _MD_CACHE[path][0] != mtime:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    parts = re.split(r"(?=^#{1,3} )", text, flags=re.M)
                    _MD_CACHE[path] = (mtime, [p.strip() for p in parts if p.strip()])
                for i, sec in enumerate(_MD_CACHE[path][1]):
                    sections.append((os.path.relpath(path, _ROOT), i, sec))
    return sections


def _score(section: str, keywords: list) -> int:
    low = section.lower()
    return sum(low.count(k.lower()) for k in keywords if k)


@tool(
    "protocol_lookup",
    "通信协议/标准知识查询：优先命中本地知识库（协议要点、公式、规范摘录），本地无结果时自动转公网学术检索",
    {"query": "查询主题，如 'LDPC 码率' / '5G NR 信道编码' / '香农容量' / 'OFDM 子载波间隔'",
     "top_k": "返回条数，1~5，默认 3"},
)
def protocol_lookup(query: str, top_k: int = 3):
    k = max(1, min(int(top_k or 3), 5))
    # 关键词切分：中文按 2~4 字滑窗 + 英文单词整体
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-/]+|[\u4e00-\u9fff]{2,4}", str(query))
    if not words:
        words = [str(query)]

    hits = []
    for rel, idx, sec in _load_sections():
        s = _score(sec, words)
        if s > 0:
            hits.append((s, rel, sec))
    hits.sort(key=lambda t: -t[0])
    picked = hits[:k]

    if picked:
        return {
            "来源": "本地知识库",
            "条目": [{
                "文件": rel,
                "内容": sec[:1200] + ("…" if len(sec) > 1200 else ""),
            } for _, rel, sec in picked],
            "说明": "命中本地资料，引用时注明知识来源即可",
        }

    # 本地无命中 → 公网学术检索兜底
    from core.lit_search import search_literature, format_references
    papers = search_literature(f"3GPP {query}", max_results=k)
    if not papers:
        papers = search_literature(str(query), max_results=k)
    if not papers:
        return {"来源": "无", "说明": "本地知识库与公网检索均未命中，请更换关键词"}
    return {"来源": "公网学术检索（本地知识库无命中）",
            "条目": format_references(papers)}
