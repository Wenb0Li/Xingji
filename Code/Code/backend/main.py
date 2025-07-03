from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import logging
from datetime import datetime
from data_processor import DataProcessor
from influx_sql_fetcher import start_fetching, get_data, fetch_historical_data_sql

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 创建处理器实例
processor = DataProcessor()

@app.route('/', methods=['GET'])
def api_info():
    """API信息页面"""
    return jsonify({
        "message": "水刀故障预测系统 API",
        "version": "1.0",
        "endpoints": {
            "current_data": "/api/dashboard/current",
            "history_data": "/api/dashboard/history?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&waterjet_id=xxx",
            "waterjets": "/api/waterjets",
            "health": "/api/health"
        },
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/dashboard/current', methods=['GET'])
def get_current_dashboard():
    """获取当前仪表板数据"""
    try:
        # 从SQL查询获取当前数据
        raw_data = get_data()
        
        # 处理数据并生成JSON
        dashboard_json = processor.process_and_export_json(raw_data)
        dashboard_data = json.loads(dashboard_json)
        
        return jsonify({
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取当前仪表板数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dashboard/history', methods=['GET'])
def get_historical_dashboard():
    """获取历史仪表板数据"""
    try:
        # 从查询参数获取日期和设备ID
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        waterjet_id = request.args.get('waterjet_id')
        
        if not start_date:
            return jsonify({
                "success": False,
                "error": "start_date 参数是必需的"
            }), 400
        
        # 使用SQL查询获取历史数据
        historical_data = fetch_historical_data_sql(start_date, end_date, waterjet_id)
        
        # 处理数据并生成JSON
        dashboard_json = processor.process_and_export_json(historical_data)
        dashboard_data = json.loads(dashboard_json)
        
        return jsonify({
            "success": True,
            "data": dashboard_data,
            "query_params": {
                "start_date": start_date,
                "end_date": end_date,
                "waterjet_id": waterjet_id
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/waterjets', methods=['GET'])
def get_waterjets():
    """获取可用的水刀设备列表"""
    return jsonify({
        "success": True,
        "data": ["WaterJet_01", "WaterJet_02", "WaterJet_03"]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    current_data = get_data()
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_count": len(current_data)
    })

if __name__ == '__main__':
    try:
        logger.info("启动后端服务...")
        
        # 启动SQL数据获取任务（每分钟执行一次）
        start_fetching()
        
        # 启动Flask API服务
        logger.info("API服务启动在 http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("服务被手动停止")
    except Exception as e:
        logger.error(f"启动服务失败: {e}") 