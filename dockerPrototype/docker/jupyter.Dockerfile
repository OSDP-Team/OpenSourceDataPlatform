FROM jupyter/pyspark-notebook:latest

USER root

RUN wget -P /usr/local/spark/jars/ https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
RUN wget -P /usr/local/spark/jars/ https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.688/aws-java-sdk-bundle-1.12.688.jar

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

USER jovyan