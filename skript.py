import dienstplan
import json

folder = input('Gib bitte den relativen Pfad des Ordners an, in dem die \
Formulare mit den Präferenzen liegen (ohne "/" am Ende): ')

prefs = dienstplan.unpack_preferences(folder)

personal_limits = dict()
for name in prefs.keys():
    personal_limits[name] = int(input('Wie viele Schichten will '+name+ \
    ' übernehmen?: '))

plans = dienstplan.find_best_plans(prefs, 2, personal_limits)
f = open('Best Plans.json', 'w')
json.dump(plans, f)
f.close()

f = open('Best Plans.txt', 'w') 
for plan in plans:
    f.write(dienstplan.format_plan(plan))

f.close()
