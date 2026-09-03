# Inventaire des savestates — 0.22.0

Pendant une session, ouvrir **Detected Save Files → Show Save Files**.
La liste affiche cinq fichiers par page, du plus récent au plus ancien :

- nom du fichier ;
- **File slot** si le nom permet de déduire un numéro, sinon **Slot unknown** ;
- date de modification locale, avec l'heure ;
- taille en octets ou en unités binaires KiB/MiB/GiB.

**Previous Page** et **Next Page** utilisent les boutons Decky, comme les autres
actions, pour une navigation à la manette. La section reste disponible en mode
compact et n'exige pas que le profil expose des boutons de changement de slot.
Elle est repliée au départ. Fermer/réouvrir la liste ou changer de session
remet la pagination à zéro. Si le nombre de fichiers diminue pendant la
consultation, la page est ramenée dans les limites de la nouvelle liste.

L'ancienne liste sommaire des cinq premiers fichiers dans **Save States** est
remplacée par cette section. Save, Load et les contrôles de slots restent
inchangés. Les numéros affichés dans l'inventaire ne sélectionnent aucun slot.

## Lecture seule et limites

Aucune ligne ne charge, n'écrase ou ne supprime une sauvegarde. L'inventaire ne
lit pas le contenu des states : il utilise le nom, la date et la taille des
fichiers trouvés par les chemins/motifs du profil. Les images d'aperçu courantes
(`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`) ne sont plus comptées comme
states même si elles correspondent à un motif large tel que `.state*`.
Il n'y a pas encore de miniatures.

**No matching files found** signifie qu'aucun fichier n'a été reconnu dans les
emplacements recherchés, pas que les slots sont vides. Les emplacements
personnalisés, identifiants de jeu dans les noms, fichiers compressés et autres
conventions peuvent ne pas être reconnus. Un fichier détecté n'est pas une
preuve de sa validité, de sa compatibilité ou d'un chargement réussi.

Les numéros de slot sont déduits des noms, pas lus dans l'émulateur en cours.
Deux fichiers différents portant le même numéro restent affichés séparément ;
un chemin répété par plusieurs motifs n'est affiché qu'une fois. Les données
inconnues restent explicitement inconnues. L'actualisation normale des sessions
rafraîchit l'inventaire : après une sauvegarde, la date n'est mise à jour que
si le fichier correspondant est trouvé et modifié sur disque.

## Test sur le Steam Deck

1. Lancer un jeu dont Save/Load fonctionne déjà, ouvrir **Show Save Files**.
2. Vérifier les noms et dates affichés. S'il y a plus de cinq fichiers, parcourir
   les pages avec la manette. Une liste vide n'exige aucune modification de config.
3. Vérifier l'accès à la liste en mode compact, puis revenir aux actions.
4. Quitter le jeu et en lancer un autre : la liste doit correspondre à la nouvelle
   session et être repliée. Aucun test de suppression n'est nécessaire.

Les tests automatisés couvrent tri, pagination, repli d'une page disparue,
dédoublonnage, métadonnées invalides, absence de mutation du résultat backend
et exclusion des aperçus. Le rendu Gaming Mode reste à valider sur le Deck.
