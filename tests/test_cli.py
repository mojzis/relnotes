from relnotes.cli import main


def test_guide_prints_the_writing_rules(capsys):
    assert main(["guide"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# relnotes guide")
    assert "kind: fixed" in out


def test_check_fails_and_points_to_the_guide(tmp_path, capsys):
    (tmp_path / "release-notes").mkdir()
    (tmp_path / "release-notes" / "bad.md").write_text("x")
    assert main(["--repo", str(tmp_path), "check"]) == 1
    assert "relnotes guide" in capsys.readouterr().err


def test_page_writes_out_file(tmp_path):
    out = tmp_path / "page.md"
    assert (
        main(["--repo", str(tmp_path), "page", "--out", str(out), "--title", "Changes"])
        == 0
    )
    assert out.read_text().startswith("# Changes\n")
