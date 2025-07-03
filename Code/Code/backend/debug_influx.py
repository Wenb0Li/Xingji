from influxdb_client import InfluxDBClient

INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "TAM4ZxqcHQzIdGWap0iAfQk5R7Vzvz_j5XORuZ-mi-rYl0Rapwu4aTLeqM0X69xtb6_FkQ-PQtCiC1ZPO82p8g=="
INFLUX_ORG = "WEWE"
INFLUX_BUCKET = "Test"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

print("=== 调试InfluxDB数据 ===")

# 1. 查看所有数据（不加任何过滤条件）
print("\n1. 查看最近的10条原始数据:")
query1 = f'''
from(bucket: "{INFLUX_BUCKET}")
|> range(start: -30d)
|> limit(n: 10)
'''

result1 = query_api.query(query1)
for table in result1:
    for record in table.records:
        print(f"时间: {record.get_time()}")
        print(f"测量: {record.get_measurement()}")
        print(f"字段: {record.get_field()}")
        print(f"值: {record.get_value()}")
        print(f"标签: {record.values}")
        print("-" * 50)

# 2. 查看有哪些测量(measurement)
print("\n2. 查看所有的测量名称:")
query2 = f'''
from(bucket: "{INFLUX_BUCKET}")
|> range(start: -30d)
|> group(columns: ["_measurement"])
|> distinct(column: "_measurement")
'''

result2 = query_api.query(query2)
measurements = []
for table in result2:
    for record in table.records:
        measurement = record.get_measurement()
        if measurement not in measurements:
            measurements.append(measurement)
            print(f"  - {measurement}")

# 3. 查看有哪些字段(field)
print("\n3. 查看所有的字段名称:")
query3 = f'''
from(bucket: "{INFLUX_BUCKET}")
|> range(start: -30d)
|> group(columns: ["_field"])
|> distinct(column: "_field")
'''

result3 = query_api.query(query3)
fields = []
for table in result3:
    for record in table.records:
        field = record.get_field()
        if field not in fields:
            fields.append(field)
            print(f"  - {field}")

# 4. 查看数据的时间范围
print("\n4. 查看数据时间范围:")
query4 = f'''
from(bucket: "{INFLUX_BUCKET}")
|> range(start: -30d)
|> group()
|> min(column: "_time")
'''

query5 = f'''
from(bucket: "{INFLUX_BUCKET}")
|> range(start: -30d)
|> group()
|> max(column: "_time")
'''

result4 = query_api.query(query4)
result5 = query_api.query(query5)

for table in result4:
    for record in table.records:
        print(f"  最早时间: {record.get_time()}")

for table in result5:
    for record in table.records:
        print(f"  最晚时间: {record.get_time()}")

client.close() 