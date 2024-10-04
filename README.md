# Alprina

A multi-agent system that generates a financial report and weekly price prediction (per agent) for Tesla (TSLA) stock.

## Why is this useful?

Banks and hedgefunds spend millions hiring hundreds of analysts the make stock price predictions. Using AI agents, we can automate this process and do a much better job. It is impossible for one human to sift through as much data as an AI powered agent can. Imagine hundreds of these agents all searching for different trends to predict prices and supporting these with evidence. This could revolutionize the financial market industry.

Morningstar provides a great visual example of how analyst price predictions currently are, and serve as a guide to how we could make this process more autonomous and efficient. See below.

<img width="781" alt="Screenshot 2024-10-04 at 3 46 53 PM" src="https://github.com/user-attachments/assets/209c0dbd-6823-409d-af0a-83e9d4076286">

## Example

Agent 1 has persona "analyze historical stock prices" and gives it's price financial report and weekly price prediction

Agent 2 has persona "analyze social media sentiment" and gives it's price financial report and weekly price prediction

## Conceptual Steps
- Pulls from Alpaca API to get up-to-date information about Tesla (TSLA) stock
- Pulls from Polygon API to get up-to-date social media sentiment about Tesla (TSLA) stock
- Utilizes ChatGPT and data fed in from given APIs to create a financial report and predict what the stock price of Tesla (TSLA) will be at the end of the current week

<img width="818" alt="Screenshot 2024-10-04 at 3 42 05 PM" src="https://github.com/user-attachments/assets/3be10c94-6c1f-49dc-baa0-d611abe15c5c">

## System requirements

- Python `>=3.8`
- [Tendermint](https://docs.tendermint.com/v0.34/introduction/install.html) `==0.34.19`
- [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==0.6.0`
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Poetry](https://python-poetry.org/)
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)


## How to use

1. Create a virtual environment with all development dependencies:

    ```bash
    poetry shell
    poetry install
    autonomy packages sync --update-packages
    ```

2. Prepare an `ethereum_private_key.txt` (for agents) file and `keys.json` (for services) files containing wallet address and/or the private key for each of the agents. You can generate a new key by running `autonomy generate-key ethereum`. This is how those files should look like:

    ethereum_private_key.txt (check that there are no newlines at the end)

    ```
    0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a
    ```

    keys.json
    ```
    [
        {
            "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
            "private_key": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
        }
    ]
    ```

3. Modify `packages/author/agents/demo_agent/aea-config.yaml` so `all_participants` contains your agent's public address.


5. Make a copy of the env file:

    ```cp sample.env .env```

5. Fill in the required environment variables in .env. You'll need a Ethereum RPC. `ALL_PARTICIPANTS` needs to contain your agent's public address. You will need to fill in each API key necessary in the .env file


6. Test the agent. Make sure to add api keys in api_keys_json param in the aea-config.yaml file to run the agent successfully. Also, make sure there is only one agent address in .env all_participants and aea-config.yaml all_participants

    ```bash
    ./run_agent.py
    ```

    and in other terminal run Tendermint:

    ```bash
    make tm
    ```

7. Test the service

    ```bash
    ./run_service.py
    ```


## Future Improvements

- Add more API's to get more up to date data
- Refine prompts for better accuracy
- Fine tune a custom GPT model with more data

## Notes

- This MVP should be run as a service with 2 agents.
- Make sure the 2 agents addresses are in the .env `ALL_PARTICIPANTS` and the `all_participants` in the aea_config.yaml
- Need API keys for Alpaca, Polygon, and ChatGPT API's
