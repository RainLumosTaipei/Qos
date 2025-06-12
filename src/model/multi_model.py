import os

from . import random_forest
from . import model_util
from pcap import chunkDetect, metricParser


def train_multiple_models():
    final_model = []

    pcap_directory = "output/chunk/A0"
    metric_directory = "data/A0/MERGED_FILES"

    flag = 1

    # 遍历数据目录，为每个文件训练一个模型
    for filename in os.listdir(pcap_directory):
        if filename.endswith('.txt'):
            pcap_file = os.path.join(pcap_directory, filename)
            metric_file = os.path.join(metric_directory,
                                       filename
                                       .replace('chunk_', '')
                                       .replace('.txt', '_merged.txt'))

            # 提取指标
            stream_map = chunkDetect.load_chunk(pcap_file)
            metrics = metricParser.read_metric(metric_file)

            X, y = model_util.prepare_data(stream_map, metrics)
            if len(X) <= 5:
                print(f"stream map is empty: {filename}")
                continue
            print(filename)

            if flag == 1:
                final_model = random_forest.train_model(X, y)
                flag = 0
            else:
                final_model = random_forest.train_model_base_on(X, y, final_model)

    model_filename = f"output/model_A0_final.joblib"
    model_util.save_model(final_model, model_filename)

def test_final_models():
    final_model =  model_util.load_model("output/model_final.joblib")

    pcap_directory = "output/chunk/A2"
    metric_directory = "data/A2/MERGED_FILES"

    m = [0.0] * 9
    count = 0

    for filename in os.listdir(pcap_directory):
        if filename.endswith('.txt'):
            pcap_file = os.path.join(pcap_directory, filename)
            metric_file = os.path.join(metric_directory,
                                       filename
                                       .replace('chunk_', '')
                                       .replace('.txt', '_merged.txt'))

            # 提取指标
            stream_map = chunkDetect.load_chunk(pcap_file)
            metrics = metricParser.read_metric(metric_file)

            X, y = model_util.prepare_data(stream_map, metrics)
            if len(X) <= 5:
                print(f"stream map is empty: {filename}")
                continue
            count = count + 1
            print(filename)
            res = model_util.print_metrics_to_string(final_model, X, y)
            m = [a + b for a, b in zip(m, res)]


    for metric in m:
        metric /= count

    print("\n=== Playback Event 评估 ===")

    print(f"\n准确率 (Accuracy): {m[0]:.4f}")
    print(f"召回率 (Recall): {m[1]:.4f}")
    print(f"F4分数 (F4 Score): {m[2]:.4f}")

    print("\n=== Playback Quality 评估 ===")

    print(f"\n准确率 (Accuracy): {m[3]:.4f}")
    print(f"召回率 (Recall): {m[4]:.4f}")
    print(f"F4分数 (F4 Score): {m[5]:.4f}")

    print("\n=== Buffer Health 评估 ===")

    print(f"\n准确率 (Accuracy): {m[6]:.4f}")
    print(f"召回率 (Recall): {m[7]:.4f}")
    print(f"F4分数 (F4 Score): {m[8]:.4f}")

def train_final_model():
    final_model = []

    pcap_directories = ["output/chunk/A0", "output/chunk/A1", "output/chunk/A2"]
    metric_directories = ["data/A0/MERGED_FILES", "data/A1/MERGED_FILES", "data/A2/MERGED_FILES"]

    flag = 1

    for pcap_directory, metric_directory in zip(pcap_directories, metric_directories):
        # 遍历数据目录，为每个文件训练一个模型
        for filename in os.listdir(pcap_directory):
            if filename.endswith('.txt'):
                pcap_file = os.path.join(pcap_directory, filename)
                metric_file = os.path.join(metric_directory,
                                           filename
                                           .replace('chunk_', '')
                                           .replace('.txt', '_merged.txt'))

                # 提取指标
                stream_map = chunkDetect.load_chunk(pcap_file)
                metrics = metricParser.read_metric(metric_file)

                X, y = model_util.prepare_data(stream_map, metrics)
                if len(X) <= 5:
                    print(f"stream map is empty: {filename}")
                    continue
                print(filename)

                if flag == 1:
                    final_model = random_forest.train_model(X, y)
                    flag = 0
                else:
                    final_model = random_forest.train_model_base_on(X, y, final_model)

    model_filename = f"output/model_final.joblib"
    model_util.save_model(final_model, model_filename)