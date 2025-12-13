import streamlit as st
import pandas as pd
import plotly.express as px
from quakefeeds import QuakeFeed
from datetime import datetime
import locale # Importar el módulo locale

# Configurar la página para usar el ancho completo
st.set_page_config(layout="wide")

# Configurar la localización a español para el formato de fecha.
# Esto asegura que los nombres de los meses salgan en español (e.g., Noviembre en lugar de November).
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    # Si 'es_ES.UTF-8' no está disponible (común en algunos entornos), probar con otras variantes
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        # Fallback si ninguna configuración de español funciona (puede mostrar meses en inglés)
        pass  


# --- TÍTULOS CENTRALIZADOS ---
st.markdown("<h1 style='text-align: center; '>Terremoto App</h1>", unsafe_allow_html=True) 
st.markdown("<h2 style='text-align: center;'>Datos en Tiempo Real de los Terremotos en Puerto Rico y en el Mundo</h2>", unsafe_allow_html=True)

token_id = "pk.eyJ1IjoibWVjb2JpIiwiYSI6IjU4YzVlOGQ2YjEzYjE3NTcxOTExZTI2OWY3Y2Y1ZGYxIn0.LUg7xQhGH2uf3zA57szCyw"

px.set_mapbox_access_token(token_id)

# --- Filtro de Magnitud Mínima ---

# Diccionario para mapear las etiquetas de la interfaz (en español) a los valores de la API (en inglés)
severity_options = {
    "todos": "all", # Etiqueta simplificada
    "significativo": "significant",
    "4.5": "4.5",
    "2.5": "2.5",
    "1.0": "1.0"
}

# Selectbox en la barra lateral para elegir la severidad
selected_severity_label = st.sidebar.selectbox(
    "Selecciona la Magnitud Mínima:",
    list(severity_options.keys()),
    index=0 # 'todos' como default
)

# Obtener el valor de la API correspondiente
min_mag_api_value = severity_options[selected_severity_label]

st.sidebar.divider() # Divisor después del filtro de Magnitud

# --- Filtro de Periodo de Tiempo ---

# Diccionario para mapear las etiquetas de tiempo (en español) a los valores de la API (en inglés)
time_options = {
    "mes": "month", # Etiqueta simplificada
    "semana": "week",
    "día": "day"
}

# Selectbox en la barra lateral para elegir el periodo de tiempo
selected_time_label = st.sidebar.selectbox(
    "Selecciona el Periodo de Tiempo:",
    list(time_options.keys()),
    index=0 # 'mes' como default
)

# Obtener el valor de la API correspondiente
time_period_api_value = time_options[selected_time_label]

st.sidebar.divider() # Divisor después del filtro de Periodo

# --- Filtro de Zona Geográfica ---

# Diccionario para mapear las etiquetas de zona a sus parámetros de mapa (lat, lon, zoom)
geo_options = {
    "Puerto Rico": {"lat": 18.25178, "lon": -66.254512, "zoom": 7.5},
    "Mundo": {"lat": 0, "lon": 0, "zoom": 1.0}
}

# Selectbox en la barra lateral para elegir la zona geográfica
selected_geo_label = st.sidebar.selectbox(
    "Selecciona la Zona Geográfica:",
    list(geo_options.keys()),
    index=0 # 'Puerto Rico' como default
)

# Obtener los parámetros de centro y zoom
map_params = geo_options[selected_geo_label]

st.sidebar.divider() # Divisor después del filtro de Zona Geográfica

# --- Checkbox para Mostrar Mapa ---
show_map = st.sidebar.checkbox("Mostrar Mapa", value=True)

st.sidebar.divider() # Divisor después del checkbox de Mapa

# --- Checkbox y Slider para Mostrar Tabla ---
show_table = st.sidebar.checkbox("Mostrar tabla con eventos", value=False)

num_events = 0
if show_table:
    # Slider que aparece solo si el checkbox está marcado
    num_events = st.sidebar.slider(
        "Cantidad de eventos a mostrar (Tabla):",
        min_value=5,
        max_value=20,
        value=5,
        step=1
    )

# --- Información del Desarrollador ---
st.sidebar.divider() # Añade un separador visual antes de la información
st.sidebar.markdown(""" Aplicacion desarrollada por:<br> <i>Kimberly M. Hernandez <br>
                     INGE3016<br>Universidad de Puerto Rico</i>""",
                    unsafe_allow_html=True)


