from live_stats import rank_candidates, get_stats
"""Interactive draft room, portrait lookup, timer and rule-based counter analysis."""
import json
import time
import unicodedata
from collections import Counter
from urllib.request import urlopen
import streamlit as st
from draft_intelligence import recommend_bans, recommend_picks, role_candidates, assign_role, open_roles, canon
from role_advisor import advise_roles

SEQUENCE = [
 ('ban','B',1),('ban','R',1),('ban','B',2),('ban','R',2),('ban','B',3),('ban','R',3),
 ('pick','B',1),('pick','R',1),('pick','R',2),('pick','B',2),('pick','B',3),('pick','R',3),
 ('ban','R',4),('ban','B',4),('ban','R',5),('ban','B',5),
 ('pick','R',4),('pick','B',4),('pick','B',5),('pick','R',5)]
ROLES=['TOP','JGL','MID','ADC','SUP']
# Qualitative matchup guidance: not a live winrate database.
COUNTERS={
 'Poppy':('Anti-dash','Gêne Jarvan IV, Nautilus, Vi, Rakan et les compositions dive.', ['Jarvan IV','Vi','Rakan','Nautilus','Lee Sin','Alistar','Camille','Ambessa']),
 'Renata Glasc':('Anti-engage','Retourne les engages groupés et protège les carries.', ['Jarvan IV','Nautilus','Rakan','Rell','Wukong','Amumu','Nocturne']),
 'Olaf':('Anti-CC','Son ultime limite le contrôle et menace les carries immobiles.', ['Nautilus','Sejuani','Maokai','Leona','Rell','Jarvan IV']),
 'Nocturne':('Dive longue portée','Contourne la vision et atteint les carries vulnérables.', ['Jhin','Jinx','Orianna','Viktor','Varus','Syndra','Aphelios']),
 'Braum':('Peel / bouclier','Réduit la valeur des projectiles et protège la backline.', ['Jhin','Ashe','Ezreal','Varus','Lucian']),
 'Xayah':('Anti-dive','Peut esquiver le verrouillage initial avec son ultime.', ['Vi','Jarvan IV','Nautilus','Nocturne','Rakan']),
 'Gwen':('Anti-frontline','DPS prolongé sur tanks et protection contre certaines attaques à distance.', ["K’Sante","K'Sante",'Ornn','Sejuani','Maokai']),
 'Cassiopeia':('DPS / zone','DPS soutenu et Miasmes contre les champions à mobilité.', ['Jarvan IV','Ambessa','Vi','K’Sante','Rakan']),
 'Malphite':('Engage à distance','Force un combat sur les carries à faible mobilité.', ['Jhin','Jinx','Varus','Jayce','Syndra','Orianna']),
 'Lissandra':('Lockdown','Neutralise les assassins et menace les flancs.', ['Akali','Qiyana','Ahri','LeBlanc','Ambessa']),
 'Morgana':('Bouclier anti-CC','Empêche un catch clé et réduit la fiabilité des hooks.', ['Nautilus','Blitzcrank','Thresh','Leona','Ashe']),
 'Zac':('Engage hors vision','Contourne les lignes de poke et atteint la backline.', ['Jayce','Varus','Jhin','Syndra','Karma']),
 'Camille':('Menace de side / dive','Peut isoler un carry et mettre sous pression une side.', ['Jhin','Orianna','Viktor','Ezreal']),
 'Viktor':('Zone / DPS','Punition des engages frontaux et dégâts soutenus.', ['Jarvan IV','K’Sante','Nautilus','Jhin']),
 'Ezreal':('Mobilité','Difficile à attraper avec un engage linéaire.', ['Jarvan IV','Nautilus','Sejuani']),
 'Draven':('Pression early','Punit les botlanes qui doivent attendre leurs spikes.', ['Jinx','Aphelios','Smolder','Sivir']),
 'Blitzcrank':('Pick','Menace les carries immobiles et les supports enchanteurs.', ['Jinx','Lulu','Orianna','Aphelios','Jhin']),
}

