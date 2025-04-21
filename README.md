# Data Stack em Kubernetes

Este projeto implementa uma data stack completa em um ambiente Kubernetes local usando kind, seguindo a arquitetura de medalhas (bronze-silver-gold) para processamento de dados financeiros.

## Visão Geral da Arquitetura

A arquitetura implementa um pipeline completo de dados com as seguintes camadas:

- **Bronze**: Ingestão de dados brutos de uma API de mercado financeiro (Yahoo Finance)
- **Silver**: Transformação dos dados JSON para o formato Delta Lake
- **Gold**: Agregação e sumarização dos dados para análise

![Arquitetura da Data Stack](docs/images/architecture.png)

O projeto utiliza as seguintes tecnologias:

- **Kubernetes**: Orquestração de containers (via kind)
- **MinIO**: Armazenamento de objetos compatível com S3
- **Apache Airflow**: Orquestração de workflows
- **PySpark**: Processamento de dados
- **Delta Lake**: Armazenamento de dados em formato de tabela
- **PostgreSQL**: Banco de dados relacional
- **Metabase**: Visualização de dados
- **Jupyter Notebook**: Análise exploratória de dados

## Pré-requisitos

Para executar este projeto, você precisará ter instalado em sua máquina:

- Docker
- kubectl
- kind (Kubernetes in Docker)
- Python 3.8+
- Git

## Estrutura do Projeto

```
data-stack-k8s/
├── kubernetes/           # Manifestos Kubernetes
│   ├── kind-config.yaml  # Configuração do cluster kind
│   ├── namespaces/       # Definições de namespaces
│   ├── minio/            # Manifestos para MinIO
│   ├── ingestor/         # Manifestos para o ingestor (Bronze)
│   ├── transformer/      # Manifestos para os jobs de transformação (Silver/Gold)
│   ├── postgres/         # Manifestos para PostgreSQL
│   ├── airflow/          # Manifestos para Airflow
│   ├── metabase/         # Manifestos para Metabase
│   └── jupyter/          # Manifestos para Jupyter
├── apps/                 # Aplicações e código
│   ├── ingestor/         # Aplicação de ingestão (Bronze)
│   ├── transformer/      # Jobs de transformação (Silver/Gold)
│   └── jupyter/          # Notebooks de exemplo
├── airflow/              # Configuração do Airflow
│   └── dags/             # DAGs do Airflow
└── docs/                 # Documentação
    ├── bronze-layer.md   # Documentação da camada Bronze
    ├── airflow-orchestration.md # Documentação da orquestração
    └── query-layer.md    # Documentação da camada de consulta
```

## Guia de Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/rgualter/data-stak-k8s.git
cd data-stack-k8s
```

### 2. Criar o Cluster Kubernetes

```bash
# Criar o cluster kind
kind create cluster --config kubernetes/kind-config.yaml

# Verificar se o cluster está funcionando
kubectl cluster-info
kubectl get nodes
```

### 3. Configurar Namespaces

```bash
kubectl apply -f kubernetes/namespaces/namespaces.yaml
```

### 4. Implantar o MinIO

```bash
kubectl apply -f kubernetes/minio/minio.yaml

# Verificar se o MinIO está em execução
kubectl get pods -n storage
```

O console do MinIO estará disponível em: http://localhost:30001

### 5. Construir e Implantar a Aplicação de Ingestão (Bronze)

```bash
# Construir a imagem Docker
cd apps/ingestor
docker build -t finance-ingestor:latest .
#kind load docker-image finance-ingestor:latest
kind load docker-image finance-ingestor:latest --name data-stack

# Implantar a aplicação
kubectl apply -f ../../kubernetes/ingestor/ingestor.yaml
```

### 6. Construir e Implantar os Jobs de Transformação (Silver/Gold)

```bash
# Construir a imagem Docker
cd ../transformer
docker build -t pyspark-transformer:latest .
#kind load docker-image pyspark-transformer:latest
kind load docker-image pyspark-transformer:latest --name data-stack

# Implantar os jobs
kubectl apply -f ../../kubernetes/transformer/transformer-jobs.yaml
```

### 7. Implantar o PostgreSQL

```bash
kubectl apply -f kubernetes/postgres/postgres.yaml
```

### 8. Implantar o Airflow

```bash
# Implantar o Airflow
kubectl apply -f kubernetes/airflow/airflow.yaml

# Copiar os DAGs para o volume persistente
kubectl cp airflow/dags/ orchestration/airflow-webserver-0:/opt/airflow/
```

O Airflow estará disponível em: http://localhost:30002

### 9. Implantar o Jupyter Notebook e Metabase

```bash
kubectl apply -f kubernetes/jupyter/jupyter.yaml
kubectl apply -f kubernetes/metabase/metabase.yaml
```

O Jupyter Notebook estará disponível em: http://localhost:30003
O Metabase estará disponível em: http://localhost:30004

## Uso da Data Stack

### Ingestão de Dados (Bronze)

A ingestão de dados é realizada pela aplicação `finance-ingestor`, que consome dados da API Yahoo Finance e os armazena no MinIO no bucket `bronze`. A ingestão pode ser executada manualmente ou agendada pelo Airflow.

### Transformação de Dados (Silver/Gold)

A transformação de dados é realizada pelos jobs PySpark:
- `bronze_to_silver.py`: Transforma os dados JSON em formato Delta Lake
- `silver_to_gold.py`: Cria métricas agregadas a partir dos dados Silver

### Orquestração com Airflow

O Airflow orquestra o pipeline de dados com dois DAGs:
- `bronze_to_silver_dag.py`: Orquestra a ingestão e transformação Bronze para Silver
- `silver_to_gold_dag.py`: Orquestra a transformação Silver para Gold

### Análise de Dados

Os dados podem ser analisados usando:
- **Jupyter Notebook**: Para análise exploratória e visualizações personalizadas
- **Metabase**: Para criação de dashboards e relatórios
- **PostgreSQL**: Para consultas SQL diretas

## Documentação Detalhada

Para informações mais detalhadas sobre cada componente da data stack, consulte:

- [Documentação da Camada Bronze](docs/bronze-layer.md)
- [Documentação da Orquestração com Airflow](docs/airflow-orchestration.md)
- [Documentação da Camada de Consulta](docs/query-layer.md)

## Destruindo o Cluster

Para destruir o cluster e limpar todos os recursos:

```bash
kind delete cluster --name data-stack
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests para melhorar este projeto.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
