FROM python:3.9-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .

# Configurar variáveis de ambiente padrão
ENV MINIO_ENDPOINT=minio-api.storage.svc.cluster.local:9000 \
    MINIO_ACCESS_KEY=minioadmin \
    MINIO_SECRET_KEY=minioadmin \
    MINIO_BUCKET=bronze \
    SYMBOLS=AAPL,MSFT,GOOGL,AMZN,META \
    INTERVAL=1d \
    RANGE=1mo

# Executar a aplicação
CMD ["python", "app.py"]
