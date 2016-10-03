# The purpose of this utility is to obtain the blames

# git blame -p {path_to_file}
import os
import subprocess


def analyse_file(file_path):
    process = subprocess.Popen("git blame -p %s" % file_path,
                               shell=True,
                               cwd=os.path.abspath("/home/lquerel/git/6611_bugs/1RawData/downloaded_repo/apache/hadoop"),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    result = process.communicate()[0]

    print result

analyse_file("hadoop-hdfs-project/hadoop-hdfs-client/src/main/java/org/apache/hadoop/fs/HdfsBlockLocation.java")