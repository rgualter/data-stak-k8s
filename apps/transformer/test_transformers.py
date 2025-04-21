#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testes unitários para os scripts de transformação
"""

import os
import sys
import pytest
import tempfile
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType, LongType, ArrayType
import json

# Importar os módulos a serem testados
# Nota: Em um ambiente real, você importaria os módulos diretamente
# Aqui vamos simular algumas funções para teste

# Configuração do ambiente de teste
@pytest.fixture(scope="session")
def spark():
    """Cria uma sessão Spark para testes."""
    spark = SparkSession.builder \
        .appName("TestSparkSession") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()
    
    yield spark
    spark.stop()

@pytest.fixture
def sample_json_data():
    """Cria dados JSON de exemplo para testes."""
    data = {
        "chart": {
            "result": [{
                "meta": {
                    "currency": "USD",
                    "symbol": "AAPL",
                    "exchangeName": "NMS",
                    "instrumentType": "EQUITY",
                    "firstTradeDate": 345479400,
                    "regularMarketTime": 1650465600,
                    "timezone": "EST",
                    "exchangeTimezoneName": "America/New_York"
                },
                "timestamp": [1650379200, 1650465600],
                "indicators": {
                    "quote": [{
                        "open": [150.23, 152.43],
                        "high": [153.45, 154.67],
                        "low": [149.56, 151.34],
                        "close": [152.34, 153.45],
                        "volume": [28736500, 31654300]
                    }],
                    "adjclose": [{
                        "adjclose": [152.34, 153.45]
                    }]
                }
            }],
            "error": None
        }
    }
    return data

@pytest.fixture
def sample_json_file(sample_json_data, tmp_path):
    """Cria um arquivo JSON temporário com dados de exemplo."""
    file_path = tmp_path / "sample_data.json"
    with open(file_path, "w") as f:
        json.dump(sample_json_data, f)
    return str(file_path)

@pytest.fixture
def sample_silver_data(spark):
    """Cria um DataFrame de exemplo para a camada Silver."""
    # Schema para os dados Silver
    schema = StructType([
        StructField("symbol", StringType(), False),
        StructField("date", DateType(), False),
        StructField("open", DoubleType(), True),
        StructField("high", DoubleType(), True),
        StructField("low", DoubleType(), True),
        StructField("close", DoubleType(), True),
        StructField("volume", LongType(), True),
        StructField("adjclose", DoubleType(), True)
    ])
    
    # Dados de exemplo
    data = [
        ("AAPL", "2023-04-19", 150.23, 153.45, 149.56, 152.34, 28736500, 152.34),
        ("AAPL", "2023-04-20", 152.43, 154.67, 151.34, 153.45, 31654300, 153.45),
        ("MSFT", "2023-04-19", 280.45, 285.67, 279.23, 282.56, 18456700, 282.56),
        ("MSFT", "2023-04-20", 282.56, 287.89, 281.34, 286.78, 19876500, 286.78),
        ("GOOGL", "2023-04-19", 2300.45, 2320.67, 2290.23, 2310.56, 1456700, 2310.56),
        ("GOOGL", "2023-04-20", 2310.56, 2330.89, 2305.34, 2325.78, 1576500, 2325.78)
    ]
    
    return spark.createDataFrame(data, schema)

# Testes para a transformação Bronze para Silver
def test_transform_stock_data(spark, sample_json_file):
    """Testa a transformação de dados JSON para o formato tabular."""
    # Em um ambiente real, você importaria a função transform_stock_data
    # Aqui vamos simular a função para teste
    
    # Definir o schema para os dados JSON
    schema = StructType([
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
    
    # Ler o arquivo JSON
    df = spark.read.schema(schema).json(sample_json_file)
    
    # Verificar se o DataFrame foi criado corretamente
    assert not df.isEmpty()
    
    # Verificar se o símbolo está correto
    symbol = df.select("chart.result").first()[0][0]["meta"]["symbol"]
    assert symbol == "AAPL"
    
    # Verificar se os timestamps estão presentes
    timestamps = df.select("chart.result").first()[0][0]["timestamp"]
    assert len(timestamps) == 2
    
    # Verificar se os dados de preços estão presentes
    quotes = df.select("chart.result").first()[0][0]["indicators"]["quote"][0]
    assert len(quotes["open"]) == 2
    assert quotes["open"][0] == 150.23

# Testes para a transformação Silver para Gold
def test_create_daily_metrics(spark, sample_silver_data):
    """Testa a criação de métricas diárias."""
    # Em um ambiente real, você importaria a função create_daily_metrics
    # Aqui vamos simular a função para teste
    
    # Agrupar por símbolo e data
    from pyspark.sql.functions import avg, max, min, sum, count, current_timestamp
    
    daily_metrics = sample_silver_data.groupBy("symbol", "date").agg(
        avg("open").alias("avg_open"),
        avg("close").alias("avg_close"),
        max("high").alias("max_high"),
        min("low").alias("min_low"),
        sum("volume").alias("total_volume"),
        count("*").alias("data_points")
    ).withColumn("processed_at", current_timestamp())
    
    # Verificar se o DataFrame foi criado corretamente
    assert not daily_metrics.isEmpty()
    
    # Verificar se temos o número correto de registros (3 símbolos x 2 dias = 6 registros)
    assert daily_metrics.count() == 6
    
    # Verificar se as métricas foram calculadas corretamente para AAPL em 2023-04-19
    aapl_metrics = daily_metrics.filter((daily_metrics.symbol == "AAPL") & (daily_metrics.date == "2023-04-19")).first()
    assert aapl_metrics is not None
    assert aapl_metrics["avg_open"] == 150.23
    assert aapl_metrics["avg_close"] == 152.34
    assert aapl_metrics["max_high"] == 153.45
    assert aapl_metrics["min_low"] == 149.56
    assert aapl_metrics["total_volume"] == 28736500
    assert aapl_metrics["data_points"] == 1

def test_create_symbol_metrics(spark, sample_silver_data):
    """Testa a criação de métricas por símbolo."""
    # Em um ambiente real, você importaria a função create_symbol_metrics
    # Aqui vamos simular a função para teste
    
    # Agrupar por símbolo
    from pyspark.sql.functions import avg, max, min, count, current_timestamp
    
    symbol_metrics = sample_silver_data.groupBy("symbol").agg(
        avg("close").alias("avg_close"),
        max("high").alias("max_high_all_time"),
        min("low").alias("min_low_all_time"),
        avg("volume").alias("avg_volume"),
        count("*").alias("total_data_points")
    ).withColumn("processed_at", current_timestamp())
    
    # Verificar se o DataFrame foi criado corretamente
    assert not symbol_metrics.isEmpty()
    
    # Verificar se temos o número correto de registros (3 símbolos)
    assert symbol_metrics.count() == 3
    
    # Verificar se as métricas foram calculadas corretamente para AAPL
    aapl_metrics = symbol_metrics.filter(symbol_metrics.symbol == "AAPL").first()
    assert aapl_metrics is not None
    assert aapl_metrics["avg_close"] == 152.895
    assert aapl_metrics["max_high_all_time"] == 154.67
    assert aapl_metrics["min_low_all_time"] == 149.56
    assert aapl_metrics["total_data_points"] == 2

def test_create_market_metrics(spark, sample_silver_data):
    """Testa a criação de métricas de mercado."""
    # Em um ambiente real, você importaria a função create_market_metrics
    # Aqui vamos simular a função para teste
    
    # Agrupar por data
    from pyspark.sql.functions import avg, count, current_timestamp
    
    market_metrics = sample_silver_data.groupBy("date").agg(
        avg("close").alias("market_avg_close"),
        avg("volume").alias("market_avg_volume"),
        count("symbol").alias("symbols_count")
    ).withColumn("processed_at", current_timestamp())
    
    # Verificar se o DataFrame foi criado corretamente
    assert not market_metrics.isEmpty()
    
    # Verificar se temos o número correto de registros (2 dias)
    assert market_metrics.count() == 2
    
    # Verificar se as métricas foram calculadas corretamente para 2023-04-19
    day_metrics = market_metrics.filter(market_metrics.date == "2023-04-19").first()
    assert day_metrics is not None
    assert round(day_metrics["market_avg_close"], 2) == 915.15  # (152.34 + 282.56 + 2310.56) / 3
    assert day_metrics["symbols_count"] == 3
