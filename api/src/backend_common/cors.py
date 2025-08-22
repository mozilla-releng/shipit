# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


def init_app(app: connexion.App):
    origins = app.app.config.get("CORS_ORIGINS") or "*"
    origins = origins.split(" ")
    app.add_middleware(
        CORSMiddleware,
        MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["authorization"],
    )
