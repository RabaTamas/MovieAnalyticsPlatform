from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='movie_analytics_pipeline',
    default_args=default_args,
    description='Movie Analytics ETL Pipeline',
    schedule_interval='0 2 * * *',  # napi 02:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['movie_analytics'],
) as dag:

    ingest_csv_chunk_1 = BashOperator(
        task_id='ingest_csv_chunk_1',
        bash_command='cd /opt/airflow/project && python etl_csv_chunk_to_staging.py 1',
    )

    ingest_csv_chunk_2 = BashOperator(
        task_id='ingest_csv_chunk_2',
        bash_command='cd /opt/airflow/project && python etl_csv_chunk_to_staging.py 2',
    )

    ingest_csv_chunk_3 = BashOperator(
        task_id='ingest_csv_chunk_3',
        bash_command='cd /opt/airflow/project && python etl_csv_chunk_to_staging.py 3',
    )

    ingest_csv_chunk_4 = BashOperator(
        task_id='ingest_csv_chunk_4',
        bash_command='cd /opt/airflow/project && python etl_csv_chunk_to_staging.py 4',
    )

    load_dimensions = BashOperator(
        task_id='load_dimensions',
        bash_command='cd /opt/airflow/project && python etl_load_dimensions.py',
    )

    load_fact = BashOperator(
        task_id='load_fact',
        bash_command='cd /opt/airflow/project && python etl_load_fact.py',
    )

    load_aggregations = BashOperator(
        task_id='load_aggregations',
        bash_command='cd /opt/airflow/project && python etl_load_aggregations.py',
    )

    data_quality = BashOperator(
        task_id='data_quality_validation',
        bash_command='cd /opt/airflow/project && python etl_data_quality_validation.py',
    )

    # Függőségek
    ingest_csv_chunk_1 >> ingest_csv_chunk_2 >> ingest_csv_chunk_3 >> ingest_csv_chunk_4
    ingest_csv_chunk_4 >> load_dimensions >> load_fact >> load_aggregations >> data_quality