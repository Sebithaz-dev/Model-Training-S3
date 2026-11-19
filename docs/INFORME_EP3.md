# Evaluación Parcial N°3 — Observabilidad y entornos reales en DevOps

**Asignatura:** DOY0101 — Ingeniería DevOps  
**Carrera:** [COMPLETAR]  
**Sección:** [COMPLETAR]  
**Docente:** [COMPLETAR]  
**Integrantes:**

- [Nombre completo 1] — [correo institucional]
- [Nombre completo 2] — [correo institucional]

**Fecha de entrega:** [dd/mm/aaaa]  
**Repositorios:**

- [Model-Training-S3](https://github.com/Sebithaz-dev/Model-Training-S3)
- [CitiBike-Infra](https://github.com/Sebithaz-dev/CitiBike-Infra)
- [Flask-Dashboard-S3](https://github.com/Sebithaz-dev/Flask-Dashboard-S3)

**Entorno de demostración:** AWS Learner Lab, cuenta `690247773624`, región `us-east-1`.
Sesión documentada: **2026-11-19**. La URL del balanceador cambia si se recrea la
infraestructura; se obtiene con:

```bash
terraform -chdir=terraform output -raw dashboard_url
```

---

> **Cómo usar este esqueleto.**
>
> Este documento ya contiene la estructura, las tablas de evidencia y los datos
> técnicos verificados. Las secciones marcadas `[COMPLETAR]` deben redactarse con
> las palabras del equipo. La **sección 10 (conclusiones y reflexiones)** está
> deliberadamente vacía: la pauta prohíbe usar IA para redactarla.
>
> Antes de entregar: reemplazar todos los `[COMPLETAR]`, agregar las capturas de
> `docs/img/`, revisar que los enlaces funcionen y exportar a PDF si el curso lo
> exige.

---

## Declaración de uso de inteligencia artificial

> La pauta permite usar IA como apoyo para redacción, referencias o diagramas,
> pero exige declarar qué herramientas se usaron y cómo. También prohíbe su uso
> en conclusiones, justificaciones técnicas y reflexiones individuales.

| Herramienta / servicio | Para qué se usó | Archivos o secciones donde se aplicó | Cómo se validó |
|---|---|---|---|
| [COMPLETAR: nombre de la herramienta] | [COMPLETAR: redacción, revisión de comandos, generación de diagramas, etc.] | [COMPLETAR] | [COMPLETAR: ejecución real, revisión del equipo, contraste con la documentación] |
| [COMPLETAR] | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] |

**Ejemplo de declaración (ajustar o eliminar si no aplica):**

> Se utilizó un asistente de IA como apoyo para ordenar la documentación técnica,
> revisar comandos de AWS/GitHub Actions y proponer la estructura de este informe.
> Todas las decisiones de arquitectura, la ejecución de los comandos y la
> verificación de los resultados fueron realizadas por el equipo. Las
> conclusiones y reflexiones individuales de la sección 10 fueron escritas sin
> asistencia de IA.

---

## Resumen ejecutivo

[COMPLETAR: 150–250 palabras. Explicar qué se construyó, sobre qué infraestructura,
qué indicadores se cumplieron y cuál es el resultado principal. No adelantar las
reflexiones personales.]

### Resultados principales de la sesión verificada

| Resultado | Valor observado | Evidencia |
|---|---|---|
| Servicios ECS en ejecución | 5/5 en `1/1` y `COMPLETED` | [`ecs-services.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ecs-services.txt) |
| Target groups del ALB | 2/2 `healthy` | [`target-group-dashboard.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/target-group-dashboard.txt), [`target-group-grafana.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/target-group-grafana.txt) |
| Endpoints del dashboard | `/health`, `/`, `/metrics` → 200 | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) |
| Targets de Prometheus | 5/5 con `up=1` | [`prometheus-up.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/prometheus-up.txt) |
| Alarmas de CloudWatch | 7/7 en `OK` | [`cloudwatch-alarms.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-alarms.txt) |
| Cobertura de tests de Flask | 83,61 % (29 tests) | [Run 44588927968](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/runs/44588927968) |
| Duración de un despliegue | 127 s | [`cloudwatch-cicd-values.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-cicd-values.txt) |
| Auditoría de cumplimiento | 47 controles, 0 fallas, 0 no evaluables | [`compliance.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.txt) |
| Gate bloqueante demostrado | PR #24 en `BLOCKED` | [`ie6-gate-bloqueante.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ie6-gate-bloqueante.txt) |
| Modelo en producción | ROC-AUC 0,6505; F1 0,4650; test 94.686 | [`README.md` — últimas métricas](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/README.md#últimas-métricas-test-temporal) |

---

## Índice

| Sección | Contenido |
|---|---|
| 1 | Contexto y alcance |
| 2 | Arquitectura de la solución |
| 3 | Implementación de los indicadores IE1–IE6 |
| 4 | Matriz consolidada IE → evidencia |
| 5 | Integración en el pipeline CI/CD (IE4) |
| 6 | Cumplimiento y auditoría (IE5) |
| 7 | Demostración del gate bloqueante (IE6) |
| 8 | Resultados y métricas |
| 9 | Limitaciones y trabajo futuro |
| 10 | Conclusiones y reflexiones individuales |
| A–D | Anexos: evidencia, comandos, URLs y checklist |

---

## 1. Contexto y alcance

### 1.1 El sistema

El proyecto Citi Bike NYC clasifica la duración de los viajes en **corto**
(≤ 15 min) o **largo** (> 15 min). El pipeline tiene tres etapas:

1. **Extracción:** datos crudos → Parquet curado en S3.
2. **Entrenamiento:** validación, feature engineering, entrenamiento y
   publicación de artefactos en S3 (`Model-Training-S3`).
3. **Dashboard:** microservicio Flask que consume los artefactos desde S3 y
   expone predicciones, métricas y `/health` (`Flask-Dashboard-S3`).

La EP3 extiende ese pipeline con **observabilidad**, **despliegue en un entorno
orquestado en la nube**, **dashboards**, **políticas de cumplimiento** y
**gates que detienen el pipeline**.

### 1.2 Repositorios y responsabilidades

| Repositorio | Rol en la EP3 | Artefactos principales |
|---|---|---|
| [`Model-Training-S3`](https://github.com/Sebithaz-dev/Model-Training-S3) | Entrenamiento, quality gate del modelo y publicación de métricas | `ml/train.py`, `ml/quality_gate.py`, `config/quality_gate.yaml`, `ml/metrics_export.py`, workflows `ci.yml`, `train.yml`, `security.yml` |
| [`CitiBike-Infra`](https://github.com/Sebithaz-dev/CitiBike-Infra) | Infraestructura como código, observabilidad, despliegue y auditoría | `terraform/`, `docker/`, `scripts/`, `docs/`, evidencia de la sesión |
| [`Flask-Dashboard-S3`](https://github.com/Sebithaz-dev/Flask-Dashboard-S3) | Microservicio desplegado, métricas de aplicación y CI/CD | `app.py`, `/metrics`, `/health`, `.github/workflows/ci-cd.yml`, `k8s/` (EP2) |

### 1.3 Alcance de esta entrega

| Incluido | Fuera de alcance (documentado) |
|---|---|
| Observabilidad con Prometheus, Grafana y CloudWatch | Stack ELK/Loki o SIEM corporativo |
| ECS on EC2 en AWS real, con ALB y 5 servicios | EKS/Kubernetes real en AWS (se usó `kind` en EP2) |
| Dashboard unificado de 4 filas | Alta disponibilidad multi-AZ y autoscaling |
| Branch protection, SonarCloud, Snyk y auditoría propia | Cumplimiento formal ISO 27001 certificado |
| Gates de calidad, cobertura, seguridad y modelo | Pruebas de carga y chaos engineering |
| Evidencia reproducible y runbook operativo | TLS/dominio propio y WAF |

> **Nota sobre IE2:** la pauta pide “entornos orquestados en la nube”. Se eligió
> **ECS on EC2** en lugar de EKS por las restricciones del Learner Lab. La
> decisión y sus consecuencias están en
> [`CitiBike-Infra/docs/ARCHITECTURE.md` §Decisión 1](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/ARCHITECTURE.md).
> `[COMPLETAR: explicar con palabras propias por qué se eligió ECS y qué se gana/pierde.]`

---

## 2. Arquitectura de la solución

### 2.1 Vista general

```text
                              ┌──────────────────────── GitHub ────────────────────────┐
                              │  Model-Training-S3    Flask-Dashboard-S3   CitiBike-Infra│
                              │  ci / train / security  ci-cd / security    infra-ci     │
                              └───────────────┬──────────────────────────────────────────┘
                                              │ GHCR (imágenes) · S3 (datos, modelo)
                                              ▼
 Internet ──► ALB (citibike-dev-alb) ──┬── :80   ──► ECS dashboard (Flask :5000)
                                       └── :3000 ──► ECS grafana   (:3000)
                                                        │
      ┌──────────────────────── EC2 t3.large · ECS cluster ─┼──────────────────────────┐
      │  prometheus :9090 ◄── scrape ── dashboard, blackbox, self                    │
      │  alertmanager :9093 ◄── alertas ── prometheus                                 │
      │  blackbox :9115 ── probes ──► /health (ECS, Grafana, Render)                  │
      │  CloudWatch agent ──► CPU, memoria y disco de la instancia                    │
      └───────────────────────────────┬───────────────────────────────────────────────┘
                                      │ awslogs
                                      ▼
                   CloudWatch Logs (5 grupos) · CloudWatch Metrics · 7 alarmas
                                      ▲
                                      │ datasource CloudWatch + Prometheus
                                 Grafana (4 filas)
```

### 2.2 Componentes

| Componente | Función | Configuración |
|---|---|---|
| **ALB** | Punto de entrada HTTP | Puertos 80 (dashboard) y 3000 (Grafana), health checks |
| **ECS on EC2** | Orquestador de los 5 servicios | 1 instancia `t3.large` AL2023 ECS-optimized, `network_mode=host` |
| **Dashboard Flask** | Microservicio de predicción y métricas | `/health`, `/`, `/predict`, `/metrics`; logs JSON con `request_id` |
| **Prometheus** | Métricas de aplicación y disponibilidad | Scrape cada 15 s a dashboard, blackbox y sí mismo |
| **Blackbox Exporter** | Probes HTTP | Dashboard ECS, Grafana y Render |
| **Alertmanager** | Recepción de alertas de Prometheus | Sin correo en la demo; visible en Prometheus/Grafana |
| **Grafana** | Dashboard unificado | Datasources CloudWatch y Prometheus; dashboard `citibike-ep3` |
| **CloudWatch Logs** | Logs de los 5 contenedores | 5 grupos `/ecs/citibike-dev/*`, retención 7 días |
| **CloudWatch Metrics** | CPU/memoria de instancia y contenedores; métricas CI/CD y modelo | `CWAgent`, `ECS/ContainerInsights`, `CitiBike/CI`, `CitiBike/Model` |
| **CloudWatch Alarms** | 7 alarmas de disponibilidad, errores, latencia, recursos y gates | `terraform/monitoring.tf`; SNS opcional con `var.alarm_email` |
| **S3** | Datos curados y artefactos del modelo | Bucket `citibike-datalake-seb-690247773624` |

### 2.3 Flujo CI/CD

```text
 Pull request
      │
      ▼
 ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
 │ Lint + tests │──►│ Snyk + Sonar │──►│ Build + smoke    │──►│ GHCR         │
 │ cobertura    │   │ quality gate │   │ test de imagen   │   │ image:sha    │
 └──────┬───────┘   └──────┬───────┘   └────────┬─────────┘   └──────┬───────┘
        │                  │                    │                    │
        └──────────────────┴────────────────────┴────────────────────┘
                                      │
                              ¿todos los checks OK?
                                 │            │
                               sí │            │ no
                                 ▼            ▼
                        merge a main     PR BLOCKED
                                 │
                                 ▼
                    deploy.sh · ECS rolling update
                                 │
                                 ▼
                    verify.sh · Prometheus · Grafana · CloudWatch
```

### 2.4 Decisión de orquestación: ECS on EC2

| Alternativa | Ventaja | Restricción en el Learner Lab |
|---|---|---|
| **EKS** | Kubernetes real y portabilidad | Requiere addons, nodegroups, IRSA/roles y Cloud Map; creación de IAM bloqueada |
| **ECS Fargate** | Sin administrar instancias | Descubrimiento por ALB/Cloud Map, sin métricas de host, mayor costo del stack |
| **ECS on EC2 (elegida)** | Usa `LabInstanceProfile`, `LabRole`, puertos fijos y métricas de host | Instancia única; no hay alta disponibilidad real |

Consecuencias documentadas:

- Se cumple el concepto de “entorno orquestado en la nube” con ECS.
- Los manifiestos de Kubernetes de la EP2 quedan como evidencia histórica en
  `Flask-Dashboard-S3/k8s/`.
- El stack de monitoreo usa `network_mode=host`; los puertos 9090/9093/9115 no
  se exponen por el ALB.
- La instancia es un único punto de falla, aceptado para una demo académica y
  cubierto por el runbook.

> `[COMPLETAR: redactar la justificación final de la decisión con las palabras del equipo.]`

### 2.5 Configuración como código y trazabilidad

| Elemento | Dónde vive | Cómo se versiona |
|---|---|---|
| Infraestructura AWS | `CitiBike-Infra/terraform/*.tf` | Terraform + state local (ignorado por git) |
| Configuración de Prometheus | `docker/prometheus/` | Imagen construida en `monitoring-images.yml` |
| Dashboard de Grafana | `docker/grafana/dashboards/citibike-ep3.json` | Imagen + provisioning |
| Alarmas | `terraform/monitoring.tf` | Terraform |
| Pipelines | `.github/workflows/*.yml` | Git + checks requeridos |
| Políticas de cumplimiento | `scripts/audit_compliance.py`, `docs/COMPLIANCE.md` | Git + check `Auditoria de cumplimiento` |
| Evidencia | `docs/evidence/<fecha>/` | Git |

---

## 3. Implementación de los indicadores IE1–IE6

### 3.1 IE1 — Monitoreo, logging y disponibilidad (20 %)

**Qué pide la rúbrica:** configurar Prometheus, CloudWatch o similar para
visualizar logs, métricas de uso, errores y disponibilidad de los
microservicios.

**Implementación:**

- **Prometheus** scrapea el dashboard (`:5000/metrics`), blackbox (`:9115`) y a
  sí mismo cada 15 s.
- **Blackbox Exporter** mide disponibilidad de:
  - `http://localhost:5000/health` (dashboard ECS),
  - `http://localhost:3000/api/health` (Grafana),
  - `https://flask-dashboard-s3.onrender.com/health` (Render).
- **Grafana** unifica Prometheus y CloudWatch en el dashboard `citibike-ep3`.
- **CloudWatch Logs** recibe los 5 contenedores vía driver `awslogs`, con
  retención de 7 días.
- **CloudWatch Agent** publica `mem_used_percent` y `disk_used_percent` de la
  instancia; `ECS/ContainerInsights` publica CPU/memoria por servicio.
- **7 alarmas de CloudWatch**: disponibilidad, 5xx, latencia p95, CPU, memoria,
  gate de CI y gate del modelo.
- **6 reglas de Prometheus**: `DashboardDown`, `PublicEndpointDown`,
  `GrafanaDown`, `HighErrorRate`, `HighLatencyP95`, `UnhandledErrors`.

**Evidencia:**

| # | Evidencia | Qué demuestra | Dónde verla | Resultado |
|---|---|---|---|---|
| 1 | Verificación end-to-end | 5 servicios ECS `1/1`, 2 targets `healthy`, 3 endpoints 200, Grafana OK | [`verify.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/verify.txt) | `Todo OK` |
| 2 | Targets de Prometheus | 5 series con `up=1` | [`prometheus-up.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/prometheus-up.txt) | 5/5 |
| 3 | Reglas de alerta | 6 reglas cargadas y en estado `inactive` | [`prometheus-rules.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/prometheus-rules.txt) | 0 alertas activas |
| 4 | Alarmas de CloudWatch | 7 alarmas en `OK` | [`cloudwatch-alarms.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-alarms.txt) | 7/7 |
| 5 | Códigos HTTP | `/health`, `/`, `/metrics`, Grafana | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) | 200 |
| 6 | Métricas disponibles | Namespaces `CWAgent`, `ECS/ContainerInsights`, `CitiBike/CI`, `CitiBike/Model` | [`cloudwatch-metrics.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-metrics.txt) | Métricas publicando |
| 7 | Dashboard de Grafana | 4 filas y 15 paneles | [`citibike-ep3.json`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docker/grafana/dashboards/citibike-ep3.json) | 4 filas |
| 8 | Grupos de logs | 5 grupos `/ecs/citibike-dev/*` con retención de 7 días | [`terraform/outputs.tf`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/terraform/outputs.tf) / [`ecs.tf`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/terraform/ecs.tf) | 5 grupos |
| 9 | Falla controlada | Procedimiento para tumbar el dashboard y ver la alarma | [`docs/TESTING.md` §5](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/TESTING.md) | Reproducible |

**Capturas pendientes:**

- `![Fila 1: disponibilidad](img/01-grafana-fila1.png)`
- `![Fila 2: errores y latencia](img/02-grafana-fila2.png)`
- `![Alarmas de CloudWatch](img/05-cloudwatch-alarms.png)`
- `![Logs en CloudWatch](img/06-cloudwatch-logs.png)`

**Limitaciones a mencionar:** retención de Prometheus de 6 h (disco efímero);
Alertmanager no envía correo en la demo; logs se consultan en CloudWatch, no en
Grafana.

---

### 3.2 IE2 — Despliegue en entorno orquestado en la nube (20 %)

**Qué pide la rúbrica:** desplegar microservicios en un entorno orquestado en la
nube, integrando configuraciones de monitoreo, trazabilidad y observabilidad de
forma automatizada.

**Implementación:**

- **Terraform** crea VPC/red, ALB, target groups, instancia ECS-optimized,
  cluster, task definitions y 5 servicios.
- **ECS on EC2** con `LabInstanceProfile` y `LabRole`; no se crean roles IAM.
- **5 servicios**: `dashboard`, `prometheus`, `grafana`, `alertmanager`,
  `blackbox`, todos `1/1`.
- **`network_mode=host`** para el stack de monitoreo, con puertos fijos.
- **`deployment_minimum_healthy_percent=0` / `maximum=100`** para permitir
  rolling update en una sola instancia.
- **`ECS_IMAGE_PULL_BEHAVIOR=always`** para no reutilizar imágenes `:latest`
  cacheadas.
- **CloudWatch Agent** y **Container Insights** habilitados desde el
  `user_data`.
- **`deploy.sh`** mide el despliegue y publica `DeploymentDurationSeconds`.
- **`verify.sh`** valida el estado end-to-end y devuelve exit code distinto de
  cero si algo falla.

**Evidencia:**

| # | Evidencia | Qué demuestra | Dónde verla | Resultado |
|---|---|---|---|---|
| 1 | Servicios ECS | 5 servicios `ACTIVE`, `1/1`, rollout `COMPLETED` | [`ecs-services.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ecs-services.txt) | 5/5 |
| 2 | Target groups | Targets del ALB en `healthy` | [`target-group-dashboard.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/target-group-dashboard.txt), [`target-group-grafana.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/target-group-grafana.txt) | 2/2 |
| 3 | Endpoints | `/health`, `/`, `/metrics` responden 200 | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) | 200 |
| 4 | Outputs de Terraform | ALB, cluster, instancia, log groups, URL interna de Prometheus | [`terraform-outputs.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/terraform-outputs.txt) | Recursos creados |
| 5 | Verificación | Servicios, targets, endpoints y Grafana | [`verify.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/verify.txt) | `Todo OK` |
| 6 | Duración de despliegue | `DeploymentDurationSeconds` | [`cloudwatch-cicd-values.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-cicd-values.txt) | 127 s |
| 7 | Infraestructura como código | Recursos y configuraciones | [`terraform/`](https://github.com/Sebithaz-dev/CitiBike-Infra/tree/main/terraform) | `terraform plan` sin diferencias |
| 8 | Decisión ECS vs EKS | Restricciones y consecuencias | [`docs/ARCHITECTURE.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/ARCHITECTURE.md) | Documentada |

**Capturas pendientes:**

- `![Salida de verify.sh](img/11-verify.png)`
- `![Servicios ECS en la consola](img/12-ecs-servicios.png)`
- `![Target groups healthy](img/13-target-groups.png)`

**Pendiente de redacción:** explicar en el informe la desviación ECS vs
Kubernetes y por qué sigue cumpliendo el concepto de “entorno orquestado”.

---

### 3.3 IE3 — Dashboard con métricas clave integradas al CI/CD (10 %)

**Qué pide la rúbrica:** crear dashboards con tiempo de despliegue, cobertura de
pruebas, uso de CPU/memoria y errores registrados, integrados en el proceso
CI/CD.

**Dashboard `citibike-ep3` (4 filas):**

| Fila | Paneles | Fuente | Qué muestra |
|---|---|---|---|
| **1. Disponibilidad** | Dashboard ECS, Dashboard Render, Quality gate del modelo, Servicios ECS corriendo, Disponibilidad por endpoint (blackbox) | Prometheus + CloudWatch | Estado de los endpoints y del gate |
| **2. Errores y latencia** | Requests por segundo, Errores 5xx por segundo, Latencia p95 | Prometheus | Tráfico, errores y latencia del dashboard |
| **3. Recursos** | CPU/memoria del servicio `dashboard`, CPU/memoria de la instancia ECS | `ECS/ContainerInsights`, `AWS/EC2`, `CWAgent` | Consumo real de recursos |
| **4. CI/CD y modelo** | Duración del despliegue, Cobertura de tests, ROC-AUC del modelo | `CitiBike/CI`, `CitiBike/Model` | Métricas del pipeline y del modelo |

**Métricas publicadas:**

| Métrica | Namespace | Origen | Valor observado |
|---|---|---|---|
| `DeploymentDurationSeconds` | `CitiBike/CI` | `scripts/deploy.sh` | 127 s |
| `TestCoveragePercent` | `CitiBike/CI` | CI de Flask | 83,61 % |
| `TestsPassed` | `CitiBike/CI` | CI de Flask | 29 |
| `QualityGatePassed` | `CitiBike/CI` | CI de Flask | 1 |
| `roc_auc` | `CitiBike/Model` | `ml/metrics_export.py` | 0,6505 |
| `f1_score` | `CitiBike/Model` | `ml/metrics_export.py` | 0,4650 |
| `QualityGatePassed` | `CitiBike/Model` | `ml/metrics_export.py` | 1 |

**Evidencia:**

| # | Evidencia | Qué demuestra | Dónde verla |
|---|---|---|---|
| 1 | Dashboard JSON | 4 filas y paneles definidos como código | [`citibike-ep3.json`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docker/grafana/dashboards/citibike-ep3.json) |
| 2 | Verificación | Grafana con datasources y dashboard de 4 filas | [`verify.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/verify.txt) |
| 3 | Métricas de CI/CD | Valores en CloudWatch | [`cloudwatch-cicd-values.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-cicd-values.txt) |
| 4 | Métricas del modelo | `roc_auc`, `f1_score`, `QualityGatePassed` | [`ml/metrics_export.py`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/ml/metrics_export.py), [`README.md` — últimas métricas](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/README.md#últimas-métricas-test-temporal) |
| 5 | Cobertura publicada desde Flask | Workflow `ci-cd.yml` y run exitoso | [PR #25](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/pull/25), [run 44588927968](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/runs/44588927968) |
| 6 | Script de métricas | `ci_metrics.py` para workflows y tests | [`scripts/ci_metrics.py`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/scripts/ci_metrics.py) |

**Capturas pendientes:**

- `![Fila 3: recursos](img/03-grafana-fila3.png)`
- `![Fila 4: CI/CD y modelo](img/04-grafana-fila4.png)`

**Pendiente de redacción:** explicar cómo un valor del dashboard cambia una
decisión técnica (por ejemplo, cobertura bajo el umbral o latencia p95 alta).

---

### 3.4 IE4 — Documentación de la integración en el pipeline (10 %)

**Qué pide la rúbrica:** documentar cómo se integran monitoreo, métricas y
seguridad en el pipeline, y cómo permiten tomar decisiones técnicas informadas.

**Documentación disponible:**

| Documento | Contenido | Enlace |
|---|---|---|
| `README.md` (Model-Training-S3) | Arquitectura, setup, pipeline de entrenamiento, CI/CD, seguridad y TBD | [Ver](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/README.md) |
| `docs/ARCHITECTURE.md` | Restricciones, decisiones ECS/observabilidad, flujo de despliegue, mapeo IE y riesgos | [Ver](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/ARCHITECTURE.md) |
| `docs/RUNBOOK.md` | Operación: inicio de sesión, verificación, alarmas, problemas comunes y cierre | [Ver](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/RUNBOOK.md) |
| `docs/COMPLIANCE.md` | Controles C1–C13, modos de auditoría, IE6 y referencias normativas | [Ver](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/COMPLIANCE.md) |
| `docs/TESTING.md` | 9 pasos de verificación manual, incluida una falla controlada y un PR bloqueado | [Ver](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/TESTING.md) |
| `docs/INFORME_EP3.md` | Este informe | — |

**Pendiente de redacción:** esta sección debe explicar, con palabras del equipo,
cómo cada herramienta cambia una decisión. La sección 5 entrega la estructura y
los hechos; el análisis es de los estudiantes.

---

### 3.5 IE5 — Políticas de cumplimiento y auditoría (20 %)

**Qué pide la rúbrica:** aplicar políticas de cumplimiento con SonarQube, branch
protection o scripts de auditoría automatizada, garantizando calidad, seguridad
y trazabilidad.

**Controles implementados (resumen de C1–C13):**

| # | Control | Herramienta | Dónde se aplica |
|---|---|---|---|
| C1 | PR obligatorio hacia `main`, sin push directo | Branch protection | Los 3 repos |
| C2 | Checks requeridos y estrictos (`strict=true`) | Branch protection | Los 3 repos |
| C3 | Force-push y borrado de `main` bloqueados | Branch protection | Los 3 repos |
| C4 | Historial lineal y conversaciones resueltas | Branch protection | Los 3 repos |
| C5 | Revisión por dueños del área | `CODEOWNERS` | Los 3 repos |
| C6 | Dependencias actualizadas de forma controlada | `dependabot.yml` | Los 3 repos |
| C7 | Reporte de vulnerabilidades | `SECURITY.md` | Los 3 repos |
| C8 | Secret scanning y push protection | GitHub Advanced Security | Los 3 repos |
| C9 | SAST + dependencias | Snyk + SonarCloud | Flask, Model-Training |
| C10 | Cobertura mínima como gate | `pytest-cov` | Model-Training (60 %), Flask (70 %) |
| C11 | Quality gate del modelo antes de publicar en S3 | `ml/quality_gate.py` + YAML | Model-Training |
| C12 | `terraform fmt/validate` y validación de configs | `infra-ci.yml` | CitiBike-Infra |
| C13 | Auditoría de cumplimiento automática | `scripts/audit_compliance.py` | CitiBike-Infra |

**Resultado de la última auditoría (modo estricto):**

```text
47 controles, 0 fallas, 0 no evaluables
```

Evidencia: [`compliance.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.txt)
y [`compliance.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.md).

**Cómo reproducirla:**

```bash
cd CitiBike-Infra
python3 scripts/audit_compliance.py --strict
python3 scripts/audit_compliance.py --strict --markdown > auditoria.md
```

**Capturas pendientes:**

- `![Auditoría 47/47](img/09-auditoria.png)`
- `![Branch protection](img/14-branch-protection.png)`

---

### 3.6 IE6 — Gates que detienen el pipeline (20 %)

**Qué pide la rúbrica:** implementar mecanismos que interrumpan automáticamente
el pipeline ante fallas críticas de seguridad o calidad.

**Gates implementados:**

| Falla | Detector | Efecto | Evidencia |
|---|---|---|---|
| Test roto o cobertura bajo el umbral | `Run tests` / `Lint y tests` | Check requerido rojo → merge bloqueado | [`ie6-gate-bloqueante.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ie6-gate-bloqueante.txt) |
| Vulnerabilidad alta o crítica | `Snyk (SCA + Code)` | Check requerido rojo | [`security.yml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/.github/workflows/security.yml) |
| Deuda de calidad sobre el umbral | `SonarCloud` | Check requerido rojo | [`security.yml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/.github/workflows/security.yml) |
| Modelo bajo el umbral | `ml/quality_gate.py` | `ml.train` no publica en S3 y el workflow falla | [`quality_gate.yaml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/config/quality_gate.yaml) |
| Infraestructura inválida | `Terraform fmt + validate` / configs de monitoreo | Check requerido rojo | [`infra-ci.yml`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/.github/workflows/infra-ci.yml) |
| Servicio caído en producción | Alarma `*-dashboard-unhealthy` + `DashboardDown` | Alarma en `ALARM` visible en CloudWatch/Grafana | [`monitoring.tf`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/terraform/monitoring.tf) |
| Despliegue que no estabiliza | Circuit breaker de ECS | Rollback automático | [`ecs.tf`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/terraform/ecs.tf) |

**Evidencia empírica del PR bloqueado (PR #24 de Flask):**

| Check | Resultado |
|---|---|
| `Run tests` | ❌ `fail` |
| `SonarCloud` | ❌ `fail` |
| `Build Docker image` | ⏭️ `skipping` |
| `Deploy en Kubernetes simulado (kind)` | ⏭️ `skipping` |
| `Deploy to Render` | ⏭️ `skipping` |
| `Publicar imagen en GHCR` | ⏭️ `skipping` |
| `mergeStateStatus` | 🔒 `BLOCKED` |

Evidencia: [`ie6-gate-bloqueante.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ie6-gate-bloqueante.txt)  
PR (cerrado después de la captura): <https://github.com/Sebithaz-dev/Flask-Dashboard-S3/pull/24>

**Quality gate del modelo (umbrales y valores):**

| Métrica | Umbral | Valor | Estado |
|---|---:|---:|---|
| `roc_auc` | ≥ 0,62 | 0,6505 | ✅ |
| `pr_auc` | ≥ 0,40 | 0,4455 | ✅ |
| `f1_score` | ≥ 0,42 | 0,4650 | ✅ |
| `recall` | ≥ 0,60 | 0,7035 | ✅ |
| `precision` | ≥ 0,30 | 0,3473 | ✅ |
| `accuracy` | ≥ 0,52 | 0,5500 | ✅ |
| `test_size` | ≥ 1.000 | 94.686 | ✅ |

**Cómo ver el gate en local:**

```bash
cd Model-Training-S3
python -m ml.quality_gate --metrics ml/artefactos/metricas.json --json
# exit code 0 si pasa; 1 si alguna métrica queda bajo el umbral
```

Para simular una falla sin tocar el modelo real, copiar `metricas.json` a
`/tmp`, bajar `roc_auc` a `0.10` y ejecutar el gate contra esa copia.

**Capturas pendientes:**

- `![PR bloqueado](img/07-pr-bloqueado.png)`
- `![Checks del PR](img/08-github-actions-gate.png)`

---

## 4. Matriz consolidada IE → evidencia

| IE | Peso | Qué se exige | Evidencia principal | Evidencia complementaria | Estado |
|---|---:|---|---|---|---|
| **IE1** | 20 % | Monitoreo, logs, métricas y disponibilidad | [`verify.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/verify.txt), [`prometheus-up.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/prometheus-up.txt) | [`cloudwatch-alarms.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-alarms.txt), dashboard, logs | ✅ Implementado y verificado |
| **IE2** | 20 % | Despliegue orquestado en la nube con observabilidad | [`ecs-services.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ecs-services.txt), [`target-group-dashboard.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/target-group-dashboard.txt) | [`terraform-outputs.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/terraform-outputs.txt), `terraform/` | ✅ Implementado y verificado |
| **IE3** | 10 % | Dashboard con métricas de despliegue, cobertura, recursos y errores | [`citibike-ep3.json`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docker/grafana/dashboards/citibike-ep3.json), [`cloudwatch-cicd-values.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-cicd-values.txt) | [Run 44588927968](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/runs/44588927968), `ml/metrics_export.py` | ✅ Implementado con datos reales |
| **IE4** | 10 % | Documentar la integración y su impacto en decisiones | `README.md`, `docs/ARCHITECTURE.md`, `docs/RUNBOOK.md`, `docs/COMPLIANCE.md`, `docs/TESTING.md` | Este informe y sus secciones 5–9 | 🟡 Parcial: falta la narrativa del equipo y las reflexiones |
| **IE5** | 20 % | Políticas de cumplimiento y auditoría automatizada | [`compliance.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.txt), [`compliance.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.md) | [`audit_compliance.py`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/scripts/audit_compliance.py), [`COMPLIANCE.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/COMPLIANCE.md) | ✅ 47/47 controles |
| **IE6** | 20 % | Gates que detienen el pipeline ante fallas críticas | [`ie6-gate-bloqueante.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ie6-gate-bloqueante.txt) | [`quality_gate.yaml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/config/quality_gate.yaml), workflows, circuit breaker | ✅ Implementado y demostrado |

**Cobertura de la rúbrica:** IE1, IE2, IE3, IE5 e IE6 están implementados y
evidenciados (90 % de la ponderación). IE4 queda parcial hasta que el equipo
complete la narrativa de las secciones 5–9 y la sección 10.

---

## 5. Integración en el pipeline CI/CD (IE4)

> Esta sección entrega la estructura y los hechos. El análisis de impacto debe
> redactarse con las palabras del equipo.

### 5.1 Etapas y herramientas

| Etapa | Herramienta | Qué valida | Si falla | Evidencia |
|---|---|---|---|---|
| Desarrollo local | `ruff`, `pytest`, `pytest-cov` | Estilo, tests y cobertura | No se abre el PR o se corrige antes | `pyproject.toml`, `requirements-dev.txt` |
| Pull request | GitHub Actions `CI` | Lint, tests, cobertura ≥ 60 %, health check | Check rojo | [`.github/workflows/ci.yml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/.github/workflows/ci.yml) |
| Pull request | Snyk + SonarCloud | Vulnerabilidades y calidad | Check rojo | [`.github/workflows/security.yml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/.github/workflows/security.yml) |
| Pull request | Build + smoke test | Imagen construible y saludable | Check rojo | `ci.yml` (job `docker`) |
| Merge | Branch protection | PR, checks estrictos, conversaciones, CODEOWNERS | Merge bloqueado | [`COMPLIANCE.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/COMPLIANCE.md) |
| Entrenamiento | `ml/train.py` + `quality_gate.py` | Métricas mínimas antes de publicar en S3 | Workflow rojo, sin artefactos nuevos | [`quality_gate.yaml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/config/quality_gate.yaml) |
| Infraestructura | Terraform + validación de configs | Recursos válidos y reproducibles | Check rojo | [`.github/workflows/infra-ci.yml`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/.github/workflows/infra-ci.yml) |
| Cumplimiento | `audit_compliance.py` | Gobierno, protección y workflows | Check rojo | [`.github/workflows/compliance.yml`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/.github/workflows/compliance.yml) |
| Despliegue | `deploy.sh` + ECS | Rolling update y estabilidad | Circuit breaker / rollback | [`scripts/deploy.sh`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/scripts/deploy.sh) |
| Operación | Prometheus + Grafana + CloudWatch | Disponibilidad, errores, latencia, recursos | Alarma / dashboard en rojo | [`monitoring.tf`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/terraform/monitoring.tf) |

### 5.2 Decisiones que habilita el pipeline

| Señal | Decisión técnica | Dónde se ve |
|---|---|---|
| Cobertura < 60 % (modelo) o < 70 % (Flask) | No mergear; agregar tests | Check `Lint y tests` / `Run tests` |
| `roc_auc` < 0,62 o `f1_score` < 0,42 | No publicar el modelo en S3 | `ml/quality_gate.py` |
| Vulnerabilidad alta/crítica | No mergear; actualizar dependencia | `Snyk (SCA + Code)` |
| Quality gate de SonarCloud en rojo | No mergear; reducir deuda | `SonarCloud` |
| Latencia p95 > 1,5 s o 5xx > 5 | Investigar; revisar dashboard y logs | Alarmas `latency-p95`, `target-5xx` |
| Servicio caído | Reiniciar/rollback; revisar `verify.sh` | Alarma `dashboard-unhealthy` |
| Auditoría con fallas | Corregir gobierno antes de seguir | `Auditoria de cumplimiento` |

> `[COMPLETAR: explicar con un ejemplo real cómo una de estas señales cambió una
> decisión del equipo. No usar IA para esta justificación.]`

### 5.3 Documentación de soporte

- [`README.md` de Model-Training-S3](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/README.md):
  arquitectura, setup, pipeline, CI/CD y TBD.
- [`docs/ARCHITECTURE.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/ARCHITECTURE.md):
  restricciones, decisiones, flujo de despliegue y riesgos.
- [`docs/RUNBOOK.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/RUNBOOK.md):
  operación y troubleshooting.
- [`docs/COMPLIANCE.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/COMPLIANCE.md):
  controles y referencias normativas.
- [`docs/TESTING.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/TESTING.md):
  verificación manual paso a paso.

---

## 6. Cumplimiento y auditoría (IE5)

La auditoría recorre los tres repositorios y verifica:

1. Protección de `main`: PR obligatorio, checks requeridos, `strict`, force-push
   y borrado bloqueados, historial lineal, conversaciones resueltas.
2. Archivos de gobierno: `SECURITY.md`, `.github/CODEOWNERS`,
   `.github/dependabot.yml`.
3. Secret scanning y push protection.
4. Último run en `main` de cada workflow en verde.

**Resultado de la sesión 2026-11-19:**

```text
47 controles, 0 fallas, 0 no evaluables
```

**Modos de ejecución:**

| Modo | Token | Protección de rama | Uso |
|---|---|---|---|
| `--strict` | Token de `gh auth` con administración | Se evalúa y un `SKIP` cuenta como falla | Evidencia para el informe |
| Sin `--strict` | `GITHUB_TOKEN` de Actions | Se marca `SKIP` | CI de cada PR |

**Evidencia:**

- [`compliance.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.txt)
- [`compliance.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.md)
- [`scripts/audit_compliance.py`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/scripts/audit_compliance.py)
- [`docs/COMPLIANCE.md`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/COMPLIANCE.md)

> `[COMPLETAR: explicar cómo se aplicaron las políticas y qué control les pareció
> más útil. Esta justificación debe ser propia.]`

---

## 7. Demostración del gate bloqueante (IE6)

### 7.1 Caso real: PR con un test que falla

Se creó el PR [#24](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/pull/24)
con un test que falla a propósito (`assert False`). El resultado fue:

```text
Run tests                                  fail
SonarCloud                                 fail
Build Docker image                         skipping
Deploy en Kubernetes simulado (kind)       skipping
Deploy to Render                           skipping
Publicar imagen en GHCR                    skipping
mergeStateStatus                           BLOCKED
```

La captura completa está en
[`ie6-gate-bloqueante.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/ie6-gate-bloqueante.txt).
El PR se cerró después de capturar la evidencia.

### 7.2 Caso del modelo: quality gate antes de S3

`ml/train.py` evalúa las métricas contra `config/quality_gate.yaml`. Si alguna
métrica queda bajo el umbral, no se suben los artefactos a S3 y el workflow
termina con error. Los umbrales actuales y los valores del modelo están en la
sección 3.6.

### 7.3 Caso de infraestructura: Terraform inválido

`infra-ci.yml` ejecuta `terraform fmt -check`, `terraform validate` y la
validación de las configuraciones de monitoreo. Un error de sintaxis o una
configuración inválida deja el check requerido en rojo y bloquea el merge.

### 7.4 Caso de operación: alarma y circuit breaker

- **Alarma `citibike-dev-dashboard-unhealthy`**: si el target del ALB no tiene
  hosts sanos, pasa a `ALARM`.
- **Alarma `citibike-dev-target-5xx`**: errores 5xx por encima de 5.
- **Alarma `citibike-dev-latency-p95`**: latencia p95 por encima de 1,5 s.
- **Circuit breaker de ECS**: si una task nueva no arranca, ECS hace rollback a
  la definición anterior.

Procedimiento reproducible para ver una alarma en vivo:
[`docs/TESTING.md` §5](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/TESTING.md).

---

## 8. Resultados y métricas

### 8.1 Disponibilidad

| Endpoint | Estado | Evidencia |
|---|---|---|
| Dashboard ECS `/health` | 200 | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) |
| Dashboard ECS `/` | 200 | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) |
| Dashboard ECS `/metrics` | 200 | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) |
| Grafana `/api/health` | 200 | [`http-status.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/http-status.txt) |
| Render `/health` | `up=1` | [`prometheus-up.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/prometheus-up.txt) |
| Prometheus | `up=1` | [`prometheus-up.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/prometheus-up.txt) |

### 8.2 CI/CD

| Métrica | Valor | Fuente |
|---|---:|---|
| Cobertura de tests de Flask | 83,61 % | [Run 44588927968](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/runs/44588927968) |
| Tests de Flask | 29 pasados | [Run 44588927968](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/runs/44588927968) |
| Duración del despliegue | 127 s | [`cloudwatch-cicd-values.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-cicd-values.txt) |
| `QualityGatePassed` (CI) | 1 | [`cloudwatch-cicd-values.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/cloudwatch-cicd-values.txt) |
| Controles de cumplimiento | 47/47 | [`compliance.txt`](https://github.com/Sebithaz-dev/CitiBike-Infra/blob/main/docs/evidence/20261119T183438Z/compliance.txt) |

### 8.3 Modelo

| Métrica | Valor | Umbral | Estado |
|---|---:|---:|---|
| ROC-AUC | 0,6505 | ≥ 0,62 | ✅ |
| PR-AUC | 0,4455 | ≥ 0,40 | ✅ |
| F1 | 0,4650 | ≥ 0,42 | ✅ |
| Recall | 0,7035 | ≥ 0,60 | ✅ |
| Precision | 0,3473 | ≥ 0,30 | ✅ |
| Accuracy | 0,5500 | ≥ 0,52 | ✅ |
| Test size | 94.686 | ≥ 1.000 | ✅ |

Fuente: [`README.md` — últimas métricas](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/README.md#últimas-métricas-test-temporal)
y [`quality_gate.yaml`](https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/config/quality_gate.yaml).

### 8.4 Recursos observados

| Recurso | Ventana | Valor observado | Fuente |
|---|---|---:|---|
| CPU de la instancia ECS | sesión 2026-11-19 | 3–20 % | `AWS/EC2` en Grafana/CloudWatch |
| Memoria de la instancia | sesión 2026-11-19 | ≈ 6–8 % | `CWAgent` |
| CPU del servicio `dashboard` | sesión 2026-11-19 | ≈ 12–13 % | `ECS/ContainerInsights` |

> Estos valores son una muestra de la sesión, no un benchmark. Sirven para
> demostrar que las métricas de host y de contenedor están llegando al
> dashboard.

---

## 9. Limitaciones y trabajo futuro

### 9.1 Limitaciones (hechos)

| Limitación | Impacto | Mitigación actual |
|---|---|---|
| Una sola instancia ECS | Punto único de falla | Runbook, circuit breaker, recreación con Terraform |
| Prometheus con retención de 6 h | No hay histórico largo | CloudWatch conserva métricas y logs |
| Alertmanager sin correo en la demo | Las alertas no llegan por email | Se ven en Grafana/Prometheus; SNS opcional con `var.alarm_email` |
| Dashboard público sin TLS | Tráfico sin cifrar | Excepción de demo documentada; en producción ACM + HTTPS |
| Credenciales del Learner Lab de 4 h | Los workflows se degradan sin credenciales | Preflight y warning en `train.yml` / CI de Flask |
| ECS en lugar de EKS | No hay portabilidad directa de Kubernetes | Manifiestos de EP2 conservados; decisión documentada |
| Logs solo en CloudWatch | No se consultan desde Grafana | Enlace directo y `aws logs tail` en el runbook |

### 9.2 Trabajo futuro

- [COMPLETAR: 3–5 ideas propias, por ejemplo TLS, multi-instancia, Loki, alertas
  por correo, autoscaling o más paneles.]
- [COMPLETAR]
- [COMPLETAR]

---

## 10. Conclusiones y reflexiones individuales

> **IMPORTANTE — LEER ANTES DE ESCRIBIR.**
>
> La pauta de la EP3 prohíbe usar inteligencia artificial para redactar
> **conclusiones, justificaciones técnicas o reflexiones individuales**. Esta
> sección debe escribirse **sin IA**, con las palabras de cada integrante.
>
> No se entrega texto generado automáticamente en esta sección. Si se usó IA en
> otras partes, ya quedó declarado al inicio del informe.

### 10.1 Conclusiones del equipo

[VACÍO — escribir aquí. Guía: ¿qué aprendió el equipo sobre observabilidad,
despliegue y gates? ¿Qué decisión técnica fue la más difícil y por qué? ¿Qué
harían distinto en una próxima entrega? Extensión sugerida: 3–5 párrafos.]

### 10.2 Reflexión individual — [Nombre completo 1]

[VACÍO — escribir aquí, sin IA. Guía: ¿qué aporté al proyecto? ¿Qué aprendí?
¿Qué herramienta o concepto me costó más y cómo lo resolví? ¿Qué evidencia de mi
trabajo puedo señalar? Extensión sugerida: 2–4 párrafos.]

### 10.3 Reflexión individual — [Nombre completo 2]

[VACÍO — escribir aquí, sin IA. Guía: ¿qué aporté al proyecto? ¿Qué aprendí?
¿Qué herramienta o concepto me costó más y cómo lo resolví? ¿Qué evidencia de mi
trabajo puedo señalar? Extensión sugerida: 2–4 párrafos.]

---

## Anexo A — Índice de evidencia

Carpeta completa:
[`CitiBike-Infra/docs/evidence/20261119T183438Z/`](https://github.com/Sebithaz-dev/CitiBike-Infra/tree/main/docs/evidence/20261119T183438Z)

| Archivo | Contenido |
|---|---|
| `verify.txt` | Verificación end-to-end (`verify.sh`) |
| `terraform-outputs.txt` | URLs y nombres de recursos desplegados |
| `ecs-services.txt` | Servicios ECS con tareas deseadas/corriendo y rollout |
| `ecs-instances.txt` | Instancias registradas en el cluster |
| `target-group-dashboard.txt` | Salud del target group del dashboard |
| `target-group-grafana.txt` | Salud del target group de Grafana |
| `http-status.txt` | Códigos HTTP de `/health`, `/`, `/metrics` y Grafana |
| `prometheus-up.txt` | Series `up` (disponibilidad por job) |
| `prometheus-rules.txt` | Reglas de alerta cargadas y su estado |
| `prometheus-alerts.txt` | Alertas activas en el momento de la captura |
| `cloudwatch-alarms.txt` | Alarmas de CloudWatch y su estado |
| `cloudwatch-metrics.txt` | Métricas disponibles por namespace |
| `cloudwatch-cicd-values.txt` | Últimos valores de las métricas de CI/CD |
| `compliance.txt` / `compliance.md` | Auditoría de cumplimiento de los 3 repos |
| `ie6-gate-bloqueante.txt` | Evidencia del PR bloqueado por el gate |

## Anexo B — Comandos de reproducción

```bash
# 1. Credenciales del Learner Lab
export AWS_REGION=us-east-1
aws sts get-caller-identity

# 2. Infraestructura
cd CitiBike-Infra
./scripts/verify.sh --wait

# 3. Dashboard
terraform -chdir=terraform output -raw dashboard_url
terraform -chdir=terraform output -raw grafana_url

# 4. Métricas y logs
curl -s "$(terraform -chdir=terraform output -raw dashboard_url)/metrics" | head
aws logs tail /ecs/citibike-dev/dashboard --since 10m

# 5. Alarmas y reglas
aws cloudwatch describe-alarms --alarm-name-prefix citibike-dev \
  --query 'MetricAlarms[].[AlarmName,StateValue]' --output table

# 6. Despliegue medido
./scripts/deploy.sh latest

# 7. Auditoría y evidencia
python3 scripts/audit_compliance.py --strict
./scripts/collect_evidence.sh

# 8. Cierre
./scripts/down.sh
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].InstanceId' --output text
```

## Anexo C — URLs y acceso de la sesión

| Recurso | Valor |
|---|---|
| Dashboard | `http://<alb-dns>` |
| Grafana | `http://<alb-dns>:3000` |
| Usuario Grafana | `admin` |
| Password Grafana | `citibike-ep3` (demo) |
| Dashboard UID | `citibike-ep3` |
| Cluster ECS | `citibike-dev-cluster` |
| Región | `us-east-1` |

> La URL del ALB se obtiene con `terraform -chdir=terraform output -raw dashboard_url`.
> No incluir credenciales AWS en el informe.

## Anexo D — Checklist antes de entregar

- [ ] Reemplazar todos los `[COMPLETAR]`.
- [ ] Agregar las capturas de `docs/img/` y verificar que se vean.
- [ ] Completar la declaración de uso de IA.
- [ ] Escribir la sección 10 **sin IA**.
- [ ] Revisar que los enlaces a GitHub funcionen (repos públicos).
- [ ] Confirmar que la evidencia corresponda a la fecha de la sesión.
- [ ] Verificar que no haya credenciales, tokens ni datos personales.
- [ ] Exportar a PDF si el curso lo exige.
- [ ] Subir el enlace del repositorio a AVA y enviarlo por correo al docente.
- [ ] Al terminar la demostración: `./scripts/down.sh` y comprobar que no queden
      instancias, ALB ni cluster activos.
