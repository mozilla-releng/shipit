import re
from functools import lru_cache
from urllib.parse import unquote, urlparse

import requests
import yaml
from flask import abort, current_app
from flask_login import current_user
from sentry_sdk import capture_exception

from shipit_api.common.config import SCOPE_PREFIX, get_allowed_github_files

GITHUB_API_ENDPOINT = "https://api.github.com/graphql"


def _require_auth():
    required_permission = f"{SCOPE_PREFIX}/github"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")


@lru_cache(maxsize=10)
def get_file_from_github(owner, repo, ref, path):
    allowed_files = get_allowed_github_files(owner, repo)
    if not any(af.fullmatch(path) for af in allowed_files):
        raise ValueError(f"Retrieving {path} not allowed for {owner}/{repo}!")

    path = unquote(path)
    query = """query {
      repository(owner:"%(owner)s", name:"%(repo)s") {
        object(expression: "%(ref)s:%(path)s") {
          ... on Blob {
            text
          }
        }
      }
    }
    """ % dict(owner=owner, repo=repo, ref=ref, path=path)
    content = query_api(query)
    return content["data"]["repository"]["object"]["text"]


def get_files_from_github(owner, repo, file_path, ref):
    query = """query {
      repository(owner:"%(owner)s", name:"%(repo)s") {
        object(expression: "%(ref)s:%(file_path)s") {
          ... on Tree {
            entries {
              name
              type
              mode
              object {
                ... on Blob {
                  byteSize
                  isBinary
                  text
                }
              }
            }
          }
        }
      }
    }
    """ % dict(owner=owner, repo=repo, ref=ref, file_path=file_path)
    content = query_api(query)

    entries = content["data"]["repository"]["object"]["entries"]
    all_manifests = {}
    for xpi in entries:
        if not xpi["name"].endswith(".yml"):
            continue
        name = xpi["name"].split(".yml")[0]
        data = yaml.safe_load(xpi["object"]["text"])
        data["name"] = name
        assert name not in all_manifests
        all_manifests[name] = data
    return all_manifests


def query_api(query):
    """Make a query with a Github auth header, returning the json"""
    _require_auth()
    if not current_app.config.get("GITHUB_TOKEN"):
        abort(500, "GITHUB_TOKEN is not defined and required in order to query github.com")
    headers = {"Authorization": "Bearer %s" % current_app.config.get("GITHUB_TOKEN")}
    req = requests.post(GITHUB_API_ENDPOINT, json={"query": query}, headers=headers)
    req.raise_for_status()

    j = req.json()
    if "errors" in j:
        abort(502, f"Github query error - {j['errors']}")
    return j


def ref_to_commit(owner, repo, ref):
    query = """
    {
      repository(name: "%(repo)s", owner: "%(owner)s") {
        ref(qualifiedName: "%(ref)s") {
          target {
            ... on Commit {
              oid
            }
          }
        }
      }
    }
    """ % dict(owner=owner, repo=repo, ref=ref)
    commit = query_api(query)
    return commit["data"]["repository"]["ref"]["target"]["oid"]


def list_github_branches(owner, repo, limit=100):
    page = {
        "hasNextPage": True,
        "endCursor": None,
    }

    branches = []
    while page["hasNextPage"]:
        after = ""
        if page["endCursor"]:
            after = f", after: \"{page['endCursor']}\""

        query = """
        {
          repository(name: "%(repo)s", owner: "%(owner)s") {
            refs(first: %(limit)s%(after)s, refPrefix: "refs/heads/") {
              nodes {
                name
                target {
                  ... on Commit {
                    committedDate
                  }
                }
              }
              pageInfo {
                endCursor
                hasNextPage
              }
            }
          }
        }
        """ % dict(owner=owner, repo=repo, limit=limit, after=after)
        content = query_api(query)
        page = content["data"]["repository"]["refs"]["pageInfo"]

        nodes = content["data"]["repository"]["refs"]["nodes"]
        branches.extend([{"committer_date": node["target"]["committedDate"], "name": node["name"]} for node in nodes])

    return branches


