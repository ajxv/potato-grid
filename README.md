
# Potato Grid

This is a Python script that creates a grid trading bot. This bot uses the ccxt library to access the Binance exchange and perform automated trades.

## Getting Started

### Prerequisites

To use this bot, you need:

-   Python 3
-   The ccxt library
-   API key and secret key for Binance.

### Installing

1.  Install Python 3 if you haven't already. You can download it from [here](https://www.python.org/downloads/).
    
2.  Install the dependencies using `pip install -r requirements.txt`.
    

### Configuration

 - Before running the bot, you need to configure it using the `config.py` file.
    - You can adjust the `Config` class variables to match your trading preferences.
 - Add your API keys in `keys.py` file: 
	```python
	API_KEY = "api-key-goes-here"
	SECRET_KEY = "secret-key-goes-here"
	```
 

### Running the Bot

Run the bot by executing `python bot.py` in the terminal.

## Functionality

The bot will initially place a number of buy and sell orders on either side of the current market price at intervals of `GRID_STEP_SIZE` and `GRID_SIZE` respectively.

Once the orders are placed, the bot will continually monitor their status. If a buy order is filled, the bot will place a new sell order at a price `GRID_SIZE` above the executed buy price. If a sell order is filled, the bot will place a new buy order at a price `GRID_SIZE` below the executed sell price.

The bot will log all executed trades and their prices in the `orders.json` file.

## Authors

-   [ed](https://github.com/gandalf-the-lonesome)
