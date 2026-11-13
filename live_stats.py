"""Optional continuously refreshed statistics feed. No invented win rates.
Accepted JSON: {"patch":"16.22","updated_at":"...","rows":[{"champion":"Vi","role":"JGL","games":1000,"wins":510,"picks":1000,"bans":300,"total_games":10000},...]}
Or CSV with same columns. A licensed/authorized data supplier must provide this feed.
"""
import io
import json
import pandas as pd
import requests
import streamlit as st
from draft_intelligence import norm
REQUIRED={'champion','role','games','wins'}
@st.cache_data(ttl=300,show_spinner=False)
def fetch_url(url):
    if not url.startswith('https://'): raise ValueError('URL HTTPS obligatoire')
    resp=requests.get(url,timeout=12,headers={'Accept':'application/json,text/csv'})
    resp.raise_for_status()
    if len(resp.content)>8_000_000: raise ValueError('Flux trop volumineux')
    if 'json' in resp.headers.get('content-type','') or url.split('?')[0].endswith('.json'):
        return parse_payload(resp.json())
    return parse_payload(resp.text)
def parse_payload(data):
    if isinstance(data,str):
        try: data=json.loads(data)
        except json.JSONDecodeError: return validate(pd.read_csv(io.StringIO(data))),{}
    if isinstance(data,dict):
        meta={k:str(data.get(k,'')) for k in ('patch','updated_at','source','queue','region','rank')}
        data=data.get('rows',[])
    else:meta={}
    return validate(pd.DataFrame(data)),meta
def validate(df):
    missing=REQUIRED-set(df.columns)
    if missing: raise ValueError('Colonnes manquantes : '+', '.join(sorted(missing)))
    df=df.copy()
    df['role']=df['role'].astype(str).str.upper().str.strip()
    df['champion']=df['champion'].astype(str).str.strip()
    for c in ['games','wins','picks','bans','total_games']:
        if c not in df:df[c]=0
        df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0)
    df=df[(df.games>0)&(df.wins>=0)&(df.wins<=df.games)&df.role.isin(['TOP','JGL','MID','ADC','SUP'])]
    df['winrate']=100*df.wins/df.games
    df['confidence']=df.games/(df.games+500)  # shrink tiny samples
    return df
def get_stats():
    return st.session_state.get('live_stats_df'),st.session_state.get('live_stats_meta',{})
def rank_candidates(recs,role=None,mode='pick'):
    df,meta=get_stats()
    if df is None or df.empty:return recs
    enriched=[]
    for rec in recs:
        name=rec['name']; r=rec.get('role',role)
        rows=df[df.champion.map(norm)==norm(name)]
        if r: rows=rows[rows.role==r]
        if rows.empty:enriched.append(dict(rec,stat_note='Aucun échantillon',stat_score=None));continue
        row=rows.sort_values('games',ascending=False).iloc[0]
        # Conservative: baseline qualitative score plus a bounded statistical modifier.
        delta=max(-10,min(10,(row.winrate-50)*row.confidence*2))
        if mode=='ban': delta=max(-10,min(10,delta))
        enriched.append(dict(rec,score=rec['score']+delta,stat_score=float(row.winrate),stat_games=int(row.games),stat_note=f"{row.winrate:.1f}% WR / {int(row.games):,} parties"))
    return sorted(enriched,key=lambda x:-x['score'])
def settings_panel():
    st.sidebar.divider()
    with st.sidebar.expander('📡 Statistiques actualisées',expanded=False):
        url=st.text_input('URL HTTPS de données agrégées JSON/CSV',value=st.session_state.get('stats_url',''),help='Flux autorisé par votre fournisseur. Rafraîchissement serveur toutes les 5 minutes.')
        if st.button('Connecter / actualiser',use_container_width=True):
            try:
                df,meta=fetch_url(url)
                st.session_state.update(live_stats_df=df,live_stats_meta=meta,stats_url=url)
                st.success(f'{len(df)} lignes chargées')
            except Exception as e:st.error(f'Flux indisponible : {e}')
        up=st.file_uploader('Ou importer des stats CSV/JSON',type=['csv','json'])
        if up and st.button('Charger ce fichier',use_container_width=True):
            try:
                df,meta=parse_payload(up.getvalue().decode('utf-8-sig'))
                st.session_state.update(live_stats_df=df,live_stats_meta=meta)
                st.success(f'{len(df)} lignes chargées')
            except Exception as e:st.error(str(e))
        with st.expander('Riot API — échantillon réel de parties classées',expanded=False):
            st.caption('Renseigne des Riot IDs pour analyser leurs parties récentes. Ce ne sont PAS des winrates globaux ni des statistiques LCK/Worlds. La clé reste dans ta session, jamais dans les exports.')
            key=st.text_input('Clé Riot API',type='password',key='riot_api_key')
            ids=st.text_area('Riot IDs, un par ligne (Pseudo#TAG)',key='riot_ids',height=90)
            region=st.selectbox('Serveur',['EUW1','EUN1','KR','NA1','BR1','JP1'],key='riot_region')
            count=st.slider('Matchs par compte',5,20,10)
            if st.button('🔄 Collecter les vraies statistiques Riot',use_container_width=True):
                try:
                    from riot_sample import collect_sample
                    with st.spinner('Collecte des matchs terminés via Riot…'):
                        payload=collect_sample(key,[x.strip() for x in ids.splitlines() if x.strip()],region,count)
                    df,meta=parse_payload(payload)
                    meta['sample_matches']=str(payload['sample_matches'])
                    st.session_state.update(live_stats_df=df,live_stats_meta=meta)
                    st.success(f"{payload['sample_matches']} matchs collectés ; {len(df)} couples champion/rôle")
                except Exception as e:st.error(str(e))
        df,meta=get_stats()
        if df is not None:
            st.caption(f"{len(df)} lignes · patch {meta.get('patch') or 'non indiqué'} · MAJ {meta.get('updated_at') or 'non indiquée'}")
            st.caption('Source : '+meta.get('source','non précisée')+' · '+meta.get('sample_matches','?')+' matchs échantillonnés (si Riot).')
            if st.button('Désactiver les statistiques'):
                st.session_state.pop('live_stats_df',None);st.session_state.pop('live_stats_meta',None);st.rerun()
        else:st.warning('Aucun flux connecté : recommandations qualitatives uniquement.')
