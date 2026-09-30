# -*- coding: utf-8 -*-
"""
通信算法库工具 —— 链路级仿真常用公式与算法的"标准答案库"

覆盖：香农容量、常见调制的理论误码率（AWGN/瑞利）、蒙特卡洛快速仿真。
定位：仿真 Agent 的曲线对不对、校验 Agent 想复核结论，直接调本工具拿
数值基准，不依赖大模型"心算"，杜绝公式记错。

实现说明：
- BPSK/QPSK：教科书精确式
- MQAM(16/64)：格雷映射方形星座，逐轴按 1D PAM 判决域做精确高斯积分
  （归一化到每比特能量 Eb=1），低信噪比不下瘫到 0.5
- 8PSK：Gray 映射并界 Ps/3
- 瑞利信道：BPSK/QPSK 精确闭合式；MQAM 不做（防误导）
- 蒙特卡洛：真实调制解调全链路仿真，随机种子固定可复现，与理论值同表输出
"""
import math

import numpy as np
from scipy.special import erf, erfc

from tools.registry import tool

_SCHEMES = ("bpsk", "qpsk", "8psk", "16qam", "64qam")


def _qfunc(x):
    return 0.5 * erfc(np.asarray(x, dtype=float) / np.sqrt(2))


def _gray2bin_std(g):
    """格雷码转自然二进制。"""
    b, mask = 0, g
    while mask:
        b ^= mask
        mask >>= 1
    return b


def _axis_levels(bits_per_axis: int):
    """返回 (格雷索引->电平 列表)。索引 i 的电平由格雷码决定，
    相邻索引电平相邻（保证单门限错一比特）。"""
    k = 1 << bits_per_axis
    mags = [2 * j - k + 1 for j in range(k)]           # -k+1,-k+3,...,k-1
    table = [0] * k
    for idx in range(k):                                # idx 为格雷码，值→幅度序号
        binv = _gray2bin_std(idx)
        table[idx] = mags[binv]
    return table                                        # 下标 = 格雷比特值


def _qam_awgn_ber(M, ebno_lin):
    """方形 QAM 格雷映射精确比特错率：逐轴按 1D PAM 判决域做高斯积分。

    星座归一化到每比特能量 Eb=1；I/Q 两轴独立同分布，故总 Pb = 单轴 Pb。
    相比并界近似，低信噪比段不会失真地饱和到 0.5。
    """
    ebno = np.asarray(ebno_lin, dtype=float)
    b = int(round(math.log2(M)))                  # 每符号比特数
    ba = b // 2                                   # 每轴比特数
    k = 1 << ba                                   # 每轴电平数
    d = math.sqrt(3.0 * b / (2.0 * (k * k - 1)))  # 使 Eb=1 的电平间隔
    lev = (2 * np.arange(1, k + 1) - 1) * d       # 升序幅度
    gray = np.array([i ^ (i >> 1) for i in range(k)], dtype=int)
    mid = (lev[:-1] + lev[1:]) / 2                # 相邻电平判决门限
    lo = np.concatenate(([-np.inf], mid))
    hi = np.concatenate((mid, [np.inf]))
    ham = np.zeros((k, k))                        # 格雷标签比特差数
    for i in range(k):
        for j in range(k):
            ham[i, j] = bin(int(gray[i]) ^ int(gray[j])).count("1")

    flat = np.atleast_1d(ebno).ravel()
    res = np.zeros(flat.size)
    for oi, eb in enumerate(flat):
        sig = math.sqrt(1.0 / (2.0 * eb))         # 每轴噪声标准差（N0=1/eb）
        p = 0.0
        for i in range(k):
            # P(判决为 j | 发送 i)：噪声落在判决域 j 内的精确概率
            pj = 0.5 * (erf((hi - lev[i]) / (sig * math.sqrt(2)))
                        - erf((lo - lev[i]) / (sig * math.sqrt(2))))
            p += float(np.dot(pj, ham[i]))
        res[oi] = p / (k * ba)
    return res.reshape(ebno.shape) if ebno.ndim else float(res[0])


def _theo_ber_awgn(scheme, ebno_lin):
    g = np.asarray(ebno_lin, dtype=float)
    if scheme == "bpsk":
        return _qfunc(np.sqrt(2 * g))
    if scheme == "qpsk":
        return _qfunc(np.sqrt(2 * g))                   # 每比特 Eb 下与 BPSK 同
    if scheme == "8psk":
        # Ps = 2·Q(sqrt(2γs)·sin(π/8))，γs = 3γb；Gray 映射下 Pb ≈ Ps/3
        return (2 / 3) * _qfunc(np.sqrt(6 * g) * np.sin(np.pi / 8))
    if scheme == "16qam":
        return _qam_awgn_ber(16, g)
    if scheme == "64qam":
        return _qam_awgn_ber(64, g)
    return None


def _theo_ber_rayleigh(scheme, ebno_lin):
    g = np.asarray(ebno_lin, dtype=float)
    if scheme in ("bpsk", "qpsk"):
        return 0.5 * (1 - np.sqrt(g / (1 + g)))
    return None


