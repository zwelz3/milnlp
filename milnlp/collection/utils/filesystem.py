import os
import stat


def is_hidden(file_path):
    """Check if file attribute is set to hidden"""
    assert os.path.exists(file_path), "The file specified does not exist."
    return bool(os.stat(file_path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)


def get_path(file_path, file_name):
    """Uses a path and filename to create a full path to the file"""
    return os.path.join(file_path, file_name)


def is_latest(file_path, base_path):
    """Takes a file_path and a path to a file for comparison (base_path),
       and returns if the file_path is up-to-date"""
    assert os.path.exists(file_path), f"The specified file-path does not exist {file_path}."
    assert os.path.exists(base_path), f"The specified base file-path does not exist {base_path}."
    return os.path.getmtime(file_path) > os.path.getmtime(base_path)


def check_ext(file_path):
    """Takes in a full path to file, and returns whether the extension is and if the document is already parsed.
    """
    supported_exts = {'pdf'}
    file_ext = file_path.split('.')[-1]  # supports arbitrary length file extensions
    assert file_ext in supported_exts, f"Extension '{file_ext}' is not supported at this time."
    if file_ext == 'pdf':
        parsed_file = file_path[:-4]+'.txt'
        if not os.path.exists(parsed_file):
            return False  # File has not been parsed before
        else:
            # file has been parsed before
            if is_latest(parsed_file,
                         file_path):  # check if parsed version already exists (i.e. txt with later date modified)
                return True
            else:
                # parsed file is out of date
                return False


def set_hidden(directory, ext='.mdoc', check=None):
    """Scans a directory and sets all files with ext extension to hidden.
       If check supplied, it will verify that a file with the same same but different extension exists."""
    assert ext[0] == '.' and (check is None or check[0] == '.'), "kwargs are not properly set."
    # todo finish function
    return None
