"""
DAG para ingestão de dados financeiros (Bronze para Silver)
Este DAG orquestra o processo de ingestão de dados da API de mercado financeiro e transformação para Delta Lake
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.operators.dummy import DummyOperator

# Configurações padrão para as tarefas
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 4, 20)
}

# Definição do DAG
dag = DAG(
    'finance_bronze_to_silver',
    default_args=default_args,
    description='Pipeline de ingestão de dados financeiros e transformação para Delta Lake',
    schedule_interval='0 */6 * * *',  # A cada 6 horas
    catchup=False,
    tags=['finance', 'bronze', 'silver', 'delta'],
)

# Tarefa de início
start = DummyOperator(
    task_id='start',
    dag=dag,
)

# Tarefa de ingestão de dados (Bronze)
ingest_finance_data = KubernetesPodOperator(
    task_id='ingest_finance_data',
    name='finance-ingestor',
    namespace='ingestion',
    image='finance-ingestor:latest',
    cmds=["python", "app.py"],
    env_vars={
        'MINIO_ENDPOINT': 'minio-api.storage.svc.cluster.local:9000',
        'MINIO_BUCKET': 'bronze',
        'SYMBOLS': 'AAPL,MSFT,GOOGL,AMZN,META',
        'INTERVAL': '1d',
        'RANGE': '1mo'
    },
    secrets=[
        {
            'secret': 'minio-credentials',
            'key': 'root-user',
            'env_var': 'MINIO_ACCESS_KEY'
        },
        {
            'secret': 'minio-credentials',
            'key': 'root-password',
            'env_var': 'MINIO_SECRET_KEY'
        }
    ],
    resources={
        'request_cpu': '100m',
        'request_memory': '256Mi',
        'limit_cpu': '200m',
        'limit_memory': '512Mi'
    },
    is_delete_operator_pod=True,
    get_logs=True,
    dag=dag,
)

# Tarefa de transformação Bronze para Silver
transform_bronze_to_silver = KubernetesPodOperator(
    task_id='transform_bronze_to_silver',
    name='bronze-to-silver',
    namespace='processing',
    image='pyspark-transformer:latest',
    cmds=["spark-submit", "--master", "local[*]", "--packages", "io.delta:delta-core_2.12:2.2.0", 
          "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension", 
          "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog",
          "bronze_to_silver.py"],
    env_vars={
        'MINIO_ENDPOINT': 'minio-api.storage.svc.cluster.local:9000',
        'BRONZE_BUCKET': 'bronze',
        'SILVER_BUCKET': 'silver'
    },
    secrets=[
        {
            'secret': 'minio-credentials',
            'key': 'root-user',
            'env_var': 'MINIO_ACCESS_KEY'
        },
        {
            'secret': 'minio-credentials',
            'key': 'root-password',
            'env_var': 'MINIO_SECRET_KEY'
        }
    ],
    resources={
        'request_cpu': '500m',
        'request_memory': '1Gi',
        'limit_cpu': '1000m',
        'limit_memory': '2Gi'
    },
    is_delete_operator_pod=True,
    get_logs=True,
    dag=dag,
)

# Tarefa de fim
end = DummyOperator(
    task_id='end',
    dag=dag,
)

# Definição do fluxo de tarefas
start >> ingest_finance_data >> transform_bronze_to_silver >> end
