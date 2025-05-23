import json
import time
from typing import Any, Dict

import requests


def test_stock_api(endpoint: str, query: str) -> Dict[str, Any]:
    """
    Test the stock query API endpoint with a given query.
    
    Args:
        endpoint (str): The API endpoint URL
        query (str): The query to send to the API
        
    Returns:
        Dict[str, Any]: The API response
    """
    try:
        print(f"Sending request to: {endpoint}")
        response = requests.post(
            endpoint,
            json={"text": query},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        # Print response details for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}")
        return {"error": str(e)}

def main():
    # API endpoint
    endpoint = "https://ukyai7smrnayjgyx5ayw2ium6i0jhufn.lambda-url.us-east-1.on.aws/query"
    
    # Test cases
    test_queries = [
        "What is the current price of Apple stock?",
        "Show me the historical prices of MSFT for the last month"
    ]
    
    print("Testing Stock Query API\n")
    print("-" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        response = test_stock_api(endpoint, query)
        
        if "error" in response:
            print(f"Error: {response['error']}")
        else:
            print("Response:")
            print(json.dumps(response, indent=2))
        
        print("-" * 50)
        time.sleep(1)  # Add a small delay between requests

if __name__ == "__main__":
    main() 