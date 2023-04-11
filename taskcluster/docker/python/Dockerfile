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

# %include api/requirements/poetry.txt
ADD topsrcdir/api/requirements/poetry.txt /tmp/poetry.txt
RUN pip install -r /tmp/poetry.txt

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache
WORKDIR /builds/worker

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
