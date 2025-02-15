from .context import mango
from .fakes import fake_account_info


def test_constructor() -> None:
    account_info = fake_account_info()
    actual = mango.AddressableAccount(account_info)
    assert actual is not None
    assert actual.address == account_info.address
