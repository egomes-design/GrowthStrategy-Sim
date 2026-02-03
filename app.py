
import random
import time
import streamlit as st

st.set_page_config(page_title='Growth Strategy Simulation (Ansoff-based)', layout='wide')

# ----------------------------
# Game content (MBA-friendly)
# ----------------------------
MOVE_CATALOG = {
    'A': {
        'name': 'Deepen the core',
        'desc': 'Execution inside today’s core business: win rate, retention, pricing/packaging, delivery, cost, reliability.'
    },
    'B': {
        'name': 'Expand the footprint',
        'desc': 'Take the current offer into new segments/geographies/channels. Often looks easy, usually hides channel/regulatory complexity.'
    },
    'C': {
        'name': 'Build the next offering',
        'desc': 'New or materially improved offerings for current customers: new features, software layers, energy efficiency, automation, services.'
    },
    'D': {
        'name': 'Enter a new arena',
        'desc': 'New customers and new economics: enterprise solutions, adjacent industries, licensing models, managed services, platforms.'
    }
}

SHOCK_CARDS = [
    {
        'title': 'Operator capex tightens',
        'text': 'For 2 quarters, carrier customers slow purchasing and push discounts.',
        'impact': {'Share Position': -1, 'Growth': -2, 'Cash Health': -1},
        'duration': 2,
        'tag': 'capex'
    },
    {
        'title': 'Energy costs spike',
        'text': 'Customers prioritize energy efficiency and opex reduction.',
        'impact': {'Optionality': +1},
        'duration': 1,
        'tag': 'energy'
    },
    {
        'title': 'Security scrutiny increases',
        'text': 'Approvals slow and compliance requirements rise in multiple countries/verticals.',
        'impact': {'Risk Events': +1},
        'duration': 1,
        'tag': 'reg'
    },
    {
        'title': 'Competitor starts a price war',
        'text': 'A major rival undercuts pricing in bids; your win-rate is challenged.',
        'impact': {'Share Position': -2, 'Cash Health': -1},
        'duration': 1,
        'tag': 'price'
    },
    {
        'title': 'Enterprise demand shifts to outcomes',
        'text': 'Buyers want outcome-based contracts and service-level guarantees.',
        'impact': {'Growth': +1, 'Risk Events': +1},
        'duration': 1,
        'tag': 'sla'
    },
    {
        'title': 'Partners consolidate',
        'text': 'Systems integrators become more powerful gatekeepers.',
        'impact': {'Growth': +1},
        'duration': 1,
        'tag': 'channel'
    },
    {
        'title': 'Supply chain constraint',
        'text': 'Specialized components are delayed; delivery reliability suffers.',
        'impact': {'Cash Health': -1, 'Risk Events': +1},
        'duration': 1,
        'tag': 'supply'
    },
    {
        'title': 'AI ops accelerates',
        'text': 'AI-assisted operations gains momentum; software attach becomes easier.',
        'impact': {'Optionality': +2},
        'duration': 1,
        'tag': 'ai'
    },
    {
        'title': 'Multi-year anchor deal',
        'text': 'A large customer offers a multi-year deal, but requires tough SLAs.',
        'impact': {'Growth': +2, 'Risk Events': +1},
        'duration': 1,
        'tag': 'anchor'
    },
    {
        'title': 'New industrial safety regulation',
        'text': 'Compliance burden rises in industrial connectivity deployments.',
        'impact': {'Risk Events': +2},
        'duration': 1,
        'tag': 'safety'
    }
]

# ----------------------------
# Engine
# ----------------------------
METRICS = ['Share Position', 'Growth', 'Cash Health', 'Optionality', 'Risk Events']


def clamp(val, lo=0, hi=25):
    return max(lo, min(hi, val))


def init_game(team_count=4, seed=None):
    if seed is None:
        seed = int(time.time()) % 100000
    rnd = random.Random(seed)

    teams = []
    for i in range(team_count):
        teams.append({
            'id': i + 1,
            'name': 'Team ' + str(i + 1),
            'm': {
                'Share Position': 12,
                'Growth': 12,
                'Cash Health': 12,
                'Optionality': 12,
                'Risk Events': 0
            },
            'cap': {
                'Execution Resilience': 4,
                'Innovation Engine': 4,
                'Partner Ecosystem': 3,
                'Risk Management': 3
            },
            'history': []
        })

    state = {
        'seed': seed,
        'rnd_state': rnd.getstate(),
        'quarter': 1,
        'teams': teams,
        'active_shocks': [],
        'shock_log': [],
        'move_log': []
    }
    return state


def rnd_from_state(state):
    rnd = random.Random()
    rnd.setstate(state['rnd_state'])
    return rnd


def save_rnd_state(state, rnd):
    state['rnd_state'] = rnd.getstate()


