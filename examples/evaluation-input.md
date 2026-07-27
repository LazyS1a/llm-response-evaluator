# Example Evaluation Input

## User Request

根据参考资料回答套餐是否包含离线使用功能。只回答“包含”或“不包含”，并附一句依据。

## Reference

基础套餐支持在线使用和云端同步。离线模式仅在专业套餐中提供。

## Model Answer

包含。基础套餐可以在没有网络时继续使用，并在恢复联网后自动同步。

## Expected Evaluation Notes

- The answer is relevant and clear.
- The central claim conflicts with the reference.
- `factuality` should be 1 or 2.
- Use `hallucination`.
- Set `human_review_required` to `true`.

