# LightLightShowXL

LightLightShowXL est une application de contrôle d'éclairage musical avancée qui synchronise des fixtures DMX avec l'audio en temps réel. L'application analyse l'audio entrant, détecte les kicks et autres éléments musicaux, puis contrôle automatiquement les fixtures d'éclairage selon des thèmes et couleurs prédéfinis.

## Fonctionnalités principales

### 🎵 Analyse audio en temps réel
- Détection automatique des kicks et des éléments rythmiques
- Support des périphériques audio d'entrée et de sortie
- Analyse spectrale pour la synchronisation musicale

### 💡 Contrôle d'éclairage
- Support complet des fixtures DMX
- Configuration flexible des fixtures (types, canaux, adresses DMX)
- Système de thèmes et couleurs personnalisables
- Monitoring en temps réel des fixtures

### 🎨 Thèmes et couleurs
- Séquences de couleurs pour l'éclairage de base
- Couleurs spéciales pour les kicks détectés
- Thèmes prédéfinis : Feu d'artifice, Coucher de Soleil, Arc-en-ciel, etc.
- Éditeur de couleurs et thèmes intégré

### ⚙️ Configuration avancée
- Interface graphique pour la configuration des fixtures
- Gestion des adresses DMX automatique
- Support de multiples types de fixtures (PAR, Moving Head, Wash, etc.)
- Validation complète des configurations

## Installation

### Prérequis
- Python 3.8 ou supérieur
- Windows (testé sur Windows 10/11)

### Dépendances
```bash
pip install tkinter sounddevice librosa numpy numba threading json
```

