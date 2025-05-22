import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import matplotlib.pyplot as plt


# Cargar el archivo Excel (asegúrate de que esté en la misma carpeta del notebook)
df = pd.read_excel("Asistentes.xlsx", engine="openpyxl")

# Mostrar las primeras filas
df.head()

# Quitar espacios en los nombres de columnas
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

# Ver columnas limpias
print(df.columns)

import matplotlib.pyplot as plt
df['genero'] = df['genero'].replace({
    'h': 'hombre',
    'm': 'mujer',
    '': 'no especificado',
    None: 'no especificado'
})
# Rellenar NaNs como 'no especificado'
df['genero'] = df['genero'].fillna('no especificado')

# Conteo por género
genero_counts = df['genero'].value_counts()

# Colores suaves (pasteles)
colores = [ '#F9E79F', '#D5F5E3', '#E8DAEF']  # rosa pastel, azul, amarillo, verde, lavanda

# Crear gráfico de dona
fig, ax = plt.subplots()
ax.pie(
    genero_counts, 
    labels=genero_counts.index, 
    autopct='%1.1f%%', 
    startangle=90,
    colors=colores,
    wedgeprops={'width': 0.4, 'edgecolor': 'white'}  # para hacer el hueco central (dona)
)
ax.set_title('Distribución por género', fontsize=14)
plt.axis('equal')  # Circulo perfecto
plt.tight_layout()
plt.show()
plt.savefig("Porcentaje_genero.png", dpi=300)

# Normalizar nombres de entidad
df['entidad'] = df['entidad'].astype(str).str.strip()

# Contar número de personas por entidad
resumen_entidad = df['entidad'].value_counts().reset_index()
resumen_entidad.columns = ['entidad', 'numero_personas']

# Crear gráfico "estilo personas"
plt.figure(figsize=(11, 6))
for i, (entidad, cantidad) in enumerate(zip(resumen_entidad['entidad'], resumen_entidad['numero_personas'])):
    personas = "👤" * cantidad  # Repetir ícono por número de personas
    plt.text(0, i, personas, fontsize=22, va='center', color='purple', fontname='Segoe UI Emoji')

# Ajustes visuales

# Quitar bordes y líneas del gráfico
ax = plt.gca()
for spine in ax.spines.values():
    spine.set_visible(False)  # Ocultar todos los bordes
ax.tick_params(left=False, bottom=False)  # Quitar marcas de los ejes


plt.yticks(range(len(resumen_entidad)), resumen_entidad['entidad'])
plt.xticks([])  # Sin eje x
#plt.title('Número de personas por entidad (👤 = 1 persona)', fontsize=14)ç
plt.title('Número de personas por entidad', fontsize=14, loc='left',  pad=20)
#plt.xlabel('Número de personas')
#plt.gca().invert_yaxis()  # Entidades de arriba hacia abajo
plt.xlim(0, 3)  # Límite horizontal acorde al máximo de personas
plt.tight_layout()
plt.show()



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

# Función para dividir texto largo en 2 líneas
def dividir_en_dos_lineas(texto, umbral=40):
    if not isinstance(texto, str):
        return texto
    if len(texto) <= umbral:
        return texto
    palabras = texto.split()
    mitad = len(palabras) // 2
    return " ".join(palabras[:mitad]) + "<br>" + " ".join(palabras[mitad:])

# Inicializar app
app = Dash(__name__)
bloques_disponibles = sorted(df_exploded["Bloque"].dropna().unique())

app.layout = html.Div([
    html.H2("Análisis por Categoría", style={"textAlign": "center"}),

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

# ✅ Ejecutar la app solo si es archivo principal
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)

