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

"""This module contains the shared state for the abci skill of HelloAbciApp."""
import os
import json
import base64
from packages.victorpolisetty.skills.stock_data_api_abci.rounds import StockDataApiAbciApp
from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, cast

from aea.exceptions import enforce
from aea.skills.base import Model
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = StockDataApiAbciApp


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


#Params = BaseParams


class Params(BaseParams):
    """A model to represent params for multiple abci apps."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        # self.agent_mech_contract_addresses = kwargs.get(
        #     "agent_mech_contract_addresses", None
        # )
        # enforce(
        #     self.agent_mech_contract_addresses is not None,
        #     "agent_mech_contract_addresses must be set!",
        # )

        # self.in_flight_req: bool = False
        # self.from_block: Optional[int] = None
        # self.req_to_callback: Dict[str, Callable] = {}
        # Load the API keys JSON from the environment variable
        api_keys_json_str = os.getenv("API_KEYS_JSON", "[]")  # Get the JSON string, or default to empty list if not found

        # Parse the JSON string into a list of lists
        api_keys_list = json.loads(api_keys_json_str)

        # Convert the list of lists into a dictionary
        self.api_keys = {key: value for key, value in api_keys_list}
        # self.api_keys: Dict = self._nested_list_todict_workaround(
        #     kwargs, "api_keys_json"
        # )
        print("API KEYS: ", self.api_keys)

        # self.file_hash_to_tools: Dict[
        #     str, List[str]
        # ] = self._nested_list_todict_workaround(
        #     kwargs,
        #     "file_hash_to_tools_json",
        # )
        self.polling_interval = kwargs.get("polling_interval", 30.0)
        self.task_deadline = kwargs.get("task_deadline", 240.0)
        self.num_agents = kwargs.get("num_agents", None)
        self.request_count: int = 0
        self.cleanup_freq = kwargs.get("cleanup_freq", 50)
        enforce(self.num_agents is not None, "num_agents must be set!")
        self.agent_index = kwargs.get("agent_index", None)
        enforce(self.agent_index is not None, "agent_index must be set!")
        self.from_block_range = kwargs.get("from_block_range", None)
        enforce(self.from_block_range is not None, "from_block_range must be set!")
        self.timeout_limit = kwargs.get("timeout_limit", None)
        enforce(self.timeout_limit is not None, "timeout_limit must be set!")
        self.max_block_window = kwargs.get("max_block_window", None)
        enforce(self.max_block_window is not None, "max_block_window must be set!")
        # maps the request id to the number of times it has timed out
        self.request_id_to_num_timeouts: Dict[int, int] = defaultdict(lambda: 0)
        #self.mech_to_config: Dict[str, MechConfig] = self._parse_mech_configs(kwargs)
        super().__init__(*args, **kwargs)


class AlpacaResponseSpecs(ApiSpecs):
    """A model that wraps ApiSpecs for the Alpaca API response specifications."""

    def get_spec(self) -> Dict[str, Any]:
        """Return the specifications for the Alpaca API request."""
        # Access the API keys loaded in Params
        api_key_id = self.context.params.api_keys["APCA-API-KEY-ID"]
        api_secret_key = self.context.params.api_keys["APCA-API-SECRET-KEY"]
        return {
            "method": "GET",
            "url": "https://data.alpaca.markets/v2/stocks/bars",
            "headers": {
                "APCA-API-KEY-ID": api_key_id,
                "APCA-API-SECRET-KEY": api_secret_key,
                "accept": "application/json"
            },
            "parameters": {
                "symbols": "TSLA",
                "timeframe": "1Week",
                "start": "2022-01-01",
                "end": "2023-02-02",
                "limit": 5
            }  # Add any necessary query parameters here
        }


# TODO: Fix this
class PolygonResponseSpecs(ApiSpecs):
    """A model that wraps ApiSpecs for the Polygon API response specifications."""

    def get_spec(self) -> Dict[str, Any]:
        """Return the specifications for the Alpaca API request."""
        # Access the API keys loaded in Params
        api_key = self.context.params.api_keys["POLYGON-API-KEY"]
        return {
            "method": "GET",
            "url": "https://api.polygon.io/v2/reference/news",
            "headers": {
                "accept": "application/json"
            },
            "parameters": {
                "apiKey": api_key,
                "ticker": "TSLA",
                "limit": 2,
            }
        }
