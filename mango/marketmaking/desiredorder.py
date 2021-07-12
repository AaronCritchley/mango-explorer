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


import mango

from decimal import Decimal


# # 🥭 DesiredOrder class
#
# Encapsulates a single order we want to be present on the orderbook.
#

class DesiredOrder:
    def __init__(self, side: mango.Side, order_type: mango.OrderType, price: Decimal, quantity: Decimal):
        self.side: mango.Side = side
        self.order_type: mango.OrderType = order_type
        self.price: Decimal = price
        self.quantity: Decimal = quantity

    def __str__(self) -> str:
        return f"""« 𝙳𝚎𝚜𝚒𝚛𝚎𝚍𝙾𝚛𝚍𝚎𝚛: {self.order_type} - {self.side} {self.quantity} at {self.price} »"""

    def __repr__(self) -> str:
        return f"{self}"
