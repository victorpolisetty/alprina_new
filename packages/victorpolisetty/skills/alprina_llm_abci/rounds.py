# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This package contains the rounds of AlprinaLlmAbciApp."""

from enum import Enum
from typing import Dict, FrozenSet, Optional, Set

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    CollectionRound,
    DegenerateRound,
    DeserializedCollection,
    EventToTimeout,
    get_name,
)
from packages.victorpolisetty.skills.alprina_llm_abci.payloads import (
    PromptLlmPayload,
)


class Event(Enum):
    """AlprinaLlmAbciApp Events"""

    DONE = "done"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    def _get_deserialized(self, key: str) -> DeserializedCollection:
        """Strictly get a collection and return it deserialized."""
        serialized = self.db.get_strict(key)
        return CollectionRound.deserialize_collection(serialized)

    @property
    def ipfs_hash_alpaca(self) -> Optional[str]:
        """Get the ipfs_hash_alpaca."""
        return self.db.get("ipfs_hash_alpaca", None)

    @property
    def participant_to_alpaca_historical_data_round(self) -> DeserializedCollection:
        """Get the participants to the hello round."""
        return self._get_deserialized("participant_to_alpaca_round")

    @property
    def ipfs_hash_polygon(self) -> Optional[str]:
        """Get the ipfs_hash_polygon."""
        return self.db.get("ipfs_hash_polygon", None)

    @property
    def participant_to_polygon_sentiment_analysis_round(self) -> DeserializedCollection:
        """Get the participants to the hello round."""
        return self._get_deserialized("participant_to_polygon_round")

    @property
    def alprina_llm(self) -> Optional[str]:
        """Get the hello_data."""
        return self.db.get("hello_data", None)

    @property
    def participant_to_alprina_llm(self) -> DeserializedCollection:
        """Get the participants to the hello round."""
        return self._get_deserialized("participant_to_hello_round")


class PromptLlmRound(CollectSameUntilThresholdRound):
    """PromptLlmRound"""

    payload_class = PromptLlmPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.alprina_llm)
    selection_key = get_name(SynchronizedData.participant_to_alprina_llm)


class FinishedPromptLlmRound(DegenerateRound):
    """FinishedPromptLlmRound"""


class AlprinaLlmAbciApp(AbciApp[Event]):
    """AlprinaLlmAbciApp"""

    initial_round_cls: AppState = PromptLlmRound
    initial_states: Set[AppState] = {
        PromptLlmRound,
    }
    transition_function: AbciAppTransitionFunction = {
        PromptLlmRound: {
            Event.NO_MAJORITY: PromptLlmRound,
            Event.ROUND_TIMEOUT: PromptLlmRound,
            Event.DONE: FinishedPromptLlmRound,
        },
        FinishedPromptLlmRound: {},
    }
    final_states: Set[AppState] = {
        FinishedPromptLlmRound,
    }
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
    db_pre_conditions: Dict[AppState, Set[str]] = {
        PromptLlmRound: set(),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedPromptLlmRound: set(),
    }
