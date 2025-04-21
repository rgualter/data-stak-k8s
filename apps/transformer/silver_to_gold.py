#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transformação de dados da camada Silver para Gold usando PySpark e Delta Lake
Este script lê dados Delta Lake da camada Silver e cria agregações para a camada Gold
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min, sum, count, date_format, window, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType, TimestampType
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações do MinIO
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'minio-api.storage.svc.cluster.local:9000')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
SILVER_BUCKET = os.environ.get('SILVER_BUCKET', 'silver')
GOLD_BUCKET = os.environ.get('GOLD_BUCKET', 'gold')

# Configurações do Delta Lake
SILVER_TABLE_PATH = f"s3a://{SILVER_BUCKET}/stock_data_delta"
GOLD_DAILY_METRICS_PATH = f"s3a://{GOLD_BUCKET}/daily_metrics"
GOLD_SYMBOL_METRICS_PATH = f"s3a://{GOLD_BUCKET}/symbol_metrics"
GOLD_MARKET_METRICS_PATH = f"s3a://{GOLD_BUCKET}/market_metrics"

def create_spark_session():
    """Cria e retorna uma sessão Spark configurada para Delta Lake e MinIO."""
    spark = SparkSession.builder \
        .appName("SilverToGoldTransformer") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}") \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()
    
    logger.info("Sessão Spark criada com sucesso")
    return spark

def read_silver_data(spark, table_path):
    """Lê os dados da camada Silver."""
    try:
        # Ler tabela Delta
        df = spark.read.format("delta").load(table_path)
        
        logger.info(f"Dados lidos com sucesso da camada Silver: {table_path}")
        logger.info(f"Número de registros: {df.count()}")
        return df
    except Exception as e:
        logger.error(f"Erro ao ler dados da camada Silver: {e}")
        raise

def create_daily_metrics(df):
    """Cria métricas diárias por símbolo."""
    try:
        # Agrupar por símbolo e data
        daily_metrics = df.groupBy("symbol", "date").agg(
            avg("open").alias("avg_open"),
            avg("close").alias("avg_close"),
            max("high").alias("max_high"),
            min("low").alias("min_low"),
            sum("volume").alias("total_volume"),
            count("*").alias("data_points")
        ).withColumn("processed_at", current_timestamp())
        
        logger.info("Métricas diárias criadas com sucesso")
        return daily_metrics
    except Exception as e:
        logger.error(f"Erro ao criar métricas diárias: {e}")
        raise

def create_symbol_metrics(df):
    """Cria métricas agregadas por símbolo."""
    try:
        # Agrupar por símbolo
        symbol_metrics = df.groupBy("symbol").agg(
            avg("close").alias("avg_close"),
            max("high").alias("max_high_all_time"),
            min("low").alias("min_low_all_time"),
            avg("volume").alias("avg_volume"),
            count("*").alias("total_data_points")
        ).withColumn("processed_at", current_timestamp())
        
        logger.info("Métricas por símbolo criadas com sucesso")
        return symbol_metrics
    except Exception as e:
        logger.error(f"Erro ao criar métricas por símbolo: {e}")
        raise

def create_market_metrics(df):
    """Cria métricas de mercado agregadas por data."""
    try:
        # Agrupar por data
        market_metrics = df.groupBy("date").agg(
            avg("close").alias("market_avg_close"),
            avg("volume").alias("market_avg_volume"),
            count("symbol").alias("symbols_count")
        ).withColumn("processed_at", current_timestamp())
        
        logger.info("Métricas de mercado criadas com sucesso")
        return market_metrics
    except Exception as e:
        logger.error(f"Erro ao criar métricas de mercado: {e}")
        raise

def save_to_delta(df, table_path):
    """Salva o DataFrame no formato Delta Lake."""
    try:
        # Salvar como tabela Delta
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .save(table_path)
        
        logger.info(f"Dados salvos com sucesso na tabela Delta: {table_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar dados na tabela Delta: {e}")
        raise

def main():
    """Função principal que executa o processo de transformação."""
    try:
        # Criar sessão Spark
        spark = create_spark_session()
        
        # Ler dados da camada Silver
        silver_df = read_silver_data(spark, SILVER_TABLE_PATH)
        
        if silver_df.count() == 0:
            logger.warning("Nenhum dado encontrado na camada Silver")
            return
        
        # Criar métricas diárias
        daily_metrics_df = create_daily_metrics(silver_df)
        save_to_delta(daily_metrics_df, GOLD_DAILY_METRICS_PATH)
        
        # Criar métricas por símbolo
        symbol_metrics_df = create_symbol_metrics(silver_df)
        save_to_delta(symbol_metrics_df, GOLD_SYMBOL_METRICS_PATH)
        
        # Criar métricas de mercado
        market_metrics_df = create_market_metrics(silver_df)
        save_to_delta(market_metrics_df, GOLD_MARKET_METRICS_PATH)
        
        logger.info("Processo de transformação Silver para Gold concluído com sucesso")
    except Exception as e:
        logger.error(f"Erro no processo de transformação: {e}")
        raise
    finally:
        if 'spark' in locals():
            spark.stop()

if __name__ == "__main__":
    main()
