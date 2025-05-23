import json
import logging
import time

import boto3
import yfinance as yf
from botocore.config import Config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_community.chat_models import BedrockChat
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    logger.info("Initializing Bedrock client...")
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=boto3.session.Session().region_name,
        config=Config(retries={'max_attempts': 5, 'mode': 'adaptive'})
    )
    logger.info("Bedrock client initialized successfully")

    logger.info("Initializing Claude 3 Sonnet model...")
    llm = BedrockChat(
        client=bedrock_client,
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs={
            "temperature": 0.1,
            "max_tokens": 1024,
            "top_p": 0.9
        }
    )
    logger.info("Claude 3 Sonnet model initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Bedrock: {str(e)}")
    raise

class Query(BaseModel):
    text: str

def get_realtime_stock_price(symbol: str) -> str:
    try:
        # Clean and validate symbol
        symbol = symbol.strip().upper()
        logger.info(f"Fetching real-time price for {symbol}")
        
        stock = yf.Ticker(symbol)
        
        # First try to get the current price from info
        try:
            current_price = (
                stock.info.get('regularMarketPrice') or 
                stock.info.get('currentPrice') or 
                stock.info.get('lastPrice')
            )
            if current_price is not None:
                logger.info(f"Price fetched from info: {symbol} = ${current_price:.2f}")
                return f"Current price of {symbol} is ${current_price:.2f}"
        except Exception as e:
            logger.warning(f"Failed to get price from info: {str(e)}")
        
        # If info fails, try getting the latest price from history
        try:
            hist = stock.history(period='1d', interval='1m')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                logger.info(f"Price fetched from history: {symbol} = ${current_price:.2f}")
                return f"Current price of {symbol} is ${current_price:.2f}"
        except Exception as e:
            logger.warning(f"Failed to get price from history: {str(e)}")
        
        # If both methods fail, try one last time with a different interval
        try:
            hist = stock.history(period='1d', interval='5m')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                logger.info(f"Price fetched from 5m history: {symbol} = ${current_price:.2f}")
                return f"Current price of {symbol} is ${current_price:.2f}"
        except Exception as e:
            logger.warning(f"Failed to get price from 5m history: {str(e)}")
        
        raise ValueError(f"Could not fetch price for {symbol} using any method")
        
    except Exception as e:
        logger.error(f"Error in get_realtime_stock_price: {str(e)}")
        raise ValueError(f"Failed to fetch price for {symbol}: {str(e)}")

def get_realtime_stock_price_wrapped(input_str: str) -> str:
    try:
        symbol = input_str.strip()
        return get_realtime_stock_price(symbol)
    except Exception as e:
        return f"Error getting real-time price: {str(e)}"

def get_historical_stock_price(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    try:
        print(f"Fetching historical data for {symbol} over period: {period} with interval: {interval}")

        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            raise ValueError(f"No historical data available for {symbol} with period {period} and interval {interval}")

        data = hist['Close'].to_dict()
        formatted_data = {str(k.date()): round(v, 2) for k, v in data.items()}

        result = {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "data_points": len(formatted_data),
            "first_date": min(formatted_data.keys()),
            "last_date": max(formatted_data.keys()),
            "first_price": formatted_data[min(formatted_data.keys())],
            "last_price": formatted_data[max(formatted_data.keys())],
            "data": formatted_data
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
        raise

def get_historical_stock_price_wrapped(input_str: str) -> str:
    try:
        symbol, period, interval = input_str.split(",")
        return get_historical_stock_price(symbol.strip(), period.strip(), interval.strip())
    except Exception as e:
        return f"Error parsing input: {str(e)}"

tools = [
    Tool(
        name="get_realtime_stock_price",
        func=get_realtime_stock_price_wrapped,
        description="Get the current stock price for a given symbol. Input should be a stock symbol like 'AAPL' or 'MSFT'"
    ),
    Tool(
        name="get_historical_stock_price",
        func=get_historical_stock_price_wrapped,
        description="Get historical stock prices. Input format: 'AAPL,1mo,1d'"
    )
]

prompt = PromptTemplate.from_template("""You are a helpful AI assistant that helps users with stock market queries. You have access to the following tools:

{tools}

For historical data queries, use the get_historical_stock_price tool with input format: 'SYMBOL,PERIOD,INTERVAL'
For current price queries, use the get_realtime_stock_price tool with just the stock symbol.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}""")

try:
    logger.info("Creating ReAct agent...")
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,  # Increased from 3 to 5
        handle_parsing_errors=True,
        return_intermediate_steps=True  # Added to help with debugging
    )
    logger.info("ReAct agent created successfully")
except Exception as e:
    logger.error(f"Error creating ReAct agent: {str(e)}")
    raise

@app.post("/query")
async def process_query(query: Query):
    try:
        logger.info(f"Processing query: {query.text}")
        # Add a 1-second delay between requests
        time.sleep(1)
        response = agent_executor.invoke({"input": query.text})
        logger.info("Query processed successfully")
        
        # Extract the final answer or error message
        if "output" in response:
            return {"response": response["output"]}
        elif "error" in response:
            return {"response": f"Error: {response['error']}"}
        else:
            return {"response": str(response)}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 