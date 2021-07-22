# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://mango.markets/) support is available at:
#   [Docs](https://docs.mango.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)


import typing

from decimal import Decimal

from .account import Account
from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .group import Group
from .layouts import layouts
from .openorders import OpenOrders
from .perpeventqueue import PerpEventQueue


# # 🥭 build_account_info_converter function
#
# Given a `Context` and an account type, returns a function that can take an `AccountInfo` and
# return one of our objects.
#

def build_account_info_converter(context: Context, account_type: str) -> typing.Callable[[AccountInfo], AddressableAccount]:
    account_type_upper = account_type.upper()
    if account_type_upper == "GROUP":
        return lambda account_info: Group.parse(context, account_info)
    elif account_type_upper == "ACCOUNT":
        def account_loader(account_info: AccountInfo) -> Account:
            layout_account = layouts.MANGO_ACCOUNT.parse(account_info.data)
            group_address = layout_account.group
            group: Group = Group.load(context, group_address)
            return Account.parse(context, account_info, group)
        return account_loader
    elif account_type_upper == "OPENORDERS":
        return lambda account_info: OpenOrders.parse(account_info, Decimal(6), Decimal(6))
    elif account_type_upper == "PERPEVENTQUEUE":
        return lambda account_info: PerpEventQueue.parse(account_info)

    raise Exception(f"Could not find AccountInfo converter for type {account_type}.")
