from typing import Generator, Dict, Any, Optional

from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.victorpolisetty.skills.alprina_llm_abci.behaviours.base import AlprinaLlmBaseBehaviour
from packages.victorpolisetty.skills.alprina_llm_abci.payloads import PromptLlmPayload
from packages.victorpolisetty.skills.alprina_llm_abci.rounds import PromptLlmRound

FILENAME = "usage"


class PromptLlmBehaviour(AlprinaLlmBaseBehaviour):  # pylint: disable=too-many-ancestors
    """Behaviour to collect ChatGpt prompt response."""

    matching_round = PromptLlmRound

    def async_act(self) -> Generator:

        # Check if maximum retries have been exceeded
        if self.context.chatgpt_response.is_retries_exceeded():
            # Wait to see if other agents can progress the round, otherwise restart
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        # Measure the local execution time of the HTTP request
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            # Prepare API request specifications
            api_specs = self.context.chatgpt_response.get_spec()

            # Make the asynchronous HTTP request to the ChatGPT API
            response = yield from self.get_http_response(
                method=api_specs["method"],
                url=api_specs["url"],
                headers=api_specs["headers"],
                parameters=api_specs["parameters"],
            )

            # Process the API response
            response = self.context.chatgpt_response.process_response(response)

        # Handle the API response
        if response:
            self.context.logger.info(
                f"Got response from {self.context.chatgpt_response.api_id}: {response}"
            )

            # Store readable data as IPFS_HASH
            ipfs_hash = yield from self.save_usage_to_ipfs(current_usage=response)

            if ipfs_hash is None:
                # something went wrong
                self.context.logger.warning("Could not save usage to IPFS.")
                return None
            payload = PromptLlmPayload(self.context.agent_address, ipfs_hash)

            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()
            self.set_done()
        else:
            self.context.logger.info(
                f"Could not get response from {self.context.chatgpt_response.api_id}"
            )

            # Wait before retrying
            yield from self.sleep(
                self.context.chatgpt_response.retries_info.suggested_sleep_time
            )
            self.context.chatgpt_response.increment_retries()

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
