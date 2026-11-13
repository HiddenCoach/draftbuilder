"""Visual LoL-style draft board; all data is escaped and derived from locked slots."""
import html
import streamlit as st

BOARD_CSS = """
<style>
.draft-arena{background:linear-gradient(125deg,#10253b,#0b1527 48%,#301d2b);border:1px solid #38506a;border-radius:18px;padding:18px;margin:8px 0 16px;box-shadow:0 16px 40px #0003}
.arena-header{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px;color:#b7c8d9;font-size:12px;letter-spacing:1.4px;font-weight:800}
.arena-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(120px,.6fr) minmax(0,1fr);gap:14px}
.team-title{font-size:15px;font-weight:800;letter-spacing:1px;margin-bottom:9px}.blue-title{color:#70c8ff}.red-title{color:#ff929a;text-align:right}
.pick-line{display:flex;align-items:center;gap:10px;min-height:61px;background:#15283d;border:1px solid #294661;border-radius:10px;padding:6px 10px;margin:5px 0}
.red-team .pick-line{flex-direction:row-reverse;background:#30202e;border-color:#603848}
.pick-avatar{width:48px;height:48px;flex:none;border-radius:7px;border:1px solid #4a6681;object-fit:cover;background:#233449}
.pick-empty{display:flex;align-items:center;justify-content:center;color:#637b93;font-weight:800;font-size:18px}
.pick-info{min-width:0;flex:1}.pick-slot{font-size:10px;color:#8da3b9;font-weight:700;letter-spacing:.7px}.pick-name{font-size:14px;font-weight:750;color:#e7f1fa;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.red-team .pick-info{text-align:right}.pick-line.is-next{border-color:#e6b95c;box-shadow:0 0 0 1px #e6b95c66}
.arena-middle{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:12px}.arena-vs{font-size:27px;font-weight:900;color:#d5b978;letter-spacing:2px}.arena-phase{font-size:11px;color:#c2d2e0}.arena-progress{width:100%;height:5px;background:#344354;border-radius:10px;overflow:hidden}.arena-progress>div{height:100%;background:#d8b46c}
.ban-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.ban-card{position:relative;display:flex;align-items:center;gap:6px;padding:4px 6px;background:#111d2d;border:1px solid #344b63;border-radius:7px;min-width:0}.ban-card img{width:30px;height:30px;object-fit:cover;border-radius:4px;filter:grayscale(.9) brightness(.7)}.ban-card .ban-x{position:absolute;top:3px;left:13px;color:#ff666d;font-weight:900;font-size:24px;line-height:28px;text-shadow:0 1px 3px #000}.ban-card span:last-child{font-size:11px;color:#c5d2df}.ban-empty{font-size:11px;color:#627c96}
@media(max-width:760px){.draft-arena{padding:10px}.arena-grid{grid-template-columns:minmax(0,1fr) 45px minmax(0,1fr);gap:5px}.pick-line{padding:4px;gap:4px;min-height:46px}.pick-avatar{width:33px;height:33px}.pick-name{font-size:11px}.pick-slot{font-size:9px}.arena-vs{font-size:15px}.arena-phase{font-size:9px}.ban-card span:last-child{display:none}.team-title{font-size:11px}}
</style>
"""

def _e(value):
    return html.escape(str(value), quote=True)

def render_board(sequence, entries, icon_url, step, side):
    """Render team picks and crossed-out bans without any mutable client state."""
    st.markdown(BOARD_CSS, unsafe_allow_html=True)
    current=sequence[step] if step < len(sequence) else None
    def team(team):
        name='BLUE' if team=='B' else 'RED'
        cls='blue-team' if team=='B' else 'red-team'
        rows=[]
        for slot in range(1,6):
            champ=entries.get(('pick',team,slot))
            active=current==('pick',team,slot)
            img=f'<img class="pick-avatar" src="{_e(icon_url(champ))}" alt="{_e(champ)}">' if champ and icon_url(champ) else '<div class="pick-avatar pick-empty">?</div>'
            rows.append(f'<div class="pick-line {"is-next" if active else ""}">{img}<div class="pick-info"><div class="pick-slot">PICK {slot}</div><div class="pick-name">{_e(champ or "En attente")}</div></div></div>')
        bans=[]
        for slot in range(1,6):
            champ=entries.get(('ban',team,slot))
            if champ:
                url=icon_url(champ)
                avatar=f'<img src="{_e(url)}" alt="{_e(champ)}">' if url else ''
                bans.append(f'<div class="ban-card">{avatar}<span class="ban-x">×</span><span>{_e(champ)}</span></div>')
            else:
                bans.append('<div class="ban-card ban-empty">—</div>')
        return f'<div class="{cls}"><div class="team-title {"blue-title" if team=="B" else "red-title"}">{name} {"• NOTRE ÉQUIPE" if (team=="B")== (side=="Blue") else "• ADVERSAIRE"}</div>{"".join(rows)}<div class="ban-list">{"".join(bans)}</div></div>'
    phase='Draft terminée' if current is None else f'{"BAN" if current[0]=="ban" else "PICK"} {current[2]} • {"BLUE" if current[1]=="B" else "RED"}'
    center=f'<div class="arena-middle"><div class="arena-vs">VS</div><div class="arena-phase">{_e(phase)}</div><div class="arena-progress"><div style="width:{100*step/len(sequence):.0f}%"></div></div><div class="arena-phase">{step}/{len(sequence)} actions</div></div>'
    st.markdown(f'<div class="draft-arena"><div class="arena-header"><span>⚔ DRAFT ROOM • COMPÉTITION</span><span>10 PICKS / 10 BANS</span></div><div class="arena-grid">{team("B")}{center}{team("R")}</div></div>',unsafe_allow_html=True)
