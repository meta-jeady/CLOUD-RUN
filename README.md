# KCORP DarkTunnel Bot

Bot Telegram qui régénère automatiquement le lien VLESS + un fichier `.dark` ouvert à partir d’un host Cloud Run.

## Déploiement sur Render

1. Crée un repo GitHub avec les 4 fichiers
2. Va sur https://render.com → New → Background Worker
3. Connecte ton repo GitHub
4. Configure :
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `python bot.py`
5. Dans Environment ajoute :
