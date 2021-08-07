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

import itertools
import json
import logging
import requests
import time
import typing


from base64 import b64encode
from decimal import Decimal
from solana.account import Account
from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.rpc.commitment import Commitment
from solana.rpc.types import DataSliceOpts, MemcmpOpts, RPCResponse, TokenAccountOpts, TxOpts

from .constants import SOL_DECIMAL_DIVISOR


# # 🥭 RateLimitException class
#
# A `RateLimitException` exception base class that allows trapping and handling rate limiting
# independent of other error handling.
#
class RateLimitException(Exception):
    pass


# # 🥭 TooMuchBandwidthRateLimitException class
#
# A `TooMuchBandwidthRateLimitException` exception that specialises the `RateLimitException`
# for when too much bandwidth has been consumed.
#
class TooMuchBandwidthRateLimitException(RateLimitException):
    pass


# # 🥭 TooManyRequestsRateLimitException class
#
# A `TooManyRequestsRateLimitException` exception that specialises the `RateLimitException`
# for when too many requests have been sent in a short time.
#
class TooManyRequestsRateLimitException(RateLimitException):
    pass


# # 🥭 TransactionException class
#
# A `TransactionException` exception that can provide additional error data, or at least better output
# of problems at the right place.
#
class TransactionException(Exception):
    def __init__(self, message: str, code: int, accounts: typing.Optional[typing.List[str]], errors: typing.Optional[typing.List[str]], logs: typing.Optional[typing.List[str]]):
        super().__init__(message)
        self.message: str = message
        self.code: int = code
        self.accounts: typing.Optional[typing.List[str]] = accounts
        self.errors: typing.Optional[typing.List[str]] = errors
        self.logs: typing.Optional[typing.List[str]] = logs

    def __str__(self) -> str:
        accounts = "No Accounts"
        if self.accounts:
            accounts = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.accounts])
        errors = "No Errors"
        if self.errors:
            errors = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.errors])
        logs = "No Logs"
        if self.logs:
            logs = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.logs])
        return f"""« 𝚃𝚛𝚊𝚗𝚜𝚊𝚌𝚝𝚒𝚘𝚗𝙴𝚡𝚌𝚎𝚙𝚝𝚒𝚘𝚗 [{self.code}] {self.message}
    Accounts:
        {accounts}
    Errors:
        {errors}
    Logs:
        {logs}
»"""

    def __repr__(self) -> str:
        return f"{self}"


_CommitmentKey = "commitment"
_EncodingKey = "encoding"
_FiltersKey = "filters"
_DataSliceKey = "dataSlice"
_DataSizeKey = "dataSize"
_MemCmp = "memcmp"
_SkipPreflightKey = "skipPreflight"
_PreflightCommitmentKey = "preflightCommitment"

UnspecifiedCommitment = Commitment("unspecified")
UnspecifiedEncoding = "unspecified"


