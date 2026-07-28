# Harness Eval：domain-kernel

- 状态：失败
- Run ID：`5e0830eac8e64fe588f46d2d7ccc45b2`
- 生成时间：2026-07-25T15:30:42+00:00
- 输出目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/evals/harness-results/20260725T153041Z-domain-kernel-5e0830eac8e64fe588f46d2d7ccc45b2`
- 项目根目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/evals`
- 规格 SHA256：`7ddd2d6f570467b60ea37d9a6bce461e6585ec29d0e1b65dc185af650c3625f5`
- 运行前 Git 提交：`N/A`
- 运行前工作区：干净或不适用
- 工具解释器：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python`

## 项目运行环境快照

不适用说明：The first domain kernel is intentionally deterministic and offline; fixtures are local.
证据指纹：`c3073f9c092e20cd99787baaa1656a85bae72e56e23c11d84c18ba5b8a64287c`

## 工程检查

| 检查 | 结果 | 退出码 | median（秒） | p95（秒） | 样本数 |
|---|---:|---:|---:|---:|---:|
| `unit-tests` | 失败 | 1 | 0.433 | 0.433 | 1 |
| `compile` | 通过 | 0 | 0.339 | 0.339 | 1 |
| `security-boundary` | 失败 | 2 | 0.183 | 0.183 | 1 |

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
输出摘要：stdout `13a1c863887ffc72ca8153fcc58dea29ad629eb363a7005d0a7761f21d146b0f` / 36 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
Can't list 'src'
Can't list 'tests'
```

### security-boundary

命令：`python3 scripts/check_security.py`
输出摘要：stdout `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes；stderr `7290363f7fd7b25af196eb3617c962c7d56697e2fef2dbc4dc5ec8bde8806b50` / 277 bytes

失败原因：
- 退出码为 2，期望 0
- stdout 缺少预期文本: 'security_boundary_ok'

#### stderr

```text
/opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/mashengyu/Desktop/quant research/market-intent-inference/evals/scripts/check_security.py': [Errno 2] No such file or directory
```
