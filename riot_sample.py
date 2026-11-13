"""Optional real Riot Match-v5 sample. Observational sample, NOT global meta statistics."""
from collections import defaultdict
from urllib.parse import quote
import requests

PLATFORMS={'EUW1':'europe','EUN1':'europe','KR':'asia','NA1':'americas','BR1':'americas','LA1':'americas','LA2':'americas','OC1':'sea','JP1':'asia'}
POSITIONS={'TOP':'TOP','JUNGLE':'JGL','MIDDLE':'MID','BOTTOM':'ADC','UTILITY':'SUP'}

def collect_sample(api_key, riot_ids, platform='EUW1', count=10, max_matches=80):
    """Fetch up to max_matches completed ranked matches for supplied Riot IDs.
    No claim of representative win rates. Raises on auth/rate errors.
    """
    if not api_key.strip(): raise ValueError('Clé API Riot requise')
    if platform not in PLATFORMS: raise ValueError('Région inconnue')
    region=PLATFORMS[platform]
    session=requests.Session()
    session.headers.update({'X-Riot-Token':api_key.strip()})
    def get(url):
        r=session.get(url,timeout=12)
        if r.status_code==429: raise RuntimeError('Limite Riot atteinte (429) : réessayez plus tard')
        if r.status_code in (401,403):raise RuntimeError('Clé Riot invalide ou expirée (401/403)')
        r.raise_for_status()
        return r.json()
    ids=[]
    for raw in riot_ids[:10]:
        if '#' not in raw: continue
        name,tag=raw.rsplit('#',1)
        acct=get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{quote(name,safe="")}/{quote(tag,safe="")}')
        puuid=acct['puuid']
        matches=get(f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{quote(puuid)}/ids?queue=420&count={min(int(count),20)}')
        ids.extend(matches)
    ids=list(dict.fromkeys(ids))[:max_matches]
    stats=defaultdict(lambda:{'games':0,'wins':0})
    loaded=0
    for match_id in ids:
        match=get(f'https://{region}.api.riotgames.com/lol/match/v5/matches/{quote(match_id)}')
        if match.get('info',{}).get('gameMode')!='CLASSIC':continue
        for p in match.get('info',{}).get('participants',[]):
            role=POSITIONS.get(p.get('teamPosition',''))
            champion=p.get('championName')
            if not role or not champion:continue
            row=stats[(champion,role)]
            row['games']+=1
            row['wins']+=int(bool(p.get('win')))
        loaded+=1
    rows=[{'champion':c,'role':r,**values} for (c,r),values in stats.items()]
    return {'source':'Riot Match-v5 — échantillon ciblé (non représentatif)','patch':'mixte (matchs récents)','updated_at':'à la demande','region':platform,'queue':'420','sample_matches':loaded,'rows':rows}
