"""codec/ — 瑶灵体感编解码模块"""

from .sensation_encoder import SensationEncoder, SpineEntry, SpineSnapshot, encode_snapshot, to_protobuf_dict
from .sensation_decoder import SensationDecoder, DownstreamCommand, HistorySnapshot, decode_history_snapshot, decode_downstream_cmd

__all__ = [
    "SensationEncoder", "SpineEntry", "SpineSnapshot", "encode_snapshot", "to_protobuf_dict",
    "SensationDecoder", "DownstreamCommand", "HistorySnapshot", "decode_history_snapshot", "decode_downstream_cmd",
]
