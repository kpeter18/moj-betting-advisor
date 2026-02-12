import streamlit as st
import pandas as pd

@st.cache_data
def load_advanced_data():
    url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
    df = pd.read_csv(url)

    # 1. Ligové priemery
    avg_home_sc_l = df['FTHG'].mean() # Priemer gólov domácich
    avg_away_sc_l = df['FTAG'].mean() # Priemer gólov hostí
    avg_home_con_l = avg_away_sc_l    # Priemer inkasovaných doma (je priemer strelených vonku)
    avg_away_con_l = avg_home_sc_l    # Priemer inkasovaných vonku

    teams = sorted(df['HomeTeam'].unique())
    stats = {}

    for team in teams:
        home_games = df[df['HomeTeam'] == team]
        away_games = df[df['AwayTeam'] == team]

        # Sila útoku (Attack Strength)
        h_att = home_games['FTHG'].mean() / avg_home_sc_l
        a_att = away_games['FTAG'].mean() / avg_away_sc_l

        # Sila obrany (Defense Strength)
        h_def = home_games['FTAG'].mean() / avg_home_con_l
        a_def = away_games['FTHG'].mean() / avg_away_con_l

        stats[team] = {
            'h_att': h_att, 'a_att': a_att,
            'h_def': h_def, 'a_def': a_def
        }
    
    return stats, avg_home_sc_l, avg_away_sc_l

# --- VÝPOČET PREDPOVEDE ---
# Očakávané góly domáci = Home_Att_Domaci * Away_Def_Hostia * Avg_Home_Goals_League
# Očakávané góly hostia = Away_Att_Hostia * Home_Def_Domaci * Avg_Away_Goals_League