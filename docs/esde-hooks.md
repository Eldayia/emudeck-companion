# Scripts ES-DE optionnels — 0.21.1

Cette première intégration ajoute le dernier événement de lancement ou de fin
ES-DE aux diagnostics de Companion : jeu, chemin ROM, système et heure.
Elle ne change ni les binds, ni la configuration des émulateurs, ni la détection
des processus. Elle ne débloque pas de nouvelles actions RetroArch. Les jeux
lancés directement par Steam restent pris en charge sans ces scripts.

## Installer sur le Steam Deck

Fermer ES-DE avant l'installation ou la désinstallation. Utiliser Python 3 en
tant qu'utilisateur `deck`, **sans sudo**. Aucune dépendance supplémentaire,
aucun service et aucun accès réseau ne sont nécessaires.

Dans Companion → Diagnostics, relever **ES-DE data folder**. Il doit s'agir du
dossier de données actif d'ES-DE, contenant `es_settings.xml` ou
`settings/es_settings.xml`, pas du dossier des médias téléchargés. Si plusieurs
installations existent, vérifier celle réellement utilisée : la détection
automatique peut sélectionner un autre dossier.

Exemple pour `~/ES-DE` (remplacer ce chemin dans toutes les commandes si besoin) :

```bash
cd ~/homebrew/plugins/EmuDeck-Companion
python3 companion_esde_hooks.py install --esde-root "$HOME/ES-DE"
```

L'installateur ajoute uniquement deux copies autonomes du script :

- `<ES-DE>/scripts/game-start/emudeck-companion.py`
- `<ES-DE>/scripts/game-end/emudeck-companion.py`

Les copies utilisent des fins de ligne Linux et sont exécutables. Les autres
scripts sont conservés. Un fichier homonyme différent ou un lien symbolique
provoque un refus avant modification. Relancer l'installation est sans effet
sur les copies identiques, hormis restaurer leur permission d'exécution.
Il n'y a pas de sauvegarde automatique, car aucun fichier préexistant différent
n'est remplacé. En cas de conflit, sauvegarder/déplacer soi-même le fichier
concerné **hors des dossiers d'événements** après inspection : ES-DE pourrait
exécuter aussi une sauvegarde laissée dans ces dossiers.

## Activation obligatoire dans ES-DE

