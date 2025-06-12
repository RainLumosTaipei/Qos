from enum import Enum

DOWN_MIN_PAYLOAD = 80 * 1024


class PacketType(Enum):
    AUDIO = 0
    VIDEO = 1
    BG = 2


# 下行chunk
class Chunk:
    #   <--                           duration                          -->
    #   GET   first_byte_wait   start    download        end   slack    GET
    #    |                        |                       |              |
    #    +------------------------+-----------------------+--------------+
    def __init__(self, get_time):
        self.size = 0
        self.start = 0
        self.end = 0
        self.request_time = get_time  # Get请求时间
        self.first_byte_wait_time = 0  # GET请求和收到的第一个包之间的持续时间
        self.download_time = 0  # 从第一个数据包到最后一个数据包之间的时间
        self.slack_time = 0  # 上次最后接收到的包到下一次GET请求之间的时间
        self.duration_time = 0  # 两个连续的GET请求之间的时间间隔
        self.type = PacketType.BG


class IpStream:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        self.chunks = []
        self.chunk = Chunk(0)
        self.isDown = False

    def save_chunk(self, next_get_time):
        if self.chunk.size > DOWN_MIN_PAYLOAD:
            self.chunk.download_time = self.chunk.end - self.chunk.start
            self.chunk.slack_time = next_get_time - self.chunk.end
            self.chunk.duration_time = next_get_time - self.chunk.request_time
            self.chunks.append(self.chunk)
        self.isDown = False
        self.chunk = Chunk(next_get_time)

    def add_chunk(self, time, size):
        if not self.isDown:
            self.isDown = True
            self.chunk.start = time
            self.chunk.first_byte_wait_time = time - self.chunk.request_time
        self.chunk.size += size
        self.chunk.end = time

    def judge_type(self):
        if len(self.chunks) == 0: return

        chunk_size = 0
        for chunk in self.chunks:
            chunk_size += chunk.size
        chunk_avg_size = chunk_size / len(self.chunks)

        for chunk in self.chunks:
            if chunk.size > chunk_avg_size:
                chunk.type = PacketType.VIDEO
            else:
                chunk.type = PacketType.AUDIO
