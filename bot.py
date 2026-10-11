import os
import re
import json
import base64
import msgpack
from io import BytesIO
from Crypto.Cipher import AES
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "TON_TOKEN_ICI")

# Tes paramètres fixes (ceux de ton lien VLESS)
UUID = "d8a6b1c2-3f4e-4a5b-8c9d-1e2f3a4b5c6d"
IP = "192.179.18.100"
PORT = 443
SNI = "crashlyticsreports-pa.googleapis.com"
PATH = "/@kcorp237"
REMARK = "@KCORP-TECH"

# Clés DarkTunnel (ne pas modifier)
KEY_256 = b"$B&E)H@McQfThWmZq4t7w!z%C*F-JaNd"
KEY_192 = b"F)J@NcRfUjXn2r4u7x!A%D*G"
IV = bytes.fromhex("232e39185523184a5723586242200e05")
# ================================================


def aes_encrypt(data: bytes, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CFB, IV, segment_size=128)
    return cipher.encrypt(data)


def extraire_host(texte: str) -> str | None:
    """Extrait le host Cloud Run depuis n'importe quel texte/lien"""
    texte = texte.strip()
    match = re.search(r"([a-z0-9\-]+\.[a-z0-9\-]+\.run\.app)", texte, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    if "run.app" in texte.lower() and " " not in texte:
        host = texte.lower().replace("https://", "").replace("http://", "").split("/")[0]
        if host.endswith(".run.app"):
            return host
    return None


def generer_config_xray(host: str) -> str:
    """Génère le JSON Xray/VLESS interne de DarkTunnel"""
    config = {
        "inbounds": [
            {
                "listen": "$SOCKS5_LISTEN_HOST",
                "port": "$SOCKS5_LISTEN_PORT",
                "protocol": "socks",
                "settings": {"auth": "noauth", "udp": True, "userLevel": 8},
            },
            {
                "listen": "$HTTP_LISTEN_HOST",
                "port": "$HTTP_LISTEN_PORT",
                "protocol": "http",
                "settings": {"userLevel": 8},
            },
        ],
        "log": {"loglevel": "none"},
        "outbounds": [
            {
                "mux": {"concurrency": 8, "enabled": "$MUX_ENABLED"},
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": IP,
                            "port": PORT,
                            "users": [
                                {
                                    "encryption": "none",
                                    "id": UUID,
                                    "flow": "",
                                    "level": 8,
                                    "security": "chacha20-poly1305",
                                }
                            ],
                        }
                    ]
                },
                "streamSettings": {
                    "network": "ws",
                    "security": "tls",
                    "tlsSettings": {
                        "allowInsecure": True,
                        "serverName": SNI,
                    },
                    "wsSettings": {
                        "headers": {"Host": host},
                        "path": PATH,
                    },
                },
            }
        ],
        "policy": {
            "levels": {
                "8": {
                    "connIdle": 300,
                    "downlinkOnly": 1,
                    "handshake": 4,
                    "uplinkOnly": 1,
                }
            },
            "system": {
                "statsOutboundUplink": False,
                "statsOutboundDownlink": False,
            },
        },
        "stats": {},
    }
    return json.dumps(config, separators=(",", ":"))


