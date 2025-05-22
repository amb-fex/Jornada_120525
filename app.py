import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# === DATOS ASISTENTES ===
df_asist = pd.read_excel("Asistentes.xlsx", engine="openpyxl")
df_asist.columns = df_asist.columns.str.strip().str.lower().str.replace(' ', '_')
df_asist['genero'] = df_asist['genero'].replace({'h': 'hombre', 'm': 'mujer', '': 'no especificado', None: 'no especificado'}).fillna('no especificado')

# Dona género
genero_counts = df_asist['genero'].value_counts().reset_index()
genero_counts.columns = ['genero', 'cuenta']
fig_dona = px.pie(genero_counts, names='genero', values='cuenta', hole=0.4, color_discrete_sequence=['#F9E79F', '#D5F5E3', '#E8DAEF'])
fig_dona.update_traces(textinfo='percent+label')
fig_dona.update_layout(title="Distribución por género", title_x=0.5)

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
    title="Número de participantes por entidad (👤 = 1 persona)",
    title_x=0.5,
    xaxis=dict(visible=False),
    yaxis=dict(tickfont=dict(size=14), automargin=True),
    width=400,
    height=600,
    margin=dict(l=80, r=40, t=50, b=50)
)

# === DATOS TALLER 1 ===
df_t1 = pd.read_excel("Taller1.xlsx", sheet_name="Taller 1. C", engine="openpyxl")
df_t1.columns = df_t1.iloc[1]
df_t1 = df_t1[2:]
df_t1 = df_t1.rename(columns={"Texto": "Texto", "Bloque": "Bloque"})
df_t1_valid = df_t1[["Texto", "Bloque"]].dropna()
df_t1_counts = df_t1_valid.groupby("Bloque").size().reset_index(name="Recuento")

# === DATOS TALLER 2 ===
df2 = pd.read_excel("Taller2.xlsx", sheet_name="Taller 1. C", engine="openpyxl")
df2.columns = df2.iloc[1]
df2 = df2[2:]
df2 = df2.rename(columns={"Texto": "Texto", "Bloque": "Bloque", "categoria": "Categoria"})
df_valid = df2[["Texto", "Bloque", "Categoria"]].dropna()
df_exploded = df_valid.assign(Categoria=df_valid["Categoria"].str.split(";")).explode("Categoria")
df_exploded["Categoria"] = df_exploded["Categoria"].str.strip()
bloques_disponibles = sorted(df_exploded["Bloque"].dropna().unique())


# === APP DASH ===
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Jornada Workshop: “Digitalización del entorno construido: estandarización y aplicaciones prácticas de integración BIM-GIS”", style={"textAlign": "center", "fontSize": "20px", "marginBottom": "30px"}),

    dcc.Tabs([
        dcc.Tab(label="Datos de Asistentes", children=[
            html.Div([
                html.Div([
                    html.H3("Distribución por género", style={"textAlign": "center"}),
                    dcc.Graph(figure=fig_dona)
                ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),
        
                html.Div([
                    html.H3("Participantes por entidad", style={"textAlign": "center"}),
                    dcc.Graph(figure=fig_entidades)
                ], style={"width": "48%", "display": "inline-block", "marginLeft": "4%", "verticalAlign": "top"})
            ], style={"width": "100%", "textAlign": "center", "marginTop": "20px"})
        ])

        dcc.Tab(label="TALLER 1 - Aportes por Bloque", children=[
            html.H2("TALLER 1 Aportes por Bloque", style={"textAlign": "center"}),
            dcc.Graph(id="grafico-t1"),
            html.Div(id="comentarios-t1", style={"marginTop": "20px", "textAlign": "center"})
        ]),
        dcc.Tab(label="TALLER 2 - Categorías por Bloque", children=[
            html.H2("TALLER 2 Aportes por Categoría y Bloque", style={"textAlign": "center"}),
            html.Div([
                html.Label("Selecciona un bloque:"),
                dcc.Dropdown(
                    id="selector-bloque",
                    options=[{"label": b, "value": b} for b in bloques_disponibles],
                    value=bloques_disponibles[0]
                )
            ], style={"width": "50%", "margin": "0 auto", "textAlign": "center"}),
            dcc.Graph(id="grafico"),
            html.Div(id="comentarios", style={"marginTop": "20px", "textAlign": "center"})
        ])
    ])
])

# === CALLBACK TALLER 1 ===
@app.callback(
    Output("grafico-t1", "figure"),
    Output("comentarios-t1", "children"),
    Input("grafico-t1", "clickData")
)
def mostrar_comentarios_t1(clickData):
    fig = px.bar(df_t1_counts, x="Bloque", y="Recuento", title="Notas por Bloque", color_discrete_sequence=["#003366"])
    fig.update_layout(
        xaxis_tickangle=0,
        xaxis_tickfont=dict(size=14),
        margin=dict(b=180),
        height=700,
        title_x=0.5
    )
    fig.update_xaxes(tickmode='array', tickvals=df_t1_counts["Bloque"], ticktext=df_t1_counts["Bloque"])
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
    Input("selector-bloque", "value"),
    Input("grafico", "clickData")
)
@app.callback(
    Output("grafico", "figure"),
    Output("comentarios", "children"),
    Input("selector-bloque", "value"),
    Input("grafico", "clickData")
)
def actualizar_dashboard(bloque_seleccionado, clickData):
    df_bloque = df_exploded[df_exploded["Bloque"] == bloque_seleccionado]
    df_bloque_counts = df_bloque.groupby("Categoria").size().reset_index(name="Recuento")

    fig = px.bar(df_bloque_counts, x="Categoria", y="Recuento", title=f"Bloque: {bloque_seleccionado}", color_discrete_sequence=["#8B0000"] )
    fig.write_html(f"grafico_{bloque_seleccionado}.html")

    fig.update_layout(
        xaxis_tickangle=0,
        xaxis_tickfont=dict(size=14),
        margin=dict(b=180),
        height=700,
        width=800
    )
    fig.update_xaxes(
        tickmode='array',
        tickvals=df_bloque_counts["Categoria"],
        ticktext=[dividir_en_dos_lineas(cat) for cat in df_bloque_counts["Categoria"]]
    )

    comentarios_div = html.Div("Haz clic en una barra para ver los comentarios.")
    if clickData:
        categoria = clickData["points"][0]["x"]
        comentarios = df_bloque[df_bloque["Categoria"] == categoria]["Texto"].dropna().unique().tolist()
        comentarios_div = html.Div([
            html.H4(f"Comentarios para: {categoria}"),
            html.Ul([html.Li(c) for c in comentarios])
        ])

    return fig, comentarios_div

# === RUN APP ===
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)


