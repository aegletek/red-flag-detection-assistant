# syntax=docker/dockerfile:1.7

ARG ORBIT_CORE_IMAGE=orbit-core:latest
FROM ${ORBIT_CORE_IMAGE} AS runtime

USER root
WORKDIR /app

COPY pyproject.toml README.md ./
COPY red_flag_detection_assistant ./red_flag_detection_assistant

RUN pip install --no-cache-dir --no-deps . \
    && chown -R orbit:orbit /app

USER orbit

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3)"

CMD ["uvicorn", "red_flag_detection_assistant.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
