from types import SimpleNamespace

from broadcast import agent_llm


class FakeCompletions:
    def __init__(self, captured):
        self._captured = captured

    def create(self, **kwargs):
        self._captured.update(kwargs)
        message = SimpleNamespace(content="  已生成的播报文本  ")
        choice = SimpleNamespace(message=message)
        usage = SimpleNamespace(prompt_tokens=42, completion_tokens=7)
        return SimpleNamespace(choices=[choice], usage=usage)


class FakeClient:
    def __init__(self, captured):
        self.chat = SimpleNamespace(completions=FakeCompletions(captured))


def test_complete_normalizes_usage_and_strips_text(monkeypatch):
    captured = {}
    monkeypatch.setattr(agent_llm, "client", lambda: FakeClient(captured))

    resp = agent_llm.complete([{"role": "user", "content": "总结一下"}], system="你是助手", max_tokens=500)

    assert agent_llm.text_of(resp) == "已生成的播报文本"
    assert resp.usage.input_tokens == 42
    assert resp.usage.output_tokens == 7
    assert captured["messages"][0] == {"role": "system", "content": "你是助手"}
    assert captured["messages"][1] == {"role": "user", "content": "总结一下"}
    assert captured["max_tokens"] == 500


def test_complete_without_system_message(monkeypatch):
    captured = {}
    monkeypatch.setattr(agent_llm, "client", lambda: FakeClient(captured))

    agent_llm.complete([{"role": "user", "content": "hi"}])

    assert captured["messages"] == [{"role": "user", "content": "hi"}]
