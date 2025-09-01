"""
Manifold Markets API client for oreacle-bot.

This module provides a clean, modular interface for interacting with the Manifold Markets API,
including market retrieval, trading, and commenting functionality.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional
import time
import requests


# API Configuration
DEFAULT_API_BASE = "https://api.manifold.markets/v0"
DEFAULT_TIMEOUT = 20
DEFAULT_MAX_RETRIES = 3
DEFAULT_MARKET_LIMIT = 1000


def create_headers(api_key: str) -> Dict[str, str]:
    """Create HTTP headers for Manifold API requests."""
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

class Outcome(str, Enum):
    """Trading outcome options for Manifold Markets."""
    YES = "YES"
    NO = "NO"


@dataclass
class LimitOrder:
    """Represents a limit order for Manifold Markets."""
    contractId: str
    outcome: Outcome
    amount: int  # M$ integer
    limitProb: float  # 0.0–1.0
    expiresMillisAfter: int = 6 * 60 * 60 * 1000  # 6 hours default

    def validate(self) -> None:
        """Validate order parameters."""
        if self.amount <= 0:
            raise ValueError("Order amount must be positive")
        if not 0.0 <= self.limitProb <= 1.0:
            raise ValueError("Limit probability must be between 0.0 and 1.0")

    def payload(self) -> Dict[str, Any]:
        """Convert order to API payload format."""
        self.validate()
        payload = asdict(self)
        payload["outcome"] = self.outcome.value  # Convert enum to string
        return payload


@dataclass
class Comment:
    """Represents a comment for Manifold Markets."""
    contractId: str
    markdown: str

    def payload(self) -> Dict[str, Any]:
        """Convert comment to API payload format."""
        return asdict(self)

class ManifoldClient:
    """
    Client for interacting with the Manifold Markets API.
    
    This client provides methods for market retrieval, trading, and commenting
    with proper error handling and retry logic.
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = DEFAULT_API_BASE, 
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """Initialize the Manifold API client."""
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self._headers = create_headers(api_key)

    def _make_request(
        self, 
        method: str, 
        path: str, 
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}{path}"
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(
                        url, 
                        headers=self._headers, 
                        params=params,
                        timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = requests.post(
                        url, 
                        headers=self._headers, 
                        json=json_data,
                        timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle retryable errors
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries - 1:
                        sleep_time = 1.5 * (attempt + 1)
                        time.sleep(sleep_time)
                        continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(1.5 * (attempt + 1))
        
        raise RuntimeError("Max retries exceeded")

    def _get_markets(self, limit: int = DEFAULT_MARKET_LIMIT) -> list:
        """Get markets from the API."""
        params = {"limit": limit}
        markets = self._make_request("GET", "/markets", params=params)
        
        if not isinstance(markets, list):
            raise ValueError("Unexpected API response format for markets")
        
        return markets

    def get_market_by_slug(self, slug: str) -> Dict[str, Any]:
        """
        Get market by slug using the correct Manifold API approach.
        
        Args:
            slug: The market slug to search for
            
        Returns:
            Market data dictionary
            
        Raises:
            ValueError: If market is not found
        """
        # First try the direct slug endpoint (if it still exists)
        try:
            return self._make_request("GET", f"/slug/{slug}")
        except (requests.exceptions.HTTPError, ValueError):
            pass
        
        # Fallback: search markets and filter by slug
        markets = self._get_markets()
        
        for market in markets:
            if market.get("slug") == slug:
                return market
        
        raise ValueError(f"No market found for slug: {slug}")

    def place_limit(self, order: LimitOrder) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            order: The limit order to place
            
        Returns:
            Order response from API
        """
        return self._make_request("POST", "/bet", json_data=order.payload())

    def place_limit_yes(
        self, 
        contract_id: str, 
        amount: int, 
        limit_prob: float
    ) -> Dict[str, Any]:
        """
        Place a YES limit order (convenience method).
        
        Args:
            contract_id: The market contract ID
            amount: Order amount in M$
            limit_prob: Limit probability (0.0-1.0)
            
        Returns:
            Order response from API
        """
        order = LimitOrder(contract_id, Outcome.YES, amount, limit_prob)
        return self.place_limit(order)

    def place_limit_no(
        self, 
        contract_id: str, 
        amount: int, 
        limit_prob: float
    ) -> Dict[str, Any]:
        """
        Place a NO limit order (convenience method).
        
        Args:
            contract_id: The market contract ID
            amount: Order amount in M$
            limit_prob: Limit probability (0.0-1.0)
            
        Returns:
            Order response from API
        """
        order = LimitOrder(contract_id, Outcome.NO, amount, limit_prob)
        return self.place_limit(order)

    def post_comment(self, comment: Comment) -> Dict[str, Any]:
        """
        Post a comment to a market.
        
        Args:
            comment: The comment to post
            
        Returns:
            Comment response from API
        """
        return self._make_request("POST", "/comment", json_data=comment.payload())