def draw_shocks(state, n=1):
    rnd = rnd_from_state(state)
    choices = rnd.sample(SHOCK_CARDS, k=min(n, len(SHOCK_CARDS)))
    save_rnd_state(state, rnd)

    for c in choices:
        active = dict(c)
        active['remaining'] = c.get('duration', 1)
        state['active_shocks'].append(active)
        state['shock_log'].append({'quarter': state['quarter'], 'title': c['title'], 'text': c['text']})


def apply_shocks_to_team(team, active_shocks):
    delta = {k: 0 for k in METRICS}
    for s in active_shocks:
        imp = s.get('impact', {})
        for k, v in imp.items():
            if k in delta:
                delta[k] += v
    for k in ['Share Position', 'Growth', 'Cash Health', 'Optionality']:
        team['m'][k] = clamp(team['m'][k] + delta[k])
    team['m']['Risk Events'] = max(0, team['m']['Risk Events'] + delta['Risk Events'])
    return delta


def apply_moves(team, alloc):
    # alloc dict: A,B,C,D each 0-10; assumes sum==10
    a = alloc.get('A', 0)
    b = alloc.get('B', 0)
    c = alloc.get('C', 0)
    d = alloc.get('D', 0)

    cap = team['cap']

    # Base effects
    team['m']['Share Position'] = clamp(team['m']['Share Position'] + int(round(0.35 * a + 0.15 * c)))
    team['m']['Growth'] = clamp(team['m']['Growth'] + int(round(0.15 * a + 0.35 * b + 0.25 * c + 0.45 * d)))
    team['m']['Cash Health'] = clamp(team['m']['Cash Health'] + int(round(0.30 * a - 0.10 * b - 0.25 * c - 0.35 * d)))
    team['m']['Optionality'] = clamp(team['m']['Optionality'] + int(round(0.05 * a + 0.15 * b + 0.35 * c + 0.55 * d)))

    # Capability learning
    cap['Execution Resilience'] = clamp(cap['Execution Resilience'] + 0.20 * a + 0.10 * b, 0, 10)
    cap['Innovation Engine'] = clamp(cap['Innovation Engine'] + 0.25 * c + 0.10 * d, 0, 10)
    cap['Partner Ecosystem'] = clamp(cap['Partner Ecosystem'] + 0.20 * b + 0.25 * d, 0, 10)
    cap['Risk Management'] = clamp(cap['Risk Management'] + 0.10 * a + 0.15 * d, 0, 10)

    # Break points (risk penalties)
    risk_add = 0
    if d >= 4 and cap['Risk Management'] < 4:
        risk_add += 1
    if b >= 4 and cap['Partner Ecosystem'] < 4:
        risk_add += 1
    if c >= 4 and cap['Innovation Engine'] < 4:
        risk_add += 1
    if a <= 1 and team['m']['Cash Health'] < 8:
        risk_add += 1

    team['m']['Risk Events'] = max(0, team['m']['Risk Events'] + risk_add)

    return risk_add


def end_of_quarter(state, team_allocs):
    # Draw shocks for the quarter
    draw_shocks(state, n=1)

    # Apply to each team
    for t in state['teams']:
        alloc = team_allocs.get(t['id'], {'A': 0, 'B': 0, 'C': 0, 'D': 0})
        move_risk = apply_moves(t, alloc)
        shock_delta = apply_shocks_to_team(t, state['active_shocks'])

        t['history'].append({
            'quarter': state['quarter'],
            'alloc': alloc,
            'move_risk': move_risk,
            'shock_delta': shock_delta,
            'metrics': dict(t['m']),
            'cap': dict(t['cap'])
        })

        state['move_log'].append({'quarter': state['quarter'], 'team': t['name'], 'alloc': alloc, 'move_risk': move_risk})

    # Decrement shock durations
    new_active = []
    for s in state['active_shocks']:
        s['remaining'] = s['remaining'] - 1
        if s['remaining'] > 0:
            new_active.append(s)
    state['active_shocks'] = new_active

    state['quarter'] += 1


def score_team(team):
    m = team['m']
    # Risk subtractor, but cap at 25 so one bad year doesn't dominate
    risk_pen = min(25, 3 * m['Risk Events'])
    return {
        'Team': team['name'],
        'Share Position': m['Share Position'],
        'Growth': m['Growth'],
        'Cash Health': m['Cash Health'],
        'Optionality': m['Optionality'],
        'Risk Events': m['Risk Events'],
        'Balanced Score': m['Share Position'] + m['Growth'] + m['Cash Health'] + m['Optionality'] - risk_pen
    }


# ----------------------------
# UI
# ----------------------------
st.title('Growth Strategy Simulation (Ansoff-based)')
st.caption('MBA classroom simulation. Teams allocate a fixed budget across four move types each quarter. The game reveals execution break points under uncertainty.')

if 'game' not in st.session_state:
    st.session_state.game = init_game(team_count=4)

