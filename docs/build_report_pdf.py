# -*- coding: utf-8 -*-
"""结课汇报书构建：以 `项目结课汇报书.md` 为唯一内容源 → HTML（屏幕态）+ PDF（打印态）

用法：
    python docs/build_report_pdf.py            # 生成 docs/项目结课汇报书.html 与 .pdf
    python docs/build_report_pdf.py --check     # 生成后逐页统计字符数，自检空页

依赖：markdown、playwright（系统 Chrome）、pypdf

设计要点（09-03 重建原因）：
  旧脚本以 `项目结课汇报.html`（一份 14 页摘要版）为源渲染 PDF，与不断增长的
  `.md` 正文完全脱节——文稿改了 PDF 不变，且摘要版每节强制分页产生大量空页。
  现在 .md 是唯一真源，HTML 与 PDF 都由它生成，两者内容必然一致；
  分页只发生在「封面之后」与「每章之前」，表格与代码块内部不断页。
"""
import os
import re
import sys

import markdown
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "项目结课汇报书.md")
OUT_HTML = os.path.join(HERE, "项目结课汇报书.html")
OUT_PDF = os.path.join(HERE, "项目结课汇报书.pdf")

BODY_MARGIN = {"top": "20mm", "bottom": "18mm", "left": "19mm", "right": "19mm"}
ZERO_MARGIN = {"top": "0", "bottom": "0", "left": "0", "right": "0"}

HEADER_TPL = (
    '<div style="width:100%; font-size:7.5px; color:#8b93a1; '
    "font-family:'Microsoft YaHei',sans-serif; padding:0 19mm; "
    'display:flex; justify-content:space-between;">'
    '<span>AI for Comm · 项目结课汇报书</span>'
    '<span>通信领域多智能体科研协作系统</span></div>'
)
FOOTER_TPL = (
    '<div style="width:100%; font-size:8px; color:#8b93a1; '
    "font-family:'Microsoft YaHei',sans-serif; text-align:center;\">"
    '<span class="pageNumber"></span> / <span class="totalPages"></span></div>'
)

