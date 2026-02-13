import streamlit as st
import pandas as pd
from scipy.stats import poisson
from datetime import datetime

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Pro Betting AI - Ultimate Risk Manager", layout="wide")

# --- JAZYKOVÉ MUTÁCIE ---
LANG = {
    "Slovenčina": {
        "sidebar_title": "Pro Betting AI ⚽",
        "select_lang": "🌍 Vyber jazyk / Language",
        "select_league": "🏆 Vyber ligu",
        "bankroll": "Tvoj bankroll (€)",
        "tab1": "🔍 Analýza", "tab2": "🔥 Top Picks", "tab3": "📊 Backtest", "tab4": "🏆 Zlatý výber",
        "analyze_btn": "Spustiť analýzu", "expected_score": "Odhadované skóre", "value_calc": "💰 Kalkulačka",
        "reliability": "Presnosť modelu", "gold_btn": "VYGENEROVAŤ ZLATÝ VÝBER", "backtest_btn": "Spustiť Backtest",
        "home": "Domáci", "away": "Hostia", "draw": "Remíza", "vklad": "Vklad", 
        "form_home": "Forma DOMA", "form_away": "Forma VONKU", "over_under": "Góly 2.5+",
        "quick_analyze": "⚡ Analýza nadchádzajúcich zápasov:", "select_match": "Vyberte zápas zo žrebu:",
        "risk_mgmt": "🛡️ Minimalizácia straty (Risk Management)",
        "fair_odd": "Férový kurz", "dnb_info": "DNB (Sázka bez remízy) - Pri remíze sa vklad vracia.",
        "dc_info": "Double Chance (1X / X2) - Vyhrávaš aj pri remíze."
    },
    "English": {
        "sidebar_title": "Pro Betting AI ⚽",
        "select_lang": "🌍 Select Language",
        "select_league": "🏆 Select League",
        "bankroll": "Your Bankroll (€)",
        "tab1": "🔍 Analysis", "tab2": "🔥 Top Picks", "tab3": "📊 Backtest", "tab4": "🏆 Gold Selection",
        "analyze_btn": "Run Analysis", "expected_score": "Expected Score", "value_calc": "💰 Calculator",
        "reliability": "Model Accuracy", "gold_btn": "GENERATE GOLD SELECTION", "backtest_btn": "Run Backtest",
        "home": "Home", "away": "Away", "draw": "Draw", "vklad": "Stake",
        "form_home": "HOME Form", "form_away": "AWAY Form", "over_under": "Goals 2.5+",
        "quick_analyze": "⚡ Upcoming match analysis:", "select_match": "Select match from fixtures:",
        "risk_mgmt": "🛡️ Risk Management (Loss Minimization)",
        "fair_odd": "Fair Odd", "dnb_info": "DNB (Draw No Bet) - Refund on draw.",
        "dc_info": "Double Chance (1X / X2) - Win on draw as well."
    }
}

LIGY = {
    "England: Premier League": "E0", "Germany: Bundesliga": "D1", "Italy: Serie A": "I1",
    "Spain: La Liga": "SP1", "France: Ligue 1": "F1", "Netherlands: Eredivisie": "N1"
}

