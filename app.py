import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="La revolución del triple en la NBA",
    page_icon="🏀",
    layout="wide"
)


@st.cache_data
def load_data():
    teams = pd.read_csv("data/team_stats_clean.csv")
    players = pd.read_csv("data/player_stats_clean.csv")
    league = pd.read_csv("data/league_3pt_evolution.csv")
    shots = pd.read_csv("data/shots_clean.csv")
    return teams, players, league, shots


df_teams, df_players, df_league, df_shots = load_data()


# =========================
# PREPARACIÓN GLOBAL
# =========================

for df in [df_teams, df_players, df_league]:
    df["SEASON"] = df["SEASON"].astype(str)
    df["SEASON_START"] = df["SEASON_START"].astype(int)
    df["SEASON_LABEL"] = df["SEASON"].str.replace("-", "/", regex=False)

season_order = (
    df_league
    .sort_values("SEASON_START")["SEASON_LABEL"]
    .tolist()
)


# =========================
# FUNCIONES
# =========================

def draw_court(fig):
    court_color = "white"
    line_width = 2.5

    shapes = []

    shapes.append(dict(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="line", x0=-30, y0=-10, x1=30, y1=-10, line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="rect", x0=-80, y0=-47.5, x1=80, y1=143, line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="circle", x0=-60, y0=83, x1=60, y1=203, line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="path", path="M -220 92.5 Q 0 320 220 92.5", line=dict(color=court_color, width=line_width)))
    shapes.append(dict(type="line", x0=-250, y0=422.5, x1=250, y1=422.5, line=dict(color=court_color, width=line_width)))

    fig.update_layout(shapes=shapes)

    fig.update_xaxes(
        range=[-250, 250],
        showgrid=False,
        zeroline=False,
        visible=False
    )

    fig.update_yaxes(
        range=[-50, 430],
        showgrid=False,
        zeroline=False,
        visible=False,
        scaleanchor="x",
        scaleratio=1
    )

    fig.update_layout(
        height=700,
        plot_bgcolor="#2b2b2b",
        paper_bgcolor="white"
    )

    return fig


# =========================
# SIDEBAR
# =========================

st.sidebar.title("Filtros")

seasons = sorted(df_teams["SEASON"].unique(), reverse=True)
selected_season = st.sidebar.selectbox("Temporada", seasons)

df_season = df_teams[df_teams["SEASON"] == selected_season]

teams_season = ["Todos los equipos"] + sorted(df_season["TEAM_NAME"].dropna().unique().tolist())
selected_team = st.sidebar.selectbox("Equipo", teams_season)

if selected_team == "Todos los equipos":
    df_scope_teams = df_season.copy()
    df_scope_players = df_players[df_players["SEASON"] == selected_season].copy()
else:
    df_team_selected = df_season[df_season["TEAM_NAME"] == selected_team]
    selected_team_id = df_team_selected["TEAM_ID"].iloc[0]

    df_scope_teams = df_team_selected.copy()
    df_scope_players = df_players[
        (df_players["SEASON"] == selected_season) &
        (df_players["TEAM_ID"] == selected_team_id)
    ].copy()

players_available = (
    df_scope_players["PLAYER_NAME"]
    .dropna()
    .sort_values()
    .unique()
)

if len(players_available) > 0:
    selected_player = st.sidebar.selectbox("Jugador", players_available)
else:
    selected_player = None
    st.sidebar.warning("No hay jugadores disponibles para esta selección.")

st.sidebar.markdown("---")
st.sidebar.caption("Datos: NBA Stats vía nba_api. CSV generados previamente para garantizar estabilidad.")


# =========================
# TÍTULO
# =========================

st.title("🏀 La revolución del triple en la NBA moderna")

st.markdown("""
Este proyecto visualiza cómo el tiro de tres puntos ha transformado la NBA durante las últimas décadas.
La aplicación combina análisis histórico, comparativas entre equipos y jugadores, y visualización espacial de lanzamientos.
""")


# =========================
# KPIs
# =========================

st.subheader("1. Indicadores principales")

c1, c2, c3, c4 = st.columns(4)

if selected_team == "Todos los equipos":
    c1.metric("Temporada", selected_season)
    c2.metric("Media triples/equipo", round(df_scope_teams["FG3A"].mean(), 2))
    c3.metric("Media puntos/equipo", round(df_scope_teams["PTS"].mean(), 2))
    c4.metric("Equipos analizados", df_scope_teams["TEAM_NAME"].nunique())
else:
    row = df_scope_teams.iloc[0]
    c1.metric("Equipo", selected_team)
    c2.metric("Triples intentados", round(row["FG3A"], 2))
    c3.metric("Puntos por partido", round(row["PTS"], 2))
    c4.metric("Victorias", int(row["W"]))


