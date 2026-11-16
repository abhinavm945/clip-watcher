"""
Anonymous Twitch IRC chat reader.
Connects to public Twitch chat anonymously without user credentials or OAuth tokens.
"""

import random
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


class TwitchChatListener:
    def __init__(
        self,
        channel: str,
        log_file: Path = Path("chat.log"),
        on_message: Optional[Callable[[datetime, str, str], None]] = None,
        host: str = "irc.chat.twitch.tv",
        port: int = 6667,
    ):
        self.channel = channel.lower().lstrip("#")
        self.log_file = log_file
        self.on_message = on_message
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.nick = f"justinfan{random.randint(10000, 99999)}"

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass

    def _run(self):
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        while self._running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                
                self._send("PASS oauth:none")
                self._send(f"NICK {self.nick}")
                self._send(f"USER {self.nick} 0 * :{self.nick}")
                self._send("CAP REQ :twitch.tv/tags twitch.tv/commands")
                self._send(f"JOIN #{self.channel}")

                buffer = ""
                while self._running:
                    data = self.sock.recv(4096).decode("utf-8", errors="ignore")
                    if not data:
                        break
                    
                    buffer += data
                    lines = buffer.split("\r\n")
                    buffer = lines.pop()

                    for line in lines:
                        if line.startswith("PING"):
                            pong = line.replace("PING", "PONG", 1)
                            self._send(pong)
                        elif "PRIVMSG" in line:
                            self._handle_privmsg(line)

            except Exception:
                if self._running:
                    time.sleep(5)
            finally:
                if self.sock:
                    try:
                        self.sock.close()
                    except Exception:
                        pass

    def _send(self, msg: str):
        if self.sock:
            self.sock.sendall(f"{msg}\r\n".encode("utf-8"))

    def _handle_privmsg(self, line: str):
        try:
            sender = "anonymous"
            if "!" in line and "PRIVMSG" in line:
                prefix = line.split("PRIVMSG")[0]
                if "!" in prefix:
                    sender = prefix.split("!")[0].split(":")[-1].strip()

            content = ""
            if " PRIVMSG #" in line:
                after_privmsg = line.split(" PRIVMSG #", 1)[1]
                if " :" in after_privmsg:
                    content = after_privmsg.split(" :", 1)[1].strip()
                else:
                    content = after_privmsg.strip()
            elif "PRIVMSG" in line:
                parts = line.split("PRIVMSG", 1)[1]
                content = parts.split(":", 1)[1].strip() if ":" in parts else parts.strip()

            now = datetime.now(timezone.utc)
            ts_str = now.isoformat()

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts_str}] <{sender}> {content}\n")

            if self.on_message:
                self.on_message(now, sender, content)
        except Exception:
            pass
