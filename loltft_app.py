from flask import Flask, jsonify, request, render_template, make_response, session, redirect, url_for
from flask_login import LoginManager, current_user, login_required, logout_user, login_user
from flask_cors import CORS
import os
import requests
import json
# from blog_view import blog
# from blog_control.user_mgmt import User

# https 만을 지원하는 기능을 http 에서 테스트 할 때 필요한 설정
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__, static_url_path='/static')
CORS(app)
app.secret_key = 'garam_server'  # 로그인 기능과 관련된 key 선언
api_key = 'RGAPI-65da7eac-40cf-4ceb-8d3b-70077b5c4716'

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
    return enc_id


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


@ app.route('/')
def index():
    return redirect('/search')


@ app.route('/search')
def search():
    return render_template('search.html')


@ app.route('/search/id', methods=['GET', 'POST'])
def search_id():
    print(request.form['summon_name'])
    if request.form['summon_name'] == '':
        # print("search_id=null")
        return redirect('/search')
    else:
        summoner_name = request.form['summon_name']
        enc_id = get_id_by_summonname(summoner_name)
        tier, rank, pts = get_rank_by_id(enc_id)
        tft_tier, tft_rank, tft_pts = get_tft_rank_by_id(enc_id)
        #print("find id of ", summoner_name)
        #print("LOL : ", tier, rank, pts)
        #print("TFT : ", tft_tier, tft_rank, tft_pts)
        return render_template('search.html', summon_name=summoner_name, tier=tier, rank=rank, pts=pts, tft_tier=tft_tier, tft_rank=tft_rank, tft_pts=tft_pts)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
