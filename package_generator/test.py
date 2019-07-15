# coding: utf8


class A(object):
    def __init__(self):
        self.name = 'A'
        self.age = 3
        #self.job = 'Police'

import pickle


def dump():
    a1 = A()
    a1.name = 'a1'
    a2 = A()
    a2.name = 'a2'
    a2.age = 38
    people = [a1, a2]

    fout = open('x.dump', 'w')
    pickle.dump(people, fout)
    fout.close()


def load():
    obj = pickle.load(open('x.dump'))
    for p in obj:
        p.job = 1
        print p.name, p.age #, p.job

#dump()
load()
