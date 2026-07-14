import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Inteligencia de Mercado BESS", layout="wide", page_icon="📈")

# Función para cargar y procesar los datos
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("BESS_Normalizado_Local.xlsx")
        
        # Categorizar por los rangos de mercado
        def asignar_rango(cap):
            if pd.isna(cap): return "Sin dato"
            elif cap < 50: return "< 50 kWh"
            elif 50 <= cap <= 100: return "50–100 kWh"
            elif 100 < cap <= 200: return "100–200 kWh"
            elif 200 < cap <= 300: return "200–300 kWh"
            elif 300 < cap <= 500: return "300–500 kWh"
            else: return "> 500 kWh"
                
        df['Rango_Capacidad'] = df['Capacidad_kWh'].apply(asignar_rango)
        
        # Calcular métricas clave para análisis
        df['Costo_USD_kWh'] = df['Precio_USD_Final_Estimado'] / df['Capacidad_kWh']
        df['Tasa_C'] = df['Potencia_kW'] / df['Capacidad_kWh'] # Relación Potencia/Energía
        
        return df
    except FileNotFoundError:
        st.error("⚠️ Archivo 'BESS_Normalizado_Local.xlsx' no encontrado.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Barra de Navegación Lateral ---
    st.sidebar.title("Navegación Comercial")
    opcion = st.sidebar.radio("Módulos:", [
        "📊 Estudio de Mercado por Rango", 
        "📋 Base de Datos General", 
        "🧮 Calculadora de Estimación"
    ])

    orden_rangos = ["< 50 kWh", "50–100 kWh", "100–200 kWh", "200–300 kWh", "300–500 kWh", "> 500 kWh"]

    # --- Pestaña 1: Estudio de Mercado (Principal) ---
    if opcion == "📊 Estudio de Mercado por Rango":
        st.title("Análisis Competitivo BESS por Segmento")
        st.markdown("Selecciona un nicho de mercado para analizar el comportamiento de precios, competidores y especificaciones técnicas de la industria.")
        
        # Selector de Rango
        rango_seleccionado = st.selectbox("Selecciona el nicho de capacidad a analizar:", orden_rangos, index=1)
        
        # Filtrar datos por el rango seleccionado
        df_nicho = df[df['Rango_Capacidad'] == rango_seleccionado].copy()
        
        if df_nicho.empty:
            st.warning("No hay datos suficientes para este rango de capacidad.")
        else:
            # Cálculos de mercado para el nicho
            precio_min = df_nicho['Precio_USD_Final_Estimado'].min()
            precio_max = df_nicho['Precio_USD_Final_Estimado'].max()
            promedio_kwh = df_nicho['Costo_USD_kWh'].mean()
            
            st.subheader(f"Resumen de Mercado: {rango_seleccionado}")
            
            # Tarjetas de Precios
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Equipos en este Nicho", len(df_nicho))
            col2.metric("Precio Base (Mínimo)", f"${precio_min:,.0f} USD")
            col3.metric("Precio Tope (Máximo)", f"${precio_max:,.0f} USD")
            col4.metric("Promedio Competitivo", f"${promedio_kwh:,.0f} USD / kWh")
            
            st.divider()
            
            # Gráficos de Análisis Comercial
            st.subheader("Inteligencia Competitiva")
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                # 1. Posicionamiento de Marcas (Precio)
                df_marcas = df_nicho.groupby('Marca')['Costo_USD_kWh'].mean().reset_index().sort_values('Costo_USD_kWh')
                fig1 = px.bar(df_marcas, x='Costo_USD_kWh', y='Marca', orientation='h',
                              title="Posicionamiento de Precio por Marca (USD/kWh)",
                              labels={'Costo_USD_kWh': 'USD / kWh'}, color='Costo_USD_kWh', color_continuous_scale='Viridis')
                st.plotly_chart(fig1, use_container_width=True)
                
            with g_col2:
                # 2. Análisis de Dispersión (Qué se está vendiendo exactamente)
                fig2 = px.scatter(df_nicho, x='Capacidad_kWh', y='Precio_USD_Final_Estimado',
                                  color='Origen', size='Capacidad_kWh', hover_name='Modelo',
                                  title="Dispersión de Oferta: Capacidad vs Precio Total",
                                  labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Precio_USD_Final_Estimado': 'Precio Total (USD)'})
                st.plotly_chart(fig2, use_container_width=True)

            # Gráfico adicional: Análisis Técnico de Potencia
            if df_nicho['Tasa_C'].notna().any():
                st.subheader("Perfil Técnico del Segmento (Orientación a Potencia vs Energía)")
                fig3 = px.box(df_nicho, x='Origen', y='Tasa_C', points="all", hover_name='Marca',
                              title="Distribución de la Tasa C (Potencia kW / Capacidad kWh) por Origen",
                              labels={'Tasa_C': 'Ratio Potencia/Capacidad (C-Rate)'})
                st.plotly_chart(fig3, use_container_width=True)

            # Tabla de datos ordenada por precio para el segmento
            st.subheader("Catálogo de Competidores en el Nicho")
            columnas_nicho = ['Marca', 'Modelo', 'Capacidad_kWh', 'Potencia_kW', 'Precio_USD_Final_Estimado', 'Costo_USD_kWh', 'Origen', 'Garantia']
            cols_disponibles = [c for c in columnas_nicho if c in df_nicho.columns]
            
            # Ordenar de más barato a más caro por kWh
            st.dataframe(df_nicho[cols_disponibles].sort_values('Costo_USD_kWh'), use_container_width=True)

    # --- Pestaña 2: Base de Datos General ---
    elif opcion == "📋 Base de Datos General":
        st.title("Explorador de Base de Datos Completa")
        st.markdown("Revisa el catálogo consolidado de todos los segmentos y orígenes.")
        
        filtro_rango = st.multiselect("Filtrar por Rango:", options=orden_rangos, default=orden_rangos)
        df_filtro = df[df['Rango_Capacidad'].isin(filtro_rango)]
        
        columnas_mostrar = ['Rango_Capacidad', 'Marca', 'Modelo', 'Capacidad_kWh', 'Potencia_kW', 'Quimica', 'Precio_Local', 'Moneda_Local', 'Precio_USD_Final_Estimado', 'Proveedor', 'Origen', 'Link']
        st.dataframe(df_filtro[[c for c in columnas_mostrar if c in df_filtro.columns]], use_container_width=True)

    # --- Pestaña 3: Calculadora ---
    elif opcion == "🧮 Calculadora de Estimación":
        st.title("Calculadora de Costos (Dimensionamiento)")
        st.markdown("Estima costos de hardware base para tus proyectos basándote en el mercado.")
        
        promedio_global = df[(df['Costo_USD_kWh'] > 50) & (df['Costo_USD_kWh'] < 2000)]['Costo_USD_kWh'].mean()
        
        col1, col2 = st.columns(2)
        with col1:
            cap_input = st.number_input("Capacidad Requerida para el Proyecto (kWh):", min_value=1.0, value=200.0, step=10.0)
            tc_input = st.number_input("Tipo de Cambio (CLP/USD):", min_value=100, value=930, step=10)
            
        with col2:
            st.info(f"**Costo Promedio del Mercado:** ${promedio_global:,.2f} USD/kWh")
            total_usd = cap_input * promedio_global
            total_clp = total_usd * tc_input
            
            st.success(f"**Presupuesto Base Estimado (USD):** ${total_usd:,.2f}")
            st.success(f"**Presupuesto Base Estimado (CLP):** ${total_clp:,.0f}")
            
        st.caption("Los costos corresponden exclusivamente a hardware base. Integraciones complejas, inversores externos PCS o interfaces de comunicación avanzadas deben presupuestarse por separado.")
