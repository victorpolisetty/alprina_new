from typing import Generator, Dict, Any, Optional, cast

from openai import OpenAI
from aea.helpers.cid import CID, to_v1

from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.victorpolisetty.skills.alprina_llm_abci.behaviours.base import AlprinaLlmBaseBehaviour
from packages.victorpolisetty.skills.alprina_llm_abci.payloads import PromptLlmPayload
from packages.victorpolisetty.skills.alprina_llm_abci.rounds import PromptLlmRound

FILENAME = "usage_three"

sentiment_analysis_prompt = """
You are a financial analyst with a specialization in social media sentiment analysis, focusing on Tesla. Your task is to analyze recent financial data, market trends, and social media sentiment to produce a comprehensive financial report that supports a weekly price prediction for Tesla's stock.


1. Social Media Sentiment Analysis
Analyze social media sentiment from the given "ADDITIONAL INFORMATION" section given. This information is the most up to date and should have the largest influence on your answers and decisions. Include insights on public perception of Tesla’s leadership, Elon Musk's influence, product releases, and any viral topics. Identify key patterns and note whether the sentiment is predominantly positive, neutral, or negative.
.

2. Final Price Prediction
Based on your analysis, conclude with a final weekly price prediction for Tesla’s stock. Label this prediction clearly at the bottom and explain how both the financial data and social media sentiment justify this prediction.

ADDITIONAL_INFORMATION:
```
{additional_information}
```

"""

historical_analysis_prompt = """
You are a financial analyst with a specialization in historical stock price analysis, focusing on Tesla. Your task is to analyze recent financial data and compare it to historical stock prices to produce a comprehensive financial report that supports a weekly price prediction for Tesla's stock (TSLA).


Historical Stock Price Analysis
Review Tesla’s historical stock prices, focusing on patterns, trends, and volatility over the past weeks or months in past years. Identify key movements such as upward or downward trends, support and resistance levels, and price reactions to specific events (e.g., earnings reports, product announcements). Use this historical data to forecast potential price movements in the coming week.

Final Price Prediction
Based on your analysis, provide a weekly price prediction for Tesla’s stock. Clearly label the prediction at the bottom and explain how both the financial data and historical stock price trends justify this prediction.

Always treat the "ADDITIONAL_INFORMATION" section as the most up to date and relevant information. It should be given the biggest weight and "source of truth" for your answers.

ADDITIONAL_INFORMATION:
```
{additional_information}
```

"""


