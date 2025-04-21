# Documentação da Camada Bronze

Este documento descreve a implementação da camada Bronze da nossa data stack, responsável pela ingestão de dados brutos de uma API de mercado financeiro e armazenamento no MinIO.

## Visão Geral

A camada Bronze é responsável por:
1. Consumir dados da API Yahoo Finance
2. Armazenar os dados brutos em formato JSON no MinIO
3. Executar periodicamente para manter os dados atualizados

## Componentes

### Aplicação Python de Ingestão

A aplicação de ingestão é um script Python que:
- Conecta-se à API Yahoo Finance para obter dados de ações
- Processa os dados recebidos
- Armazena os dados brutos em formato JSON no MinIO

### Armazenamento MinIO

O MinIO é usado como armazenamento de objetos compatível com S3, onde os dados brutos são armazenados em formato JSON em um bucket chamado "bronze".

## Implementação

### Estrutura de Diretórios

```
apps/ingestor/
├── app.py              # Aplicação Python de ingestão
├── Dockerfile          # Dockerfile para containerização
└── requirements.txt    # Dependências Python

kubernetes/
├── minio/
│   └── minio.yaml      # Manifestos para o MinIO
└── ingestor/
    └── ingestor.yaml   # Manifestos para a aplicação de ingestão
```

### Configuração do MinIO

O MinIO é implantado como um StatefulSet no namespace "storage" com:
- Persistência de dados através de um PersistentVolumeClaim
- Interface de API acessível internamente via Service
- Console de administração exposto via NodePort (30001)
- Credenciais armazenadas em um Secret

### Configuração da Aplicação de Ingestão

A aplicação de ingestão é implantada como:
1. Um Deployment para execução contínua
2. Um CronJob para execução periódica (a cada 6 horas)

Ambos usam a mesma imagem Docker e configuração, com:
- Conexão ao MinIO usando credenciais do Secret
- Configuração de símbolos de ações, intervalo e período via variáveis de ambiente
- Recursos limitados para garantir eficiência

## Construção e Implantação

### Construindo a Imagem Docker

```bash
cd apps/ingestor
docker build -t finance-ingestor:latest .
kind load docker-image finance-ingestor:latest
```

### Implantando o MinIO

```bash
kubectl apply -f kubernetes/minio/minio.yaml
```

### Implantando a Aplicação de Ingestão

```bash
kubectl apply -f kubernetes/ingestor/ingestor.yaml
```

## Verificação

Para verificar se a camada Bronze está funcionando corretamente:

1. Verifique se o MinIO está em execução:
```bash
kubectl get pods -n storage
```

2. Verifique se a aplicação de ingestão está em execução:
```bash
kubectl get pods -n ingestion
```

3. Verifique os logs da aplicação de ingestão:
```bash
kubectl logs -n ingestion -l app=finance-ingestor
```

4. Acesse o console do MinIO (http://localhost:30001) para verificar se os dados estão sendo armazenados no bucket "bronze".

## Próximos Passos

Após a implementação bem-sucedida da camada Bronze, os dados brutos estarão disponíveis no MinIO para processamento pela camada Silver, que transformará os dados JSON em formato Delta Lake usando PySpark.
