# Data Stack em Kubernetes

Este projeto implementa uma data stack completa em um ambiente Kubernetes local usando kind, seguindo a arquitetura de medalhas (bronze-silver-gold) para processamento de dados.

## Visão Geral da Arquitetura

A arquitetura implementa um pipeline completo de dados com as seguintes camadas:

- **Bronze**: Ingestão de dados brutos de uma API de mercado financeiro
- **Silver**: Transformação dos dados JSON para o formato Delta Lake
- **Gold**: Agregação e sumarização dos dados para análise

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
│   ├── postgres/         # Manifestos para PostgreSQL
│   ├── airflow/          # Manifestos para Airflow
│   ├── metabase/         # Manifestos para Metabase
│   └── jupyter/          # Manifestos para Jupyter
├── apps/                 # Aplicações e código
│   ├── ingestor/         # Aplicação de ingestão (Bronze)
│   ├── transformer/      # Jobs de transformação (Silver)
│   └── aggregator/       # Jobs de agregação (Gold)
├── airflow/              # Configuração do Airflow
│   └── dags/             # DAGs do Airflow
└── docs/                 # Documentação
```

## Configuração do Cluster

### Criando o Cluster Kind

O arquivo `kubernetes/kind-config.yaml` define um cluster minimalista com um nó control-plane e um nó worker, além de mapeamentos de porta para acessar os serviços.

Para criar o cluster:

```bash
kind create cluster --config kubernetes/kind-config.yaml
```

### Verificando o Status do Cluster

Após a criação do cluster, verifique se está funcionando corretamente:

```bash
kubectl cluster-info
kubectl get nodes
```

### Configurando Namespaces

Vamos criar namespaces separados para cada componente da nossa data stack:

```bash
kubectl apply -f kubernetes/namespaces/
```

## Próximos Passos

Nos próximos documentos, detalharemos a implementação de cada componente da data stack, incluindo:

1. Configuração do MinIO para armazenamento de dados
2. Implementação da aplicação de ingestão (camada Bronze)
3. Configuração dos jobs PySpark para transformação (camada Silver)
4. Implementação dos jobs de agregação (camada Gold)
5. Configuração do Airflow para orquestração
6. Configuração do PostgreSQL, Jupyter e Metabase para consulta e visualização
