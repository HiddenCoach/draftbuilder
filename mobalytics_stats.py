"""Best-effort reader of publicly visible Mobalytics champion/role stats.
No private API, bypass, proxy, or synthetic numbers. HTML changes may break it.
"""
import io
import re
from datetime import datetime, timezone
import pandas as pd
import requests
import streamlit as st

URL='https://mobalytics.gg/lol/tier-list/stats'
ROLE={'TOP':'TOP','JUNGLE':'JGL','MID':'MID','MIDDLE':'MID','BOT':'ADC','BOTTOM':'ADC','ADC':'ADC','SUPPORT':'SUP'}

@st.cache_data(ttl=900,show_spinner=False)
def load_mobalytics():
    r=requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (compatible; LoLDraftLab/1.0)','Accept':'text/html'},timeout=20)
    r.raise_for_status()
    tables=pd.read_html(io.StringIO(r.text),displayed_only=False)
    found=[]
    for table in tables:
        table.columns=[str(c[-1] if isinstance(c,tuple) else c).strip().lower() for c in table.columns]
        columns={c:next((v for v in table.columns if k in v),None) for c,k in [('champ','champion'),('role','role'),('win','win'),('pick','pick'),('ban','ban'),('games','matches')]}
        if not all(columns[k] for k in ('champ','role','win','games')):continue
        for _,row in table.iterrows():
            role=ROLE.get(str(row[columns['role']]).strip().upper())
            if not role:continue
            name=str(row[columns['champ']]).strip()
            def number(col):
                if not col:return None
                m=re.search(r'\d+(?:[.,]\d+)?',str(row[col]).replace(' ',''))
                return float(m.group().replace(',','.')) if m else None
            wr=number(columns['win']); games=number(columns['games'])
            if not name or wr is None or games is None or not (0<=wr<=100) or games<=0:continue
            found.append({'champion':name,'role':role,'games':int(games),'wins':round(games*wr/100),'pick_rate':number(columns['pick']),'ban_rate':number(columns['ban'])})
    if not found:raise ValueError('La page Mobalytics ne fournit pas de tableau HTML exploitable. Aucun chiffre inventé ou remplacé silencieusement.')
    patch=re.search(r'(?:Patch|patch)\s*(\d{2}\.\d{1,2})',r.text)
    return pd.DataFrame(found).drop_duplicates(['champion','role']),{'source':'Mobalytics — données publiques','patch':patch.group(1) if patch else 'non détecté','updated_at':datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),'region':'Selon filtres publics Mobalytics','rank':'Selon filtres publics Mobalytics','url':URL}

def panel():
    with st.sidebar.expander('📊 Mobalytics — statistiques',expanded=True):
        st.caption('Source demandée : Mobalytics. Actualisation serveur maximum toutes les 15 minutes. Les chiffres sont des statistiques de parties terminées, pas un flux de draft professionnelle.')
        if st.button('🔄 Charger les stats Mobalytics',use_container_width=True,key='moba_load'):
            try:
                with st.spinner('Lecture du tableau public Mobalytics…'):
                    df,meta=load_mobalytics()
                st.session_state.update(live_stats_df=df,live_stats_meta=meta)
                st.success(f'{len(df)} couples champion/poste importés')
            except Exception as exc:
                st.error('Mobalytics indisponible : '+str(exc))
                st.info('Aucune statistique fictive ne sera affichée. Vérifie les données directement sur Mobalytics ou utilise un export autorisé.')
        st.link_button('Voir les statistiques Mobalytics',URL,use_container_width=True)
        meta=st.session_state.get('live_stats_meta',{})
        if meta.get('source','').startswith('Mobalytics'):
            st.caption('Source : Mobalytics · Patch : '+meta.get('patch','?')+' · Collecte : '+meta.get('updated_at','?'))
