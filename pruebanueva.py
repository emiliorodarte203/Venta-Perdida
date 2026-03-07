import pandas as pd
import glob
import os
import streamlit as st
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import subprocess

 
# Get a list of all CSV files in a directory
csv_files = glob.glob('C:/Users/erodarteg/OneDrive - ICONN/Cigarros 2026/Venta Pérdida (317B)/*.csv')
venta_semanal = glob.glob('C:/Users/erodarteg/OneDrive - ICONN/Cigarros 2026/Venta semanal (microstrategy)/*.xlsx')
excel = ("C:\\Users\\erodarteg\\OneDrive - ICONN\\Cigarros 2026\\Inv\\MASTER.xlsx")
MASTER = pd.read_excel(excel)
 
st.set_page_config(page_title="Reporte de Venta Pérdida Cigarros y RRPS", page_icon="🚬", layout="wide", initial_sidebar_state="expanded")
st.title("📊 Reporte de Venta Perdida Cigarros y RRPS 🚬")
st.markdown("✅ Se incluyen datos de las últimas 6 semanas.", unsafe_allow_html=True)
kpi_top = st.container()
 
   
 
 
# Definir paleta de colores global
pio.templates["colors"] = pio.templates["plotly"]
pio.templates["colors"].layout.colorway = ['#2C7865', '#EE2526', '#FF9800', '#000000']
pio.templates["colors2"] = pio.templates["plotly"]
pio.templates["colors2"].layout.colorway = ['#2C7865', '#EE2526', '#FF9800', '#000000']
# Aplicar plantilla personalizada por defecto
pio.templates.default = "colors"
pio.templates.default2 = "colors2"
 
#---------------------------------------------------------------------
@st.cache_data
def venta_perdida(csv_files):
    # Función para calcular la semana contable
    def calcular_dia(fecha):
        return fecha.isocalendar()[1]
 
    combined_df = pd.DataFrame()  # Crear un DataFrame vacío para almacenar todos los datos
 
    # Loop through each CSV file and append its contents to the combined dataframe
    for csv_file in csv_files:
        df = pd.read_csv(csv_file, encoding='ISO-8859-1')
       
        # Extraer el nombre del archivo sin la ruta completa y sin la extensión .csv
        file_name = os.path.splitext(os.path.basename(csv_file))[0]
        df['Día'] = file_name
       
        # Asumir que el nombre del archivo es la fecha en formato 'ddmmyyyy'
        df['Fecha'] = pd.to_datetime(file_name, format='%d%m%Y', errors='coerce')
       
        # Calcular la semana contable
        iso = df['Fecha'].dt.isocalendar()
        df['Semana Contable'] = iso['year'].astype(str) + iso['week'].astype(str).astype(str).str.zfill(2)
       
        # Concatenar el DataFrame actual al DataFrame combinado
        combined_df = pd.concat([combined_df, df])
 
    # Eliminar las columnas no deseadas
    combined_df = combined_df.drop(columns=['UPC','CAMPO', 'INVENTARIO_UDS','INVENTARIO_PESOS','VENTA_UDS_PTD','VENTA_PESOS_PTD','NUM_TIENDA','NOMBRE_TIENDA','ESTATUS', 'PROVEEDOR', 'Fecha', 'CATEGORIA'])
    combined_df['DIVISION'] = combined_df['DIVISION'].astype(str).str[:2]
    combined_df['PLAZA'] = combined_df['PLAZA'].astype(str).str[:3]
    combined_df['MERCADO'] = combined_df['MERCADO'].astype(str).str[1:]
    combined_df = combined_df.dropna(subset=['VENTA_PERDIDA_PESOS','ID_ARTICULO'])
    combined_df['ID_ARTICULO'] = combined_df['ID_ARTICULO'].astype(float).astype(int).astype(str)
    combined_df['VENTA_PERDIDA_PESOS'] = combined_df['VENTA_PERDIDA_PESOS'].round(0).astype('int64')
    combined_df = combined_df.rename(columns={
        'ID_ARTICULO': 'ARTICULO',
    })
 
    # Mover la columna 'Día' a la primera posición
    cols = ['Día', 'Semana Contable'] + [col for col in combined_df.columns if col not in ['Día', 'Semana Contable']]
    combined_df = combined_df[cols]
    #combined_df = combined_df.drop(columns=['Día'])
    return combined_df
 
