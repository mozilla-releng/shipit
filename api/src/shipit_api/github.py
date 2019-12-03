import json

import requests
import yaml
from flask import abort, current_app
from flask_login import current_user

from shipit_api.config import SCOPE_PREFIX

GITHUB_API_ENDPOINT = "https://api.github.com/graphql"


def _require_auth():
    required_permission = f"{SCOPE_PREFIX}/github"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")


def get_file_from_github(owner, repo, file_path, ref):
    query = """query {
      repository(owner:"%(owner)s", name:"%(repo)s") {
        object(expression: "%(ref)s:%(file_path)s") {
          ... on Blob {
            text
          }
        }
      }
    }
    """ % dict(
        owner=owner, repo=repo, ref=ref, file_path=file_path
    )
    content = query_api(query)
    return content["data"]["repository"]["object"]["text"]


def query_api(query):
    """ Make a query with a Github auth header, returning the json """
    _require_auth()
    if not current_app.config.get("GITHUB_TOKEN"):
        abort(500, "GITHUB_TOKEN is not defined and required in order to query github.com")
    headers = {"Authorization": "Bearer %s" % current_app.config.get("GITHUB_TOKEN")}
    req = requests.post(GITHUB_API_ENDPOINT, json={"query": query}, headers=headers)
    req.raise_for_status()

    j = req.json()
    if "errors" in j:
        raise RuntimeError(f"Github query error - {j['errors']}")
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
    """ % dict(
        owner=owner, repo=repo, ref=ref
    )
    commit = query_api(query)
    return commit["data"]["repository"]["ref"]["target"]["oid"]


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
    """ % dict(
        owner=owner, repo=repo, branch=branch, limit=limit
    )
    commits = query_api(query)
    edges = commits["data"]["repository"]["ref"]["target"]["history"]["edges"]
    return [{"revision": e["node"]["oid"], "message": e["node"]["messageHeadline"]} for e in edges]


def get_xpi_manifest(owner, repo, ref):
    manifest = yaml.safe_load(get_file_from_github(owner, repo, "xpi-manifest.yml", ref))
    return manifest


def get_config(owner, repo, ref):
    config = yaml.safe_load(get_file_from_github(owner, repo, "taskcluster/ci/config.yml", ref))
    return config


def get_package(owner, repo, revision):
    package = json.loads(get_file_from_github(owner, repo, "package.json", revision))
    return package


def list_xpis(owner, repo, revision):
    manifest = get_xpi_manifest(owner, repo, revision)
    config = get_config(owner, repo, revision)
    xpis = []
    for xpi in filter(lambda xpi: xpi["active"], manifest["xpis"]):
        repo_parts = config["taskgraph"]["repositories"][xpi["repo-prefix"]]["default-repository"].split(":")[-1].split("/")
        xpi_owner, xpi_repo = repo_parts[-2], repo_parts[-1]
        # convert "master" into a stable ref
        ref = config["taskgraph"]["repositories"][xpi["repo-prefix"]]["default-ref"]
        commit = ref_to_commit(xpi_owner, xpi_repo, ref)
        package = get_package(xpi_owner, xpi_repo, commit)
        xpis.append(
            {
                "revision": commit,
                "version": package["version"],
                "xpi_name": xpi["name"],
                "owner": xpi_owner,
                "repo": xpi_repo,
                "manifest_revision": revision,
                "addon-type": xpi["addon-type"],
            }
        )

    return {"xpis": xpis}


def get_xpi_type(owner, repo, revision, xpi_name):
    xpis = list_xpis(owner, repo, revision)["xpis"]
    our_xpi = list(filter(lambda xpi: xpi["xpi_name"] == xpi_name, xpis))[0]
    return our_xpi["addon-type"]
