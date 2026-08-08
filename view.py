import boto3
from boto3.dynamodb.conditions import Key

db = boto3.resource("dynamodb", region_name="ap-northeast-1")
table = db.Table("todolist")

res = table.query(KeyConditionExpression=Key("user_id").eq("kawatii"))
tasks = sorted(res["Items"], key=lambda t: t["deadline"])

for t in tasks:
    print(t["deadline"], t["name"])