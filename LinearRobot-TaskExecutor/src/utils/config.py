"""Configuration fetching utilities"""
import json
import requests
from ..constants import API_BASE_URL


def fetch_layout(layout_id: str) -> dict:
    """
    Fetch layout configuration from the API.
    
    Args:
        layout_id: The layout identifier
        
    Returns:
        Dictionary containing layout data with place positions
    """
    url = f"{API_BASE_URL}/layout/{layout_id}"
    response = requests.get(url)
    return response.json()

def fetch_config(config_name: str) -> dict:
    """
    Fetch configuration from the API.
    
    Returns:
        Dictionary containing configuration data
    """
    url = f"{API_BASE_URL}/config/{config_name}"
    response = requests.get(url)
    return response.json()['value']


def fetch_program(program_name: str) -> dict:
    """
    Fetch program from the API.
    
    Returns:
        Dictionary containing program data
    """
    url = f"{API_BASE_URL}/program/{program_name}"
    response = requests.get(url)
    return response.json()['program']


def push_config(parameter_name: str, parameter_value: str):
    """
    Push configuration to the API.
    
    Args:
        parameter_name: The parameter name
        parameter_value: The parameter value
    """
    url = f"{API_BASE_URL}/config/{parameter_name}"
    response = requests.put(url, json={'value': parameter_value})
    return response.json()