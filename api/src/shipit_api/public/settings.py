# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from decouple import config

SQLALCHEMY_DATABASE_URI = config("DATABASE_URL")
APP_CHANNEL = config("APP_CHANNEL")
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Use pessimistic disconnect handling as described at
# https://docs.sqlalchemy.org/en/13/core/pooling.html#disconnect-handling-pessimistic
# In some edge cases, when GCP performs maintenance on the database, the
# connection goes away, but sqlalchemy doesn't detect it.
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
READONLY_API = True