def norm(x):
    x=unicodedata.normalize('NFKD',str(x).replace('’',"'"))
    return ''.join(c for c in x if not unicodedata.combining(c)).casefold().strip()

@st.cache_data(ttl=86400,show_spinner=False)
def champion_catalog():
    """Fetch current Riot Data Dragon catalog; fall back gracefully offline."""
    try:
        with urlopen('https://ddragon.leagueoflegends.com/api/versions.json',timeout=4) as response:
            version=json.load(response)[0]
        with urlopen(f'https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json',timeout=5) as response:
            data=json.load(response)['data']
        names={norm(v['name']):(v['name'],v['id']) for v in data.values()}
        # Some names differ from conventional shorthand.
        for alias,target in [('renata','Renata Glasc'),('wukong','MonkeyKing'),('nunu','Nunu & Willump')]:
            if norm(target) in names: names[norm(alias)]=names[norm(target)]
        return version,names
    except Exception:
        return None,{}

def portrait(name, width=65):
    version,catalog=champion_catalog()
    info=catalog.get(norm(name))
    if info and version:
        st.image(f'https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{info[1]}.png',width=width)
    else:
        st.markdown('⚔️')

def recommendations(d,enemy,own_bans,enemy_bans,selected):
    our=[norm(x) for x in d['champions'].values()]
    already={norm(x) for x in own_bans+enemy_bans+selected if x}
    scores=[]
    for name,(kind,why,targets) in COUNTERS.items():
        if norm(name) in already or norm(name) in our:continue
        matches=[x for x in targets if norm(x) in our]
        if not matches:continue
        score=len(set(norm(x) for x in matches))*2
        if norm(name) in [norm(x) for x in d.get('bans',[])]:score+=3
        scores.append((score,name,kind,why,', '.join(matches)))
    return sorted(scores,reverse=True)[:5]

# Role-aware replacements: coaching heuristics, not live matchup win rates.
REPLACEMENT_NOTES={
 'TOP': {'Gnar':'Teamfight AoE et bonne pression de lane; attention à la barre de rage.', 'Ornn':'Frontline et engage fiables; renforce le scaling.', 'Rumble':'Dégâts magiques et contrôle des zones d’objectif.', 'Gragas':'Peel, flexibilité et désengage.', 'Sion':'Frontline et engage longue portée.'},
 'JGL': {'Sejuani':'Engage et frontline, très bon suivi des contrôles.', 'Vi':'Accès fiable à une cible prioritaire, mais engage moins multi-cibles.', 'Wukong':'Engage AoE et excellente synergie avec Orianna.', 'Maokai':'Vision et contrôle de zone pour les objectifs.', 'Xin Zhao':'Escarmouches early et protection du backline.'},
 'MID': {'Syndra':'Burst et pick, conserve une bonne priorité mid.', 'Viktor':'DPS soutenu et contrôle de zone; combo engage moins explosif.', 'Taliyah':'Contrôle des déplacements et rotations rapides.', 'Hwei':'Waveclear et contrôle de zone.', 'Azir':'DPS soutenu et engage situationnel.'},
 'ADC': {'Kai’Sa':'Follow-up dive sur Jarvan/Nautilus, plus de mobilité.', 'Ashe':'Utilitaire, engage longue portée et kite.', 'Varus':'Contrôle et dégâts selon build, utile contre frontline.', 'Ezreal':'Mobilité et sécurité en weakside.', 'Xayah':'Sécurité contre les dives et DPS soutenu.'},
 'SUP': {'Braum':'Protection des carries et front-to-back.', 'Alistar':'Engage et peel polyvalents.', 'Rakan':'Engage mobile, excellent follow-up Orianna.', 'Leona':'Engage fiable sur cible unique.', 'Rell':'Engage AoE et combo avec Orianna.'}
}
ROLE_FALLBACK={
 'TOP':['Gnar','Ornn','Rumble','Gragas','Sion'],
 'JGL':['Sejuani','Vi','Wukong','Maokai','Xin Zhao'],
 'MID':['Syndra','Viktor','Taliyah','Hwei','Azir'],
 'ADC':['Kai’Sa','Ashe','Varus','Ezreal','Xayah'],
 'SUP':['Braum','Alistar','Rakan','Leona','Rell']
}

