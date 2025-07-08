#!/bin/bash

# MinIO Console forwarden
kubectl port-forward svc/minio-console 9001:9001 > minio-console.log 2>&1 &

# Airflow Webserver forwarden
kubectl port-forward svc/airflow-webserver-default 8080:8080 > airflow-webserver.log 2>&1 &

echo "MinIO Console läuft auf http://localhost:9001"
echo "Airflow Webserver läuft auf http://localhost:8080"
echo "Logs: minio-console.log / airflow-webserver.log"
echo "Beende die Forwards mit: killall kubectl"
