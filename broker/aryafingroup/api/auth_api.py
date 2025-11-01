import httpx
import os
import requests
import hashlib
from utils.httpx_client import get_httpx_client
from broker.aryafingroup.baseurl import URLConfig
from utils.logging import get_logger

logger = get_logger(__name__)

def hostlookup_login():
    """Send the login url to which a user should receive the token."""
    try:
        BASE_URL = URLConfig.BASE_URL
        HOST_LOOKUP_URL = URLConfig.HOST_LOOKUP_URL
        
        params = {
            "accesspassword": os.getenv('HOSTLOOKUP_ACCESS_PASSWORD', '2021HostLookUpAccess'),
            "version": os.getenv('HOSTLOOKUP_VERSION', 'interactive_1.0.1'),
        }
        
        client = get_httpx_client()

        response = client.post(HOST_LOOKUP_URL, json=params)
        print(response)
        if response.status_code == 200:
            result = response.json().get('result')
            print(f"Hostlookup result: {result}")
            # {'type': True, 'description': 'Hostlookup successful', 'result': {'uniqueKey': 'K0j+aTs2AmSzf68MvHSL16twVovAXMWxfOEUk5sG2GHAx884ZcZsH0y8GtrZbUdQ', 'connectionString': 'http://xtstradingnse.aryafingroup.in:3000/2hostlookup', 'timeStamp': 0, 'remarks': ''}}
            if result.get("connectionString") and result.get("uniqueKey"):
                return result.get('connectionString'), result.get('uniqueKey'), None
            else:
                return None, None, f"Error during hostlookup: Incomplete response data."
    except Exception as e:
        return None, None, f"Error during hostlookup: {str(e)}"
    return None, None, "Error during hostlookup: Unknown error or unexpected response."

def authenticate_broker(request_token):
    try:
        # Get the shared httpx client
        client = get_httpx_client()
        # Fetching the necessary credentials from environment variables
        BROKER_API_KEY = os.getenv('BROKER_API_KEY')
        BROKER_API_SECRET = os.getenv('BROKER_API_SECRET')
        # Call hostlookup to get connectionString and uniqueKey as it is needed
        connectionString, unique_key, hostlookup_error = hostlookup_login()  
        
        if hostlookup_error is not None:
            return None, None, None, hostlookup_error

        print(f'Connection String: {connectionString}, Unique Key: {unique_key}')
        # Make POST request to get the final token
        payload = {
            "appKey": BROKER_API_KEY,
            "secretKey": BROKER_API_SECRET,
            "source": "WebAPI",
            "uniqueKey": unique_key,
        }
        
        headers = {
            'Content-Type': 'application/json'
        }

        session_url = f"{connectionString}/user/session"
        logger.info(f"Authenticating with URL: {session_url} and Payload: {payload}")
        response = client.post(session_url, json=payload, headers=headers)

        logger.info(f"Authentication Response Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Authentication Result: {result}")
            # Update the base URL in URLConfig
            URLConfig.update_base_url(connectionString)
            if result.get('type') == 'success':
                token = result['result']['token']
                logger.info(f"Auth Token: {token}")

                # Call get_feed_token() after successful authentication
                feed_token, user_id, feed_error = get_feed_token()
                if feed_error:
                    return token, None, None, f"Feed token error: {feed_error}"

                return token, feed_token, user_id, None

            else:
                # Access token not present in the response
                return None, None, None, "Authentication succeeded but no access token was returned. Please check the response."
        else:
            # Handling errors from the API
            error_detail = response.json()
            logger.error(f"Authentication Error Detail: {error_detail}")
            error_message = error_detail.get('message', 'Authentication failed. Please try again.')
            return None, None, None, f"API error: {error_message}"
        
    except Exception as e:
        return None, None, None, f"Error during authentication: {str(e)}"


def get_feed_token():
    try:
        # Fetch credentials for feed token
        BROKER_API_KEY_MARKET = os.getenv('BROKER_API_KEY_MARKET')
        BROKER_API_SECRET_MARKET = os.getenv('BROKER_API_SECRET_MARKET')

        # Construct payload for feed token request
        feed_payload = {
            "secretKey": BROKER_API_SECRET_MARKET,
            "appKey": BROKER_API_KEY_MARKET,
            "source": "WebAPI"
        }

        feed_headers = {
            'Content-Type': 'application/json'
        }

        # Get feed token
        feed_url = f"{URLConfig.MARKET_DATA_URL}/auth/login"
        client = get_httpx_client()
        feed_response = client.post(feed_url, json=feed_payload, headers=feed_headers)

        feed_token = None
        user_id = None
        if feed_response.status_code == 200:
            feed_result = feed_response.json()
            if feed_result.get("type") == "success":
                feed_token = feed_result["result"].get("token")
                user_id = feed_result["result"].get("userID")
                logger.info(f"Feed Token: {feed_token}")
            else:
                return None, None, "Feed token request failed. Please check the response."
        else:
            feed_error_detail = feed_response.json()
            feed_error_message = feed_error_detail.get('description', 'Feed token request failed. Please try again.')
            return None, None, f"API Error (Feed): {feed_error_message}"
        
        return feed_token, user_id, None
    except Exception as e:
        return None, None, f"An exception occurred: {str(e)}"
