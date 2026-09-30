# 01 AWGN 信道误码率仿真（蒙特卡洛法）

## 用途
仿真 BPSK / QPSK 在加性高斯白噪声（AWGN）信道下的误码率（BER）曲线，并与理论曲线对比验证。这是通信系统仿真最基础的实验，用于验证仿真框架的正确性。

## 核心原理
- BPSK 理论误码率：BER = Q(sqrt(2·Eb/N0))，其中 Q 函数可用 erfc 表示：Q(x) = 0.5·erfc(x/√2)
- QPSK 每比特误码率与 BPSK 相同（正交分解后每路等效 BPSK）
- Eb/N0（dB）换算为噪声方差：σ² = 1 / (2·R·10^(Eb/N0/10))，码率 R=1 时 σ² = 1/(2·10^(Eb/N0/10))

## 标准代码模板

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc

def qpsk_ber_sim(ebn0_db, num_bits=1000000, seed=0):
    rng = np.random.default_rng(seed)
    ber = []
    for ebn0 in ebn0_db:
        snr_lin = 10 ** (ebn0 / 10)
        sigma = np.sqrt(1 / (2 * snr_lin))          # 每维噪声标准差
        bits = rng.integers(0, 2, num_bits)          # 随机比特
        symbols = 2 * bits - 1                       # BPSK/QPSK单维映射 ±1
        rx = symbols + sigma * rng.standard_normal(num_bits)
        err = np.sum((rx > 0) != (symbols > 0))
        ber.append(err / num_bits)
    return np.array(ber)

ebn0_db = np.arange(0, 11)
ber_sim = qpsk_ber_sim(ebn0_db)
ber_theory = 0.5 * erfc(np.sqrt(10 ** (ebn0_db / 10)))

plt.semilogy(ebn0_db, ber_theory, 'b-',  label='理论曲线')
plt.semilogy(ebn0_db, ber_sim,   'ro', label='仿真结果')
plt.xlabel('Eb/N0 (dB)'); plt.ylabel('误码率 BER')
plt.title('BPSK/QPSK 在 AWGN 信道下的误码率')
plt.legend(); plt.grid(True, which='both')
plt.savefig('ber_awgn.png', dpi=150)
```

## 预期结果与校验点
1. 仿真点应与理论曲线基本重合；Eb/N0=10dB 处理论 BER≈3.87e-6
2. 每个点至少出现 100 个错误才有统计意义：低误码率点需增大比特数，或误码数为 0 时用"3/比特数"作上限估计
3. 若仿真曲线整体偏移理论曲线约 3dB，通常是 Eb/N0 与 Es/N0 混淆（能量归一化错误）

## 常见错误
- 噪声方差忘记除以 2（复信号两维各分一半功率）
- 把信噪比 SNR 当成 Eb/N0 直接用（多进制调制两者差 log2(M)）
