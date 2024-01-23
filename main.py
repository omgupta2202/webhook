from fastapi import FastAPI, HTTPException, Body
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pydantic import BaseModel
from celery import Celery
from typing import List
from requests import post
from bson import ObjectId
from datetime import datetime

app = FastAPI()

# MongoDB
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "webhooks"
webhook_collection_name = "webhook"

# Celery
celery = Celery(
    "webhook_tasks",
    backend="redis://localhost:6379/0",
    broker="redis://localhost:6379/0",
)


class Webhook(BaseModel):
    company_id: str
    url: str
    headers: dict = None
    events: List[str]
    is_active: bool = True


class WebhookDB(Webhook):
    id: str
    created_at: int
    updated_at: int


@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client[DATABASE_NAME]
    app.webhook_collection = app.mongodb[webhook_collection_name]


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


@app.post("/webhooks/", response_model=WebhookDB)
async def create_webhook(webhook: Webhook = Body(...)):
    try:
        webhook_data = webhook.dict()
        webhook_data["created_at"] = webhook_data["updated_at"] = int(datetime.utcnow().timestamp())
        result = await app.webhook_collection.insert_one(webhook_data)
        webhook_data["id"] = str(result.inserted_id)
        creation_time = result.inserted_id.generation_time.timestamp()
        # webhook_data["created_at"] = webhook_data["updated_at"] = int(creation_time)
        return webhook_data
    except Exception as e:
        print(f"Error in create_webhook: {e}")
        raise HTTPException(status_code=520, detail="Unknown Reason")



@app.patch("/webhooks/{webhook_id}/", response_model=WebhookDB)
async def update_webhook(webhook_id: str, webhook: Webhook = Body(...)):
    webhook_id = webhook_id.strip('{}')
    decoded_webhook_id = ObjectId(webhook_id)
    result = await app.webhook_collection.update_one({"_id": decoded_webhook_id}, {"$set": webhook.dict()})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    updated_webhook = await app.webhook_collection.find_one({"_id": decoded_webhook_id})
    updated_webhook["id"] = str(updated_webhook["_id"])
    updated_webhook["created_at"] = int(updated_webhook["_id"].generation_time.timestamp())
    updated_webhook["updated_at"] = int(datetime.utcnow().timestamp())
    return WebhookDB(**updated_webhook)


@app.delete("/webhooks/{webhook_id}/", response_model=dict)
async def delete_webhook(webhook_id: str):
    webhook_id = webhook_id.strip('{}')
    decoded_webhook_id = ObjectId(webhook_id)
    result = await app.webhook_collection.delete_one({"_id": decoded_webhook_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted successfully"}


@app.get("/webhooks/", response_model=List[WebhookDB])
async def list_webhooks():
    webhooks = await app.webhook_collection.find().to_list(length=None)
    webhooks_with_id = [{"id": str(webhook["_id"]), **webhook} for webhook in webhooks]
    return [WebhookDB(**webhook) for webhook in webhooks_with_id]


@app.get("/webhooks/{webhook_id}/", response_model=WebhookDB)
async def get_webhook(webhook_id: str):
    webhook_id = webhook_id.strip('{}')
    decoded_webhook_id = ObjectId(webhook_id)
    webhook = await app.webhook_collection.find_one({"_id": decoded_webhook_id})
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookDB(**webhook, id=str(webhook["_id"]))

# Celery Task
@celery.task(bind=True, max_retries=3)
def send_webhook(self, webhook_url: str, headers: dict, event_data: dict):
    try:
        response = post(webhook_url, json=event_data, headers=headers)
        response.raise_for_status()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    if response.status_code != 200:
        raise self.retry(exc=Exception(f"Non-200 status code: {response.status_code}"), countdown=2 ** self.request.retries)
    pass


@app.post("/fire-event/", response_model=dict)
async def fire_event(event_data: dict):
    company_id = "test"
    webhooks = await app.webhook_collection.find({"company_id": company_id, "is_active": True}).to_list(length=None)
    for webhook in webhooks:
        send_webhook.apply_async(args=(webhook["url"], webhook["headers"], event_data))
    return {"message": "Event fired successfully"}
