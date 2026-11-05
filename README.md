# 周易关系演算引擎（zhouyi-engine）

以《周易》卦象系统为公共中间语言的关系演算机械引擎：人类、大语言模型与引擎三方以卦象对表，多方向求解、互相验证、迭代收敛、可回退。

纯 Python 标准库实现，无第三方依赖。

## 功能

| 命令 | 说明 |
|---|---|
| `gua` | 挂卦：实体六维属性 → 六爻卦象（算法1） |
| `audit` | 验算已声明关系，输出应力三态（一致/应变/断裂）与最小修复集 |
| `discover` | 枚举卦象成立但未声明的关系（结构机会发现） |
| `cascade` | 叙事传导：依赖级联闭包（算法2） |
| `profile` | 传导性画像 T |
| `backtest` | 回测协议：M1/M2/M2′ + 随机基线 z + 同构群置换检验（双零假设） |

## 复现

```bash
python -m unittest discover -s tests          # 19 项单元测试
python -m yijing.cli gua      cases/supply_chain.json
python -m yijing.cli backtest cases/supply_chain.json
python -m yijing.cli backtest cases/nokia.json
python -m yijing.cli backtest cases/texas_freeze.json
```

回测结果见 `results/backtest_results.json`，LLM 适配演示见 `results/llm_adaptation_demo.json`。
随机种子固定为 20261105，结果可复现。

## 案例与建模声明

- `cases/supply_chain.json`：新能源车供应链（**情景推演**，假想代工危机）；
- `cases/nokia.json`：诺基亚代际更替，仅以 2007 年 iPhone 发布**前**公开信息建模；
- `cases/texas_freeze.json`：德州寒潮（2021 Uri），以 2011 年 FERC/NERC 官方报告等事发前公开信息建模；
- `cases/supply_chain_llm_claims.json`：2026-11-05 由 LLM 会话生成的风险分析声明（用于适配层证伪演示）。

盲法交叉验证：`protocol/` 下含盲法协议、两份事发前事实包与独立建模者的编码输出；
比对结果见 `results/blind_validation.json`，由 `tools/blind_compare.py` 复算。

各案例的维度映射、断裂集依据均写入文件内 `modeling_notes` / `fracture_notes` 字段。

## 指标定义

- 信号集 = 规模≥3 的同构群成员 ∪ audit 断裂关系两端实体；
- M1 信号精确率、M2 信号召回、M2′ 级联召回（去种子闭包）；
- 基线：全体实体中同规模均匀随机重采样 1000 次，z = (obs − mean) / sd；
- 同构群置换检验：零假设(a) 均匀抽自 64 卦（主）、(b) 本案经验分布（稳健性）；
- Stouffer 合并：z = Σz_i / √n。
