#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notebook de exemplo para análise de dados financeiros
Este notebook demonstra como acessar e analisar dados das camadas Silver e Gold
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import SparkSession
import psycopg2
from sqlalchemy import create_engine

# Configurações de conexão
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'minio-api.storage.svc.cluster.local:9000')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
SILVER_BUCKET = 'silver'
GOLD_BUCKET = 'gold'

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres.storage.svc.cluster.local')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'datastack')

# Função para criar sessão Spark
def create_spark_session():
    """Cria e retorna uma sessão Spark configurada para Delta Lake e MinIO."""
    spark = SparkSession.builder \
        .appName("JupyterAnalysis") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}") \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()
    
    return spark

# Função para conectar ao PostgreSQL
def connect_to_postgres():
    """Cria e retorna uma conexão ao PostgreSQL."""
    conn_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    engine = create_engine(conn_string)
    return engine

# Exemplo 1: Leitura de dados da camada Silver usando PySpark
def read_silver_data():
    """Lê dados da camada Silver usando PySpark."""
    spark = create_spark_session()
    
    # Ler tabela Delta
    silver_df = spark.read.format("delta").load(f"s3a://{SILVER_BUCKET}/stock_data_delta")
    
    # Mostrar schema e primeiras linhas
    silver_df.printSchema()
    silver_df.show(5)
    
    # Converter para Pandas para visualização
    pandas_df = silver_df.toPandas()
    
    return pandas_df

# Exemplo 2: Leitura de dados da camada Gold usando PySpark
def read_gold_data():
    """Lê dados da camada Gold usando PySpark."""
    spark = create_spark_session()
    
    # Ler tabelas Delta da camada Gold
    daily_metrics_df = spark.read.format("delta").load(f"s3a://{GOLD_BUCKET}/daily_metrics")
    symbol_metrics_df = spark.read.format("delta").load(f"s3a://{GOLD_BUCKET}/symbol_metrics")
    market_metrics_df = spark.read.format("delta").load(f"s3a://{GOLD_BUCKET}/market_metrics")
    
    # Mostrar schema e primeiras linhas
    print("Daily Metrics:")
    daily_metrics_df.printSchema()
    daily_metrics_df.show(5)
    
    print("Symbol Metrics:")
    symbol_metrics_df.printSchema()
    symbol_metrics_df.show(5)
    
    print("Market Metrics:")
    market_metrics_df.printSchema()
    market_metrics_df.show(5)
    
    # Converter para Pandas para visualização
    daily_pandas_df = daily_metrics_df.toPandas()
    symbol_pandas_df = symbol_metrics_df.toPandas()
    market_pandas_df = market_metrics_df.toPandas()
    
    return daily_pandas_df, symbol_pandas_df, market_pandas_df

# Exemplo 3: Visualização de dados usando Matplotlib e Seaborn
def visualize_stock_data(daily_metrics_df):
    """Cria visualizações para os dados de ações."""
    # Configurar estilo
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 6))
    
    # Filtrar para um símbolo específico
    symbol = 'AAPL'  # Exemplo com Apple
    symbol_data = daily_metrics_df[daily_metrics_df['symbol'] == symbol]
    
    # Ordenar por data
    symbol_data = symbol_data.sort_values('date')
    
    # Plotar preço médio de fechamento ao longo do tempo
    plt.plot(symbol_data['date'], symbol_data['avg_close'], marker='o', linestyle='-')
    plt.title(f'Preço Médio de Fechamento para {symbol}')
    plt.xlabel('Data')
    plt.ylabel('Preço Médio de Fechamento ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Mostrar gráfico
    plt.show()
    
    # Comparação entre símbolos
    plt.figure(figsize=(12, 6))
    
    # Agrupar por símbolo e calcular média de fechamento
    symbol_avg = daily_metrics_df.groupby('symbol')['avg_close'].mean().reset_index()
    
    # Criar gráfico de barras
    sns.barplot(x='symbol', y='avg_close', data=symbol_avg)
    plt.title('Preço Médio de Fechamento por Símbolo')
    plt.xlabel('Símbolo')
    plt.ylabel('Preço Médio de Fechamento ($)')
    plt.tight_layout()
    
    # Mostrar gráfico
    plt.show()

# Exemplo 4: Exportar dados para PostgreSQL
def export_to_postgres(daily_metrics_df, symbol_metrics_df, market_metrics_df):
    """Exporta os dados para o PostgreSQL."""
    engine = connect_to_postgres()
    
    # Exportar DataFrames para PostgreSQL
    daily_metrics_df.to_sql('daily_metrics', engine, if_exists='replace', index=False)
    symbol_metrics_df.to_sql('symbol_metrics', engine, if_exists='replace', index=False)
    market_metrics_df.to_sql('market_metrics', engine, if_exists='replace', index=False)
    
    print("Dados exportados com sucesso para o PostgreSQL!")

# Exemplo de uso
if __name__ == "__main__":
    # Ler dados da camada Silver
    silver_data = read_silver_data()
    
    # Ler dados da camada Gold
    daily_metrics, symbol_metrics, market_metrics = read_gold_data()
    
    # Visualizar dados
    visualize_stock_data(daily_metrics)
    
    # Exportar para PostgreSQL
    export_to_postgres(daily_metrics, symbol_metrics, market_metrics)
