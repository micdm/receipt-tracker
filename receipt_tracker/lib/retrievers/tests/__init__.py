import os


def get_file_content(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()
