from typing import Generator
from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.base import StockDataApiBaseBehaviour
from packages.victorpolisetty.skills.stock_data_api_abci.payloads import CollectRandomnessPayload
from packages.victorpolisetty.skills.stock_data_api_abci.rounds import CollectRandomnessRound


class CollectRandomnessBehaviour(StockDataApiBaseBehaviour):
    """Retrieve randomness."""

    matching_round = CollectRandomnessRound

    def async_act(self) -> Generator:
        """
        Check whether tendermint is running or not.

        Steps:
        - Do a http request to the tendermint health check endpoint
        - Retry until healthcheck passes or timeout is hit.
        - If healthcheck passes set done event.
        """
        if self.context.randomness_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round
            yield from self.wait_until_round_end()
            self.set_done()
            return

        api_specs = self.context.randomness_api.get_spec()
        http_message, http_dialogue = self._build_http_request_message(
            method=api_specs["method"],
            url=api_specs["url"],
        )
        response = yield from self._do_request(http_message, http_dialogue)
        observation = self.context.randomness_api.process_response(response)

        if observation:
            self.context.logger.info(f"Retrieved DRAND values: {observation}.")
            payload = CollectRandomnessPayload(
                self.context.agent_address,
                observation["round"],
                observation["randomness"],
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
            self.set_done()
        else:
            self.context.logger.error(
                f"Could not get randomness from {self.context.randomness_api.api_id}"
            )
            yield from self.sleep(self.params.sleep_time)
            self.context.randomness_api.increment_retries()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.randomness_api.reset_retries()
