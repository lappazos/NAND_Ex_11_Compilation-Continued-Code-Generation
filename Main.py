import os
import sys

import CompilationEngine

FILE_LOCATION = 1

VM = ".vm"

JACK = ".jack"


def translate_files(file_path):
    """
    handle dir & path
    :param file_path: path of file or dir
    """
    files_list = []
    if os.path.isdir(file_path):
        for file in os.listdir(file_path):
            file_explicit_name, file_extension = os.path.splitext(file)
            if file_extension == JACK:
                files_list.append(file)
    elif os.path.isfile(file_path):
        file_explicit_name, file_extension = os.path.splitext(file_path)
        if file_extension == JACK:
            file_path, file = os.path.split(file_path)
            files_list.append(file)
    handle_files(files_list, file_path)


def handle_files(files_list, dir_path):
    """
    Main func go over the lines of the files
    :param files_list: list of files in the dir
    :param dir_path : path to save to
    """
    for file_name in files_list:
        file_explicit_name, file_extension = os.path.splitext(file_name)
        f = open(os.path.join(dir_path, file_explicit_name + VM), 'w')
        compilation_eng = CompilationEngine.CompilationEngine(
            os.path.join(dir_path, file_name), f)
        compilation_eng.compile_class()
        compilation_eng.write_class_to_file()
        f.close()


if __name__ == '__main__':
    filePath = sys.argv[FILE_LOCATION]
    translate_files(filePath)
