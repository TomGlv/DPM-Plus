import requests
import time

# ===== CONFIG =====
API_KEY = "RIOT_KEY"
GAME_NAME = "Mamad0uBalTr0u"
TAG_LINE = "669"
REGION = "europe"        # Pour account-v1 et match-v5
PLATFORM = "euw1"        # Pour league-v4 (spécifique à ton serveur)
DISCORD_WEBHOOK = "WEBHOOK"

def get_data(url):
    headers = {"X-Riot-Token": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else None
    except:
        return None

def main():
    # 1. On récupère ton identité
    acc = get_data(f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not acc: return
    puuid = acc['puuid']

    # 2. Check si un match a eu lieu dans les 12 dernières minutes (720 sec)
    # On met 12 min pour un cron de 10 min pour éviter les "trous"
    since = int(time.time()) - 86400
    m_list = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={since}&count=1")

    if m_list:
        match_id = m_list[0]
        game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}")
        rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")
        
        if game and rank_info:
            p = next(pl for pl in game['info']['participants'] if pl['puuid'] == puuid)
            solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), None)
            
            # Calcul KP% et Durée
            duration_min = game['info']['gameDuration'] / 60
            team_kills = sum(pl['kills'] for pl in game['info']['participants'] if pl['teamId'] == p['teamId'])
            kp = round(((p['kills'] + p['assists']) / team_kills) * 100, 1) if team_kills > 0 else 0
            
            # Embed Style
            color = 0x2ecc71 if p['win'] else 0xe74c3c
            embed = {
                "username": "OPGG+ Intelligence",
                "embeds": [{
                    "title": f"{'🟩' if p['win'] else '🟥'} MATCH ANALYZED | {p['championName'].upper()}",
                    "color": color,
                    "thumbnail": {"url": f"https://ddragon.leagueoflegends.com/cdn/14.1.1/img/champion/{p['championName']}.png"},
                    "fields": [
                        {"name": "🏆 RANK", "value": f"`{solo['tier']} {solo['rank']}` ({solo['leaguePoints']} LP)", "inline": True},
                        {"name": "⚔️ KDA", "value": f"`{p['kills']}/{p['deaths']}/{p['assists']}` (KP: `{kp}%`)", "inline": True},
                        {"name": "💰 CS", "value": f"`{p['totalMinionsKilled'] + p['neutralMinionsKilled']}` (`{round((p['totalMinionsKilled'] + p['neutralMinionsKilled'])/duration_min, 1)}/m`)", "inline": True}
                    ],
                    "footer": {"text": f"D4 Tracker • ID: {match_id}"}
                }]
            }
            requests.post(WEBHOOK, json=embed)
            print(f"Match {match_id} envoyé à Discord.")
    else:
        print("Pas de nouveau match détecté.")

if __name__ == "__main__":
    main()
