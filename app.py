import streamlit as st
import pandas as pd
from scipy.stats import poisson

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Pro Betting AI - Global Edition", layout="wide")

# --- JAZYKOVÉ MUTÁCIE ---
LANG = {
    "Slovenčina": {
        "sidebar_title": "Pro Betting AI ⚽",
        "select_lang": "🌍 Vyber jazyk / Language",
        "select_league": "🏆 Vyber ligu",
        "bankroll": "Tvoj bankroll (€)",
        "tab1": "🔍 Analýza",
        "tab2": "🔥 Top Picks",
        "tab3": "📊 Backtest",
        "tab4": "🏆 Zlatý výber",
        "analyze_btn": "Spustiť analýzu",
        "expected_score": "Odhadované skóre",
        "value_calc": "💰 Value Bet Kalkulačka",
        "reliability": "Presnosť modelu",
        "gold_btn": "VYGENEROVAŤ ZLATÝ VÝBER",
        "backtest_btn": "Spustiť Backtest",
        "no_data": "Nedostatok dát.",
        "home": "Domáci",
        "away": "Hostia",
        "draw": "Remíza",
        "vklad": "Vklad"
    },
    "English": {
        "sidebar_title": "Pro Betting AI ⚽",
        "select_lang": "🌍 Select Language",
        "select_league": "🏆 Select League",
        "bankroll": "Your Bankroll (€)",
        "tab1": "🔍 Analysis",
        "tab2": "🔥 Top Picks",
        "tab3": "📊 Backtest",
        "tab4": "🏆 Gold Selection",
        "analyze_btn": "Run Analysis",
        "expected_score": "Expected Score",
        "value_calc": "💰 Value Bet Calculator",
        "reliability": "Model Accuracy",
        "gold_btn": "GENERATE GOLD SELECTION",
        "backtest_btn": "Run Backtest",
        "no_data": "Not enough data.",
        "home": "Home",
        "away": "Away",
        "draw": "Draw",
        "vklad": "Stake"
    },
    "Deutsch": {
        "sidebar_title": "Pro Betting AI ⚽",
        "select_lang": "🌍 Sprache wählen",
        "select_league": "🏆 Liga wählen",
        "bankroll": "Ihr Bankroll (€)",
        "tab1": "🔍 Analyse",
        "tab2": "🔥 Top Picks",
        "tab3": "📊 Backtest",
        "tab4": "🏆 Goldene Auswahl",
        "analyze_btn": "Analyse ausführen",
        "expected_score": "Erwartetes Ergebnis",
        "value_calc": "💰 Value Bet Rechner",
        "reliability": "Modellgenauigkeit",
        "gold_btn": "GOLDENE AUSWAHL GENERIEREN",
        "backtest_btn": "Backtest ausführen",
        "no_data": "Nicht genügend Daten.",
        "home": "Heim",
        "away": "Gast",
        "draw": "Unentschieden",
        "vklad": "Einsatz"
    }
}

# --- MAPOVANIE LÍG ---
LIGY = {
    "England: Premier League": "E0",
    "England: Championship": "E1",
    "Germany: Bundesliga": "D1",
    "Italy: Serie A": "I1",
    "Spain: La Liga": "SP1",
    "France: Ligue 1": "F1",
    "Netherlands: Eredivisie": "N1",
    "Belgium: Pro League": "B1"
}

# --- FUNKCIE PRE VÝPOČTY ---
@st.cache_data
def load_data(liga_kod):
    url = f"https://www.football-data.co.uk/mmz4281/2324/{liga_kod}.csv"
    df = pd.read_csv(url)
    df = df.dropna(subset=['FTHG', 'FTAG'])
    avg_h, avg_a = df['FTHG'].mean(), df['FTAG'].mean()
    teams = sorted(df['HomeTeam'].unique())
    stats = {}
    for team in teams:
        h_g = df[df['HomeTeam'] == team]
        a_g = df[df['AwayTeam'] == team]
        stats[team] = {
            'h_att': h_g['FTHG'].mean() / avg_h if not h_g.empty else 0.5,
            'a_att': a_g['FTAG'].mean() / avg_a if not a_g.empty else 0.5,
            'h_def': h_g['FTAG'].mean() / avg_a if not h_g.empty else 1.5,
            'a_def': a_g['FTHG'].mean() / avg_h if not a_g.empty else 1.5
        }
    return stats, avg_h, avg_a, teams, df

def get_probabilities(e_d, e_h):
    p_d, p_r, p_a = 0, 0, 0
    for i in range(9):
        for j in range(9):
            prob = poisson.pmf(i, e_d) * poisson.pmf(j, e_h)
            if i > j: p_d += prob
            elif i == j: p_r += prob
            else: p_a += prob
    return p_d * 100, p_r * 100, p_a * 100

# --- SIDEBAR & JAZYK ---
st.sidebar.title(LANG["English"]["sidebar_title"]) # Fixný titul
sel_lang = st.sidebar.selectbox("🌍 Language", list(LANG.keys()))
t = LANG[sel_lang] # Skratka pre aktuálny preklad

