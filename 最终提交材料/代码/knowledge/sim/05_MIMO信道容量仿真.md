# 05 MIMO 信道容量仿真（SVD 分解与注水分配）

## 用途
仿真多天线（MIMO）系统容量，对比不同收发天线配置的容量增益，验证"容量随 min(Mt,Mr) 近似线性增长"的经典结论，支撑 math_agent 的 MIMO 推导。

## 核心原理
- MIMO 信道矩阵 H（Mr×Mt），元素为独立复高斯分布
- SVD 分解 H = UΣVᴴ，信道拆成 r=rank(H) 个并行子信道，奇异值平方 λi 为各子信道增益
- 等功率分配容量：C = Σ log2(1 + ρ·λi/r)，ρ 为总信噪比（每发射天线归一化）
- 注水算法：功率按 (μ − 1/(ρ·λi))⁺ 分配，容量略高于等功率，低信噪比增益明显

## 标准代码模板

```python
import numpy as np
import matplotlib.pyplot as plt

def mimo_capacity(nr, nt, snr_db, num_real=5000, seed=3):
    rng = np.random.default_rng(seed)
    snr = 10 ** (snr_db / 10)
    caps = []
    for _ in range(num_real):
        H = (rng.standard_normal((nr, nt))
             + 1j * rng.standard_normal((nr, nt))) / np.sqrt(2)
        s2 = np.linalg.svd(H, compute_uv=False) ** 2   # 奇异值平方
        caps.append(np.sum(np.log2(1 + snr * s2 / nt)))
    return np.mean(caps)

snr_db = np.arange(-10, 31, 2)
configs = [(1, 1), (2, 2), (4, 4), (8, 8)]
plt.figure(figsize=(8, 5))
for nr, nt in configs:
    c = [mimo_capacity(nr, nt, s) for s in snr_db]
    plt.plot(snr_db, c, marker='o', label=f'{nr}×{nt} MIMO')
plt.xlabel('SNR (dB)'); plt.ylabel('遍历容量 (bit/s/Hz)')
plt.title('MIMO 信道容量 vs 天线配置')
plt.legend(); plt.grid(True)
plt.savefig('mimo_capacity.png', dpi=150)
```

## 预期结果与校验点
1. SNR=20dB 时各配置遍历容量约：1×1 ≈ 5.9、2×2 ≈ 11.7、4×4 ≈ 22、8×8 ≈ 46 bit/s/Hz（近似线性倍增；注意衰落遍历容量比无衰落 log2(1+ρ) 低约 0.83 bit/s/Hz）
2. 曲线间隔在高信噪比区约等于 log2(min(Mt,Mr))·增量
3. 蒙特卡洛实现次数 5000 次足以使曲线平滑；波动大可增至 20000 次

## 常见错误
- 信道矩阵元素方差忘记归一化到 1/2（实虚各半），导致容量整体偏高约 3dB
- 信噪比分配：ρ 是总功率信噪比，等功率时每天线 ρ/nt，勿重复除
