"""
Gossip Protocol Service - Neighbor State Exchange

Implements CRDT-lite gossip protocol for distributed state synchronization.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime
import logging
import sys

sys.path.append("../..")
from shared.database import MongoManager
from shared.models import ServiceHealth, HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QMN Gossip Service", version="0.1.0")
mongo_db: Optional[MongoManager] = None


class GossipMessage(BaseModel):
    """Gossip message for state exchange."""
    region: str
    agent_states: Dict[str, Any]
    edge_updates: List[Dict[str, Any]]
    vector_clock: Dict[str, int]
    timestamp: datetime


@app.on_event("startup")
async def startup():
    global mongo_db
    import os
    mongo_db = MongoManager(os.getenv("MONGO_URL", "mongodb://localhost:27017"), "qmn")
    await mongo_db.connect()
    logger.info("Gossip service started")


@app.on_event("shutdown")
async def shutdown():
    if mongo_db:
        await mongo_db.disconnect()


async def get_mongo() -> MongoManager:
    if mongo_db is None:
        raise HTTPException(status_code=503, detail="MongoDB not available")
    return mongo_db


@app.get("/health", response_model=HealthResponse)
async def health_check(mongo: MongoManager = Depends(get_mongo)):
    healthy = await mongo.health_check()
    return HealthResponse(
        status=ServiceHealth.HEALTHY if healthy else ServiceHealth.UNHEALTHY,
        service="gossip",
        region="us-east-1",
        checks={"mongo": healthy},
    )


@app.post("/v1/gossip:exchange")
async def exchange_state(
    message: GossipMessage,
    mongo: MongoManager = Depends(get_mongo),
):
    """Exchange state with neighbor region."""
    # Update regional state
    await mongo.update_one(
        "regional_state",
        {"_id": f"region:{message.region}"},
        {
            "last_heartbeat": datetime.utcnow(),
            "version": message.vector_clock.get(message.region, 0),
        },
    )

    return {"status": "synced", "timestamp": datetime.utcnow()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8203)