def role_replacements(d, role, used, planned, enemy_picks, catalog_names):
    """Rank available same-role pivots; never return any locked/banned/planned champion."""
    blocked={norm(x) for x in used if x}
    blocked.update(norm(x) for r,x in planned.items() if r!=role and x)
    options=list(dict.fromkeys(d.get('pivots',{}).get(role,[])+ROLE_FALLBACK[role]))
    known={norm(x) for x in catalog_names}
    result=[]
    for rank,name in enumerate(options):
        if norm(name) in blocked or (known and norm(name) not in known):continue
        score=max(1,100-rank*12)
        explanation=REPLACEMENT_NOTES.get(role,{}).get(name,'Alternative du même rôle, à valider selon le matchup.')
        # Heuristic: preserve frontline/engage or DPS depending on opposing picks.
        if role=='ADC' and any(norm(x) in {norm('Ornn'),norm('Sion'),norm('K’Sante'),norm('Sejuani')} for x in enemy_picks):
            if norm(name) in {norm('Varus'),norm('Kai’Sa'),norm('Xayah')}:score+=8
        if role=='JGL' and norm(name)==norm('Wukong') and norm(planned.get('MID',''))==norm('Orianna'):score+=8
        result.append((score,name,explanation))
    return sorted(result,key=lambda x:-x[0])[:5]

