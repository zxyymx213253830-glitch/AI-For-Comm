# -*- coding: utf-8 -*-
"""
高规格 PDF 构建脚本（系统 Chrome 渲染）
方案书（上篇）+ 实践手册（下篇）双册构建
流程：封面单独渲染(无边距) + 正文渲染(页眉页脚页码) -> 目录页码回填 -> 合并
用法：python build_pdf.py
"""
import re, os
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))

DOCS = [
    {
        "src": "proposal.html",
        "out": "AI_for_Comm_项目方案书.pdf",
        "header_left": "AI for Comm · 项目方案书",
        "header_right": "上篇 · 构想与架构",
        "chapters": {
            "ch1": "01项目构想",
            "ch2": "02系统架构",
            "ch3": "03风险与对策",
            "ch4": "04任务清单",
            "chA": "A附录 · 参考资源与配套文档",
        },
    },
    {
        "src": "handbook.html",
        "out": "AI_for_Comm_实践手册.pdf",
        "header_left": "AI for Comm · 实践手册",
        "header_right": "下篇 · 操作与分工",
        "chapters": {
            "ch1": "01环境准备",
            "ch2": "02项目代码结构",
            "ch3": "03核心代码实现",
            "ch4": "04OpenTrek知识库搭建",
            "ch5": "05执行手册编写指南",
            "ch6": "06测试用例",
            "ch7": "07团队分工",
        },
    },
]

BODY_MARGIN = {"top": "22mm", "bottom": "20mm", "left": "20mm", "right": "20mm"}
ZERO_MARGIN = {"top": "0", "bottom": "0", "left": "0", "right": "0"}


def make_templates(left, right):
    header = (
        f'<div style="width:100%; font-size:7.5px; color:#888780; font-family:\'Microsoft YaHei\';'
        f' padding:0 20mm; display:flex; justify-content:space-between;">'
        f'<span>{left}</span><span>{right}</span></div>'
    )
    footer = (
        '<div style="width:100%; font-size:8px; color:#888780; font-family:\'Microsoft YaHei\';'
        ' text-align:center;"><span class="pageNumber"></span></div>'
    )
    return header, footer


def split_source(src_path):
    """返回 (cover_html, body_html)：封面无边距全幅；正文开头加空白占位页"""
    html = open(src_path, encoding="utf-8").read()
    head = html.split("<!-- ================= 封面 ================= -->")[0]
    cover_m = re.search(r'(<!-- =+ 封面 =+ -->.*?)(<!-- =+ 目录 =+ -->)', html, re.S)
    body_m = re.search(r'(<!-- =+ 目录 =+ -->.*)', html, re.S)
    cover_part, body_part = cover_m.group(1), body_m.group(1)

    cover_css = "<style>html,body{margin:0;padding:0;}@page{size:A4;margin:0;}</style>"
    cover_html = head.replace("</head>", cover_css + "</head>") + cover_part + "</body></html>"

    css_no_page = re.sub(r'@page[^{]*\{(?:[^{}]|\{[^{}]*\})*\}', '', head)
    blank = '<div style="page-break-after:always;"></div>'
    body_html = css_no_page + blank + body_part + "</body></html>"
    return cover_html, body_html


def render(pw, html_path, pdf_path, margin, header_tpl="", footer_tpl=""):
    browser = pw.chromium.launch(channel="chrome")
    page = browser.new_page()
    page.goto("file:///" + html_path.replace("\\", "/"))
    page.wait_for_timeout(800)
    page.pdf(
        path=pdf_path, format="A4", print_background=True,
        margin=margin,
        display_header_footer=bool(header_tpl),
        header_template=header_tpl,
        footer_template=footer_tpl,
    )
    browser.close()


def chapter_pages(pdf_path, chapters):
    """{ch: 绝对页码}（渲染页1为空白占位页，页码即最终PDF页码）"""
    reader = PdfReader(pdf_path)
    norm = lambda s: re.sub(r"[\s　]+", "", s or "")
    texts = [norm(p.extract_text()) for p in reader.pages]
    toc_page = next(i for i, t in enumerate(texts) if "目录" in t)  # 0-based
    result = {}
    for ch, title in chapters.items():
        key = norm(title)
        hits = [i for i, t in enumerate(texts) if key in t and i != toc_page]
        result[ch] = (hits[0] + 1) if hits else None  # 1-based
    return result


def fill_toc(body_html, pages):
    for ch, pg in pages.items():
        body_html = body_html.replace(f"@@PG_{ch}@@", str(pg) if pg else "—")
    return body_html


def build_doc(pw, cfg):
    src = os.path.join(HERE, cfg["src"])
    out = os.path.join(HERE, cfg["out"])
    tmp = lambda name: os.path.join(HERE, name)

    cover_html, body_html = split_source(src)
    open(tmp("_c.html"), "w", encoding="utf-8").write(cover_html)
    open(tmp("_b.html"), "w", encoding="utf-8").write(body_html)

    header_tpl, footer_tpl = make_templates(cfg["header_left"], cfg["header_right"])

    render(pw, tmp("_c.html"), tmp("_c.pdf"), ZERO_MARGIN)
    render(pw, tmp("_b.html"), tmp("_b.pdf"), BODY_MARGIN, header_tpl, footer_tpl)

    pages = chapter_pages(tmp("_b.pdf"), cfg["chapters"])
    print(f"  章节页码: {pages}")

    body_final = fill_toc(body_html, pages)
    open(tmp("_b.html"), "w", encoding="utf-8").write(body_final)
    render(pw, tmp("_b.html"), tmp("_bf.pdf"), BODY_MARGIN, header_tpl, footer_tpl)

    writer = PdfWriter()
    for p in PdfReader(tmp("_c.pdf")).pages:
        writer.add_page(p)
    body = PdfReader(tmp("_bf.pdf"))
    for i, p in enumerate(body.pages):
        if i == 0:
            continue  # 去空白占位页
        writer.add_page(p)
    with open(out, "wb") as f:
        writer.write(f)

    for f in ("_c.html", "_b.html", "_c.pdf", "_b.pdf", "_bf.pdf"):
        os.remove(tmp(f))

    n = len(PdfReader(out).pages)
    size = os.path.getsize(out) / 1024
    print(f"  完成: {cfg['out']}  共 {n} 页, {size:.0f} KB")


def main():
    with sync_playwright() as pw:
        for cfg in DOCS:
            print(f"构建 {cfg['src']} -> {cfg['out']}")
            build_doc(pw, cfg)


if __name__ == "__main__":
    main()
