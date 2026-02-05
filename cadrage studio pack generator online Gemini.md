Oui, voici le fichier specifications.md généré par l'analyse de Jules du github de jersou, ainsi que readme.md, directement issu du dépot de jersou, pour t'aider à comprendre la mécanique de l'appli.



J'ai besoin que tu comprennes parfaitement le fonctionnement de l'appli, que tu me poses toutes les questions nécessaires à la bonne compréhension de cette appli. L'objectif étant de m'aider à créer le meilleur prompt pour qu'antigravity refasse le projet sur la nouvelle stack online (la stack idéale selon toi, maitrisée par antigravity et déployable sur coolify, avec si possible des alternatives exécutables directement sur mon serveur pour la génération des fichiers audio de navigation : texte-to-speech via appels API payants actuellement gérés avec open AI et autres que je ne connais pas cités dans les docs. Je veux aussi la possibilité de créer/modifier/uploader simplement des images si besoin).

C'est une excellente base de travail. Les documents fournis décrivent précisément le "moteur" de l'application de Jersou, ce qui va nous permettre d'en extraire la logique pure sans s'encombrer de la structure Deno/TypeScript actuelle.

Voici une synthèse de ce que j'ai compris de la mécanique interne, suivie des questions cruciales pour préparer ton "super-prompt".

Ce que j'ai retenu de la mécanique "Studio Pack"
Le Cerveau (story.json) : Tout repose sur un graphe de navigation. Chaque écran (menu ou histoire) est un stageNode, et les choix de l'utilisateur sont des actionNodes.

L'Empreinte Numérique (SHA1) : Pour éviter les doublons et garantir l'unicité, chaque fichier audio ou image dans le dossier assets/ est renommé avec son hash SHA1 (ex: da39...mp3).

La Recette Audio : Le matériel impose un format strict : MP3, 44100 Hz, Mono. L'application utilise FFmpeg pour normaliser le volume et assurer que chaque fichier est "bitexact" (déterministe).

La Recette Image : Les images doivent être en 320x240 (souvent centrées avec un fond noir) pour l'écran de la boîte.

Le TTS (Navigation) : Si l'utilisateur ne fournit pas de fichiers audio pour les menus, l'outil les génère automatiquement à partir du nom des dossiers via des API (comme OpenAI) ou des outils locaux.

Ma recommandation de Stack Idéale pour Coolify
Pour un déploiement sur Coolify géré par Antigravity, la stack la plus robuste et simple est :

