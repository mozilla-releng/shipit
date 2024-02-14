from pprint import pprint

import pytest
from flask import Flask

from shipit_api.admin import github


@pytest.fixture(autouse=True)
def setup(monkeypatch, mocker):
    app = Flask(__name__)
    app.config["GITHUB_TOKEN"] = "token"
    with app.app_context():
        monkeypatch.setattr(github, "current_app", app)
        mocker.patch("shipit_api.admin.github._require_auth", return_value=None)
        yield


def test_list_github_branches(responses):
    rsp1 = responses.post(
        "https://api.github.com/graphql",
        json={
            "data": {
                "repository": {
                    "refs": {
                        "nodes": [{"name": "foo", "target": {"committedDate": "1"}}, {"name": "bar", "target": {"committedDate": "2"}}],
                        "pageInfo": {"hasNextPage": True, "endCursor": "abc"},
                    }
                }
            }
        },
    )
    rsp2 = responses.post(
        "https://api.github.com/graphql",
        json={
            "data": {
                "repository": {
                    "refs": {
                        "nodes": [{"name": "baz", "target": {"committedDate": "3"}}],
                        "pageInfo": {"hasNextPage": False, "endCursor": "def"},
                    }
                }
            }
        },
    )
    repos = github.list_github_branches("org", "repo", limit=2)
    assert b"after" not in rsp1.calls[0].request.body
    assert b'after: \\"abc\\",' in rsp2.calls[0].request.body

    print("Dumping for copy/paste:")
    pprint(repos)
    assert repos == [{"committer_date": "1", "name": "foo"}, {"committer_date": "2", "name": "bar"}, {"committer_date": "3", "name": "baz"}]
