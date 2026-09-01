# Evaluación Parcial N°1
## Encargo: Tu primer pipeline de despliegue
### Instrucciones y pauta de evaluación — Estudiante

| Sigla | Nombre Asignatura | Tiempo Asignado | % Ponderación |
|---|---|---|---|
| DOY0101 | Ingeniería DevOps | 2 horas pedagógicas | 25% |

---

## 1. Instrucciones generales

**Descripción**

- La Evaluación Parcial 1 corresponde a un encargo elaborado en **parejas** y consiste en la **creación de un repositorio Git** correspondiente a un microservicio previamente desarrollado, con el fin de preparar la base de trabajo para el pipeline DevOps que se construirá durante el semestre.
- Medirá los siguientes **Indicadores de Logro**:
  - **IL1.1** Define estrategias de ramificación y control de versiones utilizando Git u otros sistemas de source control en escenarios colaborativos de desarrollo en la nube, para asegurar trazabilidad del código.
  - **IL1.2** Configura flujos de trabajo DevOps que integren repositorios, automatización y colaboración en un entorno Cloud simulado, para cumplir con los estándares de CI/CD.
  - **IL1.3** Especifica convenciones y buenas prácticas de uso de repositorios mediante documentación técnica en el marco de un proyecto de desarrollo ágil, para facilitar la colaboración y la calidad del código.
- El **tiempo asignado** para desarrollar esta evaluación como encargo es de **3 semanas** y se realiza **en parejas**.
- Iniciarás tu trabajo en el taller de proyectos (**TAITE 7**) con el/la docente, pero debes finalizar el encargo en tu tiempo de trabajo autónomo.

---

## Ítem I: Instrucciones específicas de la Evaluación

- Los/las estudiantes demuestran su dominio en el uso de sistemas de control de versiones y la implementación de estrategias de trabajo colaborativo en entornos DevOps.
- Se evaluará el diseño y la ejecución de un flujo de trabajo que integre **Git, GitHub y GitHub Actions** para control de versiones, automatización y colaboración efectiva.
- Se espera que los/las estudiantes elijan uno de sus **microservicios desarrollados previamente** en ramos anteriores y lo utilicen como base para este trabajo.

### El encargo debe incluir los siguientes apartados:

1. Crean un repositorio Git en GitHub con las siguientes ramas: `main`, `develop`, `feature/<nombre>` y `hotfix/<nombre>`. **(IE5)**
2. Implementan GitFlow o trunk-based development, justificando su elección en el README del repositorio. **(IE1)**
3. Simulan un desarrollo colaborativo integrando al menos 2 cambios tipo *feature* y 1 tipo *hotfix* mediante pull requests. **(IE2)**
4. Documentan en un archivo `README.md` o wiki las convenciones de commits, flujos de merge, naming de ramas y estrategias de revisión. **(IE5)**
5. Configuran al menos una acción básica de GitHub Actions que se ejecute con cada push a `develop` y pull request a `main`. **(IE3/IE4)**

### Aspectos formales

- El encargo se entregará mediante un **enlace en GitHub** del repositorio, el cual se envía a través de **AVA** y al **correo del docente**, en la fecha estipulada.

### Materiales, herramientas o insumos requeridos

- Materiales y contenidos académicos proporcionados durante el curso, incluyendo especificaciones técnicas, análisis previos y guías de referencia.

### Indicaciones para el uso de Inteligencia Artificial (IA)

- **Uso ético:** Los estudiantes pueden utilizar la IA como apoyo para mejorar redacción, buscar referencias o crear diagramas, pero todas las ideas, análisis y justificaciones técnicas deben ser propias del equipo. Se debe declarar en el informe qué herramientas de IA se usaron y cómo se aplicaron.
- **Prohibición en reflexiones críticas:** No se permite el uso de IA para redactar conclusiones, justificaciones técnicas o reflexiones individuales, ya que estas son esenciales para evaluar el aprendizaje y comprensión del equipo.
- **Validación de contenidos:** Todo contenido generado con IA debe ser revisado y validado por los estudiantes, asegurando que sea coherente con los requerimientos del proyecto. Se recomienda el uso de herramientas antiplagio para garantizar originalidad.
- **Reflexiones individuales obligatorias:** Cada integrante debe incluir en la sección de conclusiones una reflexión personal, redactada sin apoyo de IA, explicando su aprendizaje y contribución al proyecto.
- Todo uso de IA debe ser citado: https://bibliotecas.duoc.cl/ia

---

## 2. Pauta de Evaluación

### Escala general de niveles de logro

| Categoría | % logro | Descripción |
|---|---|---|
| Muy buen desempeño | 100% | Demuestra un desempeño destacado, evidenciando el logro de todos los aspectos evaluados en el indicador. |
| Buen desempeño | 80% | Demuestra un alto desempeño del indicador, presentando pequeñas omisiones, dificultades y/o errores. |
| Desempeño aceptable | 60% | Demuestra un desempeño competente, evidenciando el logro de los elementos básicos del indicador, pero con omisiones, dificultades o errores. |
| Desempeño incipiente | 30% | Presenta importantes omisiones, dificultades o errores en el desempeño, que no permiten evidenciar los elementos básicos del logro del indicador, por lo que no puede ser considerado competente. |
| Desempeño no logrado | 0% | Presenta ausencia o incorrecto desempeño. |

### Rúbrica detallada por indicador

#### IE1. Identifica diferentes modelos de ramificación y su aplicabilidad en contextos colaborativos en la nube. *(Ponderación: 15%)*

