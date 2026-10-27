# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


@pytest.mark.parametrize(
    "url",
    (
        "/releases?product=%00",
        "/releases?status=scheduled,ship%00ped",
        "/releases?pro%00duct=firefox",
        "/releases/Firefox-1.0-build1%00",
        "/releases/Firefox-1.0-build1/ship%00",
    ),
)
def test_nul_bytes_in_url_rejected(app, url):
    with app.test_client() as client:
        response = client.get(url)
    assert response.status_code == 400


def test_nul_bytes_in_body_rejected(app):
    with app.test_client() as client:
        response = client.post("/releases", json={"branch": "try", "build_number": 1, "product": "firefox", "revision": "12\x003", "version": "69.0"})
    assert response.status_code == 400


@pytest.mark.parametrize(
    "build_number, status_code",
    (
        (0, 400),
        (1, 200),
        (2147483647, 200),
        (2147483648, 400),
        (-99999999999, 400),
    ),
)
def test_build_number_must_fit_in_db_integer(app, build_number, status_code):
    with app.test_client() as client:
        response = client.get(f"/releases?version=1.0&build_number={build_number}")
    assert response.status_code == status_code


def test_build_number_in_body_must_fit_in_db_integer(app):
    with app.test_client() as client:
        response = client.post("/releases", json={"branch": "try", "build_number": 2147483648, "product": "firefox", "revision": "123", "version": "69.0"})
    assert response.status_code == 400
