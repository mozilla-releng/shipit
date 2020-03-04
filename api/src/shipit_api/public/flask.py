# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import shipit_api.public.settings as app_config
from shipit_api.public import create_app

app = create_app(config=app_config.__file__)
