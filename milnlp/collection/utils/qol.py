# This file contains (for now) Quality of Life functions to make processing easier external to specific operations
from sumy.models.dom import ObjectDocumentModel


def doc_to_text(document):
    """Takes an object document model"""
    if type(document) is ObjectDocumentModel:
        doc_text = ' '.join([sentence._text for sentence in document.sentences])  # protected/private access
    elif type(document) is list:
        doc_text = ' '.join(document)
    else:
        assert type(document) is str, "Format of document input is not supported."

    return doc_text