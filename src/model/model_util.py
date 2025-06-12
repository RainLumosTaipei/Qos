
import numpy as np
from sklearn.exceptions import UndefinedMetricWarning
from sklearn.metrics import accuracy_score, recall_score, fbeta_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore', category=UndefinedMetricWarning)


# 数据准备
def prepare_data(stream_map, metrics):
    X = []
    y = []

    # 从stream_map中提取特征
    for key, ip_stream in stream_map.items():
        for chunk in ip_stream.chunks:
            features = [
                chunk.request_time,
                chunk.first_byte_wait_time,
                chunk.download_time,
                chunk.slack_time,
                chunk.size,
                chunk.type.value
            ]
            X.append(features)

            # 这里需要根据时间点匹配对应的 metric
            # 假设可以通过相对时间来匹配
            for metric in metrics:
                if abs(metric.relative_time - chunk.request_time) < 0.1:  # 简单的时间匹配
                    y.append([metric.playback.playback_event_type,
                              metric.playback.playback_quality_type,
                              metric.playback.buffer_warning])
                    break
    return np.array(X), np.array(y)

def print_metrics(model, X_test, y_test):
    # 模型评估
    y_pred = model.predict(X_test)

    # 分割预测值和实际值
    y_pred_event = y_pred[:, 0]
    y_test_event = y_test[:, 0]

    y_pred_quality = y_pred[:, 1]
    y_test_quality = y_test[:, 1]

    y_pred_warning = y_pred[:, 2]
    y_test_warning = y_test[:, 2]

    # 计算各指标的评估结果
    print("\n=== Playback Event 评估 ===")
    evaluate_metrics(y_test_event, y_pred_event)

    print("\n=== Playback Quality 评估 ===")
    evaluate_metrics(y_test_quality, y_pred_quality)

    print("\n=== Buffer Health 评估 ===")
    evaluate_metrics(y_test_warning, y_pred_warning)

def print_metrics_to_string(model, X_test, y_test):
    # 模型评估
    y_pred = model.predict(X_test)

    y_pred_event = y_pred[:, 0]
    y_test_event = y_test[:, 0]

    y_pred_quality = y_pred[:, 1]
    y_test_quality = y_test[:, 1]

    y_pred_warning = y_pred[:, 2]
    y_test_warning = y_test[:, 2]

    return [ *evaluate_metrics_to_string(y_test_event, y_pred_event),
             *evaluate_metrics_to_string(y_test_quality, y_pred_quality),
             *evaluate_metrics_to_string(y_test_warning, y_pred_warning) ]

# 新增：计算并打印多种评估指标
# 低缓冲警告的准确率为92%，视频状态的准确率为84%，视频分辨率的准确率为66%
def evaluate_metrics(y_true, y_pred):

    # 对于多分类问题，我们假设y_pred是概率分布，选择值最大的类别作为预测结果
    if y_pred.ndim > 1 and y_pred.shape[1] > 1:  # 检查是否为多分类问题
        y_pred_class = np.argmax(y_pred, axis=1) # 用于返回数组中最大值的索引
        y_true_class = np.argmax(y_true, axis=1) if y_true.ndim > 1 and y_true.shape[1] > 1 else y_true

        # 计算分类指标
        accuracy = accuracy_score(y_true_class, y_pred_class)
        recall = recall_score(y_true_class, y_pred_class, average='weighted')
        f4 = fbeta_score(y_true_class, y_pred_class, beta=4, average='weighted')

        print(f"\n准确率 (Accuracy): {accuracy:.4f}")
        print(f"召回率 (Recall): {recall:.4f}")
        print(f"F4分数 (F4 Score): {f4:.4f}")

        # 打印详细的分类报告
        print("\n详细分类报告:")
        print(classification_report(y_true_class, y_pred_class))
    else:
        # 对于二分类或连续值问题，使用阈值方法
        y_true_binary = (y_true > 0.5).astype(int)
        y_pred_binary = (y_pred > 0.5).astype(int)

        # 计算分类指标
        accuracy = accuracy_score(y_true_binary, y_pred_binary)
        recall = recall_score(y_true_binary, y_pred_binary, average='weighted')
        f4 = fbeta_score(y_true_binary, y_pred_binary, beta=4, average='weighted')

        print(f"\n准确率 (Accuracy): {accuracy:.4f}")
        print(f"召回率 (Recall): {recall:.4f}")
        print(f"F4分数 (F4 Score): {f4:.4f}")

def evaluate_metrics_to_string(y_true, y_pred):

    # 对于多分类问题，我们假设y_pred是概率分布，选择值最大的类别作为预测结果
    if y_pred.ndim > 1 and y_pred.shape[1] > 1:  # 检查是否为多分类问题
        y_pred_class = np.argmax(y_pred, axis=1) # 用于返回数组中最大值的索引
        y_true_class = np.argmax(y_true, axis=1) if y_true.ndim > 1 and y_true.shape[1] > 1 else y_true

        # 计算分类指标
        accuracy = accuracy_score(y_true_class, y_pred_class)
        recall = recall_score(y_true_class, y_pred_class, average='weighted')
        f4 = fbeta_score(y_true_class, y_pred_class, beta=4, average='weighted')

        return [accuracy, recall, f4]

    else:
        # 对于二分类或连续值问题，使用阈值方法
        y_true_binary = (y_true > 0.5).astype(int)
        y_pred_binary = (y_pred > 0.5).astype(int)

        # 计算分类指标
        accuracy = accuracy_score(y_true_binary, y_pred_binary)
        recall = recall_score(y_true_binary, y_pred_binary, average='weighted')
        f4 = fbeta_score(y_true_binary, y_pred_binary, beta=4, average='weighted')

        return [accuracy, recall, f4]

# 新增：保存模型到本地文件
def save_model(model, filename='output/random_forest_model.joblib'):
    try:
        joblib.dump(model, filename)
        print(f"模型已成功保存到 {filename}")
    except Exception as e:
        print(f"保存模型时出错: {e}")

# 新增：从本地文件加载模型
def load_model(filename='output/model_A1_final.joblib'):
    try:
        model = joblib.load(filename)
        print(f"模型已成功从 {filename} 加载")
        return model
    except Exception as e:
        print(f"加载模型时出错: {e}")
        return None


def metrics_to_string(y_pred):
    # 定义各部分维度和映射关系
    DIMENSIONS = {
        'event': 4,
        'quality': 9,
        'warning': 1
    }

    MAPPINGS = {
        'event': ['buffering', 'paused', 'playing', 'collecting data'],
        'quality': ['non', 'tiny (144p)', 'small (240p)', 'medium (360p)', 'large (480p)',
                    'hd720', 'hd1080', 'hd1440', 'hd2160'],
        'warning': ['no buffer warning', 'buffer warning']  # 映射0和1到对应状态
    }

    # 按维度分割预测结果
    slices = {
        'event': y_pred[:DIMENSIONS['event']],
        'quality': y_pred[DIMENSIONS['event']:DIMENSIONS['event'] + DIMENSIONS['quality']],
        'warning': y_pred[-DIMENSIONS['warning']:]
    }

    # 处理各部分预测结果
    results = []

    # 处理事件和质量（分类问题）
    for key in ['event', 'quality']:
        index = np.argmax(slices[key])
        results.append(MAPPINGS[key][index])

    # 处理警告（二分类问题）
    warning_value = int(np.round(slices['warning'][0]))  # 转换为0/1整数
    results.append(MAPPINGS['warning'][warning_value])

    return results