def list_github_commits(owner, repo, branch, limit=10):
    query = """
    {
      repository(name: "%(repo)s", owner: "%(owner)s") {
        ref(qualifiedName: "%(branch)s") {
          target {
            ... on Commit {
              id
              history(first: %(limit)s) {
                edges {
                  node {
                    author {
                      email
                      name
                    }
                    committer {
                      date
                    }
                    messageHeadline
                    oid
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % dict(owner=owner, repo=repo, branch=branch, limit=limit)
    commits = query_api(query)
    edges = commits["data"]["repository"]["ref"]["target"]["history"]["edges"]
    return [
        {
            "author": "{} <{}>".format(e["node"]["author"]["name"], e["node"]["author"]["email"]),
            "committer_date": e["node"]["committer"]["date"],
            "message": e["node"]["messageHeadline"],
            "revision": e["node"]["oid"],
        }
        for e in edges
    ]


def get_xpi_manifest(owner, repo, ref):
    return get_files_from_github(owner, repo, "manifests", ref)


def get_taskgraph_config(owner, repo, ref):
    config = yaml.safe_load(get_file_from_github(owner, repo, ref, "taskcluster/config.yml"))
    return config


def list_xpis(owner, repo, revision):
    manifests = get_xpi_manifest(owner, repo, revision)
    config = get_taskgraph_config(owner, repo, revision)
    xpis = []
    for xpi in filter(lambda xpi: xpi["active"], [manifests[m] for m in manifests]):
        if current_app.config.get("GITHUB_SKIP_PRIVATE_REPOS") and xpi.get("private-repo"):
            # Skip private repos in localdev and maybe staging
            continue
        repo_url = config["taskgraph"]["repositories"][xpi["repo-prefix"]]["default-repository"]
        xpi_owner, xpi_repo = extract_github_repo_owner_and_name(repo_url)
        # convert "master" into a stable ref
        ref = xpi.get("branch", config["taskgraph"]["repositories"][xpi["repo-prefix"]]["default-ref"])
        commit = ref_to_commit(xpi_owner, xpi_repo, ref)
        try:
            xpis.append(
                {
                    "revision": commit,
                    "branch": xpi.get("branch", "master"),
                    "xpi_name": xpi["name"],
                    "owner": xpi_owner,
                    "repo": xpi_repo,
                    "manifest_revision": revision,
                    "directory": xpi.get("directory", ""),
                    "addon-type": xpi["addon-type"],
                    "install_type": xpi.get("install-type", "yarn"),
                }
            )
        except TypeError as exc:
            capture_exception(exc)

    return {"xpis": xpis}


def get_xpi_type(owner, repo, revision, xpi_name):
    xpis = list_xpis(owner, repo, revision)["xpis"]
    our_xpi = get_single_item_from_sequence(xpis, lambda xpi: xpi["xpi_name"] == xpi_name)
    xpi_type = our_xpi["addon-type"]
    if xpi_type == "system":
        xpi_type += f"_{our_xpi['xpi_name']}"
    return xpi_type


def extract_github_repo_owner_and_name(url):
    """Given an URL, return the repo name and who owns it.
    Args:
        url (str): The URL to the GitHub repository
    Returns:
        str, str: the owner of the repository, the repository name
    """

    parts = get_parts_of_url_path(url)
    repo_owner = parts[0]
    repo_name = parts[1]

    if repo_name.endswith(".git"):
        repo_name = re.sub("\\.git$", "", repo_name)
    return repo_owner, repo_name


def get_parts_of_url_path(url):
    """Given a url, take out the path part and split it by '/'.
    Args:
        url (str): the url slice
    returns
        list: parts after the domain name of the URL
    """
    if "@" in url:
        # git@github.com:owner/repo
        return url.split(":")[-1].split("/")
    parsed = urlparse(url)
    path = unquote(parsed.path).lstrip("/")
    parts = path.split("/")
    return parts


def get_single_item_from_sequence(
    sequence,
    condition,
    ErrorClass=ValueError,
    no_item_error_message="No item matched condition",
    too_many_item_error_message="Too many items matched condition",
    append_sequence_to_error_message=True,
):
    """Return an item from a python sequence based on the given condition.
    Args:
        sequence (sequence): The sequence to filter
        condition: A function that serves to filter items from `sequence`. Function
            must have one argument (a single item from the sequence) and return a boolean.
        ErrorClass (Exception): The error type raised in case the item isn't unique
        no_item_error_message (str): The message raised when no item matched the condition
        too_many_item_error_message (str): The message raised when more than one item matched the condition
        append_sequence_to_error_message (bool): Show or hide what was the tested sequence in the error message.
            Hiding it may prevent sensitive data (such as password) to be exposed to public logs
    Returns:
        The only item in the sequence which matched the condition
    """
    filtered_sequence = [item for item in sequence if condition(item)]
    number_of_items_in_filtered_sequence = len(filtered_sequence)
    if number_of_items_in_filtered_sequence == 0:
        error_message = no_item_error_message
    elif number_of_items_in_filtered_sequence > 1:
        error_message = too_many_item_error_message
    else:
        return filtered_sequence[0]

    if append_sequence_to_error_message:
        error_message = "{}. Given: {}".format(error_message, sequence)
    raise ErrorClass(error_message)


def is_github_url(url):
    """Tell if a given URL matches a Github one.
    Args:
        url (str): The URL to test. It can be None.
    Returns:
        bool: False if the URL is not a string or if it doesn't match a Github URL
    """
    if isinstance(url, str):
        return url.startswith(("https://github.com/", "ssh://github.com/"))
    else:
        return False