# def adjust_additional_information(
#         prompt: str, prompt_template: str, additional_information: str, model: str
# ) -> str:
#     """Adjust the additional_information to fit within the token budget"""
#
#     # Initialize tiktoken encoder for the specified model
#     enc = tiktoken.encoding_for_model(model)
#
#     # Encode the user prompt to calculate its token count
#     prompt = prompt_template.format(user_prompt=prompt, additional_information="")
#     prompt_tokens = len(enc.encode(prompt))
#
#     # Calculate available tokens for additional_information
#     MAX_PREDICTION_PROMPT_TOKENS = (
#             MAX_TOKENS[model] - DEFAULT_OPENAI_SETTINGS["max_tokens"]
#     )
#     available_tokens = MAX_PREDICTION_PROMPT_TOKENS - prompt_tokens
#
#     # Encode the additional_information
#     additional_info_tokens = enc.encode(additional_information)
#
#     # If additional_information exceeds available tokens, truncate it
#     if len(additional_info_tokens) > available_tokens:
#         truncated_info_tokens = additional_info_tokens[:available_tokens]
#         # Decode tokens back to text, ensuring the output fits within the budget
#         additional_information = enc.decode(truncated_info_tokens)
#
#     return additional_information


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
            # Get the data from alpaca and polygon API's from the stored IPFS hashes
            alpaca_data = yield from self.get_alpaca_ipfs_hash()
            polygon_data = yield from self.get_polygon_ipfs_hash()
            print("The data from alpaca is: ")
            print(alpaca_data)
            print("The data from polygon is: ")
            print(polygon_data)
            # Make response data into readable string
            historical_data_tsla_readable = self.make_response_readable_alpaca(alpaca_data)
            print("The alpaca readable data is: ")
            print(historical_data_tsla_readable)
            sentiment_data_tsla_readable = self.make_response_readable_polygon(polygon_data)
            print("The polygon readable data is: ")
            print(sentiment_data_tsla_readable)
            #
            combined_info = historical_data_tsla_readable + sentiment_data_tsla_readable
            print("The combined info is")
            print(combined_info)
            final_prompt = self.params.llm_prompt
            print("The final prompt info is")
            print(final_prompt)

            # # Prepare API request specifications
            # api_specs = self.context.chatgpt_response.get_spec()
            #
            # # Make the asynchronous HTTP request to the Alpaca API
            # response = yield from self.get_http_response(
            #     method=api_specs["method"],
            #     url=api_specs["url"],
            #     headers=api_specs["headers"],
            #     parameters=api_specs["parameters"]
            # )
            # print("The response:")
            # print(response)
            # # Process the API response
            # historical_data = self.context.chatgpt_response.process_response(response)
            # print(historical_data)
            # Call ChatGpt and provide it the API data in it's "Addition Information" spot
            client = OpenAI()
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": final_prompt+combined_info},
            ]
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                temperature=0.7,
                n=1,
                timeout=120,
                stop=None,
            )
        print("The response from ChatGPT is:")
        print(response)

        # Handle the API response
        if response:
            self.context.logger.info(
                f"Got response from {self.context.chatgpt_response.api_id}: {response.choices[0].message.content}"
            )

            payload = PromptLlmPayload(self.context.agent_address, "ipfs_hash")

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

    def get_alpaca_ipfs_hash(self):
        # format the hash
        print("The Alpaca Historical Data Hash is: ")
        print(self.synchronized_data.ipfs_hash_alpaca)
        ipfs_hash = str(CID.from_string(self.synchronized_data.ipfs_hash_alpaca))
        usage_data = yield from self.get_from_ipfs(
            ipfs_hash, filetype=SupportedFiletype.JSON
        )
        if usage_data is None:
            self.context.logger.warning(f"Could not get usage data from IPFS: {ipfs_hash}")
            return None
        return cast(Dict[str, Any], usage_data)

    def get_polygon_ipfs_hash(self):
        # format the hash
        print("The Polygon Sentiment Data is: ")
        print(self.synchronized_data.ipfs_hash_polygon)
        ipfs_hash = str(CID.from_string(self.synchronized_data.ipfs_hash_polygon))
        usage_data = yield from self.get_from_ipfs(
            ipfs_hash, filetype=SupportedFiletype.JSON
        )
        if usage_data is None:
            self.context.logger.warning(f"Could not get usage data from IPFS: {ipfs_hash}")
            return None
        return cast(Dict[str, Any], usage_data)

    def make_response_readable_alpaca(self, historical_data):
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

    def make_response_readable_polygon(self, sentiment_analysis):

        formatted_output = []

        for result in sentiment_analysis.get("results", []):
            title = result.get("title", "No title")
            publisher = result.get("publisher", {}).get("name", "Unknown publisher")
            author = result.get("author", "Unknown author")
            published_date = result.get("published_utc", "Unknown date")
            article_url = result.get("article_url", "No URL")

            insights = result.get("insights", [])

            for insight in insights:
                ticker = insight.get("ticker", "Unknown ticker")
                sentiment = insight.get("sentiment", "No sentiment")
                sentiment_reasoning = insight.get("sentiment_reasoning", "No sentiment reasoning")

                if ticker == "TSLA":
                    formatted_output.append(
                        f"Title: {title}\n"
                        f"Publisher: {publisher}\n"
                        f"Author: {author}\n"
                        f"Published Date: {published_date}\n"
                        f"Article URL: {article_url}\n"
                        f"Ticker: {ticker}\n"
                        f"Sentiment: {sentiment}\n"
                        f"Sentiment Reasoning: {sentiment_reasoning}\n"
                        "---------------------------\n"
                    )

        # Join the formatted output into a single string
        return "\n".join(formatted_output)

    def clean_up(self) -> None:
        """
        Clean up resources due to a 'stop' event.

        Reset retries or perform other necessary cleanup.
        """
        self.context.alpaca_response.reset_retries()