# # 🥭 CompatibleClient class
#
# A `CompatibleClient` class that tries to be compatible with the proper Solana Client, but that handles
# some common operations better from our point of view.
#
class CompatibleClient:
    def __init__(self, cluster: str, cluster_url: str, commitment: Commitment, skip_preflight: bool):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.cluster: str = cluster
        self.cluster_url: str = cluster_url

        self._request_counter = itertools.count()

        self.commitment: Commitment = commitment
        self.skip_preflight: bool = skip_preflight
        self.encoding: str = "base64"

    def is_node_healthy(self) -> bool:
        try:
            response = requests.get(f"{self.cluster_url}/health")
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.warning("Health check failed with error: %s", str(err))
            return False

        return response.ok

    def get_balance(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment) -> RPCResponse:
        options = self._build_options(commitment, None, None)
        return self._send_request("getBalance", str(pubkey), options)

    def get_sol_balance(self, account_public_key: PublicKey) -> Decimal:
        result = self.get_balance(account_public_key)
        value = Decimal(result["result"]["value"])
        return value / SOL_DECIMAL_DIVISOR

    def get_account_info(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment,
                         encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> RPCResponse:
        options = self._build_options_with_encoding(commitment, encoding, data_slice)
        return self._send_request("getAccountInfo", str(pubkey), options)

    def get_confirmed_signature_for_address2(self, account: typing.Union[str, Account, PublicKey], before: typing.Optional[str] = None, limit: typing.Optional[int] = None) -> RPCResponse:
        if isinstance(account, Account):
            account = str(account.public_key())

        if isinstance(account, PublicKey):
            account = str(account)

        opts: typing.Dict[str, typing.Union[int, str]] = {}
        if before:
            opts["before"] = before

        if limit:
            opts["limit"] = limit

        return self._send_request("getConfirmedSignaturesForAddress2", account, opts)

    def get_confirmed_transaction(self, signature: str, encoding: str = "json") -> RPCResponse:
        return self._send_request("getConfirmedTransaction", signature, encoding)

    def get_minimum_balance_for_rent_exemption(self, size: int, commitment: Commitment = UnspecifiedCommitment) -> RPCResponse:
        options = self._build_options(commitment, None, None)
        return self._send_request("getMinimumBalanceForRentExemption", size, options)

    def get_program_accounts(self, pubkey: typing.Union[str, PublicKey],
                             commitment: Commitment = UnspecifiedCommitment,
                             encoding: typing.Optional[str] = UnspecifiedEncoding,
                             data_slice: typing.Optional[DataSliceOpts] = None,
                             data_size: typing.Optional[int] = None,
                             memcmp_opts: typing.Optional[typing.List[MemcmpOpts]] = None) -> RPCResponse:
        options = self._build_options_with_encoding(commitment, encoding, data_slice)
        options[_FiltersKey] = []

        if data_size:
            options[_FiltersKey].append({_DataSizeKey: data_size})

        for memcmps in [] if not memcmp_opts else memcmp_opts:
            options[_FiltersKey].append({_MemCmp: dict(memcmps._asdict())})

        return self._send_request("getProgramAccounts", str(pubkey), options)

    def get_recent_blockhash(self, commitment: Commitment = UnspecifiedCommitment) -> RPCResponse:
        options = self._build_options(commitment, None, None)
        return self._send_request("getRecentBlockhash", options)

    def get_token_account_balance(self, pubkey: typing.Union[str, PublicKey], commitment: Commitment = UnspecifiedCommitment):
        options = self._build_options(commitment, None, None)
        return self._send_request("getTokenAccountBalance", str(pubkey), options)

    def get_token_accounts_by_owner(self, owner: PublicKey, token_account_options: TokenAccountOpts, commitment: Commitment = UnspecifiedCommitment,) -> RPCResponse:
        options = self._build_options_with_encoding(
            commitment, token_account_options.encoding, token_account_options.data_slice)

        if not token_account_options.mint and not token_account_options.program_id:
            raise ValueError("Please provide one of mint or program_id")

        account_options: typing.Dict[str, str] = {}
        if token_account_options.mint:
            account_options["mint"] = str(token_account_options.mint)
        if token_account_options.program_id:
            account_options["programId"] = str(token_account_options.program_id)

        return self._send_request("getTokenAccountsByOwner", str(owner), account_options, options)

    def get_multiple_accounts(self, pubkeys: typing.Sequence[PublicKey], commitment: Commitment = UnspecifiedCommitment,
                              encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> RPCResponse:
        options = self._build_options_with_encoding(commitment, encoding, data_slice)
        return self._send_request("getMultipleAccounts", pubkeys, options)

    def send_transaction(self, transaction: Transaction, *signers: Account, opts: TxOpts = TxOpts(preflight_commitment=UnspecifiedCommitment)) -> RPCResponse:
        try:
            blockhash_resp = self.get_recent_blockhash()
            if not blockhash_resp["result"]:
                raise RuntimeError("failed to get recent blockhash")
            transaction.recent_blockhash = Blockhash(blockhash_resp["result"]["value"]["blockhash"])
        except Exception as err:
            raise RuntimeError("failed to get recent blockhash") from err

        transaction.sign(*signers)

        encoded_transaction: str = b64encode(transaction.serialize()).decode("utf-8")

        commitment: Commitment = opts.preflight_commitment
        if commitment == UnspecifiedCommitment:
            commitment = self.commitment

        skip_preflight: bool = opts.skip_preflight or self.skip_preflight

        return self._send_request(
            "sendTransaction",
            encoded_transaction,
            {
                _SkipPreflightKey: skip_preflight,
                _PreflightCommitmentKey: commitment,
                _EncodingKey: self.encoding,
            }
        )

    def _send_request(self, method: str, *params: typing.Any) -> RPCResponse:
        request_id = next(self._request_counter) + 1
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        raw_response = requests.post(self.cluster_url, headers=headers, data=data)

        # Some custom exceptions specifically for rate-limiting. This allows calling code to handle this
        # specific case if they so choose.
        #
        # "You will see HTTP respose codes 429 for too many requests or 413 for too much bandwidth."
        if raw_response.status_code == 413:
            raise TooMuchBandwidthRateLimitException(f"Rate limited (too much bandwidth) calling method '{method}'.")
        elif raw_response.status_code == 429:
            raise TooManyRequestsRateLimitException(f"Rate limited (too many requests) calling method '{method}'.")

        # Not a rate-limit problem, but maybe there was some other error?
        raw_response.raise_for_status()

        # All seems OK, but maybe the server returned an error? If so, try to pass on as much
        # information as we can.
        response = json.loads(raw_response.text)
        if "error" in response:
            if response["error"] is str:
                message: str = typing.cast(str, response["error"])
                raise Exception(f"Transaction failed: '{message}'")
            else:
                error_message: str = response["error"]["message"] if "message" in response["error"] else "No message"
                exception_message: str = f"Transaction failed with: '{error_message}'"
                error_code: int = response["error"]["code"] if "code" in response["error"] else -1
                error_data: typing.Dict = response["error"]["data"] if "data" in response["error"] else {}
                error_accounts = error_data["accounts"] if "accounts" in error_data else "No accounts"
                error_err = error_data["err"] if "err" in error_data else "No err"
                error_logs = error_data["logs"] if "logs" in error_data else "No logs"
                raise TransactionException(exception_message, error_code, error_accounts, error_err, error_logs)

        # The call succeeded.
        return typing.cast(RPCResponse, response)

    def _build_options(self, commitment: Commitment, encoding: typing.Optional[str], data_slice: typing.Optional[DataSliceOpts]) -> typing.Dict[str, typing.Any]:
        options: typing.Dict[str, typing.Any] = {}
        if commitment == UnspecifiedCommitment:
            options[_CommitmentKey] = self.commitment
        else:
            options[_CommitmentKey] = commitment

        if encoding:
            options[_EncodingKey] = encoding

        if data_slice:
            options[_DataSliceKey] = dict(data_slice._asdict())

        return options

    def _build_options_with_encoding(self, commitment: Commitment, encoding: typing.Optional[str], data_slice: typing.Optional[DataSliceOpts]) -> typing.Dict[str, typing.Any]:
        encoding_to_use: str = self.encoding
        if (encoding is not None) and (encoding != UnspecifiedEncoding):
            encoding_to_use = encoding
        return self._build_options(commitment, encoding_to_use, data_slice)

    def __str__(self) -> str:
        return f"« 𝙲𝚘𝚖𝚙𝚊𝚝𝚒𝚋𝚕𝚎𝙲𝚕𝚒𝚎𝚗𝚝 [{self.cluster}]: {self.cluster_url} »"

    def __repr__(self) -> str:
        return f"{self}"


class BetterClient:
    def __init__(self, client: CompatibleClient):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.compatible_client: CompatibleClient = client

        # kangda said in Discord: https://discord.com/channels/791995070613159966/836239696467591186/847816026245693451
        # "I think you are better off doing 4,8,16,20,30"
        self.retry_pauses: typing.Sequence[Decimal] = [Decimal(4), Decimal(
            8), Decimal(16), Decimal(20), Decimal(30)]

    @property
    def cluster(self) -> str:
        return self.compatible_client.cluster

    @cluster.setter
    def cluster(self, value: str) -> None:
        self.compatible_client.cluster = value

    @property
    def cluster_url(self) -> str:
        return self.compatible_client.cluster_url

    @cluster_url.setter
    def cluster_url(self, value: str) -> None:
        self.compatible_client.cluster_url = value

    @property
    def encoding(self) -> str:
        return self.compatible_client.encoding

    @encoding.setter
    def encoding(self, value: str) -> None:
        self.compatible_client.encoding = value

    @property
    def commitment(self) -> Commitment:
        return self.compatible_client.commitment

    @commitment.setter
    def commitment(self, value: Commitment) -> None:
        self.compatible_client.commitment = value

    @property
    def skip_preflight(self) -> bool:
        return self.compatible_client.skip_preflight

    @skip_preflight.setter
    def skip_preflight(self, value: bool) -> None:
        self.compatible_client.skip_preflight = value

    @staticmethod
    def from_configuration(cluster: str, cluster_url: str, commitment: Commitment, skip_preflight: bool) -> "BetterClient":
        compatible = CompatibleClient(cluster, cluster_url, commitment, skip_preflight)
        return BetterClient(compatible)

    def is_node_healthy(self) -> bool:
        return self.compatible_client.is_node_healthy()

    def get_balance(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment) -> Decimal:
        response = self.compatible_client.get_balance(pubkey, commitment)
        value = Decimal(response["result"]["value"])
        return value / SOL_DECIMAL_DIVISOR

    def get_account_info(self, pubkey: typing.Union[PublicKey, str], commitment: Commitment = UnspecifiedCommitment,
                         encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> typing.Dict:
        response = self.compatible_client.get_account_info(pubkey, commitment, encoding, data_slice)
        return response["result"]

    def get_confirmed_signatures_for_address2(self, account: typing.Union[str, Account, PublicKey], before: typing.Optional[str] = None, limit: typing.Optional[int] = None) -> typing.Sequence[str]:
        response = self.compatible_client.get_confirmed_signature_for_address2(account, before, limit)
        return [result["signature"] for result in response["result"]]

    def get_confirmed_transaction(self, signature: str, encoding: str = "json") -> typing.Dict:
        response = self.compatible_client.get_confirmed_transaction(signature, encoding)
        return response["result"]

    def get_minimum_balance_for_rent_exemption(self, size: int, commitment: Commitment = UnspecifiedCommitment) -> int:
        response = self.compatible_client.get_minimum_balance_for_rent_exemption(size, commitment)
        return response["result"]

    def get_program_accounts(self, pubkey: typing.Union[str, PublicKey],
                             commitment: Commitment = UnspecifiedCommitment,
                             encoding: typing.Optional[str] = UnspecifiedEncoding,
                             data_slice: typing.Optional[DataSliceOpts] = None,
                             data_size: typing.Optional[int] = None,
                             memcmp_opts: typing.Optional[typing.List[MemcmpOpts]] = None) -> typing.Dict:
        response = self.compatible_client.get_program_accounts(
            pubkey, commitment, encoding, data_slice, data_size, memcmp_opts)
        return response["result"]

    def get_recent_blockhash(self, commitment: Commitment = UnspecifiedCommitment) -> Blockhash:
        response = self.compatible_client.get_recent_blockhash(commitment)
        return Blockhash(response["result"]["value"]["blockhash"])

    def get_token_account_balance(self, pubkey: typing.Union[str, PublicKey], commitment: Commitment = UnspecifiedCommitment) -> typing.Dict:
        response = self.compatible_client.get_token_account_balance(pubkey, commitment)
        return response["result"]["value"]

    def get_token_accounts_by_owner(self, owner: PublicKey, token_account_options: TokenAccountOpts, commitment: Commitment = UnspecifiedCommitment,) -> typing.Sequence[typing.Dict]:
        response = self.compatible_client.get_token_accounts_by_owner(owner, token_account_options, commitment)
        return response["result"]["value"]

    def get_multiple_accounts(self, pubkeys: typing.Sequence[PublicKey], commitment: Commitment = UnspecifiedCommitment,
                              encoding: str = UnspecifiedEncoding, data_slice: typing.Optional[DataSliceOpts] = None) -> typing.Sequence[typing.Dict]:
        response = self.compatible_client.get_multiple_accounts(pubkeys, commitment, encoding, data_slice)
        return response["result"]["value"]

    def send_transaction(self, transaction: Transaction, *signers: Account, opts: TxOpts = TxOpts(preflight_commitment=UnspecifiedCommitment)) -> str:
        response = self.compatible_client.send_transaction(
            transaction, *signers, opts=opts)
        return response["result"]

    def wait_for_confirmation(self, transaction_ids: typing.Sequence[str], max_wait_in_seconds: int = 60) -> typing.Sequence[str]:
        self.logger.info(f"Waiting up to {max_wait_in_seconds} seconds for {transaction_ids}.")
        all_confirmed: typing.List[str] = []
        for wait in range(0, max_wait_in_seconds):
            for transaction_id in transaction_ids:
                time.sleep(1)
                confirmed = self.get_confirmed_transaction(transaction_id)
                if confirmed is not None:
                    self.logger.info(f"Confirmed {transaction_id} after {wait} seconds.")
                    all_confirmed += [transaction_id]

        if len(all_confirmed) != len(transaction_ids):
            self.logger.info(f"Timed out after {wait} seconds waiting on transaction {transaction_id}.")
        return all_confirmed

    def __str__(self) -> str:
        return f"« 𝙱𝚎𝚝𝚝𝚎𝚛𝙲𝚕𝚒𝚎𝚗𝚝 [{self.cluster}]: {self.cluster_url} »"

    def __repr__(self) -> str:
        return f"{self}"
