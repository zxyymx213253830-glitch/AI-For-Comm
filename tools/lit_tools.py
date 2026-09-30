# -*- coding: utf-8 -*-
"""
文献检索工具 —— 把 core/lit_search 的公网双源检索注册成 Agent 可自主调用的工具
"""
from tools.registry import tool
from core.lit_search import search_literature


@tool(
    "search_papers",
    "公网学术文献检索（arXiv + Semantic Scholar 双源，返回标题/作者/年份/摘要/链接）",
    {"query": "英文检索效果最佳，如 'LDPC channel coding 5G NR'",
     "top_k": "返回条数，1 到 8，默认 5"},
)
def search_papers(query: str, top_k: int = 5):
    k = max(1, min(int(top_k or 5), 8))
    papers = search_literature(str(query), max_results=k)
    if not papers:
        return {"文献": [], "说明": "未检索到结果，可换英文检索词或放宽主题再试"}
    slim = [{
        "标题": p["title"],
        "作者": "、".join(p["authors"][:3]) + ("等" if len(p["authors"]) > 3 else ""),
        "年份": p["year"],
        "来源": p["source"],
        "摘要": (p["abstract"] or "无摘要")[:200],
        "链接": p["url"],
    } for p in papers[: 2 * k]]
    return {"文献": slim, "说明": f"共检索到 {len(slim)} 篇（双源去重后）"}
