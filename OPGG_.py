import requests
import time

# ===== CONFIG =====
API_KEY = "RGAPI-1a9da4c9-728c-4f63-840f-aa29a0150fc0"
GAME_NAME = "Mamad0uBalTr0u"
TAG_LINE = "669"
REGION = "europe"        # Pour account-v1 et match-v5
PLATFORM = "euw1"        # Pour league-v4 (spécifique à ton serveur)
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1491693754342445216/vOqPiq_danJlw65ZRwCQiEfPAf6iTTsPm3BoGp2RMpTQj9FSupC389Y0DzRmXXAT74o-"

def get_data(url):
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

def get_stats_otp(puuid, champion_name):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=20"
    match_ids = get_data(url) or []
    wins = 0
    picks = 0
    for m_id in match_ids:
        m_data = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{m_id}")
        if m_data:
            for p in m_data['info']['participants']:
                if p['puuid'] == puuid:
                    if p['win']: wins += 1
                    if p['championName'].lower() == champion_name.lower(): picks += 1
    wr = (wins / len(match_ids)) * 100 if match_ids else 0
    pr = (picks / len(match_ids)) * 100 if match_ids else 0
    return round(wr, 1), round(pr, 1)

def main():
    print(f"--- OPGG+ PREMIUM DASHBOARD LANCÉ ---")
    acc_data = get_data(f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not acc_data: return
    puuid = acc_data['puuid']
    last_match_id = None

    while True:
        try:
            m_list = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1")
            if m_list and m_list[0] != last_match_id:
                match_id = m_list[0]
                game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}")
                
                if game:
                    p = next(pl for pl in game['info']['participants'] if pl['puuid'] == puuid)
                    duration_min = game['info']['gameDuration'] / 60
                    team_kills = sum(pl['kills'] for pl in game['info']['participants'] if pl['teamId'] == p['teamId'])
                    kp = round(((p['kills'] + p['assists']) / team_kills) * 100, 1) if team_kills > 0 else 0
                    
                    # Récupération Rang
                    rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")
                    solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), None)
                    
                    # Stats OTP (20 dernières games)
                    wr, pr = get_stats_otp(puuid, p['championName'])
                    
                    # --- CONSTRUCTION DE L'EMBED STYLE ---
                    color = 0x2ecc71 if p['win'] else 0xe74c3c # Vert Emeraude ou Rouge Alizarine
                    status_icon = "🟩" if p['win'] else "🟥"
                    
                    embed = {
                        "username": "DPM+",
                        "embeds": [{
                            "title": f"{status_icon} PERFORMANCE ANALYSIS | {p['championName'].upper()}",
                            "description": f"**Game Duration:** `{int(duration_min)}m {int((duration_min%1)*60)}s`",
                            "color": color,
                            "thumbnail": {"url": f"https://ddragon.leagueoflegends.com/cdn/14.1.1/img/champion/{p['championName']}.png"},
                            "fields": [
                                {
                                    "name": "🏆 RANKED STATUS",
                                    "value": f"**Tier:** `{solo['tier']} {solo['rank']}`\n**LPs:** `{solo['leaguePoints']} LP`",
                                    "inline": True
                                },
                                {
                                    "name": "🧠 OTP INSIGHTS (20G)",
                                    "value": f"**Winrate:** `{wr}%`\n**Pickrate:** `{pr}%`",
                                    "inline": True
                                },
                                {
                                    "name": "⚔️ COMBAT STATS",
                                    "value": f"**KDA:** `{p['kills']}/{p['deaths']}/{p['assists']}`\n**KP:** `{kp}%` | **Damage:** `{p['totalDamageDealtToChampions']}`",
                                    "inline": False
                                },
                                {
                                    "name": "💰 ECONOMY",
                                    "value": f"**CS:** `{p['totalMinionsKilled'] + p['neutralMinionsKilled']}` (`{round((p['totalMinionsKilled'] + p['neutralMinionsKilled'])/duration_min, 1)}/m`)\n**Gold/Min:** `{round(p['goldEarned']/duration_min, 0)}`",
                                    "inline": True
                                }
                            ],
                            "footer": {"text": f"Mamad0uBalTr0u Analysis • Match ID: {match_id}"},
                            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                        }]
                    }
                    
                    requests.post(DISCORD_WEBHOOK, json=embed)
                    last_match_id = match_id
                    print(f"Dashboard Premium envoyé : {match_id}")
            else:
                print("Scanning for new data...")
        except Exception as e:
            print(f"Erreur : {e}")
        
        time.sleep(180)

if __name__ == "__main__":
    main()