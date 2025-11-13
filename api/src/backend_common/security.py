# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from connexion.middleware import MiddlewarePosition
from starlette.datastructures import MutableHeaders

class CSPMiddleware:
    def __init__(self, app, headers):
        self.app = app
        self.headers = headers

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_with_extra_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for key, value in self.headers:
                    headers.append(key, value)

            await send(message)

        await self.app(scope, receive, send_with_extra_headers)


# TODO: we need to remove unsafe-inline
DEFAULT_CSP_POLICY = {
    "default-src": "'none'",
    "script-src": "'self' 'unsafe-inline'",
    "style-src": "'self' 'unsafe-inline'",
    "img-src": "'self'",
    "connect-src": "'self'",
}
CSP = "; ".join(f"{k}: {v}" for (k, v) in DEFAULT_CSP_POLICY.items())
DEFAULT_HEADERS = [
    ("x-frame-options", "SAMEORIGIN"),
    ("x-content-type-options", "nosniff"),
    ("strict-transport-security", f"max-age={365 * 24 * 60 * 60}; includeSubDomains"),
    ("content-security-policy", CSP),
    ("referrer-policy", "strict-origin-when-cross-origin"),
]

def init_app(app):
    app.add_middleware(CSPMiddleware, MiddlewarePosition.BEFORE_EXCEPTION, headers=DEFAULT_HEADERS)
