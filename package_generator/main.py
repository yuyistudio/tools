# encoding: utf8

"""
a dating system prototype
"""

import sys, os, shutil
import hashlib
import logging
from collections import Counter
from data import *
import util


def test_gift():
    logging.basicConfig(level=logging.INFO)

    p1 = Person()
    p1.generate()
    p2 = Person()
    p2.generate()

    print p1.item_attr_affection
    print p2.item_attr_affection
    print 'impression:', p1.get_person_impression(p2)

    gift = Item()
    gift.generate()

    print 'gift:', gift.name
    print 'p1 loved item:', p1.item_affection
    print 'p2 loved item:', p2.item_affection
    print 'p1 gift affection:', p1.get_item_affection(gift)
    print 'p2 gift affection:', p2.get_item_affection(gift)

    print '-' * 20
    for i in range(10):
        print '-->', i
        gift.generate()
        p1.take_item(p2, gift)
        print p1.get_gift_affection(p2, gift), p1.get_relation(p2)

    logging.info("all done")


def test_conversation():
    cc = Conversation()
    hero = Person().generate()
    speaker = Person().generate()
    cc.show(hero, speaker)


def main():
    p1 = Person().generate()

    util.save_to_disk(p1)
    p2 = util.load_from_dist()

    print p1.get_items_affection()
    print p2.get_items_affection()
    print p1.mem.relationship
    print p2.mem.relationship


if __name__ == '__main__':
    main()