### Installation
1. Clonez le repository :
```bash
git clone https://github.com/votre-username/LightLightShowXL.git
cd LightLightShowXL
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancez l'application :
```bash
python main.py
```

## Structure du projet

```
LightLightShowXL/
├── main.py                    # Point d'entrée principal
├── views/                     # Interfaces utilisateur
│   ├── main_view.py          # Vue principale
│   ├── fixtures_view.py      # Monitoring des fixtures
│   ├── Fixtures_config.py    # Configuration des fixtures
│   ├── Themes_and_colors_config.py  # Configuration thèmes/couleurs
│   ├── audiodevice_view.py   # Sélection périphériques audio
│   └── start_view.py         # Bouton de démarrage
├── audio/                    # Modules d'analyse audio
│   ├── analyzer.py           # Analyseur audio principal
│   └── output.py            # Sortie audio
├── dmx/                      # Contrôle DMX
│   └── mainboard.py         # Contrôleur principal DMX
├── fixtures/                 # Configuration des fixtures
│   └── fixtures.json        # Définitions des fixtures
├── themes/                   # Thèmes et couleurs
│   ├── colors.json          # Définitions des couleurs
│   └── themes.json          # Définitions des thèmes
└── build/                   # Fichiers de build (PyInstaller)
```

## Configuration

### Fixtures
Les fixtures sont configurées dans [`fixtures/fixtures.json`](fixtures/fixtures.json). Chaque fixture définit :
- **name** : Nom de la fixture
- **type** : Type (par, moving_head, wash, beam, spot, strobe, laser, smoke)
- **manufacturer** : Fabricant
- **dmx_address** : Adresse DMX de départ
- **channel_count** : Nombre de canaux DMX
- **channels** : Configuration des canaux (rouge, vert, bleu, etc.)
- **kick_respond** : Si la fixture répond aux kicks détectés

Exemple :
```json
{
  "Par_LED_1": {
    "name": "Par LED 1",
    "type": "par",
    "manufacturer": "Generic",
    "dmx_address": 1,
    "channel_count": 4,
    "channels": {
      "red": {"id": 1, "default": 0, "min": 0, "max": 255},
      "green": {"id": 2, "default": 0, "min": 0, "max": 255},
      "blue": {"id": 3, "default": 0, "min": 0, "max": 255},
      "white": {"id": 4, "default": 0, "min": 0, "max": 255}
    },
    "kick_respond": true
  }
}
```

### Couleurs
Les couleurs sont définies dans [`themes/colors.json`](themes/colors.json) :
```json
{
  "red": {"red": 255, "green": 0, "blue": 0},
  "green": {"red": 0, "green": 255, "blue": 0},
  "blue": {"red": 0, "green": 0, "blue": 255}
}
```

### Thèmes
Les thèmes sont configurés dans [`themes/themes.json`](themes/themes.json) :
```json
{
  "Feu d'artifice": {
    "sequence": ["red", "yellow", "green", "blue", "white"],
    "kick": ["white", "yellow"]
  }
}
```

## Utilisation

### Démarrage rapide
1. Lancez l'application avec `python main.py`
2. Sélectionnez vos périphériques audio d'entrée et de sortie
3. Cliquez sur "Start" pour commencer l'analyse audio
4. L'éclairage se synchronise automatiquement avec la musique

### Configuration des fixtures
1. Cliquez sur "Config Fixtures" dans l'interface principale
2. Ajoutez, modifiez ou supprimez des fixtures
3. Configurez les adresses DMX et les canaux
4. Sauvegardez la configuration

### Configuration des thèmes
1. Cliquez sur "Config Thèmes" dans l'interface principale
2. Créez de nouvelles couleurs ou modifiez les existantes
3. Définissez des séquences de couleurs pour vos thèmes
4. Assignez des couleurs spéciales pour les kicks

### Monitoring
- Cliquez sur "Fixtures Window" pour ouvrir une fenêtre de monitoring
- Visualisez en temps réel l'état de chaque fixture
- Les indicateurs de statut montrent l'activité (vert=prêt, rouge=kick actif, gris=inactif)

## API et Architecture

### MainBoard
Le [`MainBoard`](dmx/mainboard.py) est le contrôleur central qui :
- Gère les fixtures et leurs états
- Applique les thèmes et couleurs
- Synchronise avec l'analyse audio
- Gère les séquences et les kicks

### AudioAnalyzer
L'[`AudioAnalyzer`](audio/analyzer.py) fournit :
- Analyse spectrale en temps réel
- Détection des kicks et éléments rythmiques
- Interface avec les périphériques audio

## Développement

### Ajout de nouveaux types de fixtures
1. Modifiez la liste des types dans [`Fixtures_config.py`](views/Fixtures_config.py)
2. Ajoutez la logique de contrôle dans [`mainboard.py`](dmx/mainboard.py)
3. Testez avec des fixtures réelles

### Personnalisation des algorithmes d'analyse
- Modifiez [`analyzer.py`](audio/analyzer.py) pour ajuster la détection des kicks
- Configurez les seuils et paramètres d'analyse
- Testez avec différents styles musicaux

## Build et Distribution

Pour créer un exécutable :
```bash
pyinstaller main.py --onefile --windowed
```

Les fichiers de build se trouvent dans le dossier [`build/`](build/).

## Dépannage

### Problèmes audio
- Vérifiez que les périphériques audio sont correctement connectés
- Testez avec différents périphériques d'entrée/sortie
- Vérifiez les permissions audio de l'application

### Problèmes DMX
- Vérifiez les adresses DMX dans la configuration
- Assurez-vous qu'il n'y a pas de conflits d'adresses
- Testez avec des fixtures simples d'abord

### Performance
- Réduisez le nombre de fixtures simultanées si nécessaire
- Ajustez la fréquence de mise à jour dans les vues
- Vérifiez les performances audio avec différents buffer sizes

## Contributions

Les contributions sont les bienvenues ! Veuillez :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Committer vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Auteurs

- Votre nom - Développeur principal

## Remerciements

- Communauté Python pour les excellentes bibliothèques
- Contributeurs et testeurs
- Utilisateurs pour leurs retours et suggestions