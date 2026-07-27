# 更新日志

本项目采用[语义化版本](https://semver.org/lang/zh-CN/)记录 Skill、评测工具链与 EvalFlow Web 工作台的重要变化。

## [0.2.0] - 2026-07-28

### 新增

- EvalFlow Streamlit 工作台，支持单条评测、自定义案例和五维评分。
- JSON / JSONL 批量分析、维度均分、错误分布和低分案例统计。
- 人工复核队列、复核结果暂存及 JSON / JSONL / Markdown 导出。
- Streamlit Community Cloud 公开 Demo。
- Web 应用逻辑测试与 Streamlit 启动检查。

### 变更

- GitHub Actions 增加 Web 应用依赖安装，继续覆盖 Python 3.10 与 3.12。
- README 增加在线体验、Web 工作台说明和版本入口。
- 自动测试由 21 项增加至 30 项。

### 证据边界

- Web 工作台不调用实时模型 API。
- 内置天气学结果来自已人工复核样例。
- Prompt V1 / V2 对比仍是模拟流程演示，不代表真实模型效果提升。

## [0.1.0] - 2026-07-28

### 新增

- LLM 回答质量评测 Skill 与五维评分规则。
- 九类错误标签和强制人工复核规则。
- JSON / JSONL 校验、批量汇总和 Markdown 报告脚本。
- 10 条 PDF 页码可追溯的天气学 / STEM 评测样例。
- Prompt V1 / V2 模板、20 条成对模拟输出和对比报告。
- 21 项自动测试及 GitHub Actions。

[0.2.0]: https://github.com/LazyS1a/llm-response-evaluator/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LazyS1a/llm-response-evaluator/tree/v0.1.0
