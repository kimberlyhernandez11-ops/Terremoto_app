import streamlit as st
import pandas as pd
import plotly.express as px
from quakefeeds import QuakeFeed
from datetime import datetime
import locale 
import pytz

####################
## Ajuste del layout
#################### 
st.set_page_config(layout="wide")

###############
## Localización
###############

# Configurar la localización a español para el formato de fecha.
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    # Si 'es_ES.UTF-8' no está disponible, probar con otras variantes.
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        # Fallback si ninguna configuración de español funciona (puede mostrar meses en inglés).
        pass  

###############################    
## Formateo de fecha en español
###############################

# Lista de meses en español para formateo independiente de la configuración del sistema.
SPANISH_MONTHS = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
    7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def format_spanish_datetime(dt):
    """Formatea un datetime en español: 'D de <mes> de YYYY, hh:mm:ss a. m./p. m.'"""
    if dt is None:
        return ''

    # Asegurar que la hora esté en la zona de Puerto Rico.
    try:
        tz = pytz.timezone('America/Puerto_Rico')
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
    except Exception:
        # Si falla la localización, continuar con la fecha tal cual.
        pass

    day = dt.day
    month_name = SPANISH_MONTHS.get(dt.month, '')
    year = dt.year
    time_str = dt.strftime('%I:%M:%S %p').replace('AM', 'a. m.').replace('PM', 'p. m.')

    return f"{day} de {month_name} de {year}, {time_str}"


def filter_df_to_current_month(df, tz_name='America/Puerto_Rico'):
    """Filtra rows del DataFrame para que pertenezcan al mes y año corrientes
    en la zona horaria indicada. Se asume que `df['fecha']` es tz-aware o
    al menos tiene información de fecha que puede usarse con `dt.month`.
    """
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        return df[(df['fecha'].dt.month == now.month) & (df['fecha'].dt.year == now.year)]
    except Exception:
        # En caso de error, devolver el DataFrame sin cambios para no romper la app.
        return df

###############################
## Titulos del app centralizado
###############################

st.markdown("<h2 style='text-align: center;'>Datos en Tiempo Real de los Terremotos en Puerto Rico y en el Mundo</h2>", unsafe_allow_html=True)

token_id = "pk.eyJ1IjoibWVjb2JpIiwiYSI6IjU4YzVlOGQ2YjEzYjE3NTcxOTExZTI2OWY3Y2Y1ZGYxIn0.LUg7xQhGH2uf3zA57szCyw" # Toke id de Mapbox

px.set_mapbox_access_token(token_id)

###########################################################
## Límites del 'Bounding Box' para la región de Puerto Rico
###########################################################

# Esto filtra los datos a eventos dentro de esta caja geográfica.
PR_BOUNDS = {
    "min_lat": 16.5,
    "max_lat": 20.0,
    "min_lon": -68.0,
    "max_lon": -64.0
}

#########################
## Filtros para Severidad 
#########################

# Diccionario para mapear las etiquetas de la interfaz (en español) a los valores de la API (en inglés).
severity_options = {
    "todos": "all", 
    "significativo": "significant",
    "4.5": "4.5",
    "2.5": "2.5",
    "1.0": "1.0"
}

# Selectbox en la barra lateral para elegir la severidad.
selected_severity_label = st.sidebar.selectbox(
    "Severidad:",
    list(severity_options.keys()),
    index=0 
)

# Obtener el valor de la API correspondiente.
min_mag_api_value = severity_options[selected_severity_label]

st.sidebar.divider() # Divisor después del filtro de Severidad.

#######################
## Filtros para Periodo
#######################

# Diccionario para mapear las etiquetas de tiempo (en español) a los valores de la API (en inglés).
time_options = {
    "mes": "month", 
    "semana": "week",
    "día": "day"
}

# Selectbox en la barra lateral para elegir el periodo.
selected_time_label = st.sidebar.selectbox(
    "Periodo:",
    list(time_options.keys()),
    index=0 
)

# Obtener el valor de la API correspondiente.
time_period_api_value = time_options[selected_time_label]

st.sidebar.divider() # Divisor después del filtro de Periodo.

###############################
## Filtros para Zona Geográfica 
###############################

# Diccionario para mapear las etiquetas de zona a sus parámetros de mapa (lat, lon, zoom).
geo_options = {
    "Puerto Rico": {"lat": 18.25178, "lon": -66.254512, "zoom": 7.5},
    "Mundo": {"lat": 0, "lon": 0, "zoom": 1.0}
}

# Selectbox en la barra lateral para elegir la zona geográfica.
selected_geo_label = st.sidebar.selectbox(
    "Zona Geográfica:",
    list(geo_options.keys()),
    index=0 
)

# Obtener los parámetros de centro y zoom.
map_params = geo_options[selected_geo_label]

