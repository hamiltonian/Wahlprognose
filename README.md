# Wahlprognose
Basierend auf der [Sonntagsfragenanalyse von D. Kriesel](https://www.dkriesel.com/sonntagsfrage) habe ich mir gedacht, es wäre doch schön sowas in interaktiv zu haben. Also habe ich mal in die Tasten gehauen, mir die Daten von [wahlrecht.de](https://www.wahlrecht.de/umfragen/) gesracped (jaja, das ist der extrem hässliche Teil) und mit Hilfe einer [DASH](https://dash.plotly.com/)-App interaktiv hingebastelt.

## Herausforderungen und Todos
Neben der Organisation der Daten, was echt einfacher wäre, wenn alle Tabellen auf wahlrecht.de einheitlich formatiert wären war die größte Herausforderung, die beiden Plots so zu linken, dass wenn im oberen irgendwas geändert wird (sprich: gezoomt wird) der untere sich entsprechend anpasst. Letztendlich gelöst habe ich das mit Hilfe von zwei [Session storages](https://dash.plotly.com/dash-core-components/store) mit denen Informationen zwischen Callbacks ausgetauscht werden kann. 
Außerdem ist die App relativ langsam, was ich versucht habe mit [Ploty Resampler](https://github.com/predict-idlab/plotly-resampler) zu lösen (damit sollen die Plots schneller geladen werden, was aber vor allem zu Darstellungsfehlern in der Ansicht über die gesamte Zeit geführt hat).

Wenn ich mal wieder Zeit habe, schaue ich mir vor allem den Resampler an, das ist ja doch was hässlich wenn die Plots am Anfang der Zeitreihe nicht so hübsch sind...
