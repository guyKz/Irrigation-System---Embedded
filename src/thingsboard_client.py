"""
ThingsBoard HTTP API Client
Handles sending telemetry data to ThingsBoard cloud
"""
import requests
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ThingsBoardClient:
    """Client for communicating with ThingsBoard HTTP API"""
    
    def __init__(self, host: str, token: str, use_https: bool = True):
        """
        Initialize ThingsBoard client
        
        Args:
            host: ThingsBoard server hostname
            token: Device access token
            use_https: Use HTTPS protocol (default: True)
        """
        self.host = host
        self.token = token
        self.use_https = use_https
        self.scheme = "https" if use_https else "http"
        self.base_url = f"{self.scheme}://{self.host}"
        self.telemetry_url = f"{self.base_url}/api/v1/{self.token}/telemetry"
        
        # Statistics
        self.total_sent = 0
        self.total_failed = 0
        self.last_send_time = None
        
        logger.info(f"ThingsBoard client initialized: {self.base_url}")
        logger.info(f"Telemetry endpoint: {self.telemetry_url}")
    
    def send_telemetry(self, data: Dict, timeout: int = 8) -> bool:
        """
        Send telemetry data to ThingsBoard
        
        Args:
            data: Dictionary with telemetry key-value pairs
            timeout: Request timeout in seconds
            
        Returns:
            True if successful (2xx response), False otherwise
        """
        try:
            logger.debug(f"Sending telemetry: {data}")
            
            response = requests.post(
                self.telemetry_url,
                json=data,
                timeout=timeout
            )
            
            self.last_send_time = datetime.now()
            
            if response.ok:
                self.total_sent += 1
                logger.debug(f"Telemetry sent successfully (#{self.total_sent})")
                return True
            else:
                self.total_failed += 1
                # Compact error message
                error_msg = (response.text or "").strip().replace("\n", " ")[:200]
                logger.error(
                    f"ThingsBoard error: {response.status_code} {response.reason} - {error_msg}"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.total_failed += 1
            logger.error(f"Timeout sending to ThingsBoard (timeout={timeout}s)")
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.total_failed += 1
            logger.error(f"Connection error: {e}")
            return False
            
        except Exception as e:
            self.total_failed += 1
            logger.error(f"Unexpected error sending telemetry: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to ThingsBoard by sending empty telemetry
        
        Returns:
            True if connection successful
        """
        logger.info("Testing ThingsBoard connection...")
        test_data = {"test": "connection"}
        result = self.send_telemetry(test_data)
        
        if result:
            logger.info("✓ ThingsBoard connection successful")
        else:
            logger.error("✗ ThingsBoard connection failed")
        
        return result
    
    def get_stats(self) -> Dict:
        """
        Get client statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "success_rate": (
                self.total_sent / (self.total_sent + self.total_failed) * 100
                if (self.total_sent + self.total_failed) > 0
                else 0
            ),
            "last_send_time": self.last_send_time.isoformat() if self.last_send_time else None
        }
    
    def print_stats(self):
        """Print statistics to console"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("THINGSBOARD CLIENT STATISTICS")
        print("=" * 60)
        print(f"Total Sent:      {stats['total_sent']}")
        print(f"Total Failed:    {stats['total_failed']}")
        print(f"Success Rate:    {stats['success_rate']:.1f}%")
        print(f"Last Send:       {stats['last_send_time'] or 'Never'}")
        print("=" * 60 + "\n")