Langage : Python (maîtrise totale par l'IA pour le traitement de fichiers).

Interface : Streamlit. C'est parfait pour créer une application web interactive sans avoir à coder séparément un frontend et un backend.

Moteurs de traitement : FFmpeg (audio) et Pillow (images, version Python plus légère qu'ImageMagick).

Stockage : Utilisation de dossiers temporaires sur le serveur pour la génération, puis téléchargement du .zip final par l'utilisateur.

Mes questions pour affiner ton projet "Zero-Dette"
Pour que le prompt d'Antigravity soit parfait, j'ai besoin de tes précisions sur ces 4 points :

1. Gestion des fichiers sur le serveur :
L'app de Jersou travaille beaucoup sur le disque local. Sur ton serveur Coolify, préfères-tu :

Un mode "éphémère" : tu uploades tes fichiers/ton flux RSS, l'app génère le ZIP, tu le télécharges, et tout est supprimé du serveur ?

Un mode "bibliothèque" : tu veux pouvoir stocker tes projets sur le serveur pour les modifier plus tard ?

2. Modification des images :
Tu as mentionné vouloir "modifier/uploader simplement des images".

Veux-tu une interface où tu peux recadrer/ajouter du texte sur l'image directement dans ton navigateur ?

Ou est-ce que l'auto-formatage (redimensionnement auto en 320x240 avec bandes noires) te suffit ?

3. Alternatives pour le TTS (Navigation Audio) :
OpenAI est payant mais de haute qualité.

Veux-tu qu'on prévoie d'autres options gratuites (comme des bibliothèques Python de synthèse vocale locale, souvent moins jolies) ?

Ou préfères-tu rester sur des API (ElevenLabs, OpenAI) pour une qualité "pro" ?

4. Mode RSS :
L'app de Jersou peut découper automatiquement les podcasts longs en "Parties" de 10 épisodes. Est-ce une fonctionnalité que tu souhaites conserver absolument pour ta version Python ?

Une fois que tu m'auras répondu, je rédigerai le "Super-Prompt" que tu n'auras plus qu'à copier-coller dans Antigravity pour lancer la création du nouveau projet de zéro.

1. Gestion des fichiers sur le serveur :

L'app de Jersou travaille beaucoup sur le disque local. Sur ton serveur Coolify, préfères-tu : Un mode "éphémère" : tu uploades tes fichiers/ton flux RSS, l'app génère le ZIP, tu le télécharges, et tout est supprimé du serveur ? > oui, surtout que je ne veux pas avoir de problèmes en cas d'usage externe avec des fichiers sous droit d'auteur (peut-être prévoir une mention légale à ce sujet si c'est obligatoire ?)

Un mode "bibliothèque" : tu veux pouvoir stocker tes projets sur le serveur pour les modifier plus tard ?

2. Modification des images :

Tu as mentionné vouloir "modifier/uploader simplement des images".



Veux-tu une interface où tu peux recadrer/ajouter du texte sur l'image directement dans ton navigateur ? > auto-formatage d'abord, et possibilité de modifier via une interface simple si besoin.

Ou est-ce que l'auto-formatage (redimensionnement auto en 320x240 avec bandes noires) te suffit ?

3. Alternatives pour le TTS (Navigation Audio) :

OpenAI est payant mais de haute qualité.



Veux-tu qu'on prévoie d'autres options gratuites (comme des bibliothèques Python de synthèse vocale locale, souvent moins jolies) ? > existe-t-il des solutions gratuites auto-hébergées de bonne qualité ?

Ou préfères-tu rester sur des API (ElevenLabs, OpenAI) pour une qualité "pro" ? > oui uniquement si gratuit au moins pour 500 générations de fichiers environ (avec avertissement quand on atteint la limite, dans les logs par exemple ?)

4. Mode RSS :

L'app de Jersou peut découper automatiquement les podcasts longs en "Parties" de 10 épisodes. Est-ce une fonctionnalité que tu souhaites conserver absolument pour ta version Python ? > oui mais avec possibilité de paramétrer le découpage.



Fonctionnalité supplémentaire, je veux pouvoir "tester" le package avant de le générer. Est-ce compliqué de simuler ou d'émuler lunii pour vérifier les packages avant le téléchargement ?

C'est un plan de vol très clair. On s'éloigne du "bricolage" pour construire un outil sur mesure, propre et sécurisé. L'idée d'un simulateur intégré est excellente pour éviter de charger un pack buggé sur la boîte.

Voici le Super-Prompt conçu pour l'agent Antigravity (ou Jules). Il intègre toutes tes exigences techniques et fonctionnelles.

Le Super-Prompt à copier dans Antigravity
Contexte : Tu es un ingénieur expert en Python et Streamlit. L'objectif est de créer "StoryBox Python", une application web de génération de packs audio pour boîtes à histoires, en repartant de zéro.

Stack Technique : > * Framework : Streamlit (Interface Web).

Traitement Audio : FFmpeg (obligatoire).

Traitement Image : Pillow (Python Imaging Library).

Gestion RSS : feedparser et requests.

Architecture Fonctionnelle :

Mode Éphémère : L'application doit fonctionner sans base de données persistante. Utilise tempfile pour créer un répertoire de travail unique par session utilisateur. Une fois le ZIP téléchargé, le dossier temporaire doit être purgé.

Traitement Audio (Standard Lunii) : Implémente une fonction de conversion vers MP3, 44100Hz, Mono. Analyse le volume et applique une normalisation (filtre dynaudnorm).

Traitement Image : Redimensionnement automatique en 320x240 avec bandes noires (padding) pour conserver le ratio. Prévois une option simple pour uploader une image personnalisée pour chaque nœud.

Mode RSS Flexible : Permets l'import via URL. Implémente le découpage automatique (splitting) par groupes de N épisodes (N étant un paramètre ajustable par l'utilisateur via un curseur Streamlit).

Synthèse Vocale (TTS) : >     * Priorité 1 (Local/Gratuit) : Intègre Piper TTS (ou gTTS en alternative simple) pour une génération gratuite et illimitée.

Priorité 2 (API) : Prépare le terrain pour OpenAI/ElevenLabs. Ajoute un compteur de fichiers générés dans les logs pour avertir l'utilisateur à l'approche de la limite (ex: 500 fichiers).

Simulateur/Previewer : Crée un "Mode Test" avant la génération finale. L'utilisateur doit pouvoir naviguer visuellement dans l'arborescence (cliquer sur un menu, voir l'image associée et écouter l'audio de navigation) pour valider le pack.

Légal : Affiche un bandeau en bas de page précisant que l'outil est à usage personnel et que l'utilisateur est responsable des droits d'auteur des fichiers uploadés.

Livrables : Génère un fichier app.py complet, un requirements.txt et une structure de dossiers propre.

Pourquoi ce choix pour le TTS et l'Émulateur ?
Piper TTS : C'est la solution miracle actuelle. C'est ultra-rapide, ça tourne sur un simple processeur (parfait pour ton VPS OVH) et la qualité des voix françaises est bluffante pour du gratuit auto-hébergé.

Le Simulateur : Plutôt que d'essayer d'émuler le processeur de la Lunii (très complexe), on va créer un "Simulateur de Navigation". C'est une interface qui reproduit les boutons de la boîte. Tu cliques sur "Droite/Gauche" pour faire défiler les vignettes et "OK" pour entendre l'histoire. C'est 100% efficace pour vérifier les erreurs de menus.

Mise en place sur Coolify
Dès que l'agent a généré le code :

Crée ton nouveau dépôt GitHub (vide, avec la licence AGPLv3).

Pousse les fichiers app.py et requirements.txt.

Dans Coolify, crée une nouvelle ressource pointant sur ce dépôt.

N'oublie pas de régler le Destination Port sur 8501.

Veux-tu que je t'explique comment configurer Piper TTS spécifiquement sur ton serveur Ubuntu via Coolify pour que Jules sache exactement quoi écrire ?

oui

Pour que Piper TTS fonctionne parfaitement sur ton serveur via Coolify, il faut que l'environnement de ton conteneur sache où trouver le moteur de synthèse vocale. C'est l'étape cruciale pour avoir une qualité "pro" gratuitement et sans limite.

Voici les instructions précises à transmettre à ton agent Antigravity (Jules) pour qu'il configure correctement l'application.

1. Configuration pour Coolify (Nixpacks)
Comme Coolify utilise Nixpacks pour construire ton application, tu dois lui indiquer d'installer les dépendances système nécessaires à la voix.

Dans l'onglet Environment Variables de ta ressource Coolify, ajoute cette variable :

Key : NIXPACKS_PKGS

Value : python311 pip ffmpeg espeak-ng

Note : espeak-ng est nécessaire pour que Piper puisse traiter les phonèmes de la langue française.

2. Le Bloc de Code à donner à Jules (Piper Integration)
Donne cette consigne spécifique à ton agent pour qu'il écrive la fonction de synthèse vocale dans app.py :

"Pour la synthèse vocale, utilise la bibliothèque Python piper-tts.

À chaque démarrage de l'app, vérifie si le modèle de voix français (ex: fr_FR-siwis-low.onnx) est présent dans un dossier /models. S'il est absent, télécharge-le automatiquement depuis le dépôt officiel de Piper.

Crée une fonction generate_audio_item(text, output_path) qui utilise Piper pour transformer le texte en fichier .wav.

Utilise ensuite FFmpeg pour convertir ce .wav au format cible : MP3, 44100Hz, Mono.

Applique une normalisation sonore pour que la voix de navigation ait le même niveau que les histoires."

3. Architecture du Simulateur de Navigation
C'est la partie qui va te faire gagner un temps fou. Demande à Jules d'implémenter ceci :

L'aperçu visuel : Utilise st.image pour afficher la vignette en 320x240.

L'aperçu sonore : Ajoute un bouton "Écouter le titre" qui joue le fichier généré par Piper, et un bouton "Écouter l'histoire" pour les fichiers sources.

La logique SHA1 : Assure-toi que le simulateur utilise déjà les noms de fichiers basés sur le hash SHA1, comme dans le pack final, pour être certain que les liens dans le story.json sont corrects.

4. Rappel sur le Mode RSS
Pour le découpage des flux RSS, demande à Jules d'ajouter un composant st.sidebar.slider nommé "Nombre d'épisodes par pack".

Si le flux contient 50 épisodes et que le curseur est sur 10, l'app doit générer soit 5 fichiers ZIP séparés, soit un seul ZIP contenant 5 sous-menus "Partie 1", "Partie 2", etc..

💡 Pourquoi c'est la "Stack" gagnante ?
Confidentialité : Comme tu es en mode "éphémère", aucun fichier audio n'est stocké de façon permanente. Les dossiers temporaires sont supprimés après la création du ZIP.

Gratuité totale : Piper TTS ne coûte rien, contrairement à OpenAI, et fonctionne hors-ligne sur ton serveur.

Fiabilité : En utilisant le simulateur, tu ne télécharges sur ta boîte que des packs dont tu as vérifié la navigation sur ton navigateur.

Prêt à lancer la création du nouveau dépôt ? Une fois que Jules aura généré le premier code fonctionnel, je pourrai t'aider à tester la connexion avec ton serveur.

Souhaites-tu que je prépare un modèle de fichier requirements.txt complet pour que tu n'aies aucune erreur d'installation lors du premier déploiement ?

est-ce que c'est intéressant de mettre à jour le master prompt que tu as créé avec ces derniers éléments, ou c'est mieux d'envoyer plusieurs prompts successifs dans antigravity (master prompt d'abord, et ensuite la suite) ?

Il est bien plus efficace de fournir un "Master Prompt" complet et mis à jour.

Dans le développement par IA, donner une vision globale dès le départ permet à l'agent de structurer son code de manière cohérente (nommage des fonctions, architecture des dossiers temporaires, gestion des dépendances). Si tu procèdes par étapes successives, Jules risque de devoir réécrire (refactoriser) ce qu'il a fait à l'étape précédente pour l'adapter à la nouvelle fonctionnalité.

Voici le Master Prompt V2 optimisé pour un départ "zéro-dette". Il intègre l'analyse de la mécanique de Jersou, la stack Python/Streamlit, et tes nouvelles exigences (Piper TTS, Simulateur).

🚀 Le Master Prompt V2 (À copier dans Antigravity)
Rôle : Tu es un ingénieur expert Python/Streamlit. Ton but est de créer "StoryBox Python", un générateur de packs audio pour boîte à histoires, propre, moderne et performant.

Architecture de base (Stack) :

Interface : Streamlit (version web interactive).

Audio/Image : FFmpeg (audio) et Pillow (images).

Mode de fonctionnement : Mode éphémère. Utilise tempfile pour créer un répertoire unique par session utilisateur. Tout doit être supprimé après la génération du ZIP.

1. Logique de Traitement (Héritage Jersou) :

Standard Audio : Conversion obligatoire en MP3, 44100Hz, Mono. Applique un filtre dynaudnorm pour normaliser le volume sonore.

Standard Image : Redimensionnement en 320x240 avec padding noir pour conserver le ratio. Permets l'upload d'images personnalisées.

Structure de Sortie : Génère un story.json respectant le format "Studio Pack" (stageNodes et actionNodes). Chaque asset dans le dossier assets/ doit être nommé par son hash SHA1 pour éviter les doublons.

2. Fonctionnalités Avancées :

Flux RSS : Importation de podcasts avec un slider permettant de définir le nombre d'épisodes par pack (découpage automatique en "Partie 1", "Partie 2", etc.).

Synthèse Vocale (Piper TTS) : Intègre Piper de manière native. L'app doit vérifier la présence du modèle français fr_FR-siwis-low.onnx (le télécharger si absent) et l'utiliser pour générer les audios de navigation des menus si ceux-ci sont manquants.

Compteur de Sécurité : Logue le nombre de fichiers générés par session et prévois un avertissement visuel si l'on dépasse 500 fichiers (pour prévenir l'usage excessif des ressources).

3. Le Simulateur de Navigation (Exclusivité) :

Avant le téléchargement du ZIP, crée un onglet "Aperçu".

L'utilisateur doit pouvoir simuler la navigation (Boutons Gauche/Droite/OK) pour voir les images s'afficher et entendre les audios associés (Navigation et Histoire).

4. Légal : Ajoute une mention en bas de page stipulant que l'outil est réservé à un usage privé et que l'utilisateur est responsable du respect des droits d'auteur des fichiers qu'il traite.

Livrables attendus : Un fichier app.py robuste, un requirements.txt incluant piper-tts, feedparser, pydub, et streamlit.

Pourquoi ce prompt est meilleur que des messages successifs :
Cohérence du SHA1 : Jules saura dès le début qu'il doit hasher les fichiers. S'il l'apprenait plus tard, il devrait modifier toute sa gestion de fichiers.

Intégration du Simulateur : Le simulateur a besoin d'accéder aux fichiers temporaires avant qu'ils ne soient zippés. En le sachant dès le départ, Jules organisera ses dossiers de manière à ce que l'aperçu soit fluide.

Gestion Piper : L'installation de Piper et du modèle ONNX est un peu technique ; il est préférable qu'elle soit incluse dans la logique de démarrage (startup) de l'application.