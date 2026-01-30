def test_smoke_import_reviewer():
    import agents.review_agent.reviewer as reviewer  # noqa: F401


def test_collect_pr_diff_exists():
    import agents.review_agent.reviewer as reviewer

    assert callable(getattr(reviewer, "collect_pr_diff", None))