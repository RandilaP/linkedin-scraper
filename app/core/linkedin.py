from httpx import AsyncClient
from fastapi import HTTPException
from app.config import settings

async def get_linkedin_access_token():
    async with AsyncClient() as client:
        response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="LinkedIn authentication failed")
        return response.json()["access_token"]