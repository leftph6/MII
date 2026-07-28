# Harness Eval：bsc-webui

- 状态：通过
- Run ID：`004ae55d1cb042a99cc786601236ec06`
- 生成时间：2026-07-26T07:53:46+00:00
- 输出目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/harness-results/bsc-webui-20260726`
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
| `unit-tests` | 通过 | 0 | 1.120 | 1.120 | 1 |
| `compile` | 通过 | 0 | 0.203 | 0.203 | 1 |
| `security-boundary` | 通过 | 0 | 0.197 | 0.197 | 1 |

### unit-tests

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python -m pytest -p no:cacheprovider -q`
输出摘要：stdout `eca473fbd0e5311e6f643dfa99614f10d60ec985a8ffaeb425df56b7fbb92862` / 99 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
...........................                                              [100%]
27 passed in 0.58s
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