def render_room(d):
    from champion_ui import gallery_picker
    st.title('🎮 Draft Room PRO')
    st.caption('Portraits Riot Data Dragon (si connexion disponible) • 20 actions dans l’ordre • timer • recommandations explicables')
    side=st.radio('Notre équipe', ['Blue','Red'],horizontal=True,key='pro_side')
    key=f"pro_{d['id']}_{side}"
    if key not in st.session_state:
        st.session_state[key]={'step':0,'entries':{},'role_assignments':{'B':{},'R':{}},'seconds':30,'remaining':30,'running':False,'started':0.0}
    s=st.session_state[key]
    version,catalog=champion_catalog()
    names=sorted({v[0] for v in catalog.values()})
    if not names:
        names=sorted(set(list(d['champions'].values())+d['bans']+list(COUNTERS)))
        st.warning('Catalogue Riot indisponible : saisie limitée au catalogue local. Les portraits réapparaîtront avec une connexion Internet.')
    s.setdefault('role_assignments',{'B':{},'R':{}})
    selected=list(s['entries'].values())
    used={norm(x) for x in selected if x}
    ownteam='B' if side=='Blue' else 'R'
    enemyteam='R' if side=='Blue' else 'B'
    enemy_picks=[v for (kind,t,i),v in s['entries'].items() if kind=='pick' and t==enemyteam]
    enemy_bans=[v for (kind,t,i),v in s['entries'].items() if kind=='ban' and t==enemyteam]
    own_picks=[v for (kind,t,i),v in s['entries'].items() if kind=='pick' and t==ownteam]
    own_roles=s['role_assignments'][ownteam]
    enemy_roles=s['role_assignments'][enemyteam]
    # Plan is derived from actual actions, not stored as a stale duplicate.
    planned=dict(d['champions'])
    for role,champ in list(planned.items()):
        if norm(champ) in used:
            # An own pick of this champion is already fulfilled; an opponent ban/pick blocks it.
            if norm(champ) not in {norm(x) for x in own_picks}:
                alternatives=role_replacements(d,role,used,planned,enemy_picks,names)
                if alternatives:planned[role]=alternatives[0][1]
                else:planned[role]=None
    # Explicit role assignments made during our picks supersede the draft plan.
    overrides=s.setdefault('role_overrides',{})
    for role,name in list(overrides.items()):
        if role not in own_roles and name and norm(name) not in used:planned[role]=name
    for role,name in own_roles.items():planned[role]=name
    # Recheck collision between replacement candidates and already selected champions.
    for role,name in list(planned.items()):
        if name and norm(name) in used and norm(name) not in {norm(x) for x in own_picks}:
            alternatives=role_replacements(d,role,used,planned,enemy_picks,names)
            planned[role]=alternatives[0][1] if alternatives else None
    blocked_roles=[r for r,v in d['champions'].items() if norm(v) in {norm(x) for x in enemy_bans}]
    if blocked_roles:
        st.warning('🚨 Ban adverse sur la composition : '+', '.join(f"{r} — {d['champions'][r]}" for r in blocked_roles))
        st.markdown('### 🔄 Remplacements automatiques par rôle')
        for role in blocked_roles:
            original=d['champions'][role]
            alternatives=role_replacements(d,role,used,planned,enemy_picks,names)
            if norm(original) in {norm(x) for x in own_picks}:
                st.success(f'{role} : {original} est déjà verrouillé pour nous.')
                continue
            if not alternatives:
                st.error(f'{role} : aucune alternative disponible dans le pool local. Élargir le pool ou vérifier les bans.')
                continue
            labels={name:f'{name} — {note}' for _,name,note in alternatives}
            choices=[name for _,name,_ in alternatives]
            default=planned.get(role)
            if default not in choices:default=choices[0]
            choice=st.selectbox(f'{role} : remplacer {original}',choices,index=choices.index(default),format_func=lambda x:labels[x],key=f'replace_{key}_{role}_{s["step"]}')
            if choice!=planned.get(role):
                planned[role]=choice
            if st.button(f'Utiliser {choice} pour {role}',key=f'apply_{key}_{role}_{s["step"]}'):
                overrides[role]=choice
                st.rerun()
            st.caption(f'Suggestion prioritaire : {alternatives[0][1]} — {alternatives[0][2]}')
    st.caption('Les remplacements sont calculés selon le rôle, les champions encore disponibles et les synergies. Ce sont des recommandations qualitatives, pas des winrates en direct.')
    current=SEQUENCE[s['step']] if s['step']<len(SEQUENCE) else None
    a,b,c=st.columns([1,1,1])
    with a:
        secs=st.number_input('Temps par action (secondes)',min_value=10,max_value=120,value=s['seconds'],step=5)
        if secs!=s['seconds']:
            s['seconds']=secs
            if not s['running']:s['remaining']=secs
    with b:
        st.metric('Progression',f"{s['step']} / {len(SEQUENCE)}")
    with c:
        st.metric('Action',f"{current[1]} {current[0]} {current[2]}" if current else 'Terminée')

    @st.fragment(run_every=1)
    def timer():
        if s['running']:
            left=max(0,int(s['remaining']-(time.monotonic()-s['started'])))
            if left==0:
                s['remaining']=0;s['running']=False
        else:left=s['remaining']
        st.metric('⏱️ Chronomètre',f'{left:02d} s',delta='Temps écoulé' if left==0 else None,delta_color='off')
    timer()
    t1,t2,t3=st.columns(3)
    if t1.button('▶️ Démarrer / reprendre',disabled=s['running'] or not current,use_container_width=True):
        s['started']=time.monotonic();s['running']=True;st.rerun()
    if t2.button('⏸️ Pause',disabled=not s['running'],use_container_width=True):
        s['remaining']=max(0,int(s['remaining']-(time.monotonic()-s['started'])));s['running']=False;st.rerun()
    if t3.button('↻ Réinitialiser le timer',use_container_width=True):
        s['running']=False;s['remaining']=s['seconds'];st.rerun()
    st.divider()
    from draft_board import render_board
    from champion_ui import icon_url
    # The board itself is native Streamlit: its player squares are clickable.
    st.markdown('### ⚔️ Draft Room — Clique directement sur le carré actif')
    s.setdefault('active_slot',None)
    board_cols=st.columns([5,1,5],gap='small')
    for team,col in [('B',board_cols[0]),('R',board_cols[2])]:
        with col:
            st.markdown('**🔵 BLUE SIDE**' if team=='B' else '**🔴 RED SIDE**')
            for n in range(1,6):
                slot=('pick',team,n)
                champ=s['entries'].get(slot)
                active=current==slot
                imgcol,buttoncol=st.columns([1,4],gap='small')
                with imgcol:
                    url=icon_url(champ) if champ else None
                    if url:st.image(url,width=44)
                    else:st.markdown('🎮' if active else '▫️')
                with buttoncol:
                    label=f'{"🟡 " if active else ""}{n}. {champ or "CHOISIR CHAMPION" if active else champ or "En attente"}'
                    if st.button(label,key=f'board_pick_{key}_{team}_{n}',use_container_width=True,disabled=not active):
                        s['active_slot']=slot
                        st.rerun()
            st.caption('BANS')
            for n in range(1,6):
                slot=('ban',team,n)
                champ=s['entries'].get(slot)
                active=current==slot
                label=f'{"🟡 " if active else "🚫 "}{n}. {champ or "CHOISIR BAN" if active else champ or "—"}'
                if st.button(label,key=f'board_ban_{key}_{team}_{n}',use_container_width=True,disabled=not active):
                    s['active_slot']=slot
                    st.rerun()
    with board_cols[1]:
        st.markdown('### VS')
        st.caption(f'{s["step"]}/20')
    if current and s.get('active_slot')!=current:
        st.info('Clique sur le carré actif (jaune) pour ouvrir la galerie des champions. Les suggestions sont visibles ci-dessous.')

    with st.expander('📋 Vue texte des picks et bans',expanded=False):
        for team in ('B','R'):
            st.write(('🔵 Blue' if team=='B' else '🔴 Red')+' — Picks : '+', '.join(s['entries'].get(('pick',team,i),'—') for i in range(1,6)))
            st.write('Bans : '+', '.join(s['entries'].get(('ban',team,i),'—') for i in range(1,6)))
    st.markdown('#### 🧠 Recommandations pendant la draft')
    own_bans=[v for (kind,t,i),v in s['entries'].items() if kind=='ban' and t==ownteam]
    opp_bans=[v for (kind,t,i),v in s['entries'].items() if kind=='ban' and t==enemyteam]
    dynamic=rank_candidates(recommend_bans(planned,own_roles,enemy_picks,selected,d.get('bans',[]),enemy_roles,names),mode='ban')
    left_tip,right_tip=st.columns(2)
    with left_tip:
        st.caption('BANS ANTI-COUNTER ENCORE DISPONIBLES')
        if dynamic:
            for rec in dynamic[:3]:
                st.markdown(f'**🚫 {rec["name"]}** · score {rec["score"]:.1f} — menace : {", ".join(rec["targets"])}'+(' · '+rec['stat_note'] if rec.get('stat_note') else ''))
        else: st.caption('Aucune menace supplémentaire identifiée dans les règles locales.')
    with right_tip:
        st.caption('PICKS RECOMMANDÉS ENCORE DISPONIBLES')
        remaining=[f'{rec["role"]}: {rec["name"]}' + (' · '+rec['stat_note'] if rec.get('stat_note') else '') for rec in rank_candidates(recommend_picks(planned,own_roles,selected,names,limit=100),mode='pick')[:5]]
        if remaining:
            for item in remaining:st.markdown('**✓ '+item+'**')
        else:st.caption('Tous les picks planifiés sont verrouillés ou indisponibles.')
    st.divider()
    if current:
        kind,team,number=current
        st.subheader(f"Action suivante : {'🔵 BLUE' if team=='B' else '🔴 RED'} — {kind.upper()} {number}")
        available=[x for x in names if norm(x) not in used]
        our_turn=(team=='B')==(side=='Blue')
        bans_now=rank_candidates(recommend_bans(planned,own_roles,enemy_picks,selected,d.get('bans',[]),enemy_roles,names),mode='ban')
        picks_now=rank_candidates(recommend_picks(planned,own_roles,selected,names,limit=100),mode='pick')
        suggested=[r['name'] for r in bans_now] if kind=='ban' else [r['name'] for r in picks_now]
        # Opponent may pick any available champion. Our picks are filtered by remaining role.
        if our_turn and kind=='pick':
            remaining_roles=open_roles(own_roles)
            st.info('Postes encore libres : '+', '.join(remaining_roles))
            if not remaining_roles:
                st.error('Tous les postes sont déjà verrouillés.')
            advice=advise_roles(remaining_roles,enemy_roles,enemy_picks,planned,selected)
            ordered_roles=[x['role'] for x in advice]
            if advice:
                st.success(f'🎯 Poste conseillé : **{advice[0]["role"]}** — {advice[0]["reason"]}')
                with st.expander('Pourquoi cet ordre de rôles ?'):
                    for item in advice:st.write(f'**{item["role"]}** · {item["reason"]}')
            selected_role=st.selectbox('Poste de notre prochain pick (modifiable)',ordered_roles,key=f'role_{key}_{s["step"]}') if ordered_roles else None
            if selected_role:
                allowed={norm(x) for x in role_candidates(selected_role,names)}
                available=[x for x in available if norm(x) in allowed]
                suggested=[x for x in suggested if norm(x) in allowed]
                st.caption('Catalogue filtré par poste : aucun second TOP/JGL/MID/ADC/SUP possible.')
        else:
            selected_role=None
        if our_turn and kind=='ban':
            st.markdown('**🚫 Bans prioritaires recalculés**')
            for rec in bans_now[:5]:
                st.caption(f"{rec['name']} · {rec['why']} · menace : {', '.join(rec['targets'])}"+(' · '+rec['stat_note'] if rec.get('stat_note') else ''))
        default=next((x for x in suggested if x in available),'') if our_turn else ''
        st.caption('Sélectionne le carré actif au-dessus pour ouvrir le choix de champions à cet emplacement.')
        picker_key=f'gallery_{key}_{s["step"]}'
        if s.get('active_slot')==current:
            st.markdown('### 🎮 Sélection du carré actif')
            choice=gallery_picker('🎮 Champions disponibles — ouvrir la galerie',picker_key,blocked=selected,suggested=suggested,fallback=available,allowed=available,prioritize=our_turn)
        else:
            choice=None
        if default and not choice:
            st.info(f'💡 Pick conseillé selon le plan : **{default}**')
            if st.button(f'Choisir {default}',key=f'default_{key}_{s["step"]}'):
                st.session_state[picker_key+'_selected']=default
                st.rerun()
        if st.button('🔒 Verrouiller et passer au slot suivant',type='primary',disabled=not choice,use_container_width=True):
            if norm(choice) in used:st.error('Champion déjà sélectionné ou banni.')
            elif choice not in available:st.error('Champion non autorisé pour ce poste.')
            else:
                if kind=='pick':
                    if our_turn:
                        if selected_role in own_roles:st.error('Ce poste est déjà occupé.');st.stop()
                        s['role_assignments'][ownteam][selected_role]=choice
                    else:
                        free=open_roles(s['role_assignments'][enemyteam])
                        inferred=assign_role(choice,free)
                        if inferred:s['role_assignments'][enemyteam][inferred]=choice
                s['entries'][current]=choice;s['step']+=1;s['active_slot']=None;s['running']=False;s['remaining']=s['seconds'];st.rerun()
    else:
        st.success('Draft terminée : 10 picks et 10 bans verrouillés.')
    nav1,nav2=st.columns(2)
    if nav1.button('↩️ Annuler la dernière action',disabled=s['step']==0,use_container_width=True):
        s['step']-=1
        s['active_slot']=None
        action=SEQUENCE[s['step']]
        removed=s['entries'].pop(action,None)
        if action[0]=='pick' and removed:
            for role,champ in list(s['role_assignments'][action[1]].items()):
                if norm(champ)==norm(removed):s['role_assignments'][action[1]].pop(role,None)
        s['running']=False;s['remaining']=s['seconds'];st.rerun()
    if nav2.button('🗑️ Nouvelle simulation',use_container_width=True):
        st.session_state[key]={'step':0,'entries':{},'role_assignments':{'B':{},'R':{}},'seconds':s['seconds'],'remaining':s['seconds'],'running':False,'started':0.0};st.rerun()
    st.divider()
    st.subheader('🧠 Counter Analyzer dynamique')
    enemyteam='R' if side=='Blue' else 'B'
    ownteam='B' if side=='Blue' else 'R'
    enemy=[champ for (kind,t,i),champ in s['entries'].items() if kind=='pick' and t==enemyteam]
    ownb=[champ for (kind,t,i),champ in s['entries'].items() if kind=='ban' and t==ownteam]
    oppb=[champ for (kind,t,i),champ in s['entries'].items() if kind=='ban' and t==enemyteam]
    st.write('**Picks adverses révélés :** '+(', '.join(enemy) if enemy else 'Aucun pour le moment'))
    suggestions=rank_candidates(recommend_bans(planned,own_roles,enemy,selected,d.get('bans',[]),enemy_roles,names),mode='ban')
    if suggestions:
        st.markdown('**Bans anti-counter encore disponibles (heuristique de coaching)**')
        for rec in suggestions:
            st.markdown(f'**{rec["name"]}** · {rec["score"]} points — menace contre : {", ".join(rec["targets"])}. {rec["why"]}')
    else:st.info('Aucun counter structurel supplémentaire identifié dans la base de règles.')
    if enemy:
        st.markdown('**Risques liés aux picks adverses déjà verrouillés**')
        for champ in enemy:
            found=next(((n,k,w,t) for n,(k,w,t) in COUNTERS.items() if norm(n)==norm(champ)),None)
            if found:
                n,k,w,t=found
                overlap=[x for x in t if norm(x) in [norm(v) for v in d['champions'].values()]]
                if overlap:st.warning(f'{champ} ({k}) : {w} Menace : {", ".join(overlap)}. Ce champion est déjà pick : impossible de le bannir.')
    st.markdown('**Pivots envisageables sur les slots non verrouillés**')
    ourp=[norm(champ) for (kind,t,i),champ in s['entries'].items() if kind=='pick' and t==ownteam]
    for role,champ in d['champions'].items():
        if role not in own_roles:
            alternatives=role_replacements(d,role,used,planned,enemy,names)
            if alternatives:st.write(f'**{role} — {champ} → {planned.get(role) or chr(63)} :** '+', '.join(x[1] for x in alternatives))
    st.caption('Les suggestions sont des règles de matchup, non des taux de victoire live. Elles excluent tous les champions déjà pick ou ban et les cinq champions prévus dans notre draft.')
    export={'draft':d['id'],'side':side,'adapted_composition':planned,'role_assignments':s['role_assignments'],'sequence':[{'type':k,'team':t,'number':i,'champion':s['entries'].get((k,t,i),'')} for k,t,i in SEQUENCE]}
    st.download_button('⬇️ Exporter la simulation complète',json.dumps(export,ensure_ascii=False,indent=2),file_name=f'{d["id"]}_{side}_draft_pro.json',mime='application/json')
