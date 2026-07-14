import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Herramienta BESS", layout="wide", page_icon="🔋")

# Función para cargar los datos en caché (leyendo el archivo Excel)
@st.cache_data
def load_data():
    try:
        # Lee directamente el archivo Excel
        df = pd.read_excel("BESS_Normalizado_Local.xlsx")
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'BESS_Normalizado_Local.xlsx'. Asegúrate de haberlo subido a GitHub.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Barra de Navegación Lateral ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
    st.sidebar.title("Navegación")
    opcion = st.sidebar.radio("Ir a:", ["🧮 Calculadora de Estimación", "📊 Dashboard de Mercado", "📋 Datos Completos"])

    # Calcular promedio del mercado limpiando valores extremos
    valid_usd_kwh = df[(df['Precio_USD_Calculado'] / df['Capacidad_kWh'] > 50) & 
                       (df['Precio_USD_Calculado'] / df['Capacidad_kWh'] < 2000)]
    avg_usd_kwh = (valid_usd_kwh['Precio_USD_Calculado'] / valid_usd_kwh['Capacidad_kWh']).mean()
    if pd.isna(avg_usd_kwh):
        avg_usd_kwh = 261.71

    # --- Pestaña 1: Calculadora ---
    if opcion == "🧮 Calculadora de Estimación":
        st.title("Calculadora de Costos de Equipamiento BESS")
        st.markdown("Estima el costo base de hardware en función de la capacidad requerida.")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Parámetros de Entrada")
            capacidad_req = st.number_input("Capacidad Requerida (kWh):", min_value=1.0, value=1000.0, step=100.0)
            tc = st.number_input("Tipo de Cambio (CLP/USD):", min_value=100, value=930, step=10)

        with col2:
            st.subheader("Resultados")
            st.info(f"**Costo Promedio de la Industria:** ${avg_usd_kwh:,.2f} USD / kWh")

            costo_usd = capacidad_req * avg_usd_kwh
            costo_clp = costo_usd * tc

            st.success(f"**Costo Estimado (USD):** ${costo_usd:,.2f}")
            st.success(f"**Costo Estimado (CLP):** ${costo_clp:,.0f}")

        st.caption("Nota: Valores referenciales calculados en base al hardware bruto. No incluyen costos de integración para el estándar ISO 15118, interfaces V2G, ni obras civiles.")

    # --- Pestaña 2: Dashboard ---
    elif opcion == "📊 Dashboard de Mercado":
        st.title("Dashboard Analítico del Mercado BESS")

        # Preparar métrica para gráficos
        df['Costo_USD_kWh'] = df['Precio_USD_Final_Estimado'] / df['Capacidad_kWh']

        # Tarjetas de resumen (KPIs)
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Modelos Analizados", value=len(df))
        kpi2.metric(label="Costo Promedio Mercado", value=f"${avg_usd_kwh:,.0f} USD/kWh")
        kpi3.metric(label="Capacidad Máxima Registrada", value=f"{df['Capacidad_kWh'].max():,.0f} kWh")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            df_origen = df.groupby('Origen')['Costo_USD_kWh'].mean().reset_index()
            fig1 = px.bar(df_origen, x='Origen', y='Costo_USD_kWh', 
                          title="Costo Promedio (USD/kWh) según País de Origen",
                          color='Costo_USD_kWh', color_continuous_scale='Blues')
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            df_quimica = df.dropna(subset=['Quimica'])
            fig2 = px.pie(df_quimica, names='Quimica', 
                          title="Distribución de Tecnologías de Química",
                          hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Relación Capacidad vs. Costo Estimado")
        fig3 = px.scatter(df, x='Capacidad_kWh', y='Precio_USD_Final_Estimado', 
                          color='Hoja_Origen', hover_name='Marca',
                          labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Precio_USD_Final_Estimado': 'Precio Total Estimado (USD)'},
                          log_x=True, log_y=True)
        st.plotly_chart(fig3, use_container_width=True)

    # --- Pestaña 3: Datos ---
    elif opcion == "📋 Datos Completos":
        st.title("Base de Datos Consolidada")
        st.markdown("Explora, filtra y descarga los datos normalizados de los sistemas de almacenamiento.")

        origen_filtro = st.multiselect("Filtrar por Hoja de Origen:", options=df['Hoja_Origen'].unique(), default=df['Hoja_Origen'].unique())
        df_filtrado = df[df['Hoja_Origen'].isin(origen_filtro)]

        st.dataframe(df_filtrado, use_container_width=True)