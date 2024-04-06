
import os
import shutil
path_dir = 'E:/FILESVR/TaxAssist/files/GIT/wize'

file_list = os.listdir(path_dir)

for tmp_dir in file_list:
    #souce_file = f"{path_dir}/{tmp_dir}/work/report_guide.pdf"
    souce_file= f"{path_dir}/{tmp_dir}/report_guide.pdf"
    target_file= f"{path_dir}/{tmp_dir}/down0.pdf"
    
    if os.path.isfile(souce_file):
        print(f"MOVE :  {souce_file} -> {target_file}")
        shutil.move(souce_file, target_file)
