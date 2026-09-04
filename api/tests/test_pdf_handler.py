from pdf_handler import fix_ligature_artifacts


def test_fix_ligature_restores_specific():
    broken = "This is speci6ic and dif6icult to explain"
    fixed = fix_ligature_artifacts(broken)
    assert fixed == "This is specific and difficult to explain"


def test_fix_ligature_does_not_touch_real_numbers():
    text = "The report should be 6 pages long, see page 6"
    fixed = fix_ligature_artifacts(text)
    assert fixed == text