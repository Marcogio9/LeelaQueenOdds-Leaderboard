import requests
import chess
import chess.pgn
import math
from datetime import datetime
import json
import time

def get_games(username, since, until):
    url = f'https://lichess.org/api/games/user/{username}'
    params = {
        'since': since,
        'until': until,
        'max': 100000,
        'clocks': False,
        'pgnInJson': False
    }

    headers = {
        'Authorization': 'lip_UwVuKD9hhYcFqGhaBEBa'  # Token
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
    except:
        return ''

    if response.status_code == 200:
        return response
    else:
        print(f"Errore {response.status_code}: {response.text}")
        return ''


#%%

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
        if 100 < lead[player]['rating'] < 1600: # floor
            lead[player]['rating'] = 1600
    return lead



#%%


def update(lead, since, until):
    
    games = get_games('LeelaQueenOdds', since, until)
    
    if games.text == '':
        return lead
    
    with open('temp.pgn', 'w') as fi:
        fi.write(games.text)
        print(games.text)
    
    lead['metadata']['date'] = until
    malus_date = lead['metadata']['malus_date'] # for inactivity malus
    K = 40

    fi = open('temp.pgn', 'r')

    game = chess.pgn.read_game(fi)

    s = {'1-0': 0, '1/2-1/2': 0.5, '0-1': 1}

    games = []

    while game != None:
        games.append(game)
        game = chess.pgn.read_game(fi)

    for game in games[-1::-1]:

        if game.headers['Black'] == 'LeelaQueenOdds':
            player_color = 'White'
            leela_elo = 2100
        else:
            player_color = 'Black'
            leela_elo = 2150
        
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
        
        if (datetime.strptime(game.headers['UTCDate'], "%Y.%m.%d").timestamp()*1000) - malus_date >= 86400*7*1000:
            lead = inactivity_malus(lead)
            malus_date = datetime.strptime(game.headers['UTCDate'], "%Y.%m.%d").timestamp()*1000
            lead['metadata']['malus_date'] = malus_date
            
        if lead[player]['rating'] < 1600: # floor
            lead[player]['rating'] = 1600
        lead[player]['games'] += 1
        lead[player]['last_game'] = game.headers['UTCDate']
    
    print(f'Added {len(games)} games')
    fi.close()
    
    lead = dict(sorted(lead.items(),
                      key = lambda item: item[1]['rating'],
                      reverse = True))
    
    return lead
        
#%%


while 1:
    with open("leaderboard.json", "r") as fi:
        lead = json.load(fi)
    
        since_date = int(lead['metadata']['date'])-30000 # -30sec
        until_date = int(datetime.now().timestamp()*1000)
        
        lead = update(lead, since_date, until_date)
        
        with open("leaderboard.json", "w") as file:
            json.dump(lead, file, indent=4)
        
       
    
    time.sleep(60)
    print('-'*80)













