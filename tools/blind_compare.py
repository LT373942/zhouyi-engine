# -*- coding: utf-8 -*-
"""盲法交叉验证比对：独立建模者编码 vs 本团队编码 vs 公开断裂集。

用法：python tools/blind_compare.py
输出：results/blind_validation.json 与控制台摘要。
"""

import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys_path = ROOT
import sys
sys.path.insert(0, sys_path)

from yijing import engine
from yijing.metrics import backtest

PAIRS = [
    ("nokia", "cases/nokia.json", "protocol/blind/nokia_blind.json"),
    ("texas", "cases/texas_freeze.json", "protocol/blind/texas_blind.json"),
]


def val(x):
    return {True: 1, False: 0}.get(x) if isinstance(x, bool) else x


def lines_of(values):
    m = {"yang": 1, "yin": 0, "none": None}
    return [m[v] for v in values]


def kappa(a, b):
    """池化爻位的 Cohen's kappa（仅取双侧已定且同为 0/1 的爻位）。"""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return None
    n = len(pairs)
    po = sum(1 for x, y in pairs if x == y) / n
    pa = sum(1 for x, _ in pairs if x == 1) / n
    pb = sum(1 for _, y in pairs if y == 1) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else None


def compare(name, ours_path, blind_path):
    ours = engine.load_case(os.path.join(ROOT, ours_path))
    blind = json.load(open(os.path.join(ROOT, blind_path), encoding="utf-8"))

    our_lines = {e["id"]: lines_of(e["values"]) for e in ours["entities"]}
    blind_lines = {e["id"]: lines_of(e["values"]) for e in blind["entities"]}

    # 1) 编码一致率
    exact = sum(1 for eid in our_lines if our_lines[eid] == blind_lines[eid])
    pos_total, pos_agree, pos_blind_none = 0, 0, 0
    pooled_a, pooled_b = [], []
    diffs = []
    for eid, la in our_lines.items():
        lb = blind_lines[eid]
        for i, (x, y) in enumerate(zip(la, lb)):
            pos_total += 1
            if y is None:
                pos_blind_none += 1
            elif x == y:
                pos_agree += 1
                pooled_a.append(x); pooled_b.append(y)
            else:
                pooled_a.append(x); pooled_b.append(y)
                diffs.append(f"{eid}第{i+1}爻(我={x},盲={y})")

    # 2) 盲模回测：以公开断裂集为准
    blind_case = {
        "case": f"{name}_blind",
        "dims": ours["dims"],
        "entities": blind["entities"],
        "relations": [],
        "dependencies": blind["dependencies"],
        "seeds": blind["seeds"],
        "fracture": ours["fracture"],  # 公开断裂集（外部真值，非我方设定）
    }
    bt = backtest(blind_case, n=1000)

    # 3) 盲模预测名单 vs 公开断裂集
    pred = set(blind.get("predicted_fracture", []))
    frac = set(ours["fracture"])
    pred_p = len(pred & frac) / len(pred) if pred else None
    pred_r = len(pred & frac) / len(frac) if frac else None

    # 4) 我方 flagged vs 盲模 flagged 重叠
    our_bt = backtest(ours, n=1000)
    ov = set(our_bt["flagged"]) & set(bt["flagged"])

    return {
        "case": name,
        "exact_entity_match": f"{exact}/{len(our_lines)}",
        "position_agree_rate": round(pos_agree / max(pos_total - pos_blind_none, 1), 3),
        "blind_none_positions": pos_blind_none,
        "kappa": round(kappa(pooled_a, pooled_b), 3) if pooled_a else None,
        "diff_positions": diffs,
        "blind_clusters": bt["clusters"],
        "blind_M1": bt["M1"], "blind_M2": bt["M2"],
        "blind_M2p": bt["M2p"], "blind_T": None,
        "blind_predicted_fracture": sorted(pred),
        "pred_precision": round(pred_p, 3) if pred_p is not None else None,
        "pred_recall": round(pred_r, 3) if pred_r is not None else None,
        "flagged_overlap": sorted(ov),
        "flagged_overlap_rate": round(len(ov) / len(set(our_bt["flagged"]) | set(bt["flagged"])), 3) if our_bt["flagged"] or bt["flagged"] else None,
    }


if __name__ == "__main__":
    out = {}
    for name, ours_path, blind_path in PAIRS:
        out[name] = compare(name, ours_path, blind_path)
        r = out[name]
        print("=" * 60)
        print(f"[{name}] 实体级完全一致: {r['exact_entity_match']} | "
              f"爻位一致率: {r['position_agree_rate']} | kappa: {r['kappa']}")
        print(f"  盲模同构群: {r['blind_clusters']}")
        print(f"  盲模 M1={r['blind_M1']} M2={r['blind_M2']} M2'={r['blind_M2p']}")
        print(f"  盲模预测断裂: {r['blind_predicted_fracture']} "
              f"(精确率={r['pred_precision']}, 召回={r['pred_recall']})")
        print(f"  flagged 重叠: {r['flagged_overlap']} (Jaccard={r['flagged_overlap_rate']})")
        if r["diff_positions"]:
            print(f"  分歧爻位: {r['diff_positions']}")
    with open(os.path.join(ROOT, "results", "blind_validation.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n已存 results/blind_validation.json")
