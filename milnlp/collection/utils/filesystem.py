import os
import stat


def is_hidden(filepath):
    """Check if file attribute is set to hidden"""
    return bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)


def get_path(filepath, filename):
    """Uses a path and filename to create a full path to the file"""
    return os.path.join(filepath, filename)


def set_hidden(directory, ext='.mdoc', check=None):
    """Scans a directory and sets all files with ext extension to hidden.
       If check supplied, it will verify that a file with the same same but different extension exists."""
    assert ext[0] == '.' and (check is None or check[0] == '.'), "kwargs are not properly set."
    # todo finish function
    return None
