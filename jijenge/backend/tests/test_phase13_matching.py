from app.Modules.Matching.schema import MatchRequest, MatchResponseRequest


def test_match_limit_is_bounded():
    try:
        MatchRequest(limit=101)
        assert False
    except ValueError:
        assert True


def test_match_response_requires_boolean():
    try:
        MatchResponseRequest(accepted="not-a-bool")
        assert False
    except ValueError:
        assert True
