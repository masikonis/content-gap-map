from cgm.withhold import mask, run, terms


def test_mask_replaces_every_term_ignoring_case_longest_first():
    text, count = mask("https://x.example/blog/acme-alternatives | ACME Piano | acme piano school",
                       ["acme", "acme piano"])
    assert text == "https://x.example/blog/[withheld]-alternatives | [withheld] | [withheld] school"
    assert count == 3


def test_run_masks_text_files_and_leaves_others(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "blocklist.txt").write_text("acme\n\n")
    assert terms() == ["acme"]
    run_folder = tmp_path / "run"
    run_folder.mkdir()
    (run_folder / "pages.csv").write_text("url\nhttps://x.example/acme-vs-us\n")
    (run_folder / "raw.bin").write_bytes(b"acme")
    run(run_folder)
    assert "[withheld]-vs-us" in (run_folder / "pages.csv").read_text()
    assert (run_folder / "raw.bin").read_bytes() == b"acme"