# --- FUNKCIA: NAČÍTANIE DÁT ---
@st.cache_data
def load_data_v31(liga_kod):
    url = f"https://www.football-data.co.uk/mmz4281/2324/{liga_kod}.csv"
    df = pd.read_csv(url)
    played_df = df.dropna(subset=['FTHG', 'FTAG']).copy()
    fixtures_df = df[df['FTHG'].isna()].copy()
    played_df['Date'] = pd.to_datetime(played_df['Date'], dayfirst=True)
    played_df = played_df.sort_values(by='Date')

    avg_h, avg_a = played_df['FTHG'].mean(), played_df['FTAG'].mean()
    teams = sorted(played_df['HomeTeam'].unique())
    stats = {}

    for team in teams:
        h_g, a_g = played_df[played_df['HomeTeam'] == team], played_df[played_df['AwayTeam'] == team]
        t_h_att, t_a_att = h_g['FTHG'].mean() / avg_h if not h_g.empty else 1.0, a_g['FTAG'].mean() / avg_a if not a_g.empty else 1.0
        t_h_def, t_a_def = h_g['FTAG'].mean() / avg_a if not h_g.empty else 1.0, a_g['FTHG'].mean() / avg_h if not a_g.empty else 1.0
        last_5_h, last_5_a = h_g.tail(5), a_g.tail(5)
        
        def get_form_str(matches, is_home):
            s = ""
            for _, r in matches.iterrows():
                if is_home: res = "✅" if r['FTHG'] > r['FTAG'] else ("⬜" if r['FTHG'] == r['FTAG'] else "❌")
                else: res = "✅" if r['FTAG'] > r['FTHG'] else ("⬜" if r['FTAG'] == r['FTAG'] else "❌")
                s += res
            return s

        stats[team] = {
            'h_att': (t_h_att * 0.6) + ((last_5_h['FTHG'].mean() / avg_h if not last_5_h.empty else t_h_att) * 0.4),
            'a_att': (t_a_att * 0.6) + ((last_5_a['FTAG'].mean() / avg_a if not last_5_a.empty else t_a_att) * 0.4),
            'h_def': t_h_def, 'a_def': t_a_def,
            'h_form_str': get_form_str(last_5_h, True), 'a_form_str': get_form_str(last_5_a, False)
        }
    return stats, avg_h, avg_a, teams, played_df, fixtures_df

def get_probabilities(e_d, e_h):
    p_d, p_r, p_a, p_o25 = 0, 0, 0, 0
    for i in range(10):
        for j in range(10):
            prob = poisson.pmf(i, e_d) * poisson.pmf(j, e_h)
            if i > j: p_d += prob
            elif i == j: p_r += prob
            else: p_a += prob
            if (i + j) > 2.5: p_o25 += prob
    return p_d * 100, p_r * 100, p_a * 100, p_o25 * 100

def render_risk_analysis(h, a, stats, ah, aa, t):
    ed, eh = stats[h]['h_att'] * stats[a]['a_def'] * ah, stats[a]['a_att'] * stats[h]['h_def'] * aa
    pd, pr, pa, po = get_probabilities(ed, eh)
    
    st.markdown(f"### {h} vs {a}")
    st.write(f"**{t['expected_score']}: {round(ed)} : {round(eh)}**")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(h, f"{pd:.1f}%")
    m2.metric(t["draw"], f"{pr:.1f}%")
    m3.metric(a, f"{pa:.1f}%")
    
    st.divider()
    st.subheader(t["risk_mgmt"])
    c_dnb, c_dc = st.columns(2)
    
    dnb_odd = (100 - pr) / pd if pd > 0 else 0
    with c_dnb:
        st.write(f"**Draw No Bet (DNB1 - {h})**")
        st.info(f"{t['fair_odd']}: {dnb_odd:.2f}")
        st.caption(t["dnb_info"])
        
    dc_odd = 100 / (pd + pr) if (pd + pr) > 0 else 0
    with c_dc:
        st.write(f"**Double Chance (1X)**")
        st.info(f"{t['fair_odd']}: {dc_odd:.2f}")
        st.caption(t["dc_info"])
    
    st.write(f"📊 {t['over_under']}: **{po:.1f}%**")

# --- UI LOGIKA ---
sel_lang = st.sidebar.selectbox("🌍 Language", list(LANG.keys()))
t = LANG[sel_lang]
st.sidebar.title(t["sidebar_title"])
vybrana_liga = st.sidebar.selectbox(t["select_league"], list(LIGY.keys()))

