import requests
import os
import time

# Configuration
API_KEY = os.getenv("RIOT_KEY")
WEBHOOK = os.getenv("WEBHOOK")
GAME_NAME = "Mamad0uBalTr0u"
TAG_LINE = "669"
REGION = "europe"
PLATFORM = "euw1"
FILE_NAME = "last_match.txt"

def get_data(url):
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return None

def main():
    if not API_KEY or not WEBHOOK:
        print("Erreur : Clés API ou Webhook manquants.")
        return

    # 1. Récupérer le PUUID
    acc_url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}"
    acc = get_data(acc_url)
    if not acc:
        print("Impossible de trouver le compte Riot.")
        return
    puuid = acc['puuid']

    # 2. Récupérer le dernier match ID
    list_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1"
    m_list = get_data(list_url)
    if not m_list:
        print("Aucun match trouvé.")
        return
    last_match_id = m_list[0]

    # 3. Vérifier la mémoire (doublons)
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            saved_id = f.read().strip()
    else:
        saved_id = ""

    if last_match_id == saved_id:
        print("Match déjà analysé. On s'arrête là.")
        return

    # 4. Récupérer les détails du match et du rank
    game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{last_match_id}")
    rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")

    if game and rank_info:
        # Trouver le bon participant
        p = next(pl for pl in game['info']['participants'] if pl['puuid'] == puuid)
        
        # Trouver le rank SoloQ
        solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), 
                    {"tier": "UNRANKED", "rank": "", "leaguePoints": 0})
        
        # Calculs Stats
        duration_min = max(1, game['info']['gameDuration'] / 60)
        cs = p['totalMinionsKilled'] + p['neutralMinionsKilled']
        cs_min = round(cs / duration_min, 1)
        team_kills = sum(pl['kills'] for pl in game['info']['participants'] if pl['teamId'] == p['teamId'])
        kp = round(((p['kills'] + p['assists']) / max(1, team_kills)) * 100, 1)
        
        # Assets (Images)
        champ_name = p['championName']
        # Note : On utilise la version 14.7.1, à mettre à jour selon les patchs Riot
        champ_img = f"https://ddragon.leagueoflegends.com/cdn/14.7.1/img/champion/{champ_name}.png"

        # Couleur : Vert si victoire, Rouge si défaite
        color = 0x2ecc71 if p['win'] else 0xe74c3c

        # Construction de l'Embed Discord
        embed = {
            "embeds": [{
                "author": {
                    "name": f"PERFORMANCE ANALYSIS | {champ_name.upper()}",
                    "icon_url": champ_img
                },
                "title": f"{'🟩 WIN' if p['win'] else '🟥 LOSS'} - Game Duration: {int(duration_min)}m {int(game['info']['gameDuration'] % 60)}s",
                "color": color,
                "thumbnail": {"url": champ_img},
                "fields": [
                    {
                        "name": "🛡️ RANKED STATUS",
                        "value": f"**Tier**: {solo['tier']} {solo['rank']}\n**LPs**: {solo['leaguePoints']} LP",
                        "inline": False
                    },
                    {
                        "name": "⚔️ COMBAT STATS",
                        "value": f"**KDA**: {p['kills']}/{p['deaths']}/{p['assists']}\n**KP**: {kp}% | **Damage**: {p['totalDamageDealtToChampions']}",
                        "inline": True
                    },
                    {
                        "name": "💰 ECONOMY",
                        "value": f"**CS**: {cs} ({cs_min}/m)\n**Gold**: {p['goldEarned']}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Mamad0uBalTr0u Analysis • Match ID: {last_match_id}"
                },
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }]
        }

        # Envoi à Discord
        response = requests.post(WEBHOOK, json=embed)
        
        if response.status_code == 204 or response.status_code == 200:
            print("Message envoyé avec succès !")
            # 5. Mettre à jour la mémoire seulement si l'envoi a réussi
            with open(FILE_NAME, "w") as f:
                f.write(last_match_id)
        else:
            print(f"Erreur lors de l'envoi Discord : {response.status_code}")

if __name__ == "__main__":
    main()
