# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
APP_CHANNEL = os.environ["APP_CHANNEL"]
SQLALCHEMY_TRACK_MODIFICATIONS = False
READONLY_API = True
