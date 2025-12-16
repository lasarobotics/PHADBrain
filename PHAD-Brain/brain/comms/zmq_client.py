from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import time
import zmq

from .protocol import encode_packet, decode_packet, now_s


@dataclass
class ZMQConfig:
    """
    Patterns supported:
      - PUB/SUB (one-to-many streaming)
      - REQ/REP (simple request/response)
      - PUSH/PULL (pipeline)
    """
    mode: str = "pubsub"  # "pubsub" | "reqrep" | "pushpull"
    bind: bool = False

    # endpoints
    tx_endpoint: str = "tcp://*:5809"          # bind-side tx
    rx_endpoint: str = "tcp://127.0.0.1:5809"  # connect-side rx

    # optional topic (PUB/SUB)
    topic: str = "PHAD"


class ZMQClient:
    """
    Optional low-latency transport if you ever want to bypass NT4 for some messages.
    (But NT4 is usually fine for FRC.)
    """

    def __init__(self, cfg: ZMQConfig):
        self.cfg = cfg
        self._ctx = zmq.Context.instance()

        self._sock_tx = None
        self._sock_rx = None

        if cfg.mode == "pubsub":
            self._setup_pubsub()
        elif cfg.mode == "reqrep":
            self._setup_reqrep()
        elif cfg.mode == "pushpull":
            self._setup_pushpull()
        else:
            raise ValueError(f"Unknown ZMQ mode: {cfg.mode}")

    # -----------------------------
    # Setup
    # -----------------------------
    def _setup_pubsub(self):
        if self.cfg.bind:
            self._sock_tx = self._ctx.socket(zmq.PUB)
            self._sock_tx.bind(self.cfg.tx_endpoint)
        else:
            self._sock_rx = self._ctx.socket(zmq.SUB)
            self._sock_rx.connect(self.cfg.rx_endpoint)
            self._sock_rx.setsockopt_string(zmq.SUBSCRIBE, self.cfg.topic)

    def _setup_reqrep(self):
        if self.cfg.bind:
            self._sock_rx = self._ctx.socket(zmq.REP)
            self._sock_rx.bind(self.cfg.tx_endpoint)
        else:
            self._sock_tx = self._ctx.socket(zmq.REQ)
            self._sock_tx.connect(self.cfg.rx_endpoint)

    def _setup_pushpull(self):
        if self.cfg.bind:
            self._sock_rx = self._ctx.socket(zmq.PULL)
            self._sock_rx.bind(self.cfg.tx_endpoint)
        else:
            self._sock_tx = self._ctx.socket(zmq.PUSH)
            self._sock_tx.connect(self.cfg.rx_endpoint)

    # -----------------------------
    # Send / Receive
    # -----------------------------
    def send(self, payload: Any) -> None:
        if self._sock_tx is None:
            raise RuntimeError("This ZMQClient is not configured with a TX socket.")
        data = encode_packet(payload)

        if self.cfg.mode == "pubsub":
            self._sock_tx.send_multipart([self.cfg.topic.encode("utf-8"), data])
        else:
            self._sock_tx.send(data)

    def recv(self, timeout_ms: int = 0) -> Optional[Dict[str, Any]]:
        if self._sock_rx is None:
            raise RuntimeError("This ZMQClient is not configured with an RX socket.")

        if timeout_ms > 0:
            poller = zmq.Poller()
            poller.register(self._sock_rx, zmq.POLLIN)
            events = dict(poller.poll(timeout_ms))
            if self._sock_rx not in events:
                return None

        if self.cfg.mode == "pubsub":
            parts = self._sock_rx.recv_multipart()
            if len(parts) != 2:
                return None
            _, data = parts
        else:
            data = self._sock_rx.recv()

        return decode_packet(data)

    # -----------------------------
    # Convenience: req/rep
    # -----------------------------
    def request(self, payload: Any, timeout_ms: int = 200) -> Optional[Dict[str, Any]]:
        """
        Only for reqrep mode on the client side.
        """
        if self.cfg.mode != "reqrep":
            raise RuntimeError("request() only valid for reqrep mode.")

        self.send(payload)
        # Wait for reply
        t0 = time.time()
        while (time.time() - t0) * 1000.0 < timeout_ms:
            rep = self.recv(timeout_ms=10)
            if rep is not None:
                return rep
        return None
