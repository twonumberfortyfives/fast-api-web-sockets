import asyncio
import base64
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

cipher = Fernet(os.getenv("ENCRYPTION_KEY"))


async def encrypt_message(message: str) -> bytes:
    return cipher.encrypt(message.encode())


async def decrypt_message(encrypted_message: bytes) -> str:
    return cipher.decrypt(encrypted_message).decode()


async def main():
    message = "Helloo ssdlsdöö"
    encrypted_message = await encrypt_message(message)

    encoded_data = base64.b64encode(encrypted_message).decode("utf-8")
    encoded_data_in_bytes = base64.b64decode(encoded_data.encode("utf-8"))

    decrypted_message = await decrypt_message(encoded_data_in_bytes)
    print(encrypted_message)
    print(decrypted_message)


if __name__ == "__main__":
    asyncio.run(main())