# =========================
# EVOLUCIÓN HISTÓRICA
# =========================

st.subheader("2. Evolución histórica del triple")

df_league_plot = df_league.sort_values("SEASON_START").copy()

fig_evolution = px.line(
    df_league_plot,
    x="SEASON_LABEL",
    y="AVG_FG3A",
    markers=True,
    category_orders={"SEASON_LABEL": season_order},
    title="Evolución de triples intentados por equipo y partido",
    labels={
        "SEASON_LABEL": "Temporada",
        "AVG_FG3A": "Triples intentados por partido"
    }
)

fig_evolution.update_xaxes(type="category")
fig_evolution.update_layout(height=550)

st.plotly_chart(fig_evolution, use_container_width=True)


# =========================
# PESO DEL TRIPLE
# =========================

st.subheader("3. Peso del triple sobre el total de tiros")

df_league_plot["AVG_THREE_POINT_RATE_PCT"] = df_league_plot["AVG_THREE_POINT_RATE"] * 100

fig_rate = px.line(
    df_league_plot,
    x="SEASON_LABEL",
    y="AVG_THREE_POINT_RATE_PCT",
    markers=True,
    category_orders={"SEASON_LABEL": season_order},
    title="Proporción de triples sobre el total de tiros",
    labels={
        "SEASON_LABEL": "Temporada",
        "AVG_THREE_POINT_RATE_PCT": "% de tiros que son triples"
    }
)

fig_rate.update_xaxes(type="category")
fig_rate.update_layout(height=550)

st.plotly_chart(fig_rate, use_container_width=True)


# =========================
# COMPARATIVA EQUIPOS
# =========================

st.subheader("4. Comparativa de equipos")

col1, col2 = st.columns(2)

with col1:
    fig_scatter = px.scatter(
        df_season,
        x="FG3A",
        y="PTS",
        size="W",
        hover_name="TEAM_NAME",
        title=f"Triples intentados vs puntos - {selected_season}",
        labels={
            "FG3A": "Triples intentados",
            "PTS": "Puntos por partido",
            "W": "Victorias"
        }
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    df_rank_team = df_season.sort_values("FG3A", ascending=False)

    fig_bar_team = px.bar(
        df_rank_team,
        x="FG3A",
        y="TEAM_NAME",
        orientation="h",
        title=f"Ranking de equipos por triples intentados - {selected_season}",
        labels={
            "FG3A": "Triples intentados",
            "TEAM_NAME": "Equipo"
        }
    )

    fig_bar_team.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar_team, use_container_width=True)


# =========================
# EVOLUCIÓN EQUIPO
# =========================

if selected_team != "Todos los equipos":
    st.subheader(f"5. Evolución del equipo seleccionado: {selected_team}")

    team_history = (
        df_teams[df_teams["TEAM_NAME"] == selected_team]
        .sort_values("SEASON_START")
        .copy()
    )

    fig_team_history = px.line(
        team_history,
        x="SEASON_LABEL",
        y=["FG3A", "PTS"],
        markers=True,
        category_orders={"SEASON_LABEL": season_order},
        title=f"Evolución de triples intentados y puntos - {selected_team}",
        labels={
            "SEASON_LABEL": "Temporada",
            "value": "Valor por partido",
            "variable": "Métrica"
        }
    )

    fig_team_history.update_xaxes(type="category")
    fig_team_history.update_layout(height=550)

    st.plotly_chart(fig_team_history, use_container_width=True)

else:
    st.subheader("5. Evolución general de la liga")

    fig_general = px.line(
        df_league_plot,
        x="SEASON_LABEL",
        y=["AVG_FG3A", "AVG_PTS"],
        markers=True,
        category_orders={"SEASON_LABEL": season_order},
        title="Evolución general de triples intentados y puntos por equipo",
        labels={
            "SEASON_LABEL": "Temporada",
            "value": "Valor promedio",
            "variable": "Métrica"
        }
    )

    fig_general.update_xaxes(type="category")
    fig_general.update_layout(height=550)

    st.plotly_chart(fig_general, use_container_width=True)


# =========================
# JUGADORES
# =========================

st.subheader("6. Comparativa de jugadores")

top_n = st.slider("Número de jugadores en el ranking", 5, 30, 15)

df_rank_players = df_scope_players.sort_values("FG3M", ascending=False).head(top_n)

fig_players_rank = px.bar(
    df_rank_players,
    x="FG3M",
    y="PLAYER_NAME",
    orientation="h",
    title=f"Top {top_n} jugadores por triples anotados - {selected_season}",
    labels={
        "FG3M": "Triples anotados por partido",
        "PLAYER_NAME": "Jugador"
    }
)