#---------------------------------------------------------------------
@st.cache_data
def venta(venta_semanal):
    concat_venta = pd.DataFrame()
 
    for xlsx_file in venta_semanal:
        try:
            df2 = pd.read_excel(xlsx_file)
           
            # Verificar si ya existe la columna 'Semana Contable'
            if 'Semana Contable' not in df2.columns:
                print(f"Advertencia: La columna 'Semana Contable' no existe en {xlsx_file}.")
                continue  # Salta este archivo si no tiene la columna necesaria
           
            # Asegúrate de que la columna 'Semana Contable' sea de tipo object
            df2['Semana Contable'] = df2['Semana Contable'].astype(str)
           
            # Concatenar los datos
            concat_venta = pd.concat([concat_venta, df2], ignore_index=True)
       
        except Exception as e:
            print(f"Error al procesar el archivo {xlsx_file}: {e}")
   
    # Reorganizar columnas si es necesario
    if 'Semana Contable' in concat_venta.columns:
        cols2 = ['Semana Contable'] + [col2 for col2 in concat_venta.columns if col2 not in ['Semana Contable']]
        concat_venta = concat_venta[cols2]
 
    col = 'Venta Neta Total'
    concat_venta[col] = (
    concat_venta[col]
    .astype(str)
    .str.replace(r'[\$,]', '', regex=True)   # quita $ y comas
    .str.replace(r'\((.*?)\)', r'-\1', regex=True)  # convierte (56.03) → -56.03
)

    concat_venta[col] = (
    pd.to_numeric(concat_venta[col], errors='coerce')
    .fillna(0)
    .round(0)
    .astype('int64')
)

 
 
    # Eliminar columnas específicas no deseadas
    columnas_a_eliminar = [col for col in concat_venta.columns if 'Unnamed' in col] + ['Metrics']
    concat_venta = concat_venta.drop(columns=columnas_a_eliminar, errors='ignore')
    #concat_venta = concat_venta.dropna(subset=['Venta Neta Total', 'Artículo' ])
    print(concat_venta['División'].unique())
    concat_venta['División'] = concat_venta['División'].astype(float).astype(int).astype(str)
    concat_venta['Plaza'] = concat_venta['Plaza'].astype(float).astype(int).astype(str)
    concat_venta['Mercado'] = concat_venta['Mercado'].astype(float).astype(int).astype(str)
    concat_venta['Artículo'] = concat_venta['Artículo'].astype(float).astype(int).astype(str)
    concat_venta['Semana Contable'] = concat_venta['Semana Contable'].astype('str')
    concat_venta['Venta Neta Total'] = concat_venta['Venta Neta Total'].fillna(0).round(0).astype('int64')
    concat_venta = concat_venta.rename(columns={
        'Artículo': 'ARTICULO',
        'División': 'DIVISION',
        'Plaza': 'PLAZA',
        'Mercado': 'MERCADO',
    })
 
    return concat_venta
 
 
 
#---------------------------------------------------------------------
 
# Cargar los DataFrames por separado
VENTA_PERDIDA = venta_perdida(csv_files)
VENTA = venta(venta_semanal)
MASTER['ARTICULO'] = MASTER['ARTICULO'].astype(str)
 
 #---------------------------------------------------------------------
# 🔒 FILTRAR SOLO LAS ÚLTIMAS 6 SEMANAS REALES

# Asegurar formato numérico YYYYWW
VENTA_PERDIDA['Semana Contable'] = (
    VENTA_PERDIDA['Semana Contable']
    .astype(str)
    .str.replace(r'\D', '', regex=True)
    .astype(int)
)

VENTA['Semana Contable'] = (
    VENTA['Semana Contable']
    .astype(str)
    .str.replace(r'\D', '', regex=True)
    .astype(int)
)

# Obtener semanas disponibles reales (diario + semanal)
semanas_disponibles = (
    pd.concat([
        VENTA_PERDIDA['Semana Contable'],
        VENTA['Semana Contable']
    ])
    .dropna()
    .drop_duplicates()
    .sort_values()
)

# Últimas 6 semanas
ultimas_6_semanas = semanas_disponibles.tail(10).tolist()

# Filtrar dataframes
VENTA_PERDIDA = VENTA_PERDIDA[VENTA_PERDIDA['Semana Contable'].isin(ultimas_6_semanas)]
VENTA = VENTA[VENTA['Semana Contable'].isin(ultimas_6_semanas)]

 
familia_dict = MASTER.set_index('ARTICULO')['FAMILIA'].to_dict()
segmento_dict = MASTER.set_index('ARTICULO')['SEGMENTO'].to_dict()
subcategoria_dict = MASTER.set_index('ARTICULO')['SUBCATEGORIA'].to_dict()
proveedor_dict = MASTER.set_index('ARTICULO')['PROVEEDOR'].to_dict()
 
VENTA_PERDIDA['FAMILIA'] = VENTA_PERDIDA['ARTICULO'].map(familia_dict)
VENTA_PERDIDA['SEGMENTO'] = VENTA_PERDIDA['ARTICULO'].map(segmento_dict)
VENTA_PERDIDA['SUBCATEGORIA'] = VENTA_PERDIDA['ARTICULO'].map(subcategoria_dict)
VENTA_PERDIDA['PROVEEDOR'] = VENTA_PERDIDA['ARTICULO'].map(proveedor_dict)
 
 
VENTA['FAMILIA'] = VENTA['ARTICULO'].map(familia_dict)
VENTA['SEGMENTO'] = VENTA['ARTICULO'].map(segmento_dict)
VENTA['SUBCATEGORIA'] = VENTA['ARTICULO'].map(subcategoria_dict)
VENTA['PROVEEDOR'] = VENTA['ARTICULO'].map(proveedor_dict)
 
VENTA_PERDIDA = VENTA_PERDIDA.dropna(subset=['PROVEEDOR'])
 
 
 
# Diccionario de mapeo de códigos de plaza a nombres
map_plaza = {
    "100": "Reynosa",
    "110": "Matamoros",
    "200": "México",
    "300": "Jalisco",
    "400": "Coahuila (Saltillo)",
    "410": "Coahuila (Torreón)",
    "500": "Nuevo León",
    "600": "Baja California (Tijuana)",
    "610": "Baja California (Ensenada)",
    "620": "Baja California (Mexicali)",
    "650": "Sonora (Hermosillo)",
    "700": "Puebla",
    "720": "Morelos",
    "800": "Yucatán",
    "890": "Quintana Roo",
}
 
# Aplicar el mapeo al DataFrame
VENTA['PLAZA'] = VENTA['PLAZA'].apply(lambda x: map_plaza.get(x, x))
VENTA_PERDIDA['PLAZA'] = VENTA_PERDIDA['PLAZA'].apply(lambda x: map_plaza.get(x, x))
 
 
map_division = {
    "10": "Coah-Tamps",
    "20": "México-Península",
    "30": "Pacífico",
    "50": "Nuevo León",
}
 
