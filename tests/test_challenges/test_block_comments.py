import textwrap

from pylox.main import run


def test_block_comments(capsys):
    source = """\
        /* this is a
        multiline
        comment */
        1
    """
    correct = """\
        TokenType.NUMBER 1 1.0
        TokenType.EOF  None
    """
    run(source)
    assert capsys.readouterr()[0] == textwrap.dedent(correct)


def test_block_comments_error(capsys):
    source = """\
        /* this is a
        multiline
        comment *
        1
    """
    run(source)
    assert capsys.readouterr()[1].startswith("[line 1] Error: Unexpected character.")
