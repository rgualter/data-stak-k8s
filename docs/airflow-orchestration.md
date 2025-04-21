# Documentação da Orquestração com Apache Airflow

Este documento descreve a implementação da orquestração do pipeline de dados usando Apache Airflow, responsável por agendar e executar os jobs entre as diferentes camadas da data stack.

## Visão Geral

O Apache Airflow é usado para orquestrar o fluxo de dados entre as camadas:
1. Ingestão de dados da API de mercado financeiro (Bronze)
2. Transformação dos dados JSON para Delta Lake (Silver)
3. Agregação e criação de métricas (Gold)

## Componentes

### Apache Airflow

O Airflow é implantado no cluster Kubernetes com os seguintes componentes:
- Webserver: Interface web para gerenciamento e monitoramento dos DAGs
- Scheduler: Responsável por agendar e executar as tarefas
- PostgreSQL: Banco de dados para armazenar metadados do Airflow
- KubernetesExecutor: Executor que cria pods Kubernetes para cada tarefa

### DAGs (Directed Acyclic Graphs)

Dois DAGs foram implementados para orquestrar o pipeline:

1. **bronze_to_silver_dag.py**: Orquestra o processo de ingestão de dados e transformação para a camada Silver
   - Executa a cada 6 horas
   - Tarefas:
     - Ingestão de dados da API de mercado financeiro
     - Transformação dos dados JSON para Delta Lake

2. **silver_to_gold_dag.py**: Orquestra o processo de transformação da camada Silver para Gold
   - Executa a cada 6 horas, 30 minutos após o DAG bronze_to_silver
   - Tarefas:
     - Transformação dos dados Delta Lake para métricas agregadas

## Implementação

### Estrutura de Diretórios

```
kubernetes/airflow/
└── airflow.yaml       # Manifestos Kubernetes para o Airflow

airflow/dags/
├── bronze_to_silver_dag.py  # DAG para ingestão e transformação Bronze para Silver
└── silver_to_gold_dag.py    # DAG para transformação Silver para Gold
```

### Configuração do Airflow

O Airflow é configurado com:
- KubernetesExecutor para executar tarefas como pods Kubernetes
- Volumes persistentes para DAGs e logs
- Serviço NodePort para acesso à interface web (porta 30002)
- ServiceAccount e RBAC para permissões necessárias
- ConfigMaps e Secrets para configurações e credenciais

### Configuração dos DAGs

Os DAGs são configurados para:
- Usar KubernetesPodOperator para executar tarefas como pods Kubernetes
- Definir recursos (CPU e memória) para cada tarefa
- Configurar variáveis de ambiente e secrets para acesso ao MinIO
- Definir dependências entre tarefas para garantir a ordem correta de execução

## Implantação

### Implantando o Airflow

```bash
# Criar os namespaces
kubectl apply -f kubernetes/namespaces/namespaces.yaml

# Implantar o Airflow
kubectl apply -f kubernetes/airflow/airflow.yaml

# Copiar os DAGs para o volume persistente
kubectl cp airflow/dags/ orchestration/airflow-webserver-0:/opt/airflow/
```

### Acessando a Interface Web

A interface web do Airflow está disponível em:
```
http://localhost:30002
```

## Monitoramento

Para monitorar o status dos DAGs e tarefas:
1. Acesse a interface web do Airflow
2. Verifique o status dos DAGs na página principal
3. Clique em um DAG para ver detalhes e histórico de execução
4. Verifique os logs das tarefas para diagnóstico de problemas

## Alertas

O Airflow está configurado para enviar alertas por e-mail em caso de falha nas tarefas. Para configurar destinatários adicionais ou outros métodos de alerta, modifique os parâmetros `email_on_failure` e `email_on_retry` nos DAGs.

## Próximos Passos

Após a implementação bem-sucedida da orquestração com Airflow, os dados estarão disponíveis nas camadas Bronze, Silver e Gold para consulta e visualização através da camada de consulta (PostgreSQL, Jupyter e Metabase).
