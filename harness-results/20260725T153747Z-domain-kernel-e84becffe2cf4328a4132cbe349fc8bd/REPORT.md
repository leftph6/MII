# Harness Eval：domain-kernel

- 状态：失败
- Run ID：`e84becffe2cf4328a4132cbe349fc8bd`
- 生成时间：2026-07-25T15:37:48+00:00
- 输出目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/harness-results/20260725T153747Z-domain-kernel-e84becffe2cf4328a4132cbe349fc8bd`
- 项目根目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference`
- 规格 SHA256：`727753d4754683788f5d25cbc0f9a31b7829ea3d77e8e55dc3e086f38e4352c2`
- 运行前 Git 提交：`N/A`
- 运行前工作区：干净或不适用
- 工具解释器：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python`

## 项目运行环境快照

不适用说明：The first domain kernel is intentionally deterministic and offline; fixtures are local.
证据指纹：`c3073f9c092e20cd99787baaa1656a85bae72e56e23c11d84c18ba5b8a64287c`

## 工程检查

| 检查 | 结果 | 退出码 | median（秒） | p95（秒） | 样本数 |
|---|---:|---:|---:|---:|---:|
| `unit-tests` | 失败 | 1 | 0.335 | 0.335 | 1 |
| `compile` | 通过 | 0 | 0.236 | 0.236 | 1 |
| `security-boundary` | 通过 | 0 | 0.214 | 0.214 | 1 |

### unit-tests

命令：`python3 -m pytest -q`
输出摘要：stdout `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes；stderr `6292e661a1694825c6029238517051e765f6b77e8df24530e939a6e1a9f3022e` / 69 bytes

失败原因：
- 退出码为 1，期望 0
- stdout 缺少预期文本: 'passed'

#### stderr

```text
/opt/homebrew/opt/python@3.13/bin/python3.13: No module named pytest
```

### compile

命令：`python3 -m compileall -q src tests`
输出摘要：stdout `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

### security-boundary

命令：`python3 scripts/check_security.py`
输出摘要：stdout `601ae2734ca6e74a0b37946183395a26726ca65897aa034dbd7c34ac1a996a61` / 21 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
security_boundary_ok
```
