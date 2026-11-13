"""Pure, testable draft recommendations. Qualitative rules, not live winrates."""
import unicodedata
ROLES=('TOP','JGL','MID','ADC','SUP')
ROLE_POOLS={
'TOP':['K’Sante','Ambessa','Gnar','Rumble','Olaf','Jayce','Ornn','Gwen','Poppy','Camille','Jax','Gragas','Renekton','Malphite','Sion','Fiora','Aatrox','Shen','Kennen'],
'JGL':['Jarvan IV','Vi','Nocturne','Lee Sin','Sejuani','Wukong','Xin Zhao','Poppy','Maokai','Viego','Qiyana','Elise','Nidalee','Trundle','Zac','Olaf','Amumu'],
'MID':['Orianna','Syndra','Ryze','Viktor','Akali','Ahri','Taliyah','Azir','Hwei','Jayce','LeBlanc','Lissandra','Cassiopeia','Galio','Yone','Corki','Zoe'],
'ADC':['Jhin','Ezreal','Kai’Sa','Lucian','Ashe','Varus','Jinx','Aphelios','Xayah','Caitlyn','Sivir','Smolder','Miss Fortune','Zeri','Draven','Twitch','Kog’Maw'],
'SUP':['Nautilus','Renata Glasc','Alistar','Rakan','Lulu','Braum','Karma','Leona','Rell','Bard','Thresh','Milio','Lux','Nami','Poppy','Blitzcrank','Morgana','Janna']}
# Explicit counter relationships: candidate -> threats it counters.
COUNTER_RULES={
'Poppy':{'targets':['Jarvan IV','Vi','Rakan','Nautilus','Lee Sin','Alistar','Camille','Ambessa','Wukong'],'why':'Anti-dash : gêne les entrées de la frontline et les dives.'},
'Renata Glasc':{'targets':['Jarvan IV','Nautilus','Rakan','Rell','Wukong','Amumu','Nocturne'],'why':'Anti-engage : peut retourner un combat groupé.'},
'Olaf':{'targets':['Nautilus','Sejuani','Maokai','Leona','Rell','Jarvan IV'],'why':'Anti-CC : menace les carries derrière la frontline.'},
'Nocturne':{'targets':['Jhin','Jinx','Orianna','Viktor','Varus','Syndra','Aphelios'],'why':'Dive longue portée : punit les carries immobiles.'},
'Braum':{'targets':['Jhin','Ashe','Ezreal','Varus','Lucian'],'why':'Peel et bouclier : limite le follow-up à projectiles.'},
'Xayah':{'targets':['Vi','Jarvan IV','Nautilus','Nocturne','Rakan'],'why':'Anti-dive : peut esquiver le verrouillage initial.'},
'Gwen':{'targets':['K’Sante','Ornn','Sejuani','Maokai','Sion'],'why':'DPS anti-frontline et pression en side.'},
'Cassiopeia':{'targets':['Jarvan IV','Ambessa','Vi','K’Sante','Rakan'],'why':'DPS continu et zone anti-déplacement.'},
'Malphite':{'targets':['Jhin','Jinx','Varus','Jayce','Syndra','Orianna'],'why':'Engage à distance sur les carries peu mobiles.'},
'Lissandra':{'targets':['Akali','Qiyana','Ahri','LeBlanc','Ambessa'],'why':'Contrôle ciblé contre les assassins et flancs.'},
'Morgana':{'targets':['Nautilus','Blitzcrank','Thresh','Leona','Ashe'],'why':'Bouclier anti-CC qui réduit la fiabilité des catches.'},
'Zac':{'targets':['Jayce','Varus','Jhin','Syndra','Karma'],'why':'Engage hors vision contre les compositions poke.'},
'Camille':{'targets':['Jhin','Orianna','Viktor','Ezreal'],'why':'Dive et isolement de carry.'},
'Viktor':{'targets':['Jarvan IV','K’Sante','Nautilus','Jhin'],'why':'Contrôle de zone et DPS prolongé.'},
'Ezreal':{'targets':['Jarvan IV','Nautilus','Sejuani'],'why':'Mobilité contre les engages linéaires.'},
'Draven':{'targets':['Jinx','Aphelios','Smolder','Sivir'],'why':'Pression early contre les botlanes scaling.'},
'Blitzcrank':{'targets':['Jinx','Lulu','Orianna','Aphelios','Jhin'],'why':'Catch menaçant sur carries immobiles.'},
'Janna':{'targets':['Jarvan IV','Rakan','Nautilus','Wukong','Alistar'],'why':'Désengage qui interrompt la séquence d’entrée.'},
'Taliyah':{'targets':['Vi','Jarvan IV','Ambessa','Camille','Rakan'],'why':'Zone anti-dash et contrôle des rotations.'},
}
def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '').replace('’',"'"))
    return ''.join(c for c in s if not unicodedata.combining(c)).casefold().strip()
