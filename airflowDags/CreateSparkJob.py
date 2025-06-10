from airflow import DAGAdd commentMore actions
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime

# Define the DAG
with DAG(
    "clone_and_run_spark_k8s_operator",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["spark", "kubernetes", "stackable"],
) as dag:
# SparkApplication YAML
spark_yaml = {
    "apiVersion": "spark.stackable.tech/v1alpha1",
    "kind": "SparkApplication",
    "metadata": {"name": "spark-job", "namespace": "default"},
    "spec": {
        "sparkImage": {"productVersion": "3.5.5"},
        "mode": "cluster",
        "mainApplicationFile": "local:///tmp/your-private-repo/airflowDags/SparkTest.py",
        "driver": {"config": {"resources": {"memory": {"limit": "1Gi"}}}},
        "executor": {"replicas": 1, "config": {"resources": {"memory": {"limit": "2Gi"}}}}
    }
}

with DAG("spark_job", start_date=datetime(2023, 1, 1), schedule_interval=None, catchup=False) as dag:

    # Clone the private repository
    clone_repo = BashOperator(
        task_id='clone_private_repo',
        bash_command="""
        rm -rf /tmp/your-private-repo || true
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}'
        GIT_USER='{{ var.value.GIT_USER }}'
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
        task_id='clone_repo',
        bash_command=
        """
        rm -rf /tmp/your-private-repo || true 
        GIT_TOKEN='{{ var.value.GITHUB_TOKEN }}' 
        GIT_USER='{{ var.value.GIT_USER }}' 
        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/NESuchi/Open-Source-Data-Platform.git /tmp/your-private-repo
         """ 
    )

    # Create and run Spark application using Stackable operator
    run_spark_job = SparkKubernetesOperator(
        task_id='run_spark_application',
        namespace='default',
        application_file='/tmp/your-private-repo/airflowDags/SparkTest.py',
        
        # Spark configuration
        spark_conf={
            'spark.app.name': 'airflow-spark-job',
            'spark.kubernetes.namespace': 'default',
            'spark.executor.instances': '1',
            'spark.executor.cores': '1',
            'spark.executor.memory': '2g',
            'spark.driver.cores': '1',
            'spark.driver.memory': '1g',
        },
        
        # Driver configuration
        driver_config={
            'cores': 1,
            'memory': '1g',
            'serviceAccount': 'spark-driver-sa',  # Adjust as needed
        },
        
        # Executor configuration
        executor_config={
            'cores': 1,
            'memory': '2g',
            'instances': 1,
        },
        
        # Volume mounts for shared storage
        volume_mounts=[
            {
                'name': 'shared-volume',
                'mountPath': '/shared'
            }
        ],
        
        # Volumes
        volumes=[
            {
                'name': 'shared-volume',
                'persistentVolumeClaim': {
                    'claimName': 'shared-spark-pvc'
                }
            }
        ],
        
        # Image configuration (using Stackable Spark image)
        image='ghcr.io/stackable/spark:3.4.1-debian-11-r0',
        
        # Additional configurations
        do_xcom_push=True,
        
        # Connection ID for Kubernetes (adjust as needed)
        kubernetes_conn_id='kubernetes_default',
    submit_spark_job = KubernetesPodOperator(
        task_id='submit_spark_job',
        name='spark-submitter',
        image='bitnami/kubectl:latest',
        cmds=['kubectl'],
        arguments=['apply', '-f', '-'],
        env_vars={'KUBECONFIG': '/var/run/secrets/kubernetes.io/serviceaccount'},
        in_cluster=True,
        body_template=str(spark_yaml).replace("'", '"')
    )

    # Set task dependencies
    clone_repo >> run_spark_job
    clone_repo >> submit_spark_job