# ── 靛蓝瓷主题（与研究报告 HTML 同源配色） ─────────────────────────
CSS = """
:root{
  --ink:#0a1f3d; --ink-tint:#152a4a; --paper:#f1f3f5; --paper-tint:#e6eaee;
  --gold:#c9973f; --gold-soft:#e3c88f; --text:#1a2332; --muted:#5b6472;
  --line:#d7dce2; --serif:"Songti SC","STSong","SimSun",serif;
  --sans:"PingFang SC","Microsoft YaHei",sans-serif;
  --mono:"JetBrains Mono","Consolas","Courier New",monospace;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--paper);color:var(--text);font-family:var(--sans);
  text-rendering:optimizeLegibility;}
body{line-height:1.78;font-size:10.5pt;-webkit-print-color-adjust:exact;print-color-adjust:exact;}

/* ── 封面 ── */
.cover{width:210mm;height:296mm;background:var(--ink);color:#e9edf2;
  display:flex;flex-direction:column;justify-content:center;
  padding:26mm 22mm;position:relative;overflow:hidden;}
.cover::before{content:"";position:absolute;inset:0;
  background:radial-gradient(ellipse 120% 60% at 85% -10%,rgba(201,151,63,.18),transparent 60%),
             radial-gradient(ellipse 90% 45% at -10% 110%,rgba(21,42,74,.95),transparent 65%);}
.cover::after{content:"";position:absolute;right:-60mm;top:-40mm;width:180mm;height:180mm;
  border:1px solid rgba(201,151,63,.16);border-radius:50%;}
.cover>*{position:relative;}
.cover .kicker{font-size:12px;letter-spacing:.34em;color:var(--gold);margin-bottom:24px;}
.cover h1{font-family:var(--serif);font-size:41px;font-weight:700;line-height:1.34;margin-bottom:16px;}
.cover .subtitle{font-size:15.5px;color:#b6c2d4;letter-spacing:.05em;margin-bottom:34px;}
.cover .rule{width:52mm;height:2px;background:var(--gold);margin-bottom:30px;}
.cover .meta{font-size:11.5px;color:#93a2b8;line-height:2.05;}
.cover .meta b{color:#dfe6ef;font-weight:600;}
.cover .claim{margin-top:34px;padding:13px 16px;border-left:2px solid var(--gold);
  background:rgba(201,151,63,.07);font-size:10.5px;color:#a9b6c8;line-height:1.85;}
.cover .foot{position:absolute;bottom:20mm;left:22mm;right:22mm;
  display:flex;justify-content:space-between;font-size:9.5px;color:#6d7d94;
  border-top:1px solid rgba(255,255,255,.1);padding-top:11px;}

/* ── 目录 ── */
.toc{padding:2mm 0 6mm;}
.toc h2{font-family:var(--serif);font-size:20px;color:var(--ink);
  border-bottom:2px solid var(--gold);padding-bottom:7px;margin-bottom:14px;
  page-break-before:auto;break-before:auto;}
.toc ol{list-style:none;columns:2;column-gap:9mm;}
.toc li{break-inside:avoid;font-size:9.6px;line-height:1.62;padding:2.2px 0;color:var(--text);}
.toc li.l2{font-weight:700;color:var(--ink);margin-top:6px;}
.toc li.l2 .no{color:var(--gold);font-family:var(--mono);margin-right:6px;}
.toc li.l3{padding-left:13px;color:var(--muted);}
.toc li.l3 .no{font-family:var(--mono);margin-right:5px;color:#9aa4b2;}

/* ── 正文 ── */
.body{padding:0;}
.body h2{font-family:var(--serif);font-size:19px;color:var(--ink);
  margin:0 0 11px;padding:0 0 7px;border-bottom:2px solid var(--gold);
  page-break-before:always;break-before:page;page-break-after:avoid;break-after:avoid;}
.body h2 .no{color:var(--gold);font-family:var(--mono);font-size:15px;
  letter-spacing:.06em;margin-right:9px;}
.body h3{font-size:13px;color:var(--ink);margin:15px 0 7px;padding-left:9px;
  border-left:3px solid var(--gold);page-break-after:avoid;break-after:avoid;}
.body h3 .no{color:var(--gold);font-family:var(--mono);margin-right:6px;}
.body h4{font-size:11.2px;color:var(--ink-tint);margin:11px 0 5px;
  page-break-after:avoid;break-after:avoid;}
.body p{margin:0 0 7.5px;text-align:left;}
.body ul,.body ol{margin:0 0 8px 20px;page-break-inside:avoid;break-inside:avoid;}
.body li{margin-bottom:3.2px;text-align:left;}
.body strong{color:var(--ink);font-weight:700;}
.body em{color:var(--ink-tint);}
.body a{color:#1d5fa8;text-decoration:none;}
.body code{font-family:var(--mono);font-size:.88em;background:var(--paper-tint);
  color:#8a5a12;padding:1px 4px;border-radius:2px;}
.body pre{background:#0d1b2f;color:#dfe6ef;padding:10px 12px;border-radius:3px;
  margin:0 0 9px;overflow:hidden;page-break-inside:avoid;break-inside:avoid;
  border-left:3px solid var(--gold);}
.body pre code{background:none;color:inherit;padding:0;font-size:8.6px;line-height:1.62;
  white-space:pre-wrap;word-break:break-word;
  /* 架构图含中文，须用全角=2×半角的等宽中文字体，否则制表符与中文宽度不一致会错位 */
  font-family:"Sarasa Mono SC","NSimSun","SimSun",monospace;}
.body blockquote{margin:0 0 9px;padding:8px 13px;background:#fff;
  border-left:3px solid var(--gold-soft);color:var(--muted);font-size:9.9px;
  page-break-inside:avoid;break-inside:avoid;}
.body blockquote p{margin:0 0 3px;}
.body hr{border:none;border-top:1px solid var(--line);margin:13px 0;}
.body table{width:100%;border-collapse:collapse;margin:0 0 10px;font-size:9.1px;
  line-height:1.55;background:#fff;page-break-inside:auto;}
.body thead{display:table-header-group;}
.body tr{page-break-inside:avoid;break-inside:avoid;}
.body th{background:var(--ink);color:#eef2f7;font-weight:600;text-align:left;
  padding:5px 7px;border:1px solid var(--ink-tint);font-size:9px;}
.body td{padding:4.5px 7px;border:1px solid var(--line);vertical-align:top;
  word-break:break-word;}
.body tbody tr:nth-child(even) td{background:#f7f9fb;}
.body table code{font-size:8.4px;}
"""