# Aplicar el mapeo al DataFrame
VENTA['DIVISION'] = VENTA['DIVISION'].map(map_division)
VENTA_PERDIDA['DIVISION'] = VENTA_PERDIDA['DIVISION'].map(map_division)
 
plazas_acacia = {
    "100": "Reynosa",
    "110": "Matamoros",
    "200": "México",
    "300": "Jalisco",
    "400": "Coahuila (Saltillo)",
    "410": "Coahuila (Torreón)",
    "500": "Nuevo León",
    "600": "Baja California (Tijuana)",
    "610": "Baja California (Ensenada)",
    "620": "Baja California (Mexicali)",
    "650": "Sonora (Hermosillo)",
    "700": "Puebla",
    "720": "Morelos",
    "800": "Yucatán",
    "890": "Quintana Roo",
}
 
 
# Calcular la suma de 'Venta Neta Total'
if 'Venta Neta Total' in VENTA.columns:
    suma_venta_neta_total = VENTA['Venta Neta Total'].sum()
    print(f"Suma total de 'Venta Neta Total': {suma_venta_neta_total}")
else:
    print("La columna 'Venta Neta Total' no existe en el DataFrame.")
 
#---------------------------------------------------------------------
st.sidebar.image("https://raw.githubusercontent.com/Edwinale20/Sdkiap/main/folder/el-logo.png", width=170)
st.sidebar.title("Filtros 🔠")
 
 
# Paso 1: Crear una lista de opciones para el filtro, incluyendo "Ninguno"
opciones_proveedor = ['Ninguno'] + list(VENTA_PERDIDA['PROVEEDOR'].unique())
proveedor = st.sidebar.selectbox('Seleccione el Proveedor', opciones_proveedor)
 
opciones_division = ['Ninguno'] + list(VENTA_PERDIDA['DIVISION'].unique())
division = st.sidebar.selectbox('Seleccione la División', opciones_division)
 
# Paso 2 - Sidebar para elegir filtro
tipo_filtro_acacia = st.sidebar.selectbox(
    'Seleccione la Plaza 🏪',
    ['Total plazas', 'Plazas 🏪']
)
 
# Paso 3 - Mostrar multiselect solo si quiere filtrar
if tipo_filtro_acacia == 'Plazas 🏪':
    opciones_plaza_acacia = list(set(plazas_acacia.values()))
    plazas_acacia_seleccionadas = st.sidebar.multiselect('Plazas 🏪', opciones_plaza_acacia)
else:
    plazas_acacia_seleccionadas = []  # No selecciona nada
 
# BUSCADOR MULTI PARA ARTÍCULOS
    
opciones_mercado = ['Ninguno'] + list(VENTA_PERDIDA['MERCADO'].unique())
mercado = st.sidebar.selectbox('Seleccione el Mercado', opciones_mercado)
 
opciones_semana = ['Ninguno'] + list(VENTA_PERDIDA['Semana Contable'].unique())
semana = st.sidebar.selectbox('Seleccione la semana', opciones_semana)
 
opciones_familia = ['Ninguno'] + list(VENTA_PERDIDA['FAMILIA'].unique())
familia = st.sidebar.selectbox('Seleccione la Familia', opciones_familia)
 
opciones_categoria = ['Ninguno'] + list(VENTA_PERDIDA['SUBCATEGORIA'].unique())
categoria = st.sidebar.selectbox('Seleccione la Categoria', opciones_categoria)
 
 
# Filtrar por Proveedor
if proveedor == 'Ninguno':
    df_venta_perdida_filtrada = VENTA_PERDIDA
    df_venta_filtrada = VENTA
else:
    df_venta_perdida_filtrada = VENTA_PERDIDA[VENTA_PERDIDA['PROVEEDOR'] == proveedor]
    df_venta_filtrada = VENTA[VENTA['PROVEEDOR'] == proveedor]
 
 
# Filtrar por División
if division != 'Ninguno':
    df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['DIVISION'] == division]
    df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['DIVISION'] == division]
 
# Paso 3 - Filtrar solo si seleccionó plazas
if plazas_acacia_seleccionadas:
    df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['PLAZA'].isin(plazas_acacia_seleccionadas)]
    df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['PLAZA'].isin(plazas_acacia_seleccionadas)]
 
# Filtrar por Mercado
if mercado != 'Ninguno':
    df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['MERCADO'] == mercado]
    df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['MERCADO'] == mercado]
 
# Filtrar por Semana
if semana != 'Ninguno':
    df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'] == semana]
    df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['Semana Contable'] == semana]
 
# Filtrar por Familia
if familia != 'Ninguno':
    df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['FAMILIA'] == familia]
    df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['FAMILIA'] == familia]
 
# Filtrar por Categoria
if categoria != 'Ninguno':
    df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['SUBCATEGORIA'] == categoria]
    df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['SUBCATEGORIA'] == categoria]
 

# Modificar la columna 'Semana Contable' en ambos DataFrames
# Semana Contable se queda como texto ordenable: YYYY-WWW (ej: 2025-W52, 2026-W01)
for d in (df_venta_perdida_filtrada, df_venta_filtrada):
    wk = pd.to_numeric(d['Semana Contable'], errors='coerce').astype('Int64')
    s  = wk.astype(str).str.zfill(6)
    d['Semana Contable'] = s.str[:4] + "-Sem " + s.str[-2:]
 
df_venta_perdida_filtrada = df_venta_perdida_filtrada[df_venta_perdida_filtrada['FAMILIA'] != 'BYE']
df_venta_filtrada = df_venta_filtrada[df_venta_filtrada['FAMILIA'] != 'BYE']
 
 
 
