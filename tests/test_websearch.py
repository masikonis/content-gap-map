from cgm.websearch import normalize, on_page


def test_normalize_ignores_case_punctuation_and_spacing():
    assert normalize("  How much do piano lessons COST?!  ") == "how much do piano lessons cost"


def test_on_page_finds_a_question_split_by_markup():
    page = "<html><body><h1>Forum</h1><p>How much do <b>piano</b> lessons&nbsp;cost?</p></body></html>"
    assert on_page("How much do piano lessons cost?", page)


def test_on_page_ignores_scripts_and_missing_questions():
    page = "<script>var q = 'Can adults learn piano?';</script><p>Piano lessons near me</p>"
    assert not on_page("Can adults learn piano?", page)


def test_on_page_ignores_unclosed_scripts_without_slowing_down():
    page = "<script>" * 5000 + "<p>Can adults learn piano?</p>"
    assert not on_page("Can adults learn piano?", page)


def test_local_and_private_hosts_are_not_public():
    from cgm.websearch import public_address
    for host in ["localhost", "127.0.0.1", "192.168.1.1", "169.254.169.254", "::1"]:
        assert public_address(host) is None
