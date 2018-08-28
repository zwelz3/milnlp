import os
import json
import subprocess
#
from .utils.filesystem import get_path, is_hidden


def init_metadoc(filepath, original_name, filename=None):
    """Creates an empty metatdata document for a specified file
       either takes a directory and filename, or a full path"""
    if filename is not None:
        fullpath = os.path.join(filepath, filename)
    else:
        fullpath = filepath

    fcheck = os.path.isfile(fullpath)
    if fcheck:
        print("Removing old metadata file.", fullpath)
        os.remove(fullpath)

    flag = 1
    try:
        # todo move to build mdoc function that always retains hidden attribute
        with open(r"{}".format(fullpath), 'w') as metadoc:
            payload = {"directory": os.path.dirname(filepath),
                       "filename": original_name}
            json.dump(payload, metadoc)
            flag = subprocess.check_call(["attrib", "+H", fullpath])
    except FileNotFoundError:
        print("File was not created due to incorrect directory path.")
        raise
    except PermissionError:
        raise

    if flag != 0:
        # remove metadata file
        os.remove(fullpath)
        assert flag == 0, "File was unable to be created"
    else:
        print(f"Metadata file created:  {os.path.basename(fullpath)}")


def create_all_metadocs(filelist):
    """Loops through the collection of files and creates a basic metadata document for each."""
    for file in filelist:
        filepath = os.path.dirname(file)
        og_name = os.path.basename(file)
        filename = '.'.join(og_name.split('.')[:-1]) + '.mdoc'
        metapath = os.path.join(filepath, filename)
        init_metadoc(metapath, og_name)


def remove_all_metadocs(filepath):
    for item in [get_path(filepath, f) for f in os.listdir(filepath) if os.path.isfile(get_path(filepath, f))]:
        if is_hidden(item) and item.endswith('mdoc'):
            print(f"Removing metadata file:\t {item}")
            os.remove(item)
    for item in [get_path(filepath, f) for f in os.listdir(filepath) if os.path.isdir(get_path(filepath, f))]:
        remove_all_metadocs(item)


def process_mdocs(item, mdoc_list, smdoc_keywords):
    """Process all MDOC files at level"""
    for file in os.listdir(item):
        if os.path.isfile(get_path(item,file)) and file.endswith('.mdoc'):
            # Single file
            print('-> Adding MDOC: ', file, end="")
            with open(get_path(item, file)) as jsondoc:
                data = json.load(jsondoc)

            try:
                mdoc_keywords = set(data["keywords"].keys())
            except KeyError:  # the mdoc file has no keywords todo log
                continue
            # Do something with the latest metadoc data
            mdoc_list.append({
                "name": file,
                "keywords": list(mdoc_keywords)
            })
            print(f'| Discovered {len(mdoc_keywords)} keywords.')
            smdoc_keywords = smdoc_keywords.union(mdoc_keywords)
    return mdoc_list, smdoc_keywords


def process_smdocs(item, mdoc_list, smdoc_keywords):
    """Process lower level SMDOCs into current level"""
    smdoc_list = []
    for file in os.listdir(item):
        path = '\\'.join([item, file])
        if os.path.isdir(path):
            #print("Looking for .smdoc file in: ", path)
            for file in os.listdir(path):
                if file.endswith('.smdoc'):
                    #print(f"-> {file} found!")
                    smdoc_path = '\\'.join([path, file])
                    with open(smdoc_path) as smdoc:
                        print(f"-> Extracting from {smdoc_path}")
                        data = json.load(smdoc)
                    del data["metadocs"] # scrub extra information to prevent file size explosion
                    smdoc_list.append(data)  # add individual file results to smdoc_list
                    smdoc_keywords = smdoc_keywords.union(set(data['keywords']))  # add keywords to total set
    return smdoc_list, smdoc_keywords


def write_smdoc(smdoc_path, smdoc_file, payload):
    smdoc_fullpath = "\\".join([smdoc_path, smdoc_file])
    print("Writing SMDOC: ", smdoc_fullpath, '\n')
    if os.path.isfile(smdoc_fullpath):
        os.remove(smdoc_fullpath)
    flag = 1
    with open(smdoc_fullpath, 'w') as smdoc:
        json.dump(payload, smdoc, indent=2)
        flag = subprocess.check_call(["attrib", "+H", smdoc_fullpath])

        if flag != 0:
            # remove metadata file
            os.remove(smdoc_fullpath)
            assert flag == 0, "SMDOC was unable to be created"
        else:
            print(f"SMDOC file created.")


def build_supermetadocs(dlist):
    levels = sorted(set(dlist.values()), reverse=True)
    for level in levels:
        print("============================")
        print(f"  Processing Level {level}")
        print("============================")
        for item, lvl in dlist.items():
            if lvl == level and lvl == max(levels):
                # Replace this level with generic level processing

                # Initialize SMDOC fields (replace with class Phase II)
                smdoc_path = os.path.abspath(item)
                smdoc_file = r"{}_lvl{}.smdoc".format(os.path.basename(item), lvl)
                mdoc_list = []
                smdoc_keywords = set()

                print("Path: ", smdoc_path)
                print("File: ", smdoc_file)

                # Process mdocs in directory
                mdoc_list, smdoc_keywords = process_mdocs(item, mdoc_list, smdoc_keywords)
                # Write SMDOC for current level
                payload = {
                    "directory": smdoc_path,
                    "filename": smdoc_file,
                    "metadocs": mdoc_list,
                    "supermetadocs": [],
                    "keywords": list(smdoc_keywords),
                }
                write_smdoc(smdoc_path, smdoc_file, payload)

            # Now SMDOC may contain lower level SMDOCs as well as MDOCs
            elif lvl == level:
                # Initialize SMDOC fields (replace with class Phase II)
                smdoc_path = os.path.abspath(item)
                smdoc_file = r"{}_lvl{}.smdoc".format(os.path.basename(item), lvl)
                mdoc_list = []
                smdoc_keywords = set()

                print("Path: ", smdoc_path)
                print("File: ", smdoc_file)

                # Process MDOCs in directory
                mdoc_list, smdoc_keywords = process_mdocs(item, mdoc_list, smdoc_keywords)
                # Process SMDOCs in directory
                smdoc_list, smdoc_keywords = process_smdocs(item, mdoc_list, smdoc_keywords)
                # Write SMDOC for current level
                payload = {
                    "directory": smdoc_path,
                    "filename": smdoc_file,
                    "metadocs": mdoc_list,
                    "supermetadocs": smdoc_list,
                    "keywords": list(smdoc_keywords),
                }
                write_smdoc(smdoc_path, smdoc_file, payload)