#--------------------------------------------------------------------
 
# Aplicar plantilla personalizada por defecto
 
@st.cache_data
def graficar_porcentaje_venta_perdida_por_semana(df_venta_filtrada, df_venta_perdida_filtrada):
    # Filtrar semanas comunes
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_filtrada_suma = df_venta_filtrada[df_venta_filtrada['Semana Contable'].isin(semanas_comunes)].groupby('Semana Contable')['Venta Neta Total'].sum().reset_index()
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)].groupby('Semana Contable')['VENTA_PERDIDA_PESOS'].sum().reset_index()
 
    # Calcular el porcentaje de venta perdida sobre la venta neta total
    df_combined = pd.merge(df_venta_filtrada_suma, df_venta_perdida_filtrada_suma, on='Semana Contable')
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total'].replace(0, np.nan)) * 100
 
    # Crear la gráfica de líneas solo con el % de venta perdida
    fig = go.Figure(go.Scatter(
        x=df_combined['Semana Contable'],
        y=df_combined['% Venta Perdida'],
        mode='lines+markers+text',
        name='% Venta Perdida',
        hovertemplate='% de Venta Perdida: %{y:.2f}%',
        text=df_combined['% Venta Perdida'].apply(lambda x: f'{x:.2f}%'),
        textposition='top center'  # Posición de las etiquetas
    ))
 
    # Configurar el diseño de la gráfica
    fig.update_layout(
        title='Venta Perdida semanal 🗓️',
        title_font=dict(size=20),
        #xaxis=dict(title='Semana Contable'),
        yaxis=dict(title='% de Venta Perdida'),
        yaxis_tickformat=".2f",  # Formato de los ticks del eje y
        template="colors"  # Aplicar la plantilla personalizada
    )
 
    fig.update_traces(
    textposition="top left",
    textfont=dict(size=18)  # Ajusta el valor de size según tus preferencias
    )
 
    return fig
 
# Uso de la función
figura = graficar_porcentaje_venta_perdida_por_semana(df_venta_filtrada, df_venta_perdida_filtrada)
 
 
@st.cache_data
def graficar_venta_perdida_por_proveedor_y_semana(df_venta_perdida_filtrada, df_venta_filtrada):
    # Filtrar semanas comunes
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)]
 
    # Agrupar por Proveedor y Semana Contable para sumar la venta perdida
    df_venta_perdida_por_proveedor_y_semana = df_venta_perdida_filtrada_suma.groupby(['Semana Contable', 'PROVEEDOR'])['VENTA_PERDIDA_PESOS'].sum().reset_index()
 
    # Agrupar por Semana Contable para sumar la venta neta total
    df_venta_filtrada_suma = df_venta_filtrada[df_venta_filtrada['Semana Contable'].isin(semanas_comunes)].groupby('Semana Contable')['Venta Neta Total'].sum().reset_index()
 
    # Calcular el porcentaje de venta perdida sobre la venta neta total
    df_combined = pd.merge(df_venta_perdida_por_proveedor_y_semana, df_venta_filtrada_suma, on='Semana Contable', how='left')
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total'].replace(0, np.nan)) * 100
 
    # Crear la gráfica de líneas por proveedor
    fig = go.Figure()
 
    # Añadir una línea por cada proveedor
    proveedores = df_combined['PROVEEDOR'].unique()
    for proveedor in proveedores:
        df_proveedor = df_combined[df_combined['PROVEEDOR'] == proveedor]
        fig.add_trace(go.Scatter(
            x=df_proveedor['Semana Contable'],
            y=df_proveedor['% Venta Perdida'],
            mode='lines+markers',
            name=proveedor,
            hovertemplate=(
                '%{x}<br>'
                '% Venta Perdida: %{y:.2f}%<br>'
                '<b>Venta Perdida $:</b> %{customdata[0]:,.0f}'
                '<extra></extra>'),
            customdata=df_proveedor[['VENTA_PERDIDA_PESOS']].values
 
        ))
 
    # Configurar el diseño de la gráfica
    fig.update_layout(
        title='Venta Perdida semanal por Proveedor 🗓️',
        title_font=dict(size=20),
        xaxis=dict(title='Semana Contable'),
        yaxis=dict(title='% de Venta Perdida'),
        yaxis_tickformat=".2f",  # Formato de los ticks del eje y
        template="plotly"  # Aplicar la plantilla personalizada
    )
 
    return fig
 
# Uso de la función
figura2 = graficar_venta_perdida_por_proveedor_y_semana(df_venta_perdida_filtrada, df_venta_filtrada)
 
 
 
 
@st.cache_data
def graficar_venta_perdida_por_subcategoria(df_venta_filtrada, df_venta_perdida_filtrada):
    # Filtrar semanas comunes y sumar las ventas por subcategoría y semana
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)]
    df_venta_perdida_suma = df_venta_perdida_filtrada_suma.groupby(['Semana Contable', 'SUBCATEGORIA'])['VENTA_PERDIDA_PESOS'].sum().reset_index()
   
    # Calcular el porcentaje de venta perdida respecto a la venta neta
    df_venta_suma = df_venta_filtrada[df_venta_filtrada['Semana Contable'].isin(semanas_comunes)].groupby('Semana Contable')['Venta Neta Total'].sum().reset_index()
    df_venta_perdida_suma = pd.merge(df_venta_perdida_suma, df_venta_suma, on='Semana Contable')
    df_venta_perdida_suma['% Venta Perdida'] = (df_venta_perdida_suma['VENTA_PERDIDA_PESOS'] / df_venta_perdida_suma['Venta Neta Total'].replace(0, np.nan)) * 100
 
    # Crear la gráfica apilada
    fig = px.bar(
        df_venta_perdida_suma,
        x='Semana Contable',
        y=df_venta_perdida_suma['VENTA_PERDIDA_PESOS'] / 1e6,  # Convertir a millones
        color='SUBCATEGORIA',
        text='% Venta Perdida',
        title='Venta Perdida por Categoria 📊',
        labels={'VENTA_PERDIDA_PESOS': 'Venta Perdida en Pesos (M)'},
        hover_data={'% Venta Perdida': ':.1f'}
    )
 
 
    # Ajustar el diseño para mostrar las etiquetas de porcentaje
    fig.update_traces(
        texttemplate='%{text:.2f}%',
        textposition='inside',
        hovertemplate='%{x}<br>$%{y:.2f}M de pesos<br>%{text:.1f}% de Venta Perdida')
 
 
    # Configurar el layout
    fig.update_layout(title_font=dict(size=20), barmode='stack',  template="colors", yaxis=dict(title='Venta Perdida en Pesos'))
 
    return fig
 
