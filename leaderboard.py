import chess
import chess.pgn
import tqdm
import math
from datetime import datetime
import json


bar = tqdm.tqdm(10)

def escore(elo): # expected score
    return 1/(1+10**(elo/400))

def adjust1(timecontrol):
    time, inc = timecontrol.split('+')
    time = int(time)
    inc = int(inc)
    
    b1 = 150
    b2 = 150
    
    normalized_32 = math.log(180 + math.log(1 + 2)*b1)*b2
    
    return math.log(time + math.log(1 + inc)*b1)*b2 - normalized_32

def model1(timecontrol):
    time, inc = timecontrol.split('+')
    time = int(time)
    inc = int(inc)
    
    b1 = 158
    b2 = 251
    #a = -120
    #c = 0
    
    normalized_32 = math.log(180 + math.log(1 + 2)*b1)*b2
    
    return math.log(time + math.log(1 + inc)*b1)*b2 - normalized_32

def model2(timecontrol):
    time, inc = timecontrol.split('+')
    time = int(time)
    inc = int(inc)
    
    b1 = 406
    b2 = 390
    #a = -179
    #c = -16
    ba = 45
    
    normalized_32 = math.log(ba + 180 + math.log(2 + 2)*b1)*b2
    
    return math.log(ba + time + math.log(2 + inc)*b1)*b2 - normalized_32

adjust2 = model1

def k_tresh(games):
    tresh = [30, 150]
    K = [40, 20, 10]
    for i in range(len(tresh)):
        if games > tresh[i]:
            continue
        else:
            return K[i]
    return K[i]

def inactivity_malus(lead):
    for player in lead.keys():
        if lead[player]['BOT']: continue
        
        lead[player]['rating'] -= 10
        if lead[player]['rating'] < 1600: # floor
            lead[player]['rating'] = 1600
    return lead


malus_date = 1400000000 # for inactivity malus

K = 40

fi = open('lichess_LeelaQueenOdds_2024-11-18.pgn', 'r')

game = chess.pgn.read_game(fi)

lead = {}
s = {'1-0': 0, '1/2-1/2': 0.5, '0-1': 1}

games = []

while game != None:
    bar.update(1)
    games.append(game)
    game = chess.pgn.read_game(fi)


elo_tresh = [datetime.strptime('2024.11.01', "%Y.%m.%d").timestamp()*1000,
             datetime.strptime('2024.11.12', "%Y.%m.%d").timestamp()*1000]


for game in games[-1::-1]:
    bar.update(1)
    
    t = datetime.strptime(game.headers['UTCDate'], "%Y.%m.%d").timestamp()*1000
    
    if t < elo_tresh[0]:
        leela_elo = 1950
        adjust = adjust1
    elif t < elo_tresh[1]:
        leela_elo = 2100
        adjust = adjust1
    else:
        leela_elo = 2450
        adjust = adjust2
    
    if game.headers['Black'] == 'LeelaQueenOdds':
        player_color = 'White'
        leela_elo -= 100
    else:
        player_color = 'Black'
    
    player = game.headers[player_color]
    if player not in lead.keys():
        lead[player] = {
            'rating': 1600,
            'games': 0,
            'last_game': None,
            'BOT': False}
        if int(game.headers[player_color + 'Elo']) > 2000:
            lead[player]['rating'] = 1800
        elif int(game.headers[player_color + 'Elo']) > 1800:
            lead[player]['rating'] = int(game.headers[player_color + 'Elo']) - 200
    
    r = s[game.headers['Result']]
    if player_color == 'White':
        r = 1-r
    
    leela_elo -= adjust(game.headers['TimeControl'])
    
    K = k_tresh(lead[player]['games'])
    if r == 0.5: K = K/2 # Halving 'K' for Draws
    
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
    'date': int(datetime(2024, 11, 19).timestamp()*1000),
    'malus_date': malus_date,
    'prevlinks': [],
    'BOT': True}


#%%

# adding reference

time_control = ['1+0', '1+1', '3+0', '3+2', '5+3', '10+5', '15+10']

baseline = 2450

for tc in time_control:
    t, inc = tc.split('+')
    lead['LeelaQueenOdds as white ' + tc + ' (Reference)'] = {
        'rating': baseline - adjust2(str(int(t)*60)+'+'+inc),
        'games': 0,
        'last_game': None,
        'BOT': True}
    
    lead['LeelaQueenOdds as black ' + tc + ' (Reference)'] = {
        'rating': baseline - adjust2(str(int(t)*60)+'+'+inc) - 100,
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



