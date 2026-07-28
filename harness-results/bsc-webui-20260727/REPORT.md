# Harness Eval：bsc-webui

- 状态：通过
- Run ID：`23862f48171b490897850466078e5557`
- 生成时间：2026-07-27T06:29:18+00:00
- 输出目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/harness-results/bsc-webui-20260727`
- 项目根目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference`
- 规格 SHA256：`c31dd84de33e9d0ebe8f33e7f42c9d49008b99e61e69db8bdd1019a509a158af`
- 运行前 Git 提交：`N/A`
- 运行前工作区：干净或不适用
- 工具解释器：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python`

## 项目运行环境快照

不适用说明：The BSC WebUI acceptance suite uses local fixtures and fake transports; live GeckoTerminal/RPC smoke is explicitly separate.
证据指纹：`bedc3e047da8595000d4aafff2e9bd99b1292b84fdb881548ede077f59c49fe9`

## 工程检查

| 检查 | 结果 | 退出码 | median（秒） | p95（秒） | 样本数 |
|---|---:|---:|---:|---:|---:|
| `unit-tests` | 通过 | 0 | 0.658 | 0.658 | 1 |
| `compile` | 通过 | 0 | 0.215 | 0.215 | 1 |
| `security-boundary` | 通过 | 0 | 0.184 | 0.184 | 1 |

### unit-tests

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python -m pytest -p no:cacheprovider -q`
输出摘要：stdout `aae06057bdf12f086771094a014295687848263784dc6086070bd54f87f00559` / 99 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
..............................                                           [100%]
30 passed in 0.09s
```

### compile

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python -m compileall -q src tests scripts`
输出摘要：stdout `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

### security-boundary

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python scripts/check_security.py`
输出摘要：stdout `601ae2734ca6e74a0b37946183395a26726ca65897aa034dbd7c34ac1a996a61` / 21 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
security_boundary_ok
```
