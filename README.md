# Model Training — Citi Bike S3

Pipeline de entrenamiento automatizado para clasificar la duración de viajes de Citi Bike NYC en **corto** (< 15 min) o **largo** (≥ 15 min), utilizando datos curados desde AWS Glue y subiendo artefactos a S3.

---

## Arquitectura

```
AWS Glue (ETL)                          GitHub Actions                     S3
┌─────────────────┐    ┌──────────────────────────────┐    ┌─────────────────────┐
│ Landing Parquet │    │  checkout → setup python     │    │ modelo.pkl          │
│       ↓         │──▶│       ↓                      │──▶│ transformers.pkl    │
│ Curado + FE base│    │  python -m ml.train          │    │ metricas.json       │
└─────────────────┘    │       ↓                      │    └─────────────────────┘
                       │  upload artifacts to S3      │
                       └──────────────────────────────┘
                                  ▲
                           schedule: weekly
                           (domingo 2am UTC)
```

1. **AWS Glue** lee desde `landing/`, crea features temporales (`hour`, `month`, `dayofweek`, `is_weekend`, `age`), filtra outliers y guarda en `curated/`.
2. **GitHub Actions** (semanal o manual) descarga el Parquet curado, entrena el modelo y sube los artefactos a S3.
3. **Dashboard Flask** (repositorio separado) consume `modelo.pkl`, `transformers.pkl` y `metricas.json` desde S3 para predicciones y visualización de métricas.

---

## Setup

```bash
git clone <repo-url>
cd Model-Training-S3
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Llenar .env con credenciales AWS
```

### Variables de entorno

| Variable | Descripción |
|---|---|
| `AWS_ACCESS_KEY_ID` | Access Key de AWS (Learner Lab) |
| `AWS_SECRET_ACCESS_KEY` | Secret Key de AWS |
| `AWS_SESSION_TOKEN` | Session Token (Learner Lab) |
| `AWS_REGION` | Región (default: `us-east-1`) |
| `S3_BUCKET_NAME` | Bucket de destino |
| `S3_DATA_KEY` | Ruta al Parquet curado en S3 |
| `S3_MODEL_PREFIX` | Prefix donde subir artefactos (default: `models/`) |

---

## Uso local

### Entrenar

```bash
python -m ml.train --input data/datos.parquet
```

Requiere un archivo Parquet local con las columnas del dataset curado. Al finalizar sube automáticamente los artefactos a S3 si las credenciales están configuradas.

Los hiperparámetros y umbrales viven en `config/model.yaml` (cargado por `ml/config.py`). Para usar una configuración alternativa sin tocar el repo:

```bash
python -m ml.train --input data/datos.parquet --config config/model-experimento.yaml
# o
MODEL_CONFIG=config/model-experimento.yaml python -m ml.train --input data/datos.parquet
```

Antes del feature engineering se valida el schema del Parquet contra el contrato declarado en `ml/data_validation.py`; si los datos no cumplen (columna ausente, tipo incorrecto, valor fuera de rango), el pipeline aborta con `DataValidationError`.

### Probar predicción (CLI)

```bash
python -m ml.predict
```

Ejecuta ejemplos de prueba con un Passenger (`Customer`, 5pm → largo) vs un Suscriptor (`Subscriber`, 8am → corto).

---

## Pipeline de entrenamiento (`ml/train.py`)

### Entradas

Parquet con columnas:

| Columna | Tipo | Descripción |
|---|---|---|
| `tripduration` | int | Duración del viaje en segundos |
| `starttime` | datetime | Inicio del viaje |
| `start_station_id` | int | ID de estación de inicio |
| `usertype` | str | `Customer` / `Subscriber` |
| `gender` | str | `Male` / `Female` / `Unknown` |
| `birth_year` | int | Año de nacimiento |
| `year` | int | Año del viaje |
| `hour` | int | Hora (0-23) |
| `month` | int | Mes (1-12) |
| `dayofweek` | int | Día de semana (0=lunes, 6=domingo) |
| `is_weekend` | int | 1 si fin de semana, 0 si no |
| `age` | int | Edad calculada (`year - birth_year`) |

### Feature Engineering

- `start_station_freq` — frequency encoding con `log1p`
- `usertype` / `gender` — `LabelEncoder` (fiteado sobre training set)
- Escalado con `StandardScaler`

### Target

- **1** (`largo`) si `tripduration / 60 > 15` (> 900 segundos)
- **0** (`corto`) en caso contrario
- Umbral de decisión del modelo: **0.65**

