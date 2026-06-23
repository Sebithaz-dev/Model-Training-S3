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

Workflow `.github/workflows/train.yml`:

- **Trigger:** Semanal (domingo 2am UTC) + `workflow_dispatch` manual
- **Pasos:** checkout → setup python → instalar deps → configurar AWS → descargar datos curados desde S3 → entrenar → subir artefactos
- **Secrets requeridos:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `S3_BUCKET_NAME`
- **Variables:** `AWS_REGION` (default `us-east-1`), `S3_DATA_KEY` (default `curated/citibike_trips/citibike_curated.snappy.parquet`), `S3_MODEL_PREFIX` (default `models/`)

---

## Repositorios relacionados

- [Flask-Dashboard-S3](https://github.com/anomalyco/Flask-Dashboard-S3) — Dashboard Flask + Chart.js que consume los artefactos de S3

---

## Estructura del proyecto

```
.
├── .env.example            # Variables de entorno (template)
├── .github/workflows/      # CI/CD
│   └── train.yml
├── ml/                     # Código fuente del pipeline
│   ├── __init__.py
│   ├── train.py            # Entrenamiento del modelo
│   ├── predict.py          # Predicción local (CLI demo)
│   └── s3_utils.py         # Subida/descarga desde S3
├── pyproject.toml
└── requirements.txt
```
