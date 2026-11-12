# The container image (specs/0054): the release's own wheel on Python 3.14, for hosts without it.
#
#   docker build -f container/Dockerfile --build-arg WHEEL=<file> --build-arg WHEEL_SHA256=<sha256> container/
#
# The build context is container/ holding this file, requirements.lock and the wheel. At a release the wheel is the
# PyPI-served file (sha256 equal to the built one, 0054 §4a); in CI it is the wheel built from the checkout. Every check
# of 0054 §6 is container/check_image.py's, run on the built image.

# python:3.14-slim (Debian trixie), the multi-platform index, pinned by digest (§4b). Its SQLite build is attested on
# linux/amd64 and linux/arm64; the gate below refuses the build otherwise (I2).
ARG BASE=python@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f
FROM ${BASE}

ARG WHEEL
ARG WHEEL_SHA256
COPY requirements.lock /tmp/requirements.lock
COPY ${WHEEL} /tmp/${WHEEL}

# I1: the wheel by sha256; its dependencies by hash from the committed lock; nothing resolved at build time.
RUN test -n "${WHEEL}" && test -n "${WHEEL_SHA256}" \
 && echo "${WHEEL_SHA256}  /tmp/${WHEEL}" | sha256sum -c - \
 && pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
 && pip install --no-cache-dir --no-deps "/tmp/${WHEEL}" \
 && pip check \
 && rm "/tmp/${WHEEL}" /tmp/requirements.lock \
 && useradd --system --uid 10001 --home-dir /home/veracium --no-create-home --shell /usr/sbin/nologin veracium \
 && mkdir -p /home/veracium /data \
 && chown 10001:10001 /home/veracium /data \
 && chmod 700 /home/veracium /data

# I4: non-root. The working directory is NOT /data: there, the default relative store path would land on the volume
# whatever the store variable is called, and I4 could not tell a wrong name from the right one (0054 §4b, C1).
USER 10001
WORKDIR /home/veracium

# §2: the four values the image fixes. It sets no trust-bearing variable (I3): ANTHROPIC_API_KEY,
# VERACIUM_MCP_CAPABILITY, VERACIUM_MCP_SOURCE_ID and VERACIUM_USER are the host's to supply at run time.
ENV VERACIUM_DB_PATH=/data/veracium.db \
    XDG_CONFIG_HOME=/data/config \
    XDG_STATE_HOME=/data/state \
    HOME=/home/veracium \
    PYTHONDONTWRITEBYTECODE=1

# I2, the attested gate: the status itself, as I2 reads it, never doctor's prose (C2). doctor prints why on refusal.
RUN python -c "import sys; from veracium.store.schema_version import runtime_status as r; s = r(); print('runtime status:', s.status); sys.exit(0 if s.status == 'attested' else 1)" \
 || { veracium doctor; exit 1; }

LABEL org.opencontainers.image.source="https://github.com/veracium-ai/Veracium" \
      org.opencontainers.image.description="Veracium: provenance-aware memory for AI agents, as an MCP stdio server (specs/0054)" \
      org.opencontainers.image.licenses="MIT"
VOLUME ["/data"]
ENTRYPOINT ["veracium-mcp"]
