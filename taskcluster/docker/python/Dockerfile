# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM          python:$PYTHON_VERSION

# Add worker user
RUN mkdir /builds && \
    groupadd -g 1000 -o worker && \
    useradd -d /builds/worker -s /bin/bash -m worker -g 1000 -o -u 1000 && \
    mkdir /builds/worker/artifacts && \
    chown worker:worker /builds/worker/artifacts

# %include-run-task

# Use pinned tox version from requirements
# %include api/requirements/tox.txt
ADD topsrcdir/api/requirements/tox.txt /tmp/tox.txt
RUN pip install -r /tmp/tox.txt && rm -rf /tmp/tox.txt

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache
WORKDIR /builds/worker

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
