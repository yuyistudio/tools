# encoding: utf8

"""
incremental update package generator
"""

import sys, os, shutil
import hashlib
import logging
from collections import Counter


file_counter = Counter()


def get_file_md5(filename):
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    f = open(filename, 'rb')
    while True:
        b = f.read(1024*1024*10)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()


def is_same_file(f1, f2):
    if os.path.getsize(f1) == os.path.getsize(f2):
        return get_file_md5(f1) == get_file_md5(f2)
    else:
        return False


def process_folder(old, new, output):
    old_fs = os.listdir(old)
    new_fs = os.listdir(new)
    for diff in (set(new_fs) - set(old_fs)):
        f1 = new + '/' + diff
        f2 = output + '/' + diff
        logging.info("copy %s to %s", f1, f2)
        file_counter['copy'] += 1
        if os.path.isfile(f1):
            shutil.copyfile(f1, f2)
        else:
            shutil.copytree(f1, f2)
    for same in (set(new_fs) & set(old_fs)):
        f1 = old + '/' + same
        f2 = new + '/' + same
        f3 = output + '/' + same
        f1_isfile = os.path.isfile(f1)
        f2_isfile = os.path.isfile(f2)
        if f1_isfile != f2_isfile:
            # new type diffs from old type
            logging.info("copy %s to %s", f2, f3)
            file_counter['copy'] += 1
            shutil.copy(f2, f3)
        elif f1_isfile:
            # both file
            if not is_same_file(f1, f2):
                logging.info("copy %s to %s", f2, f3)
                file_counter['copy'] += 1
                shutil.copy(f2, f3)
            else:
                logging.info("IGNORE %s", f2)
                file_counter['ignore'] += 1
        else:
            # both folder
            if not os.path.exists(f3):
                os.mkdir(f3)
            process_folder(f1, f2, f3)


def main():
    logging.basicConfig(level=logging.INFO)
    old, new, output = sys.argv[1], sys.argv[2], sys.argv[3]
    if not os.path.exists(output):
        os.mkdir(output)
    process_folder(old, new, output)
    logging.info("all done, %d copied, %d ignored", file_counter['copy'], file_counter['ignore'])


if __name__ == '__main__':
    main()