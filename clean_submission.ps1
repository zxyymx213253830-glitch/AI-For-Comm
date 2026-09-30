# ============================================================
#  AI for Comm · 交付包清理
#  清掉 最终提交材料\ 里的多余文件：不入包的过程性目录、过期研究报告、
#  __pycache__、无源孤本
#
#  用法： powershell -ExecutionPolicy Bypass -File clean_submission.ps1        # 只预览
#         powershell -ExecutionPolicy Bypass -File clean_submission.ps1 -Yes   # 真删
#
#  默认 dry-run：不带 -Yes 时只打印将要删除什么，不动任何文件。
# ============================================================
param([switch]$Yes)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dst  = Join-Path $Root '最终提交材料'
$Demo = Join-Path $Dst '演示成果'

# 与 build_submission.ps1 的白名单保持一致：不在名单内的研究报告视为过期
$Reports = @(
    'research_20260901_234713.html',
    'research_20260902_003653.html',
    'research_20260902_215747.html',
    'research_20260902_225648.html'
)
$ReportCount = $Reports.Count

if (-not (Test-Path $Dst)) { throw "交付包目录不存在：$Dst" }

$targets = @()

# ── 0. 不入包的目录：中间材料（过程性凭据保留在仓库根目录）────
foreach ($d in '中间材料') {
    $p = Join-Path $Dst $d
    if (Test-Path $p) { $targets += $p }
}

# ── 1. 演示成果里不在白名单内的研究报告 ────────────────────
Get-ChildItem (Join-Path $Demo 'research_*.html') -File -ErrorAction SilentlyContinue |
    Where-Object { $Reports -notcontains $_.Name } |
    ForEach-Object { $targets += $_.FullName }

# ── 2. Python 缓存 ─────────────────────────────────────────
Get-ChildItem $Dst -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    ForEach-Object { $targets += $_.FullName }
Get-ChildItem $Dst -Recurse -File -Include '*.pyc' -ErrorAction SilentlyContinue |
    ForEach-Object { $targets += $_.FullName }

# ── 3. 演示成果里不在白名单内的其它文件（改名孤本、内容重复件）────
$DemoKeep = $Reports + @('ber_comparison.png', 'bpsk_ber_awgn.png', 'bpsk_awgn_ber.png')
Get-ChildItem $Demo -File -ErrorAction SilentlyContinue |
    Where-Object { $DemoKeep -notcontains $_.Name } |
    ForEach-Object { $targets += $_.FullName }

# ── 4. 构建脚本自己留下的临时件 ────────────────────────────
foreach ($f in '_rc.html', '_rb.html', '_rc.pdf', '_rb.pdf') {
    $p = Join-Path $Dst $f
    if (Test-Path $p) { $targets += $p }
}

if (-not $targets) {
    Write-Host "交付包很干净，无需清理。" -ForegroundColor Green
    return
}

Write-Host ("将清理 {0} 项：" -f $targets.Count) -ForegroundColor Yellow
$targets | ForEach-Object { Write-Host "    $_" }

if (-not $Yes) {
    Write-Host "`n这是预览。确认无误后加 -Yes 真删： " -NoNewline
    Write-Host "powershell -File clean_submission.ps1 -Yes" -ForegroundColor Cyan
    return
}

foreach ($t in $targets) {
    Remove-Item $t -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    已删除 $t"
}
Write-Host "`n清理完成。" -ForegroundColor Green
