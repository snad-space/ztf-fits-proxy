from httpx import AsyncClient, Limits


# https://stackoverflow.com/a/74397436/5437597


class HTTPXClientWrapper:
    def __init__(self):
        self.client = None

    def start(self):
        """Instantiate the client. Call from the FastAPI startup hook."""
        self.client = AsyncClient(
            timeout=60,
            limits=Limits(max_connections=10, max_keepalive_connections=10, keepalive_expiry=60),
        )

    async def stop(self):
        """Gracefully shutdown. Call from FastAPI shutdown hook."""
        await self.client.aclose()
        self.client = None

    def __getattr__(self, item):
        """Forward all other attributes to the client."""
        if self.client is None:
            raise RuntimeError("Client not instantiated. Call start() first.")
        return getattr(self.client, item)


http_client = HTTPXClientWrapper()
