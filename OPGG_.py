import requests
import os

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
    return res.json() if res.status_code == 200 else None

def main():
    # 1. Récupérer le PUUID
    acc = get_data(f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not acc: return
    puuid = acc['puuid']

    # 2. Récupérer le dernier match (uniquement le plus récent)
    m_list = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1")
    if not m_list: return
    last_match_id = m_list[0]

    # 3. Lire le dernier match enregistré dans la "mémoire"
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            saved_id = f.read().strip()
    else:
        saved_id = ""

    # 4. Comparaison
    if last_match_id != saved_id:
        # Nouveau match détecté ! On récupère les détails
        game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{last_match_id}")
        rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")
        
        if game and rank_info:
            p = next(pl for pl in game['info']['participants'] if pl['puuid'] == puuid)
            solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), {"tier": "Unranked", "rank": "", "leaguePoints": 0})
            
            # Formatage Discord
            color = 0x2ecc71 if p['win'] else 0xe74c3c
            embed = {
                "embeds": [{
                    "title": f"{'🟩' if p['win'] else '🟥'} NOUVELLE GAME ANALYSÉE",
                    "description": f"Match ID: `{last_match_id}`",
                    "color": color,
                    "fields": [
                        {"name": "Champion", "value": f"**{p['championName']}**", "inline": True},
                        {"name": "Rank", "value": f"{solo['tier']} {solo['rank']} ({solo['leaguePoints']} LP)", "inline": True},
                        {"name": "KDA", "value": f"{p['kills']}/{p['deaths']}/{p['assists']}", "inline": True}
                    ]
                }]
            }
            requests.post(WEBHOOK, json=embed)

            # 5. Mettre à jour la "mémoire"
            with open(FILE_NAME, "w") as f:
                f.write(last_match_id)
            
            # On signale à GitHub qu'il y a eu un changement de fichier
            print(f"NEW_MATCH_DETECTED={last_match_id}")
    else:
        print("Aucun nouveau match depuis la dernière vérification.")

if __name__ == "__main__":
    main()
