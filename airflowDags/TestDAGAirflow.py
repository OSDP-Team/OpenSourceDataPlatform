from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def print_hello():
    print("Hello from Airflow running in AKS!")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='test_aks_airflow',
    default_args=default_args,
    description='Ein einfacher Test-DAG für Airflow in AKS',
    schedule_interval='@daily',
    start_date=datetime(2025, 6, 1),
    catchup=False,
    tags=['test', 'aks'],
) as dag:

    # Einfacher Bash-Task
    task_hello_bash = BashOperator(
        task_id='print_hello_bash',
        bash_command='echo "Hello World from Airflow on AKS!"'
    )

    # Einfacher Python-Task
    task_hello_python = PythonOperator(
        task_id='print_hello_python',
        python_callable=print_hello
    )

    task_hello_bash >> task_hello_python