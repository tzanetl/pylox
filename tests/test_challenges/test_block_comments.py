from pylox.main import run


def test_block_comments(capsys):
    source = """\
        /* this is a
        multiline
        comment */
        print 1;
    """
    run(source)
    assert capsys.readouterr()[0] == "1\n"


def test_block_comments_error(capsys):
    source = """\
        /* this is a
        multiline
        comment *
        1;
    """
    run(source)
    assert capsys.readouterr()[1].startswith("[line 1] Error: Unexpected character.")
