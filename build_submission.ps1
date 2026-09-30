# ============================================================
#  AI for Comm · 交付包构建
#  把仓库当前状态同步进 最终提交材料\
#
#  用法： powershell -ExecutionPolicy Bypass -File build_submission.ps1
#
#  约定：
#    1. 本脚本只新增与覆盖，不删除任何文件；
#       包内多余文件请用 clean_submission.ps1 -Yes 处理。
#    2. 交付包内所有文件都能在仓库里找到源（无孤本），
#       否则下次构建就会与包内实际脱节。
#    3. 项目文档三态同源：先跑 docs\build_report_pdf.py 生成
#       HTML 与 PDF，再跑本脚本，三者内容必然一致。
#    4. 过程性材料（运行日志、评测原始结果、验证截图、排查记录、
#       历史存档）保留在仓库 中间材料\ 与 logs\，不随包提交。
# ============================================================
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dst  = Join-Path $Root '最终提交材料'
$Code = Join-Path $Dst '代码'
$Doc  = Join-Path $Dst '项目文档'
$Demo = Join-Path $Dst '演示成果'

# 演示成果收录的四份研究报告：不取“最新 N 份”，而是四份有代表性的样本
# （改造前基线 → 双坑修复后复跑 → 第二个题材 → 分段统稿改造后首份跨领域报告）
# 改动时请同步修改 clean_submission.ps1 里的同名白名单
$Reports = @(
    'research_20260901_234713.html',   # BPSK/AWGN 基线，正文最丰满的一份
    'research_20260902_003653.html',   # 同课题复跑：统稿双坑修复后
    'research_20260902_215747.html',   # LDPC 码在 5G NR 中的应用：第二个题材
    'research_20260902_225648.html'    # PUSCH 链路预算：分段统稿改造后首份跨领域报告
)
$ReportCount = $Reports.Count


function Copy-Tree {
    param([string]$SrcDir, [string]$DstDir)
    if (-not (Test-Path $SrcDir)) { Write-Warning "源目录缺失，跳过：$SrcDir"; return }
    New-Item -ItemType Directory -Force -Path $DstDir | Out-Null
    robocopy $SrcDir $DstDir /E /XD __pycache__ .pytest_cache .qoder .git `
        /XF *.pyc /NFL /NDL /NJH /NJS /NP /R:1 /W:1 | Out-Null
    # robocopy 退出码 0~7 均为成功（8 起才是错误）
    if ($LASTEXITCODE -ge 8) { throw "robocopy 失败（$LASTEXITCODE）：$SrcDir" }
    $global:LASTEXITCODE = 0
}


function Copy-File {
    param([string]$Src, [string]$DstDir)
    if (-not (Test-Path $Src)) { Write-Warning "源文件缺失，跳过：$Src"; return }
    New-Item -ItemType Directory -Force -Path $DstDir | Out-Null
    Copy-Item $Src $DstDir -Force
}


Write-Host "=== 交付包构建 ===" -ForegroundColor Cyan
Write-Host "源：$Root"
Write-Host "目标：$Dst`n"

# ── 1. 代码：九个目录 + 根文件 ──────────────────────────────
Write-Host "[1/4] 同步代码目录" -ForegroundColor Yellow
foreach ($d in 'core', 'agents', 'tools', 'prompts', 'web',
               'knowledge', 'skills', 'evals', 'tests') {
    Copy-Tree (Join-Path $Root $d) (Join-Path $Code $d)
}
foreach ($f in 'main.py', 'config.json', 'requirements.txt', 'Dockerfile',
               'docker-compose.yml', '.dockerignore', 'build_kb_json.py',
               '目录结构说明.md') {
    Copy-File (Join-Path $Root $f) $Code
}

# ── 2. 项目文档：汇报书三态 + 架构图 + 历史文档 + 构建脚本 ──
Write-Host "[2/4] 同步项目文档" -ForegroundColor Yellow
foreach ($f in '项目结课汇报书.md', '项目结课汇报书.html', '项目结课汇报书.pdf',
               'build_report_pdf.py', 'architecture.svg',
               'AI_for_Comm_项目方案书.pdf', 'AI_for_Comm_实践手册.pdf') {
    Copy-File (Join-Path $Root "docs\$f") $Doc
}

# ── 3. 演示成果：白名单四份研究报告 + 本地真跑的仿真图 ────────
Write-Host "[3/4] 同步演示成果" -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $Demo | Out-Null
foreach ($r in $Reports) {
    Copy-File (Join-Path $Root "outputs\$r") $Demo
}
Get-ChildItem (Join-Path $Root 'outputs\sim\*.png') -File |
    ForEach-Object { Copy-Item $_.FullName $Demo -Force; Write-Host "    + $($_.Name)" }
# 仿真值与理论值对照标杆图：源在验证截图目录，包内保持同名，避免产生孤本
Copy-File (Join-Path $Root 'docs\验证记录图片\bpsk_awgn_ber.png') $Demo

# ── 4. 汇总与一致性校验 ─────────────────────────────────────
Write-Host "[4/4] 校验" -ForegroundColor Yellow
$All = Get-ChildItem $Dst -Recurse -File
$Sum = ($All | Measure-Object Length -Sum).Sum
Write-Host ("    交付包合计：{0} 个文件，{1:N2} MB" -f $All.Count, ($Sum / 1MB))

foreach ($d in '项目文档', '演示成果', '代码') {
    $p = Join-Path $Dst $d
    if (Test-Path $p) {
        $f = Get-ChildItem $p -Recurse -File
        Write-Host ("      {0,-8} {1,4} 个 {2,8:N1} MB" -f $d, $f.Count,
            ((($f | Measure-Object Length -Sum).Sum) / 1MB))
    }
    else { Write-Warning "      $d 目录缺失" }
}

# 中间材料不入包：若历史构建残留该目录，提示走清理脚本
if (Test-Path (Join-Path $Dst '中间材料')) {
    Write-Warning "包内存在 中间材料\ 目录（不属于交付内容），请执行： powershell -File clean_submission.ps1 -Yes"
}

$ExpectDemo = $ReportCount + 3
$ActualDemo = (Get-ChildItem $Demo -File).Count
if ($ActualDemo -ne $ExpectDemo) {
    Write-Warning "演示成果应为 $ExpectDemo 份（$ReportCount 报告 + 3 图），实际 $ActualDemo 份"
    Write-Warning "多出的文件请执行： powershell -File clean_submission.ps1 -Yes"
}

$Must = @("$Doc\项目结课汇报书.md", "$Doc\项目结课汇报书.html", "$Doc\项目结课汇报书.pdf",
          "$Code\main.py", "$Code\config.json", "$Code\core\pipeline.py",
          "$Code\core\report.py", "$Code\tests\test_latex_escape.py",
          "$Dst\提交材料清单.md")
$Miss = $Must | Where-Object { -not (Test-Path $_) }
if ($Miss) { Write-Warning "关键文件缺失：`n    $($Miss -join "`n    ")" }
else { Write-Host "    关键文件齐备（$($Must.Count) 项）" -ForegroundColor Green }

# 交付包内的文档是否落后于仓库源（三态同源检查）
$MdSrc = Get-Item (Join-Path $Root 'docs\项目结课汇报书.md')
$PdfSrc = Get-Item "$Doc\项目结课汇报书.pdf" -ErrorAction SilentlyContinue
if ($PdfSrc -and $MdSrc.LastWriteTime -gt $PdfSrc.LastWriteTime) {
    Write-Warning "文稿比 PDF 新，请重跑： python docs\build_report_pdf.py"
}

Write-Host "`n=== 构建完成 ===" -ForegroundColor Cyan
