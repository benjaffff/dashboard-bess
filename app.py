import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inteligencia y Finanzas BESS", layout="wide", page_icon="🏦")

# --- 1. Carga y Preparación de Datos ---
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
        df['Quimica'] = df['Quimica'].fillna('No Especificada')
        df['Proveedor'] = df['Proveedor'].fillna('Venta Directa')
        df['Origen'] = df['Origen'].fillna('Desconocido')
        
        return df
    except FileNotFoundError:
        st.error("⚠️ Archivo 'BESS_Normalizado_Local.xlsx' no encontrado.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("Módulos Estratégicos")
    opcion = st.sidebar.radio("Navegación:", [
        "📊 Análisis de Competencia", 
        "📋 Catálogo General", 
        "🏦 Evaluador Financiero (Landed Cost & LCOS)"
    ])

    orden_rangos = ["< 50 kWh", "50–100 kWh", "100–200 kWh", "200–300 kWh", "300–500 kWh", "> 500 kWh"]

    # --- Pestaña 1: Análisis de Competencia ---
    if opcion == "📊 Análisis de Competencia":
        st.title("Estudio de Mercado BESS")
        rango_seleccionado = st.selectbox("Selecciona el nicho a analizar:", orden_rangos, index=1)
        df_nicho = df[df['Rango_Capacidad'] == rango_seleccionado].copy()
        
        if not df_nicho.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Equipos en este Nicho", len(df_nicho))
            col2.metric("Precio Base (Mínimo)", f"${df_nicho['Precio_USD_Final_Estimado'].min():,.0f} USD")
            col3.metric("Precio Tope (Máximo)", f"${df_nicho['Precio_USD_Final_Estimado'].max():,.0f} USD")
            col4.metric("Costo Promedio Unitario", f"${df_nicho['Costo_USD_kWh'].mean():,.0f} USD/kWh")
            
            st.divider()
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                fig_total = px.scatter(
                    df_nicho, x='Capacidad_kWh', y='Precio_USD_Final_Estimado', 
                    color='Marca', hover_name='Modelo',
                    title="Capacidad vs Precio Total Estimado (USD)",
                    labels={'Capacidad_kWh': 'Capacidad (kWh)', 'Precio_USD_Final_Estimado': 'Precio (USD)'}
                )
                fig_total.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
                st.plotly_chart(fig_total, use_container_width=True)
                
            with col_graf2:
                df_marcas = df_nicho.groupby('Marca')['Costo_USD_kWh'].mean().reset_index().sort_values('Costo_USD_kWh')
                fig_bar = px.bar(
                    df_marcas, x='Costo_USD_kWh', y='Marca', orientation='h',
                    title="Ranking de Precio Promedio por Marca",
                    color='Costo_USD_kWh', color_continuous_scale='RdYlGn_r', text_auto='.0f'
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    # --- Pestaña 2: Catálogo General ---
    elif opcion == "📋 Catálogo General":
        st.title("Base de Datos Maestra")
        filtro_rango = st.multiselect("Filtrar por Rango:", options=orden_rangos, default=orden_rangos)
        df_filtro = df[df['Rango_Capacidad'].isin(filtro_rango)]
        st.dataframe(df_filtro.sort_values('Capacidad_kWh'), use_container_width=True)

    # --- Pestaña 3: Evaluador Financiero ---
    elif opcion == "🏦 Evaluador Financiero (Landed Cost & LCOS)":
        st.title("Modelado Económico Avanzado")
        st.markdown("Estructura los costos reales de importación, integración y venta para asegurar la rentabilidad del proyecto.")
        
        # Parámetros Base
        st.subheader("1. Costo Base del Equipo y Logística (Landed Cost)")
        col_import1, col_import2, col_import3 = st.columns(3)
        
        with col_import1:
            capacidad = st.number_input("Capacidad del BESS (kWh):", value=100.0, step=10.0)
            precio_fob = st.number_input("Precio en Origen (FOB USD):", value=22000.0, step=1000.0)
        with col_import2:
            flete_seguro = st.number_input("Flete Marítimo + Seguro (USD):", value=2500.0, step=500.0)
            arancel = st.number_input("Arancel Aduanero (%):", value=0.0, step=1.0)
        with col_import3:
            tc = st.number_input("Tipo de Cambio (CLP/USD):", value=930, step=10)
            st.info("El IVA (19%) no es un costo final, pero debe considerarse para el flujo de caja inicial en aduanas.")

        # Cálculos de importación en USD
        cif = precio_fob + flete_seguro
        costo_arancelario = cif * (arancel / 100)
        landed_cost_usd = cif + costo_arancelario
        iva_importacion_usd = landed_cost_usd * 0.19
        
        st.divider()
        
        # Integración y Margen
        st.subheader("2. Integración de Sistemas (BOS) y Margen Comercial")
        col_bos1, col_bos2 = st.columns(2)
        
        with col_bos1:
            costo_pcs = st.number_input("Costo Inversor PCS Externo (USD):", value=0.0, step=500.0)
            costo_ems = st.number_input("Costo Integración EMS/Comunicaciones (USD):", value=1500.0, step=500.0)
        with col_bos2:
            margen = st.slider("Margen Neto de Comercialización (%):", min_value=5.0, max_value=100.0, value=30.0, step=1.0)
            
        capex_total_usd = landed_cost_usd + costo_pcs + costo_ems
        precio_venta_usd = capex_total_usd / (1 - (margen/100))
        ganancia_neta_usd = precio_venta_usd - capex_total_usd

        st.divider()
        
        # --- NUEVA SECCIÓN: Selector de Moneda y Resultados ---
        st.subheader("📊 Resultados Financieros del Proyecto")
        moneda_vista = st.radio("Mostrar resultados en:", ["USD (Dólares)", "CLP (Pesos Chilenos)"], horizontal=True)
        
        # Lógica de conversión dinámica
        es_clp = "CLP" in moneda_vista
        simbolo = "CLP" if es_clp else "USD"
        factor_conv = tc if es_clp else 1.0
        fmt = ",.0f" if es_clp else ",.2f" # Sin decimales para CLP, 2 decimales para USD
        
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.markdown("### Costos de Adquisición e Integración")
            st.info(f"**Costo Puesto en Chile (Neto DDP):** ${landed_cost_usd * factor_conv:{fmt}} {simbolo}")
            st.caption(f"Requerimiento de Caja (IVA importación): ${iva_importacion_usd * factor_conv:{fmt}} {simbolo}")
            st.warning(f"**Costo Total de Inversión (CAPEX con BOS):** ${capex_total_usd * factor_conv:{fmt}} {simbolo}")

        with col_res2:
            st.markdown("### Proyección Comercial")
            st.success(f"**PRECIO DE VENTA SUGERIDO:** ${precio_venta_usd * factor_conv:{fmt}} {simbolo}")
            st.metric(f"Ganancia Neta Proyectada ({simbolo})", f"${ganancia_neta_usd * factor_conv:{fmt}}")

        st.divider()

        # Costo Nivelado (LCOS)
        st.subheader("3. Argumento de Venta a Largo Plazo: LCOS")
        st.latex(r"LCOS = \frac{CAPEX}{\text{Capacidad Útil} \times \text{Ciclos de Vida} \times \text{DoD}}")
        
        col_lcos1, col_lcos2 = st.columns(2)
        
        with col_lcos1:
            ciclos = st.number_input("Ciclos de Vida Garantizados:", value=6000, step=500)
            dod = st.slider("Profundidad de Descarga (DoD) permitida (%):", min_value=50, max_value=100, value=90) / 100
            
        with col_lcos2:
            energia_total_almacenada = capacidad * ciclos * dod
            lcos_usd = capex_total_usd / energia_total_almacenada
            
            # Formato especial para el LCOS (requiere decimales incluso en CLP)
            fmt_lcos = ",.2f" if es_clp else ",.4f"
            
            st.info(f"Energía total circulada en la vida útil: **{energia_total_almacenada:,.0f} kWh**")
            st.success(f"**LCOS (Costo por kWh almacenado):** ${lcos_usd * factor_conv:{fmt_lcos}} {simbolo}")
