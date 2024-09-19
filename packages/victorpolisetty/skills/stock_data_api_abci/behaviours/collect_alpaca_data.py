from typing import Generator, Dict, Any, Optional

from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.base import StockDataApiBaseBehaviour
from packages.victorpolisetty.skills.stock_data_api_abci.payloads import CollectAlpacaHistoricalDataPayload
from packages.victorpolisetty.skills.stock_data_api_abci.rounds import CollectAlpacaHistoricalDataRound

FILENAME = "usage_one"


class CollectAlpacaHistoricalDataBehaviour(StockDataApiBaseBehaviour):  # pylint: disable=too-many-ancestors
    """Behaviour to observe and collect Alpaca historical data."""

    matching_round = CollectAlpacaHistoricalDataRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API for historical stock price data.
        - If the request fails, retry until max retries are exceeded.
        - Send an observation transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        # Check if maximum retries have been exceeded
        if self.context.alpaca_response.is_retries_exceeded():
            # Wait to see if other agents can progress the round, otherwise restart
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        # Measure the local execution time of the HTTP request
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            # Prepare API request specifications
            api_specs = self.context.alpaca_response.get_spec()

            # Make the asynchronous HTTP request to the Alpaca API
            response = yield from self.get_http_response(
                method=api_specs["method"],
                url=api_specs["url"],
                headers=api_specs["headers"],
                parameters=api_specs["parameters"],
            )

            # Process the API response
            historical_data = self.context.alpaca_response.process_response(response)

        # Handle the API response
        if historical_data:
            self.context.logger.info(
                f"Got historical data from {self.context.alpaca_response.api_id}: {historical_data}"
            )

            # Store readable data as IPFS_HASH
            ipfs_hash = yield from self.save_usage_to_ipfs(current_usage=historical_data)

            if ipfs_hash is None:
                # something went wrong
                self.context.logger.warning("Could not save usage to IPFS.")
                return None
            payload = CollectAlpacaHistoricalDataPayload(self.context.agent_address, ipfs_hash_alpaca=ipfs_hash)
            print("The payload is:")
            print(payload)

            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()
            self.set_done()
        else:
            self.context.logger.info(
                f"Could not get historical data from {self.context.alpaca_response.api_id}"
            )

            # Wait before retrying
            yield from self.sleep(
                self.context.alpaca_response.retries_info.suggested_sleep_time
            )
            self.context.alpaca_response.increment_retries()

    def save_usage_to_ipfs(self, current_usage: Dict[str, Any]) -> Generator[None, None, Optional[str]]:
        """Save usage to ipfs."""
        ipfs_hash = yield from self.send_to_ipfs(
            FILENAME, current_usage, filetype=SupportedFiletype.JSON
        )

        if ipfs_hash is None:
            self.context.logger.warning("Could not update usage.")
            return None
        return ipfs_hash

    def clean_up(self) -> None:
        """
        Clean up resources due to a 'stop' event.

        Reset retries or perform other necessary cleanup.
        """
        self.context.alpaca_response.reset_retries()
