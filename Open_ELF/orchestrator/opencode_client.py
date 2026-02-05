#!/usr/bin/env python3
"""
Optimized OpenCode Client - Single session reuse with heartbeats
Eliminates constant session spawning and cold starts
"""

import requests
import time
import threading
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger("OpenCodeClient")

class OptimizedOpenCodeClient:
    """OpenCode client that reuses a single session with heartbeats"""
    
    def __init__(self, base_url: str = "http://localhost:4096"):
        self.base_url = base_url
        self.http_session = requests.Session()  # Reuse HTTP connection
        self.opencode_session_id = None
        self.last_heartbeat = None
        self.heartbeat_interval = 300  # 5 minutes
        self.session_lock = threading.Lock()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()
        logger.info("🔗 OpenCode client initialized with heartbeat thread")
    
    def _ensure_session(self) -> bool:
        """Ensure we have a valid OpenCode session"""
        with self.session_lock:
            # Create session if none exists
            if not self.opencode_session_id:
                logger.info("🆕 Creating new OpenCode session")
                try:
                    response = self.http_session.post(
                        f"{self.base_url}/session", 
                        json={"title": f"ELF Persistent Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
                        timeout=30  # Longer timeout for cold start
                    )
                    if response.status_code in [200, 201]:
                        self.opencode_session_id = response.json().get("id")
                        self.last_heartbeat = datetime.now()
                        logger.info(f"✅ OpenCode session created: {self.opencode_session_id}")
                        return True
                    else:
                        logger.error(f"❌ Failed to create session: {response.status_code} - {response.text[:200]}")
                        return False
                except Exception as e:
                    logger.error(f"❌ Session creation failed: {e}")
                    return False
            
            # Session exists, check if it's still valid
            try:
                response = self.http_session.get(
                    f"{self.base_url}/session/{self.opencode_session_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    logger.debug(f"✅ Session {self.opencode_session_id} is valid")
                    return True
                else:
                    logger.warning(f"⚠️ Session invalid, creating new one")
                    self.opencode_session_id = None
                    return self._ensure_session()
            except Exception as e:
                logger.warning(f"⚠️ Session check failed, creating new one: {e}")
                self.opencode_session_id = None
                return self._ensure_session()
    
    def _heartbeat_worker(self):
        """Background thread to keep session alive"""
        while True:
            try:
                time.sleep(self.heartbeat_interval)
                
                if self.opencode_session_id:
                    with self.session_lock:
                        logger.debug(f"💓 Sending heartbeat for session {self.opencode_session_id}")
                        try:
                            # Send a simple message to keep session alive
                            response = self.http_session.post(
                                f"{self.base_url}/session/{self.opencode_session_id}/message",
                                json={"parts": [{"type": "text", "text": "[HEARTBEAT] ELF session keepalive"}]},
                                timeout=30
                            )
                            if response.status_code in [200, 201, 204]:
                                self.last_heartbeat = datetime.now()
                                logger.debug("✅ Heartbeat successful")
                            else:
                                logger.warning(f"⚠️ Heartbeat failed: {response.status_code}")
                                self.opencode_session_id = None
                        except Exception as e:
                            logger.warning(f"⚠️ Heartbeat error: {e}")
                            self.opencode_session_id = None
            except Exception as e:
                logger.error(f"❌ Heartbeat worker error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def send_message(self, message: str, agent: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Send message using persistent session
        Returns: (success: bool, response_text: Optional[str])
        """
        # Ensure we have a valid session
        if not self._ensure_session():
            return False, "Failed to establish OpenCode session"
        
        try:
            # Build message body
            body = {"parts": [{"type": "text", "text": message}]}
            if agent:
                body["agent"] = agent
            
            logger.info(f"📤 Sending message to session {self.opencode_session_id[:8]}...")
            response = self.http_session.post(
                f"{self.base_url}/session/{self.opencode_session_id}/message",
                json=body,
                timeout=300  # 5 minute timeout for AI response
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info("✅ Message sent successfully")
                
                # Wait for and get response
                response_text = self._wait_for_response(timeout=300)
                return True, response_text
            else:
                logger.error(f"❌ Message send failed: {response.status_code} - {response.text[:200]}")
                return False, f"HTTP {response.status_code}: {response.text[:200]}"
                
        except Exception as e:
            logger.error(f"❌ Message send error: {e}")
            return False, str(e)
    
    def _wait_for_response(self, timeout: int = 300) -> Optional[str]:
        """Wait for AI response by polling."""
        start_time = time.time()
        poll_interval = 5  # Poll every 5 seconds

        while time.time() - start_time < timeout:
            try:
                response = self.http_session.get(
                    f"{self.base_url}/session/{self.opencode_session_id}/message",
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        messages = data
                    else:
                        messages = data.get("messages", []) if isinstance(data, dict) else []

                    # Look for the latest assistant response
                    for msg in reversed(messages):
                        if not isinstance(msg, dict):
                            continue
                        role = msg.get("role") or msg.get("info", {}).get("role")
                        if role != "assistant":
                            continue
                        content = msg.get("content", "")
                        if not content:
                            parts = msg.get("parts", []) or []
                            content = "".join(
                                part.get("text", "")
                                for part in parts
                                if isinstance(part, dict) and part.get("type") == "text"
                            )
                        if content:
                            logger.info(f"📥 Response received ({len(content)} chars)")
                            return content

                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"⚠️ Response polling error: {e}")
                time.sleep(poll_interval)

        logger.warning("⏰ Response wait timeout")
        return None
    
    def health_check(self) -> bool:
        """Check if OpenCode server is responsive"""
        try:
            response = self.http_session.get(f"{self.base_url}/global/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

# Singleton instance
_client_instance = None
_client_lock = threading.Lock()

def get_opencode_client() -> OptimizedOpenCodeClient:
    """Get singleton OpenCode client instance"""
    global _client_instance
    with _client_lock:
        if _client_instance is None:
            _client_instance = OptimizedOpenCodeClient()
        return _client_instance

if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)
    client = get_opencode_client()
    
    if client.health_check():
        print("✅ OpenCode server is healthy")
        success, response = client.send_message("Hello, this is a test message from optimized client")
        if success:
            print(f"✅ Test message sent successfully: {response[:100]}...")
        else:
            print(f"❌ Test message failed: {response}")
    else:
        print("❌ OpenCode server is not responding")
