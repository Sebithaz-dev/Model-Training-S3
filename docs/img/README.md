# Capturas para el informe EP3

El informe (`docs/INFORME_EP3.md`) referencia estas imágenes. Guárdalas en esta
carpeta con los nombres indicados para que los enlaces funcionen sin editar el
Markdown.

| Archivo | Qué capturar | Dónde |
|---|---|---|
| `01-grafana-fila1.png` | Fila **1. Disponibilidad** completa | Grafana → dashboard `citibike-ep3` |
| `02-grafana-fila2.png` | Fila **2. Errores y latencia** con tráfico reciente | Grafana → dashboard `citibike-ep3` |
| `03-grafana-fila3.png` | Fila **3. Recursos** (servicio e instancia) | Grafana → dashboard `citibike-ep3` |
| `04-grafana-fila4.png` | Fila **4. CI/CD y modelo** (duración, cobertura, ROC-AUC) | Grafana → dashboard `citibike-ep3` |
| `05-cloudwatch-alarms.png` | Las 8 alarmas en estado `OK` | Consola AWS → CloudWatch → Alarms |
| `06-cloudwatch-logs.png` | Último stream de `/ecs/citibike-dev/dashboard` | Consola AWS → CloudWatch → Log groups |
| `07-pr-bloqueado.png` | PR de demo con `mergeStateStatus = BLOCKED` | GitHub → Pull requests |
| `08-github-actions-gate.png` | Checks `Run tests` / `SonarCloud` en rojo y jobs en `skipping` | GitHub → Actions |
| `09-auditoria.png` | Salida `47 controles, 0 fallas, 0 no evaluables` | Terminal o GitHub Actions |
| `10-falla-controlada.png` | Alarma `citibike-dev-dashboard-unhealthy` en `ALARM` y fila 1 en rojo | `docs/TESTING.md` §5 (CitiBike-Infra) |
| `11-verify.png` | Salida de `./scripts/verify.sh --wait` con `Todo OK` | Terminal |
| `12-ecs-servicios.png` | Los 5 servicios ECS en `1/1` | Consola AWS → ECS |
| `13-target-groups.png` | Target groups `healthy` | Consola AWS → EC2 → Target groups |
| `14-branch-protection.png` | Reglas de protección de `main` | GitHub → Settings → Branches |
| `15-correo-sns.png` | Correo de la alarma (ALARM y OK) recibido vía SNS | Bandeja del correo de `alarm_email` |
| `16-grafana-fila5.png` | Fila **5. Logs** con errores y logs recientes | Grafana → dashboard `citibike-ep3` |
| `17-pr-seguridad.png` | PR con dependencia vulnerable: Snyk en rojo y `BLOCKED` | `docs/TESTING.md` §6.1 (CitiBike-Infra) |
| `18-deploy-ecs.png` | Resumen del job `Deploy en AWS ECS` (commit, revisiones y duración) | GitHub → Actions → CI/CD Flask Dashboard |

## Cómo capturar Grafana

1. Abrir `http://<alb-dns>:3000` con el usuario `admin`; la contraseña se obtiene con
   `terraform -chdir=terraform output -raw grafana_admin_password` (CitiBike-Infra).
2. Elegir el rango de tiempo **Last 30 minutes**.
3. Usar el menú **Share → Snapshot** o una captura de pantalla de la fila.
4. Guardar con el nombre exacto de la tabla.

## Cómo capturar el PR bloqueado

La evidencia en texto ya está en
`CitiBike-Infra/docs/evidence/20261119T183438Z/ie6-gate-bloqueante.txt`. Para la
captura visual, repetir el procedimiento de `CitiBike-Infra/docs/TESTING.md` §6
en una rama de prueba y **cerrar el PR sin mergear** al terminar.

## Recomendaciones

- Recortar solo la zona relevante; evitar datos personales o credenciales.
- Usar formato PNG y un ancho mínimo de 1200 px para que se lea en el PDF.
- Si una captura queda muy grande, dividirla en dos (fila superior/inferior).
- Verificar que el nombre del archivo coincida exactamente con el del informe
  (distingue mayúsculas y minúsculas).
