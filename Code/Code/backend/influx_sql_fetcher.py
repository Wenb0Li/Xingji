import time
import threading
from influxdb_client import InfluxDBClient
from influxdb_client.client.flux_table import FluxStructureEncoder
import logging
import json

# InfluxDB 配置
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "TAM4ZxqcHQzIdGWap0iAfQk5R7Vzvz_j5XORuZ-mi-rYl0Rapwu4aTLeqM0X69xtb6_FkQ-PQtCiC1ZPOkyp8g=="
INFLUX_ORG = "WEWE"
INFLUX_BUCKET = "Test"

# 全局变量存储数据
stored_data = []
data_lock = threading.Lock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data_with_sql():
    """
    使用SQL查询从InfluxDB获取数据
    """
    global stored_data
    
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    
    try:
        # SQL查询语句 - InfluxDB 2.x SQL语法
        sql_query = f"""
        SELECT 
            time,
            _field,
            _value,
            _measurement
        FROM "{INFLUX_BUCKET}"
        WHERE 
            time >= now() - interval '1 hour'
            AND _field = 'temperature'
        ORDER BY time ASC
        """
        
        logger.info(f"执行SQL查询: {sql_query}")
        
        # 由于InfluxDB Cloud的SQL支持限制，我们用等效的Flux查询来模拟SQL结果
        # 转换SQL为等效的Flux查询
        flux_equivalent = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_field"] == "temperature")
        |> sort(columns: ["_time"], desc: false)
        |> map(fn: (r) => ({{
            time: r._time,
            _field: r._field,
            _value: r._value,
            _measurement: r._measurement
        }}))
        '''
        
        query_api = client.query_api()
        result = query_api.query(flux_equivalent)
        
        # 处理查询结果，模拟SQL结果格式
        data_list = []
        for table in result:
            for record in table.records:
                # 构造类似SQL查询结果的数据结构
                data_point = {
                    'time': record.get_time().isoformat(),
                    '_field': record.get_field(),
                    '_value': record.get_value(),
                    '_measurement': record.get_measurement(),
                    'timestamp': int(record.get_time().timestamp())
                }
                
                # 添加其他字段
                for key, value in record.values.items():
                    if key not in ['_time', '_field', '_value', '_measurement'] and not key.startswith('_start') and not key.startswith('_stop'):
                        data_point[key] = value
                        
                data_list.append(data_point)
        
        # 线程安全地更新数据
        with data_lock:
            stored_data = data_list
            
        logger.info(f"SQL查询成功，获取 {len(data_list)} 条数据")
        
    except Exception as e:
        logger.error(f"SQL查询失败: {e}")
        # 如果SQL失败，尝试备用查询
        try_backup_query(client)
    finally:
        client.close()

def try_backup_query(client):
    """
    备用查询方法
    """
    global stored_data
    
    try:
        logger.info("尝试备用查询方法...")
        
        # 简单的Flux查询作为备用
        backup_query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r._field == "temperature")
        |> sort(columns: ["_time"])
        '''
        
        query_api = client.query_api()
        result = query_api.query(backup_query)
        
        data_list = []
        for table in result:
            for record in table.records:
                data_point = {
                    'time': record.get_time().isoformat(),
                    '_field': record.get_field(),
                    '_value': record.get_value(),
                    '_measurement': record.get_measurement(),
                    'timestamp': int(record.get_time().timestamp())
                }
                data_list.append(data_point)
        
        with data_lock:
            stored_data = data_list
            
        logger.info(f"备用查询成功，获取 {len(data_list)} 条数据")
        
    except Exception as e:
        logger.error(f"备用查询也失败: {e}")

def fetch_historical_data_sql(start_date: str, end_date: str = None, waterjet_id: str = None):
    """
    使用SQL查询历史数据
    """
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    
    try:
        if end_date is None:
            from datetime import datetime
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # SQL查询语句
        where_conditions = [
            f"time >= '{start_date}T00:00:00Z'",
            f"time <= '{end_date}T23:59:59Z'",
            "_field = 'temperature'"
        ]
        
        if waterjet_id:
            where_conditions.append(f"waterjet_id = '{waterjet_id}'")
        
        where_clause = " AND ".join(where_conditions)
        
        sql_query = f"""
        SELECT 
            time,
            _field,
            _value,
            _measurement,
            waterjet_id
        FROM "{INFLUX_BUCKET}"
        WHERE {where_clause}
        ORDER BY time ASC
        """
        
        logger.info(f"执行历史数据SQL查询: {sql_query}")
        
        # 转换为等效的Flux查询
        waterjet_filter = f' and r["waterjet_id"] == "{waterjet_id}"' if waterjet_id else ''
        
        flux_equivalent = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: {start_date}T00:00:00Z, stop: {end_date}T23:59:59Z)
        |> filter(fn: (r) => r["_field"] == "temperature"{waterjet_filter})
        |> sort(columns: ["_time"], desc: false)
        '''
        
        query_api = client.query_api()
        result = query_api.query(flux_equivalent)
        
        data_list = []
        for table in result:
            for record in table.records:
                data_point = {
                    'time': record.get_time().isoformat(),
                    '_field': record.get_field(),
                    '_value': record.get_value(),
                    '_measurement': record.get_measurement(),
                    'timestamp': int(record.get_time().timestamp())
                }
                
                # 添加标签
                for key, value in record.values.items():
                    if not key.startswith('_table') and not key.startswith('_start') and not key.startswith('_stop'):
                        data_point[key] = value
                
                data_list.append(data_point)
        
        logger.info(f"历史数据SQL查询成功，获取 {len(data_list)} 条数据")
        return data_list
        
    except Exception as e:
        logger.error(f"历史数据SQL查询失败: {e}")
        return []
    finally:
        client.close()

def get_data():
    """获取存储的数据"""
    with data_lock:
        return stored_data.copy()

def start_fetching():
    """每分钟获取一次数据"""
    def fetch_loop():
        while True:
            fetch_data_with_sql()
            time.sleep(60)  # 等待60秒（1分钟）
    
    # 立即执行一次
    fetch_data_with_sql()
    
    # 启动后台线程
    fetch_thread = threading.Thread(target=fetch_loop, daemon=True)
    fetch_thread.start()
    logger.info("SQL数据获取任务已启动，每分钟执行一次")

if __name__ == "__main__":
    # 测试SQL查询
    start_fetching()
    
    time.sleep(5)  # 等待首次查询完成
    
    # 显示当前数据
    current_data = get_data()
    print(f"当前数据条数: {len(current_data)}")
    
    if current_data:
        print("前5条数据:")
        for i, item in enumerate(current_data[:5]):
            print(f"  {i+1}: {item}")
    
    # 测试历史数据查询
    print("\n测试历史数据查询...")
    historical_data = fetch_historical_data_sql("2023-12-01", "2023-12-31")
    print(f"历史数据条数: {len(historical_data)}") 