"""Streamlit's headless UI tests; no browser or personal data required."""
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


class Upload(BytesIO):
    name = 'demo.csv'


def test_initial_screen():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == 'CSV Cleaner Pro'


def test_ui_process_and_invalidate_result():
    with patch('streamlit.file_uploader', return_value=Upload(b'id,name\n001, A \n001, A \n')):
        app = AppTest.from_file(str(APP)).run()
        assert not app.exception
        app.checkbox[0].check()
        app.checkbox[1].check()
        app.button[0].click().run()
        assert not app.exception
        assert app.metric[0].value == '2 → 1'
        assert app.metric[1].value == '1'
        app.checkbox[1].uncheck().run()
        assert not app.metric


def test_ui_bad_file_has_clear_error():
    with patch('streamlit.file_uploader', return_value=Upload(b'')):
        app = AppTest.from_file(str(APP)).run()
        assert not app.exception
        assert 'пуст' in app.error[0].value