# Uso de la función
figura3 = graficar_venta_perdida_por_subcategoria(df_venta_filtrada, df_venta_perdida_filtrada)
 
 
@st.cache_data
def graficar_venta_perdida_por_mercado_lineas(df_venta_filtrada, df_venta_perdida_filtrada):
    # Filtrar semanas comunes
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_filtrada_suma = df_venta_filtrada[df_venta_filtrada['Semana Contable'].isin(semanas_comunes)]
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)]
   
    # Sumar las ventas netas y perdidas por mercado y semana
    df_venta_suma = df_venta_filtrada_suma.groupby(['Semana Contable', 'MERCADO'])['Venta Neta Total'].sum().reset_index()
    df_venta_perdida_suma = df_venta_perdida_filtrada_suma.groupby(['Semana Contable', 'MERCADO'])['VENTA_PERDIDA_PESOS'].sum().reset_index()
 
    # Combinar los DataFrames para poder calcular el porcentaje
    df_combined = pd.merge(df_venta_perdida_suma, df_venta_suma, on=['Semana Contable', 'MERCADO'])
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total']) * 100
    # Redondear el porcentaje a un decimal y formatear como texto con el símbolo %
    df_combined['% Venta Perdida'] = df_combined['% Venta Perdida'].round(1).astype(str) + '%'
 
    # Filtrar solo los mercados más grandes para reducir el tamaño de los datos
    mercados_a_mostrar = df_combined.groupby('MERCADO')['VENTA_PERDIDA_PESOS'].sum().nlargest(5).index
    df_combined = df_combined[df_combined['MERCADO'].isin(mercados_a_mostrar)]
 
    # Crear la gráfica de líneas con marcadores y texto
    fig = px.line(df_combined,
                  x='Semana Contable',
                  y='% Venta Perdida',
                  color='MERCADO',
                  title='Venta Perdida semanal por Mercado 🏙️',
                  labels={'% Venta Perdida': '% Venta Perdida'},
                  markers=True,
                  text='% Venta Perdida')  # Añadir el porcentaje de venta perdida como texto
 
    # Configurar el layout para que se muestre el % Venta Perdida en el texto sobre los puntos
    fig.update_traces(textposition="top center")
 
    # Configurar el layout general
    fig.update_layout(title_font=dict(size=20),template="colors", xaxis=dict(title='Semana Contable'), yaxis=dict(title='% Venta Perdida'))
 
    return fig
 
# Uso de la función
figura4 = graficar_venta_perdida_por_mercado_lineas(df_venta_filtrada, df_venta_perdida_filtrada)
 
 
 
 
@st.cache_data
def graficar_venta_perdida_por_familia(df_venta_filtrada, df_venta_perdida_filtrada):
    # Filtrar semanas comunes
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_filtrada_suma = df_venta_filtrada[df_venta_filtrada['Semana Contable'].isin(semanas_comunes)]
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)]
   
    # Sumar las ventas netas y perdidas por familia
    df_venta_suma = df_venta_filtrada_suma.groupby(['Semana Contable', 'FAMILIA'])['Venta Neta Total'].sum().reset_index()
    df_venta_perdida_suma = df_venta_perdida_filtrada_suma.groupby(['Semana Contable', 'FAMILIA'])['VENTA_PERDIDA_PESOS'].sum().reset_index()
 
    # Combinar los DataFrames para poder calcular el porcentaje
    df_combined = pd.merge(df_venta_perdida_suma, df_venta_suma, on=['Semana Contable', 'FAMILIA'])
 
    # Calcular el porcentaje de venta perdida respecto a la venta neta total de la misma familia
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total'].replace(0, np.nan)) * 100
 
    # Crear una tabla pivote para que la familia sea una columna y la semana se muestre en el eje x
    df_pivot = df_combined.pivot(index='Semana Contable', columns='FAMILIA', values='% Venta Perdida').reset_index()
 
    # Definir una paleta de colores personalizada similar a la gráfica de la izquierda
    custom_colors = [
        '#00712D', '#FF9800', '#000080', '#FF6347', '#000000',
        '#FFD700', '#008080', '#CD5C5C', '#FF7F50', '#006400',
        '#8B0000', '#FFDEAD', '#ADFF2F', '#2F4F4F', '#33A85C']
 
    # Crear la gráfica de barras apiladas
    fig = px.bar(df_pivot,
                 x='Semana Contable',
                 y=df_pivot.columns[1:],  # Excluyendo la columna 'Semana Contable'
                 title='Venta Perdida por Familia de artículos 📚',
                 labels={'value': '% Venta Perdida', 'variable': 'Familia'},
                 hover_name='Semana Contable',
                 color_discrete_sequence=custom_colors)  # Aplicando la paleta de colores personalizada
 
    # Configurar el layout para que solo se muestre el % Venta Perdida en el hover
    fig.update_traces(hovertemplate='%{y:.1f}%')
 
    # Configurar el layout general
    fig.update_layout(title_font=dict(size=20),
                      xaxis=dict(title='Semana Contable'),
                      yaxis=dict(title='% Venta Perdida'))
 
    return fig
 
