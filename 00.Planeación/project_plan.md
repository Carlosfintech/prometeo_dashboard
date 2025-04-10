# Proyecto Prometeo Cross Selling

## Introducción

En el contexto de la creciente adopción de Open Banking, las entidades financieras requieren soluciones ágiles que optimicen la venta cruzada de sus productos (p. ej. seguros, tarjetas de crédito, planes de inversión). Para responder de forma veloz y efectiva a estas necesidades, se propone un proyecto de Investigación y Desarrollo (I+D), complementado con design thinking y un enfoque lean, con el fin de generar y validar en apenas 20-24 horas un prototipo que identifique clientes con alta propensión a adquirir un producto financiero adicional. El proyecto abarcará desde la exploración de datos (EDA) y la investigación de mercado/competencia, hasta la creación de un modelo predictivo, su implementación en un dashboard interactivo y la elaboración de un informe ejecutivo con recomendaciones de negocio.

## Descripción

Este proyecto tiene como finalidad construir un prototipo en 20 a 24 horas que permita detectar oportunidades de venta cruzada de productos financieros —por ejemplo, seguros, tarjetas de crédito, inversiones— a partir de datos proporcionados por APIs de Open Banking, bases de datos internas con información de productos contratados y un CRM con datos demográficos. 

**Pregunta clave:**
> ¿Cómo identificar qué clientes tienen mayor probabilidad de adquirir un nuevo producto financiero (ej.: un seguro) con base en su comportamiento transaccional y su perfil?

Para ello, se llevará a cabo un proyecto rápido de I+D que aplicará design thinking y metodologías lean, enfocándose en el desarrollo de modelos y su integración en un dashboard interactivo que permita al equipo de ventas o a los directivos consultar insights y recomendaciones de manera inmediata.

## Objetivos

### Objetivo General

Crear un prototipo integrado (investigación + EDA + modelado + dashboard) para optimizar el cross-selling en Open Banking, alineado a las necesidades de Prometeo, bajo un enfoque de I+D y en un plazo no mayor a 20-24 horas.

### Objetivos Específicos

1. **Observar e Investigar (Fase 1):** Analizar casos de uso del Open Finance, los productos de Prometeo, la competencia, las tendencias mundiales, y explorar los datos disponibles (EDA).  Así mismo,s e investigará las mejores prácticas de venta cruzada en Instituciones Financieras.
2. **Definir y Focalizar (Fase 2):** Precisar KPIs y métricas de interés, y delimitar el alcance del MVP.  
3. **Idear y Diseñar (Fase 3):** Proponer la estrategia de *feature engineering* y la arquitectura conceptual del proyecto.  
4. **Prototipar y Validar (Fase 4):** Implementar el modelo (clasificación + series de tiempo), construir un dashboard e integrarlo con un chat de IA.  
5. **Presentar Conclusiones (Fase 5):** Comunicar los hallazgos, métricas clave y recomendaciones de escalabilidad.  

## Metodología

La propuesta integra un proceso de I+D coherente con el flujo de trabajo de data science, abarcando:

### Fase 0 – Setup

- Configuración inicial del entorno, repositorios y dependencias.

### Fase 1 – Observación e Investigación (incluye EDA)

- Investigación de productos, competidores y tendencias en Open Banking.  
- Análisis Exploratorio de Datos para comprender la distribución y la calidad de la información disponible.

### Fase 2 – Definición y Focalización

- Establecimiento de objetivos concretos, KPIs y alcance del MVP.

### Fase 3 – Ideación y Diseño

- Diseño de la arquitectura analítica y desarrollo de variables clave (*Feature Engineering*).

### Fase 4 – Prototipado y Validación

- Entrenamiento del modelo de clasificación (Random Forest / XGBoost).  
- Implementación de series de tiempo (opcional).  
- Construcción de un dashboard con visualizaciones y un posible chat interactivo.

### Fase 5 – Presentación y Conclusiones

- Generación de un informe ejecutivo (2-3 páginas) con resultados, hallazgos y recomendaciones.

## Fases y Tareas Detalladas

### Fase 0: Setup

**Tarea 0.1:** Configuración Inicial (~1 hora)  
- Repositorio Git/GitHub, estructura de carpetas `/data`, `/notebooks`, `/dashboard`.  
- Instalación de librerías.  
- Herramientas: Git, GitHub, Python, ChatGPT.

