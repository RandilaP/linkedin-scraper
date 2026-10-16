from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import os
from datetime import datetime
import jwt
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(title="Professional Jobs API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables (in production, use proper env management)
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

# OAuth2 scheme for endpoint protection
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    posted_date: datetime
    experience_level: Optional[str]
    employment_type: Optional[str]
    skills: List[str] = Field(default_factory=list)

class JobResponse(BaseModel):
    jobs: List[Job]
    total: int
    page: int
    per_page: int

async def get_linkedin_access_token():
    """Get access token from LinkedIn OAuth2"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "client_credentials",
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET,
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to authenticate with LinkedIn")
        return response.json()["access_token"]

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/api/v1/jobs", response_model=JobResponse)
async def get_jobs(
    token: str = Depends(verify_token),
    keywords: Optional[str] = Query(None, description="Search keywords"),
    location: Optional[str] = Query(None, description="Job location"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """
    Get job listings with various filters.
    Uses LinkedIn's Marketing API to fetch real job data.
    """
    try:
        linkedin_token = await get_linkedin_access_token()
        
        # Build LinkedIn API query
        query_params = {
            "keywords": keywords,
            "location": location,
            "experience": experience_level,
            "start": (page - 1) * per_page,
            "count": per_page,
        }
        
        # Remove None values
        query_params = {k: v for k, v in query_params.items() if v is not None}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.linkedin.com/v2/jobs",
                params=query_params,
                headers={"Authorization": f"Bearer {linkedin_token}"},
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch jobs from LinkedIn"
                )
            
            data = response.json()
            
            # Transform LinkedIn response to our Job model
            jobs = [
                Job(
                    id=item["id"],
                    title=item["title"],
                    company=item["company"]["name"],
                    location=item["location"]["name"],
                    description=item["description"],
                    posted_date=datetime.fromisoformat(item["posted_date"]),
                    experience_level=item.get("experience_level"),
                    employment_type=item.get("employment_type"),
                    skills=item.get("skills", [])
                )
                for item in data["elements"]
            ]
            
            return JobResponse(
                jobs=jobs,
                total=data["paging"]["total"],
                page=page,
                per_page=per_page
            )
            
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)