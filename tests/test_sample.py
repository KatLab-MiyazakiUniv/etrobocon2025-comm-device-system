from src.sample import Sample


def test_say(capfd):
    sample = Sample("Kat")
    sample.say()

    out, err = capfd.readouterr()
    assert out == "Hello Kat.\n"
    assert err == ''
