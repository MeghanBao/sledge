# sledge —— 把 Isabelle 的锤子递给 agent

[English](README.md) · **中文** · [Deutsch](README.de.md)

`sledge` 让 AI agent（或你自己）用 [Isabelle](https://isabelle.in.tum.de/) 证明助手及其 **Sledgehammer** 自动化，去**独立**判定一条形式化数学命题。你给它一条命题，它只回答三种之一：

- ✅ **VERIFIED**：Isabelle 机器核验通过了一个证明。
- ✗ **REFUTED**：命题为假（找到了反例）。
- ❓ **UNKNOWN**：没找到证明（或本机没装 Isabelle）。

**"没证出来"绝不会被当成"证伪"。** 证不出的命题一律停在 UNKNOWN——sledge 不吹牛。

> PyPI 包名：`sledge-prover`；导入名与命令：`sledge`。

---

## 给外行人：这到底是个什么东西？

像 Isabelle 这样的**证明助手**，是一种用绝对严格的方式检查数学证明的程序——它只有在每一个微小的逻辑步骤都被核验之后，才接受一条命题。靠"感觉对"是过不了的。

**Sledgehammer** 是 Isabelle 最有名的功能：你把一个目标丢给它，它就把问题甩给一堆强大的自动证明器，再把一个 Isabelle 能核验的证明递回来。它就像一台"证明探测器"。

为什么要把它接到 AI 上？因为大语言模型（ChatGPT、Claude…）很会说，但**会胡编**——它们会"证明"出错误的东西。所以与其信模型，不如让模型去**提出**一条精确命题，让 **Isabelle 当裁判**。Isabelle 核验通过，就是真的成立；通不过，sledge 就诚实地说 **UNKNOWN**，绝不假装。

**一句话概括：**

> AI 提出命题，Isabelle 的锤子裁决——VERIFIED、REFUTED，或一个诚实的 UNKNOWN。

---

## 为什么要做它

"听起来对"和"可证明为对"之间的鸿沟，正是 AI 推理翻车的地方。核验器填这个鸿沟：模型提出，一个**不会撒谎的检查者**裁决。`sledge` 就是**形式化**命题的这个检查者——而且它吃的正是 Isabelle 比其它证明器强的那口饭：Sledgehammer 的自动化，很多目标它无需人写证明就能自己搞定。

它和姊妹工具 [`wtns`](https://github.com/MeghanBao/wtns)（用 SymPy/Z3 核验**答案**）一个理念：**生产者不能给自己盖章**，不确定就报 UNKNOWN，绝不伪造。

---

## 前置条件

`sledge` 驱动一个**真实的 Isabelle 安装**——它自己不带。

1. 安装 Isabelle：<https://isabelle.in.tum.de/>（数 GB 的下载）。
2. 确保 `isabelle` 命令在 `PATH` 上，或把 `ISABELLE_BINARY` 设成它的完整路径。

没装 Isabelle 时，所有核验都诚实返回 **UNKNOWN**（库和命令行照样能装、能跑，只是暂时证不了东西）。

## 安装

```bash
pip install sledge-prover           # 核心（纯 Python，无依赖）
pip install "sledge-prover[mcp]"    # + 给 agent 用的 MCP server
```

从克隆的仓库做开发：`pip install -e ".[dev]"`。需要 Python ≥ 3.9。

## 快速上手（命令行）

```bash
# 尝试证明一条命题（Isabelle/HOL 语法）：
sledge prove "(a::nat) + b = b + a"
# ✓ VERIFIED: proved by simp        （装了 Isabelle 时）

# 更难的目标会自动落到 Sledgehammer 的外部证明器上。
sledge prove "(a::int) + b = b + a"

# 改为找反例：
sledge refute "(n::nat) > 0"
# ✗ REFUTED: 找到反例（n = 0）

# 直接构建一个完整的 .thy theory 文件：
sledge check mytheory.thy
```

退出码对应裁决：**0 = VERIFIED，1 = REFUTED，2 = UNKNOWN**。加 `--json` 得到机器可读输出；`--no-sledgehammer` 只用便宜的 tactic；`-i THEORY` 加 import；`-t 秒数` 设超时。

## 快速上手（Python）

```python
from sledge import prove, refute

prove("(a::nat) + b = b + a")                 # VERIFIED（用的证明方法在 .detail 里）
prove("distinct [a, b] ⟹ a ≠ b")             # 先试 tactic，再上 Sledgehammer
refute("(n::nat) > 0")                         # REFUTED，附反例
```

每次调用返回一个 `Result`，含 `.status`、`.reason`、`.detail`，仅在 VERIFIED 时为真值。

## 作为 MCP server 使用（给 agent）

```bash
pip install "sledge-prover[mcp]"
```

```json
{
  "mcpServers": {
    "sledge": { "command": "sledge-mcp" }
  }
}
```

agent 会拿到两个 tool：`prove_statement` 和 `find_counterexample`，各自返回 `{status, reason, detail}`。这样 agent 就能在"声称一条引理之前"先核验它——证不了时得到诚实的 UNKNOWN。

## 它是怎么工作的

给定一条命题，`prove`：

1. 先试一批便宜的 Isabelle tactic（`simp`、`auto`、`blast`、`metis`…）；
2. 都不行就上 **Sledgehammer**，解析它给出的证明（`Try this: by (metis …)`）并**重新核验这个证明**——所以 VERIFIED 永远意味着一个真正机器核验通过的证明；
3. 还证不出，就跑 **Nitpick/Quickcheck** 找反例 → REFUTED；
4. 否则 → **UNKNOWN**。

## 它**故意不做**的事

- 它**不做自动形式化**。你给的是 Isabelle/HOL 语法；把英文/中文变成它，是另一个更难的问题。
- 它**不**把"没找到证明"当成"假"。那是朴素证明器的头号大忌；这里一律 **UNKNOWN**。
- 它**不**负责安装或管理 Isabelle。

## 状态说明

证明/解析逻辑用一个 Isabelle 替身做了测试（13 个通过，无需安装）。输出解析针对的是 Sledgehammer/Nitpick 的标准格式；当你在自己的 Isabelle 版本上跑时，可能需要根据本地措辞微调 `parse_sledgehammer` / `parse_counterexample`。

## 它适合用在哪

- **Agent** —— 一个 MCP 工具，让 agent 在断言形式化主张前先核验。
- **RLVR** —— 为形式化数学生成提供可验证奖励（证明通过与否，二值分明）。
- **自动形式化管线** —— 补上**验证**那一半：给一个候选 Isabelle 命题，它到底证不证得出来？

## 开发与测试

```bash
pip install -e ".[dev]"
pytest -q          # 13 个测试，无需 Isabelle
```

## 许可

MIT —— 见 [LICENSE](LICENSE)。
