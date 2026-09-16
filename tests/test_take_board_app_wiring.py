from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_persistent_take_board_controls_are_wired():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    for text in (
        'Keep / Select Take',
        'Return to Review',
        'Reject Take',
        'Save Notes & Tags',
        'Send Selected Takes to Cinema',
        'production_take_select_ui',
        'production_take_action_ui',
        'production_cinema_export_ui',
    ):
        assert text in src


def test_take_board_callbacks_use_authoritative_services():
    src = (ROOT / "film_lab" / "ui_handlers.py").read_text(encoding="utf-8")
    assert 'from film_lab.take_board import select_take, review_take, reject_take, save_take_direction' in src
    assert 'from film_lab.take_board import export_selected_to_cinema' in src
