
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union

@dataclass
class NetworkInfo:
    src_ip: str
    dst_ip: str
    protocol: Optional[str] = 0
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0

@dataclass
class PlaybackInfo:
    playback_event: List[int]  # buffering, paused, playing, collect data
    playback_event_type: int  # 0 1 2 3
    epoch_time: int # long
    start_time: int
    playback_progress: float
    video_length: float
    playback_quality: List[int] # non, tiny (144p), small (240p), medium (360p), large (480p),
                                # hd720, hd1080, hd1440, hd2160
    playback_quality_type: int # 0 1 2 3 4 5 6 7 8
    buffer_health: float
    buffer_warning: int         # 0表示大于20s,1表示小于20s
    buffer_progress: float      # null
    buffer_valid: Optional[bool] = -1  # -1, true, false

@dataclass
class Metric:
    relative_time: float
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    networks: List[NetworkInfo] = field(default_factory=list)
    playback: PlaybackInfo = field(default_factory=PlaybackInfo)