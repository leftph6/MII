from market_intent_inference.application.run_store import RunStore


def test_run_store_redacts_connection_material(tmp_path) -> None:
    store = RunStore(tmp_path)
    result = store.write(
        "run-1",
        {
            "rpc_url": "https://user:secret@rpc.example/path?api_key=hidden#frag",
            "authorization": "Bearer hidden-token",
            "rpc": {
                "rpc_scheme": "https",
                "rpc_host": "rpc.example",
                "has_userinfo": True,
                "rpc_fingerprint": "abc123",
            },
        },
        [
            {
                "rpc_url": "https://user:secret@rpc.example/path?api_key=hidden#frag",
                "authorization": "Bearer hidden-token",
            }
        ],
    )
    assert result["audit_degraded"] is False
    text = (tmp_path / "run-1" / "summary.json").read_text()
    assert "secret" not in text
    assert "hidden" not in text
    assert "api_key" not in text
    assert "Bearer" not in text
    assert "rpc.example" in text
    assert "rpc.example/path" not in text
    assert len(store.read_events("run-1")) == 1


def test_run_store_appends_events_without_overwriting(tmp_path) -> None:
    store = RunStore(tmp_path)
    store.write("run-2", {}, [{"event_name": "first"}])
    store.write("run-2", {}, [{"event_name": "second"}])
    events = store.read_events("run-2")
    assert [event["event_name"] for event in events] == ["first", "second"]


def test_run_store_write_failure_is_degraded(tmp_path) -> None:
    blocked = tmp_path / "blocked"
    blocked.write_text("not-a-dir")
    store = RunStore(blocked)
    result = store.write("run-2", {"ok": True}, [{"event_name": "run.completed"}])
    assert result["audit_degraded"] is True


def test_run_store_rejects_symlinked_run_directory(tmp_path) -> None:
    root = tmp_path / "runs"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)

    result = RunStore(root).write("escape", {"ok": True}, [])

    assert result["audit_degraded"] is True
    assert not (outside / "summary.json").exists()
