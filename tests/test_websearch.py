from cgm.websearch import normalize, on_page


def test_normalize_ignores_case_punctuation_and_spacing():
    assert normalize("  How much do piano lessons COST?!  ") == "how much do piano lessons cost"


def test_on_page_finds_a_question_split_by_markup():
    page = "<html><body><h1>Forum</h1><p>How much do <b>piano</b> lessons&nbsp;cost?</p></body></html>"
    assert on_page("How much do piano lessons cost?", page)


def test_on_page_ignores_scripts_and_missing_questions():
    page = "<script>var q = 'Can adults learn piano?';</script><p>Piano lessons near me</p>"
    assert not on_page("Can adults learn piano?", page)
