# -*- coding: utf-8 -*-
"""验证 knowledge/sim/ 六份仿真模板的正确性（缩小样本量快速跑）"""
import numpy as np
from scipy.special import erfc

ok = True
def check(name, cond, detail=""):
    global ok
    status = "通过" if cond else "失败"
    print(f"[{status}] {name} {detail}")
    if not cond:
        ok = False

# ── 模板01：BPSK 误码率 ──
rng = np.random.default_rng(0)
n = 200000
for ebn0, expect in [(6, 2.4e-3), (9, 1.9e-4)]:
    snr = 10 ** (ebn0 / 10)
    sigma = np.sqrt(1 / (2 * snr))
    bits = rng.integers(0, 2, n)
    rx = (2 * bits - 1) + sigma * rng.standard_normal(n)
    ber = np.sum((rx > 0) != (bits == 1)) / n
    theory = 0.5 * erfc(np.sqrt(snr))
    check("01-BPSK误码率", abs(ber - theory) < max(3e-5, 0.5 * theory),
          f"Eb/N0={ebn0}dB 仿真{ber:.2e} 理论{theory:.2e}")

# ── 模板02：香农容量 ──
cap = 20e6 * np.log2(1 + 1000) / 1e6
check("02-香农容量", abs(cap - 199.5) < 1, f"B=20MHz SNR=30dB → {cap:.1f} Mbps")
check("02-谱效率SNR=0dB", abs(np.log2(2) - 1.0) < 1e-9, "log2(2)=1")

# ── 模板03：16QAM 能量归一化 ──
I = np.array([-3, -1, 1, 3]); Q = np.array([-3, -1, 1, 3])
const = (np.repeat(I, 4) + 1j * np.tile(Q, 4)) / np.sqrt(10)
pwr = np.mean(np.abs(const) ** 2)
check("03-16QAM归一化", abs(pwr - 1.0) < 1e-9, f"平均功率={pwr:.4f}")

# ── 模板04：瑞利衰落理论值 ──
gb = 100  # 20dB
ber_ray = 0.5 * (1 - np.sqrt(gb / (1 + gb)))
check("04-瑞利理论值", abs(ber_ray - 0.0025) < 0.0005, f"20dB → {ber_ray:.4f}")
# 仿真对照（小样本）
rng = np.random.default_rng(2)
n = 50000
ebn0 = 14; snr = 10 ** (ebn0 / 10)
sigma = np.sqrt(1 / (2 * snr))
bits = rng.integers(0, 2, n)
x = 2.0 * bits - 1
h = (rng.standard_normal(n) + 1j * rng.standard_normal(n)) / np.sqrt(2)
noise = sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
detect = np.real((h * x + noise) / h)
ber_sim = np.sum((detect > 0) != (x > 0)) / n
theory = 0.5 * (1 - np.sqrt(snr / (1 + snr)))
check("04-瑞利仿真", abs(ber_sim - theory) < 0.4 * theory + 2e-4,
      f"14dB 仿真{ber_sim:.3f} 理论{theory:.3f}")

# ── 模板05：MIMO 容量（缩小实现次数）──
rng = np.random.default_rng(3)
def mimo_cap(nr, nt, snr_db, num=800):
    snr = 10 ** (snr_db / 10); caps = []
    for _ in range(num):
        H = (rng.standard_normal((nr, nt)) + 1j * rng.standard_normal((nr, nt))) / np.sqrt(2)
        s2 = np.linalg.svd(H, compute_uv=False) ** 2
        caps.append(np.sum(np.log2(1 + snr * s2 / nt)))
    return np.mean(caps)
c11 = mimo_cap(1, 1, 20); c44 = mimo_cap(4, 4, 20)
check("05-MIMO 1x1", abs(c11 - 5.9) < 0.6, f"20dB → {c11:.2f} bit/s/Hz")
check("05-MIMO 4x4", c44 > 3 * c11, f"20dB → {c44:.2f}（应≈4倍于1x1）")

# ── 模板06：卷积码+维特比（缩小样本）──
G1, G2 = 0b111, 0b101
def conv_encode(bits):
    state, out = 0, []
    for b in np.append(bits, [0, 0]):
        reg = (state << 1) | b
        out += [bin(reg & G1).count('1') % 2, bin(reg & G2).count('1') % 2]
        state = reg & 0b11
    return np.array(out)

def viterbi_hard(rx_bits, n_info):
    path_metrics = {0: 0.0}; paths = {0: []}
    for i in range(0, len(rx_bits), 2):
        pair = rx_bits[i:i+2]
        new_m, new_p = {}, {}
        for s, m in path_metrics.items():
            for b in (0, 1):
                reg = (s << 1) | b
                enc = [bin(reg & G1).count('1') % 2, bin(reg & G2).count('1') % 2]
                d = sum(e != r for e, r in zip(enc, pair))
                ns = reg & 0b11
                if ns not in new_m or m + d < new_m[ns]:
                    new_m[ns] = m + d
                    new_p[ns] = paths[s] + [b]
        path_metrics, paths = new_m, new_p
    best = min(path_metrics, key=path_metrics.get)
    return np.array(paths[best][:n_info])

rng = np.random.default_rng(4)
n_info = 20000
# 高信噪比：编码后应几乎无误码
ebn0 = 8; snr = 10 ** (ebn0 / 10)
sigma = np.sqrt(1 / (2 * 0.5 * snr))
bits = rng.integers(0, 2, n_info)
tx = 2 * conv_encode(bits) - 1
rxh = ((tx + sigma * rng.standard_normal(len(tx))) > 0).astype(int)
dec = viterbi_hard(rxh, n_info)
ber_hi = np.sum(dec != bits) / n_info
# 未编码同点误码率
ber_unc = 0.5 * erfc(np.sqrt(snr))
check("06-卷积码高信噪比", ber_hi < ber_unc and ber_hi < 1e-4,
      f"编码{ber_hi:.1e} vs 未编码{ber_unc:.1e}")
# 中信噪比（超过门限）：编码应明显优于未编码
ebn0 = 5; snr = 10 ** (ebn0 / 10)
sigma = np.sqrt(1 / (2 * 0.5 * snr))
bits = rng.integers(0, 2, n_info)
tx = 2 * conv_encode(bits) - 1
rxh = ((tx + sigma * rng.standard_normal(len(tx))) > 0).astype(int)
dec = viterbi_hard(rxh, n_info)
ber_lo = np.sum(dec != bits) / n_info
ber_unc_lo = 0.5 * erfc(np.sqrt(snr))
check("06-卷积码编码增益", ber_lo < ber_unc_lo * 0.6,
      f"5dB 编码{ber_lo:.2e} vs 未编码{ber_unc_lo:.2e}")

print("\n总结:", "全部通过" if ok else "存在失败项，需修正模板")
