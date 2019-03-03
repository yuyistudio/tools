tmp_folder=.tmp
output=$tmp_folder/c
rm -rf $output
python main.py $tmp_folder/a $tmp_folder/b $output
