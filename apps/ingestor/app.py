#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação de ingestão de dados financeiros (Camada Bronze)
Esta aplicação consome dados da API Yahoo Finance e armazena os dados brutos em formato JSON no MinIO.
"""

import os
import json
import time
import logging
import requests
import datetime
from minio import Minio
from minio.error import S3Error

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
MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'bronze')

# Configurações da API de mercado financeiro
SYMBOLS = os.environ.get('SYMBOLS', 'AAPL,MSFT,GOOGL,AMZN,META').split(',')
INTERVAL = os.environ.get('INTERVAL', '1d')
RANGE = os.environ.get('RANGE', '1mo')

def create_minio_client():
    """Cria e retorna um cliente MinIO."""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False  # Definido como False para ambiente de desenvolvimento
        )
        logger.info(f"Cliente MinIO criado com sucesso: {MINIO_ENDPOINT}")
        return client
    except Exception as e:
        logger.error(f"Erro ao criar cliente MinIO: {e}")
        raise

def ensure_bucket_exists(client, bucket_name):
    """Garante que o bucket especificado existe, criando-o se necessário."""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' criado com sucesso")
        else:
            logger.info(f"Bucket '{bucket_name}' já existe")
    except S3Error as e:
        logger.error(f"Erro ao verificar/criar bucket: {e}")
        raise

def fetch_stock_data(symbol):
    """
    Busca dados de ações da API Yahoo Finance.
    Em um ambiente real, usaríamos a API diretamente, mas aqui simulamos a chamada.
    """
    try:
        # Em um ambiente real, esta seria a chamada para a API Yahoo Finance
        # Aqui estamos simulando a estrutura de dados que seria retornada
        
        # Simulação de dados para demonstração
        timestamp = int(time.time())
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Estrutura básica simulando os dados que viriam da API
        data = {
            "chart": {
                "result": [{
                    "meta": {
                        "currency": "USD",
                        "symbol": symbol,
                        "exchangeName": "NMS",
                        "instrumentType": "EQUITY",
                        "firstTradeDate": 345479400,
                        "regularMarketTime": timestamp,
                        "timezone": "EST",
                        "exchangeTimezoneName": "America/New_York"
                    },
                    "timestamp": [timestamp - 86400*5, timestamp - 86400*4, timestamp - 86400*3, timestamp - 86400*2, timestamp - 86400],
                    "indicators": {
                        "quote": [{
                            "open": [150.23, 152.43, 153.12, 151.98, 154.67],
                            "high": [153.45, 154.67, 155.23, 153.45, 156.78],
                            "low": [149.56, 151.34, 152.45, 150.67, 153.45],
                            "close": [152.34, 153.45, 151.98, 154.67, 155.89],
                            "volume": [28736500, 31654300, 26897400, 29345600, 32456700]
                        }],
                        "adjclose": [{
                            "adjclose": [152.34, 153.45, 151.98, 154.67, 155.89]
                        }]
                    }
                }],
                "error": None
            }
        }
        
        logger.info(f"Dados obtidos com sucesso para o símbolo: {symbol}")
        return data
    except Exception as e:
        logger.error(f"Erro ao buscar dados para o símbolo {symbol}: {e}")
        raise

def save_to_minio(client, bucket_name, data, symbol):
    """Salva os dados JSON no MinIO."""
    try:
        # Gera um nome de arquivo baseado no símbolo e timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"stock_data/{symbol}/{timestamp}.json"
        
        # Converte os dados para string JSON
        json_data = json.dumps(data).encode('utf-8')
        
        # Salva o arquivo no MinIO
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=json_data,
            length=len(json_data),
            content_type="application/json"
        )
        
        logger.info(f"Dados salvos com sucesso no MinIO: {object_name}")
        return object_name
    except S3Error as e:
        logger.error(f"Erro ao salvar dados no MinIO: {e}")
        raise

def main():
    """Função principal que executa o processo de ingestão."""
    try:
        # Cria cliente MinIO
        minio_client = create_minio_client()
        
        # Garante que o bucket existe
        ensure_bucket_exists(minio_client, MINIO_BUCKET)
        
        # Para cada símbolo, busca os dados e salva no MinIO
        for symbol in SYMBOLS:
            logger.info(f"Processando símbolo: {symbol}")
            
            # Busca dados da API
            stock_data = fetch_stock_data(symbol)
            
            # Salva os dados no MinIO
            object_name = save_to_minio(minio_client, MINIO_BUCKET, stock_data, symbol)
            
            logger.info(f"Processamento concluído para o símbolo {symbol}: {object_name}")
        
        logger.info("Processo de ingestão concluído com sucesso")
    except Exception as e:
        logger.error(f"Erro no processo de ingestão: {e}")
        raise

if __name__ == "__main__":
    main()
