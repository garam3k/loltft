from flask import Flask, jsonify, request, render_template, make_response, session, redirect, url_for
from flask_login import LoginManager, current_user, login_required, logout_user, login_user
from flask_cors import CORS
import os
import requests
import json
import ssl
import time
# from blog_view import blog
# from blog_control.user_mgmt import User

# https 만을 지원하는 기능을 http 에서 테스트 할 때 필요한 설정
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__, static_url_path='/static')
CORS(app)
app.secret_key = 'garam_server'  # 로그인 기능과 관련된 key 선언
api_key = 'RGAPI-0ef0516d-c0a5-4e6c-8db8-02505c88b2ff'

# app.register_blueprint(blog.blog_abtest, url_prefix='/blog')
# login_manager = LoginManager()  # 로그인 객체 선언
# login_manager.init_app(app)  # 앱 등록
# login_manager.session_protection = 'strong'  # 보안 강화


def get_id_by_summonname(summon_name):
    base_url = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'
    headers = {'X-Riot-Token': api_key}
    res = requests.get(base_url+summon_name, headers=headers)

    # print(str(res.status_code) + " // " + res.text)

    enc_id = json.loads(res.text)['id']
    puuid = json.loads(res.text)['puuid']
    return {'id': enc_id, 'puuid': puuid}


def get_rank_by_id(enc_id):
    base_url = 'https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/'
    headers = {'X-Riot-Token': api_key}
    res = requests.get(base_url+enc_id, headers=headers)
    if res.text == '[]':
        return None, None, None
    res = json.loads(res.text)[0]
    #print("lol:", res)
    if res['queueType'] == 'RANKED_SOLO_5x5':
        tier, rank, pts = res['tier'], res['rank'], res['leaguePoints']
    else:
        tier, rank, pts = None, None, None
    #print(tier, rank, pts)
    return tier, rank, pts


def get_tft_rank_by_id(enc_id):
    base_url = 'https://kr.api.riotgames.com/tft/league/v1/entries/by-summoner/'
    headers = {'X-Riot-Token': api_key}
    res = requests.get(base_url+enc_id, headers=headers)
    if res.text == '[]':
        # print("null")
        return None, None, None
    res = json.loads(res.text)[0]
    #print("tft:", res)
    tft_tier, tft_rank, tft_pts = res['tier'], res['rank'], res['leaguePoints']
    return tft_tier, tft_rank, tft_pts


def my_match_data_by_puuid(pid, pname):
    base_url = 'https://asia.api.riotgames.com/lol/match/v5/matches/'
    headers = {'X-Riot-Token': api_key}
    res = requests.get(base_url+pid, headers=headers)
    res = json.loads(res.text)

    start_time = round(time.time() - res['info']['gameStartTimestamp']/1000)
    if start_time > 3600*24:
        start_time = str(start_time // (3600*24)) + 'days ago'
    elif start_time > 3600:
        start_time = str(start_time // (3600)) + 'hours ago'
    else:
        start_time = str(start_time // (60)) + 'mins ago'
    game_type = res['info']['gameMode']
    if game_type == 'ARAM':
        game_type = '칼바람'
    elif game_type == 'CLASSIC':
        game_type = '솔로랭크'
    game_time = res['info']['gameDuration']
    game_time = str(game_time // 60000)+'m ' + \
        str((game_time % 60000) // 1000)+'s'
    kda, cs, deal, win = -1, -1, -1, False
    participants = res['info']['participants']
    for i in range(10):
        if participants[i]['summonerName'] != pname:
            continue
        kills = participants[i]['kills']
        deaths = participants[i]['deaths']
        assists = participants[i]['assists']
        if deaths == 0:
            kda = kills + assists
        else:
            kda = round((kills + assists) / deaths, 2)
        cs = participants[i]['totalMinionsKilled']
        deal = participants[i]['totalDamageDealtToChampions']
        win = participants[i]['win']
        if win:
            win = 'primary'
        else:
            win = 'danger'

    return {'start_time': start_time, 'kda': kda, 'game_time': game_time, 'game_type': game_type, 'cs': cs, 'deal': deal, 'win': win}


def match_list_by_puuid(pid):
    base_url = 'https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'
    headers = {'X-Riot-Token': api_key}
    res = requests.get(base_url+pid+'/ids?count=5', headers=headers)
    res = json.loads(res.text)
    return res


@ app.before_request
def before_request():
    if request.url.startswith('https://'):
        url = request.url.replace('https://', 'http://', 1)
        code = 301
        return redirect(url, code=code)


@ app.route('/')
def index():
    return redirect('/search')


@ app.route('/search')
def search():
    return render_template('search.html')


@ app.route('/search/id', methods=['GET', 'POST'])
def search_id():
    # print(request.form['summon_name'])
    if request.form['summon_name'] == '':
        # print("search_id=null")
        return redirect('/search')
    else:
        summoner_name = request.form['summon_name']
        ids = get_id_by_summonname(summoner_name)
        enc_id, puuid = ids['id'], ids['puuid']
        tier, rank, pts = get_rank_by_id(enc_id)
        tft_tier, tft_rank, tft_pts = get_tft_rank_by_id(enc_id)
        lol_list = [tier, rank, pts]
        tft_list = [tft_tier, tft_rank, tft_pts]
        #print("find id of ", summoner_name)
        #print("LOL : ", tier, rank, pts)
        #print("TFT : ", tft_tier, tft_rank, tft_pts)

        matches = match_list_by_puuid(puuid)
        # print(matches)
        match_list = []
        for i in range(len(matches)):
            match_list.append(my_match_data_by_puuid(
                matches[i], summoner_name))
        # print(match_list)

        return render_template('search.html', summon_name=summoner_name, lol_list=lol_list, tft_list=tft_list, match_list=match_list)


@ app.route('/search/legacy')
def search_legacy():
    pass


if __name__ == '__main__':
    #ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    #ssl_context.load_cert_chain(certfile='newcert.pem', keyfile='newkey.pem', password='secret')
    app.run(host='0.0.0.0', port='80', debug=True)
