from broadcast import digest


def test_key_extracts_url():
    assert digest._key("- 标题 https://example.com/a?x=1，") == "https://example.com/a?x=1"


def test_key_falls_back_to_line_when_no_url():
    assert digest._key("  没有链接的一行  ") == "没有链接的一行"


def test_load_seen_missing_file_returns_empty_set(tmp_path, monkeypatch):
    monkeypatch.setattr(digest, "DIGEST_PATH", str(tmp_path / "does-not-exist.md"))
    assert digest.load_seen() == set()


def test_load_seen_collects_urls(tmp_path, monkeypatch):
    path = tmp_path / "digest.md"
    path.write_text("- 已经播过 https://a.example/1\n- 也播过 https://b.example/2\n", encoding="utf-8")
    monkeypatch.setattr(digest, "DIGEST_PATH", str(path))
    assert digest.load_seen() == {"https://a.example/1", "https://b.example/2"}


def test_dedup_drops_seen_lines_only():
    seen = {"https://a.example/1"}
    text = "- 旧的 https://a.example/1\n- 新的 https://c.example/3\n- 没链接的一行"
    result = digest.dedup(text, seen)
    assert "https://a.example/1" not in result
    assert "https://c.example/3" in result
    assert "没链接的一行" in result


def test_append_writes_dated_section(tmp_path, monkeypatch):
    path = tmp_path / "digest.md"
    monkeypatch.setattr(digest, "DIGEST_PATH", str(path))
    digest.append("今日播报", "第一条内容")
    text = path.read_text(encoding="utf-8")
    assert "今日播报" in text
    assert "第一条内容" in text