---

### Fase 1: Observación e Investigación (EDA)

**Tarea 1.1:** Análisis de Productos/Servicios y Competencia  
- Exploración de APIs, productos y competidores (Belvo, Plaid, Tink).  
- Herramientas: Navegador, ChatGPT/Claude, Google Docs/Notion.

**Tarea 1.2:** Análisis Exploratorio de Datos (EDA)  
- Integración de datos transaccionales, demográficos y de productos contratados.  
- Herramientas: Python (pandas, matplotlib, seaborn), Jupyter/Colab.

---

### Fase 2: Definición y Focalización

**Tarea 2.1:** Alcance, Objetivos y KPIs (~1 hora)  
- Definición de la variable objetivo, métricas de evaluación (AUC-ROC, F1, etc.).  
- Herramientas: Google Docs/Notion, ChatGPT.

---

### Fase 3: Ideación y Diseño

**Tarea 3.1:** *Feature Engineering* y Arquitectura (~2 horas)  
- Ejemplos: `avg_monthly_spend`, `favorite_category`, `ingreso_vs_limite_credito`.  
- Herramientas: Python, Figma/Draw.io, ChatGPT.

---

### Fase 4: Prototipado y Validación

**Tarea 4.1:** Modelado Predictivo (~3-4 horas)  
- Modelos: Random Forest / XGBoost.  
- Evaluación: AUC-ROC, F1, feature importance.  
- Herramientas: Python, Jupyter/Colab.

**Tarea 4.2:** Series de Tiempo (Opcional)  
- Modelo: Prophet o ARIMA para detectar patrones de gasto.  
- Herramientas: Python, Jupyter.

**Tarea 4.3:** Dashboard Interactivo (~3-4 horas)  
- Visualización con lovable, automatización con n8n.  
- Integración con ChatGPT/Claude para consultas naturales.

---

### Fase 5: Presentación y Conclusiones

**Tarea 5.1:** Informe Ejecutivo (~1-2 horas)  
- Resumen de hallazgos, recomendaciones de negocio.  
- Herramientas: Google Slides/Docs, ChatGPT.

---

## Recursos y Tecnologías

- **Lenguaje:** Python (pandas, numpy, scikit-learn, XGBoost, Prophet, statsmodels)  
- **Visualización:** Jupyter/Colab, matplotlib, seaborn  
- **Dashboard:** lovable, n8n, FastAPI (opcional)  
- **Control de Versiones:** Git y GitHub  
- **Documentación:** Google Docs, Notion, Figma/Draw.io

## Cronograma (Estimado ~20 horas)

- Fase 0 (Setup): ~1 hora  
- Fase 1 (Investigación + EDA): ~5-6 horas  
- Fase 2 (Definición y KPIs): ~1 hora  
- Fase 3 (Feature Engineering + Diseño): ~2 horas  
- Fase 4 (Modelado + Dashboard): ~7-8 horas  
- Fase 5 (Informe): ~1-2 horas  

## Limitaciones y Riesgos

- **Tiempo limitado:** Se prioriza un MVP sobre profundidad analítica.  
- **Integraciones técnicas:** lovable, n8n y APIs pueden requerir configuración compleja.  
- **Complejidad del modelo:** Diversidad de productos puede requerir abordaje multicategórico.

## Conclusión

El presente proyecto busca, mediante una combinación de I+D, design thinking y metodologías lean, demostrar en un plazo acotado la viabilidad de una solución de cross-selling alineada al ecosistema de Open Banking. 

Al integrar datos transaccionales, demográficos y de productos financieros, se pretende identificar de manera rápida y confiable qué clientes tienen una mayor propensión a adquirir seguros, tarjetas de crédito, inversiones o cualquier otra oferta financiera.

La construcción de un modelo predictivo, la visualización de insights en un dashboard interactivo y la generación de un informe ejecutivo permitirán que los tomadores de decisión (CEO, equipo de I+D y fuerzas comerciales) evalúen de forma ágil el impacto, la factibilidad y el retorno de inversión de esta iniciativa de venta cruzada. Con ello, se sientan las bases para un despliegue más robusto y escalable en futuros desarrollos.