import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inteligencia Comercial BESS", layout="wide", page_icon="💰")

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("BESS_Normalizado_Local.xlsx")
        
        def asignar_rango(cap):
            if pd.isna(cap): return "Sin dato"
            elif cap < 50: return "< 50 kWh"
            elif 50 <= cap <= 100: return "50–100 kWh"
            elif 100 < cap <= 200: return "100–200 kWh"
            elif 200 < cap <= 300: return "200–300 kWh"
            elif 300 < cap <= 500: return "300–500 kWh"
            else: return "> 500 kWh"
                
        df['Rango_Capacidad'] = df['Capacidad_kWh'].apply(asignar_rango)
        df['Costo_USD_kWh'] = df['Precio_USD_Final_Estimado'] / df['Capacidad_kWh']
        df['Tasa_C'] = df['Potencia_kW'] / df['Capacidad_kWh']
        
        return df
    except FileNotFoundError:
        st.error("⚠️ Archivo 'BESS_Normalizado_Local.xlsx' no encontrado.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("Módulos Comerciales")
    opcion = st.sidebar.radio("Ir a:", [
        "📊 Análisis Financiero y Competencia", 
        "📋 Catálogo General", 
        "💰 Simulador de Márgenes (Ventas)"
    ])

    orden_rangos = ["< 50 kWh", "50–100 kWh", "100–200 kWh", "200–300 kWh", "300–500 kWh", "> 500 kWh"]

    # --- Pestaña 1: Análisis Financiero ---
    if opcion == "📊 Análisis Financiero y Competencia":
        st.title("Análisis Financiero de la Competencia")
        st.markdown("Evalúa cómo se comportan los precios del mercado para detectar oportunidades de venta.")
        
        rango_seleccionado = st.selectbox("Selecciona el nicho a analizar:", orden_rangos, index=1)
        df_nicho = df[df['Rango_Capacidad'] == rango_seleccionado].copy()
        
        if not df_nicho.empty:
            st.subheader("Tendencias de Precio vs. Capacidad")
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                # Gráfico 1: Relación Directa (Precio Total vs Capacidad) con línea de tendencia
                fig_total = px.scatter(
                    df_nicho, x='Capacidad_kWh', y='Precio_USD_Final_Estimado', 
                    color='Marca', hover_name='Modelo', trendline="ols",
                    title="Relación: Capacidad (kWh) vs Precio Total (USD)",
                    labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Precio_USD_Final_Estimado': 'Precio Total Estimado (USD)'}
                )
                st.plotly_chart(fig_total, use_container_width=True)
                
            with col_graf2:
                # Gráfico 2: Economía de Escala (Costo por kWh vs Capacidad)
                fig_kwh = px.scatter(
                    df_nicho, x='Capacidad_kWh', y='Costo_USD_kWh', 
                    color='Origen', size='Potencia_kW', hover_name='Marca', trendline="lowess",
                    title="Economía de Escala: Costo Unitario (USD/kWh) vs Capacidad",
                    labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Costo_USD_kWh': 'Costo Unitario (USD / kWh)'}
                )
                st.plotly_chart(fig_kwh, use_container_width=True)

            st.divider()
            st.subheader("Ranking de Competidores (Costo por kWh)")
            
            # Gráfico de barras ordenado
            df_marcas = df_nicho.groupby('Marca')['Costo_USD_kWh'].mean().reset_index().sort_values('Costo_USD_kWh')
            fig_bar = px.bar(
                df_marcas, x='Costo_USD_kWh', y='Marca', orientation='h',
                title="¿Quién vende más caro/barato en este segmento?",
                color='Costo_USD_kWh', color_continuous_scale='RdYlGn_r', text_auto='.0f'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- Pestaña 2: Base de Datos General ---
    elif opcion == "📋 Catálogo General":
        st.title("Base de Datos Completa")
        filtro_rango = st.multiselect("Filtrar por Rango:", options=orden_rangos, default=orden_rangos)
        df_filtro = df[df['Rango_Capacidad'].isin(filtro_rango)]
        columnas_mostrar = ['Rango_Capacidad', 'Marca', 'Modelo', 'Capacidad_kWh', 'Precio_USD_Final_Estimado', 'Costo_USD_kWh', 'Origen']
        st.dataframe(df_filtro[[c for c in columnas_mostrar if c in df_filtro.columns]].sort_values('Costo_USD_kWh'), use_container_width=True)

    # --- Pestaña 3: Simulador de Márgenes ---
    elif opcion == "💰 Simulador de Márgenes (Ventas)":
        st.title("Simulador de Rentabilidad Comercial")
        st.markdown("Calcula tu precio de venta final aplicando tu margen de ganancia sobre el costo promedio de la industria.")
        
        # Filtramos valores extremos para tener un costo base realista
        df_realista = df[(df['Costo_USD_kWh'] > 50) & (df['Costo_USD_kWh'] < 1500)]
        costo_base_kwh = df_realista['Costo_USD_kWh'].mean()
        
        st.info(f"**Costo Proveedor Estimado (Mercado Base):** ${costo_base_kwh:,.2f} USD por kWh")
        
        col_calc1, col_calc2 = st.columns(2)
        
        with col_calc1:
            st.subheader("Tus Parámetros")
            cap_input = st.number_input("Capacidad del Equipo a Vender (kWh):", min_value=1.0, value=100.0, step=10.0)
            margen_input = st.slider("Margen de Ganancia Esperado (%):", min_value=5, max_value=100, value=30, step=5)
            tc_input = st.number_input("Tipo de Cambio (CLP/USD):", min_value=500, value=930, step=10)
            
        with col_calc2:
            st.subheader("Proyección Financiera")
            
            # Cálculos
            costo_compra_usd = cap_input * costo_base_kwh
            precio_venta_usd = costo_compra_usd * (1 + (margen_input / 100))
            ganancia_neta_usd = precio_venta_usd - costo_compra_usd
            
            precio_venta_clp = precio_venta_usd * tc_input
            ganancia_neta_clp = ganancia_neta_usd * tc_input
            
            st.warning(f"**Costo de Adquisición (USD):** ${costo_compra_usd:,.2f}")
            st.success(f"**Precio de Venta Sugerido (USD):** ${precio_venta_usd:,.2f}")
            st.metric(label="Tu Ganancia Neta (USD)", value=f"${ganancia_neta_usd:,.2f}")
            
            st.divider()
            st.success(f"**Precio de Venta Sugerido (CLP):** ${precio_venta_clp:,.0f}")
            st.metric(label="Tu Ganancia Neta (CLP)", value=f"${ganancia_neta_clp:,.0f}")