fig_players_rank.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_players_rank, use_container_width=True)


# =========================
# EVOLUCIÓN JUGADOR
# =========================

if selected_player is not None:
    st.subheader(f"7. Evolución del jugador seleccionado: {selected_player}")

    player_history = (
        df_players[df_players["PLAYER_NAME"] == selected_player]
        .sort_values("SEASON_START")
        .copy()
    )

    if not player_history.empty:
        fig_player_history = px.line(
            player_history,
            x="SEASON_LABEL",
            y=["FG3A", "FG3M", "PTS"],
            markers=True,
            category_orders={"SEASON_LABEL": season_order},
            title=f"Evolución estadística de {selected_player}",
            labels={
                "SEASON_LABEL": "Temporada",
                "value": "Valor por partido",
                "variable": "Métrica"
            }
        )

        fig_player_history.update_xaxes(type="category")
        fig_player_history.update_layout(height=550)

        st.plotly_chart(fig_player_history, use_container_width=True)
    else:
        st.warning("No hay datos históricos suficientes para este jugador.")


# =========================
# SHOT CHART
# =========================

st.subheader("8. Shot chart sobre la cancha")

st.markdown("""
Esta visualización representa espacialmente los lanzamientos disponibles para jugadores seleccionados.
Cada punto corresponde a un tiro real, ubicado según sus coordenadas en la cancha.
""")

shot_players = sorted(df_shots["PLAYER_NAME_CUSTOM"].dropna().unique())
shot_seasons = sorted(df_shots["SEASON"].dropna().unique(), reverse=True)

col_filter1, col_filter2 = st.columns(2)

with col_filter1:
    selected_shot_player = st.selectbox("Jugador para shot chart", shot_players)

with col_filter2:
    selected_shot_season = st.selectbox("Temporada para shot chart", shot_seasons)

df_shot_filtered = df_shots[
    (df_shots["PLAYER_NAME_CUSTOM"] == selected_shot_player) &
    (df_shots["SEASON"] == selected_shot_season)
]

if df_shot_filtered.empty:
    st.warning("No hay datos de tiros para esta combinación de jugador y temporada.")
else:
    fig_court = px.scatter(
        df_shot_filtered,
        x="LOC_X",
        y="LOC_Y",
        color="SHOT_MADE_FLAG",
        hover_data=[
            "PLAYER_NAME_CUSTOM",
            "TEAM_NAME",
            "GAME_DATE",
            "SHOT_DISTANCE",
            "SHOT_TYPE",
            "SHOT_ZONE_BASIC",
            "SHOT_ZONE_AREA",
            "SHOT_ZONE_RANGE",
            "ACTION_TYPE",
            "EVENT_TYPE"
        ],
        title=f"Shot chart de {selected_shot_player} - {selected_shot_season}",
        labels={
            "LOC_X": "Coordenada X",
            "LOC_Y": "Coordenada Y",
            "SHOT_MADE_FLAG": "Tiro anotado"
        }
    )

    fig_court = draw_court(fig_court)
    st.plotly_chart(fig_court, use_container_width=True)


# =========================
# HEATMAP
# =========================

st.subheader("9. Mapa de densidad de lanzamientos")

if not df_shot_filtered.empty:
   fig_heat = px.density_heatmap(
    df_shot_filtered,
    x="LOC_X",
    y="LOC_Y",
    nbinsx=45,
    nbinsy=45,
    color_continuous_scale="Inferno",
    title=f"Densidad de tiros de {selected_shot_player} - {selected_shot_season}",
    labels={
        "LOC_X": "Coordenada X",
        "LOC_Y": "Coordenada Y",
        "count": "Frecuencia"
    }
)

fig_heat.update_traces(
    opacity=0.78
)

fig_heat = draw_court(fig_heat)

st.plotly_chart(fig_heat, use_container_width=True)


# =========================
# CONCLUSIONES
# =========================

st.subheader("10. Conclusiones")

st.markdown("""
A través de estas visualizaciones se observa cómo el triple ha pasado de ser un recurso secundario
a convertirse en uno de los elementos centrales del juego moderno.

Las visualizaciones temporales permiten ver la evolución histórica, las comparativas de equipos y jugadores
permiten identificar protagonistas y estilos de juego, y los shot charts permiten entender la dimensión espacial
de esta transformación.

El uso de filtros interactivos por temporada, equipo y jugador facilita una exploración libre del dataset y permite
descubrir patrones concretos dentro de una narrativa general: la revolución del triple en la NBA.
""")