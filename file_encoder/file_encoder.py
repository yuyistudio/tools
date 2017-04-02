# -*- coding: utf-8 -*-  
import os  
import os.path  
import sys
import random
import shutil  

CLASSIFIED_PREFIX = 'tmpfolder'
config = {}
root_dir = os.getcwd()
tmp_dir = root_dir
encode_char_count = 512

class FileInfo:
    def __init__(self, full, parent, filename, basename, ext):
        self.full = full
        self.parent = parent
        self.filename = filename
        self.basename = basename
        self.ext = ext

def mkdir_p(path):
    if os.path.exists(path):
        return
    os.makedirs(path)

def _every_file(output, path, is_classified_target):
    for parent, dirnames, filenames in os.walk(path):
        if os.path.basename(parent).startswith(CLASSIFIED_PREFIX) != is_classified_target:
            continue
        for filename in filenames:
            (basename, ext) = os.path.splitext(filename)
            output.append(FileInfo(os.path.join(parent, filename), parent, filename, basename, ext[1:]))
    
def every_file(path, fn, is_classified_target):
    res = []
    _every_file(res, path, is_classified_target)
    for fi in res:
        fn(fi)

join = os.path.join
def safe_rename (src, dest):
    if src == dest:
        return
    print 'rename', src, dest
    if not os.path.exists(src):
        raise ValueError('rename error, src doesn\'t exist `%s`' % src)
    if os.path.isfile(dest):
        return False
    os.rename(src, dest)
    return True

def file_encoder(fi):
    print 'encode', fi.full
    key = config['key']
    def xor(data):
        result_data = []
        for i in range(min(len(data), encode_char_count)):
            result_data.append(chr(ord(key[i % len(key)]) ^ ord(data[i])))
        return ''.join(result_data)
    with open(fi.full, 'rb+') as f:
        f.seek(0, 0)
        result_data = xor(f.read(encode_char_count))
        f.seek(0, 0)
        f.write(result_data)

def get_file_classifier(random_rename = False):
    def file_classify(fi):
        dest_path = join(tmp_dir, CLASSIFIED_PREFIX + fi.ext[::-1])
        mkdir_p(dest_path)
        rename_counter = 100
        output_dir = join(tmp_dir, CLASSIFIED_PREFIX + fi.ext[::-1])
        while rename_counter > 0:
            if random_rename:
                dest_file = join(output_dir, str(random.randint(0, 99999999)) + '.' + fi.ext)
            else:
                if rename_counter == 100:
                    dest_file = join(output_dir, fi.filename)
                else:
                    dest_file = join(output_dir, fi.basename + '.' + str(random.randint(0, 9999)) + '.' + fi.ext)
            if safe_rename(fi.full, dest_file):
                break
            rename_counter -= 1
            continue
    return file_classify

counter = 0
def file_random_rename(fi):
    global counter
    dest_file = join(fi.parent, fi.filename[::-1])
    counter += 1
    safe_rename(fi.full, dest_file)

def check_password(passwd):
    import md5
    m1 = md5.new()   
    m1.update(passwd)
    target_md5 = 'a4732edf27a0148f495550b2378f8537'
    input_md5 = m1.hexdigest() 
    return input_md5 == target_md5

def output(info):
    sys.stderr.write(info)
    sys.stderr.write('\n')

def main():
    if len(sys.argv) == 2 and sys.argv[1].startswith('c'):
        every_file(root_dir, get_file_classifier(random_rename = True), False)
        for filename in os.listdir(root_dir):
            if filename.startswith(CLASSIFIED_PREFIX):
                continue
            dest_path = os.path.join(root_dir, filename)
            if os.path.isdir(dest_path):
                shutil.rmtree(dest_path)
        output('done')
    elif len(sys.argv) == 1:
        sys.stderr.write('password: ')
        sys.stderr.flush()
        passwd = raw_input()
        if not check_password(passwd):
            output('password incorrect')
            return
        config['key'] = passwd
        every_file(root_dir, file_random_rename, True)
        mkdir_p(tmp_dir)
        every_file(root_dir, file_encoder, True)
        output('done')
    else:
        output('unknown error, args `%s`' % ' '.join(sys.argv))

'''
使用方法：
1、将当前目录下的所有文件进行归类处理。默认会将所有文件以随机数字重命名，保留后缀名。
python ./file_encoder.py classify 
2、将当期目录下所有已经归类完成的文件进行加密或者解密。
python ./file_encoder.py
此时会提示输入密码。目前密码是算好md5写死在代码里面的。
'''
main()
