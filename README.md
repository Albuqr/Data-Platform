[🇬🇧 English](#factory-data-platform) · [🇧🇷 Português](#factory-data-platform-pt)

---

# Factory Data Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)
![Docker](https://img.shields.io/badge/Docker-containerised-2496ED)
![BigQuery](https://img.shields.io/badge/BigQuery-warehouse-4285F4)
![Kafka](https://img.shields.io/badge/Kafka-KRaft-231F20)
![Redis](https://img.shields.io/badge/Redis-baseline-DC382D)
[![Live](https://img.shields.io/badge/live-data--platform.albuqr.com-brightgreen)](https://data-platform.albuqr.com)

Portfolio project. Uses anonymized planning and maintenance data from a Brazilian food manufacturer. It covers 28 documented machines across two product lines and integrates a BigQuery data lakehouse and a real-time Kafka transaction monitor behind a single FastAPI abstraction layer, with a Flask dashboard for operational visibility.

## Architecture

The system is split across three repositories with a strict dependency hierarchy. The [Factory Lakehouse](https://github.com/Albuqr/Factory_Lakehouse) ingests and models operational data — equipment maintenance schedules and budget allocations — and exposes a lakehouse API. The [Transaction Monitor](https://github.com/Albuqr/Transaction_Monitor) consumes a Kafka topic of financial transactions, computes per-cost-center baselines in Redis, and exposes a monitor API. Both upstream services are consumed exclusively by this repository's Platform API, a FastAPI application that acts as the single integration point for the presentation layer.

The Flask frontend calls only the Platform API — never BigQuery or Redis directly. This dependency inversion means the dashboard has no knowledge of the underlying storage or streaming technology. If the lakehouse migrates from BigQuery to a different warehouse, or if the baseline store moves from Redis to another system, only the Platform API adapts; the dashboard and its templates remain unchanged.

The dashboard has Overview, Equipment, Budget, Alerts and Case Study pages, available in English and Portuguese. Amounts show in BRL or as approximate USD, converted at a disclosed daily rate. Alerts are stored demo data, and reviews stay in the visitor's browser. Domain terms are defined in [GLOSSARY.md](GLOSSARY.md).

## Live URLs

| Service | URL |
|---------|-----|
| Dashboard | https://data-platform.albuqr.com |
| Platform API | https://platform-api.albuqr.com |
| Lakehouse API | https://lakehouse-api.albuqr.com |
| Factory Lakehouse | https://lakehouse.albuqr.com |
| Transaction Monitor | https://transaction-monitor.albuqr.com |

## Tech Stack

| Technology | Role |
|------------|------|
| Flask | Frontend dashboard |
| FastAPI | Platform API and lakehouse middleware |
| httpx | Service client HTTP calls |
| BigQuery | Analytical warehouse |
| dbt | Data transformation |
| Airflow | Pipeline scheduling |
| Kafka (KRaft) | Transaction event streaming |
| Redis | Real-time baseline store |
| SQLite | Alert persistence |
| Docker | Containerisation |
| Easypanel | VPS deployment |
| Frankfurter | Daily USD to BRL reference rate |

## Key Design Decisions

**Dependency inversion** — The dashboard never calls BigQuery or Redis directly. All data access goes through the Platform API. Underlying services can be replaced without touching the presentation layer, and the dashboard's contract is a single, stable HTTP interface.

**Rule-based anomaly detection** — Zero labeled anomaly history exists in the source data, which makes a supervised ML approach inappropriate: there is nothing to train on and no way to validate recall. A 20% deviation threshold from the cost center's running mean is explicit, auditable, and honest about what the data actually supports.

**Cost center granularity** — Source transactions contained no supplier descriptions or line-item identifiers. Operating at cost center level is the finest granularity the data actually supports. This is documented explicitly rather than compensated for with fabricated dimensions.

**Redis over BigQuery for baseline** — The detection pipeline targets a sub-30-second SLA from transaction arrival to alert. A BigQuery query job incurs several seconds of cold-start latency per invocation, which would make that SLA unachievable. Redis delivers the per-cost-center mean in under a millisecond.

**Maintenance status measured from the latest record** — The source data is static, so measuring from today would eventually mark every machine overdue. Status is calculated from the date of the most recent maintenance record, and that date is shown on screen.

**Alert reviews stay in the browser** — On a public demo, shared reviews would soon leave later visitors nothing to try. Reviews are saved only in each visitor's browser, and the Platform API's write route requires an API key.

## Data & Known Gaps

| Source | Status | Notes |
|--------|--------|-------|
| Equipment | Available | 28 named and documented machines out of a larger fleet — remaining machines lack identification records |
| Budget | Available | 8 cost centers, monthly allocations from a DRE spreadsheet |
| Actuals | Unavailable | Source transactions had no cost center mapping — variance data is null, documented not fabricated |
| Alerts | Available (demo) | Stored alerts from the monitor demo, rule-based detection at 20% deviation threshold; no live pipeline |

## Related Repositories

- [Factory Lakehouse](https://github.com/Albuqr/Factory_Lakehouse) — BigQuery ingestion, dbt models, lakehouse API
- [Transaction Monitor](https://github.com/Albuqr/Transaction_Monitor) — Kafka consumer, Redis baselines, alert API
- [Data Platform](https://github.com/Albuqr/Data-Platform) — Platform API and Flask dashboard (this repository)

## Running Locally

**Prerequisites:** Python 3.11, pip, Docker (optional).

```bash
git clone https://github.com/Albuqr/Data-Platform.git
cd Data-Platform
```

Create a `.env` file at the repository root:

```
PLATFORM_API_URL=http://localhost:8000
```

To point at the live API instead, set `PLATFORM_API_URL=https://platform-api.albuqr.com` and skip the middleware step.

**Middleware (Platform API):**

Set these in the `.env` file. `RESOLUTIONS_API_KEY` is optional: without it, `POST /api/post_resolutions` rejects every request. Key holders send it in the `X-API-Key` header.

```
LAKEHOUSE_API_URL=<lakehouse API URL>
MONITOR_API_URL=<monitor API URL>
RESOLUTIONS_API_KEY=<optional secret>
```

```bash
cd middleware
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
pip install -r requirements.txt
flask run
```

The dashboard will be available at `http://localhost:5000`.

---

[🇬🇧 English](#factory-data-platform) · [🇧🇷 Português](#factory-data-platform-pt)

---

<a id="factory-data-platform-pt"></a>

# Factory Data Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)
![Docker](https://img.shields.io/badge/Docker-containerised-2496ED)
![BigQuery](https://img.shields.io/badge/BigQuery-warehouse-4285F4)
![Kafka](https://img.shields.io/badge/Kafka-KRaft-231F20)
![Redis](https://img.shields.io/badge/Redis-baseline-DC382D)
[![Live](https://img.shields.io/badge/live-data--platform.albuqr.com-brightgreen)](https://data-platform.albuqr.com)

Projeto de portfólio. Usa dados anonimizados de planejamento e manutenção de uma indústria alimentícia brasileira. Abrange 28 máquinas documentadas em duas linhas de produção e integra um data lakehouse no BigQuery e um monitor de transações em tempo real via Kafka por trás de uma camada de abstração FastAPI, com um dashboard Flask para visibilidade operacional.

## Arquitetura

O sistema é dividido em três repositórios com uma hierarquia de dependências estrita. O [Factory Lakehouse](https://github.com/Albuqr/Factory_Lakehouse) ingere e modela dados operacionais — calendários de manutenção de equipamentos e alocações orçamentárias — e expõe uma API de lakehouse. O [Transaction Monitor](https://github.com/Albuqr/Transaction_Monitor) consome um tópico Kafka de transações financeiras, calcula baselines por centro de custo no Redis e expõe uma API de monitoramento. Ambos os serviços upstream são consumidos exclusivamente pela API de Plataforma deste repositório, uma aplicação FastAPI que atua como único ponto de integração para a camada de apresentação.

O frontend Flask chama apenas a API de Plataforma — nunca o BigQuery ou o Redis diretamente. Essa inversão de dependência significa que o dashboard não tem conhecimento da tecnologia de armazenamento ou streaming subjacente. Se o lakehouse migrar do BigQuery para outro warehouse, ou se o armazenamento de baselines mudar do Redis para outro sistema, apenas a API de Plataforma se adapta; o dashboard e seus templates permanecem inalterados.

O dashboard tem as páginas Visão geral, Equipamentos, Orçamento, Alertas e Estudo de caso, em inglês e português. Os valores aparecem em BRL ou em USD aproximado, convertidos a uma taxa diária informada na tela. Os Alertas são dados de demonstração armazenados, e as revisões ficam no navegador do visitante. Os termos do domínio estão definidos em [GLOSSARY.md](GLOSSARY.md).

## URLs em Produção

| Serviço | URL |
|---------|-----|
| Dashboard | https://data-platform.albuqr.com |
| API de Plataforma | https://platform-api.albuqr.com |
| API de Lakehouse | https://lakehouse-api.albuqr.com |
| Factory Lakehouse | https://lakehouse.albuqr.com |
| Transaction Monitor | https://transaction-monitor.albuqr.com |

## Stack Tecnológica

| Tecnologia | Função |
|------------|--------|
| Flask | Dashboard frontend |
| FastAPI | API de plataforma e middleware de lakehouse |
| httpx | Chamadas HTTP dos clientes de serviço |
| BigQuery | Warehouse analítico |
| dbt | Transformação de dados |
| Airflow | Agendamento de pipelines |
| Kafka (KRaft) | Streaming de eventos de transações |
| Redis | Armazenamento de baselines em tempo real |
| SQLite | Persistência de alertas |
| Docker | Containerização |
| Easypanel | Deploy em VPS |
| Frankfurter | Taxa de referência diária de USD para BRL |

## Decisões de Projeto

**Inversão de dependência** — O dashboard nunca chama o BigQuery ou o Redis diretamente. Todo acesso a dados passa pela API de Plataforma. Os serviços subjacentes podem ser substituídos sem modificar a camada de apresentação, e o contrato do dashboard é uma única interface HTTP estável.

**Detecção de anomalias baseada em regras** — Não existe histórico de anomalias rotuladas nos dados de origem, o que torna uma abordagem de ML supervisionado inadequada: não há nada para treinar e nenhuma forma de validar a cobertura. Um limiar de 20% de desvio em relação à média acumulada do centro de custo é explícito, auditável e honesto sobre o que os dados efetivamente suportam.

**Granularidade por centro de custo** — As transações de origem não continham descrições de fornecedores ou identificadores de linha de item. Operar no nível de centro de custo é a granularidade mais fina que os dados realmente suportam. Isso está documentado explicitamente em vez de ser compensado com dimensões fabricadas.

**Redis em vez de BigQuery para baselines** — O pipeline de detecção tem um SLA de menos de 30 segundos desde a chegada da transação até o alerta. Um job de consulta no BigQuery incorre em vários segundos de latência de cold start por invocação, o que tornaria esse SLA inatingível. O Redis entrega a média por centro de custo em menos de um milissegundo.

**Status de manutenção medido a partir do registro mais recente** — Os dados de origem são estáticos, então medir a partir de hoje acabaria marcando todas as máquinas como atrasadas. O status é calculado a partir da data do registro de manutenção mais recente, e essa data aparece na tela.

**Revisões de Alertas ficam no navegador** — Em uma demonstração pública, revisões compartilhadas logo deixariam os próximos visitantes sem nada para testar. As revisões ficam salvas apenas no navegador de cada visitante, e a rota de escrita da API de Plataforma exige uma chave de API.

## Dados e Limitações Conhecidas

| Fonte | Status | Observações |
|-------|--------|-------------|
| Equipamentos | Disponível | 28 máquinas nomeadas e documentadas de uma frota maior — as máquinas restantes não possuem registros de identificação |
| Orçamento | Disponível | 8 centros de custo, alocações mensais extraídas do DRE |
| Realizado | Indisponível | As transações de origem não tinham mapeamento de centro de custo — dados de variação são nulos, documentados e não fabricados |
| Alertas | Disponível (demonstração) | Alertas armazenados da demonstração do monitor, detecção baseada em regras com limiar de 20% de desvio; sem pipeline ao vivo |

## Repositórios Relacionados

- [Factory Lakehouse](https://github.com/Albuqr/Factory_Lakehouse) — Ingestão no BigQuery, modelos dbt, API de lakehouse
- [Transaction Monitor](https://github.com/Albuqr/Transaction_Monitor) — Consumidor Kafka, baselines no Redis, API de alertas
- [Data Platform](https://github.com/Albuqr/Data-Platform) — API de plataforma e dashboard Flask (este repositório)

## Executando Localmente

**Pré-requisitos:** Python 3.11, pip, Docker (opcional).

```bash
git clone https://github.com/Albuqr/Data-Platform.git
cd Data-Platform
```

Crie um arquivo `.env` na raiz do repositório:

```
PLATFORM_API_URL=http://localhost:8000
```

Para apontar para a API em produção, defina `PLATFORM_API_URL=https://platform-api.albuqr.com` e pule a etapa do middleware.

**Middleware (API de Plataforma):**

Defina estas variáveis no arquivo `.env`. `RESOLUTIONS_API_KEY` é opcional: sem ela, `POST /api/post_resolutions` rejeita todas as requisições. Quem tem a chave a envia no cabeçalho `X-API-Key`.

```
LAKEHOUSE_API_URL=<URL da API de lakehouse>
MONITOR_API_URL=<URL da API de monitoramento>
RESOLUTIONS_API_KEY=<segredo opcional>
```

```bash
cd middleware
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
pip install -r requirements.txt
flask run
```

O dashboard estará disponível em `http://localhost:5000`.