### Modelo

```python
LogisticRegression(random_state=42, max_iter=1000, class_weight="balanced")
```

### Salidas (subidas a S3)

| Archivo | Contenido |
|---|---|
| `modelo.pkl` | Modelo entrenado (joblib) |
| `transformers.pkl` | LabelEncoders + Scaler + station_freq + feature_cols |
| `metricas.json` | Métricas de evaluación + umbral + features usadas |

---

## Métricas reportadas

Las métricas se calculan sobre el test set (80/20 split estratificado) y se guardan en `metricas.json`:

| Métrica | Descripción |
|---|---|
| `accuracy` | Exactitud global |
| `recall` | Recall clase positiva (`largo`) |
| `precision` | Precisión clase positiva |
| `f1` | F1-score clase positiva |
| `roc_auc` | Área bajo la curva ROC |
| `gini` | Coeficiente Gini (`2 * roc_auc - 1`) |
| `confusion_matrix` | Matriz [[TN, FP], [FN, TP]] |
| `train_size` / `test_size` | Tamaño de cada split |
| `proportion` | Proporción de viajes largos en test |

---

## CI/CD (GitHub Actions)

### `ci.yml` — lint y tests (calidad continua)

- **Triggers:** `push` a `develop` y `pull_request` a `main`.
- **Pasos:** checkout → setup Python 3.11 (cache de pip) → instalar `requirements-dev.txt` → `ruff check` → `pytest`.
- **Propósito:** garantizar que todo lo que llega a `main` o se integra en `develop` pasa lint y tests. Bloquea el merge si falla.

### `train.yml` — entrenamiento + subida a S3

- **Trigger:** Semanal (domingo 2am UTC) + `workflow_dispatch` manual
- **Pasos:** checkout → setup python → instalar deps → configurar AWS → descargar datos curados desde S3 → entrenar → subir artefactos
- **Secrets requeridos:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `S3_BUCKET_NAME`
- **Variables:** `AWS_REGION` (default `us-east-1`), `S3_DATA_KEY` (default `curated/citibike_trips/citibike_curated.snappy.parquet`), `S3_MODEL_PREFIX` (default `models/`)

---

## Estrategia de branching: Trunk-Based Development (TBD)

Este repositorio usa **trunk-based development** en lugar de GitFlow.

### Justificación

- **`main` es el único trunk de integración.** Siempre está en estado *deployable*: la CI corre en cada PR a `main` y el workflow de entrenamiento corre desde `main`.
- **Ramas de vida corta.** Las `feature/*` y `hotfix/*` duran **menos de 2-3 días** y se integran por PR *squash* a `main`. Esto reduce el riesgo de merge, hace los cambios revisables en pequeño y mantiene el historial lineal y legible.
- **Equipo pequeño, releases continuos.** GitFlow (con `release/*` de larga duración y `develop` como rama de integración paralela) agrega ceremonia innecesaria para un pipeline de ML que publica artefactos a S3 de forma continua. TBD minimiza la distancia entre *código escrito* y *código en producción*.
- **Feedback rápido.** Al integrar contra `main` continuamente, los conflictos y los fallos se detectan en horas, no en semanas.
- **`develop` existe como rama de respaldo/sincronización** (no como rama de integración paralela): se mantiene *fast-forward* con `main` y la CI corre sobre ella para validar cambios de infraestructura o experimentos antes de tocar `main`.

### Ramas

| Rama | Tipo | Duración | Propósito |
|---|---|---|---|
| `main` | Trunk | Permanente | Código en producción. Siempre *deployable*. |
| `develop` | Espejo de `main` | Permanente | Sincronizada con `main` vía fast-forward. Sirve de superficie para validar pushes directos (la CI corre aquí). |
| `feature/<nombre>` | Efímera | < 2-3 días | Nueva funcionalidad. Se abre desde `main` y se integra por PR *squash* a `main`. |
| `hotfix/<nombre>` | Efímera | < 1 día | Corrección urgente. Se abre desde `main`, se integra por PR *squash* a `main` y se backportea a `develop` por fast-forward. |

### Flujo de trabajo

```
main (trunk, siempre deployable)
 │
 ├── feature/data-validation ──► PR #2 (squash) ──► main
 ├── feature/model-config ─────► PR #3 (squash) ──► main
 ├── hotfix/predict-label-encoder ─► PR #4 (squash) ──► main ──► fast-forward develop
 │
 CI (ci.yml): push a develop + PR a main
```

