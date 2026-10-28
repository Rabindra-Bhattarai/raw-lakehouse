FROM python:3.12-slim

RUN pip install --no-cache-dir dbt-core==1.12.6 dbt-trino==1.10.6

WORKDIR /dbt
ENV DBT_PROFILES_DIR=/dbt
ENTRYPOINT ["dbt"]
CMD ["build"]