# Uso de la función
figura5 = graficar_venta_perdida_por_familia(df_venta_filtrada, df_venta_perdida_filtrada)
 
 
@st.cache_data
def graficar_venta_perdida_por_segmento(df_venta_filtrada, df_venta_perdida_filtrada):
    # Sumar las ventas netas y perdidas por segmento
    df_venta_suma = df_venta_filtrada.groupby('SEGMENTO').agg({'Venta Neta Total': 'sum'}).reset_index()
    df_venta_perdida_suma = df_venta_perdida_filtrada.groupby('SEGMENTO').agg({'VENTA_PERDIDA_PESOS': 'sum'}).reset_index()
 
    # Combinar los DataFrames para calcular el porcentaje
    df_combined = pd.merge(df_venta_perdida_suma, df_venta_suma, on='SEGMENTO', how='inner')
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total']) * 100
 
    # Crear gráfico de barras apilado
    fig = px.bar(df_combined,
                 x='SEGMENTO',
                 y='VENTA_PERDIDA_PESOS',
                 color='% Venta Perdida',
                 text='% Venta Perdida',
                 title='Venta Perdida por segmento 🚬',
                 labels={'VENTA_PERDIDA_PESOS': 'Venta Perdida', 'SEGMENTO': 'SEGMENTO'},
                 color_continuous_scale=px.colors.sequential.Viridis)
 
    # Ajustar layout y formato de texto
    fig.update_layout(
                      title_font=dict(size=20),
                      #xaxis=dict(title='SEGMENTO'),
                      yaxis=dict(title='Venta Perdida'),
                      template="colors2")
   
    fig.update_traces(
        texttemplate='%{text:.2f}%',
        textposition='outside',
        hovertemplate='Venta Perdida: $%{y:,.2f}<br>% Venta Perdida: %{text:.2f}%'
    )
 
    return fig
 
# Uso de la función
figura6 = graficar_venta_perdida_por_segmento(df_venta_filtrada, df_venta_perdida_filtrada)
 
 
 
@st.cache_data
def graficar_venta_perdida_por_plaza(df_venta_perdida_filtrada, df_venta_filtrada):
    # Sumar la venta perdida y venta neta total por plaza y semana
    df_venta_perdida_por_plaza = df_venta_perdida_filtrada.groupby(['Semana Contable', 'PLAZA']).agg({'VENTA_PERDIDA_PESOS': 'sum'}).reset_index()
    df_venta_neta_por_plaza = df_venta_filtrada.groupby(['Semana Contable', 'PLAZA']).agg({'Venta Neta Total': 'sum'}).reset_index()
 
    # Combinar los DataFrames para calcular el porcentaje de venta perdida
    df_combined = pd.merge(df_venta_perdida_por_plaza, df_venta_neta_por_plaza, on=['Semana Contable', 'PLAZA'], how='inner')
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total']) * 100
    df_combined['% Venta Perdida'] = df_combined['% Venta Perdida'].round(1)
 
 
    # Crear gráfico de líneas
    fig = go.Figure()
   
    colores = ['#00712D', '#FF9800', '#000080', '#FF6347', '#000000',
               '#FFD700', '#008080', '#FF7F50', '#006400', '#8B0000',
               '#FFCC66', '#33A85C', '#CD5C5C', '#FFA07A', '#2F4F4F']
 
    for i, plaza in enumerate(df_combined['PLAZA'].unique()):
        df_plaza = df_combined[df_combined['PLAZA'] == plaza]
        fig.add_trace(go.Scatter(
            x=df_plaza['Semana Contable'],
            y=df_plaza['% Venta Perdida'],
            mode='lines+markers+text',
            text=df_plaza['% Venta Perdida'].apply(lambda x: f'{x:.1f}%'),
            textposition='top right',
            name=plaza,
            line=dict(color=colores[i % len(colores)]),  # ← Esto ya funciona bien
            hovertemplate=
                '<b>Plaza:</b> ' + plaza + '<br>' +
                '<b>Semana:</b> %{x}<br>'+
                '<b>% Venta Perdida:</b> %{y:.1f}%<br>'+
                '<b>Venta Perdida $:</b> %{customdata[0]:,.0f}<extra></extra>',
            customdata=df_plaza[['VENTA_PERDIDA_PESOS']].values
        ))
 
 
    fig.update_layout(
        title='Venta Perdida semanal por Plaza 🌄',
        yaxis_title='% Venta Perdida',
        hovermode='closest',
        title_font=dict(size=27),
        showlegend=True
    )
 
   
    fig.update_traces(
    textposition="top right",
    textfont=dict(size=17)  # Ajusta el valor de size según tus preferencias
    )
 
    return fig
 
