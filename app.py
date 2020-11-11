import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go

from common import *

app = dash.Dash(__name__)

server = app.server

with open('sample.pgn', 'r') as f:
    pgn = f.read()

hero = 0 # white

games = pgn.split('\n\n\n')[:-1]
nodes = build_tree(games, hero)
data = format_data(nodes)
fig = go.Figure(data)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Label('Lichess Username'),
            dcc.Input(id='username', value='CheckRaiseMate', type='text'),
        ], style={'textAlign': 'left'}, className='flex-item'),

        html.Div([
            html.Label('Color'),
            dcc.RadioItems(
                id='color',
                options=[
                    {'label': 'White', 'value': 'white'},
                    {'label': 'Black', 'value': 'black'},
                ],
                value='white'
            ),
        ], style={'textAlign': 'left'}, className='flex-item'),

    ], className='flex-container'),

    html.Div([
        html.Button('Get games', id='button'),
        dcc.Loading(
            id="loading-1",
            type="default",
            children=dcc.Graph(id='graph', figure=fig)
        ),
    ], style={'textAlign': 'center'}),
])

@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State('username', 'value'), dash.dependencies.State('color', 'value')]
    )
def update_output(n_clicks, username, color):
    if n_clicks is None:
        raise PreventUpdate
    else:
        pgn = get_pgn(username, color, games=100)
        games = pgn.split('\n\n\n')[:-1]
        hero = 0 if color == 'white' else 1
        nodes = build_tree(games, hero)
        data = format_data(nodes)
        fig = go.Figure(data=data)
        fig.update_layout(title_text=f"{username}'s {color} repertoire")

        return fig

app.run_server(debug=True, use_reloader=True)