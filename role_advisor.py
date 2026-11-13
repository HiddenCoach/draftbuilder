"""Explainable draft order advisor; heuristic, not verified matchup winrates."""
from draft_intelligence import ROLES, ROLE_POOLS, COUNTER_RULES, norm

BLIND={'TOP':1,'JGL':4,'MID':2,'ADC':3,'SUP':4}

def advise_roles(open_own, enemy_roles, enemy_picks, planned, used):
    """Rank open roles: respond to enemy role reveals, protect counterpick roles."""
    out=[]
    used_norm={norm(x) for x in used}
    for role in open_own:
        planned_champ=planned.get(role)
        score=BLIND[role]*10
        reasons=[]
        if role in enemy_roles:
            score+=40
            reasons.append(f"Poste adverse révélé : {enemy_roles[role]}; possibilité d'adapter le matchup")
        else:
            if role=='TOP':
                score-=25
                reasons.append('Conserver le counterpick TOP si le matchup adverse est inconnu')
            elif role=='MID':
                score-=12
                reasons.append('MID non révélé : éviter un blind exposé si possible')
            else:
                reasons.append('Poste relativement facile à sécuriser en première rotation')
        if planned_champ and norm(planned_champ) in used_norm:
            score-=10
            reasons.append('Champion prévu indisponible : prévoir un pivot')
        for enemy in enemy_picks:
            if any(norm(enemy)==norm(c) for c in ROLE_POOLS.get(role,[])) and role not in enemy_roles:
                reasons.append('Un pick adverse pourrait être flex sur ce poste')
                break
        out.append({'role':role,'score':score,'reason':' · '.join(reasons)})
    return sorted(out,key=lambda x:(-x['score'],ROLES.index(x['role'])))
