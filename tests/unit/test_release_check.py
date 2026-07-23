from scripts.release_check import valid_release_ref


def test_release_ref_accepts_main_branch() -> None:
    assert valid_release_ref("main", set(), "", "") is True


def test_release_ref_accepts_exact_github_tag_checkout() -> None:
    assert valid_release_ref("", {"v0.1.0"}, "tag", "v0.1.0") is True


def test_release_ref_rejects_arbitrary_detached_head() -> None:
    assert valid_release_ref("", {"v0.1.0"}, "branch", "main") is False
    assert valid_release_ref("", {"v0.1.0"}, "tag", "v0.1.1") is False
    assert valid_release_ref("", set(), "tag", "v0.1.0") is False