st.sidebar.divider() # Divisor después del filtro de Zona Geográfica.

#############################
## Checkbox para Mostrar Mapa
#############################

show_map = st.sidebar.checkbox("Mostrar Mapa", value=True)

st.sidebar.divider() # Divisor después del checkbox de Mapa.

#######################################
## Checkbox y Slider para Mostrar Tabla
#######################################

show_table = st.sidebar.checkbox("Mostrar tabla con eventos", value=False)

num_events = 0
if show_table:
    # Slider que aparece solo si el checkbox está marcado.
    num_events = st.sidebar.slider(
        "Cantidad de eventos a mostrar (Tabla):",
        min_value=5,
        max_value=20,
        value=5,
        step=1
    )

################################
## Información del Desarrollador
################################

st.sidebar.divider() # Añade un separador visual antes de la información.
st.sidebar.markdown(""" Aplicación desarrollada por:<br> <i>Kimberly M. Hernandez <br>
                     INGE3016<br>Universidad de Puerto Rico</i>""",
                    unsafe_allow_html=True)

##################################
## Obtención de datos de Terremoto
##################################

def generaTabla(min_mag_filter, time_period_filter, selected_geo_label, selected_severity_label):
    
    # Obtención de datos de Terremoto (API) - La API trae >= min_mag.
    feed = QuakeFeed(min_mag_filter, time_period_filter)
    
    longitudes = [feed.location(i)[0] for i in range(len(feed))] # Lista de longitud (Eje X)
    
    latitudes = [feed.location(i)[1] for i in range(len(feed))] # Lista de latitud (Eje Y)
    
    date = list(feed.event_times) # Lista de las fechas y horas del evento
    
    depths = list(feed.depths) # Lista de las profundidades (en km)
    
    places = list(feed.places) # Lista de las ubicaciones
    
    magnitudes = list(feed.magnitudes) # Lista de las magnitudes (escala Richter)
    
    df = pd.DataFrame([date,longitudes,latitudes,places,magnitudes,depths]).transpose() # Creación del DataFrame Inicial
    
    df.columns = ["fecha","lon","lat","loc","mag","prof"] # Nombres de columnas
    
    # Conversión a numérico.
    df["lat"] = pd.to_numeric(df["lat"])
    df["lon"] = pd.to_numeric(df["lon"])
    df["mag"] = pd.to_numeric(df["mag"])
    df["prof"] = pd.to_numeric(df["prof"])

    ######################
    ## Filtro de Severidad
    ######################
    
    # Se usa una tolerancia de +/- 0.05 para capturar valores muy cercanos a la magnitud seleccionada.
    if selected_severity_label in ["1.0", "2.5", "4.5"]:
        # Convertir la etiqueta seleccionada a flotante
        exact_mag = float(selected_severity_label)
        
        # Definir el rango de tolerancia.
        tolerance = 0.05 
        
        # Filtrar solo si la magnitud está dentro del rango estricto [exact_mag - tolerance, exact_mag + tolerance].
        df = df[
            (df['mag'] >= exact_mag - tolerance) & 
            (df['mag'] <= exact_mag + tolerance)
        ]
        
        # Si es "significativo", se aplica un umbral mínimo (e.g., 5.0).
    elif selected_severity_label == "significativo":
        # Se define "significativo" como cualquier evento de magnitud 5.0 o superior.
        min_significant_mag = 5.0
        
        # Filtro para solo mostrar eventos >= 5.0.
        df = df[df['mag'] >= min_significant_mag]
    
    # Aplicar Filtro Geográfico (Puerto Rico Bounding Box)
    if selected_geo_label == "Puerto Rico":
        PR_BOUNDS = {
            "min_lat": 16.5, "max_lat": 20.0,
            "min_lon": -68.0, "max_lon": -64.0
        }
        
        df = df[
            (df['lat'] >= PR_BOUNDS['min_lat']) & 
            (df['lat'] <= PR_BOUNDS['max_lat']) &
            (df['lon'] >= PR_BOUNDS['min_lon']) &
            (df['lon'] <= PR_BOUNDS['max_lon'])
        ]
        
    ############################################
    ## Filtro para eliminar magnitudes negativas
    ############################################
    
    df = df[df['mag'] >= 0]

    # Procesamiento de Fecha y Hora 
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    if df['fecha'].dt.tz is None:
        df['fecha'] = df['fecha'].dt.tz_localize('UTC')
        
    df['fecha'] = df['fecha'].dt.tz_convert('America/Puerto_Rico')

    # Si el usuario seleccionó "mes", filtrar solo los eventos del mes y año
    # corrientes en la zona horaria de Puerto Rico (evita considerar últimos 30 días).
    if time_period_filter == 'month':
        df = filter_df_to_current_month(df, tz_name='America/Puerto_Rico')

    # Formatear cada fecha en español usando la función de ayuda para evitar depender de locale.
    df['fecha'] = df['fecha'].apply(lambda d: format_spanish_datetime(d.to_pydatetime() if hasattr(d, 'to_pydatetime') else d))
    
    #####################################################
    ## Clasificación según la escala de Richter (columna)
    #####################################################
    
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
        else:
            return "legendario"
    
    df['clasificacion'] = df['mag'].apply(classify_magnitude)
    
    return df

