def normalize_language(language):
    for lookup_key in ("alpha_2", "alpha_3"):
        try:
            from pycountry import languages  # get ISO list of languages for lookup
            language = languages.get(**{lookup_key: language})
            return language.name.lower()
        except KeyError:
            pass
    return language