# Uso de la función
figura7 = graficar_venta_perdida_por_plaza(df_venta_perdida_filtrada, df_venta_filtrada)
 
 
@st.cache_data
def graficar_venta_perdida(df_venta_filtrada, df_venta_perdida_filtrada):
    # Filtrar semanas comunes
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_filtrada_suma = df_venta_filtrada[df_venta_filtrada['Semana Contable'].isin(semanas_comunes)]
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)]
 
    # Sumar las ventas netas y perdidas por división y semana
    df_venta_suma = df_venta_filtrada_suma.groupby(['Semana Contable', 'DIVISION'])['Venta Neta Total'].sum().reset_index()
    df_venta_perdida_suma = df_venta_perdida_filtrada_suma.groupby(['Semana Contable', 'DIVISION'])['VENTA_PERDIDA_PESOS'].sum().reset_index()
 
    # Combinar los DataFrames para calcular el porcentaje
    df_combined = pd.merge(df_venta_perdida_suma, df_venta_suma, on=['Semana Contable', 'DIVISION'])
    df_combined['% Venta Perdida'] = (df_combined['VENTA_PERDIDA_PESOS'] / df_combined['Venta Neta Total']) * 100
 
    # Crear el gráfico estático
    fig = go.Figure()
 
    # Agregar líneas de base con puntos
    for division in df_combined['DIVISION'].unique():
        df_div = df_combined[df_combined['DIVISION'] == division]
        fig.add_trace(go.Scatter(x=df_div['Semana Contable'],
                                 y=df_div['% Venta Perdida'],
                                 mode='lines+markers+text',
                                 name=division,
                                 text=df_div['% Venta Perdida'].apply(lambda x: f'{x:.1f}%'),
                                 textposition='top right',
                                 hovertemplate=
                                    '<b>División:</b> ' + division + '<br>' +
                                    '<b>Semana:</b> %{x}<br>'+
                                    '<b>% Venta Perdida:</b> %{y:.1f}%<br>'+
                                    '<b>Venta Perdida $:</b> %{customdata[0]:,.0f}<extra></extra>',
                                 customdata=df_div[['VENTA_PERDIDA_PESOS']].values
                                         ))
 
    # Configurar el layout
    fig.update_layout(title="Venta Perdida semanal por División 🏴🏳️",
                      title_font=dict(size=20),
                      yaxis_title="% Venta Perdida",
                      hovermode="closest")
 
    return fig
 
# Uso de la función
figura8 = graficar_venta_perdida(df_venta_filtrada, df_venta_perdida_filtrada)
 
@st.cache_data
def graficar_top_venta_perdida_en_dinero(df_venta_filtrada, df_venta_perdida_filtrada, MASTER):
    # Convertir ARTICULO a string para garantizar la conexión con MASTER
    df_venta_filtrada['ARTICULO'] = df_venta_filtrada['ARTICULO'].astype(str)
    df_venta_perdida_filtrada['ARTICULO'] = df_venta_perdida_filtrada['ARTICULO'].astype(str)
    MASTER['ARTICULO'] = MASTER['ARTICULO'].astype(str)
 
    # Crear un diccionario de mapeo ARTICULO -> DESCRIPCIÓN
    articulo_a_descripcion = MASTER.set_index('ARTICULO')['DESCRIPCIÓN'].to_dict()
 
    # Filtrar semanas comunes
    semanas_comunes = set(df_venta_filtrada['Semana Contable']).intersection(set(df_venta_perdida_filtrada['Semana Contable']))
    df_venta_perdida_filtrada_suma = df_venta_perdida_filtrada[df_venta_perdida_filtrada['Semana Contable'].isin(semanas_comunes)]
 
    # Sumar las ventas perdidas por artículo
    df_venta_perdida_suma = df_venta_perdida_filtrada_suma.groupby(['Semana Contable', 'ARTICULO'])['VENTA_PERDIDA_PESOS'].sum().reset_index()
 
    # Calcular el total de venta perdida por artículo para determinar el Top 10
    top_articulos = (
        df_venta_perdida_suma.groupby('ARTICULO')['VENTA_PERDIDA_PESOS']
        .sum()
        .nlargest(10)
        .index
    )
    df_top_venta_perdida = df_venta_perdida_suma[df_venta_perdida_suma['ARTICULO'].isin(top_articulos)]
 
    # Mapear ARTICULO a DESCRIPCIÓN
    df_top_venta_perdida['DESCRIPCIÓN'] = df_top_venta_perdida['ARTICULO'].map(articulo_a_descripcion)
 
    # Crear la gráfica apilada
    fig = px.bar(
        df_top_venta_perdida,
        x='Semana Contable',
        y='VENTA_PERDIDA_PESOS',
        color='DESCRIPCIÓN',  # Usamos DESCRIPCIÓN en lugar de ARTICULO
        color_discrete_sequence = ['#007074', '#FFBF00', '#9694FF', '#222831', '#004225', '#1230AE', '#8D0B41', '#522258',
         '#1F7D53', '#EB5B00', '#0D1282', '#09122C', '#ADFF2F', '#2F4F4F', "#7C00FE", "#D10363", "#16404D"],
        text='VENTA_PERDIDA_PESOS',
        title='Top 10 Artículos con Mayor Venta Perdida (En Pesos)',
        labels={'VENTA_PERDIDA_PESOS': 'Venta Perdida en Pesos', 'DESCRIPCIÓN': 'Descripción del Artículo'},
        hover_data={'VENTA_PERDIDA_PESOS': ':,.2f'} )
   
 
    # Ajustar el diseño para mostrar las etiquetas de valores
    fig.update_traces(
        texttemplate='$%{text:,.2f}',
        textposition='inside',
        hovertemplate='%{x}<br>$%{y:,.2f} pesos<br>'
    )
 
    # Configurar el layout general
    fig.update_layout(
        title_font=dict(size=20),
        barmode='stack',
        #template="colors2",
        yaxis=dict(title='Venta Perdida en Pesos'),
        xaxis=dict(title='Semana Contable')
    )
 
    return fig
 