try:
    stats, avg_h, avg_a, zoznam_timov, played_df, fixtures_df = load_data_v31(LIGY[vybrana_liga])
    tab1, tab2, tab3, tab4 = st.tabs([t["tab1"], t["tab2"], t["tab3"], t["tab4"]])

    with tab1:
        st.header(t["tab1"])
        c1, c2 = st.columns(2)
        dom = c1.selectbox(t["home"], zoznam_timov, key="m_d")
        host = c2.selectbox(t["away"], zoznam_timov, index=1, key="m_h")
        if st.button(t["analyze_btn"]): render_risk_analysis(dom, host, stats, avg_h, avg_a, t)

    with tab2:
        st.header(t["tab2"])
        if st.button("RUN SCANNER"):
            res = []
            for dt in zoznam_timov:
                for ht in zoznam_timov:
                    if dt != ht:
                        ed, eh = stats[dt]['h_att'] * stats[ht]['a_def'] * avg_h, stats[ht]['a_att'] * stats[dt]['h_def'] * avg_a
                        p_d, _, _, _ = get_probabilities(ed, eh)
                        if p_d > 70: res.append({"Match": f"{dt}-{ht}", "Tip": "1", "Chance %": round(p_d, 2)})
            st.table(pd.DataFrame(res).sort_values(by="Chance %", ascending=False).reset_index(drop=True))

    with tab3:
        st.header(t["tab3"])
        if st.button(t["backtest_btn"]):
            correct, total = 0, 0
            for _, r in played_df.iterrows():
                ed, eh = stats[r['HomeTeam']]['h_att']*stats[r['AwayTeam']]['a_def']*avg_h, stats[r['AwayTeam']]['a_att']*stats[r['HomeTeam']]['h_def']*avg_a
                pd_, pr_, pa_, _ = get_probabilities(ed, eh)
                pred = "1" if pd_ > pr_ and pd_ > pa_ else ("2" if pa_ > pd_ and pa_ > pr_ else "X")
                real = "1" if r['FTHG'] > r['FTAG'] else ("X" if r['FTHG'] == r['FTAG'] else "2")
                total += 1
                if pred == real: correct += 1
            st.metric(t["reliability"], f"{(correct/total)*100:.2f}%")

    with tab4:
        st.header(t["tab4"])
        if st.button(t["gold_btn"]):
            reliab = []
            for tim in zoznam_timov:
                c, tot = 0, 0
                for _, r in played_df[(played_df['HomeTeam'] == tim) | (played_df['AwayTeam'] == tim)].iterrows():
                    ed, eh = stats[r['HomeTeam']]['h_att']*stats[r['AwayTeam']]['a_def']*avg_h, stats[r['AwayTeam']]['a_att']*stats[r['HomeTeam']]['h_def']*avg_a
                    pd_, pr_, pa_, _ = get_probabilities(ed, eh)
                    pred = "1" if pd_ > pr_ and pd_ > pa_ else ("2" if pa_ > pd_ and pa_ > pr_ else "X")
                    real = "1" if r['FTHG'] > r['FTAG'] else ("X" if r['FTHG'] == r['FTAG'] else "2")
                    tot += 1
                    if pred == real: c += 1
                if tot > 5: reliab.append({"Team": tim, "Acc %": round((c/tot)*100, 2)})
            st.session_state.gold_list = pd.DataFrame(reliab).sort_values(by="Acc %", ascending=False).head(3).reset_index(drop=True)
            st.session_state.gold_list.index += 1
            st.table(st.session_state.gold_list)
        
        if 'gold_list' in st.session_state:
            st.divider()
            st.subheader(t["quick_analyze"])
            q_team = st.selectbox("TOP Team", st.session_state.gold_list['Team'], key="q_t_s")
            team_fixtures = fixtures_df[(fixtures_df['HomeTeam'] == q_team) | (fixtures_df['AwayTeam'] == q_team)].head(5)
            if not team_fixtures.empty:
                f_opts = [f"{r['HomeTeam']} vs {r['AwayTeam']} ({r['Date']})" for _, r in team_fixtures.iterrows()]
                selected_f = st.selectbox(t["select_match"], f_opts)
                f_h, f_a = selected_f.split(" vs ")[0], selected_f.split(" vs ")[1].split(" (")[0]
                render_risk_analysis(f_h, f_a, stats, avg_h, avg_a, t)
            else: st.warning("No upcoming fixtures.")

except Exception as e:
    st.error(f"Error: {e}")