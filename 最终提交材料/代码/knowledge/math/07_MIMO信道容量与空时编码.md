# MIMO 信道容量与空时编码

## 别名
Multiple-Input Multiple-Output、多天线系统、Spatial Multiplexing、空间复用、Diversity、分集、Alamouti、Beamforming、波束赋形

---

## 一、MIMO 系统模型

### 1.1 基本模型

```
                  H (信道矩阵)
发送天线阵列 ══════════════╗══════════════ 接收天线阵列
  x₁ ──→                 ║                  → y₁
  x₂ ──→       Nt × Nr   ║    Nr × Nt       → y₂
  ...                    ║                  → ...
  x_Nt ──→              ║                  → y_Nr
```

### 1.2 数学模型

```
y = Hx + n

其中：
  y: 接收向量 (Nr × 1)
  H: 信道矩阵 (Nr × Nt)
  x: 发送向量 (Nt × 1)
  n: 噪声向量 ~ CN(0, N₀·I)
```

**总功率约束**：E[||x||²] ≤ P（总功率在所有天线上分配，而非单天线）

### 1.3 信道矩阵的意义

```
H 的第 (i, j) 个元素 hᵢⱼ：
  第 j 根发射天线 → 第 i 根接收天线的信道系数
```

| 信道类型 | H 的特点 |
|---------|---------|
| **理想 i.i.d. Rayleigh** | 各元素独立同分布 ~ CN(0,1) |
| **相关信道** | H = Rr^(1/2)·H_iid·Rt^(1/2) |
| **LoS 主导** | H 含有秩-1 确定性分量 |
| **毫米波** | H 可以用少量路径稀疏表示 |

---

## 二、MIMO 信道容量

### 2.1 决定性容量（发端已知 CSI）

当发射机**完全知道 H** 时，可做最优功率分配。通过 SVD 分解：

```
H = U·Σ·V^H

Σ = diag(σ₁, σ₂, ..., σ_min)  — 信道奇异值
min = min(Nt, Nr)              — 空间自由度（并行子信道数量）
```

MIMO 信道等价于 **min(Nt, Nr) 个并行独立子信道**：

```
C = max Σ log₂(1 + Pᵢ·σᵢ²/N₀)
    ΣPᵢ ≤ P
```

### 2.2 水填充算法 (Water-Filling)

最优功率分配：

```
Pᵢ = max(0, μ - N₀/σᵢ²)

μ: 水位 (water-level) — 由总功率约束确定
```

```
可视化：

  N₀/σᵢ² (噪声水平)
  ┌──┐
  │  │  ← 水面 μ
  │~~│────┬────── 倒水
  │~~│ 水 │
──┴──┴──┴─┴──────
σ₁² σ₂² σ₃² σ₄² (信道增益)
```

**直觉**：增益高的子信道分到更多功率，增益太低的子信道可能被"关掉"。

### 2.3 遍历容量与中断容量

| 概念 | 定义 | 适用场景 |
|------|------|---------|
| **遍历容量** | E_H[C(H)] — 对所有信道实现的平均 | 快衰落，编码跨越足够多的相干时间 |
| **中断容量** | Pr[C(H) < R] ≤ ε 时的最大 R | 慢衰落，每次传输经历一个固定 H |
| **遍历容量下界** | C ≥ log₂(1 + SNR·||H||²/Nt)（CSI 未知，等功率分配） | 发端无 CSI 时的可达速率 |

### 2.4 高 SNR 下的容量增长

```
当 Nt = Nr = M, 高 SNR:

C ≈ M · log₂(SNR) + M · log₂(e/π) + o(1)

→ 容量随 min(Nt, Nr) 线性增长！
→ 多天线系统的根本优势
```

### 2.5 例题

**题目**：4×4 MIMO 系统，SNR = 20dB，假设信道矩阵各元素 i.i.d. Rayleigh，发射机知道 CSI，求近似容量。

**解**：
```
SNR = 20dB → SNR_linear = 100

奇异值分布 (i.i.d. Rayleigh 4×4):
  E[σᵢ²] 近似满足 Marchenko-Pastur 律

近似容量：
  C ≈ min(Nt,Nr) · log₂(1 + SNR) 
    ≈ 4 · log₂(101) 
    ≈ 4 · 6.66 
    ≈ 26.6 bps/Hz

对比 SISO (1×1)：
  C_SISO = log₂(101) ≈ 6.66 bps/Hz

MIMO 增益 ≈ 4×
```

---

## 三、空间复用 vs 分集

MIMO 提供的两种根本性增益：

| 增益类型 | 目标 | 如何实现 | 度量 |
|---------|------|---------|------|
| **空间复用** | 提高数据率 | 不同天线发送独立数据流 | 复用增益 r = lim(SNR→∞) R/log₂(SNR) |
| **分集** | 提高可靠性 | 不同天线发送相同数据（经编码） | 分集阶数 d = lim(SNR→∞) -log Pe / log SNR |

### 分集-复用折衷 (Zheng & Tse, 2003)

