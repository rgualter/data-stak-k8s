FROM apache/spark-py:v3.3.0

USER root

# Instalar dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-11-jdk \
    python3-pip \
    python3-setuptools \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar variáveis de ambiente
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Instalar dependências Python
COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY *.py /app/

# Ponto de entrada
ENTRYPOINT ["spark-submit", "--master", "local[*]", "--packages", "io.delta:delta-core_2.12:2.2.0", "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension", "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog"]
