# Référence config.json

| clé | rôle |
|---|---|
| `raw_video` | chemin du rush |
| `start` / `end` | début (≈0.9) et fin (un peu avant la durée réelle) en secondes du rush |
| `grade` | `normal` (extérieur) ou `bright` (intérieur sombre) |
| `framing` | voir SKILL.md étape 3 |
| `caption_y` | hauteur des sous-titres (1500 défaut, 1560 en mode inset) |
| `signature` | texte italique final (défaut « Une vie au cœur de l'impact ») |
| `flat_labels` | étiquettes de la courbe `flat` (défaut jan→juin) |
| `scenes` | liste `{"text": ...}` — mots `~` masqués |
| `key_words` | mots en gros/rouge dans les sous-titres (minuscules, apostrophe incluse : `l'éternel`) |
| `heads` | `{"from","to","kicker","title"}` — `\n` pour 2 lignes |
| `gfx` | `{"from","to","kind","kicker","title"}` (+ `pills`) |

## Ancres temporelles (`from` / `to`)
- `"S3"` : début de la scène 3 (index à partir de 0)
- `"S3:parce"` : juste avant le 1er mot de la scène 3 qui commence par « parce »
- `"S3:si#1"` : 2e occurrence (compte à partir de 0)
- `"END"` : fin de la vidéo
Le mot doit exister tel qu'écrit dans `text` (début du mot, insensible à la casse, `~` compris).
Un titre et un écran ne doivent pas se chevaucher : l'écran prend le relais à son ancre `from`.

## Types d'écrans (`kind`)
| kind | rendu | quand |
|---|---|---|
| `outline` | très gros texte en contour lumineux rouge, arrivée en zoom | mot-choc (POURQUOI ?, PATIENCE, LA CROIX) |
| `up` | carte verre + courbe verte qui monte | fruits, croissance, victoire |
| `down` | courbe rouge qui descend | échec, impatience, difficultés |
| `flat` | ligne plate avec 6 étiquettes | stagnation, « rien ne bouge », routine |
| `wave` | zigzag rouge | hauts et bas, « la vie est faite de problèmes » |
| `verse` | carte verset : icône Bible, texte qui s'écrit lettre par lettre ; `kicker` = référence (ex. « Philippiens 4 : 7 ») ; `title` = le verset | citation biblique (Louis Segond 1910 si cité mot pour mot ; sinon « Jésus à Gethsémané » etc.) |
| `shield` | bouclier + coche qui se dessine | protection, promesse, « Dieu est de ton côté » |
| `target` | cible qui apparaît + flèche plantée au centre | but, objectif, vision |
| `pills` | 3 pastilles qui s'allument au mot prononcé — ajouter `"pills":[{"label":"FORCE","at":"S7:force"}, …]` (un seul écran pills par vidéo) | énumération |

## Habitudes de MBAIDADJE TIMOTHE
- Fin : titre « NE L'OUBLIE PAS » (sur-titre « retiens bien ») ou déclaration « AU NOM DE JÉSUS-CHRIST », + signature.
- Titres courts et percutants, sur-titres qui reprennent le début de sa phrase.
- Jamais de texte sur le visage ; le visage reste centré et pas trop zoomé.