```
d*(r) = (Nt - r)(Nr - r)   — 最优折衷曲线

→ 不可能同时获得最大复用增益和最大分集增益
→ 必须在"快"和"可靠"之间做选择
```

---

## 四、空时编码

### 4.1 为什么要空时编码

直接在不同天线上发独立数据流 → 空间干扰严重 → 需要编码。

### 4.2 Alamouti 方案 (2×1)

最经典的**发射分集**方案（1998）：

```
时隙 1: 天线1发 x₁, 天线2发 x₂
时隙 2: 天线1发 -x₂*, 天线2发 x₁*

编码矩阵：
    [ x₁   x₂ ]
X = [          ]
    [-x₂*  x₁* ]
```

**特点**：
- 获得满分集阶数 2（2 发射天线 × 1 接收天线 → d = 2）
- 无需发端知道 CSI
- 速率 = 1 符号/时隙（全速率）
- 解码复杂度极低（线性合并）

### 4.3 空时分组码 (STBC)

Alamouti 方案的推广：Nt > 2 天线时，不存在全速率、满分集的**正交** STBC（复信号）。

| 方案 | 天线数 | 速率 | 分集 | 正交 |
|------|-------|------|------|------|
| Alamouti | 2 | 1 | 满 | 是 |
| 3/4 速率 OSTBC | 3 | 3/4 | 满 | 是 |
| 1/2 速率 OSTBC | 4 | 1/2 | 满 | 是 |
| Golden Code | 2 | 2 | 满 | 不会损失速率 |

### 4.4 空分复用（V-BLAST）

不追求分集，追求**最高速率**——每根天线发送独立数据流。接收端用连续干扰消除（SIC）解码。

```
流程：
  1. 用追零 (ZF) 或 MMSE 检测最强信号
  2. 从接收信号中减去已解码的符号
  3. 重复，直至所有流解码完毕

可达速率 ≈ min(Nt, Nr) × log₂(1+SNR)  (高SNR)
```

---

## 五、预编码与波束赋形

### 5.1 线性预编码

发射前用矩阵 W 预处理：

```
x = W·s    (s 为原始数据符号)

接收信号：
y = H·W·s + n
```

| 预编码方案 | 公式 | 特点 |
|-----------|------|------|
| **追零 (ZF)** | W = H^H (HH^H)^(-1) | 完全消除流间干扰 |
| **MMSE** | W = H^H (HH^H + N₀/P·I)^(-1) | 平衡干扰和噪声 |
| **SVD** | W = V（来自 H 的 SVD） | 容量最优（需 CSI） |
| **码本预编码** | W 从 3GPP 预定义码本中选 | 5G NR 实际方案 |

### 5.2 码本预编码（5G NR 实践）

5G NR 定义了 Type I（常规精度）和 Type II（高精度）两种码本。UE 测量下行 CSI-RS 后上报 PMI（预编码矩阵指示符）给基站。

---

## 六、大规模 MIMO

### 6.1 核心概念

```
大规模 MIMO = Nt >> Nr (基站有数十到数百根天线)

当 Nt → ∞ 时，发生两个"魔法"：
```

| 魔法 | 原因 | 后果 |
|------|------|------|
| **信道硬化** | 大数定律 → 随机信道趋近确定性 | 遍历容量可用确定性公式算 |
| **有利传播** | 不同用户的信道向量渐近正交 | 最大比合并 (MRC) 就接近最优 |

### 6.2 渐进容量

```
Nt → ∞, Nr 固定，功率 P/Nt (单天线功率固定)：

C → Nr · log₂(1 + P/N₀)

→ 每个用户 (Nr 个用户) 获得 SISO 容量，无干扰！
```

---

## 七、MIMO 与信息论的核心公式速查

| 公式 | 含义 |
|------|------|
| C = log₂ det(I + SNR·HH^H / Nt) | 等功率分配的 MIMO 容量（发端不知 CSI） |
| C = Σ log₂(1 + Pᵢ·σᵢ²/N₀) | 水填充容量（发端知 CSI） |
| C ≈ min(Nt,Nr)·log₂(SNR) | 高 SNR 下容量随自由度线性增长 |
| d*(r) = (Nt-r)(Nr-r) | 分集-复用最优折衷 |
| ||hᵘ·hᵛ|| → 0 (Nt → ∞) | 有利传播条件 |

---

## 来源

- Telatar, E. "Capacity of Multi-antenna Gaussian Channels", European Trans. Telecom., 1999
- Foschini, G.J. "Layered Space-Time Architecture for Wireless Communication", Bell Labs Tech. J., 1996
- Alamouti, S.M. "A Simple Transmit Diversity Technique for Wireless Communications", IEEE JSAC, 1998
- Zheng, L. & Tse, D.N.C. "Diversity and Multiplexing: A Fundamental Tradeoff", IEEE Trans. Info. Theory, 2003
- Marzetta, T.L. "Noncooperative Cellular Wireless with Unlimited Numbers of Base Station Antennas", IEEE Trans. Wireless Comm., 2010
- 3GPP TS 38.214 (5G NR 物理层过程)
