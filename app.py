import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import json
import requests


# === DATOS ASISTENTES ===
df_asist = pd.read_excel("Asistentes.xlsx", engine="openpyxl")
df_asist.columns = df_asist.columns.str.strip().str.lower().str.replace(' ', '_')
df_asist['genero'] = df_asist['genero'].replace({'h': 'hombre', 'm': 'mujer', '': 'no especificado', None: 'no especificado'}).fillna('no especificado')

# Dona género
genero_counts = df_asist['genero'].value_counts().reset_index()
genero_counts.columns = ['genero', 'cuenta']
fig_dona = px.pie(genero_counts, names='genero', values='cuenta', hole=0.4, color_discrete_sequence=['#F9E79F', '#D5F5E3', '#E8DAEF'])
fig_dona.update_traces(textinfo='percent+label')
#fig_dona.update_layout(title="Distribución por género", title_x=0.5)

# Entidad - figurines
df_asist['entidad'] = df_asist['entidad'].astype(str).str.strip()
entidades = df_asist['entidad'].value_counts().reset_index()
entidades.columns = ['entidad', 'cuenta']

fig_entidades = go.Figure()
for _, row in entidades.iterrows():
    texto = "👤" * row["cuenta"]
    fig_entidades.add_trace(go.Scatter(
        x=[0], y=[row["entidad"]], mode="text",
        text=[texto], textposition="middle left",
        textfont=dict(size=20), showlegend=False, hoverinfo="skip"
    ))
fig_entidades.update_layout(
    
    title_x=0.5,
    xaxis=dict(visible=False),
    yaxis=dict(tickfont=dict(size=14), automargin=True),
    width=400,
    height=600,
    margin=dict(l=80, r=40, t=50, b=50)
)


porcentaje = (
    df_asist["ambito"]
    .value_counts(normalize=True)
    .mul(100)
    .reset_index()
)

# Renombrar columnas 
porcentaje.columns = ["ambito", "porcentaje"]

# Crear el gráfico de pastel
fig_tipo_entidad = px.pie(
    porcentaje,
    names="ambito",
    values="porcentaje",
    #title="Tipo de entidad (Pública, Privada, Académica)",
    hole=0.4,
    color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]  # Añadido color para 'Académica'
)

fig_tipo_entidad.update_traces(textinfo="percent+label")
fig_tipo_entidad.update_layout(title_x=0.5)
#fig_tipo_entidad.show()

# Calcular el número de asistentes por provincia
provincia_counts = (
    df_asist["provincia"]
    .value_counts()
    .reset_index(name="Asistentes")
    .rename(columns={"index": "provincia"})
)


# Gráfico circular
fig_pie_provincia = px.pie(
    provincia_counts,
    names="provincia",
    values="Asistentes",
    #title="Distribución de asistentes por provincia",
    hole=0.4
)
fig_pie_provincia.update_traces(textinfo="percent+label")
fig_pie_provincia.update_layout(title_x=0.5)

# Contar asistentes por provincia
df = (
    df_asist["provincia"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "provincia", "provincia": "Asistentes"})
)

# Normalizar nombres para que coincidan con el GeoJSON
df["provincia"] = (
    df["provincia"]
    .astype(str)
    .str.strip()
    .replace({
        "Valencia": "València/Valencia",
        "Bavaria": "Alacant/Alicante",
        "Santa Cruz de Tenerife": "Santa Cruz De Tenerife"
    })
)

# Agregar filas para países con 0 asistentes
paises_extra = pd.DataFrame({
    "provincia": ["España", "Portugal", "Francia"],
    "Asistentes": [0, 0, 0]
})

df = pd.concat([df, paises_extra], ignore_index=True)

# 1. Cargar el GeoJSON unificado
with open("provincias_y_paises.geojson", "r", encoding="utf-8") as f:
    geojson_total = json.load(f)


fig = px.choropleth(
    df,  # asegúrate de que df tenga la columna 'provincia'
    geojson=geojson_total,
    locations="provincia",
    featureidkey="properties.provincia",
    color="Asistentes",
    #title="Mapa unificado: provincias españolas + países invitados"
))



# === DATOS TALLER 1 ===
df_t1 = pd.read_excel("Taller1.xlsx", sheet_name="Taller 1. C", engine="openpyxl")
df_t1.columns = df_t1.iloc[1]
df_t1 = df_t1[2:]
df_t1 = df_t1.rename(columns={"Texto": "Texto", "Bloque": "Bloque"})
df_t1_valid = df_t1[["Texto", "Bloque"]].dropna()
df_t1_counts = df_t1_valid.groupby("Bloque").size().reset_index(name="Recuento")

# Crear gráfico de torta para resumen de bloques (usando fig_t1_counts)
fig_t1_pie = px.pie(
    df_t1_counts,
    names="Bloque",
    values="Recuento",
    title="Distribución de aportes por bloque (Taller 1)",
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Pastel
)

