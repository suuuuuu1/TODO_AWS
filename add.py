import boto3
from datetime import datetime, timezone

db = boto3.resource("dynamodb", region_name="ap-northeast-1")
table = db.Table("todolist")

table.put_item(Item={
    "user_id": "776376619875041300",
    "task_id": datetime.now(timezone.utc).isoformat(),
    "name": "math",
    "deadline": "2026-08-30",
})
print("保存できたよ")