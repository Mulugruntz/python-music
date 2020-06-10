from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Channel:
    name: str
    channel_score: str

@dataclass
class Score:
    channels: List[Channel]
    bpm: int
    time_signature: Tuple[int, int]

