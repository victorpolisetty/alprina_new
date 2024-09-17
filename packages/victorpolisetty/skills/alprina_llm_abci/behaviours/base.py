# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

"""This module contains the base behaviour for the 'scraper_abci' skill."""

from abc import ABC
from typing import cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    BaseBehaviour,
)
from packages.victorpolisetty.skills.alprina_llm_abci.models import AlprinaLlmParams, SharedState
from packages.victorpolisetty.skills.alprina_llm_abci.rounds import (
    SynchronizedData,
)


class AlprinaLlmBaseBehaviour(BaseBehaviour, ABC):  # pylint: disable=too-many-ancestors
    """Base behaviour for the alprina_llm_abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> AlprinaLlmParams:
        """Return the params."""
        return cast(AlprinaLlmParams, super().params)

    @property
    def local_state(self) -> SharedState:
        """Return the state."""
        return cast(SharedState, self.context.state)
