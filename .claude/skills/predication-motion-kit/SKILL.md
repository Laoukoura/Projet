---
name: predication-motion-kit
description: Monte une prédication verticale (TikTok/Reels, 1080x1920) au style « sombre teinté rouge + motion design » de MBAIDADJE TIMOTHE — rush plein écran étalonné, sphères rouges flottantes, particules, gros titres blancs animés mot par mot avec sur-titre italique, sous-titres mot par mot calés à la syllabe sur la voix, flashs aux changements de scène, et écrans graphiques (texte contour lumineux, courbes, verset qui s'écrit, bouclier, cible, pastilles). Utilise CE skill dès que l'utilisateur envoie un rush de prédication + son texte et demande de « monter », « habiller » la vidéo « comme les précédentes », « avec le motion design », « style sombre et rouge », ou « comme la vidéo de référence ».
---

# Kit « Prédication Motion » (sombre & rouge)

Pipeline en 5 étapes, piloté par un seul fichier `config.json` placé dans un dossier de travail (ex. `/home/claude/job`). Toutes les commandes se lancent depuis ce dossier avec `KIT_CFG=config.json` (valeur par défaut). `K=/chemin/du/skill/scripts`.

**Le texte est indispensable** : aucun outil de transcription n'est disponible hors ligne. Si l'utilisateur n'envoie pas le texte, le lui demander (sous-titres auto de CapCut, ou dictée) — ne jamais inventer les paroles. Si le réseau est ouvert, on peut installer Whisper pour transcrire, puis corriger avec lui.

Contrainte d'environnement : chaque commande est limitée à ~300 s et les processus en arrière-plan sont tués. D'où le découpage en lots ci-dessous (1 CPU, rush 4K HEVC).

## Étape 1 — Analyse du rush
1. Écrire un `config.json` minimal (`raw_video`, `start`, `end`, `scenes`) — voir `references/exemple_config.json`.
2. `python3 $K/prepare.py` → durée, `sil.txt`, `a16.wav`, `audio.m4a`, `face_check.png`.
3. Regarder `face_check.png` pour choisir le cadrage (étape 3).

## Étape 2 — Découpage du texte et alignement
- Découper le texte en **scènes** de 1 à 2 phrases (~3–10 s). Phrase-choc seule = scène seule.
- Hésitations / répétitions / « euh » : les garder dans le texte mais préfixer chaque mot par `~` (ex. `~de ~te, de ton travail`) → comptés pour le rythme, jamais affichés. Les [rires] s'omettent.
- Corriger l'orthographe dans le texte (les sous-titres l'affichent tel quel).
- `python3 $K/align.py` → `wt.json` + tableau « segment de voix | n=syllabes détectées s=syllabes du texte | mots ». Si n≈s sur la plupart des lignes, l'alignement est bon. Gros écarts répétés = texte ne correspondant pas à l'audio : vérifier avec l'utilisateur.

## Étape 3 — Habillage (config) puis étalonnage
Compléter `config.json` (détails dans `references/config.md`) :
- `heads` : un titre (sur-titre italique minuscule + titre MAJUSCULE, 1–2 lignes, ≤ ~18 caractères/ligne) pour chaque passage où le visage est à l'écran.
- `gfx` : 5 à 7 écrans graphiques plein cadre sur les moments forts (une par idée-clé, jamais deux d'affilée du même type si possible).
- `key_words` : mots affichés en gros et en rouge dans les sous-titres.
- `framing` : règle d'or **aucun texte sur le visage** — titre au-dessus de la tête, sous-titres sur la poitrine.
  - visage moyen/centré → `{"mode":"full","face_y":0.40}`
  - tête haute dans l'image → `{"mode":"full","face_y":0.33–0.36,"pad_top":260}` (descend l'image, fond flouté en haut)
  - visage très gros / filmé de près → `{"mode":"inset","zooms":[0.80,0.88],"top":260}` + `"caption_y":1560`
  - image sombre (intérieur) → `"grade":"bright"`
- Puis : `python3 $K/proxy.py 0 1 2 3 4` (lots de 4–6 scènes par appel, `timeout 290`), ensuite `python3 $K/proxy.py concat` → `base.mp4` (durée = end − start).

## Étape 4 — Calques animés
- Tester 3–5 instants : `python3 -c "import sys;sys.path.insert(0,'$K');import render_states as R;R.render_state(T).save('t.png')"` et vérifier (composer sur une image de `base.mp4` si besoin).
- Rendu par lots : `python3 $K/render_states.py 0 130`, puis `130 270`, etc. (~130 états par appel). La 1re ligne affiche le nombre total d'états.

## Étape 5 — Composition
`timeout 295 python3 $K/compose.py /mnt/user-data/outputs/<nom>.mp4` → contrôler 8–10 images (planche), puis `present_files`.

## Après livraison
Décrire en quelques lignes les écrans graphiques utilisés et tout choix notable (cadrage modifié, orthographe corrigée, hésitations masquées). Proposer d'ajuster une phrase décalée ou un titre.