# === DATOS TALLER 2 ===
df2 = pd.read_excel("Taller2.xlsx", sheet_name="Taller 1. C", engine="openpyxl")
df2.columns = df2.iloc[1]
df2 = df2[2:]
df2 = df2.rename(columns={"Texto": "Texto", "Bloque": "Bloque", "categoria": "Categoria"})
df_valid = df2[["Texto", "Bloque", "Categoria"]].dropna()
df_exploded = df_valid.assign(Categoria=df_valid["Categoria"].str.split(";")).explode("Categoria")
df_exploded["Categoria"] = df_exploded["Categoria"].str.strip()
bloques_disponibles = sorted(df_exploded["Bloque"].dropna().unique())


footer_img2 = html.Img(src="/assets/Aportes_taller1_por_bloques.png", style={"width": "100%", "marginTop": "40px"})
footer_img3 = html.Img(src="/assets/Aportes_taller2_por_bloques.png", style={"width": "100%", "marginTop": "40px"})

# === APP DASH ===
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Jornada Workshop: “Digitalización del entorno construido: estandarización y aplicaciones prácticas de integración BIM-GIS”", style={"textAlign": "center", "fontSize": "20px", "marginBottom": "30px"}),
    


    
       
    dcc.Tabs([
        dcc.Tab(label="Datos de Asistentes", children=[
            html.Div([
                # Fila 1: Género, Provincia, Ámbito
                html.Div([
                    html.Div([
                        html.H3("Distribución por género", style={"textAlign": "center"}),
                        dcc.Graph(figure=fig_dona)
                    ], style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
    
                    html.Div([
                        html.H3("Provincia de procedencia", style={"textAlign": "center"}),
                        dcc.Graph(figure=fig_pie_provincia)
                    ], style={"width": "32%", "display": "inline-block", "marginLeft": "2%", "verticalAlign": "top"}),
    
                    html.Div([
                        html.H3("Ámbito institucional", style={"textAlign": "center"}),
                        dcc.Graph(figure=fig_tipo_entidad)
                    ], style={"width": "32%", "display": "inline-block", "marginLeft": "2%", "verticalAlign": "top"})
                ], style={"width": "100%", "textAlign": "center", "marginTop": "20px"}),
    
                # Fila 2: Entidades, Mapa
                html.Div([
                    html.Div([
                        html.H3("Participantes por entidad", style={"textAlign": "center"}),
                        dcc.Graph(figure=fig_entidades)
                    ], style={"width": "18%", "display": "inline-block", "verticalAlign": "top"}),
    
                    html.Div([
                        html.H3("Mapa de asistentes por provincia", style={"textAlign": "center"}),
                        dcc.Graph(figure=fig)
                    ], style={"width": "78%", "display": "inline-block", "marginLeft": "4%", "verticalAlign": "top"})
                ], style={"width": "100%", "textAlign": "center", "marginTop": "40px"})
            ])
        ]),
        dcc.Tab(label="TALLER 1 - Aportes por Bloque", children=[
            html.Div([
                # Título y mini-imagen al lado
                html.Div([
                    html.Div([
                        html.Img(src="/assets/Aportes_taller1_por_bloques.png", style={"height": "150px", "marginRight": "5px"})
                    ], style={"display": "inline-block", "verticalAlign": "middle"}),
        
                    html.H2("TALLER 1 Aportes por Bloque", style={
                        "display": "inline-block",
                        "verticalAlign": "middle",
                        "marginBottom": "10px"
                    })
                ], style={"textAlign": "center", "marginTop": "20px"}),
        
                # Fila de gráficos
                html.Div([
                    html.Div([
                        dcc.Graph(id="grafico-t1"),
                        html.Div(id="comentarios-t1", style={"marginTop": "5px", "textAlign": "center"})
                    ], style={"width": "66%", "display": "inline-block", "verticalAlign": "top"}),
        
                    html.Div([
                        dcc.Graph(figure=fig_t1_pie)
                    ], style={"width": "32%", "display": "inline-block", "marginLeft": "2%", "verticalAlign": "top"})
                ], style={"width": "100%", "marginTop": "10px"})
            ])
        ]),
        dcc.Tab(label="TALLER 2 - Categorías por Bloque", children=[
            html.Div([
                html.Div([
                    html.H2("TALLER 2 Aportes por Categoría y Bloque", style={"textAlign": "center"}),
        
                    html.Div([
                        html.Label("Selecciona un bloque:"),
                        dcc.Dropdown(
                            id="selector-bloque",
                            options=[{"label": b, "value": b} for b in bloques_disponibles],
                            value=bloques_disponibles[0]
                        )
                    ], style={"width": "80%", "margin": "0 auto", "textAlign": "center"}),
        
                    # Fila con dos gráficos: barra y torta
                    html.Div([
                        html.Div([
                            dcc.Graph(id="grafico"),
                            html.Div(id="comentarios", style={"marginTop": "5px", "textAlign": "center"})
                        ], style={"width": "49%", "display": "inline-block", "verticalAlign": "top"}),
        
                        html.Div([
                            dcc.Graph(id="grafico_t2_pie")
                        ], style={"width": "49%", "display": "inline-block", "marginLeft": "2%", "verticalAlign": "top"})
                    ])
                ], style={"width": "66%", "display": "inline-block", "verticalAlign": "top"}),
        
                html.Div([
                    footer_img3
                ], style={"width": "32%", "display": "inline-block", "marginLeft": "2%", "verticalAlign": "top"})
            ], style={"width": "100%", "marginTop": "20px"})
        ])
    ])

# === CALLBACK TALLER 1 ===
@app.callback(
    Output("grafico-t1", "figure"),
    Output("comentarios-t1", "children"),
    Input("grafico-t1", "clickData")
)
def mostrar_comentarios_t1(clickData):
    def dividir_en_renglones(texto, palabras_por_linea=2):
        palabras = texto.split()
        renglones = [
            " ".join(palabras[i:i + palabras_por_linea])
            for i in range(0, len(palabras), palabras_por_linea)
        ]
        return "<br>".join(renglones)

    tickvals = df_t1_counts["Bloque"]
    ticktext = [dividir_en_renglones(bloque) for bloque in tickvals]

    fig = px.bar(df_t1_counts, x="Bloque", y="Recuento", title="Notas por Bloque", color_discrete_sequence=["#003366"])

    fig.update_xaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )

    # Ajustes dinámicos según el número de barras
    if len(df_t1_counts) == 1:
        fig.update_layout(
            margin=dict(l=200, r=200),
            width=800
        )
    else:
        fig.update_layout(
            margin=dict(b=180),
            width=1000
        )

    fig.update_layout(
        xaxis_tickangle=0,
        xaxis_tickfont=dict(size=12),
        height=700,
        title_x=0.5
    )

    comentarios_div = html.Div("Haz clic en una barra para ver los comentarios.")
    if clickData:
        bloque = clickData["points"][0]["x"]
        comentarios = df_t1_valid[df_t1_valid["Bloque"] == bloque]["Texto"].dropna().unique().tolist()
        comentarios_div = html.Div([
            html.H4(f"Comentarios para: {bloque}"),
            html.Ul([html.Li(c) for c in comentarios])
        ])
    return fig, comentarios_div


