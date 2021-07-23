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
from solana.publickey import PublicKey

from .account import Account
from .combinableinstructions import CombinableInstructions
from .context import Context
from .group import Group
from .marketoperations import MarketOperations
from .orders import Order, OrderType, Side
from .spotmarket import SpotMarket
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .wallet import Wallet


# # 🥭 SpotMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#

class SpotMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket, market_instruction_builder: SpotMarketInstructionBuilder):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.market_instruction_builder: SpotMarketInstructionBuilder = market_instruction_builder

        self.market_index = group.find_spot_market_index(spot_market.address)
        self.open_orders_address = self.account.spot_open_orders[self.market_index]

    def cancel_order(self, order: Order) -> typing.Sequence[str]:
        self.logger.info(f"Cancelling {self.spot_market.symbol} order {order}.")
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        cancel: CombinableInstructions = self.market_instruction_builder.build_cancel_order_instructions(order)
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.spot_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]
        crank: CombinableInstructions = self.market_instruction_builder.build_crank_instructions(open_orders_to_crank)
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()

        return (signers + cancel + crank + settle).execute(self.context)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, quantity: Decimal) -> Order:
        client_id: int = self.context.random_client_id()
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        order: Order = Order(id=0, client_id=client_id, side=side, price=price,
                             quantity=quantity, owner=self.open_orders_address, order_type=order_type)
        self.logger.info(f"Placing {self.spot_market.symbol} order {order}.")
        place: CombinableInstructions = self.market_instruction_builder.build_place_order_instructions(order)
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.spot_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]
        crank: CombinableInstructions = self.market_instruction_builder.build_crank_instructions(open_orders_to_crank)
        settle: CombinableInstructions = self.market_instruction_builder.build_settle_instructions()

        (signers + place + crank + settle).execute(self.context)

        return order

    def settle(self) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        settle = self.market_instruction_builder.build_settle_instructions()
        return (signers + settle).execute(self.context)

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        signers: CombinableInstructions = CombinableInstructions.from_wallet(self.wallet)
        open_orders_to_crank: typing.List[PublicKey] = []
        for event in self.spot_market.unprocessed_events(self.context):
            open_orders_to_crank += [event.public_key]
        crank = self.market_instruction_builder.build_crank_instructions(open_orders_to_crank, limit)
        return (signers + crank).execute(self.context)

    def load_orders(self) -> typing.Sequence[Order]:
        all_orders = self.spot_market.orders(self.context)
        orders: typing.List[Order] = []
        for serum_order in all_orders:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def load_my_orders(self) -> typing.Sequence[Order]:
        if not self.open_orders_address:
            return []

        all_orders = self.spot_market.orders(self.context)
        serum_orders = [o for o in all_orders if o.open_order_address == self.open_orders_address]
        orders: typing.List[Order] = []
        for serum_order in serum_orders:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def __str__(self) -> str:
        return f"""« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙾𝚙𝚎𝚛𝚊𝚝𝚒𝚘𝚗𝚜 [{self.spot_market.symbol}] »"""
