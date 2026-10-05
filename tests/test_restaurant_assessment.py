from pathlib import Path

HTML = Path("restaurant-assessment/index.html")


def source():
    return HTML.read_text(encoding="utf-8")


def test_restaurant_assessment_exists():
    assert HTML.is_file()


def test_qualification_handler_has_single_bind_guard():
    text = source()

    assert 'let qualificationPriorities = [];' in text
    assert (
        'if(form.dataset.qualificationHandlerBound === "true") return;'
        in text
    )
    assert (
        'form.dataset.qualificationHandlerBound = "true";'
        in text
    )


def test_qualification_uses_current_priorities():
    text = source()

    update = '''qualificationPriorities = Array.isArray(priorities)
      ? [...priorities]
      : [];'''

    assert update in text
    assert 'qualificationPriorities.map((p,i)' in text


def test_horeca_form_is_excluded_from_refresh_listener():
    text = source()

    assert 'if(form.id !== "horecaQualificationForm"){' in text
    assert 'setTimeout(refreshOperationalLayer, 50);' in text


def test_refresh_keeps_existing_scoring_separate():
    text = source()

    assert 'const priorities = renderOperationalPriorities();' in text
    assert 'updateQualificationContext(priorities);' in text
    assert 'setupQualification(priorities);' in text


def test_declared_semantics_preserved():
    text = source()

    assert (
        "DECLARED — risultati derivati dall'autovalutazione; "
        "da sottoporre a osservazione e verifica."
        in text
    )
