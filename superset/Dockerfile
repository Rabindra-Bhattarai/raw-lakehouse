FROM apache/superset:4.1.1

USER root
# Driver so Superset can talk to Trino
RUN pip install --no-cache-dir "trino[sqlalchemy]==0.330.0"
COPY superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap.sh setup_dashboard.py /app/setup/
RUN chmod +x /app/setup/bootstrap.sh
USER superset

CMD ["/app/setup/bootstrap.sh"]
