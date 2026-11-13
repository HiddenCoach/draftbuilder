"""Searchable champion gallery with Riot Data Dragon icons."""
import html
import streamlit as st
from draft_room_pro import champion_catalog, norm

ROLE_HINTS = {'ALL':'Tous','TOP':'Top','JGL':'Jungle','MID':'Mid','ADC':'ADC','SUP':'Support'}


def icon_url(name):
    version, catalog = champion_catalog()
    found = catalog.get(norm(name))
    return f'https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{found[1]}.png' if found and version else None


def champion_tile(name, size=46):
    url=icon_url(name)
    safe=html.escape(name)
    if url:
        return f'<div class="champ-tile"><img src="{html.escape(url,quote=True)}" width="{size}" height="{size}" loading="lazy" alt="{safe}"><span>{safe}</span></div>'
    return f'<div class="champ-tile"><span>⚔️ {safe}</span></div>'


def gallery_picker(label,key,blocked=(),suggested=(),fallback=(),columns=8,allowed=None,prioritize=False):
    """Riot icon grid inside an expandable dropdown; return chosen champion or None."""
    version,catalog=champion_catalog()
    names=sorted(set(x[0] for x in catalog.values()),key=str.casefold)
    if not names:
        names=sorted(set(fallback)|set(suggested),key=str.casefold)
        st.info('Catalogue Riot temporairement indisponible : sélection locale uniquement.')
    unavailable={norm(x) for x in blocked}
    names=[n for n in names if norm(n) not in unavailable]
    if allowed is not None:
        allowed_set={norm(x) for x in allowed}
        names=[n for n in names if norm(n) in allowed_set]
    if prioritize:
        preferred={norm(x) for x in suggested}
        names.sort(key=lambda n:(norm(n) not in preferred,n.casefold()))
    with st.popover(label,use_container_width=True):
        search=st.text_input('🔎 Rechercher un champion',key=key+'_search',placeholder='Nom du champion…')
        only=st.toggle('Suggestions prioritaires uniquement',key=key+'_suggestions',value=False)
        if only:
            preferred={norm(x) for x in suggested}
            names=[n for n in names if norm(n) in preferred]
        if search:
            names=[n for n in names if norm(search) in norm(n)]
        st.caption(f'{len(names)} champions disponibles · icônes officielles Riot')
        if suggested:
            st.markdown('**⭐ Suggestions prioritaires :** '+', '.join(x for x in suggested[:6] if norm(x) in {norm(y) for y in names}))
        if not names:
            st.warning('Aucun champion correspondant.')
        for start in range(0,len(names),columns):
            cols=st.columns(columns,gap='small')
            for j,name in enumerate(names[start:start+columns]):
                with cols[j]:
                    url=icon_url(name)
                    if url: st.image(url,use_container_width=True)
                    else: st.write('⚔️')
                    if st.button(name,key=f'{key}_champ_{norm(name)}',use_container_width=True,help=f'Sélectionner {name}'):
                        st.session_state[key+'_selected']=name
                        st.rerun()
    chosen=st.session_state.get(key+'_selected')
    if chosen and norm(chosen) in unavailable:
        st.session_state.pop(key+'_selected',None)
        chosen=None
    if chosen:
        st.markdown(champion_tile(chosen,42),unsafe_allow_html=True)
    return chosen


def visual_roster(champions):
    cols=st.columns(len(champions))
    for i,(role,name) in enumerate(champions.items()):
        with cols[i]:
            st.caption(role)
            url=icon_url(name)
            if url:st.image(url,width=70)
            st.markdown(f'**{name}**')
