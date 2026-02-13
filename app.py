import streamlit as st
import pandas as pd
from scipy.stats import poisson

# --- KONFIGURÁCIA ---
st.set_page_config(page_title="Pro Betting AI - Risk Management", layout="wide")

# (Predchádzajúce funkcie load_data, get_probabilities zostávajú nezmenené...)
# [Doplnené pre stručnosť, v app.py použi kompletné funkcie z verzie 2.9]

def render_advanced_analysis(h, a, stats, ah, aa, t, bankroll):
    ed, eh = stats[h]['h_att'] * stats[a]['a_def'] * ah, stats[a]['a_att'] * stats[h]['h_def'] * aa
    pd, pr, pa, po = get_probabilities(ed, eh)
    
    st.markdown(f"### {h} vs {a}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Výhra " + h, f"{pd:.1f}%")
    col2.metric("Remíza", f"{pr:.1f}%")
    col3.metric("Výhra " + a, f"{pa:.1f}%")

    st.divider()
    st.subheader("🛡️ Strategické poistenie (Risk Management)")
    
    # VÝPOČET DNB (Draw No Bet)
    # Férový kurz DNB = (100 - šanca na remízu) / šanca na výhru
    dnb_fair_quote = (100 - pr) / pd if pd > 0 else 0
    # Double Chance (1X) = 100 / (šanca na 1 + šanca na X)
    dc_fair_quote = 100 / (pd + pr) if (pd + pr) > 0 else 0

    c_risk1, c_risk2 = st.columns(2)
    with c_risk1:
        st.write("**Draw No Bet (DNB1)**")
        st.info(f"Férový kurz: {dnb_fair_quote:.2f}")
        st.caption("Ak zápas skončí remízou, vklad sa vracia.")
    
    with c_risk2:
        st.write("**Double Chance (1X)**")
        st.info(f"Férový kurz: {dc_fair_quote:.2f}")
        st.caption("Vyhrávaš pri výhre domáceho aj pri remíze.")

    # Kellyho odporúčanie pre začiatočníka (Fractional Kelly 10%)
    st.divider()
    if pd > 0:
        st.write("💡 **Rada pre začiatočníka:**")
        if pd > 60:
            st.success(f"Vysoká pravdepodobnosť na výhru {h}. Odporúčame stávku bez remízy (DNB) pre minimalizáciu straty.")
        elif (pd + pr) > 75:
            st.warning(f"Zápas je vyrovnanejší. Bezpečnejšia voľba je Double Chance (1X).")

# --- HLAVNÝ KÓD (zjednotený z 2.9) ---
# [Vlož sem kompletný kód z verzie 2.9 a vymeň render_analysis za túto novú render_advanced_analysis]