vybrana_liga = st.sidebar.selectbox(t["select_league"], list(LIGY.keys()))
user_bankroll = st.sidebar.number_input(t["bankroll"], min_value=1, value=100)

try:
    stats, avg_h, avg_a, zoznam_timov, raw_df = load_data(LIGY[vybrana_liga])

    tab1, tab2, tab3, tab4 = st.tabs([t["tab1"], t["tab2"], t["tab3"], t["tab4"]])

    with tab1:
        st.header(t["tab1"])
        c1, c2 = st.columns(2)
        dom = c1.selectbox(t["home"], zoznam_timov, key="d1")
        host = c2.selectbox(t["away"], zoznam_timov, index=1, key="h1")
        if st.button(t["analyze_btn"]):
            ed = stats[dom]['h_att'] * stats[host]['a_def'] * avg_h
            eh = stats[host]['a_att'] * stats[dom]['h_def'] * avg_a
            p_d, p_r, p_a = get_probabilities(ed, eh)
            st.subheader(f"{t['expected_score']}: {round(ed)} : {round(eh)}")
            m1, m2, m3 = st.columns(3)
            m1.metric(dom, f"{p_d:.1f}%")
            m2.metric(t["draw"], f"{p_r:.1f}%")
            m3.metric(host, f"{p_a:.1f}%")
            st.divider()
            st.subheader(t["value_calc"])
            k1 = st.number_input(f"Odd {dom}", value=2.0, key="k1")
            for name, prob, odd in [(dom, p_d, k1)]: # Príklad pre jedného
                val = (prob * odd) / 100
                if val > 1.05:
                    vklad = (((prob/100 * odd) - 1) / (odd - 1)) * user_bankroll * 0.2
                    st.success(f"**{name}**: VALUE {val:.2f} | {t['vklad']}: {max(0,vklad):.2f} €")

    with tab2:
        st.header(t["tab2"])
        if st.button(t["analyze_btn"], key="btn_top"):
            res = []
            for dt in zoznam_timov:
                for ht in zoznam_timov:
                    if dt != ht:
                        ed, eh = stats[dt]['h_att'] * stats[ht]['a_def'] * avg_h, stats[ht]['a_att'] * stats[dt]['h_def'] * avg_a
                        p_d, p_r, p_a = get_probabilities(ed, eh)
                        if p_d > 65: res.append({"Match": f"{dt}-{ht}", "Tip": "1", "%": f"{p_d:.1f}"})
            st.table(pd.DataFrame(res))

    with tab3:
        st.header(t["tab3"])
        f_tim = st.selectbox(t["home"], ["ALL"] + zoznam_timov)
        if st.button(t["backtest_btn"]):
            correct, total = 0, 0
            for _, row in raw_df.iterrows():
                dt, ht = row['HomeTeam'], row['AwayTeam']
                if f_tim != "ALL" and dt != f_tim and ht != f_tim: continue
                ed, eh = stats[dt]['h_att'] * stats[ht]['a_def'] * avg_h, stats[ht]['a_att'] * stats[dt]['h_def'] * avg_a
                p_d, p_r, p_a = get_probabilities(ed, eh)
                pred = "1" if p_d > p_r and p_d > p_a else ("2" if p_a > p_d and p_a > p_r else "X")
                real = "1" if row['FTHG'] > row['FTAG'] else ("X" if row['FTHG'] == row['FTAG'] else "2")
                total += 1
                if pred == real: correct += 1
            st.metric(t["reliability"], f"{(correct/total)*100:.1f}%" if total > 0 else "0%")

    with tab4:
        st.header(t["tab4"])
        if st.button(t["gold_btn"]):
            reliab = []
            for tim in zoznam_timov:
                c, tot = 0, 0
                for _, row in raw_df.iterrows():
                    if row['HomeTeam'] == tim or row['AwayTeam'] == tim:
                        dt, ht = row['HomeTeam'], row['AwayTeam']
                        ed, eh = stats[dt]['h_att'] * stats[ht]['a_def'] * avg_h, stats[ht]['a_att'] * stats[dt]['h_def'] * avg_a
                        p_d, p_r, p_a = get_probabilities(ed, eh)
                        pred = "1" if p_d > p_r and p_d > p_a else ("2" if p_a > p_d and p_a > p_r else "X")
                        real = "1" if row['FTHG'] > row['FTAG'] else ("X" if row['FTHG'] == row['FTAG'] else "2")
                        tot += 1
                        if pred == real: c += 1
                if tot > 5: reliab.append({"Team": tim, "Acc": (c/tot)*100})
            top = pd.DataFrame(reliab).sort_values(by="Acc", ascending=False).head(3)
            for _, r in top.iterrows():
                st.success(f"{r['Team']} - {t['reliability']}: {r['Acc']:.1f}%")

except Exception as e:
    st.error(f"Error: {e}")