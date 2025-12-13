# 🌍 Terremoto App

Aplicación interactiva desarrollada con **Streamlit** que muestra datos en tiempo real sobre terremotos en **Puerto Rico** y en el **mundo**, utilizando la API de USGS a través de la librería `quakefeeds`.

La aplicación está pensada como una herramienta educativa y de divulgación científica, que permite a estudiantes, investigadores y público general visualizar de manera sencilla y atractiva la actividad sísmica reciente. Con una interfaz intuitiva y filtros personalizables, el usuario puede explorar la información de acuerdo con sus intereses.

## ✨ Características principales
- **Filtros dinámicos**:
  - Severidad del evento (micro, menor, moderado, fuerte, etc.).
  - Periodo de tiempo (día, semana, mes).
  - Zona geográfica (Puerto Rico o mundo).
- **Visualizaciones interactivas**:
  - Mapa con eventos sísmicos en tiempo real (Mapbox).
  - Histogramas de magnitudes y profundidades.
- **Tabla de eventos**:
  - Lista de los últimos terremotos con fecha, localización, magnitud y clasificación según la escala de Richter.
- **Estadísticas rápidas**:
  - Cantidad total de eventos.
  - Promedio de magnitudes.
  - Promedio de profundidades.
- **Clasificación automática**:
  - Cada evento se categoriza en niveles como *micro*, *menor*, *moderado*, *fuerte*, *mayor*, *épico* o *legendario*.

## 📋 Requisitos
- Python 3.8 o superior.
- Librerías necesarias:
  - `streamlit`
  - `pandas`
  - `plotly`
  - `quakefeeds`
  - `locale`

Instalación rápida:
```bash
pip install streamlit pandas plotly quakefeeds
