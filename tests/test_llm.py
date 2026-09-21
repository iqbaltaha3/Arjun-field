import llm

def test_safe_fallback_without_key(monkeypatch):
    monkeypatch.setattr(llm, 'LLM_API_KEY', '')
    out=llm.extract('आज बूथ 147 में कार्यकर्ताओं की बैठक हुई। लगभग 20 लोग थे।')
    assert out['activity_type']=='other'
    assert 'बैठक' in out['observation']
    assert out['attendance_estimate'] is None