1. `git checkout main && git pull`
2. `git checkout -b feature/<nombre-corto-en-kebab-case>`
3. Commits pequeños con [Conventional Commits](#convenciones-de-commits).
4. `git push -u origin feature/<nombre>`
5. Abrir PR a `main` (la CI corre automáticamente).
6. Revisión según la [estrategia de revisión](#estrategia-de-revision).
7. *Squash & merge* a `main`. La rama efímera se borra.
8. Tras un hotfix, `develop` se sincroniza con `main` por fast-forward.

### Convenciones de commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<scope>): <descripcion imperativa en presente>

<cuerpo opcional explicando el por qué>

<footer opcional: BREAKING CHANGE: ... o Co-Authored-By>
```

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad (`feat(validation): ...`, `feat(config): ...`) |
| `fix` | Corrección de bug (`fix(predict): ...`) |
| `docs` | Solo documentación |
| `test` | Solo tests |
| `refactor` | Reestructuración sin cambio de comportamiento |
| `ci` | Cambios en CI/CD |
| `chore` | Tareas de mantenimiento (deps, configs) |

Reglas:
- El **scope** es el módulo afectado (`validation`, `config`, `predict`, `ci`).
- La descripción va en **imperativo presente**, minúsculas, sin punto final, **< 72 chars**.
- El cuerpo explica el **por qué**, no el qué (el diff ya muestra el qué).
- *Squash & merge* produce un commit por PR, manteniendo el historial lineal.

### Naming de ramas

- `feature/<nombre-corto-en-kebab-case>` — describe la capacidad, no la solución (`feature/data-validation`, no `feature/add-checks`).
- `hotfix/<nombre-corto-en-kebab-case>` — describe el bug o síntoma (`hotfix/predict-label-encoder`).
- Sin prefijo `feature/`/`hotfix/` no se aceptan PRs a `main`.
- Nada de ramas con nombres de persona ni de fechas.

### Flujos de merge

| Origen → Destino | Estrategia | Condición |
|---|---|---|
| `feature/*` → `main` | **Squash & merge** | CI verde + 1 aprobación |
| `hotfix/*` → `main` | **Squash & merge** | CI verde + 1 aprobación (revisión acelerada) |
| `main` → `develop` | **Fast-forward** | Automático tras cada merge a `main` |

- No se hace *merge commit* ni *rebase* directo a `main`: solo squash para mantener un commit por PR.
- `main` nunca recibe commits directos: todo entra por PR.
- `develop` nunca recibe commits de feature: solo se sincroniza desde `main`.

### Estrategia de revisión

- **Todo cambio a `main` requiere al menos 1 aprobación** (branch protection recomendada).
- La **CI debe estar verde** (lint + tests) antes de mergear — es obligatoria, no opcional.
- Para **hotfixes**, la revisión se acelera pero sigue siendo obligatoria: se prioriza revisar el alcance mínimo y que exista test que cubra el bug corregido.
- El revisor verifica:
  1. El PR hace **una sola cosa** (tamaño pequeño, < ~300 líneas cuando sea posible).
  2. No introduce **hardcodeo** ni secretos (credenciales viajan por `secrets`/`.env`, nunca en código).
  3. Incluye **tests** para la nueva funcionalidad o el bug corregido.
  4. El **commit message** cumple Conventional Commits.
  5. La **documentación** relevante (README, schemas) se actualiza si el comportamiento cambia.

---

## Repositorios relacionados

- [Flask-Dashboard-S3](https://github.com/anomalyco/Flask-Dashboard-S3) — Dashboard Flask + Chart.js que consume los artefactos de S3

---

## Estructura del proyecto

```
.
├── .env.example            # Variables de entorno (template)
├── .github/workflows/      # CI/CD
│   ├── ci.yml              # Lint + tests (push a develop, PR a main)
│   └── train.yml           # Entrenamiento semanal + subida a S3
├── config/
│   └── model.yaml          # Hiperparámetros y umbrales del modelo
├── ml/                     # Código fuente del pipeline
│   ├── __init__.py
│   ├── config.py           # Carga de configuración YAML
│   ├── data_validation.py  # Validación de schema y calidad de datos
│   ├── train.py            # Entrenamiento del modelo
│   ├── predict.py          # Predicción local (CLI demo)
│   └── s3_utils.py         # Subida/descarga desde S3
├── tests/                  # Tests unitarios (pytest)
├── pyproject.toml          # Config de ruff y pytest
├── requirements.txt        # Dependencias runtime
└── requirements-dev.txt    # Dependencias desarrollo (pytest, ruff)
```
