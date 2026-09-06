"""Single-instance handshake (SPEC §10.3): second launch forwards argv to the
running instance over a localhost TCP port, then exits.

TCP instead of QLocalServer named pipes: Windows allows multiple named-pipe
server instances on one name, which silently steals connections from zombie
processes; a localhost port can only be bound by a live process. An ACK round
trip guards against a foreign service squatting on the port.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket

PORT = 47654  # xvg-plotter single-instance port (unassigned IANA range)


class SingleInstance(QObject):
    message = Signal(list)

    def __init__(self):
        super().__init__()
        self.is_primary = False
        self._srv = QTcpServer()
        if self._srv.listen(QHostAddress(QHostAddress.SpecialAddress.LocalHost), PORT):
            self.is_primary = True
            self._srv.newConnection.connect(self._accept)

    def send(self, argv: list[str]) -> bool:
        """Forward argv to the primary; True only if it ACKed."""
        sock = QTcpSocket()
        sock.connectToHost(QHostAddress(QHostAddress.SpecialAddress.LocalHost), PORT)
        if not sock.waitForConnected(500):
            return False
        sock.write(json.dumps(argv).encode() + b"\n")
        sock.flush()
        ok = sock.waitForReadyRead(1000) and bytes(sock.readAll()).strip() == b"ok"
        sock.disconnectFromHost()
        return ok

    def _accept(self) -> None:
        while (sock := self._srv.nextPendingConnection()) is not None:
            sock.readyRead.connect(lambda sk=sock: self._read(sk))

    def _read(self, sock: QTcpSocket) -> None:
        data = bytes(sock.readAll()).strip()
        if not data:
            return
        sock.write(b"ok")
        sock.flush()
        try:
            self.message.emit(json.loads(data.decode()))
        except (ValueError, UnicodeDecodeError):
            pass
        sock.disconnectFromHost()