def generaTabla(min_mag_filter, time_period_filter):
    
    # Se usan ambos filtros en la llamada a QuakeFeed
    feed = QuakeFeed(min_mag_filter, time_period_filter)

    longitudes = [feed.location(i)[0] for i in range(len(feed))]
    
    latitudes = [feed.location(i)[1] for i in range(len(feed))]
    
    date = list(feed.event_times)
    
    depths = list(feed.depths)
    
    places = list(feed.places)
    
    magnitudes = list(feed.magnitudes)
    
    df = pd.DataFrame([date,longitudes,latitudes,places,magnitudes,depths]).transpose()
    
    df.columns = ["fecha","lon","lat","loc","mag","prof"]
    
    # Conversión a numérico (como estaba originalmente)
    df["lat"] = pd.to_numeric(df["lat"])
    df["lon"] = pd.to_numeric(df["lon"])
    df["mag"] = pd.to_numeric(df["mag"])
    df["prof"] = pd.to_numeric(df["prof"])
    
    # --- FILTRO PARA ELIMINAR MAGNITUDES NEGATIVAS ---
    # Esto resuelve el error en Plotly ya que 'size' debe ser positivo.
    df = df[df['mag'] >= 0]

    # 1. Asegurar que 'fecha' sea datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # 2. Corregir la zona horaria (UTC -> AST):
    # El error "Already tz-aware" ocurre si tz_localize se llama en una serie que ya tiene zona horaria.
    # Se añade una comprobación para aplicar tz_localize solo si es tz-naive (no tiene zona horaria).
    if df['fecha'].dt.tz is None:
        # Si no es consciente (tz-naive), la localizamos a UTC (la zona de origen de los datos de USGS)
        df['fecha'] = df['fecha'].dt.tz_localize('UTC')
        
    # Ahora que la columna es definitivamente tz-aware, la convertimos a la hora local de Puerto Rico (AST).
    df['fecha'] = df['fecha'].dt.tz_convert('America/Puerto_Rico')
    
    # ACTUALIZACIÓN: Incluir la hora exacta del evento
    # '%#d' elimina el cero inicial. '%B' es el nombre completo del mes.
    # '%I:%M:%S %p' añade la hora, minutos, segundos y AM/PM.
    df['fecha'] = df['fecha'].dt.strftime('%#d de %B de %Y, %I:%M:%S %p')
    
    # 3. Añadir la columna de Clasificación según la escala de Richter
    def classify_magnitude(mag):
        if mag < 2.0:
            return "micro"
        elif 2.0 <= mag <= 3.9:
            return "menor"
        elif 4.0 <= mag <= 4.9:
            return "ligero"
        elif 5.0 <= mag <= 5.9:
            return "moderado"
        elif 6.0 <= mag <= 6.9:
            return "fuerte"
        elif 7.0 <= mag <= 7.9:
            return "mayor"
        elif 8.0 <= mag <= 9.9:
            return "épico"
        else: # 10.0 o más
            return "legendario"
    
    df['clasificacion'] = df['mag'].apply(classify_magnitude)
    
    return df

def generaMapa(df, map_params):

    # CAMBIO: Se usa una escala de color sequential (Magma) para reflejar mejor la intensidad (rojo = fuerte)
    fig = px.scatter_mapbox(df,
                            lat="lat",
                            lon="lon",
                            color="mag",
                            size="mag",
                            hover_name="loc",
                            hover_data={"mag":True,
                                        "prof":True,
                                        "lat":True,
                                        "lon":True,
                                        "fecha":True},
                            color_continuous_scale=px.colors.cyclical.IceFire, # Nueva escala de color
                            size_max=8,
                            opacity=0.5, # Aumenta un poco la opacidad para Magma
                            center=dict(lat=map_params["lat"], lon=map_params["lon"]), # Centro dinámico
                            mapbox_style="dark", 
                            zoom=map_params["zoom"]) # Zoom dinámico
    
    return fig

def generaHistMag(df):
    
    # Se agrega el parámetro 'labels' para cambiar el nombre del eje x
    fig = px.histogram(df,
                        x="mag",
                        color_discrete_sequence=["red"],
                        labels={"mag": "Magnitudes"}) # Eje X actualizado
    
    return fig

