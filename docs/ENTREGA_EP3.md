# Entrega EP3 — lo que falta antes de subir el enlace a AVA

Este archivo es solo para el equipo. Todo lo que se podía dejar listo sin una
sesión del Learner Lab ni redacción propia ya está en los repositorios.

## 1. Datos del encabezado (2 min)

En `docs/INFORME_EP3.md`: sección, docente, correo institucional de Diego y
fecha de entrega.

## 2. Una sesión del Learner Lab (≈ 45 min)

Antes de empezar:

- `CitiBike-Infra/terraform/terraform.tfvars`: descomentar `alarm_email` con un
  correo real (se crea solo desde el example si no existe).
- Credenciales del lab en el shell y en los secrets `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY` y `AWS_SESSION_TOKEN` de Flask-Dashboard-S3 y
  Model-Training-S3.

Luego, desde `CitiBike-Infra/`:

```bash
./scripts/sesion_ep3.sh
```

Levanta todo, verifica, genera tráfico, mide un despliegue, provoca la falla
controlada y recolecta la evidencia en `docs/evidence/<fecha>/`. Durante la
falla llega el correo de la alarma (confirmar antes la suscripción SNS que AWS
envía al levantar el entorno).

Con el entorno arriba:

1. Evidencia del gate de seguridad:
   `./scripts/demo_gate_seguridad.sh ../Flask-Dashboard-S3 docs/evidence/<fecha>`
2. Un push cualquiera a `main` de Flask-Dashboard-S3 (por PR) para que corra el
   job `deploy-ecs` y quede su resumen en Actions.
3. Las capturas de `docs/img/README.md`, guardadas en `docs/img/` con esos
   nombres.
4. `./scripts/down.sh`.

Subir la carpeta de evidencia nueva (CitiBike-Infra) y las capturas
(Model-Training-S3) con un PR en cada repo.

## 3. Texto propio, sin IA (la pauta lo exige)

En `docs/INFORME_EP3.md`, los bloques marcados `[COMPLETAR sin IA…]` /
`[COMPLETAR: …]` y la sección 10:

- 1.3 y 2.4: por qué ECS (autorizado por el docente por costo) y qué se gana y
  pierde.
- 3.2: por qué ECS sigue siendo un entorno orquestado.
- 3.3 y 5.2: un ejemplo real de cómo una señal del pipeline o del dashboard
  cambió una decisión.
- 6: cómo aplicaron las políticas y qué control les sirvió más.
- 10.1 conclusiones del equipo; 10.2 y 10.3 una reflexión por integrante.

Después, en la sección 4 (matriz), cambiar IE4 de 🟡 a ✅.

## 4. Revisión final

- La declaración de uso de IA (al inicio del informe) describe el uso real:
  si usaron otras herramientas, agréguenlas; si alguna fila no aplica, bórrenla.
- Que no queden `[COMPLETAR` ni `[VACÍO` en el informe.
- Que las imágenes de `docs/img/` se vean en GitHub.
- Que los tres repositorios sean públicos y los enlaces abran.

## 5. Entrega

- AVA: el enlace
  `https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/docs/INFORME_EP3.md`
  (el informe enlaza a los otros dos repositorios).
- Correo al docente, por ejemplo:

  > Asunto: EP3 DOY0101 — Diego Hernández y Sebastián Escobar
  >
  > Estimado/a profesor/a:
  >
  > Le enviamos el enlace de nuestra Evaluación Parcial 3 de Ingeniería
  > DevOps: https://github.com/Sebithaz-dev/Model-Training-S3/blob/main/docs/INFORME_EP3.md
  >
  > El informe enlaza a los repositorios del proyecto (Model-Training-S3,
  > Flask-Dashboard-S3 y CitiBike-Infra) y a la evidencia de cada indicador.
  >
  > Saludos,
  > Diego Hernández y Sebastián Escobar
