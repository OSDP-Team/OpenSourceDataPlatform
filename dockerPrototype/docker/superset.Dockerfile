FROM apache/superset:latest

USER root
RUN pip install --no-cache-dir psycopg2-binary && rm -rf ~/.cache/pip
USER superset