Steps to install dependencies and get started-

pip install 'fastapi[all]' 'motor[asyncio]' celery requests
pip install redis
brew services start redis
uvicorn main:app --reload
celery -A main.celery worker --loglevel=info

Setup monngodb server:
   brew tap mongodb/brew
1. brew install mongodb-community
2. tar xzvf mongodb-macos*.tgz
3. cd mongodb-macos*
4. sudo cp bin/* /usr/local/bin
5. sudo mkdir -p /usr/local/var/mongodb
6. sudo mkdir -p /usr/local/var/log/mongodb
7. sudo chown $USER /usr/local/var/mongodb
8. sudo chown $USER /usr/local/var/log/mongodb
9. mongod --dbpath /usr/local/var/mongodb --logpath /usr/local/var/log/mongodb/mongo.log --fork
10. mongosh
11. connect mongo atlas compass

Additional Steps(if mongo server don't connect):
nano ~/.zshrc
export PATH="/usr/local/opt/mongodb-community/bin:$PATH"
source ~/.zshrc

Test the Webhook:
http POST http://127.0.0.1:8000/webhooks/ company_id=test url=http://test.com/events headers:='{}' events:='["event1", "event2"]'

Fire an Event:
http POST http://127.0.0.1:8000/fire-event/ '{"event_data": "your_event_data"}'

Using Postman-

1. Create a Webhook Subscription:
Method: POST
URL: http://127.0.0.1:8000/webhooks/
Headers: Content-Type: application/json
Body:
{
  "company_id": "your_company_id",
  "url": "http://example.com/events",
  "headers": {"Authorization": "Bearer token"},
  "events": ["event1", "event2"]
}

2. Update Your Own Webhook Subscription:
Method: PATCH
URL: http://127.0.0.1:8000/webhooks/{webhook_id}/ (Replace {webhook_id} with the actual ID)
Headers: Content-Type: application/json
Body:
{
  "company_id": "your_company_id",
  "url": "http://updated-url.com/events",
  "headers": {"Authorization": "Bearer updated-token"},
  "events": ["updated-event"]
}

3. Delete Your Own Webhook Subscription:
Method: DELETE
URL: http://127.0.0.1:8000/webhooks/{webhook_id}/ (Replace {webhook_id} with the actual ID)

4. Get Your Own Webhook(s) Subscription:
Method: GET
URL: http://127.0.0.1:8000/webhooks/
Query Params: company_id=your_company_id
This will retrieve a list of all webhook subscriptions associated with the specified company ID.

Method: GET
URL: http://127.0.0.1:8000/webhooks/{webhook_id}/ (Replace {webhook_id} with the actual ID)
This will retrieve details about a specific webhook subscription.

5. Fire an Event:
Method: POST
URL: http://127.0.0.1:8000/fire-event/
Headers: Content-Type: application/json
Body:
{
  "event_data": "your_event_data"
}