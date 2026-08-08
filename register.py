import os
import requests

APP_ID = "1535181765193240576"
TOKEN = os.environ["DISCORD_TOKEN"]

commands = [
    {"name": "view", "type": 1, "description": "自分のTODO一覧を見る"},
    {"name": "add", "type": 1, "description": "タスクを追加する（フォームが開くよ）"},
    {"name": "rm", "type": 1, "description": "タスクを消す（選んで削除）"},
    {"name": "done", "type": 1, "description": "タスクに完了設定を付ける"},
]

r = requests.put(
    f"https://discord.com/api/v10/applications/{APP_ID}/commands",
    headers={"Authorization": f"Bot {TOKEN}"},
    json=commands,
)
print(r.status_code, r.text[:200])