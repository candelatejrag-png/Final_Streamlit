import streamlit as st
import pandas as pd


# configuramos la pagina
st.set_page_config(page_title='Dashboard de Ventas', page_icon='', layout='wide', initial_sidebar_state='expanded')


# titulo principal
st.title('Dashboard de Ventas - Empresa de Alimentación')
st.write('Dashboard solicitado por CEO y Jefe de Ventas')
st.divider()


# cargamos los datos con la cache
def load_data():
    # leemos los dos CSVs
    # para que la url se carge rapido vamos a leer solo las columnas que utilizo en el codigo
    # para ayudar con la velocidad tambien especifico los tipos de esas columnas
    COLS = [
    "id","date","store_nbr","family","sales","onpromotion",
    "holiday_type","locale","locale_name","description","transferred",
    "dcoilwtico","city","state","store_type","cluster","transactions",
    "year","month","week","quarter","day_of_week"]
    DTYPES = {
        "store_nbr": "int16",
        "cluster": "int16",
        "onpromotion": "int32",
        "year": "int16",
        "month": "int8",
        "week": "int16",
        "quarter": "int8",
        "sales": "float32",
        "transactions": "float32",
        "family": "category",
        "state": "category",
        "city": "category",
        "store_type": "category",
        "day_of_week": "category",
        "holiday_type": "category",
        "locale": "category",
        "locale_name": "category",
        "transferred": "boolean",}
    
    df1 = pd.read_csv("parte_1.csv", usecols=COLS, dtype=DTYPES, low_memory=False)
    df2 = pd.read_csv("parte_2.csv", usecols=COLS, dtype=DTYPES, low_memory=False)

    # unimos los dos en un unico df
    df = pd.concat([df1, df2], ignore_index=True)

    # convertimos 'date' a datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # creamos la columna 'year_month' para contar meses reales
    df['year_month'] = df['date'].dt.strftime('%Y-%m')

    # aseguramos que los tipos numericos en ventas y promocion son correctos
    df['sales'] = pd.to_numeric(df['sales'], errors='coerce').fillna(0.0)
    df['onpromotion'] = pd.to_numeric(df['onpromotion'], errors='coerce').fillna(0).astype(int)
    df['transactions'] = pd.to_numeric(df['transactions'], errors='coerce')

    return df


# cargamos los datos
df = load_data()

st.sidebar.title('Filtros')
st.sidebar.divider()


# seleccionamos el rango de fechas
min_date = df['date'].min()
max_date = df['date'].max()

date_range = st.sidebar.date_input('Rango de fechas', value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())

# aplicamos el filtro por fechas
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
    df_f = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
else:
    df_f = df.copy()

st.sidebar.divider()
st.sidebar.write(f'Registros filtrados: {len(df_f)}')

# creamos las pestañas
tab1, tab2, tab3, tab4 = st.tabs(['Pestaña 1 - Global', 'Pestaña 2 - Tienda', 'Pestaña 3 - Estado', 'Pestaña 4 - Extra'])

# PESTAÑA 1: GLOBAL
with tab1:
    st.header('Pestaña 1: Vision global')
    st.write('KPIs globales, rankings y estacionalidad')
    st.divider()

    # a) conteo general
    total_scores = df_f['store_nbr'].nunique()
    total_products = df_f['family'].nunique()
    total_states = df_f['state'].nunique()
    total_months = df_f['year_month'].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f'Tiendas', total_scores)         # sin formatearlo con f'' porque st.metric() siempre exige al menos 2 argumentos!!!
    c2.metric(f'Productos (family)', total_products)
    c3.metric(f'Estados', total_states)
    c4.metric(f'Meses con datos', total_months)

    st.divider()

    # b) analisis en terminos medios/rankings
    # b.i) ranking top 10 producto mas vendidos (sum sales)
    st.subheader('Top 10 productos mas vendidos')
    top_products = (df_f.groupby('family', as_index=False)['sales'].sum().sort_values('sales', ascending=False).head(10).set_index('family'))
    st.bar_chart(top_products)
    st.dataframe(top_products.reset_index(), use_container_width=True)

    st.divider()

    # bii) distribucion de ventas por tiendas
    # para la 'distribucion' usamos la tabla de ventas totales por tienda y un grafico de barras
    st.subheader('Distribucion de ventas por tienda (ventas totales por tienda)')
    sales_by_store = (df_f.groupby('store_nbr', as_index=False)['sales'].sum().sort_values('sales', ascending=False).set_index('store_nbr'))
    st.bar_chart(sales_by_store.head(30))       # mostramos top 30 para que sea legible
    with st.expander('Ver tabla completa por tienda'):
        st.dataframe(sales_by_store.reset_index(), use_container_width=True)
    
    st.divider()

    # biii) top 10 tiendas con ventas en productos en promocion
    st.subheader('Top 10 tiendas con ventas en productos en promocion')
    promo_df = df_f[df_f['onpromotion'] > 0]
    top_promo_stores = (promo_df.groupby('store_nbr', as_index=False)['sales'].sum().sort_values('sales', ascending=False).head(10).set_index('store_nbr'))
    st.bar_chart(top_promo_stores)
    st.dataframe(top_promo_stores.reset_index(), use_container_width=True)

    st.divider()

    # c) estacionalidad
    # ci) dia de la semana con mas ventas por termino medio
    st.subheader('Estacionalidad: ventas medias por dia de la semana')
    dow_avg = (df_f.groupby('day_of_week', as_index=False)['sales'].mean().sort_values('sales', ascending=False).set_index('day_of_week'))
    st.bar_chart(dow_avg)
    st.dataframe(dow_avg.reset_index(), use_container_width=True)

    st.divider()

    # cii) volumen de ventas medio por semana del año (promedio sobre todos los años)
    st.subheader('Estacionalidad: ventas medias por semana del año')
    week_avg = (df_f.groupby('week', as_index=False)['sales'].mean().sort_values('week').set_index('week'))
    st.line_chart(week_avg)
    with st.expander('Ver tabla (ventas medias por semana)'):
        st.dataframe(week_avg.reset_index(), use_container_width=True)

    st.divider()

    # ciii) volumen de ventas medio por mes (promedio sobre todos los años)
    st.subheader('Estacionalidad: ventas medias por mes')
    month_avg = (df_f.groupby('month', as_index=False)['sales'].mean().sort_values('month').set_index('month'))
    st.line_chart(month_avg)
    with st.expander('Ver tabla (ventas medias por mes)'):
        st.dataframe(month_avg.reset_index(), use_container_width=True)


