import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inteligencia Comercial BESS", layout="wide", page_icon="💰")

# --- 1. Carga y Preparación de Datos ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("BESS_Normalizado_Local.xlsx")
        
        # Asignar rangos de mercado
        def asignar_rango(cap):
            if pd.isna(cap): return "Sin dato"
            elif cap < 50: return "< 50 kWh"
            elif 50 <= cap <= 100: return "50–100 kWh"
            elif 100 < cap <= 200: return "100–200 kWh"
            elif 200 < cap <= 300: return "200–300 kWh"
            elif 300 < cap <= 500: return "300–500 kWh"
            else: return "> 500 kWh"
                
        df['Rango_Capacidad'] = df['Capacidad_kWh'].apply(asignar_rango)
        
        # Calcular métricas clave
        df['Costo_USD_kWh'] = df['Precio_USD_Final_Estimado'] / df['Capacidad_kWh']
        df['Tasa_C'] = df['Potencia_kW'] / df['Capacidad_kWh']
        
        # Rellenar valores nulos comunes
        df['Quimica'] = df['Quimica'].fillna('No Especificada')
        df['Proveedor'] = df['Proveedor'].fillna('Venta Directa')
        df['Origen'] = df['Origen'].fillna('Desconocido')
        
        # --- NUEVAS COLUMNAS PARA SEGMENTACIÓN ---
        # 1. Segmentar Mercado
        if 'Hoja_Origen' in df.columns:
            df['Mercado'] = df['Hoja_Origen'].apply(lambda x: 'CHILE' if str(x).strip().upper() == 'CHILE' else 'INTERNACIONAL')
        else:
            df['Mercado'] = 'INTERNACIONAL'
            
        # 2. Segmentar Inversor
        def tiene_inversor(potencia):
            # Si no hay dato de potencia o es 0, asumimos que es solo el rack de baterías
            if pd.isna(potencia) or potencia <= 0:
                return 'SIN INVERSOR'
            else:
                return 'CON INVERSOR'
                
        df['Tipo_Inversor'] = df['Potencia_kW'].apply(tiene_inversor)
        
        return df
    except FileNotFoundError:
        st.error("⚠️ Archivo 'BESS_Normalizado_Local.xlsx' no encontrado en el repositorio.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Filtros Globales (Barra Lateral) ---
    st.sidebar.title("Filtros Globales")
    filtro_mercado = st.sidebar.selectbox("Mercado:", ["TODOS", "CHILE", "INTERNACIONAL"])
    filtro_inversor = st.sidebar.selectbox("Tipo de Sistema:", ["TODOS", "CON INVERSOR", "SIN INVERSOR"])
    
    # Aplicar Filtros Globales al DataFrame
    if filtro_mercado != "TODOS":
        df = df[df['Mercado'] == filtro_mercado]
        
    if filtro_inversor != "TODOS":
        df = df[df['Tipo_Inversor'] == filtro_inversor]
        
    st.sidebar.divider()

    # Verificar si el DataFrame quedó vacío tras aplicar los filtros
    if df.empty:
        st.warning("⚠️ No hay equipos que cumplan con la combinación de filtros seleccionada. Intenta ajustar el Mercado o el Tipo de Sistema en la barra lateral.")
    else:
        # --- 2. Barra Lateral de Navegación ---
        st.sidebar.title("Módulos Comerciales")
        opcion = st.sidebar.radio("Ir a:", [
            "📊 Análisis Financiero y Competencia", 
            "📋 Catálogo General", 
            "💰 Calculadora de Costos y Rentabilidad"
        ])

        orden_rangos = ["< 50 kWh", "50–100 kWh", "100–200 kWh", "200–300 kWh", "300–500 kWh", "> 500 kWh"]

        # --- Pestaña 1: Análisis Financiero y Competencia ---
        if opcion == "📊 Análisis Financiero y Competencia":
            st.title("Estudio de Mercado BESS y Competencia")
            st.markdown("Selecciona un segmento para evaluar precios, competidores y especificaciones técnicas.")
            
            rango_seleccionado = st.selectbox("Selecciona el nicho a analizar:", orden_rangos, index=1)
            df_nicho = df[df['Rango_Capacidad'] == rango_seleccionado].copy()
            
            if not df_nicho.empty:
                precio_min = df_nicho['Precio_USD_Final_Estimado'].min()
                precio_max = df_nicho['Precio_USD_Final_Estimado'].max()
                promedio_kwh = df_nicho['Costo_USD_kWh'].mean()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Equipos en este Nicho", len(df_nicho))
                col2.metric("Precio Base (Mínimo)", f"${precio_min:,.0f} USD")
                col3.metric("Precio Tope (Máximo)", f"${precio_max:,.0f} USD")
                col4.metric("Costo Promedio Unitario", f"${promedio_kwh:,.0f} USD/kWh")
                
                st.divider()
                
                st.subheader("1. Análisis de Precios y Escala")
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    fig_total = px.scatter(
                        df_nicho, x='Capacidad_kWh', y='Precio_USD_Final_Estimado', 
                        color='Marca', hover_name='Modelo', trendline="ols",
                        title="Relación Directa: Capacidad vs Precio Total (USD)",
                        labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Precio_USD_Final_Estimado': 'Precio Estimado (USD)'}
                    )
                    fig_total.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                    st.plotly_chart(fig_total, use_container_width=True)
                    
                with col_graf2:
                    fig_kwh = px.scatter(
                        df_nicho, x='Capacidad_kWh', y='Costo_USD_kWh', 
                        color='Origen', hover_name='Marca',
                        title="Economía de Escala: Costo Unitario (USD/kWh)",
                        labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Costo_USD_kWh': 'USD / kWh'}
                    )
                    fig_kwh.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                    st.plotly_chart(fig_kwh, use_container_width=True)

                st.divider()

                st.subheader("2. Mapeo de Competidores y Tecnologías")
                col_pie1, col_pie2, col_bar = st.columns([1, 1, 1.5])
                
                with col_pie1:
                    fig_origen = px.pie(df_nicho, names='Origen', hole=0.4, 
                                        title="Origen de Fabricación", color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_origen.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_origen, use_container_width=True)
                    
                with col_pie2:
                    fig_quimica = px.pie(df_nicho, names='Quimica', hole=0.4, 
                                         title="Tecnología de Batería", color_discrete_sequence=px.colors.qualitative.Set3)
                    fig_quimica.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_quimica, use_container_width=True)
                    
                with col_bar:
                    df_marcas = df_nicho.groupby('Marca')['Costo_USD_kWh'].mean().reset_index().sort_values('Costo_USD_kWh')
                    fig_bar = px.bar(
                        df_marcas, x='Costo_USD_kWh', y='Marca', orientation='h',
                        title="Ranking de Precio Promedio por Marca",
                        color='Costo_USD_kWh', color_continuous_scale='RdYlGn_r', text_auto='.0f',
                        labels={'Costo_USD_kWh': 'Promedio USD/kWh'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                st.divider()
                
                st.subheader("3. Perfil Técnico y Proveedores")
                col_tec1, col_tec2 = st.columns(2)
                
                with col_tec1:
                    df_tasa = df_nicho.dropna(subset=['Tasa_C'])
                    if not df_tasa.empty:
                        fig_c_rate = px.box(df_tasa, x='Origen', y='Tasa_C', points="all", hover_name='Marca',
                                            title="Orientación Comercial: Potencia (Tasa C) vs Origen",
                                            labels={'Tasa_C': 'Tasa C (Potencia/Capacidad)', 'Origen': 'País de Origen'})
                        st.plotly_chart(fig_c_rate, use_container_width=True)
                    else:
                        st.info("No hay datos suficientes de potencia para calcular la Tasa C en este nicho.")
                        
                with col_tec2:
                    conteo_proveedores = df_nicho['Proveedor'].value_counts().reset_index()
                    conteo_proveedores.columns = ['Proveedor', 'Cantidad de Equipos']
                    fig_prov = px.bar(conteo_proveedores.head(7), x='Cantidad de Equipos', y='Proveedor', orientation='h',
                                      title="Principales Distribuidores / Proveedores",
                                      color='Cantidad de Equipos', color_continuous_scale='Blues')
                    fig_prov.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_prov, use_container_width=True)

                st.subheader(f"Equipos Analizados en {rango_seleccionado}")
                columnas_nicho = ['Marca', 'Modelo', 'Capacidad_kWh', 'Potencia_kW', 'Quimica', 'Precio_USD_Final_Estimado', 'Costo_USD_kWh', 'Proveedor', 'Origen']
                st.dataframe(df_nicho[[c for c in columnas_nicho if c in df_nicho.columns]].sort_values('Costo_USD_kWh'), use_container_width=True)
            else:
                st.warning("No hay equipos registrados en el mercado para este segmento de capacidad.")

        # --- Pestaña 2: Catálogo General ---
        elif opcion == "📋 Catálogo General":
            st.title("Base de Datos Maestra")
            filtro_rango = st.multiselect("Filtrar por Rango:", options=orden_rangos, default=orden_rangos)
            df_filtro = df[df['Rango_Capacidad'].isin(filtro_rango)]
            columnas_mostrar = ['Rango_Capacidad', 'Marca', 'Modelo', 'Capacidad_kWh', 'Potencia_kW', 'Quimica', 'Precio_Local', 'Moneda_Local', 'Precio_USD_Final_Estimado', 'Costo_USD_kWh', 'Proveedor', 'Origen', 'Garantia', 'Link']
            st.dataframe(df_filtro[[c for c in columnas_mostrar if c in df_filtro.columns]].sort_values('Capacidad_kWh'), use_container_width=True)

        # --- Pestaña 3: Calculadora de Costos y Rentabilidad ---
        elif opcion == "💰 Calculadora de Costos y Rentabilidad":
            st.title("Calculadora de Costos y Rentabilidad Comercial")
            st.markdown("Estima el costo base del equipo y, de manera opcional, proyecta tu precio de venta final y ganancias.")
            
            df_realista = df[(df['Costo_USD_kWh'] > 50) & (df['Costo_USD_kWh'] < 1500)]
            
            if not df_realista.empty:
                costo_base_kwh = df_realista['Costo_USD_kWh'].mean()
                st.info(f"**Costo Base Promedio del Mercado Segmentado:** ${costo_base_kwh:,.2f} USD por kWh")
            else:
                costo_base_kwh = 0
                st.warning("⚠️ No hay suficientes datos con precios válidos en este segmento para establecer un costo base promedio.")
            
            col_calc1, col_calc2 = st.columns(2)
            
            with col_calc1:
                st.subheader("Parámetros Base")
                cap_input = st.number_input("Capacidad del Equipo (kWh):", min_value=1.0, value=100.0, step=10.0)
                tc_input = st.number_input("Tipo de Cambio (CLP/USD):", min_value=500, value=930, step=10)
                
                st.divider()
                
                # --- OPCIÓN PARA SACAR / MOSTRAR LO DEL MARGEN ---
                aplicar_margen = st.checkbox("Activar modo vendedor (Calcular margen de ganancia comercial)", value=False)
                
                if aplicar_margen:
                    margen_input = st.slider("Margen de Ganancia Esperado (%):", min_value=5, max_value=100, value=30, step=5)
                else:
                    margen_input = 0
                
            with col_calc2:
                st.subheader("Resultados Financieros")
                
                # Cálculo de Costo Base
                costo_compra_usd = cap_input * costo_base_kwh
                costo_compra_clp = costo_compra_usd * tc_input
                
                st.warning(f"**Costo de Adquisición / Estimado (USD):** ${costo_compra_usd:,.2f}")
                st.warning(f"**Costo de Adquisición / Estimado (CLP):** ${costo_compra_clp:,.0f}")
                
                # Cálculo de Venta (Solo si el checkbox está activo)
                if aplicar_margen:
                    st.divider()
                    precio_venta_usd = costo_compra_usd * (1 + (margen_input / 100))
                    ganancia_neta_usd = precio_venta_usd - costo_compra_usd
                    
                    precio_venta_clp = precio_venta_usd * tc_input
                    ganancia_neta_clp = ganancia_neta_usd * tc_input
                    
                    st.success(f"**Precio de Venta Sugerido (USD):** ${precio_venta_usd:,.2f}")
                    st.metric(label="Tu Ganancia Neta (USD)", value=f"${ganancia_neta_usd:,.2f}")
                    
                    st.success(f"**Precio de Venta Sugerido (CLP):** ${precio_venta_clp:,.0f}")
                    st.metric(label="Tu Ganancia Neta (CLP)", value=f"${ganancia_neta_clp:,.0f}")
