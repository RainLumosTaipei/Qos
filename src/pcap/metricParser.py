import re
from typing import List, Dict, Any, Optional, Union
from .metric import NetworkInfo, PlaybackInfo, Metric

def parse_network_info(network_str: str) -> List[NetworkInfo]:
    networks = []
    # 去除首尾的方括号并分割网络信息
    network_list = network_str.strip('[]').split('], [')
    for net in network_list:
        net = net.replace('[', '').replace(']', '')
        parts = [p.strip() for p in net.split(',')]
        src_ip = parts[0]
        dst_ip = parts[1]
        protocol = parts[2] if parts[2] != '0' else None
        packets_sent = int(parts[3])
        packets_received = int(parts[4])
        bytes_sent = int(parts[5])
        bytes_received = int(parts[6])
        network = NetworkInfo(
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=protocol,
            packets_sent=packets_sent,
            packets_received=packets_received,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received
        )
        networks.append(network)
    return networks

def first_non_zero_index(arr):
    for i, val in enumerate(arr):
        if val != 0:
            return i
    return -1  # 如果所有元素都是0，返回-1

def parse_playback_info(playback_str: str) -> PlaybackInfo:
    playback_str = playback_str.strip('[]')
    # 先分割出第一个列表
    first_list_str, remaining = playback_str.split(']', 1)
    playback_event = [int(x.strip()) for x in first_list_str.strip('[').split(',')]
    playback_event_type = first_non_zero_index(playback_event)

    remaining = remaining.lstrip(',')
    parts = remaining.split(',', 4)

    epoch_time = int(parts[0].strip())
    start_time = int(parts[1].strip())
    playback_progress = float(parts[2].strip())
    video_length = float(parts[3].strip())

    # 提取播放质量列表
    new_part = parts[4].strip().lstrip('[')
    new_parts = new_part.split('],')
    quality_list_str = new_parts[0]
    playback_quality = [int(x.strip()) for x in quality_list_str.split(',')]
    playback_quality_type = first_non_zero_index(playback_quality)

    new_parts = new_parts[1].split(',')
    buffer_health = float(new_parts[0].strip())
    buffer_warning = 0
    if buffer_health < 20:
        buffer_warning = 1
    text_progress = new_parts[1].strip()
    if text_progress == 'null':
        buffer_progress = 0
    else:
        buffer_progress = float(text_progress)
    buffer_valid = bool(new_parts[2].strip()) if new_parts[2].strip() != '-1' else None

    playback = PlaybackInfo(
        playback_event=playback_event,
        playback_event_type=playback_event_type,
        epoch_time=epoch_time,
        start_time=start_time,
        playback_progress=playback_progress,
        video_length=video_length,
        playback_quality=playback_quality,
        playback_quality_type=playback_quality_type,
        buffer_health=buffer_health,
        buffer_warning=buffer_warning,
        buffer_progress=buffer_progress,
        buffer_valid=buffer_valid
    )
    return playback

def parse_metric(text: str) -> List[Metric]:
    """解析整个网络数据文本块"""
    metrics = []
    lines = text.strip().split('\n')
    for line in lines:
        if line:
            line = line.strip('[]')
            parts = line.split(', [[', 2)

            relative_time = float(parts[0].split(',')[0].strip())
            packets_sent = int(parts[0].split(',')[1].strip())
            packets_received = int(parts[0].split(',')[2].strip())
            bytes_sent = int(parts[0].split(',')[3].strip())
            bytes_received = int(parts[0].split(',')[4].strip())

            networks = parse_network_info(parts[1])
            playback = parse_playback_info(parts[2])
            metric = Metric(
                relative_time=relative_time,
                packets_sent=packets_sent,
                packets_received=packets_received,
                bytes_sent=bytes_sent,
                bytes_received=bytes_received,
                networks=networks,
                playback=playback
            )
            metrics.append(metric)
    return metrics


def read_metric(file_path: str) -> List[Metric]:
    """从文件读取网络数据"""
    try:
        with open(file_path, 'r') as file:
            text = file.read()
            return parse_metric(text)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []


def write_metric(metrics: List[Metric], file_path: str) -> None:
    """将Metric对象列表写入文件"""
    try:
        with open(file_path, 'w') as file:
            for metric in metrics:
                # 构建头部信息
                header = f"[{metric.relative_time}, {metric.packets_sent}, {metric.packets_received}, {metric.bytes_sent}, {metric.bytes_received}]"

                # 构建网络信息
                network_items = []
                for net in metric.networks:
                    protocol = net.protocol if net.protocol is not None else '0'
                    network_items.append(
                        f"[{net.src_ip}, {net.dst_ip}, {protocol}, {net.packets_sent}, {net.packets_received}, {net.bytes_sent}, {net.bytes_received}]")
                networks = f"[{', '.join(network_items)}]"

                # 构建播放信息
                playback = metric.playback
                playback_event = f"[{', '.join(map(str, playback.playback_event))}]"
                quality = f"[{', '.join(map(str, playback.playback_quality))}]"
                buffer_valid = playback.buffer_valid if playback.buffer_valid is not None else -1

                playback_info = (f"[{playback_event}, {playback.epoch_time}, {playback.start_time}, "
                                 f"{playback.playback_progress}, {quality}, {playback.buffer_health}, "
                                 f"{playback.buffer_progress}, {buffer_valid}]")

                # 写入完整的一行
                line = f"[{header}, {networks}, {playback_info}]\n"
                file.write(line)
        print(f"成功将 {len(metrics)} 条记录写入文件: {file_path}")
    except Exception as e:
        print(f"写入文件时出错: {e}")