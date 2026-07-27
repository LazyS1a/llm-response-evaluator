# LLM Response Evaluator

一个面向 AI 训练师、LLM 评测和 AI 产品测试场景的 Codex Skill 项目。它使用透明的五维评分规则审查模型回答，输出可校验的结构化 JSON，并通过纯 Python 脚本汇总整批评测结果。

## 解决什么问题

大模型回答经常出现答非所问、事实错误、遗漏要求、格式违规和引用错位。只写一句“回答不好”无法支持复盘和迭代，本项目把评价拆成统一维度、错误标签、证据说明和人工复核规则。

## 核心能力

- 按相关性、事实性、完整性、指令遵循和清晰度进行 1-5 分评分。
- 标注幻觉、无依据声明、答非所问、信息遗漏、指令违规和引用错位等错误。
- 对低置信度、低事实性和高风险案例自动要求人工复核。
- 校验单条 JSON 或批量 JSONL 的字段、分数、标签与复核逻辑。
- 汇总维度均分、通过数量、人工复核数量、错误标签和低分案例。
- 提供 10 条带 PDF 页码依据的天气学 / STEM 评测样例和人工复核表。

## 项目结构

```text
llm-response-evaluator/
├── skills/llm-response-evaluator/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   │   ├── rubric.md
│   │   ├── output-schema.md
│   │   └── stem-case-schema.md
│   └── scripts/
│       ├── validate_evaluations.py
│       ├── validate_stem_cases.py
│       ├── build_stem_review_sheet.py
│       ├── mark_stem_review.py
│       ├── build_prompt_simulation.py
│       ├── compare_prompt_versions.py
│       └── summarize_evaluations.py
├── data/
│   ├── sample_evaluations.jsonl
│   ├── stem_cases.jsonl
│   └── stem_draft_evaluations.jsonl
├── experiments/
│   ├── prompt-v1-question-only.txt
│   └── prompt-v2-reference-guided.txt
├── examples/evaluation-input.md
├── sources/meteorology_source_index.md
├── outputs/
├── tests/
└── README.md
```

## 快速验证

项目仅依赖 Python 3.10+ 标准库。

```powershell
python skills/llm-response-evaluator/scripts/validate_evaluations.py data/sample_evaluations.jsonl

python skills/llm-response-evaluator/scripts/validate_stem_cases.py `
  data/stem_cases.jsonl `
  --coverage-out outputs/stem_coverage.json

python skills/llm-response-evaluator/scripts/build_stem_review_sheet.py `
  data/stem_cases.jsonl `
  data/stem_draft_evaluations.jsonl `
  --output outputs/stem_human_review.md

python skills/llm-response-evaluator/scripts/mark_stem_review.py `
  data/stem_cases.jsonl stem-001 stem-002 `
  --status human_reviewed

python skills/llm-response-evaluator/scripts/build_prompt_simulation.py `
  data/stem_cases.jsonl `
  data/stem_draft_evaluations.jsonl `
  --outputs-out outputs/simulated_prompt_outputs.jsonl `
  --evaluations-out outputs/simulated_prompt_evaluations.jsonl

python skills/llm-response-evaluator/scripts/compare_prompt_versions.py `
  outputs/simulated_prompt_evaluations.jsonl `
  --json-out outputs/simulated_prompt_comparison.json `
  --markdown-out outputs/simulated_prompt_comparison.md

python skills/llm-response-evaluator/scripts/summarize_evaluations.py `
  data/sample_evaluations.jsonl `
  --json-out outputs/sample_summary.json `
  --markdown-out outputs/sample_report.md

python -m unittest discover -s tests -v
```

## 在 Codex 中使用

将 `skills/llm-response-evaluator` 复制到个人 Skills 目录并重启 Codex，然后输入：

```text
使用 $llm-response-evaluator，根据给定参考资料评测这段模型回答，并返回结构化 JSON。
```

Skill 负责依据规则判断答案；Python 脚本只做确定性的格式校验与批量统计，不会调用外部模型或读取 API Key。

天气学 / STEM 数据集的候选答案是为了校验流程而写的合成样例。它可以展示来源追踪、错误分类和人工复核流程，但不能当作真实模型排行榜。把真实模型输出替换进去之前，应记录模型名称、日期、提示词版本和原始回答。

`experiments` 中还提供一个透明标注的 Prompt V1/V2 模拟实验：V1 使用预先编写的混合质量候选答案，V2 使用人工复核参考答案。它只验证成对输出、评分和对比报告流程，不能证明任何真实模型获得效果提升。

## 证据边界

- 样例报告只能说明评测流程可运行，不能证明某个模型的真实准确率。
- 当前样例是用于验证工具链的合成案例，不代表生产数据或用户规模。
- 天气学参考答案来自本地课程 PDF 的页码级核对，原 PDF 不随仓库分发。
- 高风险、低置信度或引用冲突案例必须人工复核。
- 当前版本没有实时模型 API、Web 界面或生产部署。

## 后续升级

- 将 Markdown 人工复核表升级为轻量评审页面和 CSV 导入导出。
- 记录双人标注差异和一致性。
- 接入用户自选模型进行盲测对比。
- 增加按任务类型配置的评分规则。
