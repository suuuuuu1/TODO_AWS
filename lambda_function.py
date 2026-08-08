import json
import os
import base64
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from nacl.signing import VerifyKey

PUBLIC_KEY = os.environ["DISCORD_PUBLIC_KEY"]
table = boto3.resource("dynamodb").Table("todolist")


def lambda_handler(event, context):
    headers = event.get("headers") or {}
    sig = headers.get("x-signature-ed25519", "")
    ts = headers.get("x-signature-timestamp", "")
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode()

    try:
        VerifyKey(bytes.fromhex(PUBLIC_KEY)).verify((ts + body).encode(), bytes.fromhex(sig))
    except Exception:
        return {"statusCode": 401, "body": "invalid request signature"}

    data = json.loads(body)

    if data["type"] == 1:  # PING
        return respond({"type": 1})

    user = (data.get("member") or {}).get("user") or data.get("user") or {}
    user_id = user.get("id", "unknown")

    if data["type"] == 5:  # /add のフォーム送信が届いた
        values = {}
        for row in data["data"]["components"]:
            c = row["components"][0]
            values[c["custom_id"]] = c.get("value") or ""
        try:
            datetime.strptime(values["deadline"], "%Y-%m-%d")
        except ValueError:
            return respond({"type": 4, "data": {"content": "⚠️ 期限は 2026-08-31 みたいな YYYY-MM-DD の形で書いてね"}})
        table.put_item(Item={
            "user_id": user_id,
            "task_id": datetime.now(timezone.utc).isoformat(),
            "name": values["name"],
            "content": values["content"],
            "deadline": values["deadline"],
        })
        msg = "追加したよ ✅ 〆" + values["deadline"] + "『" + values["name"] + "』"
        return respond({"type": 4, "data": {"content": msg}})

    if data["type"] == 3:  # /rm のメニューで選ばれた
        task_id = data["data"]["values"][0]
        table.delete_item(Key={"user_id": user_id, "task_id": task_id})
        return respond({"type": 4, "data": {"content": "消したよ 🗑️"}})

    command = data["data"]["name"]

    if command == "add":
        return respond({
            "type": 9,
            "data": {
                "custom_id": "add_modal",
                "title": "タスク追加",
                "components": [
                    {"type": 1, "components": [{"type": 4, "custom_id": "name", "label": "タスク名", "style": 1, "required": True}]},
                    {"type": 1, "components": [{"type": 4, "custom_id": "deadline", "label": "期限 (YYYY-MM-DD)", "style": 1, "required": True, "min_length": 10, "max_length": 10}]},
                    {"type": 1, "components": [{"type": 4, "custom_id": "content", "label": "内容（書かなくてもOK）", "style": 2, "required": False}]},
                ],
            },
        })

    if command == "view":
        res = table.query(KeyConditionExpression=Key("user_id").eq(user_id))
        tasks = sorted(res["Items"], key=lambda t: t["deadline"])
        if tasks:
            lines = ["・" + t["deadline"] + "　" + t["name"] for t in tasks]
            text = "📋 きみのタスク:\n" + "\n".join(lines)
        else:
            text = "まだタスク無いよ"
        return respond({"type": 4, "data": {"content": text}})

    if command == "rm":
        res = table.query(KeyConditionExpression=Key("user_id").eq(user_id))
        tasks = sorted(res["Items"], key=lambda t: t["deadline"])[:25]
        if not tasks:
            return respond({"type": 4, "data": {"content": "消すタスクが無いよ"}})
        options = [{"label": (t["deadline"] + "　" + t["name"])[:100], "value": t["task_id"]} for t in tasks]
        return respond({
            "type": 4,
            "data": {
                "content": "どれを消す？",
                "components": [{"type": 1, "components": [
                    {"type": 3, "custom_id": "rm_select", "options": options}
                ]}],
            },
        })

    return respond({"type": 4, "data": {"content": "/" + command + " はまだ工事中🚧"}})


def respond(payload):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }
