# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import pulsarity

project = "Pulsarity"
copyright = "2024, Bryce Gruber"
author = "Bryce Gruber"
version = pulsarity.version.base_version
release = pulsarity.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]

html_theme_options = {
    "repository_url": "https://github.com/i-am-grub/Pulsarity",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_issues_button": True,
}


# -- Options for autodoc / autosummary ---------------------------------------

autodoc_typehints = "description"
autodoc_typehints_description_target = "all"
autodoc_typehints_format = "short"
autosummary_generate = True
autosummary_ignore_module_all = False
autosummary_imported_members = True

always_document_param_types = True

autodoc_default_options = {
    "members": True,
    "special-members": "__contains__, __version__, __len__",
    "exclude-members": "__weakref__",
}


# -- MySt  ---------------------------------------
# https://myst-parser.readthedocs.io/en/stable/syntax/optional.html#syntax-extensions

myst_enable_extensions = ["alert"]
