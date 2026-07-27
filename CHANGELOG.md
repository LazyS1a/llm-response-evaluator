# 更新日志

本项目采用[语义化版本](https://semver.org/lang/zh-CN/)记录 Skill、评测工具链与 EvalFlow Web 工作台的重要变化。

## [0.2.2] - 2026-07-28

### 新增

- EvalFlow 桌面端、移动端成品截图和三工作区操作演示 GIF。

### 变更

- README 首屏增加产品演示，并补充桌面端与移动端截图。
- 优化项目简介中的 Codex Skill 表述。

### 兼容性

- 应用功能、评分规则、复核逻辑、数据结构和导出格式保持不变。
- 自动测试仍为 30 项。

## [0.2.1] - 2026-07-28

### 变更

- 增加 EvalFlow 品牌图标，并重做工作台标题区与紧凑侧栏。
- 内置案例改为只读评测材料面板，用户问题、模型回答和参考答案更易扫描。
- 专业领域与难度使用中文标签，统一评分状态、图表和操作按钮的视觉语义。
- 优化桌面端与移动端响应式布局，减少默认 Streamlit 界面感。

### 兼容性

- 五维评分规则、人工复核逻辑、数据结构和导出格式保持不变。
- 自动测试仍为 30 项。

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

[0.2.2]: https://github.com/LazyS1a/llm-response-evaluator/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/LazyS1a/llm-response-evaluator/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/LazyS1a/llm-response-evaluator/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LazyS1a/llm-response-evaluator/tree/v0.1.0
