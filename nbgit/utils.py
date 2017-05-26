import os
import fnmatch

def rglob(match='*',root='.',exclude_dirs=[]):
    """ Recursive Glob
        Args:
            match: <str> string to match
            root: <str> dir to start recursive search
            exclude: <list[str]> list of directories to skip
    """
    matches = []
    for froot, _, filenames in os.walk(root):
        if not any(xdir in froot for xdir in exclude_dirs):
            for filename in fnmatch.filter(filenames, match):
                matches.append(os.path.join(froot, filename))
    return matches


def copy_append(input_path,output_path,open_type=None):
    """ COPY OR APPEND input_path to output_path
    """
    if not open_type:
        if os.path.isfile(output_path): open_type='a'
        else: open_type='w'
    with open(output_path,open_type) as output_file:
        with open(input_path,'r') as input_file:
            output_file.write(input_file.read())