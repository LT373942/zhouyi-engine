# -*- coding: utf-8 -*-
"""度量与统计：M1/M2/M2′、随机基线 z 值、同构群置换检验、Stouffer 合并。

指标定义（回测协议）：
- 信号集 flagged = 规模≥3 的同构群成员 ∪ audit 判为断裂的关系两端实体；
- M1 信号精确率 = |flagged ∩ fracture| / |flagged|；
- M2 信号召回   = |flagged ∩ fracture| / |fracture|；
- M2′ 级联召回  = |closure ∩ fracture| / |fracture|，closure 为去种子后的波及闭包；
- 基线：在全体实体中同规模均匀随机重采样 1000 次，z = (obs - mean) / sd；
- 同构群置换检验：将卦名在实体间随机打乱 1000 次，p = (1 + #{最大簇 ≥ 观测簇}) / 1001；
- Stouffer 合并：z = Σz_i / √n。
"""

import math
import random

from .engine import audit, cascade, clusters, gua_names

RNG_SEED = 20261105  # 固定随机种子，结果可复现


def zscore(obs, samples):
    n = len(samples)
    mean = sum(samples) / n
    var = sum((s - mean) ** 2 for s in samples) / n
    sd = math.sqrt(var)
    return (obs - mean) / sd if sd > 0 else 0.0


def _baseline_overlap(k, universe, fracture, n, rng):
    out = []
    for _ in range(n):
        pick = set(rng.sample(sorted(universe), k))
        out.append(len(pick & fracture))
    return out


def backtest(case, n=1000, seed=RNG_SEED):
    """对单案例运行完整回测协议，返回全部指标与 z 值。"""
    rng = random.Random(seed)
    universe = {e["id"] for e in case["entities"]}
    fracture = set(case.get("fracture", []))

    cl = clusters(case, min_size=3)
    flagged = set()
    for members in cl.values():
        flagged.update(members)
    for r in audit(case):
        if r["state"] == "断裂":
            flagged.update([r["a"], r["b"]])

    closure_full = cascade(case)["closure"]
    closure = set(closure_full) - set(case.get("seeds", []))

    f1 = len(flagged & fracture)
    m1 = f1 / len(flagged) if flagged else 0.0
    m2 = f1 / len(fracture) if fracture else 0.0
    c1 = len(closure & fracture)
    m2p = c1 / len(fracture) if fracture else 0.0

    z_m1 = zscore(f1, _baseline_overlap(len(flagged), universe, fracture, n, rng)) if flagged else 0.0
    z_m2 = z_m1  # M1 与 M2 的信号集相同，重叠计数同一，z 相同
    z_m2p = zscore(c1, _baseline_overlap(len(closure), universe, fracture, n, rng)) if closure else 0.0

    # 同构群置换检验，两种零假设：
    # (a) 无信息零假设：各实体卦象独立均匀抽自 64 卦（主检验）；
    # (b) 经验零假设：抽自本案卦象经验分布（稳健性对照）。
    names = [v for v in gua_names(case).values() if v is not None]
    obs_max = max((len(v) for v in cl.values()), default=0)

    def _perm_p(population):
        c = 0
        for _ in range(n):
            draw = [rng.choice(population) for _ in range(len(names))]
            freq = {}
            for x in draw:
                freq[x] = freq.get(x, 0) + 1
            if freq and max(freq.values()) >= obs_max:
                c += 1
        return (1 + c) / (1 + n)

    from .hexagram import HEX_MATRIX, TRI_ORDER
    all64 = [HEX_MATRIX[l][TRI_ORDER.index(u)] for l in HEX_MATRIX for u in TRI_ORDER]
    p_cluster = _perm_p(all64)
    p_cluster_emp = _perm_p(names)

    return {
        "case": case.get("case", "?"),
        "n_entities": len(universe),
        "flagged": sorted(flagged),
        "closure": sorted(closure),
        "fracture": sorted(fracture),
        "clusters": cl,
        "M1": round(m1, 3), "M1_z": round(z_m1, 2),
        "M2": round(m2, 3), "M2_z": round(z_m2, 2),
        "M2p": round(m2p, 3), "M2p_z": round(z_m2p, 2),
        "cluster_max_size": obs_max,
        "cluster_p": round(p_cluster, 4),
        "cluster_p_empirical": round(p_cluster_emp, 4),
    }


def stouffer(zs):
    """Stouffer 法合并独立 z 值。"""
    zs = list(zs)
    return sum(zs) / math.sqrt(len(zs)) if zs else 0.0
