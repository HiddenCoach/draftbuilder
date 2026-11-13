import copy
import json
from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(page_title='LoL Draft Lab',page_icon='⚔️',layout='wide',initial_sidebar_state='expanded')
ROLES=['TOP','JGL','MID','ADC','SUP']
DEFAULT=json.loads((Path(__file__).parent/'drafts.json').read_text(encoding='utf-8'))
if 'drafts' not in st.session_state: st.session_state.drafts=copy.deepcopy(DEFAULT)
if 'custom' not in st.session_state: st.session_state.custom=[]
if 'notes' not in st.session_state: st.session_state.notes={}
if 'scouting' not in st.session_state: st.session_state.scouting={}
if 'simulation' not in st.session_state: st.session_state.simulation={}
st.markdown('''<style>
.stApp {background:#0c1322;color:#e8edf7} [data-testid="stSidebar"]{background:#111c30}
.block-container{padding-top:1.7rem;max-width:1450px} h1,h2,h3{letter-spacing:-.03em}
[data-testid="stMetric"]{background:#182640;padding:15px;border-radius:12px}
.stButton button[kind="primary"]{background:#2474d5;border:0}
</style>''',unsafe_allow_html=True)

def canon(x): return str(x).lower().replace('’',"'").strip()
def check(d):
    own={canon(x) for x in d['champions'].values() if x.strip()}
    return [b for b in d['bans'] if canon(b) in own]
def markdown(d):
    lines=[f"# {d['id']} — {d['type']}",'', '## Composition']+[f"- {r}: {d['champions'][r]}" for r in ROLES]
    lines+=['','## Bans prioritaires']+[f"- **{b}** : {d.get('ban_reasons',{}).get(b,'À valider selon les picks adverses')}" for b in d['bans']]
    lines+=['','## Priorité de sécurisation',' → '.join(d['pick_priority']),'','## Plan de jeu',f"**Early :** {d['early']}",f"**Mid :** {d['mid']}",f"**Late :** {d['late']}",'','## Win condition',d['win_condition'],'','## Pivots']+[f"- {r}: {', '.join(d['pivots'].get(r,[]))}" for r in ROLES]
    return '\n\n'.join(lines)

def draft_editor(d, prefix):
    st.subheader('Modifier / approfondir cette fiche')
    with st.form(prefix+'editor'):
        cols=st.columns(5)
        champs={r:cols[i].text_input(r,value=d['champions'][r]) for i,r in enumerate(ROLES)}
        bans=st.text_input('Bans prioritaires (séparés par des virgules)',value=', '.join(d['bans']))
        early=st.text_area('Plan early',d['early'],height=100)
        mid=st.text_area('Plan mid',d['mid'],height=100)
        late=st.text_area('Plan late',d['late'],height=100)
        win=st.text_area('Win condition',d['win_condition'],height=90)
        save=st.form_submit_button('💾 Enregistrer les modifications',type='primary')
    if save:
        newb=[b.strip() for b in bans.split(',') if b.strip()]
        overlap=set(map(canon,newb)) & set(map(canon,champs.values()))
        if overlap: st.error('Auto-ban interdit : '+', '.join(overlap))
        elif len(set(map(canon,champs.values())))<5: st.error('Un champion apparaît plusieurs fois dans notre composition.')
        else:
            d.update(champions=champs,bans=newb,early=early,mid=mid,late=late,win_condition=win)
            d['ban_reasons']={b:d.get('ban_reasons',{}).get(b,'Counter à justifier selon les picks adverses.') for b in newb}
            st.success('Fiche modifiée dans cette session. Pense à exporter la bibliothèque pour la conserver.')
            st.rerun()

st.sidebar.title('⚔️ LoL Draft Lab')
st.sidebar.caption('Playbook compétitif • Worlds / LCK : inspirations tactiques, pas de statistiques live')
page=st.sidebar.radio('Navigation',['📚 Draft Builder','🔬 Analyse approfondie','🎮 Draft Room 10 picks','🎯 Scouting & counters','🗂️ Ma bibliothèque'],label_visibility='collapsed')
all_drafts=st.session_state.drafts+st.session_state.custom
st.sidebar.divider()
st.sidebar.metric('Drafts disponibles',len(all_drafts))
st.sidebar.caption('Données enregistrées en session : export JSON recommandé pour conserver le travail.')

