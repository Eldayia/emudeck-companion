# Blocage sur « Detecting active emulator… » — 0.21.3

Cet écran attend le premier résultat de `get_current_session`. Avant 0.21.2,
une réponse jamais reçue laissait le chargement affiché indéfiniment, tandis
que les sondages continuaient à envoyer des requêtes. Cela ne permettait pas
de distinguer une panne du backend de l'absence de jeu.

Depuis 0.21.2, une attente supérieure à 8 secondes affiche **Detection unavailable**.
Une erreur efface également l'ancienne session affichée pour ne pas proposer
d'actions sur des informations périmées. Un seul sondage/rafraîchissement de
session est en vol à la fois. Le délai frontend n'annule pas la requête Decky :
si elle reste bloquée, aucun nouveau sondage ne s'empile. Une réponse tardive
n'est pas appliquée ; si la requête finit, un prochain sondage peut récupérer
la session. Le délai concerne la lecture de session, pas toutes les RPC.

La 0.21.2 rendait la vérification XML du réglage ES-DE optionnelle au chargement.
La 0.21.3 utilise un lecteur limité au format des paramètres ES-DE, sans module
XML ni dépendance native, y compris pour afficher le réglage enregistré. Le journal
du Deck a confirmé `ModuleNotFoundError: No module named 'xml.etree'` pendant
l'import de la version 0.21.1. Ce cas est désormais simulé dans les tests.
Les copies de scripts ES-DE sont inchangées, sans réinstallation nécessaire.

La 0.21.3 corrige aussi `Plugin.get_current_session() takes 1 positional argument
but 2 were given`, introduit en 0.21.2 : une callback de promesse transmettait
implicitement `undefined` à l'appel Decky sans argument. Les sondages et le
rafraîchissement manuel invoquent désormais explicitement la RPC avec zéro
argument. Un test reproduit l'erreur avant correction et vérifie les deux routes.

## Collecter les logs

Les appels `loader/call_plugin_method` sans réponse peuvent indiquer un backend
bloqué ou indisponible, mais ne donnent pas leur cause ni toujours le plugin.
Les avertissements `legacy` d'EmuDecky ne prouvent pas un problème Companion.

Après avoir ouvert Companion :

```bash
sudo journalctl -u plugin_loader -b --no-pager | grep -Ei -B 5 -A 15 'EmuDeck.?Companion|Traceback|ModuleNotFoundError|ImportError|ExpatError' | tail -n 180
```

Relire les logs avant partage (noms de jeux et chemins éventuels). Si le problème
persiste, garder ces logs avant de redémarrer Decky. Un redémarrage interrompt
temporairement les plugins Decky ; il ne réinstalle pas les hooks ES-DE :

```bash
sudo systemctl restart plugin_loader
```

Les tests couvrent réussite, absence de jeu, erreur immédiate, requête bloquée,
réponse/erreur tardive et reprise, sans remplacer le test réel sous Gaming Mode.
