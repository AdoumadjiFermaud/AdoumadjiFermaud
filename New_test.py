import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
import os

# Créer l'instance Dash
app = dash.Dash(__name__)
# Exposer l'objet `server` pour Gunicorn
server = app.server

# Charger les données
file_path = "donneesBEH.xlsx"
df = pd.read_excel(file_path, sheet_name="Tableau 1")

# Nettoyage et transformation des données
df.columns = ["Cause", "Femmes_N", "Femmes_Taux", "Hommes_N", "Hommes_Taux", 
              "Moins_65_N", "Moins_65_Taux", "Age_65_84_N", "Age_65_84_Taux", 
              "Age_85_plus_N", "Age_85_plus_Taux", "Ensemble_N", "Ensemble_Taux"]
df = df.iloc[1:].reset_index(drop=True)

# Convertir les colonnes numériques
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df.fillna(0, inplace=True)

# Layout du tableau de bord
app.layout = html.Div([
    html.H1("Tableau de bord des causes de mortalité", style={'textAlign': 'center', 'color': '#003366'}),
    
    dcc.Dropdown(
        id='cause-dropdown',
        options=[{'label': cause, 'value': cause} for cause in df['Cause'].unique()],
        value=df['Cause'].unique()[0],
        multi=False,
        style={'width': '50%', 'margin': 'auto'}
    ),
    
    dcc.Graph(id='bar-chart'),
    dcc.Graph(id='pie-chart'),
    dcc.Graph(id='heatmap'),
    dcc.Graph(id='line-chart'),
    dcc.Graph(id='scatter-plot'),
    dcc.Graph(id='radar-chart'),
    dcc.Graph(id='top-causes-bar'),
    dcc.Graph(id='mortality-gap-bar'),
    dcc.Graph(id='age-group-bar')
])

# Callback pour mettre à jour les graphiques
@app.callback(
    [Output('bar-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('heatmap', 'figure'),
     Output('line-chart', 'figure'),
     Output('scatter-plot', 'figure'),
     Output('radar-chart', 'figure'),
     Output('top-causes-bar', 'figure'),
     Output('mortality-gap-bar', 'figure'),
     Output('age-group-bar', 'figure')],
    [Input('cause-dropdown', 'value')]
)
def update_graphs(selected_cause):
    filtered_df = df[df['Cause'] == selected_cause]

    if filtered_df.empty:
        empty_fig = px.bar(title="Aucune donnée disponible")
        return [empty_fig] * 9  # Retourne 9 figures vides

    # Graphique en barres → Nombre de décès par sexe
    bar_chart_data = pd.DataFrame({
        "Sexe": ["Femmes", "Hommes"],
        "Nombre de décès": [filtered_df['Femmes_N'].values[0], filtered_df['Hommes_N'].values[0]]
    })

    bar_chart_fig = px.bar(
        bar_chart_data, x="Sexe", y="Nombre de décès",
        title=f"Nombre de décès - {selected_cause}",
        color="Sexe"
    )

    # Graphique en secteurs (camembert) → Répartition par sexe
    pie_chart_fig = px.pie(
        names=["Femmes", "Hommes"], 
        values=[filtered_df['Femmes_N'].values[0], filtered_df['Hommes_N'].values[0]],
        title=f"Répartition hommes/femmes - {selected_cause}"
    )

    # Heatmap des taux par tranche d'âge
    heatmap_fig = px.imshow(
        np.array([[filtered_df['Moins_65_Taux'].values[0], 
                   filtered_df['Age_65_84_Taux'].values[0], 
                   filtered_df['Age_85_plus_Taux'].values[0]]]),
        labels={'x': "Groupe d'âge", 'y': "Taux de mortalité"},
        x=['<65', '65-84', '85+'],
        title=f"Taux de mortalité par âge - {selected_cause}",
        color_continuous_scale="Blues"
    )

    # Graphique en ligne → Évolution fictive des taux
    line_chart_fig = px.line(
        x=['2010', '2015', '2020'], 
        y=np.random.randint(10, 100, 3), 
        title=f"Évolution des taux de mortalité - {selected_cause}"
    )

    # Nuage de points → Relation femmes/hommes
    scatter_fig = px.scatter(
        x=[filtered_df['Femmes_Taux'].values[0]], 
        y=[filtered_df['Hommes_Taux'].values[0]],
        title=f"Corrélation hommes/femmes - {selected_cause}"
    )

    # Radar chart → Répartition des taux de mortalité
    radar_chart_fig = px.line_polar(
        r=[filtered_df['Moins_65_Taux'].values[0], 
           filtered_df['Age_65_84_Taux'].values[0], 
           filtered_df['Age_85_plus_Taux'].values[0]],
        theta=['<65', '65-84', '85+'],
        title=f"Répartition des taux de mortalité - {selected_cause}"
    )

    # Graphique en barres → Top causes de mortalité
    top_causes_fig = px.bar(
        df.sort_values("Ensemble_N", ascending=False).head(10),
        x='Cause', y='Ensemble_N', title="Top 10 des causes de mortalité",
        color='Ensemble_N', color_continuous_scale='Reds'
    )

    # Graphique en barres empilées → Comparaison hommes/femmes
    mortality_gap_fig = px.bar(
        df, x='Cause', y=['Femmes_Taux', 'Hommes_Taux'],
        title="Comparaison du taux de mortalité hommes/femmes",
        barmode='stack'
    )

    # Graphique en barres groupées → Taux par âge
    age_group_fig = px.bar(
        df, x='Cause', y=['Moins_65_Taux', 'Age_65_84_Taux', 'Age_85_plus_Taux'],
        title="Comparaison des taux de mortalité par groupes d'âge",
        barmode='group'
    )

    return bar_chart_fig, pie_chart_fig, heatmap_fig, line_chart_fig, scatter_fig, radar_chart_fig, top_causes_fig, mortality_gap_fig, age_group_fig


# Configuration du port pour Railway
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

