# -*- coding: utf-8 -*-
"""
公网文献检索模块 —— arXiv + Semantic Scholar 双源
（整合自同学项目 AI_agents_programme/core/lit_search.py，实现保持一致）

本地执行，不依赖 OpenTrek 平台。供 lit_review_agent 在调用前做公网检索，
把检索结果注入 Prompt（RAG 式增强）。

- arXiv:             官方 API，公开免费，无需 key
- Semantic Scholar:  Graph API，公开免费（有限流）；可设置环境变量 S2_API_KEY 提高配额
- 异常兜底：一个源失败不影响另一个；两个都失败时返回空列表（调用方退化为纯平台 KB）

返回统一结构：
    [{"title": str, "authors": [str], "year": int|None,
      "abstract": str, "doi": str|None, "url": str}, ...]
"""
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import os
import ssl
import time

# ── Semantic Scholar API Key（可选）──────────────────
S2_API_KEY = os.environ.get("S2_API_KEY", "")

# ── 超时（秒）───────────────────────────────────────
TIMEOUT = 15
# Semantic Scholar 单独用更短超时：它常在工具回环里被调用，卡 30s 会拖死流水线
S2_TIMEOUT = 8
# 429 是 IP 级限流，重试基本无用：命中后进入冷却期直接跳过该源
S2_COOLDOWN_SEC = 600
_s2_cooldown_until = 0.0

# ── SSL 兜底：本机缺 CA 证书时退化为不验证 ──
_UNVERIFIED_CTX = ssl._create_unverified_context()


def _open(url: str, headers: dict, timeout: int = TIMEOUT):
    """带 SSL 兜底的 urlopen：默认验证失败 → 不验证重试；超时重试 1 次"""
    req = urllib.request.Request(url, headers=headers)
    last_err = None
    for _ in range(2):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            if isinstance(e.reason, ssl.SSLCertVerificationError):
                return urllib.request.urlopen(req, timeout=timeout, context=_UNVERIFIED_CTX)
    raise last_err


# ═══════════════════════════════════════════════════
#  arXiv
# ═══════════════════════════════════════════════════

def search_arxiv(query: str, max_results: int = 5, sort_by: str = "relevance") -> list:
    """通过 arXiv API 检索论文。

    Args:
        query:      检索词（支持 arXiv 语法，如 all:"LDPC" AND cat:cs.IT）
        max_results: 返回条数（1~10）
        sort_by:    relevance / submittedDate
    Returns:
        统一结构的文献列表
    """
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)

    try:
        with _open(url, {"User-Agent": "lit-review-agent/1.0"}) as resp:
            xml_text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[lit_search] arXiv 检索失败: {e}")
        return []

    # 解析 Atom XML
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"[lit_search] arXiv XML 解析失败: {e}")
        return []

    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
        summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
        published = entry.findtext("atom:published", "", ns)
        year = int(published[:4]) if published and published[:4].isdigit() else None
        authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
        link = entry.findtext("atom:id", "", ns).strip()  # 形如 http://arxiv.org/abs/xxxx
        doi = None
        # arXiv 新版本会带 arxiv:doi 字段
        for el in entry.iter():
            if el.tag.endswith("doi"):
                doi = el.text
                break
        papers.append({
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": summary,
            "doi": doi,
            "url": link,
            "source": "arXiv",
        })
    return papers[:max_results]


# ═══════════════════════════════════════════════════
#  Semantic Scholar
# ═══════════════════════════════════════════════════