def generer_dark_file(host: str, name: str = REMARK) -> bytes:
    """Génère un vrai fichier .dark ouvert (non verrouillé)"""

    inner = {
        "InjectConfig": {
            "IsEncrypted": True,
            "EncryptedMode": aes_encrypt(b"DIRECT", KEY_192),
            "EncryptedProxyHost": aes_encrypt(b"localhost", KEY_192),
            "EncryptedProxyPort": aes_encrypt(b"8080", KEY_192),
            "EncryptedServerNameIndication": aes_encrypt(b"", KEY_192),
            "EncryptedPayload": aes_encrypt(
                b"[method] [host_port] [protocol][crlf]Host: [host][crlf]Service: SSH[crlf]Mode: Bypass[crlf][crlf]",
                KEY_192,
            ),
            "EncryptedDnsttDnsHost": aes_encrypt(b"1.1.1.1", KEY_192),
            "EncryptedDnsttDnsPort": aes_encrypt(b"53", KEY_192),
            "EncryptedDnsttServerName": aes_encrypt(b"", KEY_192),
            "EncryptedDnsttPubkey": aes_encrypt(b"", KEY_192),
        },
        "SshConfig": {
            "IsEncrypted": True,
            "IsLocked": True,
            "EncryptedHost": aes_encrypt(b"", KEY_192),
            "EncryptedPort": aes_encrypt(b"80", KEY_192),
            "EncryptedUsername": aes_encrypt(b"", KEY_192),
            "EncryptedPassword": aes_encrypt(b"", KEY_192),
        },
        "V2RayConfig": {
            "IsEncrypted": True,
            "IsInjectModeEnabled": False,
            "EncryptedConfig": aes_encrypt(generer_config_xray(host).encode("utf-8"), KEY_192),
        },
    }

    inner_packed = msgpack.packb(inner, use_bin_type=True)
    encrypted_inner = aes_encrypt(inner_packed, KEY_192)

    outer_msgpack = {
        "LockedAppConfig": {
            "VersionCode": 0,
            "VersionName": "",
            "Message": "",
            "ConnectedMessage": "",
            "Password": "",
            "ExpiredAtTimestamp": 0,
            "HardwareIdList": [],
            "TunnelType": "VLESS",
            "IsSshLocked": False,
        },
        "EncryptedLockedConfig": encrypted_inner,
    }

    outer_packed = msgpack.packb(outer_msgpack, use_bin_type=True)
    encrypted_outer = aes_encrypt(outer_packed, KEY_256)

    final = {
        "type": "VLESS",
        "name": name,
        "encryptedLockedConfig": base64.urlsafe_b64encode(encrypted_outer).decode("utf-8").rstrip("="),
    }

    payload = base64.b64encode(json.dumps(final, separators=(",", ":")).encode("utf-8")).decode("utf-8")
    content = f"darktunnel://{payload}"
    return content.encode("utf-8")


def generer_lien_vless(host: str) -> str:
    path_encoded = PATH.replace("/", "%2F")
    return (
        f"vless://{UUID}@{IP}:{PORT}"
        f"?encryption=none"
        f"&security=tls"
        f"&sni={SNI}"
        f"&type=ws"
        f"&host={host}"
        f"&path={path_encoded}"
        f"#{REMARK}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *KCORP DarkTunnel Bot*\n\n"
        "Envoie-moi le lien de ta console Cloud Run.\n\n"
        "Je vais automatiquement :\n"
        "• Extraire le nouveau host\n"
        "• Régénérer le lien VLESS\n"
        "• Générer un fichier `.dark` ouvert\n\n"
        "Exemple :\n"
        "`https://xxxxx-xxxxx.us-central1.run.app`",
        parse_mode="Markdown",
    )


async def traiter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte = update.message.text or ""
    host = extraire_host(texte)

    if not host:
        await update.message.reply_text(
            "❌ Aucun host Cloud Run détecté (doit contenir `.run.app`).\n\n"
            "Envoie le lien de ta console qui contient le host."
        )
        return

    lien = generer_lien_vless(host)
    dark_bytes = generer_dark_file(host)
    filename = f"KCORP-TECH-{host.split('.')[0]}.dark"

    await update.message.reply_text(
        f"✅ *Host détecté :*\n`{host}`\n\n"
        f"🔗 *Lien VLESS régénéré :*\n`{lien}`",
        parse_mode="Markdown",
    )

    await update.message.reply_document(
        document=InputFile(BytesIO(dark_bytes), filename=filename),
        caption=(
            f"📁 *Fichier DarkTunnel ouvert*\n\n"
            f"Host : `{host}`\n"
            f"→ Config → Import → File dans DarkTunnel"
        ),
        parse_mode="Markdown",
    )


def main():
    if not BOT_TOKEN or BOT_TOKEN == "TON_TOKEN_ICI":
        print("❌ Erreur : BOT_TOKEN non défini")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, traiter))

    print("🚀 Bot KCORP DarkTunnel démarré...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
