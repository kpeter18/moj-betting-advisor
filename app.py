import streamlit as st
import pandas as pd
from scipy.stats import poisson

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Pro Betting AI Advisor", layout="wide")

# --- MAPOVANIE LÍG (ZDROJ: football-data.co.uk) ---
LIGY = {
    "Anglicko: Premier League": "E0",
    "Anglicko: Championship": "E1",
    "Nemecko: Bundesliga": "D1",
    "Taliansko: Serie A": "I1",
    "Španielsko: La Liga": "SP1",
    "Francúzsko: Ligue 1": "F1",
    "Holandsko: Eredivisie": "N1",
    "Belgicko: Pro League": "B1"
}

# --- FUNKCIA: NAČÍTANIE DÁT A VÝPOČET SILY ---
@st.cache_data
def load_data(liga_kod):
    # Dáta za aktuálnu sezónu 2023/2024
    url = f"https://www.football-data.co.uk/mmz4281/2324/{liga_kod}.csv"
    df = pd.read_csv(url)
    
    # Výpočet ligových priemerov
    avg_home_g = df['FTHG'].mean()
    avg_away_g = df['FTAG'].mean()
    
    teams = sorted(df['HomeTeam'].unique())
    stats = {}

    for team in teams:
        h_games = df[df['HomeTeam'] == team]
        a_games = df[df['AwayTeam'] == team]
        
        # Sila útoku (Attack Strength)
        h_att = h_games['FTHG'].mean() / avg_home_g
        a_att = a_games['FTAG'].mean() / avg_away_g
        
        # Sila obrany (Defense Strength)
        h_def = h_games['FTAG'].mean() / avg_away_g
        a_def = h_games['FTHG'].mean() / avg_home_g
        
        stats[team] = {
            'h_att': h_att, 'a_att': a_att,
            'h_def': h_def, 'a_def': a_def
        }
    
    return stats, avg_home_g, avg_away_g

# --- FUNKCIA: POISSONOV VÝPOČET % ---
def get_probabilities(exp_g_d, exp_g_h):
    p_domaci, p_remiza, p_hostia = 0, 0, 0
    for i in range(10): # Maximálne 9 gólov na zápas
        for j in range(10):
            prob = poisson.pmf(i, exp_g_d) * poisson.pmf(j, exp_g_h)
            if i > j: p_domaci += prob
            elif i == j: p_remiza += prob
            else: p_hostia += prob
    return p_domaci * 100, p_remiza * 100, p_hostia * 100

# --- GRAFICKÉ ROZHRANIE (SIDEBAR) ---
st.sidebar.header("Nastavenia")
vybrana_liga = st.sidebar.selectbox("Vyber ligu", list(LIGY.keys()))
bankroll = st.sidebar.number_input("Tvoj rozpočet (Bankroll €)", min_value=0, value=100)

# --- NAČÍTANIE DÁT ---
try:
    liga_kod = LIGY[vybrana_liga]
    stats, avg_h, avg_a = load_data(liga_kod)
    zoznam_timov = list(stats.keys())

    # --- VÝBER TÍMOV ---
    st.title(f"⚽ {vybrana_liga} - Analýza")
    col1, col2 = st.columns(2)
    with col1:
        domaci = st.selectbox("Domáci tím", zoznam_timov, index=0)
    with col2:
        hostia = st.selectbox("Hostia tím", zoznam_timov, index=1)

    if st.button("SPUSTIŤ ANALÝZU ZÁPASU"):
        # Matematický výpočet očakávaných gólov
        exp_g_d = stats[domaci]['h_att'] * stats[hostia]['a_def'] * avg_h
        exp_g_h = stats[hostia]['a_att'] * stats[domaci]['h_def'] * avg_a
        
        # Percentá
        d_pct, r_pct, h_pct = get_probabilities(exp_g_d, exp_g_h)
        
        # Zobrazenie výsledkov
        st.divider()
        st.subheader(f"Predpokladané skóre: {round(exp_g_d)} : {round(exp_g_h)}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Výhra {domaci}", f"{d_pct:.1f}%")
        m2.metric("Remíza", f"{r_pct:.1f}%")
        m3.metric(f"Výhra {hostia}", f"{h_pct:.1f}%")

        # --- VALUE BET SEKCIÁ ---
        st.divider()
        st.subheader("💰 Kalkulačka výhodnosti (Value Bet)")
        st.write("Zadaj kurzy zo svojej stávkovej kancelárie:")
        
        k_col1, k_col2, k_col3 = st.columns(3)
        k1 = k_col1.number_input(f"Kurz na {domaci}", value=2.0, step=0.01)
        kx = k_col2.number_input(f"Kurz na Remízu", value=3.0, step=0.01)
        k2 = k_col3.number_input(f"Kurz na {hostia}", value=3.5, step=0.01)

        # Výpočet hodnoty
        v1 = (d_pct * k1) / 100
        vx = (r_pct * kx) / 100
        v2 = (h_pct * k2) / 100

        def display_value(name, val, prob, odd):
            if val > 1.05: # Hodnota aspoň 5%
                st.success(f"**{name}** má hodnotu! (Value: {val:.2f})")
                # Kellyho kritérium (zjednodušené): ((p*k)-1)/(k-1)
                kelly = ((prob/100 * odd) - 1) / (odd - 1)
                vklad = max(0, kelly * bankroll * 0.2) # Riskujeme len 20% z Kellyho (bezpečnejšie)
                st.write(f"👉 Odporúčaný vklad: **{vklad:.2f} €**")
            else:
                st.write(f"{name}: Bez hodnoty ({val:.2f})")

        display_value(domaci, v1, d_pct, k1)
        display_value("Remíza", vx, r_pct, kx)
        display_value(hostia, v2, h_pct, k2)

except Exception as e:
    st.error(f"Nepodarilo sa načítať dáta pre túto ligu: {e}")