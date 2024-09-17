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

"""This package contains round behaviours of StockDataApiAbciApp."""

from typing import Set, Type
from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.hello import HelloBehaviour
from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.collect_alpaca_data import CollectAlpacaHistoricalDataBehaviour
from packages.victorpolisetty.skills.stock_data_api_abci.behaviours.collect_polygon_sentiment_analysis import CollectPolygonSentimentAnalysisBehaviour


from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.victorpolisetty.skills.stock_data_api_abci.rounds import StockDataApiAbciApp


class StockDataApiRoundBehaviour(AbstractRoundBehaviour):
    """StockDataApiBehaviour"""

    initial_behaviour_cls = HelloBehaviour
    abci_app_cls = StockDataApiAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = [  # type: ignore
        HelloBehaviour,
        CollectAlpacaHistoricalDataBehaviour,
        CollectPolygonSentimentAnalysisBehaviour,
    ]
