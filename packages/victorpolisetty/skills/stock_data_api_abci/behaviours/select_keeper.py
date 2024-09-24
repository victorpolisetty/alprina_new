import random
from abc import ABC
from typing import Generator

from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.base import StockDataApiBaseBehaviour
from packages.victorpolisetty.skills.stock_data_api_abci.payloads import (
    SelectKeeperPayload,
)
from packages.victorpolisetty.skills.stock_data_api_abci.rounds import (
    SelectKeeperRound,
)


class SelectKeeperBehaviour(StockDataApiBaseBehaviour):
    """Select the keeper agent."""

    matching_round = SelectKeeperRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        participants = sorted(self.synchronized_data.participants)
        random.seed(self.synchronized_data.most_voted_randomness, 2)  # nosec
        index = random.randint(0, len(participants) - 1)  # nosec

        keeper_address = participants[index]

        self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
        payload = SelectKeeperPayload(self.context.agent_address, keeper_address)

        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()

        self.set_done()
