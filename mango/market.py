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

from solana.publickey import PublicKey

from .token import Token


# # 🥭 Market class
#
# This class describes a crypto market. It *must* have a base token and a quote token.
#

class Market(metaclass=abc.ABCMeta):
    def __init__(self, base: Token, quote: Token):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.base: Token = base
        self.quote: Token = quote

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}/{self.quote.symbol}"

    def __str__(self) -> str:
        return f"« 𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} »"

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 AddressableMarket class
#
# This class describes a crypto market. It *must* have a base token and a quote token.
#

class AddressableMarket(Market):
    def __init__(self, base: Token, quote: Token, address: PublicKey):
        super().__init__(base, quote)
        self.address: PublicKey = address

    def __str__(self) -> str:
        return f"« 𝙰𝚍𝚍𝚛𝚎𝚜𝚜𝚊𝚋𝚕𝚎𝙼𝚊𝚛𝚔𝚎𝚝 {self.symbol} [{self.address}] »"
