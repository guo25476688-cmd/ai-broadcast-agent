from broadcast.summarize import summarize_source


def test_summarize_source_skips_llm_call_when_no_items():
    res = summarize_source("arxiv", [], keywords=["agent"], max_tokens=600)
    assert res["summary"] == "_(今日无相关条目)_"
    assert res["usage"].input_tokens == 0
    assert res["usage"].output_tokens == 0