def split_front_matter(md_text):
    """把 md 拆成 (封面素材 dict, 正文 md)。正文从第一个 `## ` 开始。"""
    lines = md_text.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    head, body = lines[:idx], "\n".join(lines[idx:])

    title = next((l[2:].strip() for l in head if l.startswith("# ")), "项目结课汇报书")
    quotes = [re.sub(r"^>\s?", "", l).strip() for l in head if l.startswith(">")]
    quotes = [q for q in quotes if q]
    subtitle = re.sub(r"\*\*", "", quotes[0]) if quotes else ""
    metas = [re.sub(r"\*\*", "", q) for q in quotes[1:]]
    claim = metas[-1] if len(metas) > 2 else ""
    meta_lines = metas[:-1] if claim else metas
    return {"title": title, "subtitle": subtitle,
            "metas": meta_lines, "claim": claim}, body


_SPECIAL = re.compile(
    r"^(\s*```|#{1,6}\s|\s*\||\s*-{3,}\s*$|\s*$|\s*[-*+]\s+|\s*\d+[.、)]\s+)")
_ASCII_TAIL = re.compile(r"[A-Za-z0-9)\]%]$", re.ASCII)
_ASCII_HEAD = re.compile(r"^[A-Za-z0-9(\[]", re.ASCII)


def join_soft_wraps(md_text):
    """合并段落内的手动软换行。

    文稿是按 40~50 字手动折行写的，直接交给 Markdown 渲染会在每个折行处留下
    一个空格，中文段落因此显得松散。这里在非代码块区域把软换行拼回去：
    中英文交界处补空格，纯中文交界直接相连。
    """
    out, fence = [], False
    lines = md_text.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip().startswith("```"):
            fence = not fence
            out.append(ln)
            continue
        if fence or _SPECIAL.match(ln) or not out or out[-1] == "\x00":
            out.append(ln)
            continue
        prev = out[-1]
        if not prev.strip() or _SPECIAL.match(prev):
            out.append(ln)
            continue
        gap = " " if (_ASCII_TAIL.search(prev) and _ASCII_HEAD.match(ln)) else ""
        out[-1] = prev.rstrip() + gap + ln.strip()
    return "\n".join(out)


def md_to_html(md_body):
    """md → HTML 片段，并把章号/节号拆成可着色的 span。"""
    html = markdown.markdown(
        join_soft_wraps(md_body),
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )

    def chapter(m):
        return f'<h2><span class="no">{m.group(1)}</span>{m.group(2)}</h2>'

    def section(m):
        return f'<h3><span class="no">{m.group(1)}</span>{m.group(2)}</h3>'

    html = re.sub(r"<h2>(\d{2})\s*(.*?)</h2>", chapter, html, flags=re.S)
    html = re.sub(r"<h3>(\d+\.\d+)\s*(.*?)</h3>", section, html, flags=re.S)
    return html


def build_toc(md_body):
    """从正文提取 h2/h3 生成目录条目。"""
    items = []
    for m in re.finditer(r"^(#{2,3})\s+(.+?)\s*$", md_body, re.M):
        level = len(m.group(1))
        text = re.sub(r"[*`]", "", m.group(2)).strip()
        no, _, name = text.partition(" ")
        if level == 2 and re.fullmatch(r"\d{2}", no):
            items.append(f'<li class="l2"><span class="no">{no}</span>{name}</li>')
        elif level == 3 and re.fullmatch(r"\d+\.\d+", no):
            items.append(f'<li class="l3"><span class="no">{no}</span>{name}</li>')
        else:
            items.append(f'<li class="l{"level"}">{text}</li>')
    return '<nav class="toc"><h2>目录</h2><ol>' + "".join(items) + "</ol></nav>"


def cover_section(cover):
    metas = "".join(f"<div>{m}</div>" for m in cover["metas"])
    claim = f'<div class="claim">{cover["claim"]}</div>' if cover["claim"] else ""
    return f"""<section class="cover">
  <div class="kicker">AI 创新大赛 · 结课汇报</div>
  <h1>{cover['title']}</h1>
  <div class="subtitle">{cover['subtitle'].split('·')[0].strip()}</div>
  <div class="rule"></div>
  <div class="meta">{metas}</div>
  {claim}
  <div class="foot"><span>AI for Comm</span><span>阿里云专有云 OpenTrek Agent Dev</span></div>
</section>"""


