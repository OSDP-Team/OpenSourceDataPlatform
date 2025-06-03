from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'test',
    'start_date': datetime(2024, 1, 1),
    'retries': 0,
}

dag = DAG(
    'simple_test_dag',
    default_args=default_args,
    description='Einfacher Test DAG',
    schedule_interval=None,  # Manuell ausführbar
    catchup=False,
    tags=['test'],
)

def hello_world():
    print("🚀 HELLO WORLD - DAG LÄUFT!")
    print(f"⏰ Ausgeführt am: {datetime.now()}")
    print("✅ Git-Sync funktioniert!")
    return "SUCCESS"

hello_task = PythonOperator(
    task_id='hello_world_task',
    python_callable=hello_world,
    dag=dag,
)