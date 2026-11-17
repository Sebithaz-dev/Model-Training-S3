# Politica de seguridad

## Versiones soportadas

Se mantiene la rama `main`. Las ramas de features y los PRs se descartan tras
el merge.

## Reportar una vulnerabilidad

No abras un issue publico. Usa **Security > Report a vulnerability** en este
repositorio (GitHub Private Vulnerability Reporting) o escribe a
`sebithaz-dev@users.noreply.github.com` indicando:

- version o commit afectado
- pasos para reproducir
- impacto estimado
- mitigacion sugerida, si la hay

## Controles automatizados

| Control | Herramienta | Donde |
|---|---|---|
| Dependencias vulnerables | Dependabot alerts + Snyk | GitHub + `security.yml` |
| Secretos filtrados | GitHub secret scanning + push protection + gitleaks | GitHub + `security.yml` |
| Calidad y cobertura | SonarCloud (Quality Gate bloqueante) | `security.yml` |
| Imagen de contenedor | Trivy (CVEs HIGH/CRITICAL) | `security.yml` |
| Calidad del modelo | Quality gate (`config/quality_gate.yaml`) | `ml/train.py` |
| Branch protection | Checks requeridos + review obligatorio | GitHub |

Los hallazgos **HIGH/CRITICAL** y las regresiones del modelo detienen el
pipeline (ver `docs/COMPLIANCE.md`).