def generaHistProf(df):
    
    fig = px.histogram(df,
                        x="prof",
                        color_discrete_sequence=["red"],
                        labels={"prof": "Profundidades"}) # Eje X actualizado
    
    return fig


# Llamada a la función con ambos valores de selectbox
df = generaTabla(min_mag_api_value, time_period_api_value)

# --- CÁLCULO DE ESTADÍSTICAS ---
total_events = len(df)
# Prevenir error si no hay eventos después del filtro
avg_magnitude = df["mag"].mean() if total_events > 0 else 0
avg_depth = df["prof"].mean() if total_events > 0 else 0
# Formatear la fecha de la petición con nombres de meses en español y AM/PM.
current_date = datetime.now().strftime("%#d de %B de %Y, %I:%M:%S %p")

# Divisor solicitado para separar título y estadísticas
st.divider()

# --- Estadísticas (Formato Centralizado SIN RECUADRO) ---
col_left, col_center, col_right = st.columns([1, 1.5, 1])

with col_center:
    if total_events > 0:
        # Se deja el texto centrado con un poco de margen.
        stats_html = f"""
        <div style='text-align: center; margin-bottom: 20px;'> 
            <p style='margin: 0;'><strong>Fecha de petición:</strong> {current_date}</p>
            <p style='margin: 0;'><strong>Cantidad de eventos:</strong> {total_events}</p>
            <p style='margin: 0;'><strong>Promedio de magnitudes:</strong> {avg_magnitude:.2f}</p>
            <p style='margin: 0;'><strong>Promedio de profundidades:</strong> {avg_depth:.2f} km</p>
        </div>
        """
        st.markdown(stats_html, unsafe_allow_html=True)


# Divisor para separar estadísticas de la tabla/mapa
st.divider()

# --- Tabla DataFrame (Debajo de las estadísticas) ---

# Se muestra la tabla de datos si el checkbox está marcado 
if show_table and num_events > 0:
    
    # 1. Tomar los primeros N eventos
    df_to_display = df.head(num_events).copy()
    
    # 2. Resetear el índice para que empiece en 0
    # drop=False mantiene la columna de índice actual (0, 1, 2, ...)
    df_to_display = df_to_display.reset_index(drop=True)
    
    # 3. Sumarle 1 al índice para que empiece en 1
    df_to_display.index = df_to_display.index + 1
    
    # 4. Seleccionar, renombrar y mostrar solo las columnas requeridas
    st.dataframe(
        df_to_display[['fecha', 'loc', 'mag', 'clasificacion']].rename(columns={
            'fecha': 'Fecha y Hora (AST)', # Título actualizado
            'loc': 'Localización',
            'mag': 'Magnitud',
            'clasificacion': 'Clasificación'
        }),
        use_container_width=True # Ajustar la tabla al ancho del contenedor
    )
    
    st.divider() # Divisor después de la tabla

# --- Mapa e Histogramas (Estructura de tres columnas para alineación horizontal) ---

# Chequear si hay datos para graficar
if total_events > 0: 
    
    # Columnas: Hist. Mag (1.5), Hist. Prof (1.5), Mapa (3) -> Ratio ajustado a [1.5, 1.5, 3] (25%, 25%, 50%)
    hist_mag_col, hist_prof_col, map_container = st.columns([1.5, 1.5, 3])

    with hist_mag_col:
        # Encabezado centralizado y pequeño (h6)
        st.markdown("<h6 style='text-align: center;'>Histograma de Magnitudes</h6>", unsafe_allow_html=True)
        # CAMBIO CLAVE: Usar st.plotly_chart()
        st.plotly_chart(generaHistMag(df), use_container_width=True)

    with hist_prof_col:
        # Encabezado centralizado y pequeño (h6)
        st.markdown("<h6 style='text-align: center;'>Histograma de Profundidades</h6>", unsafe_allow_html=True)
        # CAMBIO CLAVE: Usar st.plotly_chart()
        st.plotly_chart(generaHistProf(df), use_container_width=True)

    with map_container:
        if show_map:
            # CAMBIO CLAVE: Usar st.plotly_chart()
            st.plotly_chart(generaMapa(df, map_params), use_container_width=True)

else:
    st.warning("No hay datos de terremotos positivos para los filtros seleccionados.")