| Nivel | Descripción |
|---|---|
| Muy buen desempeño (100%) | Identifica con precisión diversos modelos de ramificación (Git Flow, GitHub Flow, trunk-based, entre otros), explicando claramente su aplicabilidad y ventajas en contextos colaborativos en la nube. |
| Buen desempeño (80%) | Identifica al menos dos modelos de ramificación y describe correctamente su aplicación en entornos colaborativos en la nube. |
| Desempeño aceptable (60%) | Identifica modelos de ramificación básicos y entrega una descripción general de su uso, con ejemplos parciales o poco específicos. |
| Desempeño incipiente (30%) | Identifica al menos un modelo de ramificación, pero con errores o sin vincularlo adecuadamente a contextos colaborativos. |
| Desempeño no logrado (0%) | No logra identificar modelos de ramificación ni su aplicabilidad en contextos colaborativos. |

#### IE2. Simula un flujo de trabajo colaborativo donde aplica correctamente comandos de Git (clone, commit, push, pull, merge, etc.) documentando la trazabilidad del código fuente. *(Ponderación: 15%)*

| Nivel | Descripción |
|---|---|
| Muy buen desempeño (100%) | Simula eficazmente un flujo colaborativo usando comandos Git adecuados, documentando con precisión cada etapa de trazabilidad del código. |
| Buen desempeño (80%) | Simula correctamente un flujo de trabajo colaborativo básico con comandos Git y presenta documentación general de la trazabilidad. |
| Desempeño aceptable (60%) | Simula parcialmente un flujo colaborativo, con algunos comandos mal aplicados o documentación limitada de los cambios. |
| Desempeño incipiente (30%) | Simula de forma incorrecta varios comandos Git y no documenta de manera adecuada la trazabilidad. |
| Desempeño no logrado (0%) | No realiza una simulación de flujo colaborativo o no emplea comandos Git pertinentes. |

#### IE3. Implementa un flujo de trabajo DevOps básico que automatice la integración de cambios desde un repositorio Git en un entorno cloud simulado. *(Ponderación: 25%)*

| Nivel | Descripción |
|---|---|
| Muy buen desempeño (100%) | Implementa un flujo de trabajo DevOps básico completamente funcional, automatizando de forma precisa la integración de cambios desde un repositorio Git en un entorno cloud simulado, sin errores y con documentación clara. |
| Buen desempeño (80%) | Implementa un flujo de trabajo DevOps básico que automatiza adecuadamente la integración de cambios desde un repositorio Git en un entorno cloud simulado, con mínimas observaciones. |
| Desempeño aceptable (60%) | Implementa un flujo de trabajo DevOps básico que automatiza parcialmente la integración de cambios desde un repositorio Git, aunque presenta fallos menores o falta de coherencia en el entorno cloud simulado. |
| Desempeño incipiente (30%) | Implementa un flujo de trabajo DevOps básico con errores importantes en la automatización o en la conexión entre el repositorio Git y el entorno cloud simulado. |
| Desempeño no logrado (0%) | No implementa un flujo de trabajo DevOps básico o la automatización de integración de cambios desde un repositorio Git no está presente. |

#### IE4. Configura herramientas de automatización (GitHub Actions, GitLab CI o similares), explicando su rol en los procesos CI/CD. *(Ponderación: 25%)*

| Nivel | Descripción |
|---|---|
| Muy buen desempeño (100%) | Configura herramientas de automatización de forma completa y funcional, y explica con claridad y precisión su rol dentro del proceso CI/CD, contextualizando su utilidad en un flujo de desarrollo real. |
| Buen desempeño (80%) | Configura herramientas de automatización correctamente, y explica de manera adecuada su rol en los procesos CI/CD, aunque con detalles menores por mejorar. |
| Desempeño aceptable (60%) | Configura herramientas de automatización con limitaciones o errores menores, y entrega una explicación básica pero comprensible de su función en CI/CD. |
| Desempeño incipiente (30%) | Configura herramientas de automatización de forma incompleta o incorrecta, y explica su rol en CI/CD de manera poco clara o con errores de concepto. |
| Desempeño no logrado (0%) | No configura herramientas de automatización, ni explica su función dentro de los procesos CI/CD. |

#### IE5. Elabora una guía de buenas prácticas para el uso de repositorios en equipos DevOps, incluyendo naming de ramas, mensajes de commit, estructuras de carpetas y control de versiones. *(Ponderación: 20%)*

| Nivel | Descripción |
|---|---|
| Muy buen desempeño (100%) | Elabora una guía de buenas prácticas completa, clara y aplicable, que incluye de forma precisa todos los aspectos solicitados: naming de ramas, mensajes de commit, estructuras de carpetas y control de versiones. |
| Buen desempeño (80%) | Elabora una guía de buenas prácticas bien estructurada, abarcando la mayoría de los aspectos solicitados con recomendaciones claras y funcionales. |
| Desempeño aceptable (60%) | Elabora una guía de buenas prácticas con algunos aspectos desarrollados de forma parcial o superficial, pero que ofrece lineamientos utilizables. |
| Desempeño incipiente (30%) | Elabora una guía de buenas prácticas incompleta, con recomendaciones generales o confusas, omitiendo varios elementos clave. |
| Desempeño no logrado (0%) | No elabora una guía de buenas prácticas, o el contenido presentado no es pertinente ni aplicable. |

**Total: 100%**