def page(extra_css, inner, title="AI for Comm 项目结课汇报书"):
    return (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1.0">'
            f'<title>{title}</title><style>{CSS}\n{extra_css}</style></head>'
            f'<body>{inner}</body></html>')


COVER_CSS = "@page{size:A4;margin:0;}\nhtml,body{background:#0a1f3d;}"
PRINT_CSS = "@page{size:A4;margin:20mm 19mm 18mm;}\nbody{background:#fff;font-size:10.2pt;}"
SCREEN_CSS = """@media screen{
  body{background:var(--paper);padding:24px 0;}
  .cover{margin:0 auto 24px;border-radius:3px;box-shadow:0 2px 24px rgba(10,31,61,.22);}
  .wrap{max-width:1000px;margin:0 auto;padding:26px 34px 64px;background:#fff;
        box-shadow:0 2px 22px rgba(10,31,61,.13);border-radius:3px;}
  .body{font-size:11pt;}
}"""


def print_pdf(pw, html_path, pdf_path, margin, header="", footer=""):
    browser = pw.chromium.launch(channel="chrome")
    page = browser.new_page()
    page.goto("file:///" + html_path.replace("\\", "/"))
    page.wait_for_timeout(700)
    page.pdf(path=pdf_path, format="A4", print_background=True, margin=margin,
             display_header_footer=bool(header),
             header_template=header, footer_template=footer,
             prefer_css_page_size=False)
    browser.close()


def check_pages(pdf_path):
    """逐页统计可提取字符数，暴露空页与孤儿页。"""
    reader = PdfReader(pdf_path)
    print(f"\n逐页字符数（共 {len(reader.pages)} 页）：")
    thin = []
    for i, p in enumerate(reader.pages, 1):
        txt = (p.extract_text() or "").strip()
        flag = ""
        if i > 1 and len(txt) < 260:
            flag = "  ← 偏空"
            thin.append(i)
        head = re.sub(r"\s+", " ", txt)[:44]
        print(f"  {i:02d} {len(txt):5d} | {head}{flag}")
    if thin:
        print(f"\n[!] 偏空页：{thin}")
    else:
        print("\n[OK] 无偏空页")


def main():
    do_check = "--check" in sys.argv
    md_text = open(SRC, encoding="utf-8").read()
    cover, md_body = split_front_matter(md_text)
    toc = build_toc(md_body)
    body = md_to_html(md_body)

    tmp_body = os.path.join(HERE, "_rb.html")
    tmp_cover = os.path.join(HERE, "_rc.html")
    tmp_body_pdf = os.path.join(HERE, "_rb.pdf")
    tmp_cover_pdf = os.path.join(HERE, "_rc.pdf")

    cover_sec = cover_section(cover)
    main_sec = f'<main class="body">{body}</main>'
    open(tmp_cover, "w", encoding="utf-8").write(page(COVER_CSS, cover_sec))
    open(tmp_body, "w", encoding="utf-8").write(page(PRINT_CSS, toc + main_sec))

    # 屏幕阅读态 HTML：封面 + 目录 + 正文合成一份，双击即可看
    open(OUT_HTML, "w", encoding="utf-8").write(
        page(SCREEN_CSS, cover_sec + f'<div class="wrap">{toc}{main_sec}</div>'))

    with sync_playwright() as pw:
        print_pdf(pw, tmp_cover, tmp_cover_pdf, ZERO_MARGIN)
        print_pdf(pw, tmp_body, tmp_body_pdf, BODY_MARGIN, HEADER_TPL, FOOTER_TPL)

    writer = PdfWriter()
    for p in PdfReader(tmp_cover_pdf).pages:
        writer.add_page(p)
    for p in PdfReader(tmp_body_pdf).pages:
        writer.add_page(p)
    with open(OUT_PDF, "wb") as f:
        writer.write(f)

    for f in (tmp_cover, tmp_body, tmp_cover_pdf, tmp_body_pdf):
        if os.path.exists(f):
            os.remove(f)

    n = len(PdfReader(OUT_PDF).pages)
    print(f"完成: {os.path.basename(OUT_HTML)}  {os.path.getsize(OUT_HTML)/1024:.0f} KB")
    print(f"完成: {os.path.basename(OUT_PDF)}  共 {n} 页, {os.path.getsize(OUT_PDF)/1024:.0f} KB")
    if do_check:
        check_pages(OUT_PDF)


if __name__ == "__main__":
    main()
