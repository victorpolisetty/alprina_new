from typing import Generator, Dict, Any, Optional

from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.base import StockDataApiBaseBehaviour
from packages.victorpolisetty.skills.stock_data_api_abci.payloads import CollectAlpacaHistoricalDataPayload
from packages.victorpolisetty.skills.stock_data_api_abci.rounds import CollectAlpacaHistoricalDataRound

FILENAME = "usage"


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
            print(type(historical_data))
            # TODO: Make readable in LLM abci
            historical_data_tsla_readable = self.make_response_readable(historical_data)
            print("The readable data is: ")
            print(historical_data_tsla_readable)

            # Store readable data as IPFS_HASH
            ipfs_hash = yield from self.save_usage_to_ipfs(current_usage=historical_data)

            if ipfs_hash is None:
                # something went wrong
                self.context.logger.warning("Could not save usage to IPFS.")
                return None
            payload = CollectAlpacaHistoricalDataPayload(self.context.agent_address, ipfs_hash)

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

    def make_response_readable(self, historical_data):
        """
        Convert the historical data into a readable format for the LLM.

        Args:
            historical_data (dict): The raw historical data from the API.

        Returns:
            str: A human-readable string representation of the data.
        """
        # Extract TSLA historical data
        tsla_data = historical_data.get('bars', {}).get('TSLA', [])

        # Initialize a list to store readable lines
        readable_lines = []

        # Iterate through each entry in the historical data
        for entry in tsla_data:
            # Extract each required value
            date = entry.get('t', 'N/A')
            open_price = entry.get('o', 'N/A')
            high_price = entry.get('h', 'N/A')
            low_price = entry.get('l', 'N/A')
            close_price = entry.get('c', 'N/A')
            volume = entry.get('v', 'N/A')
            trade_count = entry.get('n', 'N/A')
            volume_weighted_avg_price = entry.get('vw', 'N/A')

            # Format the extracted data into a readable string
            readable_line = (
                f"Date: {date}\n"
                f"  - Opening Price: ${open_price}\n"
                f"  - High Price: ${high_price}\n"
                f"  - Low Price: ${low_price}\n"
                f"  - Closing Price: ${close_price}\n"
                f"  - Volume: {volume} shares\n"
                f"  - Trade Count: {trade_count} trades\n"
                f"  - Volume Weighted Average Price (VWAP): ${volume_weighted_avg_price}\n"
            )

            # Append the formatted string to the list
            readable_lines.append(readable_line)

        # Join all the lines into a single string with separating newlines
        readable_output = "\n".join(readable_lines)

        # Optional: Add an explanation of the data
        explanation = (
            "This data includes the weekly trading information for TSLA:\n"
            "- 'Opening Price' is the price at which TSLA opened on the specified date.\n"
            "- 'High Price' and 'Low Price' represent the highest and lowest prices reached.\n"
            "- 'Closing Price' is the price at the market close.\n"
            "- 'Volume' is the total number of shares traded during the week.\n"
            "- 'Trade Count' is the number of individual trades that took place.\n"
            "- 'VWAP' is the Volume Weighted Average Price, a useful indicator for assessing price trends.\n"
        )

        # Combine the data and explanation into the final readable format
        return explanation + "\n" + readable_output

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
