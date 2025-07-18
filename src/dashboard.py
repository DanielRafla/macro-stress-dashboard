import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px

# ─────────── Load data ───────────
macro = pd.read_csv(
    "data/processed/macro_data.csv", index_col=0, parse_dates=True
)
mc = pd.read_parquet("data/processed/mc_paths.parquet")

# ─────────── Historical yield curve figure ───────────
yield_history_fig = px.line(
    macro,
    x=macro.index,
    y=["2Y_Treasury", "10Y_Treasury"],
    title="Historical 2Y vs 10Y Treasury Yields",
    labels={
        "2Y_Treasury": "2Y",
        "10Y_Treasury": "10Y",
        "value": "Yield (%)",
        "index": "Date",
    },
)
yield_history_fig.update_layout(legend_title_text="Tenor")

# ─────────── Options ───────────
scenario_options = [
    {"label": s, "value": s}
    for s in mc.index.get_level_values(0).unique()
]
metric_options = [
    {"label": "Fed Funds Rate", "value": "FedFunds"},
    {"label": "Credit Spread",  "value": "HY_OAS"},
    {"label": "Tech ETF",       "value": "Technology"},
]

# ─────────── Monte Carlo time series helper ───────────
def _make_ts_fig(scenario, metric, shock_bp):
    df_base = mc.xs('base')[metric]
    df_up   = mc.xs('up')[metric]
    df_down = mc.xs('down')[metric]
    scale = shock_bp / 250.0

    if scenario == 'up':
        df_scn = df_base + (df_up - df_base) * scale
    elif scenario == 'down':
        df_scn = df_base + (df_down - df_base) * scale
    else:
        df_scn = df_base.copy()

    fig = go.Figure()
    # Base scenario line (dashed) in red
    fig.add_trace(
        go.Scatter(
            x=df_base.index,
            y=df_base,
            name='base',
            line=dict(color='red', dash='dash'),
            opacity=0.6,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_scn.index,
            y=df_scn,
            name=f"{scenario} shock ({shock_bp} bp)",
            line=dict(color='steelblue')
        )
    )
    fig.update_layout(
        title=f"{metric} under '{scenario}' shock ({shock_bp} bp)",
        xaxis_title='Date',
        yaxis_title=metric,
        legend_title_text='Scenario'
    )
    return fig

# ─────────── Monte Carlo snapshot helper ───────────
def _make_snap_fig(scenario, shock_bp):
    valid = macro[["2Y_Treasury", "10Y_Treasury"]].dropna()
    last_date = valid.index.max()
    base_vals = valid.loc[last_date]
    scale = shock_bp / 250.0
    if scenario == 'up':
        scn_vals = base_vals + base_vals * scale * 0.2
    elif scenario == 'down':
        scn_vals = base_vals - base_vals * scale * 0.2
    else:
        scn_vals = base_vals.copy()

    labels = ['2Y', '10Y']
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[base_vals['2Y_Treasury'], base_vals['10Y_Treasury']],
        y=labels, orientation='h', marker_color='lightgrey', name='base'
    ))
    fig.add_trace(go.Bar(
        x=[scn_vals['2Y_Treasury'], scn_vals['10Y_Treasury']],
        y=labels, orientation='h', marker_color='steelblue', name=f"{scenario} shock ({shock_bp} bp)"
    ))
    fig.update_layout(
        title_text=f"Yield Curve Snapshot ({last_date.date()})",
        xaxis_title="Yield (%)",
        yaxis_title="Tenor",
        legend_title_text="Scenario",
        xaxis=dict(range=[0, float(base_vals.max()) * 1.5])
    )
    text = f"2Y: {scn_vals['2Y_Treasury']:.2f}%, 10Y: {scn_vals['10Y_Treasury']:.2f}% (as of {last_date.date()})"
    return fig, text

# ─────────── Dash App Setup ───────────
app = dash.Dash(__name__)
app.title = 'Macro-Stress Dashboard'

app.layout = html.Div([
    html.H1('Macro-Stress Dashboard'),

    html.Div([
        html.Label('Scenario:'),
        dcc.Dropdown(
            id='scenario', options=scenario_options, value='base'
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),

    html.Div([
        html.Label('Metric:'),
        dcc.Dropdown(
            id='metric', options=metric_options, value='FedFunds'
        ),
    ], style={'width': '30%', 'display': 'inline-block'}),

    html.Div([
        html.Label('Shock Size (bp):'),
        dcc.Slider(
            id='shock-size',
            min=0, max=300, step=10, value=0,
            marks={i: str(i) for i in range(0, 301, 50)}
        ),
        html.Div(id='shock-output', style={'marginTop': '10px'})
    ], style={'width': '50%', 'margin': '20px 0'}),

    dcc.Graph(id='time-series-chart'),

    html.Hr(),

    html.H3('Historical Yield Curve'),
    dcc.Graph(figure=yield_history_fig),

    html.Hr(),

    html.H3('Yield Curve Snapshot'),
    html.Pre(id='snapshot-text'),
    dcc.Graph(id='snapshot-graph', style={'width': '50%'}),
])

# ─────────── Callbacks ───────────
@app.callback(
    Output('time-series-chart', 'figure'),
    Input('scenario', 'value'),
    Input('metric', 'value'),
    Input('shock-size', 'value')
)
def update_time_series(scenario, metric, shock_bp):
    return _make_ts_fig(scenario, metric, shock_bp)

@app.callback(
    Output('snapshot-graph', 'figure'),
    Output('snapshot-text', 'children'),
    Input('scenario', 'value'),
    Input('shock-size', 'value')
)
def update_snapshot(scenario, shock_bp):
    fig, text = _make_snap_fig(scenario, shock_bp)
    return fig, text

@app.callback(
    Output('shock-output', 'children'),
    Input('shock-size', 'value')
)
def update_shock_output(shock_bp):
    return f'Current shock size: {shock_bp} bp'

# ─────────── Run Server ───────────
if __name__ == '__main__':
    app.run()

