from agentix import main


def test_models():
    models = main.get_default_model()
    assert isinstance(models, dict)
    assert isinstance(models.get("models"), list)
