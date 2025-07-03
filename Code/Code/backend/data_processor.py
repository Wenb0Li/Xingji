import json
import numpy as np
from datetime import datetime, timedelta
from scipy.interpolate import interp1d
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        # 温度转换参数
        self.min_temp = 25.0      # 最低温度
        self.max_temp = 49.5      # 最高温度
        
        # 时间轴配置（从02am到10pm，每2小时一个点，共11个点）
        self.time_labels = [
            "02am", "04am", "06am", "08am", "10am", 
            "12pm", "02pm", "04pm", "06pm", "08pm", "10pm"
        ]
        
        # 纵轴配置（0-1，共11个点）
        self.y_axis_values = [i/10.0 for i in range(11)]  # [0.0, 0.1, 0.2, ..., 1.0]
    
    def temperature_to_percentage(self, temperature: float) -> float:
        """
        将温度转换为百分比 (0-1范围)
        温度范围: 25°C - 49.5°C 对应 0% - 100%
        """
        if temperature <= self.min_temp:
            return 0.0
        elif temperature >= self.max_temp:
            return 1.0
        else:
            # 线性转换
            percentage = (temperature - self.min_temp) / (self.max_temp - self.min_temp)
            return round(percentage, 3)
    
    def process_raw_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        处理原始数据，提取温度并转换为百分比
        """
        processed_data = []
        
        for data_point in raw_data:
            try:
                # 假设温度字段名为 'temperature' 或 'value'（根据实际情况调整）
                temperature = None
                
                if 'temperature' in data_point:
                    temperature = float(data_point['temperature'])
                elif 'value' in data_point and data_point.get('field') == 'temperature':
                    temperature = float(data_point['value'])
                elif 'value' in data_point:
                    temperature = float(data_point['value'])
                
                if temperature is not None:
                    percentage = self.temperature_to_percentage(temperature)
                    
                    processed_point = {
                        'timestamp': data_point.get('timestamp', 0),
                        'time': data_point.get('time', ''),
                        'temperature': temperature,
                        'fault_probability': percentage,
                        'original_data': data_point
                    }
                    processed_data.append(processed_point)
                    
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"处理数据点时出错: {e}, 数据: {data_point}")
                continue
        
        # 按时间排序
        processed_data.sort(key=lambda x: x['timestamp'])
        logger.info(f"成功处理 {len(processed_data)} 个数据点")
        
        return processed_data
    
    def generate_time_series_data(self, processed_data: List[Dict]) -> Dict[str, Any]:
        """
        生成时间序列可视化数据 - 修正为严格匹配前端接口
        """
        if not processed_data:
            logger.warning("没有数据可处理")
            return self.get_empty_time_series()
        
        try:
            # 提取时间和故障概率数据
            timestamps = [point['timestamp'] for point in processed_data]
            probabilities = [point['fault_probability'] for point in processed_data]
            
            # 生成目标时间点（从02am到10pm的11个点）
            target_times = self.generate_target_timestamps()
            
            # 如果数据点足够，使用插值平滑
            if len(timestamps) >= 2:
                # 创建插值函数
                interp_func = interp1d(
                    timestamps, 
                    probabilities, 
                    kind='cubic',
                    bounds_error=False, 
                    fill_value='extrapolate'
                )
                
                # 在目标时间点进行插值
                interpolated_probabilities = interp_func(target_times)
                interpolated_probabilities = np.clip(interpolated_probabilities, 0, 1)
                
            else:
                interpolated_probabilities = [probabilities[0] if probabilities else 0.5] * len(target_times)
            
            # 构建时间序列数据 - 严格按照前端接口
            time_series = []
            for i, (time_label, probability) in enumerate(zip(self.time_labels, interpolated_probabilities)):
                time_series.append({
                    "time": time_label,
                    "probability": round(float(probability), 3),
                    "timestamp": int(target_times[i])
                })
            
            # 获取最新数据点
            latest_data = processed_data[-1] if processed_data else {
                'temperature': 25.0,
                'fault_probability': 0.0,
                'time': datetime.now().isoformat()
            }
            
            # 构建完整的响应数据 - 严格按照前端接口定义
            result = {
                "timeSeries": time_series,
                "latestData": {
                    "temperature": latest_data['temperature'],
                    "faultProbability": latest_data['fault_probability'],
                    "timestamp": latest_data['time']
                },
                "availableWaterJets": ["WaterJet_01", "WaterJet_02", "WaterJet_03"],
                "availableDates": self.get_recent_dates()
            }
            
            logger.info("时间序列数据生成成功")
            return result
            
        except Exception as e:
            logger.error(f"生成时间序列数据时出错: {e}")
            return self.get_empty_time_series()
    
    def generate_target_timestamps(self) -> List[int]:
        """
        生成目标时间戳（今天的02am到10pm）
        """
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 生成从02am到10pm的时间戳
        target_times = []
        for hour in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:  # 02am到10pm
            target_time = today.replace(hour=hour)
            target_times.append(int(target_time.timestamp()))
        
        return target_times
    
    def get_recent_dates(self) -> List[str]:
        """
        获取最近的日期列表
        """
        dates = []
        for i in range(7):  # 最近7天
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        return dates
    
    def get_empty_time_series(self) -> Dict[str, Any]:
        """
        返回空的时间序列数据结构 - 严格按照前端接口
        """
        return {
            "timeSeries": [
                {
                    "time": time_label,
                    "probability": 0.0,
                    "timestamp": int(datetime.now().timestamp())
                }
                for time_label in self.time_labels
            ],
            "latestData": {
                "temperature": 25.0,
                "faultProbability": 0.0,
                "timestamp": datetime.now().isoformat()
            },
            "availableWaterJets": ["WaterJet_01"],
            "availableDates": self.get_recent_dates()
        }
    
    def process_and_export_json(self, raw_data: List[Dict]) -> str:
        """
        完整的数据处理流程，返回JSON字符串
        """
        # 1. 处理原始数据
        processed_data = self.process_raw_data(raw_data)
        
        # 2. 生成时间序列数据
        time_series_data = self.generate_time_series_data(processed_data)
        
        # 3. 转换为JSON
        json_result = json.dumps(time_series_data, ensure_ascii=False, indent=2)
        
        logger.info("数据处理完成，JSON生成成功")
        return json_result

# 全局处理器实例
processor = DataProcessor()

def get_processed_dashboard_data(raw_data: List[Dict]) -> str:
    """
    获取处理后的仪表板数据（JSON格式）
    供其他模块调用
    """
    return processor.process_and_export_json(raw_data)

# 测试示例
if __name__ == "__main__":
    # 模拟原始数据
    sample_data = [
        {"timestamp": 1703123400, "time": "2023-12-21T02:30:00Z", "value": 26.5, "field": "temperature"},
        {"timestamp": 1703127000, "time": "2023-12-21T03:30:00Z", "value": 28.2, "field": "temperature"},
        {"timestamp": 1703130600, "time": "2023-12-21T04:30:00Z", "value": 32.1, "field": "temperature"},
        {"timestamp": 1703134200, "time": "2023-12-21T05:30:00Z", "value": 35.8, "field": "temperature"},
        {"timestamp": 1703137800, "time": "2023-12-21T06:30:00Z", "value": 41.2, "field": "temperature"},
    ]
    
    # 处理数据
    result_json = get_processed_dashboard_data(sample_data)
    print("生成的JSON数据:")
    print(result_json) 