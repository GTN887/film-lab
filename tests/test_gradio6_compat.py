from pathlib import Path
import inspect
import gradio as gr

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_gradio6_audio_uses_buttons_api():
    assert "show_download_button" not in APP
    assert "show_share_button" not in APP
    assert 'buttons=[]' in APP


def test_gradio6_chatbot_does_not_use_removed_type_argument():
    assert 'gr.Chatbot(label="Rehearsal takes", type="messages"' not in APP
    assert "type" not in inspect.signature(gr.Chatbot).parameters


def test_gradio6_textbox_uses_copy_button_api():
    assert "show_copy_button" not in APP
    assert 'buttons=["copy"]' in APP


def test_full_film_lab_ui_builds_under_installed_gradio():
    import app
    demo = app.build_ui()
    assert isinstance(demo, gr.Blocks)
