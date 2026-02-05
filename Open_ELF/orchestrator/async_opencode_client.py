#!/usr/bin/env python3
"""
Async OpenCode Client - Fully async SSE and HTTP client
Replaces blocking requests with aiohttp for non-blocking operations
"""

import json
import logging
import asyncio
import aiohttp
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("AsyncOpenCodeClient")


class AsyncOpenCodeClient:
    """Fully async OpenCode client for SSE streaming and HTTP requests"""

    def __init__(self, base_url: str = "http://localhost:4096"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.opencode_session_id: Optional[str] = None
        self.last_heartbeat: Optional[datetime] = None
        self.heartbeat_interval = 300  # 5 minutes
        self.session_lock = asyncio.Lock()
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        await self._start_heartbeat()
        logger.info("🔗 Async OpenCode client initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("🔌 Async OpenCode client closed")

    async def _ensure_session(self) -> bool:
        """Ensure we have a valid OpenCode session"""
        async with self.session_lock:
            # Create session if none exists
            if not self.opencode_session_id:
                logger.info("🆕 Creating new OpenCode session")
                try:
                    async with self.session.post(
                        f"{self.base_url}/session",
                        json={
                            "title": f"ELF Async Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        },
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            self.opencode_session_id = data.get("id")
                            self.last_heartbeat = datetime.now()
                            logger.info(
                                f"✅ OpenCode session created: {self.opencode_session_id}"
                            )
                            return True
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"❌ Failed to create session: {response.status} - {error_text[:200]}"
                            )
                            return False
                except Exception as e:
                    logger.error(f"❌ Session creation failed: {e}")
                    return False

            # Session exists, check if it's still valid
            try:
                async with self.session.get(
                    f"{self.base_url}/session/{self.opencode_session_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ Session {self.opencode_session_id} is valid")
                        return True
                    else:
                        logger.warning(f"⚠️ Session invalid, creating new one")
                        self.opencode_session_id = None
                        return await self._ensure_session()
            except Exception as e:
                logger.warning(f"⚠️ Session check failed, creating new one: {e}")
                self.opencode_session_id = None
                return await self._ensure_session()

    async def _start_heartbeat(self):
        """Start heartbeat background task"""
        self.heartbeat_task = asyncio.create_task(self._heartbeat_worker())

    async def _heartbeat_worker(self):
        """Background task to keep session alive"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if self.opencode_session_id:
                    async with self.session_lock:
                        logger.debug(
                            f"💓 Sending heartbeat for session {self.opencode_session_id}"
                        )
                        try:
                            async with self.session.post(
                                f"{self.base_url}/session/{self.opencode_session_id}/message",
                                json={
                                    "parts": [
                                        {
                                            "type": "text",
                                            "text": "[HEARTBEAT] ELF async session keepalive",
                                        }
                                    ]
                                },
                                timeout=aiohttp.ClientTimeout(total=30),
                            ) as response:
                                if response.status in [200, 201, 204]:
                                    self.last_heartbeat = datetime.now()
                                    logger.debug("✅ Heartbeat successful")
                                else:
                                    logger.warning(
                                        f"⚠️ Heartbeat failed: {response.status}"
                                    )
                                    self.opencode_session_id = None
                        except Exception as e:
                            logger.warning(f"⚠️ Heartbeat error: {e}")
                            self.opencode_session_id = None
            except asyncio.CancelledError:
                logger.info("Heartbeat worker cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat worker error: {e}")
                await asyncio.sleep(60)

    async def send_message(
        self, message: str, agent: Optional[str] = None, timeout: int = 300
    ) -> Tuple[bool, Optional[str]]:
        """
        Send message using persistent session
        Returns: (success: bool, response_text: Optional[str])
        """
        if not await self._ensure_session():
            return False, "Failed to establish OpenCode session"

        try:
            body = {"parts": [{"type": "text", "text": message}]}
            if agent:
                body["agent"] = agent

            logger.info(
                f"📤 Sending message to session {self.opencode_session_id[:8]}..."
            )

            async with self.session.post(
                f"{self.base_url}/session/{self.opencode_session_id}/message",
                json=body,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status in [200, 201, 204]:
                    logger.info("✅ Message sent successfully")

                    # Wait for and get response
                    response_text = await self._wait_for_response(timeout=timeout)
                    return True, response_text
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Message send failed: {response.status} - {error_text[:200]}"
                    )
                    return False, f"HTTP {response.status}: {error_text[:200]}"

        except asyncio.TimeoutError:
            logger.error(f"❌ Message send timeout after {timeout}s")
            return False, f"Timeout after {timeout}s"
        except Exception as e:
            logger.error(f"❌ Message send error: {e}")
            return False, str(e)

    async def _wait_for_response(self, timeout: int = 300) -> Optional[str]:
        """Wait for AI response by polling asynchronously."""
        start_time = datetime.now()
        poll_interval = 5  # Poll every 5 seconds

        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                async with self.session.get(
                    f"{self.base_url}/session/{self.opencode_session_id}/message",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            messages = data
                        else:
                            messages = (
                                data.get("messages", [])
                                if isinstance(data, dict)
                                else []
                            )

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
                                    if isinstance(part, dict)
                                    and part.get("type") == "text"
                                )
                            if content:
                                logger.info(
                                    f"📥 Response received ({len(content)} chars)"
                                )
                                return content

                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"⚠️ Response polling error: {e}")
                await asyncio.sleep(poll_interval)

        logger.warning("⏰ Response wait timeout")
        return None

    async def health_check(self) -> bool:
        """Check if OpenCode server is responsive"""
        try:
            async with self.session.get(
                self.base_url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    async def listen_sse(self):
        """
        Async SSE event listener - yields events as they arrive
        Returns an async generator of parsed JSON events
        """
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                logger.info("🎧 Connecting to SSE stream...")

                async with self.session.get(
                    f"{self.base_url}/event",
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                    timeout=aiohttp.ClientTimeout(total=None),  # No timeout for SSE
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ SSE connection failed: {response.status}")
                        await asyncio.sleep(5)
                        retry_count += 1
                        continue

                    logger.info("✅ Connected to SSE stream")
                    retry_count = 0  # Reset on successful connection

                    async for line in response.content:
                        if not self.session or self.session.closed:
                            logger.info("SSE listener stopped")
                            break

                        line_str = line.decode("utf-8").strip()

                        if line_str.startswith("data:"):
                            data_str = line_str[5:].strip()
                            if data_str:
                                try:
                                    event_data = json.loads(data_str)
                                    yield event_data
                                except json.JSONDecodeError as e:
                                    logger.warning(f"⚠️ Failed to parse SSE data: {e}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"❌ SSE connection error: {e}")
                retry_count += 1
                await asyncio.sleep(min(2**retry_count, 30))  # Exponential backoff
            except asyncio.CancelledError:
                logger.info("SSE listener cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected SSE error: {e}")
                retry_count += 1
                await asyncio.sleep(5)

        logger.warning(f"SSE listener stopped after {retry_count} retries")


# Singleton instance
_client_instance: Optional[AsyncOpenCodeClient] = None
_client_lock = asyncio.Lock()


async def get_async_opencode_client() -> AsyncOpenCodeClient:
    """Get singleton async OpenCode client instance"""
    global _client_instance
    async with _client_lock:
        if _client_instance is None:
            _client_instance = AsyncOpenCodeClient()
            await _client_instance.__aenter__()
        return _client_instance


async def close_async_client():
    """Close the singleton async client"""
    global _client_instance
    async with _client_lock:
        if _client_instance is not None:
            await _client_instance.__aexit__(None, None, None)
            _client_instance = None


if __name__ == "__main__":
    # Test the async client
    async def test():
        logging.basicConfig(level=logging.INFO)

        async with AsyncOpenCodeClient() as client:
            # Test health check
            if await client.health_check():
                print("✅ OpenCode server is healthy")

                # Test SSE listener (listen for 5 seconds)
                print("🎧 Listening to SSE events for 5 seconds...")
                event_count = 0
                try:
                    async for event in client.listen_sse():
                        event_count += 1
                        print(
                            f"📨 Event #{event_count}: {event.get('type', 'unknown')}"
                        )
                        if event_count >= 10:
                            break
                except asyncio.TimeoutError:
                    pass

                print(f"✅ Test complete: {event_count} events received")
            else:
                print("❌ OpenCode server is not responding")

    asyncio.run(test())
