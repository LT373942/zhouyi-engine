# -*- coding: utf-8 -*-
"""SNA 方法基线：在同一案例的依赖图上运行社会网络分析中心性指标，
与本文同构群标记做对比。纯标准库实现。

指标：
- 被依赖度（depended_by，度中心性的有向变体）：直接依赖某实体的数量；
- PageRank（d=0.85，100 轮迭代，边方向 t→h，重要性流向被依赖者）；
- 介数中心性（Brandes 算法，有向图）。

标记规则（与本文信号集可比）：按各指标取分最高的前 |断裂集| 个实体为高危标记，
计算与公开断裂集的精确率（k=|断裂| 时精确率=召回率）。并列时全部计入并在结果中注明。
"""

import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
import sys
sys.path.insert(0, ROOT)

from yijing import engine


def graph(case):
    """依赖图，边 t→h（重要性/影响从被依赖者流向依赖者）。"""
    adj = {e["id"]: [] for e in case["entities"]}
    for h, t in case.get("dependencies", []):
        adj[t].append(h)
    return adj


def degree_scores(case):
    adj = graph(case)
    return {k: len(v) for k, v in adj.items()}


def pagerank_scores(case, d=0.85, iters=100):
    adj = graph(case)
    nodes = list(adj)
    n = len(nodes)
    rank = {x: 1.0 / n for x in nodes}
    for _ in range(iters):
        nxt = {x: (1 - d) / n for x in nodes}
        for t in nodes:
            share = d * rank[t] / len(adj[t]) if adj[t] else 0
            for h in adj[t]:
                nxt[h] += share
        rank = nxt
    return rank


def betweenness_scores(case):
    """Brandes 有向图介数中心性（归一化省略，仅用于排序）。"""
    adj = graph(case)
    nodes = list(adj)
    bc = {x: 0.0 for x in nodes}
    for s in nodes:
        # BFS 最短路径计数
        dist = {s: 0}
        sigma = {x: 0 for x in nodes}
        sigma[s] = 1
        pred = {x: [] for x in nodes}
        order, queue = [], [s]
        while queue:
            v = queue.pop(0)
            order.append(v)
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = {x: 0.0 for x in nodes}
        for v in reversed(order):
            for p in pred[v]:
                delta[p] += sigma[p] / sigma[v] * (1 + delta[v])
            if v != s:
                bc[v] += delta[v]
    return bc


def topk(scores, k):
    """取前 k 名，处理并列：边界分数并列者全部计入。"""
    items = sorted(scores.items(), key=lambda kv: -kv[1])
    if not items:
        return []
    cut = items[k - 1][1] if k <= len(items) else items[-1][1]
    picked = [x for x, s in items if s >= cut and s > 0]
    return sorted(picked)


def evaluate(case):
    fracture = set(case["fracture"])
    k = len(fracture)
    res = {}
    for name, fn in (("depended_by", degree_scores),
                     ("pagerank", pagerank_scores),
                     ("betweenness", betweenness_scores)):
        picked = set(topk(fn(case), k))
        inter = len(picked & fracture)
        prec = inter / len(picked) if picked else 0.0
        rec = inter / k if k else 0.0
        res[name] = {"picked": sorted(picked), "precision": round(prec, 3),
                     "recall": round(rec, 3)}
    return res


def framework_signals(case):
    """框架信号（同构群 / 传导闭包 / 组合）在同一口径下的 P/R，供公平对比。"""
    from yijing.metrics import backtest
    bt = backtest(case, n=1000)
    fracture = set(case["fracture"])
    closure = set(bt["closure"])
    flagged = set(bt["flagged"])
    out = {}
    for name, sig in (("isomorphism", flagged), ("cascade", closure), ("combined", flagged | closure)):
        inter = len(sig & fracture)
        out[name] = {"picked": sorted(sig),
                     "precision": round(inter / len(sig), 3) if sig else 0.0,
                     "recall": round(inter / len(fracture), 3)}
    return out


CASES = ["supply_chain", "nokia", "texas_freeze", "fukushima", "financial_2008",
         "film_digital", "blockbuster", "chip_shortage", "edu_double_reduction",
         "europe_energy_2022"]

if __name__ == "__main__":
    out = {}
    for c in CASES:
        case = engine.load_case(os.path.join(ROOT, f"cases/{c}.json"))
        out[case["case"]] = evaluate(case)
        out[case["case"]]["framework"] = framework_signals(case)
        print("=" * 60)
        print(case["case"], f"断裂集({len(case['fracture'])}):", sorted(case["fracture"]))
        for m, r in out[case["case"]].items():
            if m == "framework":
                for fm, fr in r.items():
                    print(f"  框架·{fm:11s} P={fr['precision']} R={fr['recall']} picked={fr['picked']}")
            else:
                print(f"  {m:12s} P={r['precision']} R={r['recall']} picked={r['picked']}")
    with open(os.path.join(ROOT, "results", "sna_baseline.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n已存 results/sna_baseline.json")