# === CALLBACK TALLER 2 ===
@app.callback(
    Output("grafico", "figure"),
    Output("comentarios", "children"),
    Output("grafico_t2_pie", "figure"),
    Input("selector-bloque", "value"),
    Input("grafico", "clickData")
)



def actualizar_dashboard(bloque_seleccionado, clickData):
    df_bloque = df_exploded[df_exploded["Bloque"] == bloque_seleccionado]
    df_bloque_counts = df_bloque.groupby("Categoria").size().reset_index(name="Recuento")

    def dividir_en_renglones(texto, palabras_por_linea=2):
        palabras = texto.split()
        renglones = [
            " ".join(palabras[i:i + palabras_por_linea])
            for i in range(0, len(palabras), palabras_por_linea)
        ]
        return "<br>".join(renglones)

    tickvals = df_bloque_counts["Categoria"]
    ticktext = [dividir_en_renglones(cat) for cat in tickvals]

    fig_bar = px.bar(df_bloque_counts, x="Categoria", y="Recuento", 
                 title=f"Bloque: {bloque_seleccionado}", 
                 color_discrete_sequence=["#8B0000"])

    fig_bar.update_xaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )

       # Ajuste específico si hay solo una barra
    if len(df_bloque_counts) == 1:
        fig.update_layout(margin=dict(l=200, r=200), width=800)
    else:
        fig.update_layout(margin=dict(b=100), width=1000)

    fig.update_layout(
        xaxis_tickangle=0,
        xaxis_tickfont=dict(size=12),
        height=700
    )
    
    fig.write_html(f"grafico_{bloque_seleccionado}.html")
       # Torta
    fig_pie = px.pie(df_bloque_counts, names="Categoria", values="Recuento",
                     hole=0.4,
                     title="Distribución por categoría")
    fig_pie.update_traces(textinfo="percent+label")


    comentarios_div = html.Div("Haz clic en una barra para ver los comentarios.")
    if clickData:
        categoria = clickData["points"][0]["x"]
        comentarios = df_bloque[df_bloque["Categoria"] == categoria]["Texto"].dropna().unique().tolist()
        comentarios_div = html.Div([
            html.H4(f"Comentarios para: {categoria}"),
            html.Ul([html.Li(c) for c in comentarios])
        ])

    return fig_bar, comentarios_div, fig_pie

# === RUN APP ===
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=1200)