#################################
## Mapa de Puerto Rico y el mundo
#################################

def generaMapa(df, map_params):

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
                            color_continuous_scale=px.colors.cyclical.IceFire, 
                            size_max=8,
                            opacity=0.5,
                            center=dict(lat=map_params["lat"], lon=map_params["lon"]), # Centro dinámico
                            mapbox_style="dark", 
                            zoom=map_params["zoom"]) # Zoom dinámico
    
    return fig

###########################
## Histograma de magnitudes
###########################

def generaHistMag(df):
    
    fig = px.histogram(df,
                        x="mag",
                        color_discrete_sequence=["red"],
                        labels={"mag": "Magnitudes"}) 
    
    fig.update_xaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
    
    return fig

##############################
## Histograma de profundidades
##############################

def generaHistProf(df):
    
    fig = px.histogram(df,
                        x="prof",
                        color_discrete_sequence=["red"],
                        labels={"prof": "Profundidades"}) 
    
    fig.update_xaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
    
    return fig


# Llamada a la función con valores de selectbox.
df = generaTabla(min_mag_api_value, time_period_api_value, selected_geo_label, selected_severity_label)

##########################
## Calculo de estadisticas
##########################

total_events = len(df)
# Prevenir error si no hay eventos después del filtro.
avg_magnitude = df["mag"].mean() if total_events > 0 else 0
avg_depth = df["prof"].mean() if total_events > 0 else 0
# Formatear la fecha de la petición con nombres de meses en español y AM/PM.
# Usar la zona horaria de Puerto Rico para la fecha actual y formatearla en español.
now = datetime.now()
try:
    now = pytz.timezone('America/Puerto_Rico').localize(now)
except Exception:
    try:
        now = now.astimezone(pytz.timezone('America/Puerto_Rico'))
    except Exception:
        pass
current_date = format_spanish_datetime(now)

# Divisor para separar título y estadísticas.
st.divider()

######################################
## Estadísticas (Formato Centralizado)
######################################
 
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


# Divisor para separar estadísticas de la tabla/mapa.
st.divider()

###############################################
## Tabla DataFrame (Debajo de las estadísticas)
###############################################

# Se muestra la tabla de datos si el checkbox está marcado.
if show_table and num_events > 0:
    
    # Tomar los primeros N eventos.
    df_to_display = df.head(num_events).copy()
    
    # Resetear el índice para que empiece en 0.
    df_to_display = df_to_display.reset_index(drop=True)
    
    # Sumarle 1 al índice para que empiece en 1
    df_to_display.index = df_to_display.index + 1
    
    # Seleccionar y mostrar las columnas requeridas.
    st.dataframe(
        df_to_display[['fecha', 'loc', 'mag', 'clasificacion']].rename(columns={
            'fecha': 'Fecha y Hora', 
            'loc': 'Localización',
            'mag': 'Magnitud',
            'clasificacion': 'Clasificación'
        }),
        use_container_width=True # Ajustar la tabla al ancho del contenedor.
    )
    
    st.divider() # Divisor después de la tabla.

##############################################################################
## Mapa e Histogramas (Estructura de tres columnas para alineación horizontal)
##############################################################################

# Chequear si hay datos para graficar.
if total_events > 0: 
    
    # Columnas: Hist. Mag (1.5), Hist. Prof (1.5), Mapa (3) -> Ratio ajustado a [1.5, 1.5, 3] (25%, 25%, 50%).
    hist_mag_col, hist_prof_col, map_container = st.columns([1.5, 1.5, 3])

    with hist_mag_col:
        # Encabezado centralizado y pequeño (h6)
        st.markdown("<h6 style='text-align: center;'>Histograma de Magnitudes</h6>", unsafe_allow_html=True)
        st.plotly_chart(generaHistMag(df), use_container_width=True)

    with hist_prof_col:
        # Encabezado centralizado.
        st.markdown("<h6 style='text-align: center;'>Histograma de Profundidades</h6>", unsafe_allow_html=True)
        st.plotly_chart(generaHistProf(df), use_container_width=True)

    with map_container:
        if show_map:
            st.plotly_chart(generaMapa(df, map_params), use_container_width=True)

else:
    st.warning("No hay datos de terremotos positivos para los filtros seleccionados.")