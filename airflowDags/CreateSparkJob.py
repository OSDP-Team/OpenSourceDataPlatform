import logging
import time
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook

log = logging.getLogger(__name__)

class SparkKubernetesOperator(BaseOperator):
    def __init__(self, spark_manifest: dict, namespace="default", poll_interval=10, **kwargs):
        super().__init__(**kwargs)
        self.spark_manifest = spark_manifest
        self.namespace = namespace
        self.poll_interval = poll_interval
        self.job_name = spark_manifest["metadata"]["name"]
        self.manifest_namespace = spark_manifest["metadata"].get("namespace", namespace)

    def execute(self, context):
        hook = KubernetesHook(conn_id=None) # Consider using a named Airflow connection ID
        api_client = hook.get_api_client()
        custom_objects_api = api_client.CustomObjectsApi()

        log.info(f"Attempting to create SparkApplication: {self.job_name} in namespace: {self.manifest_namespace}")

        try:
            # 1. Create SparkApplication
            custom_objects_api.create_namespaced_custom_object(
                group="spark.stackable.tech",
                version="v1alpha1",
                namespace=self.manifest_namespace,
                plural="sparkapplications",
                body=self.spark_manifest,
            )
            log.info(f"SparkApplication {self.job_name} created successfully.")

            # 2. Monitor Status
            status = "UNKNOWN"
            # Loop until the application is in a terminal state (Completed or Failed)
            while status not in ["Completed", "Failed"]:
                try:
                    spark_app = custom_objects_api.get_namespaced_custom_object(
                        group="spark.stackable.tech",
                        version="v1alpha1",
                        namespace=self.manifest_namespace,
                        plural="sparkapplications",
                        name=self.job_name,
                    )
                    status = spark_app.get("status", {}).get("applicationState", {}).get("state", "UNKNOWN")
                    log.info(f"SparkApplication {self.job_name} current state: {status}")

                    if status == "Completed":
                        log.info(f"SparkApplication {self.job_name} completed successfully.")
                        break # Exit loop on success
                    elif status == "Failed":
                        log.error(f"SparkApplication {self.job_name} failed.")
                        error_message = spark_app.get("status", {}).get("applicationState", {}).get("errorMessage", "No specific error message.")
                        raise Exception(f"SparkApplication {self.job_name} failed: {error_message}")
                    else: # "Unknown", "Pending", "Submitted", "Running", or any other non-terminal state
                        log.info(f"SparkApplication {self.job_name} is in state: {status}. Waiting for {self.poll_interval} seconds...")
                        time.sleep(self.poll_interval)

                except Exception as e:
                    log.error(f"Error while polling SparkApplication {self.job_name}: {e}")
                    raise # Re-raise to fail the Airflow task

        except Exception as e:
            log.error(f"Error creating SparkApplication {self.job_name}: {e}")
            raise # Re-raise to fail the Airflow task
