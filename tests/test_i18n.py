"""Catalog coverage, including dynamic errors and user-owned report keys."""
import ast
from pathlib import Path
import pytest
from src.csv_cleaner.i18n import ERRORS, EN, translate, translate_error


@pytest.mark.parametrize('source,target', ERRORS)
def test_all_error_templates_translate(source, target):
    assert translate_error(source.format('3', '2', '4'), 'en') == target.format('3', '2', '4')
    assert translate_error(source.format('3', '2', '4'), 'ru') == source.format('3', '2', '4')


def test_every_domain_error_has_translation():
    templates = {source for source, _ in ERRORS}
    for path in (Path('src/csv_cleaner/core.py'), Path('src/csv_cleaner/files.py')):
        for node in ast.walk(ast.parse(path.read_text())):
            if not (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                    and isinstance(node.exc.func, ast.Name) and node.exc.func.id == 'CleanerError'):
                continue
            message = node.exc.args[0]
            if isinstance(message, ast.Constant):
                source = message.value
            else:
                parts = []
                index = 0
                for part in message.values:
                    if isinstance(part, ast.Constant):
                        parts.append(part.value)
                    else:
                        parts.append('{' + str(index) + '}')
                        index += 1
                source = ''.join(parts)
            assert source in templates


def test_catalog_languages():
    for source, target in EN.items():
        assert translate(source, 'en') == target
        assert translate(source, 'ru') == source
        assert not any('\u0400' <= char <= '\u04ff' for char in target)
