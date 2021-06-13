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

import abc
import logging
import rx
import typing

from datetime import datetime
from decimal import Decimal

from .context import Context
from .market import Market


# # 🥭 Oracles
#
# This file deals with fetching prices from exchanges and oracles.
#


# # 🥭 OracleSource class
#
# This class describes an oracle and can be used to tell `Prices` from different `Oracle`s
# apart.
#

class OracleSource():
    def __init__(self, provider_name: str, source_name: str, market: Market) -> None:
        self.provider_name = provider_name
        self.source_name = source_name
        self.market = market

    def __str__(self) -> str:
        return f"« OracleSource '{self.source_name}' from '{self.provider_name}' for market '{self.market.symbol}' »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Price class
#
# This class contains all relevant info for a price.
#


class Price():
    def __init__(self, source: OracleSource, timestamp: datetime, market: Market, top_bid: Decimal, mid_price: Decimal, top_ask: Decimal) -> None:
        self.source = source
        self.timestamp = timestamp
        self.market = market
        self.top_bid = top_bid
        self.mid_price = mid_price
        self.top_ask = top_ask

    @property
    def spread(self) -> Decimal:
        return (self.top_ask - self.top_bid) / 2

    def __str__(self) -> str:
        return f"{self.timestamp} [{self.source.provider_name}] {self.market.symbol}: {self.mid_price:,.8f}"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Oracle class
#
# Derived versions of this class can fetch prices for a specific market.
#


class Oracle(metaclass=abc.ABCMeta):
    def __init__(self, name: str, market: Market) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.market = market

    @property
    def symbol(self) -> str:
        return self.market.symbol

    @abc.abstractmethod
    def fetch_price(self, context: Context) -> Price:
        raise NotImplementedError("Oracle.fetch_price() is not implemented on the base type.")

    @abc.abstractmethod
    def to_streaming_observable(self, context: Context) -> rx.core.typing.Observable:
        raise NotImplementedError("Oracle.fetch_price() is not implemented on the base type.")


# # 🥭 OracleProvider class
#
# Derived versions of this class allow creation of oracles for markets.
#


class OracleProvider(metaclass=abc.ABCMeta):
    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def oracle_for_market(self, context: Context, market: Market) -> typing.Optional[Oracle]:
        raise NotImplementedError("OracleProvider.create_oracle_for_market() is not implemented on the base type.")

    @abc.abstractmethod
    def all_available_symbols(self, context: Context) -> typing.List[str]:
        raise NotImplementedError("OracleProvider.all_available_symbols() is not implemented on the base type.")