@tool(
    "comm_lib",
    "通信链路级标准算法库：理论误码率曲线、香农容量、蒙特卡洛快速仿真，可作仿真结果的正确性基准",
    {"action": "操作，取 theo_ber|shannon|monte_carlo_ber",
     "scheme": "调制方式 bpsk|qpsk|8psk|16qam|64qam",
     "channel": "信道 awgn|rayleigh，默认 awgn（rayleigh 仅支持 bpsk/qpsk）",
     "ebn0_db": "Eb/N0 点，逗号分隔 dB 值，如 '0,2,4,6,8,10'；缺省取 0~10 步长 2",
     "bandwidth": "带宽 Hz（仅 shannon 用，默认 1e6）",
     "snr_db": "信噪比 dB（仅 shannon 用，默认 10）",
     "nbits": "蒙特卡洛每点比特数，默认 200000"},
)
def comm_lib(action: str, scheme: str = "bpsk", channel: str = "awgn",
             ebn0_db: str = "", bandwidth: float = 1e6, snr_db: float = 10,
             nbits: int = 200000):
    action = str(action).strip().lower()
    scheme = str(scheme).strip().lower()

    if action == "shannon":
        snr = 10 ** (float(snr_db) / 10)
        c = float(bandwidth) * np.log2(1 + snr)
        return {"信道容量_bps": round(c, 2), "公式": "C = B·log2(1+SNR)",
                "说明": f"带宽 {bandwidth} Hz、信噪比 {snr_db} dB（线性 SNR={snr:.1f}）下"}

    if scheme not in _SCHEMES:
        raise ValueError(f"调制方式「{scheme}」不支持，可选：{', '.join(_SCHEMES)}")
    db = np.array([float(v) for v in str(ebn0_db).split(",") if v.strip()]) \
        if ebn0_db else np.arange(0, 11, 2, dtype=float)
    lin = 10 ** (db / 10)

    if action == "theo_ber":
        ber = (_theo_ber_awgn if channel == "awgn" else _theo_ber_rayleigh)(scheme, lin)
        if ber is None:
            raise ValueError(f"{channel} 信道的 {scheme} 无内置精确式，"
                             f"rayleigh 仅支持 bpsk/qpsk；awgn 支持全部")
        note = "（BPSK/QPSK 精确式）" if scheme in ("bpsk", "qpsk") \
            else "（1D PAM 判决域精确积分）" if "qam" in scheme \
            else "（Gray 映射并界近似）"
        return {"调制": scheme, "信道": channel,
                "EbN0_dB": [round(float(v), 1) for v in db],
                "理论误码率": [float(f"{v:.3e}") for v in ber],
                "说明": note + "数值可与仿真曲线逐点对照"}

    if action == "monte_carlo_ber":
        if scheme == "8psk":
            raise ValueError("蒙特卡洛暂不支持 8PSK，请改用 theo_ber 或选 qam/psk 二进制调制")
        nbits = max(20000, min(int(nbits), 4_000_000))
        rng = np.random.default_rng(42)
        out = []
        for d, eb in zip(db, lin):
            if scheme in ("bpsk", "qpsk"):
                bits = rng.integers(0, 2, size=nbits)
                s = 2 * bits - 1
                sig = np.sqrt(1 / (2 * eb))
                if channel == "awgn":
                    n = 1.0
                else:
                    n = rng.rayleigh(1.0, nbits)        # 衰落幅度
                r = s * n + rng.normal(0, sig, nbits)
                ber = float(np.mean((r < 0) != (bits == 0)))
            else:
                M = 16 if scheme == "16qam" else 64
                b = int(np.log2(M))
                ba = b // 2
                tbl = np.array(_axis_levels(ba), dtype=float)
                # 归一化到 Es = b（即每比特能量 Eb=1），与 _qam_awgn_ber 同口径
                lv_scale = np.sqrt(np.mean(tbl ** 2) * 2 / b)
                tbl_n = tbl / lv_scale
                nb = nbits // b
                bits = rng.integers(0, 2, size=(nb, b))
                gi = bits[:, :ba] @ (1 << np.arange(ba - 1, -1, -1))
                gq = bits[:, ba:] @ (1 << np.arange(ba - 1, -1, -1))
                sym = (tbl[gi] + 1j * tbl[gq]) / lv_scale
                noise = (rng.normal(0, 1 / np.sqrt(2 * eb), nb)
                         + 1j * rng.normal(0, 1 / np.sqrt(2 * eb), nb))
                if channel == "rayleigh":
                    h = rng.rayleigh(1 / np.sqrt(2), nb) + 1j * rng.rayleigh(1 / np.sqrt(2), nb)
                    sym = sym * h
                r = sym + noise
                # 最近邻判决：逐轴找最近电平
                def _axis_dec(vals):
                    dmat = np.abs(vals[:, None] - tbl_n[None, :])
                    idx = np.argmin(dmat, axis=1)
                    return idx
                di, dq = _axis_dec(r.real), _axis_dec(r.imag)
                rec = np.zeros((nb, b), dtype=int)
                for k in range(ba):
                    rec[:, k] = (di >> (ba - 1 - k)) & 1
                    rec[:, ba + k] = (dq >> (ba - 1 - k)) & 1
                ber = float(np.mean(rec != bits))
            out.append({"EbN0_dB": round(float(d), 1), "误码率": float(f"{ber:.3e}")})
        theo = (_theo_ber_awgn if channel == "awgn" else _theo_ber_rayleigh)(scheme, lin)
        if theo is not None:
            for i, t in enumerate(out):
                t["理论值"] = float(f"{theo[i]:.3e}")
        return {"调制": scheme, "信道": channel, "每点比特数": nbits, "结果": out}

    raise ValueError(f"不支持的操作「{action}」，可选：theo_ber / shannon / monte_carlo_ber")
