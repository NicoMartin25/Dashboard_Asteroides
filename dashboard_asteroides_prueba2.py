import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import numpy as np


#pip install streamlit requests pandas plotly

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard de Asteroides NASA", layout="wide")

# --- ENCABEZADO ---
st.markdown("<h1 style='text-align:center; color:#00BFFF;'>☄️ Dashboard de Asteroides Prueba n°1 </h1>", unsafe_allow_html=True)
st.write("Visualización interactiva de datos de la NASA sobre asteroides cercanos a la Tierra.")

# --- PANEL LATERAL ---
st.sidebar.header("🔧 Configuración")
api_key = st.sidebar.text_input("Tu API Key de NASA:  (usa esta api de prueba: cYbxAv1a6gfBqtAj4xzMhwADzuKWfOYf8uptv5jD ")
start_date = st.sidebar.date_input("Fecha de inicio")
end_date = st.sidebar.date_input("Fecha de fin")

# --- BOTÓN PARA OBTENER DATOS ---
if st.sidebar.button("Obtener datos"):
    with st.spinner("Cargando datos desde la NASA..."):
        url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
        res = requests.get(url)

        if res.status_code == 200:
            data = res.json()
            asteroids = []

            # --- PROCESAR DATOS ---
            for date, items in data["near_earth_objects"].items():
                for a in items:
                    approach = a["close_approach_data"][0]
                    asteroids.append({
                        "fecha": date,
                        "nombre": a["name"],
                        "diámetro_min_km": a["estimated_diameter"]["kilometers"]["estimated_diameter_min"],
                        "diámetro_max_km": a["estimated_diameter"]["kilometers"]["estimated_diameter_max"],
                        "peligroso": a["is_potentially_hazardous_asteroid"],
                        "velocidad_km_h": float(approach["relative_velocity"]["kilometers_per_hour"]),
                        "distancia_lunar": float(approach["miss_distance"]["lunar"])
                    })

            df = pd.DataFrame(asteroids)

            # --- FILTROS ---
            st.sidebar.subheader("🧩 Filtros Avanzados")
            min_diam = st.sidebar.slider("Diámetro mínimo (km)", float(df["diámetro_min_km"].min()), float(df["diámetro_max_km"].max()), 0.0)
            max_diam = st.sidebar.slider("Diámetro máximo (km)", float(df["diámetro_min_km"].min()), float(df["diámetro_max_km"].max()), float(df["diámetro_max_km"].max()))
            max_dist = st.sidebar.slider("Distancia máxima (en lunas)", float(df["distancia_lunar"].min()), float(df["distancia_lunar"].max()), float(df["distancia_lunar"].max()))

            df_filtered = df[
                (df["diámetro_max_km"] >= min_diam) &
                (df["diámetro_min_km"] <= max_diam) &
                (df["distancia_lunar"] <= max_dist)
            ]

            st.success(f"Se obtuvieron {len(df_filtered)} asteroides filtrados entre {start_date} y {end_date}.")

            # --- CREAR TABS ---
            tab1, tab2, tab3 = st.tabs(["📊 Análisis de Datos", "🌍 Mapa 3D", "ℹ️ Acerca de"])

            # ====================================================
            # TAB 1: ANÁLISIS PRINCIPAL
            # ====================================================
            with tab1:
                st.subheader("📅 Línea de tiempo: cantidad de asteroides por fecha")
                count_by_date = df_filtered.groupby("fecha").size().reset_index(name="cantidad")
                fig_line = px.line(
                    count_by_date,
                    x="fecha",
                    y="cantidad",
                    markers=True,
                    title="Número de Asteroides Detectados por Día",
                    line_shape="spline"
                )
                fig_line.update_traces(line_color="#00BFFF", marker=dict(size=8, color="white", line=dict(width=2, color="#00BFFF")))
                st.plotly_chart(fig_line, use_container_width=True)

                # --- DISPERSIÓN ---
                st.subheader("🚀 Velocidad vs Distancia")
                fig_scatter = px.scatter(
                    df_filtered,
                    x="velocidad_km_h",
                    y="distancia_lunar",
                    color="peligroso",
                    size="diámetro_max_km",
                    hover_name="nombre",
                    labels={
                        "velocidad_km_h": "Velocidad (km/h)",
                        "distancia_lunar": "Distancia (en lunas)"
                    },
                    title="Relación entre Velocidad y Distancia",
                    color_discrete_map={True: "#FF6347", False: "#00CED1"}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

                # --- HISTOGRAMA ---
                st.subheader("📏 Distribución del tamaño de los asteroides")
                fig_hist = px.histogram(
                    df_filtered,
                    x="diámetro_max_km",
                    nbins=20,
                    color="peligroso",
                    title="Distribución del Diámetro Máximo (km)",
                    labels={"diámetro_max_km": "Diámetro Máx (km)"},
                    color_discrete_map={True: "#FF6347", False: "#00CED1"}
                )
                st.plotly_chart(fig_hist, use_container_width=True)

                # --- PIE CHART COMPLEMENTARIO ---
                st.subheader("☢️ Proporción de Asteroides Peligrosos")
                pie_data = df_filtered["peligroso"].value_counts().reset_index()
                pie_data.columns = ["peligroso", "cantidad"]
                fig_pie = px.pie(
                    pie_data,
                    values="cantidad",
                    names="peligroso",
                    color="peligroso",
                    title="Distribución: Peligrosos vs No Peligrosos",
                    color_discrete_map={True: "#FF4500", False: "#4682B4"}
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # ====================================================
            # TAB 2: MAPA 3D
            # ====================================================
            with tab2:
                st.subheader("🌍 Visualización 3D de Cercanía de Asteroides")
                np.random.seed(42)
                df_filtered["latitud"] = np.random.uniform(-90, 90, df_filtered.shape[0])
                df_filtered["longitud"] = np.random.uniform(-180, 180, df_filtered.shape[0])

                fig_map = px.scatter_geo(
                    df_filtered,
                    lat="latitud",
                    lon="longitud",
                    color="peligroso",
                    size="diámetro_max_km",
                    projection="orthographic",
                    hover_name="nombre",
                    hover_data={
                        "diámetro_max_km": True,
                        "velocidad_km_h": True,
                        "distancia_lunar": True
                    },
                    title="Asteroides Cercanos a la Tierra (Simulación 3D)"
                )
                fig_map.update_geos(
                    showland=True,
                    landcolor="black",
                    oceancolor="midnightblue",
                    showocean=True,
                    projection_rotation=dict(lon=0, lat=0, roll=0)
                )
                st.plotly_chart(fig_map, use_container_width=True)

            # ====================================================
            # TAB 3: ACERCA DE
            # ====================================================
            with tab3:
                st.subheader("ℹ️ Acerca de")
                st.markdown("""
                ---
                ### Sobre el proyecto
                
                este proyecto busca mostrar de una manera **simple y visual** que está pasando en el espacio.
                El **Dashboard de Asteroides** toma información directamente de la **API Pública de la NASA** y la transforma en graficos faciles de entender.
                
                **Línea de tiempo:** muestra cuantos asteroides se detectaron cada día.
                
                **Velocidad vs Distancia:** permite ver qué tan rapido se mueven y qué tan cerca pasan de la tierra.
                
                **Distribucion de tamaños:** Nos ayuda a entender si la mayoría son pequeños o si hay algunos gigantes.
                
                **Proporción de peligro:** indica qué procentaje tiene potencial de riesgo.
                
                **Mapa 3D:** Representa de forma simulada su cercanía al planeta.
                
                ---
                La idea esta basada en el miedo a lo desconocido y a las posibilidades de peligro que un asteroide impacte contra la tierra, pero tambien es *acercar los datos espaciales al píblico en general y de manera sencilla*, despertando asi la curiosidad por la ciencia y lo desconocido, mostrando como la tecnología puede ayudarnos a entender mejor nuestro entorno e incluso el espacio exterior
                """)
                
                # --- SIDEBAR: FICHA TÉCNICA ---
                st.sidebar.markdown("---")
                st.sidebar.header("🧾 Ficha Técnica")

                st.sidebar.markdown("""
                ### 1. *Importación de librerías*
                ```python
                import streamlit as st
                import requests
                import pandas as pd
                import plotly.express as px
                import numpy as np
                ```

                Estas librerías hacen posible:
                * **streamlit:** crear la interfaz web interactiva.  
                * **requests:** conectarse a la API de la NASA y descargar los datos.  
                * **pandas:** organizar los datos en tablas (DataFrames).  
                * **plotly.express:** generar gráficos interactivos y bonitos.  
                * **numpy:** generar números aleatorios para simular posiciones (latitud/longitud) en el mapa 3D.

                ---

                ### 2. *Configuración inicial del dashboard*
                ```python
                st.set_page_config(page_title="Dashboard de Asteroides NASA", layout="wide")
                ```

                Esto define el *título de la pestaña del navegador* y que la app use el modo ancho (“wide”), ocupando todo el espacio horizontal disponible.

                Luego, se coloca un *encabezado* y una breve descripción:
                ```python
                st.markdown("<h1 style='text-align:center; color:#00BFFF;'>☄️ Dashboard de Asteroides Prueba n°1 </h1>", unsafe_allow_html=True)
                st.write("Visualización interactiva de datos de la NASA sobre asteroides cercanos a la Tierra.")
                ```

                ---

                ### 3. *Panel lateral (Sidebar)*
                El panel lateral permite *ingresar parámetros* antes de traer los datos:

                * La *API Key* (clave para acceder a la API de la NASA).  
                * Las *fechas de inicio y fin* para consultar los asteroides detectados en ese rango.

                ```python
                api_key = st.sidebar.text_input("Tu API Key de NASA: ...")
                start_date = st.sidebar.date_input("Fecha de inicio")
                end_date = st.sidebar.date_input("Fecha de fin")

                if st.sidebar.button("Obtener datos"):
                    ...
                ```

                ---

                ### 4. *Conexión con la API de la NASA*
                Cuando el usuario hace clic en el botón, el programa construye una *URL de consulta* con las fechas elegidas y la API key:
                ```python
                url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
                res = requests.get(url)
                ```

                La API responde con un archivo en formato *JSON*.  
                Si la respuesta es correcta (`status_code == 200`), el código recorre los datos y extrae:

                * Fecha  
                * Nombre  
                * Tamaño (mínimo y máximo)  
                * Si es peligroso o no  
                * Velocidad  
                * Distancia a la Tierra (en “distancia lunar”)

                Todo se guarda en un *DataFrame de Pandas*.

                ---

                ### 5. *Filtros avanzados*
                Luego, el panel lateral ofrece *sliders* para filtrar por:

                * Tamaño mínimo y máximo (en km)  
                * Distancia máxima (en lunas)

                ---

                ### 6. *Creación de pestañas (Tabs)*
                ```python
                tab1, tab2, tab3 = st.tabs(["📊 Análisis de Datos", "🌍 Mapa 3D", "ℹ️ Acerca de"])
                ```
                Cada pestaña contiene distintas visualizaciones o información.

                ---

                ### 7. *TAB 1: Análisis de Datos*
                Muestra gráficos interactivos con **Plotly**:

                1. Línea de tiempo (detecciones por día)  
                2. Dispersión (velocidad vs distancia)  
                3. Histograma (tamaño)  
                4. Circular (proporción de peligrosos)

                ---

                ### 8. *TAB 2: Mapa 3D*
                Como la API no da coordenadas reales, se *simulan posiciones aleatorias*:

                ```python
                df_filtered["latitud"] = np.random.uniform(-90, 90, df_filtered.shape[0])
                df_filtered["longitud"] = np.random.uniform(-180, 180, df_filtered.shape[0])
                ```

                ---

                ### Descripción general del proyecto
                Este proyecto busca mostrar de una manera *simple y visual* qué está pasando allá afuera.  
                El *Dashboard de Asteroides* toma información directamente de la *API pública de la NASA* y la transforma en gráficos fáciles de entender.

                * 📅 **Línea de tiempo:** muestra cuántos asteroides se detectaron cada día.  
                * 🚀 **Velocidad vs distancia:** permite ver qué tan rápido se mueven y qué tan cerca pasan de la Tierra.  
                * 📏 **Distribución de tamaños:** muestra si predominan los pequeños o hay algunos gigantes.  
                * ☢️ **Proporción de peligrosos:** indica el porcentaje con potencial de riesgo.  
                * 🌍 **Mapa 3D:** representa de forma simulada su cercanía al planeta.
                """)
                
            
        else:
            st.error(f"Error al obtener los datos: {res.status_code}")
