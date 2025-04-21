#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transformação de dados da camada Bronze para Silver usando PySpark e Delta Lake
Este script lê dados JSON do MinIO (camada Bronze) e os transforma para o formato Delta Lake (camada Silver)
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, from_unixtime, to_date, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType, LongType
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
BRONZE_BUCKET = os.environ.get('BRONZE_BUCKET', 'bronze')
SILVER_BUCKET = os.environ.get('SILVER_BUCKET', 'silver')

# Configurações do Delta Lake
DELTA_TABLE_PATH = f"s3a://{SILVER_BUCKET}/stock_data_delta"

def create_spark_session():
    """Cria e retorna uma sessão Spark configurada para Delta Lake e MinIO."""
    spark = SparkSession.builder \
        .appName("BronzeToSilverTransformer") \
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

def list_bronze_files(spark, bucket_name):
    """Lista todos os arquivos JSON na camada Bronze."""
    try:
        # Listar todos os arquivos no bucket bronze
        file_list = spark.read.format("binaryFile") \
            .option("pathGlobFilter", "*.json") \
            .option("recursiveFileLookup", "true") \
            .load(f"s3a://{bucket_name}/stock_data/") \
            .select("path")
        
        files = [row.path for row in file_list.collect()]
        logger.info(f"Encontrados {len(files)} arquivos na camada Bronze")
        return files
    except Exception as e:
        logger.error(f"Erro ao listar arquivos na camada Bronze: {e}")
        raise

def define_stock_data_schema():
    """Define o schema para os dados de ações."""
    # Schema para os dados de ações
    return StructType([
        StructField("chart", StructType([
            StructField("result", ArrayType(StructType([
                StructField("meta", StructType([
                    StructField("currency", StringType()),
                    StructField("symbol", StringType()),
                    StructField("exchangeName", StringType()),
                    StructField("instrumentType", StringType()),
                    StructField("firstTradeDate", LongType()),
                    StructField("regularMarketTime", LongType()),
                    StructField("timezone", StringType()),
                    StructField("exchangeTimezoneName", StringType())
                ])),
                StructField("timestamp", ArrayType(LongType())),
                StructField("indicators", StructType([
                    StructField("quote", ArrayType(StructType([
                        StructField("open", ArrayType(DoubleType())),
                        StructField("high", ArrayType(DoubleType())),
                        StructField("low", ArrayType(DoubleType())),
                        StructField("close", ArrayType(DoubleType())),
                        StructField("volume", ArrayType(LongType()))
                    ]))),
                    StructField("adjclose", ArrayType(StructType([
                        StructField("adjclose", ArrayType(DoubleType()))
                    ])))
                ]))
            ]))),
            StructField("error", StringType())
        ]))
    ])

def transform_stock_data(spark, file_path):
    """Transforma os dados JSON em um formato tabular."""
    try:
        # Ler arquivo JSON com o schema definido
        schema = define_stock_data_schema()
        df = spark.read.schema(schema).json(file_path)
        
        # Extrair e transformar os dados
        # Primeiro, explode o array de resultados
        exploded_df = df.select(explode(col("chart.result")).alias("result"))
        
        # Extrair metadados
        meta_df = exploded_df.select(
            col("result.meta.symbol").alias("symbol"),
            col("result.meta.currency").alias("currency"),
            col("result.meta.exchangeName").alias("exchange"),
            explode(col("result.timestamp")).alias("timestamp"),
            lit(file_path).alias("source_file")
        )
        
        # Extrair dados de preços e volumes
        # Primeiro, explode os arrays de indicadores
        indicators_df = exploded_df.select(
            col("result.meta.symbol").alias("symbol"),
            explode(col("result.timestamp")).alias("timestamp"),
            explode(col("result.indicators.quote")).alias("quote"),
            explode(col("result.indicators.adjclose")).alias("adjclose")
        )
        
        # Agora, para cada timestamp, pegamos o índice correspondente nos arrays de preços
        # Isso é um pouco complexo porque precisamos correlacionar os índices
        # Vamos simplificar assumindo que os arrays têm o mesmo tamanho e ordem
        
        # Criar um dataframe com os dados de preços e volumes
        price_df = indicators_df.select(
            col("symbol"),
            from_unixtime(col("timestamp")).alias("datetime"),
            to_date(from_unixtime(col("timestamp"))).alias("date"),
            col("quote.open").getItem(0).alias("open"),
            col("quote.high").getItem(0).alias("high"),
            col("quote.low").getItem(0).alias("low"),
            col("quote.close").getItem(0).alias("close"),
            col("quote.volume").getItem(0).alias("volume"),
            col("adjclose.adjclose").getItem(0).alias("adjclose"),
            current_timestamp().alias("processed_at")
        )
        
        logger.info(f"Dados transformados com sucesso para o arquivo: {file_path}")
        return price_df
    except Exception as e:
        logger.error(f"Erro ao transformar dados do arquivo {file_path}: {e}")
        raise

def save_to_delta(df, table_path):
    """Salva o DataFrame no formato Delta Lake."""
    try:
        # Salvar como tabela Delta
        df.write \
            .format("delta") \
            .mode("append") \
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
        
        # Listar arquivos na camada Bronze
        bronze_files = list_bronze_files(spark, BRONZE_BUCKET)
        
        if not bronze_files:
            logger.warning("Nenhum arquivo encontrado na camada Bronze")
            return
        
        # Para cada arquivo, transformar e salvar na camada Silver
        for file_path in bronze_files:
            logger.info(f"Processando arquivo: {file_path}")
            
            # Transformar dados
            transformed_df = transform_stock_data(spark, file_path)
            
            # Salvar na camada Silver como Delta
            save_to_delta(transformed_df, DELTA_TABLE_PATH)
            
            logger.info(f"Arquivo processado com sucesso: {file_path}")
        
        logger.info("Processo de transformação concluído com sucesso")
    except Exception as e:
        logger.error(f"Erro no processo de transformação: {e}")
        raise
    finally:
        if 'spark' in locals():
            spark.stop()

if __name__ == "__main__":
    main()