if page=='📚 Draft Builder':
    st.title('Draft Builder')
    st.caption('40 compositions • 8 archétypes • bans anti-counter sans auto-ban')
    a,b=st.columns([1,2])
    types=sorted(set(x['type'] for x in all_drafts))
    typ=a.selectbox('Archétype',types)
    options=[x for x in all_drafts if x['type']==typ]
    d=b.selectbox('Composition',options,format_func=lambda x:x['id']+' — '+' / '.join(x['champions'].values()))
    cols=st.columns(5)
    for i,r in enumerate(ROLES):
        with cols[i]:
            st.caption(r)
            st.markdown(f"### {d['champions'][r]}")
    st.divider()
    left,right=st.columns([1,1.3])
    with left:
        st.subheader('🚫 Bans prioritaires')
        for i,ban in enumerate(d['bans']): st.markdown(f"**B{i+1} — {ban}**  "+d.get('ban_reasons',{}).get(ban,'Counter à valider'))
        if check(d): st.error('Auto-ban détecté : '+', '.join(check(d)))
        else: st.success('Aucun champion de notre équipe n’est banni.')
        st.subheader('🔀 Priorité de sécurisation')
        st.write(' → '.join(d['pick_priority']))
        st.caption('Priorité stratégique : l’ordre exact B1–B5 dépend des réponses adverses.')
    with right:
        st.subheader('🗺️ Plan de jeu')
        for title,key in [('Early • 0–14 min','early'),('Mid • 14–25 min','mid'),('Late • 25 min +','late')]:
            with st.expander(title,expanded=True):st.write(d[key])
        st.subheader('🎯 Win condition')
        st.info(d['win_condition'])
        st.subheader('🔄 Pivots par rôle')
        for role in ROLES: st.write(f"**{role} :** {', '.join(d['pivots'].get(role,[]))}")
    st.download_button('⬇️ Exporter la fiche Markdown',markdown(d),file_name=d['id']+'_draft.md')
    with st.expander('✏️ Modifier et approfondir la fiche'): draft_editor(d,'main')

elif page=='🔬 Analyse approfondie':
    st.title('Analyse approfondie')
    d=st.selectbox('Draft à analyser',all_drafts,format_func=lambda x:x['id']+' — '+x['type']+' — '+', '.join(x['champions'].values()))
    st.subheader('Identité et win condition')
    st.info(d['win_condition'])
    st.markdown('### Plan de match')
    for name,key in [('0–14 min : early','early'),('14–25 min : mid','mid'),('25 min + : late','late')]:
        with st.expander(name,expanded=True): st.write(d[key])
    st.markdown('### Menaces et contres')
    for b in d['bans']: st.write(f"**{b}** — {d.get('ban_reasons',{}).get(b,'À vérifier')}")
    st.markdown('### Pivots de draft')
    for role in ROLES:
        st.write(f"**{role} ({d['champions'][role]})** → "+', '.join(d['pivots'].get(role,[])))
    st.markdown('### Checklist pré-fight')
    for x in ['Waves préparées','Vision des flancs','Flashs ennemis identifiés','Ultimates synchronisés','Menace sur le carry identifiée','Cible d’engage annoncée']:
        st.checkbox(x,key='check_'+d['id']+x)
    note=st.text_area('Notes de review / adaptations scrim',st.session_state.notes.get(d['id'],''),height=140,key='note_'+d['id'])
    if st.button('Enregistrer la review'): st.session_state.notes[d['id']]=note;st.success('Review conservée dans la session.')
    with st.expander('✏️ Modifier la stratégie et les bans'): draft_editor(d,'deep')

