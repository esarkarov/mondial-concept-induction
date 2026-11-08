from src import config


def test_seed():
    assert config.SEED == 42


def test_masked_organizations():
    assert len(config.MASKED_ORGANIZATIONS) == 11
    assert len(set(config.MASKED_ORGANIZATIONS)) == 11
    assert "NATO" in config.MASKED_ORGANIZATIONS
    assert config.EU_ORGANIZATION not in config.MASKED_ORGANIZATIONS