# Uso de la función
figura9 = graficar_top_venta_perdida_en_dinero(df_venta_filtrada, df_venta_perdida_filtrada, MASTER)
 
#---------------------------------------------------------------------
# Divisor y encabezado
# Primera parte
st.divider()
st.subheader(':orange[Comparación de Venta perdida por Semana y Categoria]')
c1, c6, c3 = st.columns([4, 3, 4])
 
with c1:
    st.plotly_chart(figura, use_container_width=True)
with c6:
    st.plotly_chart(figura6, use_container_width=True)
with c3:
    st.plotly_chart(figura3, use_container_width=True)
# Segunda parte
st.divider()
st.subheader(':orange[Comparación por División y Plaza]')
c4, c5 = st.columns([4, 4])
 
with c4:
    st.plotly_chart(figura7, use_container_width=True)
 
with c5:    
    st.plotly_chart(figura8, use_container_width=True)
 
# Tercera parte
st.divider()
st.subheader(':orange[Comparación de Venta perdida por Mercado y División]')
c6, c7, c8 = st.columns([4, 3, 4])
 
with c6:
    st.plotly_chart(figura4, use_container_width=True)
with c7:
    st.plotly_chart(figura5, use_container_width=True)
with c8:
    st.plotly_chart(figura2, use_container_width=True)
 
# Cuarta parte
st.divider()
st.subheader(':orange[Artículos con mayor venta perdida]')
c9 = st.columns([4])  # Si planeas añadir más columnas, ajusta los pesos.
with c9[0]:  
    st.plotly_chart(figura9, use_container_width=True)
 
MASTER['ARTICULO'] = MASTER['ARTICULO'].astype(str)
articulo_a_descripcion = MASTER.set_index('ARTICULO')['DESCRIPCIÓN'].to_dict()
 
def Fig10(df_venta_perdida_filtrada, df_venta_filtrada, articulo_a_descripcion=None):
    def pick(df, opciones):
        return next((c for c in opciones if c in df.columns), None)
 
    col_articulo = pick(df_venta_perdida_filtrada, ["ARTICULO","Artículo","ARTÍCULO"])
    col_plaza    = pick(df_venta_perdida_filtrada, ["PLAZA","Plaza"])
    col_mercado  = pick(df_venta_perdida_filtrada, ["MERCADO","Mercado"])
    col_semana   = pick(df_venta_perdida_filtrada, ["Semana Contable","SEMANA_CONTABLE"])
 
    df_combined = pd.merge(
        df_venta_perdida_filtrada,
        df_venta_filtrada,
        on=[col_articulo,col_plaza,col_mercado,col_semana],
        how="inner"
    )
 
    df_combined['% Venta Perdida'] = (
        df_combined['VENTA_PERDIDA_PESOS'] /
        df_combined['Venta Neta Total'].replace(0, np.nan)
    ) * 100
 
    # Últimas 3 semanas
    ult_3_sem = sorted(df_combined[col_semana].unique(), reverse=True)[:3]
    df_3sem = df_combined[df_combined[col_semana].isin(ult_3_sem)]
 
    # 1️⃣ Artículo → en %
    art_kpi = (
        df_3sem.groupby(col_articulo)[["Venta Neta Total","VENTA_PERDIDA_PESOS"]]
        .sum()
        .assign(pct=lambda d: (d["VENTA_PERDIDA_PESOS"]/d["Venta Neta Total"].replace(0,np.nan))*100)
        .sort_values(["Venta Neta Total","VENTA_PERDIDA_PESOS"], ascending=False)
        .head(1)
    )
    art_code = art_kpi.index[0]
    art_desc = articulo_a_descripcion.get(str(art_code), str(art_code)) if articulo_a_descripcion else str(art_code)
    art_pct  = art_kpi["pct"].iloc[0]
 
    # 2️⃣ Plaza → en pesos $
    ultima_sem = max(df_combined[col_semana])
    plaza_grp = (
        df_combined[df_combined[col_semana]==ultima_sem]
        .groupby(col_plaza)["VENTA_PERDIDA_PESOS"]
        .sum()
    )
    plaza_kpi = plaza_grp.idxmax()
    plaza_vp  = plaza_grp.max()
 
    # 3️⃣ Mercado → en pesos $
    mercado_grp = (
        df_3sem.groupby(col_mercado)["VENTA_PERDIDA_PESOS"]
        .sum()
    )
    mercado_kpi = mercado_grp.idxmax()
    mercado_vp  = mercado_grp.max()
 
    return {
        "Articulo": (art_desc, art_pct),
        "Plaza": (plaza_kpi, plaza_vp),
        "Mercado": (mercado_kpi, mercado_vp)
    }
 
kpis = Fig10(df_venta_perdida_filtrada, df_venta_filtrada, articulo_a_descripcion)
 
with kpi_top:
    c7, c8, c9 = st.columns([4,3,4])
 
    # Artículo en %
    with c7:
        nombre, pct = kpis["Articulo"]
        st.metric("🚨 Artículo 80/20 con alta VP (Últimas 3 semanas)", f"{pct:.2f}%", delta=nombre)
 
    # Plaza en $
    with c8:
        nombre, vp = kpis["Plaza"]
        st.metric("🏬 Plaza con mayor VP (Última semana)", f"${vp:,.0f}", delta=nombre)
 
    # Mercado en $
    with c9:
        nombre, vp = kpis["Mercado"]
        st.metric("🛒 Mercado con mayor VP (Últimas 3 semanas)", f"${vp:,.0f}", delta=nombre)
