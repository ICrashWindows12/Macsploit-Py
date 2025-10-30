import asyncio
import struct
from enum import IntEnum


class IpcTypes(IntEnum):
    IPC_EXECUTE = 0
    IPC_SETTING = 1


class MessageTypes(IntEnum):
    PRINT = 1
    ERROR = 2


class Client:
    def __init__(self, host="127.0.0.1", port=5553):
        self._host = host
        self._port = port
        self._reader = None
        self._writer = None

    async def attach(self, port=None):
        if port:
            self._port = port

        if self._writer is not None:
            raise RuntimeError("AlreadyInjectedError: Socket is already connected.")

        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        print(f"[+] Connected to {self._host}:{self._port}")

        asyncio.create_task(self._listen())

    async def detach(self):
        if not self._writer:
            raise RuntimeError("NotInjectedError: Socket is already closed.")

        self._writer.close()
        await self._writer.wait_closed()
        self._reader = self._writer = None
        print("[+] Connection closed.")

    async def _listen(self):
        try:
            while True:
                # Read header (16 bytes minimum)
                header = await self._reader.readexactly(16)
                if not header:
                    break

                msg_type = header[0]
                length = struct.unpack("<Q", header[8:16])[0]

                message_bytes = await self._reader.readexactly(length)
                message = message_bytes.decode("utf-8")

                if msg_type == MessageTypes.PRINT:
                    print(f"[PRINT] {message}")
                elif msg_type == MessageTypes.ERROR:
                    print(f"[ERROR] {message}")
                else:
                    print(f"[?] Unknown message type {msg_type}: {message}")
        except asyncio.IncompleteReadError:
            print("[!] Connection closed by remote host.")

    def _build_header(self, type_: IpcTypes, length: int = 0) -> bytearray:
        data = bytearray(16)
        data[0] = type_
        struct.pack_into("<Q", data, 8, length)
        return data

    def execute_script(self, script: str):
        if not self._writer:
            raise RuntimeError("NotInjectedError: Please attach before executing scripts.")

        encoded = script.encode("utf-8")
        header = self._build_header(IpcTypes.IPC_EXECUTE, len(encoded))
        self._writer.write(header + encoded)

    def update_setting(self, key: str, value: bool):
        if not self._writer:
            raise RuntimeError("NotInjectedError: Please attach before updating settings.")

        payload = f"{key} {'true' if value else 'false'}".encode("utf-8")
        header = self._build_header(IpcTypes.IPC_SETTING, len(payload))
        self._writer.write(header + payload)


async def main():
    client = Client()
    await client.attach(5553) # port change port to whatever from 5553-5563

    # To send your "script" (the same thing as in JS)
    script = 'print("Hello from Python!")' # CHANGE THIS TO LOADSTRING SCRIPT 
    client.execute_script(script)

    # Optional: update setting example
    client.update_setting("auto_attach", True)

    # Keep alive
    await asyncio.sleep(5)
    await client.detach()

if __name__ == "__main__":
    asyncio.run(main())
# NOTE: to change script go to script = 'print("Hello from Python!")' and change the value
# Use chatgpt lol from Munq's original JS script shoutout to him I guess for providing the structure
# Enjoy! (it works trust me bro)
