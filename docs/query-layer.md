# Documentação da Camada de Consulta

Este documento descreve a implementação da camada de consulta da nossa data stack, responsável por fornecer acesso aos dados processados para análise e visualização.

## Visão Geral

A camada de consulta é composta por três componentes principais:
1. PostgreSQL: Banco de dados relacional para armazenamento de metadados e consultas diretas
2. Jupyter Notebook: Ambiente interativo para análise exploratória de dados
3. Metabase: Ferramenta de visualização e criação de dashboards

## Componentes

### PostgreSQL

O PostgreSQL é usado como banco de dados relacional para:
- Armazenar metadados do pipeline de dados
- Permitir consultas SQL diretas aos dados processados
- Servir como fonte de dados para o Metabase

### Jupyter Notebook

O Jupyter Notebook fornece um ambiente interativo para:
- Análise exploratória dos dados das camadas Silver e Gold
- Criação de visualizações personalizadas
- Execução de análises avançadas usando Python e PySpark
- Exportação de dados para o PostgreSQL

### Metabase

O Metabase é uma ferramenta de visualização que permite:
- Criar dashboards interativos
- Compartilhar visualizações com outros usuários
- Configurar alertas baseados em métricas
- Acessar dados do PostgreSQL e diretamente do Delta Lake no MinIO

## Implementação

### Estrutura de Diretórios

```
kubernetes/
├── postgres/
│   └── postgres.yaml      # Manifestos para o PostgreSQL
├── jupyter/
│   └── jupyter.yaml       # Manifestos para o Jupyter Notebook
└── metabase/
    └── metabase.yaml      # Manifestos para o Metabase

apps/jupyter/
└── example_notebook.py    # Notebook de exemplo para análise de dados
```

### Configuração do PostgreSQL

O PostgreSQL é implantado como um StatefulSet no namespace "storage" com:
- Persistência de dados através de um PersistentVolumeClaim
- Serviço para acesso interno ao cluster
- Configuração de usuário, senha e banco de dados

### Configuração do Jupyter Notebook

O Jupyter Notebook é implantado como um Deployment no namespace "visualization" com:
- Imagem jupyter/pyspark-notebook que inclui Python, PySpark e bibliotecas de análise de dados
- Persistência de dados através de um PersistentVolumeClaim
- Serviço NodePort para acesso externo (porta 30003)
- Variáveis de ambiente para conexão com MinIO e PostgreSQL

### Configuração do Metabase

O Metabase é implantado como um Deployment no namespace "visualization" com:
- Serviço NodePort para acesso externo (porta 30004)
- Configuração para usar o PostgreSQL como banco de dados de metadados
- Probes de liveness e readiness para garantir disponibilidade

## Notebook de Exemplo

Um notebook de exemplo foi criado para demonstrar como:
1. Conectar-se ao MinIO para acessar dados das camadas Silver e Gold
2. Ler dados usando PySpark e Delta Lake
3. Criar visualizações usando Matplotlib e Seaborn
4. Exportar dados para o PostgreSQL para uso com o Metabase

## Implantação

### Implantando o PostgreSQL

```bash
kubectl apply -f kubernetes/postgres/postgres.yaml
```

### Implantando o Jupyter Notebook

```bash
kubectl apply -f kubernetes/jupyter/jupyter.yaml
```

### Implantando o Metabase

```bash
kubectl apply -f kubernetes/metabase/metabase.yaml
```

## Acesso

### Acessando o Jupyter Notebook

O Jupyter Notebook está disponível em:
```
http://localhost:30003
```

### Acessando o Metabase

O Metabase está disponível em:
```
http://localhost:30004
```

## Configuração do Metabase

Após acessar o Metabase pela primeira vez, é necessário:
1. Criar uma conta de administrador
2. Configurar a conexão com o PostgreSQL:
   - Host: postgres.storage.svc.cluster.local
   - Port: 5432
   - Database: datastack
   - Username: postgres
   - Password: postgres
3. Opcionalmente, configurar a conexão direta com o Delta Lake no MinIO (requer configuração adicional)

## Próximos Passos

Após a implementação bem-sucedida da camada de consulta, a data stack estará completa e pronta para uso. Os usuários poderão:
- Explorar os dados usando o Jupyter Notebook
- Criar dashboards no Metabase
- Executar consultas SQL no PostgreSQL
- Configurar alertas e relatórios automáticos
