if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
import pandas as pd

# Cargar hoja
df = pd.read_excel("Taller2.xlsx", sheet_name="Taller 1. C", engine="openpyxl")

# Usar fila 2 como cabecera real
df.columns = df.iloc[1]
df = df[2:]  # Eliminar encabezado viejo

# Renombrar columnas útiles
df = df.rename(columns={
    "Texto": "Texto",
    "Bloque": "Bloque",
    "categoria": "Categoria"
})

# Filtrar filas válidas
df_valid = df[["Texto", "Bloque", "Categoria"]].dropna()

# Separar múltiples categorías por ;
df_exploded = df_valid.assign(Categoria=df_valid["Categoria"].str.split(";")).explode("Categoria")
df_exploded["Categoria"] = df_exploded["Categoria"].str.strip()

from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Crear lista de bloques únicos
bloques_disponibles = sorted(df_exploded["Bloque"].dropna().unique())

# Inicializar app
app = Dash(__name__)

app.layout = html.Div([
    html.H2("Análisis por Categoría", style={"textAlign": "center"}),

    html.Div([
        html.Label("Selecciona un bloque:"),
        dcc.Dropdown(
            id="selector-bloque",
            options=[{"label": b, "value": b} for b in bloques_disponibles],
            value=bloques_disponibles[0]  # valor por defecto
        )
    ], style={"width": "50%", "margin": "0 auto", "textAlign": "center"}),

    dcc.Graph(id="grafico"),
    html.Div(id="comentarios", style={"marginTop": "20px", "textAlign": "center"})
])

@app.callback(
    Output("grafico", "figure"),
    Output("comentarios", "children"),
    Input("selector-bloque", "value"),
    Input("grafico", "clickData")
)
def actualizar_dashboard(bloque_seleccionado, clickData):
    df_bloque = df_exploded[df_exploded["Bloque"] == bloque_seleccionado]
    df_bloque_counts = df_bloque.groupby("Categoria").size().reset_index(name="Recuento")

    fig = px.bar(df_bloque_counts, x="Categoria", y="Recuento", title=f"Bloque: {bloque_seleccionado}")
    # Exportar gráfico como archivo HTML (se sobrescribe en cada cambio de bloque)
    fig.write_html(f"grafico_{bloque_seleccionado}.html")

    fig.update_layout(
        xaxis_tickangle=0,  # Mantener horizontal
        xaxis_tickfont=dict(size=14),  # Letra más grande
        margin=dict(b=180),  # Más espacio abajo
        height=700,          # Más alto si es necesario
    )
    
    # Mostrar el texto completo sin cortar
    fig.update_xaxes(
        tickmode='array',
        tickvals=df_bloque_counts["Categoria"],
        ticktext=df_bloque_counts["Categoria"]  # Sin saltos de línea
    )


    # Mostrar comentarios si hay click
    comentarios_div = html.Div("Haz clic en una barra para ver los comentarios.")
    if clickData:
        categoria = clickData["points"][0]["x"]
        comentarios = df_bloque[df_bloque["Categoria"] == categoria]["Texto"].dropna().unique().tolist()
        comentarios_div = html.Div([
            html.H4(f"Comentarios para: {categoria}"),
            html.Ul([html.Li(c) for c in comentarios])
        ])

    return fig, comentarios_div

# Ejecutar la app
app.run(debug=True)
# Exportar gráfico como archivo HTML (se sobrescribe en cada cambio de bloque)

