import functools
import itertools
import numpy as np
import plotly.graph_objects as go
import requests

from datetime import datetime

def get_points(result, hero):
    s = result.split('-')[hero]
    if s == '0':
        return 0
    elif s == '1':
        return 1
    elif s=='1/2':
        return .5
    
def score2color(score):
    r = (1 - score) * 255
    g = score * 255
    return f'rgb({r},{g},0)'

color_codes = ('#000000', '#FFFFFF')

@functools.lru_cache
def get_pgn(username, color, token=None, perfType='blitz', games=10):
    params = dict(
        color = color,
        perfType = perfType,
        max = games
    )
    headers = {}
    if token is not None:
        headers['Authorization'] = 'Bearer ' + token
    r = requests.get(f'https://lichess.org/api/games/user/{username}', params=params, headers=headers)
    pgn = r.text
    
    return pgn

class Node:
    idx_generator = itertools.count(-1)
    
    def __init__(self, parent, move):
        self.idx = next(self.idx_generator)
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.points = 0
        self.color = 0 if parent is None else 1 - parent.color
        self.depth = self.parent.depth + 1 if parent is not None else 0
    
    def step(self, move):
        # see if it already exists
        for child in self.children:
            if child.move == move:
                return child
            
        # if not, create a new one
        node = Node(self, move)
        self.children.append(node)
        return node
    
    def __repr__(self):
        return f'{self.color}: {self.move} ({self.visits})'
    
    def score(self):
        return self.points / self.visits
    
    def priority(self):
        return self.visits * (1 - self.score())
    
    def game_string(self):
        moves = []
        node = self
        while node.move != 'root':
            moves.append(node.move)
            node = node.parent
        moves.reverse()
        with_nums = []
        for i, move in enumerate(moves):
            if i%2 == 0:
                with_nums.append(f'{i//2+1}.')
            with_nums.append(move)
        return ' '.join(with_nums)
    
def build_tree(games, hero, max_depth=4):
    Node.idx_generator = itertools.count(-1) # reset index

    nodes = []

    root = Node(None, 'root')

    for game in games:
        info, moves = game.split('\n\n')
        tokens = moves.split()
        result = tokens.pop()
        points = get_points(result, hero)
        moves = [t for t in tokens if not t[0].isnumeric()]
        node = root
        for move in moves[:max_depth]:
            node = node.step(move)
            node.visits += 1
            node.points += points
            if node not in nodes: nodes.append(node)
                
    return nodes

def format_data(nodes):
    label, color_node, source, target, value, color_link, customdata = [], [], [], [], [], [], []

    for node in nodes:
        label.append(node.move)
        color_node.append(color_codes[node.color])
        customdata.append([node.game_string(), node.score() * 100])
        if node.parent.move != 'root':
            source.append(node.parent.idx)
            target.append(node.idx)
            value.append(node.visits)
            color_link.append(score2color(node.score()))
            
    node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label = label,
        color = color_node,
        customdata = customdata,
        hovertemplate = "%{customdata[0]}<br />You scored %{customdata[1]:.0f}% in %{value:.f} games<extra></extra>"
    )
    
    link = dict(
        source = source,
        target = target,
        value = value,
        color = color_link,
        hovertemplate = "%{target.label}<br />%{value:.f} of %{source.value:.f} games<extra></extra>"
    )
    
    data = go.Sankey(node=node, link=link)
    
    return data