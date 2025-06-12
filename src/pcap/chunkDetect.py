from collections import defaultdict
from typing import Dict, Tuple
import re
from scapy.all import rdpcap
from scapy.layers.inet import TCP, UDP

from .chunk import IpStream, Chunk, PacketType

GET_MIN_PAYLOAD = 300



# 根据地址查找连接信息的函数（未找到时自动添加）
def find_stream(stream_map, src: str, dst: str) -> IpStream:
    # 确保键的顺序是固定的
    if src <= dst:
        key = (src, dst)
    else:
        key = (dst, src)

    if key not in stream_map:
        stream_map[key] = IpStream(src, dst)
    return stream_map[key]


def is_private_ip(ip: str) -> bool:
    """判断IP地址是否为私有地址"""
    # 分割IP地址为四部分
    parts = list(map(int, ip.split('.')))

    # 检查是否为A类私有地址 (10.0.0.0/8)
    if parts[0] == 10:
        return True

    # 检查是否为B类私有地址 (172.16.0.0/12)
    if parts[0] == 172 and 16 <= parts[1] <= 31:
        return True

    # 检查是否为C类私有地址 (192.168.0.0/16)
    if parts[0] == 192 and parts[1] == 168:
        return True

    # 检查是否为回环地址 (127.0.0.0/8)
    if parts[0] == 127:
        return True

    # 检查是否为链路本地地址 (169.254.0.0/16)
    if parts[0] == 169 and parts[1] == 254:
        return True

    return False


def is_up_stream(src) -> bool:
    """判断是否为内网地址"""
    return is_private_ip(src)


def is_GQUIC(packet):
    return (packet.haslayer(UDP) and
            (packet['UDP'].dport == 443 or packet['UDP'].sport == 443))

# 筛选包
def chunk_detect(input_file):
    try:
        # 读取pcap文件
        packets = rdpcap(input_file)
        print("read packets: ", len(packets))
        start_time = packets[0].time
        client_ip = packets[0]['IP'].src

        stream_map: Dict[Tuple[str, str], IpStream] = defaultdict(IpStream)

        for packet in packets:
            if packet.haslayer(TCP) or is_GQUIC(packet):
                src_ip = packet['IP'].src
                dst_ip = packet['IP'].dst
                payload = packet.len
                time = packet.time - start_time

                # 获取对应的流
                ip_stream = find_stream(stream_map, src_ip, dst_ip)
                # GET
                if is_up_stream(src_ip) or client_ip == src_ip:
                    if payload > GET_MIN_PAYLOAD:
                        ip_stream.save_chunk(time)
                # 接受数据
                else:
                    ip_stream.add_chunk(time, payload)

        # 判断数据包类型, 使用list()复制键列表
        for key in list(stream_map.keys()):
            if not stream_map[key].chunks:
                del stream_map[key]
            else:
                stream_map[key].judge_type()

        return stream_map

    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return None


def save_chunk(stream_map, outfile):
    try:
        with open(outfile, 'w') as f:
            # 遍历所有的IpStream对象
            for key, ipStream in stream_map.items():
                f.write(f"Source IP: {ipStream.src}, Destination IP: {ipStream.dst}\n")
                for chunk in ipStream.chunks:
                    f.write(f"  "
                            f"GET: {chunk.request_time}, "
                            f"TTFB: {chunk.first_byte_wait_time}, "
                            f"down: {chunk.download_time}, "
                            f"slack: {chunk.slack_time}, "
                            f"size: {chunk.size}, "
                            f"type: {chunk.type.name}\n")
                f.write('\n')
        print(f"Data saved to {outfile} successfully.")
    except Exception as e:
        print(f"Error saving data to file: {e}")


def load_chunk(file_path):
    try:
        with open(file_path, 'r') as file:
            data = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")

    stream_map: Dict[Tuple[str, str], IpStream] = defaultdict(IpStream)
    current_stream = None
    prev_get_time = None

    lines = data.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否是新的IP流
        ip_match = re.match(r'Source IP: (\d+\.\d+\.\d+\.\d+), Destination IP: (\d+\.\d+\.\d+\.\d+)', line)
        if ip_match:
            src_ip, dst_ip = ip_match.groups()
            key = (src_ip, dst_ip)
            if key not in stream_map:  # 新创建的流
                current_stream = IpStream(src_ip, dst_ip)
                stream_map[key] = current_stream
            prev_get_time = None
            continue

        # 解析GET请求行
        get_match = re.match(
            r'GET: ([\d.]+), TTFB: ([\d.]+), down: ([\d.]+), slack: ([\d.]+), size: (\d+), type: (\w+)', line)
        if get_match and current_stream:
            get_time, ttfb, download, slack, size, packet_type = get_match.groups()

            get_time = float(get_time)
            ttfb = float(ttfb)
            download = float(download)
            slack = float(slack)
            size = int(size)

            # 创建新的Chunk
            chunk = Chunk(get_time)
            chunk.size = size
            chunk.first_byte_wait_time = ttfb
            chunk.download_time = download
            chunk.slack_time = slack

            chunk.start = get_time + ttfb
            chunk.end = chunk.start + download

            # 设置类型
            if packet_type == "AUDIO":
                chunk.type = PacketType.AUDIO
            elif packet_type == "VIDEO":
                chunk.type = PacketType.VIDEO

            # 计算duration_time（与前一个GET请求的时间间隔）
            if prev_get_time is not None:
                chunk.duration_time = get_time - prev_get_time

            # 添加到流中
            current_stream.chunks.append(chunk)
            prev_get_time = get_time

    return stream_map



