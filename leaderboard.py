import chess
import chess.pgn
import tqdm
import math
from datetime import datetime
import json


bar = tqdm.tqdm(10)

def escore(elo): # expected score
    return 1/(1+10**(elo/400))

def adjust(timecontrol):
    time, inc = timecontrol.split('+')
    time = int(time)
    inc = int(inc)
    
    return 150*math.log(time + math.log(inc+1)*150)-876

def k_tresh(games):
    tresh = [20, 100]
    K = [40, 20, 10]
    for i in range(len(tresh)):
        if games > tresh[i]:
            continue
        else:
            return K[i]
    return K[i]

def inactivity_malus(lead):
    for player in lead.keys():
        lead[player]['rating'] -= 10
        if lead[player]['rating'] < 1600: # floor
            lead[player]['rating'] = 1600
    return lead


malus_date = 1400000000 # for inactivity malus

K = 40

fi = open('lichess_LeelaQueenOdds_2024-10-31.pgn', 'r')

game = chess.pgn.read_game(fi)

lead = {}
s = {'1-0': 0, '1/2-1/2': 0.5, '0-1': 1}

games = []

while game != None:
    bar.update(1)
    games.append(game)
    game = chess.pgn.read_game(fi)


for game in games[-1::-1]:
    bar.update(1)

    if game.headers['Black'] == 'LeelaQueenOdds':
        player_color = 'White'
        leela_elo = 1900
    else:
        player_color = 'Black'
        leela_elo = 1950
    
    player = game.headers[player_color]
    if player not in lead.keys():
        lead[player] = {
            'rating': 1600,
            'games': 0,
            'last_game': None,
            'BOT': False}
    
    r = s[game.headers['Result']]
    if player_color == 'White':
        r = 1-r
    
    leela_elo -= adjust(game.headers['TimeControl'])
    
    K = k_tresh(lead[player]['games'])
    adj = (r - escore(leela_elo - lead[player]['rating'])) * K
    
    lead[player]['rating'] += adj
    
    if datetime.strptime(game.headers['UTCDate'], "%Y.%m.%d").timestamp()*1000 - malus_date >= 86400*7*1000:
        lead = inactivity_malus(lead)
        malus_date = datetime.strptime(game.headers['UTCDate'], "%Y.%m.%d").timestamp()*1000
        
    
    if lead[player]['rating'] < 1600: # floor
        lead[player]['rating'] = 1600
    lead[player]['games'] += 1
    lead[player]['last_game'] = game.headers['UTCDate']
    
        
    
lead['metadata'] = {
    'rating': 0,
    'date': int(datetime(2024, 11, 1).timestamp()*1000),
    'malus_date': malus_date,
    'prevlinks': []}


#%%

# adding reference

time_control = ['1+0', '1+1', '3+0', '3+2', '5+3', '10+5', '15+10']

baseline = 2150

for tc in time_control:
    t, inc = tc.split('+')
    lead['LeelaQueenOdds as white ' + tc + ' (Reference)'] = {
        'rating': baseline - adjust(str(int(t)*60)+'+'+inc),
        'games': 0,
        'last_game': None,
        'BOT': True}
    
    lead['LeelaQueenOdds as black ' + tc + ' (Reference)'] = {
        'rating': baseline - adjust(str(int(t)*60)+'+'+inc) - 50,
        'games': 0,
        'last_game': None,
        'BOT': True}



#%%

lea = dict(sorted(lead.items(),
                  key = lambda item: item[1]['rating'],
                  reverse = True))


fi.close() 

# Save
with open("leaderboard.json", "w") as file:
    json.dump(lea, file, indent=4)





