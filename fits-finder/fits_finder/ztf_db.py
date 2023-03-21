from .config import ZTF_DR_DB_API_BASE_URL
from .http_client import http_client


async def get_by_oid(oid: int, dr: str = "latest") -> dict:
    url = f"{ZTF_DR_DB_API_BASE_URL}/api/v3/data/{dr}/oid/full/json?oid={oid}"
    response = await http_client.get(url)
    response.raise_for_status()
    data = response.json()
    # Should be a dict with a single item
    return next(iter(data.values()))