Ouvrir le menu principal → **Other settings** → **Enable custom event scripts**
et activer cette option. Le libellé traduit dépend de la langue. Companion ne
modifie pas cette préférence. Elle active aussi les autres scripts déjà présents :
vérifier leur contenu avant de l'activer. Aucun événement de navigation n'est
nécessaire. Voir la [documentation officielle des scripts ES-DE](https://gitlab.com/es-de/emulationstation-de/-/blob/master/INSTALL-DEV.md#custom-event-scripts).

## Vérifier

Depuis 0.21.1, les diagnostics du plugin lisent `CustomEventScripts` dans le
fichier de configuration, sans le modifier. **ES-DE script activation** distingue
le réglage enregistré (activé, désactivé, inconnu) et la réception d'un événement
durant le démarrage actuel. La configuration sur disque peut différer du réglage
en mémoire ; un ancien événement ne prouve pas que les scripts sont toujours
activés. Si deux fichiers de configuration sont présents, le plugin ne devine
pas lequel est actif. La source ou la raison du statut inconnu est affichée.

Le texte statique « Not checked; enable custom event scripts » de 0.21.0 était
une limitation d'affichage, pas une erreur d'exécution. **Aucune réinstallation
des hooks n'est nécessaire pour 0.21.1** : leurs fichiers sont inchangés. Leur
commande `status` autonome conserve l'ancien champ `activation` ; utiliser les
diagnostics du plugin pour la nouvelle vérification du réglage.

Lancer un jeu depuis ES-DE, ouvrir Companion, puis **Refresh Diagnostics**.
La section **ES-DE hooks** doit afficher `event_received`, puis `game-start`
et le bon jeu dans **Last ES-DE event**. Quitter normalement le jeu, revenir
dans ES-DE puis actualiser : le dernier événement doit devenir `game-end`.

Vérification équivalente en terminal :

```bash
python3 companion_esde_hooks.py status --esde-root "$HOME/ES-DE"
```

- `not_installed` / `partial_install` : zéro ou une seule copie reconnue.
- `waiting_for_event` : copies présentes, aucun événement lu ; vérifier
  l'activation, le dossier actif et les permissions, puis lancer un jeu ES-DE.
- `event_received` : événement valide reçu durant ce démarrage du Deck ; ce
  n'est pas une preuve que les scripts sont encore activés actuellement.
- `previous_boot` : ancien événement ignoré après redémarrage du Deck.
- `modified_hooks` : copie différente de la version fournie ; inspecter avant
  de la déplacer/remplacer. L'outil refuse de supprimer des modifications.
- `unreadable_or_invalid` : fichier, droits ou données invalides ; contrôler
  également le journal ES-DE. Les erreurs du recorder sont écrites sur stderr.

La comparaison **Same path** signifie uniquement que la ROM du dernier événement
et celle du processus détecté ont le même chemin. Elle ne prouve pas que c'est
la même session. Les archives, playlists ou liens symboliques peuvent donner
des chemins différents. `game-end` est un événement ES-DE, pas une garantie de
fin du processus ; les lancements détachés ou le mode arrière-plan peuvent
modifier son moment d'arrivée. Aucun événement ne tue un processus, ne remplace
la ROM détectée, ni n'autorise l'envoi d'une commande.

## Données et confidentialité

Le script remplace atomiquement un unique fichier local :
`<ES-DE>/.emudeck-companion-events/latest.json`. Le dossier créé est privé
(`0700`) et le fichier `0600`. Il contient le dernier événement, l'identifiant
du démarrage Linux, l'heure, le nom du jeu, le chemin ROM et le système.
Ce n'est pas un historique de temps de jeu. Aucun contenu ROM n'est lu et aucun
argument n'est exécuté comme commande. Les données sont limitées en taille.

Le dernier événement valide figure dans les diagnostics copiés/exportés :
relire noms et chemins avant de partager. Le fichier reste sur disque après
désinstallation des hooks, mais Companion l'ignore sans les deux scripts.

## Désactiver, désinstaller et mettre à jour

Fermer ES-DE, puis :

```bash
python3 companion_esde_hooks.py remove --esde-root "$HOME/ES-DE"
```

Seules les deux copies identiques à la version du plugin sont supprimées.
Les dossiers, autres scripts, paramètres ES-DE et dernier événement restent
intacts. Pour effacer aussi les données, supprimer **uniquement** le fichier
`<ES-DE>/.emudeck-companion-events/latest.json` dans le gestionnaire de fichiers.
Les scripts sont recréables par `install` ; un événement effacé n'est pas
récupérable par Companion. Ne pas désactiver l'option globale si d'autres
scripts en ont besoin.

Les copies sont indépendantes du plugin et ne se mettent pas à jour avec
`git pull`. Pour une future version modifiant le recorder, les retirer avec
l'ancienne version **avant** la mise à jour, puis réinstaller les nouvelles
copies. Retirer également les hooks avant de désinstaller Companion : sinon,
ils continueront à mettre à jour leur unique fichier local.

## Validation de cette version

Tests automatisés : installation répétée, conflits, suppression prudente,
rollback après erreur d'écriture, copie autonome, caractères spéciaux,
écriture atomique, limites de taille, données invalides et ancien démarrage.
Les primitives POSIX réelles (liens/FIFO) nécessitent Linux ; les branches de
refus sont également simulées sur Windows. Le parcours ES-DE réel reste à
valider sur le Steam Deck avec le test lancement/retour ci-dessus.
