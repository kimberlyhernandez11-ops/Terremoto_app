# 🌍 Terremoto App

Aplicación interactiva desarrollada con **Streamlit** que muestra datos en tiempo real sobre terremotos en **Puerto Rico** y en el **mundo** usando la librería `quakefeeds`.

Es una herramienta educativa y de divulgación que permite explorar la actividad sísmica reciente con filtros y visualizaciones sencillas.

## ✨ Características principales 
- **Filtros dinámicos**:
  - Severidad (todos, significativo, magnitud específica como `2.5`, `4.5`, `1.0`).
  - Periodo: `día`, `semana`, `mes` (cuando se selecciona `mes` se muestran únicamente los eventos del mes y año corrientes en la zona horaria de Puerto Rico).
  - Zona geográfica: `Puerto Rico` o `Mundo` (bounding box para PR).
- **Visualizaciones interactivas**:
  - Mapa con eventos (Mapbox) y popups con magnitud, profundidad y fecha.
  - Histogramas de magnitudes y profundidades.
- **Tabla de eventos**:
  - Muestra fecha y hora (formateadas en español, p. ej. `5 de marzo de 2023, 02:30:00 p. m.`), localización, magnitud y clasificación.
- **Formato y localización**:
  - Los nombres de mes se muestran en español de forma consistente (no dependen del locale del sistema).
  - Fechas y hora se muestran en la zona horaria `America/Puerto_Rico`.
- **Clasificación automática**:
  - Cada evento se etiqueta como *micro*, *menor*, *ligero*, *moderado*, *fuerte*, *mayor*, *épico* o *legendario* según la magnitud.

## 🧪 Pruebas
- Se incluye una prueba simple `tests/test_filters.py` que verifica el filtrado por mes corriente.

## 📋 Requisitos
- Python 3.8 o superior
- Dependencias (ver `requirements.txt`): `streamlit`, `pandas`, `plotly`, `quakefeeds`, `pytz`, `tzdata`, entre otras.

Instalación rápida:
```bash
pip install -r requirements.txt
```

Ejecutar la aplicación:
```bash
streamlit run streamlit_app.py
```

Ejecutar pruebas:
```bash
python -m pytest -q
```

Si encuentras algún comportamiento inesperado al seleccionar `mes`, `Puerto Rico` y una severidad concreta (ej. `2.5`), la app ahora filtra para mostrar solo eventos del mes en curso en la zona horaria de Puerto Rico.