def search_semantic_scholar(query: str, limit: int = 5) -> list:
    """通过 Semantic Scholar Graph API 检索论文（含 IEEE 元数据）。

    Args:
        query: 检索词（英文效果最佳）
        limit: 返回条数（1~10）
    Returns:
        统一结构的文献列表（限流冷却期内直接返回空，不阻塞调用方）
    """
    global _s2_cooldown_until
    params = {
        "query": query,
        "limit": min(limit, 10),
        "fields": "title,authors,year,abstract,url,externalIds,venue",
    }
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)

    headers = {"User-Agent": "lit-review-agent/1.0"}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY

    # 无 key 且处于限流冷却期 → 直接放弃该源（arXiv 已能独力交付）
    if not S2_API_KEY and time.time() < _s2_cooldown_until:
        print("[lit_search] Semantic Scholar 限流冷却中，跳过该源")
        return []

    # 429 只再试一次（短退避）；仍失败则进冷却期，避免每次检索都白等几十秒
    data = None
    for attempt in (1, 2):
        try:
            with _open(url, headers, timeout=S2_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 1 and not S2_API_KEY:
                print("[lit_search] Semantic Scholar 429 限流，2s 后再试一次")
                time.sleep(2)
                continue
            print(f"[lit_search] Semantic Scholar HTTP {e.code}: "
                  f"{e.read().decode(errors='replace')[:150]}")
            if e.code == 429 and not S2_API_KEY:
                _s2_cooldown_until = time.time() + S2_COOLDOWN_SEC
                print(f"[lit_search] Semantic Scholar 进入 {S2_COOLDOWN_SEC}s 冷却期")
            return []
        except Exception as e:
            print(f"[lit_search] Semantic Scholar 检索失败: {e}")
            return []
    if data is None:
        return []

    papers = []
    for p in data.get("data", []) or []:
        authors = [a.get("name", "") for a in (p.get("authors") or [])]
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI") or p.get("doi")
        papers.append({
            "title": p.get("title", ""),
            "authors": authors,
            "year": p.get("year"),
            "abstract": p.get("abstract") or "",
            "doi": doi,
            "url": p.get("url") or (f"https://doi.org/{doi}" if doi else ""),
            "source": "SemanticScholar",
        })
    return papers[:limit]


# ═══════════════════════════════════════════════════
#  统一入口
# ═══════════════════════════════════════════════════

def search_literature(query: str, max_results: int = 5) -> list:
    """双源并行检索：arXiv + Semantic Scholar，去重合并。

    Args:
        query:      检索词
        max_results: 每源条数（总返回 ≤ 2×）
    Returns:
        统一结构的文献列表
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Semantic Scholar 对英文效果最好；arXiv 接受带引号检索
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_arxiv = pool.submit(search_arxiv, query, max_results=max_results)
        f_s2 = pool.submit(search_semantic_scholar, query, limit=max_results)

        papers = []
        for fut in as_completed([f_arxiv, f_s2]):
            try:
                papers += fut.result()
            except Exception as e:
                print(f"[lit_search] 某源失败: {e}")

    # 按 DOI/URL 去重（arXiv 预印本与已发表可能重复）
    seen = set()
    dedup = []
    for p in papers:
        key = p["doi"] or p["url"] or p["title"][:50]
        if key in seen:
            continue
        seen.add(key)
        dedup.append(p)
    return dedup


def format_references(papers: list) -> str:
    """把文献列表格式化成可注入 Prompt 的文本。"""
    if not papers:
        return ""
    lines = ["【公网检索到的相关文献】"]
    for i, p in enumerate(papers, 1):
        authors = "、".join(p["authors"][:3]) + (" 等" if len(p["authors"]) > 3 else "")
        year = p["year"] or "N/A"
        doi = f", DOI: {p['doi']}" if p["doi"] else ""
        lines.append(
            f"{i}. [{p['source']}] {p['title']} — {authors}, {year}{doi}"
            f"\n    摘要: {(p['abstract'] or '无摘要')[:180]}"
        )
    lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════
#  自测入口：python core/lit_search.py "LDPC 5G NR"
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "LDPC channel coding 5G NR"
    print(f"检索: {q}\n")
    t0 = time.time()
    res = search_literature(q, max_results=3)
    print(f"耗时 {time.time()-t0:.1f}s, 共 {len(res)} 条:\n")
    print(format_references(res))
