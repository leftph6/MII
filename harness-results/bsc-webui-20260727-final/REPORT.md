# Harness Eval：bsc-webui

- 状态：通过
- Run ID：`4da4ae77b6c14cee887b8c249d5e98b7`
- 生成时间：2026-07-27T15:57:28+00:00
- 输出目录：`/Users/mashengyu/Desktop/quant research/market-intent-inference/harness-results/bsc-webui-20260727-final`
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
| `unit-tests` | 通过 | 0 | 6.777 | 6.777 | 1 |
| `compile` | 通过 | 0 | 2.597 | 2.597 | 1 |
| `security-boundary` | 通过 | 0 | 1.898 | 1.898 | 1 |

### unit-tests

命令：`/Users/mashengyu/miniforge3/envs/codex-engineering/bin/python -m pytest -p no:cacheprovider -q`
输出摘要：stdout `4ec477482b4b81afd67a41d19561a9fa7dce3921b1db450427de1f7237431aeb` / 99 bytes；stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` / 0 bytes

#### stdout

```text
...................................                                      [100%]
35 passed in 0.48s
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
