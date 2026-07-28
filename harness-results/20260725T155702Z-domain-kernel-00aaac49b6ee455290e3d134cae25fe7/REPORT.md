# Harness Eval：domain-kernel

- 状态：通过
- Run ID：`00aaac49b6ee455290e3d134cae25fe7`
- 生成时间：2026-07-25T15:57:03+00:00
- 输出目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/harness-results/20260725T155702Z-domain-kernel-00aaac49b6ee455290e3d134cae25fe7`
- 项目根目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference`
- 规格 SHA256：`9a70aa8981a1a722784f4e3629a2e5043ffc3902b928de0bc86a064317cd7162`
- 运行前 Git 提交：`N/A`
- 运行前工作区：干净或不适用
- 工具解释器：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python`

## 项目运行环境快照

不适用说明：The first domain kernel is intentionally deterministic and offline; fixtures are local.
证据指纹：`c3073f9c092e20cd99787baaa1656a85bae72e56e23c11d84c18ba5b8a64287c`

## 工程检查

| 检查 | 结果 | 退出码 | median（秒） | p95（秒） | 样本数 |
|---|---:|---:|---:|---:|---:|
| `unit-tests` | 通过 | 0 | 0.537 | 0.537 | 1 |
| `compile` | 通过 | 0 | 0.218 | 0.218 | 1 |
| `security-boundary` | 通过 | 0 | 0.167 | 0.167 | 1 |

### unit-tests

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python -m pytest -q`
输出摘要：stdout `f7a3bec363ef6cea193d4cc7fa9ad2b56c5a7474291c49994461aa80347dc518` / 99 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
..............                                                           [100%]
14 passed in 0.02s
```

### compile

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python -m compileall -q src tests`
输出摘要：stdout `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

### security-boundary

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python scripts/check_security.py`
输出摘要：stdout `601ae2734ca6e74a0b37946183395a26726ca65897aa034dbd7c34ac1a996a61` / 21 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
security_boundary_ok
```
