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

"""This package contains the rounds of StockDataApiAbciApp."""

from enum import Enum
from typing import Dict, FrozenSet, Optional, Set

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    CollectionRound,
    DegenerateRound,
    DeserializedCollection,
    EventToTimeout,
    get_name,
)
from packages.victorpolisetty.skills.stock_data_api_abci.payloads import (
    CollectRandomnessPayload,
    SelectKeeperPayload,
    CollectAlpacaHistoricalDataPayload,
    CollectPolygonSentimentAnalysisPayload,
)


class Event(Enum):
    """StockDataApiAbciApp Events"""

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
    def hello_data(self) -> Optional[str]:
        """Get the hello_data."""
        return self.db.get("hello_data", None)

    @property
    def participant_to_hello_round(self) -> DeserializedCollection:
        """Get the participants to the hello round."""
        return self._get_deserialized("participant_to_hello_round")

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


class CollectRandomnessRound(CollectSameUntilThresholdRound):
    """A round for collecting randomness"""

    payload_class = CollectRandomnessPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = get_name(SynchronizedData.most_voted_randomness)


class SelectKeeperRound(CollectSameUntilThresholdRound):
    """A round in a which keeper is selected"""

    payload_class = SelectKeeperPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_selection)
    selection_key = get_name(SynchronizedData.most_voted_keeper_address)


class CollectAlpacaHistoricalDataRound(OnlyKeeperSendsRound):
    """CollectAlpacaHistoricalDataRound"""

    keeper_payload: Optional[CollectAlpacaHistoricalDataPayload] = None
    payload_class = CollectAlpacaHistoricalDataPayload
    synchronized_data_class = SynchronizedData

    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    # payload_key = (SynchronizedData.participant_to_alpaca_historical_data_round, SynchronizedData.ipfs_hash_alpaca)
    payload_key = "ipfs_hash_alpaca"
    # collection_key = get_name(SynchronizedData.participant_to_alpaca_historical_data_round)
    # selection_key = get_name(SynchronizedData.ipfs_hash_alpaca)


class CollectPolygonSentimentAnalysisRound(OnlyKeeperSendsRound):
    """CollectPolygonSentimentAnalysisRound"""

    keeper_payload: Optional[CollectPolygonSentimentAnalysisPayload] = None
    payload_class = CollectPolygonSentimentAnalysisPayload
    synchronized_data_class = SynchronizedData

    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    # collection_key = get_name(SynchronizedData.participant_to_polygon_sentiment_analysis_round)
    # selection_key = get_name(SynchronizedData.ipfs_hash_polygon)
    payload_key = "ipfs_hash_polygon"


class FinishedHelloRound(DegenerateRound):
    """FinishedHelloRound"""


class StockDataApiAbciApp(AbciApp[Event]):
    """StockDataApiAbciApp"""

    initial_round_cls: AppState = CollectRandomnessRound
    initial_states: Set[AppState] = {
        CollectRandomnessRound,
    }
    transition_function: AbciAppTransitionFunction = {
        CollectRandomnessRound: {
            Event.DONE: SelectKeeperRound,
            Event.NO_MAJORITY: CollectRandomnessRound,
            Event.ROUND_TIMEOUT: CollectRandomnessRound,
        },
        SelectKeeperRound: {
            Event.DONE: CollectAlpacaHistoricalDataRound,
            Event.NO_MAJORITY: SelectKeeperRound,
            Event.ROUND_TIMEOUT: SelectKeeperRound,
        },
        CollectAlpacaHistoricalDataRound: {
            Event.DONE: CollectPolygonSentimentAnalysisRound,
            Event.NO_MAJORITY: CollectAlpacaHistoricalDataRound,
            Event.ROUND_TIMEOUT: CollectAlpacaHistoricalDataRound,
        },
        CollectPolygonSentimentAnalysisRound: {
            Event.DONE: FinishedHelloRound,
            Event.NO_MAJORITY: CollectPolygonSentimentAnalysisRound,
            Event.ROUND_TIMEOUT: CollectPolygonSentimentAnalysisRound,
        },
        FinishedHelloRound: {},
    }
    final_states: Set[AppState] = {
        FinishedHelloRound,
    }
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
    db_pre_conditions: Dict[AppState, Set[str]] = {
        CollectRandomnessRound: set(),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedHelloRound: set(),
    }