elif page=='🎮 Draft Room 10 picks':
    st.title('Draft Room — Blue / Red Side')
    st.caption('Ordre officiel des 10 picks : B1, R1, R2, B2, B3, R3, puis R4, B4, B5, R5. Deux phases de bans : 3 + 2 par équipe.')
    d=st.selectbox('Plan de départ',all_drafts,format_func=lambda x:x['id']+' — '+x['type'])
    side=st.radio('Notre side',['Blue','Red'],horizontal=True)
    key=d['id']+'_'+side
    if key not in st.session_state.simulation:
        seq=['B1','R1','R2','B2','B3','R3','R4','B4','B5','R5']
        ours=['B1','B2','B3','B4','B5'] if side=='Blue' else ['R1','R2','R3','R4','R5']
        values={slot:'' for slot in seq}
        for slot,ch in zip(ours,d['pick_priority']):values[slot]=ch
        st.session_state.simulation[key]={'picks':values,'blue_bans':d['bans'][:5] if side=='Blue' else ['']*5,'red_bans':d['bans'][:5] if side=='Red' else ['']*5}
    sim=st.session_state.simulation[key]
    c1,c2=st.columns(2)
    with c1:
        st.subheader('🔵 Blue bans')
        for i in range(3):sim['blue_bans'][i]=st.text_input(f'Blue ban {i+1}',sim['blue_bans'][i],key=key+'bb'+str(i))
    with c2:
        st.subheader('🔴 Red bans')
        for i in range(3):sim['red_bans'][i]=st.text_input(f'Red ban {i+1}',sim['red_bans'][i],key=key+'rb'+str(i))
    st.subheader('Phase 1 — Picks')
    seq=['B1','R1','R2','B2','B3','R3','R4','B4','B5','R5']
    for slot in seq[:6]:
        sim['picks'][slot]=st.text_input(slot,sim['picks'][slot],key=key+slot)
    st.subheader('Phase 2 — Bans')
    c1,c2=st.columns(2)
    with c1:
        for i in (3,4):sim['blue_bans'][i]=st.text_input(f'Blue ban {i+1}',sim['blue_bans'][i],key=key+'bb'+str(i))
    with c2:
        for i in (3,4):sim['red_bans'][i]=st.text_input(f'Red ban {i+1}',sim['red_bans'][i],key=key+'rb'+str(i))
    st.subheader('Phase 2 — Picks')
    for slot in seq[6:]:sim['picks'][slot]=st.text_input(slot,sim['picks'][slot],key=key+slot)
    picks=[(slot,canon(v)) for slot,v in sim['picks'].items() if v.strip()]
    bans=[canon(v) for v in sim['blue_bans']+sim['red_bans'] if v.strip()]
    duplicates=sorted({v for _,v in picks if sum(v==w for _,w in picks)>1})
    invalid=[slot for slot,v in picks if v in bans]
    ownslots=['B1','B2','B3','B4','B5'] if side=='Blue' else ['R1','R2','R3','R4','R5']
    ownbans=sim['blue_bans'] if side=='Blue' else sim['red_bans']
    selfbans=[v for v in ownbans if canon(v) in {canon(sim['picks'][s]) for s in ownslots}]
    if duplicates:st.error('Champion pick plusieurs fois : '+', '.join(duplicates))
    if invalid:st.error('Pick déjà banni aux slots : '+', '.join(invalid))
    if selfbans:st.error('Auto-ban détecté : '+', '.join(selfbans))
    if not duplicates and not invalid and not selfbans:st.success('Aucun conflit entre les picks et les bans renseignés.')
    st.download_button('⬇️ Exporter la simulation JSON',json.dumps(sim,ensure_ascii=False,indent=2),file_name=f'{d["id"]}_{side}_simulation.json',mime='application/json')

