"""Lightweight localization (C35): a dict-backed Qt translator.

The zh-CN translation lives in `zh_CN.py` as a plain {English: Chinese} dict.
`DictTranslator` serves it to Qt's tr() lookup, so extending a language needs
no Qt Linguist toolchain: add strings to the dict, restart, done. Untranslated
strings fall back to English (the dict lookup returns None and Qt keeps the
source text). Lookup ignores the tr() context — this app's strings are unique.
"""
from __future__ import annotations

from PySide6.QtCore import QTranslator

from . import zh_CN

# settings value → menu label; "system" means "follow the OS locale"
LANGUAGES = {"system": "System default", "en": "English", "zh_CN": "中文（简体）"}


class DictTranslator(QTranslator):
    def __init__(self, strings: dict[str, str], parent=None):
        super().__init__(parent)
        self._strings = strings

    def translate(self, context, source_text, disambiguation=None, n=-1):
        t = self._strings.get(str(source_text))
        return t if t else None


def install_translator(app, lang: str) -> DictTranslator | None:
    """Install the translation for `lang` ("zh_CN"); None = keep English."""
    catalogs = {"zh_CN": zh_CN.STRINGS}
    strings = catalogs.get(lang)
    if not strings:
        return None
    tr = DictTranslator(strings, app)
    return tr if app.installTranslator(tr) else None