state = st.session_state.game

with st.sidebar:
    st.header('Game control')
    team_count = st.number_input('Number of teams', min_value=2, max_value=10, value=len(state['teams']), step=1)
    shock_info = st.checkbox('Show shock details to players (facilitator choice)', value=True)
    max_quarters = st.number_input('Number of quarters', min_value=4, max_value=12, value=8, step=1)

    if st.button('Reset game'):
        st.session_state.game = init_game(team_count=int(team_count))
        st.rerun()

    st.divider()
    st.write('Seed')
    st.code(str(state['seed']))

colA, colB = st.columns([2, 1])
with colA:
    st.subheader('Current quarter: Q' + str(state['quarter']) + ' of ' + str(int(max_quarters)))

with colB:
    if state['quarter'] > int(max_quarters):
        st.success('Game complete')

st.divider()

st.markdown('#### Teams allocate 10 points per quarter')
st.write('Each team must allocate 10 points across the four move types. Point allocations drive outcomes and capability learning; concentrated bets can create break-point risk.')

team_allocs = {}

for t in state['teams']:
    st.markdown('### ' + t['name'])
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 2])
    with c1:
        a = st.slider('A', 0, 10, 3, key='A_' + str(t['id']))
        st.caption(MOVE_CATALOG['A']['name'])
    with c2:
        b = st.slider('B', 0, 10, 2, key='B_' + str(t['id']))
        st.caption(MOVE_CATALOG['B']['name'])
    with c3:
        c = st.slider('C', 0, 10, 3, key='C_' + str(t['id']))
        st.caption(MOVE_CATALOG['C']['name'])
    with c4:
        d = st.slider('D', 0, 10, 2, key='D_' + str(t['id']))
        st.caption(MOVE_CATALOG['D']['name'])
    with c5:
        total = a + b + c + d
        st.metric('Total', str(total), help='Must equal 10 to submit')
        st.write(MOVE_CATALOG['A']['desc'])
        st.write(MOVE_CATALOG['B']['desc'])
        st.write(MOVE_CATALOG['C']['desc'])
        st.write(MOVE_CATALOG['D']['desc'])

    team_allocs[t['id']] = {'A': int(a), 'B': int(b), 'C': int(c), 'D': int(d)}

st.divider()

can_advance = True
for tid, alloc in team_allocs.items():
    if alloc['A'] + alloc['B'] + alloc['C'] + alloc['D'] != 10:
        can_advance = False

btn_col1, btn_col2 = st.columns([1, 3])
with btn_col1:
    advance = st.button('Submit and advance quarter', disabled=(not can_advance) or state['quarter'] > int(max_quarters))

with btn_col2:
    if not can_advance:
        st.warning('All teams must allocate exactly 10 points before you can advance.')

if advance:
    end_of_quarter(state, team_allocs)
    st.rerun()

# Show shocks
st.markdown('## Quarter events')
if len(state['shock_log']) == 0:
    st.info('No events yet. Submit allocations to start Q1.')
else:
    last_q = state['shock_log'][-1]['quarter']
    last_events = [s for s in state['shock_log'] if s['quarter'] == last_q]
    if shock_info:
        for ev in last_events:
            st.markdown('**' + ev['title'] + '**')
            st.write(ev['text'])
    else:
        st.write('Facilitator has hidden event details.')

# Leaderboard
st.markdown('## Leaderboard')
rows = [score_team(t) for t in state['teams']]
rows_sorted = sorted(rows, key=lambda r: r['Balanced Score'], reverse=True)
st.dataframe(rows_sorted, use_container_width=True)

# History charts
st.markdown('## Trends')
import pandas as pd

hist_rows = []
for t in state['teams']:
    for h in t['history']:
        hist_rows.append({
            'Team': t['name'],
            'Quarter': h['quarter'],
            'Share Position': h['metrics']['Share Position'],
            'Growth': h['metrics']['Growth'],
            'Cash Health': h['metrics']['Cash Health'],
            'Optionality': h['metrics']['Optionality'],
            'Risk Events': h['metrics']['Risk Events']
        })

if len(hist_rows) > 0:
    hist_df = pd.DataFrame(hist_rows)
    metric_choice = st.selectbox('Metric', ['Share Position', 'Growth', 'Cash Health', 'Optionality', 'Risk Events'])
    chart_df = hist_df.pivot_table(index='Quarter', columns='Team', values=metric_choice, aggfunc='max').sort_index()
    st.line_chart(chart_df)

# Facilitator notes
with st.expander('Facilitator controls and notes'):
    st.write('Tip: Hide shock details if you want teams to infer what happened from results. Reveal shocks to emphasize environmental uncertainty.')
    st.write('Debrief: After the game, ask teams to map A/B/C/D to the Ansoff matrix and discuss where break points appeared (sales motion, partners, compliance, SLA ops, capital intensity).')
