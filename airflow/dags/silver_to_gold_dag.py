"""
DAG para transformação de dados financeiros (Silver para Gold)
Este DAG orquestra o processo de transformação de dados Delta Lake da camada Silver para Gold
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
    'finance_silver_to_gold',
    default_args=default_args,
    description='Pipeline de transformação de dados financeiros da camada Silver para Gold',
    schedule_interval='30 */6 * * *',  # A cada 6 horas, 30 minutos após o DAG bronze_to_silver
    catchup=False,
    tags=['finance', 'silver', 'gold', 'delta'],
)

# Tarefa de início
start = DummyOperator(
    task_id='start',
    dag=dag,
)

# Tarefa de transformação Silver para Gold
transform_silver_to_gold = KubernetesPodOperator(
    task_id='transform_silver_to_gold',
    name='silver-to-gold',
    namespace='processing',
    image='pyspark-transformer:latest',
    cmds=["spark-submit", "--master", "local[*]", "--packages", "io.delta:delta-core_2.12:2.2.0", 
          "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension", 
          "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog",
          "silver_to_gold.py"],
    env_vars={
        'MINIO_ENDPOINT': 'minio-api.storage.svc.cluster.local:9000',
        'SILVER_BUCKET': 'silver',
        'GOLD_BUCKET': 'gold'
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
start >> transform_silver_to_gold >> end
