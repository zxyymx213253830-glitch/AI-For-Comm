# -*- coding: utf-8 -*-
"""结课汇报书 PDF 构建：封面无边距渲染 + 正文页眉页脚页码渲染 → 合并
用法：python build_report_pdf.py   （依赖 playwright + 系统 Chrome + pypdf）"""
import re, os
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "项目结课汇报.html")
OUT = os.path.join(HERE, "项目结课汇报书.pdf")

BODY_MARGIN = {"top": "22mm", "bottom": "20mm", "left": "20mm", "right": "20mm"}
ZERO_MARGIN = {"top": "0", "bottom": "0", "left": "0", "right": "0"}


def split_source():
    """按封面注释标记拆出 (cover_html, body_html)"""
    html = open(SRC, encoding="utf-8").read()
    head = html.split("<!-- ================= 封面 ================= -->")[0]
    cover_part = re.search(r'(<!-- =+ 封面 =+ -->.*?)(<!-- =+ 封面结束 =+ -->)', html, re.S).group(1)
    body_part = re.split(r'<!-- =+ 封面结束 =+ -->', html, 1)[1]

    cover_css = "<style>html,body{margin:0;padding:0;}@page{size:A4;margin:0;}</style>"
    cover_html = head.replace("</head>", cover_css + "</head>") + cover_part + "</body></html>"

    css_no_page = re.sub(r'@page[^{]*\{(?:[^{}]|\{[^{}]*\})*\}', '', head)
    body_html = css_no_page + body_part + "</body></html>"
    return cover_html, body_html


def render(pw, html_path, pdf_path, margin, header_tpl="", footer_tpl=""):
    browser = pw.chromium.launch(channel="chrome")
    page = browser.new_page()
    page.goto("file:///" + html_path.replace("\\", "/"))
    page.wait_for_timeout(800)
    page.pdf(path=pdf_path, format="A4", print_background=True, margin=margin,
             display_header_footer=bool(header_tpl),
             header_template=header_tpl, footer_template=footer_tpl)
    browser.close()


def main():
    tmp = lambda n: os.path.join(HERE, n)
    cover_html, body_html = split_source()
    open(tmp("_rc.html"), "w", encoding="utf-8").write(cover_html)
    open(tmp("_rb.html"), "w", encoding="utf-8").write(body_html)

    header = ('<div style="width:100%; font-size:7.5px; color:#888780; font-family:\'Microsoft YaHei\';'
              ' padding:0 20mm; display:flex; justify-content:space-between;">'
              '<span>AI for Comm · 项目结课汇报书</span><span>通信领域多智能体科研协作系统</span></div>')
    footer = ('<div style="width:100%; font-size:8px; color:#888780; font-family:\'Microsoft YaHei\';'
              ' text-align:center;"><span class="pageNumber"></span></div>')

    with sync_playwright() as pw:
        render(pw, tmp("_rc.html"), tmp("_rc.pdf"), ZERO_MARGIN)
        render(pw, tmp("_rb.html"), tmp("_rb.pdf"), BODY_MARGIN, header, footer)

    writer = PdfWriter()
    for p in PdfReader(tmp("_rc.pdf")).pages:
        writer.add_page(p)
    for p in PdfReader(tmp("_rb.pdf")).pages:
        writer.add_page(p)
    with open(OUT, "wb") as f:
        writer.write(f)

    for f in ("_rc.html", "_rb.html", "_rc.pdf", "_rb.pdf"):
        os.remove(tmp(f))
    n = len(PdfReader(OUT).pages)
    print(f"完成: {os.path.basename(OUT)}  共 {n} 页, {os.path.getsize(OUT)/1024:.0f} KB")


if __name__ == "__main__":
    main()