elif page=='🎯 Scouting & counters':
    st.title('Scouting & Counter Analyzer')
    d=st.selectbox('Notre composition',all_drafts,format_func=lambda x:x['id']+' — '+x['type'])
    st.subheader('Menaces prioritaires')
    for ban in d['bans']:
        with st.expander(ban):
            st.write(d.get('ban_reasons',{}).get(ban,'À vérifier'))
            st.caption('Si le rôle du champion est déjà verrouillé sans flex crédible, réévaluer ce ban.')
    st.subheader('Scouting adversaire')
    opp=st.text_input('Nom de l’équipe adverse',value='Adversaire')
    info=st.session_state.scouting.get(opp,{})
    with st.form('scout_form'):
        pools={r:st.text_input(f'Champion pool {r}',info.get(r,'')) for r in ROLES}
        notes=st.text_area('Tendances / bans ciblés / habitudes',info.get('notes',''))
        saved=st.form_submit_button('💾 Sauvegarder le scouting')
    if saved:
        st.session_state.scouting[opp]={**pools,'notes':notes};st.success('Scouting conservé dans la session.')
    st.markdown('### Pivots si un counter est disponible')
    role=st.selectbox('Rôle à adapter',ROLES)
    st.write('Champion initial : **'+d['champions'][role]+'**')
    st.write('Alternatives : **'+', '.join(d['pivots'].get(role,[]))+'**')
    st.caption('Un pivot exige une nouvelle vérification des dégâts, matchups, bans et conditions de victoire.')

else:
    st.title('Ma bibliothèque')
    st.caption('Création de drafts, import/export et sauvegarde des analyses.')
    with st.expander('➕ Créer une draft personnalisée',expanded=True):
        with st.form('newdraft'):
            name=st.text_input('Identifiant unique',placeholder='CUSTOM-01')
            typ=st.selectbox('Archétype',sorted(set(x['type'] for x in DEFAULT)))
            cs=st.columns(5)
            champions={r:cs[i].text_input(r,key='new'+r) for i,r in enumerate(ROLES)}
            bans=st.text_input('Bans (virgules)')
            win=st.text_area('Win condition')
            create=st.form_submit_button('Créer')
        if create:
            bn=[x.strip() for x in bans.split(',') if x.strip()]
            if not name or any(not v for v in champions.values()):st.error('Identifiant et 5 champions requis.')
            elif name in [x['id'] for x in all_drafts]:st.error('Identifiant déjà utilisé.')
            elif set(map(canon,bn)) & set(map(canon,champions.values())):st.error('Impossible de bannir un champion de notre équipe.')
            elif len(set(map(canon,champions.values())))<5:st.error('Doublon de champion.')
            else:
                st.session_state.custom.append({'id':name,'type':typ,'champions':champions,'bans':bn,'ban_reasons':{b:'À préciser' for b in bn},'pick_priority':list(champions.values()),'early':'À compléter','mid':'À compléter','late':'À compléter','win_condition':win or 'À compléter','pivots':{r:[] for r in ROLES},'notes':'Draft personnalisée'})
                st.success('Draft créée. Elle apparaît dans le Draft Builder.')
    st.subheader('Export de la bibliothèque')
    bundle={'drafts':st.session_state.drafts,'custom':st.session_state.custom,'notes':st.session_state.notes,'scouting':st.session_state.scouting,'simulation':st.session_state.simulation}
    st.download_button('⬇️ Sauvegarder toutes les données (JSON)',json.dumps(bundle,ensure_ascii=False,indent=2),file_name='lol_draft_lab_backup.json',mime='application/json',type='primary')
    upload=st.file_uploader('Importer une sauvegarde JSON',type='json')
    if upload and st.button('Restaurer la sauvegarde'):
        try:
            data=json.load(upload)
            if not isinstance(data.get('drafts'),list):raise ValueError('Champ drafts manquant')
            for entry in data['drafts']+data.get('custom',[]):
                if not all(k in entry for k in ('id','type','champions','bans','pick_priority','early','mid','late','win_condition','pivots')):raise ValueError('Structure de draft invalide')
                if set(map(canon,entry['bans'])) & set(map(canon,entry['champions'].values())):raise ValueError('Une draft contient un auto-ban')
            for k in ('drafts','custom','notes','scouting','simulation'):
                if k in data:st.session_state[k]=data[k]
            st.success('Sauvegarde restaurée.');st.rerun()
        except Exception as e:st.error(f'Import impossible : {e}')
    st.subheader('Inventaire')
    st.dataframe(pd.DataFrame([{'ID':x['id'],'Type':x['type'],**x['champions']} for x in all_drafts]),hide_index=True,use_container_width=True)
    st.caption('Les données ne sont pas synchronisées avec Riot ni les sites de statistiques. La mise à jour méta nécessite une révision manuelle des fiches.')