def canon(s,catalog=()):
    return next((x for x in catalog if norm(x)==norm(s)),s)
def role_candidates(role,catalog=()):
    # Data Dragon lacks reliable positional data: curated role pool, never pretend otherwise.
    known={norm(x) for x in catalog}
    return [canon(x,catalog) for x in ROLE_POOLS[role] if not known or norm(x) in known]
def open_roles(own_assignments):
    return [r for r in ROLES if r not in own_assignments]
def recommend_bans(planned, own_assignments, enemy_picks, all_used, initial_bans=(), enemy_roles=None, catalog=()):
    """Rank enemy counter threats. Exclude our picks/plans, bans, and locked enemy roles."""
    enemy_roles=enemy_roles or {}
    own=list(own_assignments.values())
    current=[own_assignments.get(r,planned.get(r)) for r in ROLES]
    current=[c for c in current if c]
    forbidden={norm(x) for x in list(all_used)+current+own if x}
    locked_enemy_roles=set(enemy_roles.keys())
    initial={norm(x) for x in initial_bans}
    result=[]
    for name,rule in COUNTER_RULES.items():
        if norm(name) in forbidden:continue
        roles=[r for r in ROLES if any(norm(name)==norm(x) for x in ROLE_POOLS[r])]
        if roles and all(r in locked_enemy_roles for r in roles):continue
        hits=[c for c in current if any(norm(c)==norm(t) for t in rule['targets'])]
        if not hits:continue
        score=10*len(hits)+(5 if norm(name) in initial else 0)
        # Prioritize the current, locked composition over merely planned champions.
        score+=4*sum(norm(c) in {norm(v) for v in own} for c in hits)
        result.append({'name':canon(name,catalog),'score':score,'targets':hits,'why':rule['why'],'roles':roles})
    return sorted(result,key=lambda x:(-x['score'],x['name']))
def recommend_picks(planned, own_assignments, used, catalog=(), limit=12):
    """Only one champion per still-open role; never duplicate a role already locked."""
    forbidden={norm(x) for x in used}
    result=[]
    for role in open_roles(own_assignments):
        priority=planned.get(role)
        candidates=[priority]+role_candidates(role,catalog) if priority else role_candidates(role,catalog)
        seen=set()
        for rank,c in enumerate(candidates):
            if not c or norm(c) in seen or norm(c) in forbidden:continue
            seen.add(norm(c))
            result.append({'role':role,'name':canon(c,catalog),'score':100-rank*8,'reason':'Composition prévue' if rank==0 else 'Alternative du même poste'})
    return sorted(result,key=lambda x:-x['score'])[:limit]
def assign_role(champ,available_roles,preferred=None):
    if preferred in available_roles:return preferred
    matches=[r for r in available_roles if any(norm(champ)==norm(c) for c in ROLE_POOLS[r])]
    return matches[0] if len(matches)==1 else None
