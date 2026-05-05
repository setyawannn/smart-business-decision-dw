FROM apache/superset:latest

USER root

RUN uv pip install --python /app/.venv/bin/python --no-cache clickhouse-connect

COPY config/superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap /app/bootstrap
RUN chown -R superset:superset /app/pythonpath/superset_config.py /app/bootstrap

USER superset
