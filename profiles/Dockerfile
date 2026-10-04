ARG BASE_IMAGE=python@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
FROM ${BASE_IMAGE}
COPY requirements.lock /requirements.lock
COPY wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
