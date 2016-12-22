"""qs: utilitaire de statistiques de devoirs

usage: qs <exercice:bareme> ...

Options:
  -h --help      Show this help message.
  exercice:bareme path the the exercice/bareme separated by :
"""
import csv
import sys
# import statistics (requires >= 3.4)
import numpy
import os
import json
from docopt import docopt
from jinja2 import Environment, FileSystemLoader
import operator

NOTE=20
TOTAL=4
QS_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_DIR = os.path.join(QS_PATH, 'templates')

def clean(l):
    def el_clean(e):
        # replace hypothetic ',' by ','
        # e.g export from calc with french number formatting
        ec = e.replace(',', '.')
        return float(ec)

    return list(map(el_clean, l))

def main(exercices_baremes):
    if len(exercices_baremes) < 1:
        sys.exit(0)

    files = {}
    for exercice_bareme in exercices_baremes:
        exo, bareme = exercice_bareme.split(':')
        files[exo] = bareme
# grouping by student
    students = {}
# students = {
#   s1 : {
#      note: # note
#      sum: # sum
#      exercice1 : {
#         raw : [] # raw results
#         sum :    # the sum according the 
#         
#      }
#      exercice2 : [],
#   } 
# }
    bar = {}
# bareme = {
#     'title': [] # titles of the questions
#     'points': [] # corresponding points
# }
#
#
    general = {
        'total': 0}
    for exo, bareme in files.items():
        exoname = os.path.basename(exo).split('.')[0].replace('_', '-')
        with open(bareme) as baremefile:
            # bareme should only contains two lines
            reader = list(csv.reader(baremefile, delimiter=','))
            bar.setdefault(exoname, {})
            bar[exoname]['title'] = reader[0]
            bar[exoname]['points'] = clean(reader[1])
            bar[exoname]['total'] = sum(bar[exoname]['points'])
            bar[exoname]['sum'] = [0]*len(bar[exoname]['title'])

            # filling the general
            general['total'] = general['total'] + bar[exoname]['total']
            # max_questions
            general.setdefault('max_questions', len(reader[0]))
            if general['max_questions'] < len(reader[0]):
                general['max_questions'] = len(reader[0])

        with open(exo) as exofile:
            reader = csv.reader(exofile, delimiter=',')
            for row in reader:
                name = ' '.join(row[0:2]).decode('UTF-8')
                students.setdefault(name, {})
                students[name].setdefault('exercices', {})
                students[name]['name'] = name
                raw = clean(row[2:])
                corrected = raw[0:]
                # set raw results
                students[name]['exercices'].setdefault(exoname, {})
                students[name]['exercices'][exoname].setdefault('raw', raw)
                # update success 
                bar[exoname]["sum"] = map(operator.add, bar[exoname]["sum"], raw)
                # compute corrected result 
                for i in range(len(bar[exoname]['title'])):
                    corrected[i] = raw[i] * bar[exoname]['points'][i] / TOTAL
                students[name]['exercices'][exoname].setdefault('corrected', corrected)
                # compute the sum
                s = sum(corrected)    
                students[name]['exercices'][exoname].setdefault('sum', s)
                # compute the note
                note = s/bar[exoname]['total'] * NOTE
                students[name]['exercices'][exoname].setdefault('note', note)
                # repeating the bareme
                students[name]['exercices'][exoname].setdefault('bar', bar[exoname])
                # number of extra columns 
                students[name]['exercices'][exoname]['bar']['extra'] = general['max_questions'] - len(bar[exoname]['title'])
                # filling student general  
                students[name].setdefault('sum', 0)
                students[name]['sum'] = s + students[name]['sum']
                students[name].setdefault('note', 0)
                students[name]['note'] = round(students[name]['sum']/general['total']*NOTE, 1)
                students[name]['total'] = general['total']
    

    # update success
    for exoname, data in bar.items():
        data["success"] = map( lambda x: round(100*x/(TOTAL*len(students.values()))), data["sum"])

    general['notes'] = numpy.array(list(map(lambda e: e['note'], students.values())))
    general['avg'] = round(numpy.mean(general['notes']), 1)
    general['std'] = round(numpy.std(general['notes']), 1)


    env = Environment(loader=FileSystemLoader(searchpath=TEMPLATES_DIR))
    template = env.get_template('stats.tex.j2')
    rendered_text = template.render(students=sorted(students.values(), key=operator.itemgetter('note'), reverse=True), general=general, bar=bar)

    with open('out.tex', 'w') as f:
        f.write(rendered_text.encode('UTF-8'))

    
if __name__ == '__main__':
    arguments = docopt(__doc__, version=0.1)
    main(arguments['<exercice:bareme>'])
