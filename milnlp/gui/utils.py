import shelve
from os import path
#
from pandas import DataFrame as df
from milnlp.collection.topic_model import *


def load_query_list(shelf_path='./obj/query_shelf'):
    """Loads a Python shelve file.
    Resets 'matches' and 'processed' if on different system."""
    with shelve.open(shelf_path, 'r') as shelf:
        query_obj_list = [shelf[key] for key in shelf.keys()]

    # Clean up matches if running on different machine
    clean = False
    for query in query_obj_list:
        if query.match:
            for key, match in query.match.items():
                if not path.exists(key):
                    clean = True  # means some directory didn't match up
    # Have to run through after all have been checked
    if clean:
        for query in query_obj_list:
            query.match = None
            query.processed = False

    return query_obj_list


def process_query_list(query_obj_list, attribute_list=None, flag_list=None):
    """Takes a query object list and returns the formatted row for the GUI"""
    if not attribute_list:
        attribute_list = ['UUID', 'phrase', 'flags']

    if not flag_list:
        try:
            flag_list = list(query_obj_list[0].flags.keys())
        except AttributeError:
            raise Exception("You are trying to load a corrupt file.")

    query_list = []
    for query in query_obj_list:
        row = []
        for attr in attribute_list:
            if not attr == 'flags':
                row.append(getattr(query, attr))
            else:
                for flag in flag_list:
                    if getattr(query, 'type') == 'simple':
                        row.append(u'\u2713') if getattr(query, attr)[flag] else row.append(u'\u2715')
                    else:
                        row.append('-')
        query_list.append(tuple(row))

    header = attribute_list[:-1]
    header.extend(flag_list)
    query_list = df(query_list, columns=header)
    return query_list