# PESTAÑA 2: POR TIENDA
with tab2:
    st.header('Pestaña 2: Informacion por tienda')
    st.write('Selecciona una tienda para ver métricas y gráficos')
    st.divider()

    # creamos el desplegable de tienda
    stores = sorted(df_f['store_nbr'].dropna().unique().tolist())
    store_selected = st.selectbox(f'Selecciona tienda (store_nbr)', stores)

    # filtramos por tienda
    dstore = df_f[df_f['store_nbr'] == store_selected].copy()

    # a) numero total de ventas por año (sum sales) - ordenado
    st.subheader('Ventas totales por año')
    sales_year = (dstore.groupby('year', as_index=False)['sales'].sum().sort_values('year').set_index('year'))
    st.bar_chart(sales_year)
    st.dataframe(sales_year.reset_index(), use_container_width=True)

    st.divider()

    # b) numero total de productos vendidos (suma de sales)
    # sales = volumen/ventas
    total_products_sold = dstore['sales'].sum()

    # c) numero total de productos vendidos en promocion
    total_products_sold_promo = dstore.loc[dstore['onpromotion'] > 0, 'sales'].sum()

    # mostramos KPIs en columnas
    k1, k2, k3 = st.columns(3)
    k1.metric(f'Total ventas (sales)', total_products_sold)
    k2.metric(f'Ventas en promocion', total_products_sold_promo)
    k3.metric(f'Productos distintos', dstore['family'].nunique())

    st.divider()

    # descargamos los datos filtrados
    st.subheader('Descargar datos de la tienda seleccionada')
    csv_store = dstore.to_csv(index=False)
    st.download_button(label='Descargar CSV (tienda)', data=csv_store, file_name=f'tienda_{store_selected}.csv', mime='text/csv')


# PESTAÑA 3: POR ESTADO
with tab3:
    st.header('Pestaña 3: Información por estado')
    st.write('Selecciona un estado para ver transacciones, ranking de tiendas y producto líder')
    st.divider()

    # creamos desplegable de estado
    states = sorted(df_f['state'].dropna().unique().tolist())
    state_selected = st.selectbox(f'Selecciona estado (state)', states)

    # filtramos por estado
    dstate = df_f[df_f['state'] == state_selected].copy()

    # a) numero total de transacciones por año
    tx = dstate[['date', 'store_nbr', 'year', 'transactions']].drop_duplicates()
    tx_year = (tx.groupby('year', as_index=False)['transactions'].sum().sort_values('year').set_index('year'))
    st.subheader('Transacciones totales por año')
    st.bar_chart(tx_year)
    st.dataframe(tx_year.reset_index(), use_container_width=True)

    st.divider()

    # b) ranking de tiendas con mas ventas (top 10)
    st.subheader('Top 10 tiendas con más ventas en el estado')
    top_state_stores = (dstate.groupby('store_nbr', as_index=False)['sales'].sum().sort_values('sales', ascending=False).head(10).set_index('store_nbr'))
    st.bar_chart(top_state_stores)
    st.dataframe(top_state_stores.reset_index(), use_container_width=True)

    st.divider()

    # c) producto mas vendido en el estado 
    best_product = (dstate.groupby('family', as_index=False)['sales'].sum().sort_values('sales', ascending=False).head(1))
    if len(best_product) == 1:
        st.metric(f'Producto mas vendido (family)', best_product.iloc[0]['family'], best_product.iloc[0]['sales'])
    else:
        st.warning('No hay datos suficientes para calcular el producto más vendido')


# PESTAÑA 4: EXTRA
with tab4:
    st.header('Pestaña 4: Extra (insight)')
    st.write('Gráficos adicionales para acelerar conclusiones')
    st.divider()

    # 1
    st.subheader('¿Cómo influyen las promociones en ventas medias?')
    show_table = st.checkbox('Mostrar tabla comparativa (promoción vs no promoción)')

    aux = df_f.copy()
    aux['promo_flag'] = aux['onpromotion'].apply(lambda x: 'Promoción' if x > 0 else 'Sin promoción')

    promo_compare = (aux.groupby('promo_flag', as_index=False)['sales'].mean().sort_values('sales', ascending=False).set_index('promo_flag'))

    st.bar_chart(promo_compare)

    if show_table:
        st.dataframe(promo_compare.reset_index(), use_container_width=True)

    st.divider()

    # 2. evolución mensual de ventas
    st.subheader('Evolución mensual de ventas totales')
    monthly_sales = (df_f.groupby('year_month', as_index=False)['sales'].sum().sort_values('year_month').set_index('year_month'))
    st.line_chart(monthly_sales)
    with st.expander('Ver tabla (ventas mensuales)'):
        st.dataframe(monthly_sales.reset_index(), use_container_width=True)

    st.divider()

    st.caption('Desarrollado con Streamlit')