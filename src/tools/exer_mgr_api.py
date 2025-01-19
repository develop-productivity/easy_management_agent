import numpy as np
import random


# 计算单天的指标
def calculate_daily_metrics(durations, intensities, calories):
    # 运动负荷指数 (ELI)  反映用户每日运动总负荷，帮助评估运动量是否达标。
    eli = sum(d * i for d, i in zip(durations, intensities))
    # 心血管效益评分 (CBS)， 反映用户日常训练中有氧运动的比例，评估心血管健康的锻炼效果。
    cbs = (sum(d * i for d, i in zip(durations, intensities)) / sum(durations)) * 100 if sum(durations) > 0 else 0
    # 卡路里效率 (CE)， 衡量用户在单位时间内的卡路里消耗，反映锻炼效率。
    ce = sum(calories) / sum(durations) if sum(durations) > 0 else 0
    # 强度一致性系数 (ICF)， 衡量用户锻炼强度的波动性，数值越接近 1 表示强度分配越稳定。
    icf = 1 - (np.std(intensities) / np.mean(intensities)) if len(intensities) > 1 else 1
    return {"ELI": eli, "CBS": cbs, "CE": ce, "ICF": icf}

# 归一化函数
def normalize_daily_metrics(all_metrics):
    # 找到每个指标的最大值和最小值
    # max_values = {key: max(metrics[key] for metrics in all_metrics) for key in all_metrics[0].keys()}
    # min_values = {key: min(metrics[key] for metrics in all_metrics) for key in all_metrics[0].keys()}
    # 对每个指标的每天值进行归一化
    # normalized = {key: [] for key in all_metrics[0].keys()}
    normalized = {key: [] for key in all_metrics[0].keys()}
    for metrics in all_metrics:
        for key, value in metrics.items():
            # normalized_value = (value - min_values[key]) / (max_values[key] - min_values[key]) if max_values[key] != min_values[key] else 0
            normalized[key].append(round(value, 3))
    return normalized

# 计算每天的指标
def calculate_metrics(data):
    daily_metrics = [
        calculate_daily_metrics(
            durations=data["duration_list"][i],
            intensities=data["intensity_list"][i],
            calories=data["calories_list"][i],
        )
        for i in range(len(data["duration_list"]))
    ]
    normalized_daily_metrics = normalize_daily_metrics(daily_metrics)
    return normalized_daily_metrics

if __name__ == "__main__":
    # 示例输入数据
    data = {
        "duration_list": [[30, 45], [60], [20, 25, 15]],  # 每天的运动时长 (分钟)
        "intensity_list": [[7, 8], [5], [6, 7, 5]],       # 每天的运动强度 (1-10)
        "calories_list": [[200, 300], [400], [150, 200, 100]],  # 每天的消耗卡路里 (kcal)
    }
    def generate_random_data(days):
        data = {
            "duration_list": [],
            "intensity_list": [],
            "calories_list": [],
        }
        for _ in range(days):
            num_activities = random.randint(1, 5)
            durations = [random.randint(10, 60) for _ in range(num_activities)]
            intensities = [random.randint(1, 10) for _ in range(num_activities)]
            calories = [random.randint(50, 500) for _ in range(num_activities)]
            data["duration_list"].append(durations)
            data["intensity_list"].append(intensities)
            data["calories_list"].append(calories)
        return data

    # 生成7天的随机数据
    data = generate_random_data(7)
    
    print(calculate_metrics(data))
