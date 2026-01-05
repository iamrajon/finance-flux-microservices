import pika
import json
import os
import threading
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ExpenseCache
from datetime import datetime


def process_expense_event(ch, method, properties, body):
    """Process expense events from RabbitMQ"""
    try:
        message = json.loads(body)
        event_type = message.get('event_type')
        data = message.get('data')
        
        print(f"Received event: {event_type}")
        
        db = SessionLocal()
        
        if event_type == 'expense.created':
            expense_cache = ExpenseCache(
                expense_id=data['expense_id'],
                user_id=data['user_id'],
                amount=data['amount'],
                category_id=data['category_id'],
                date=datetime.fromisoformat(data['date'])
            )
            db.add(expense_cache)
            db.commit()
            print(f"Cached expense {data['expense_id']}")
        
        elif event_type == 'expense.updated':
            # Update cached expense
            cached = db.query(ExpenseCache).filter(
                ExpenseCache.expense_id == data['expense_id']
            ).first()
            if cached:
                cached.amount = data['amount']
                cached.category_id = data['category_id']
                db.commit()
                print(f"Updated cached expense {data['expense_id']}")
        
        elif event_type == 'expense.deleted':
            # Remove from cache
            cached = db.query(ExpenseCache).filter(
                ExpenseCache.expense_id == data['expense_id']
            ).first()
            if cached:
                db.delete(cached)
                db.commit()
                print(f"Removed cached expense {data['expense_id']}")
        
        db.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"❌ Error processing event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer():
    """Start RabbitMQ consumer in a separate thread"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER', 'guest'),
            os.getenv('RABBITMQ_PASSWORD', 'guest')
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', '5672')),
                credentials=credentials
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='expense_events', durable=True)
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue='expense_events',
            on_message_callback=process_expense_event
        )
        
        print("Analytics Service consumer started, waiting for messages...")
        channel.start_consuming()
        
    except Exception as e:
        print(f"Consumer error: {e}")


def init_consumer():
    """Initialize consumer in a background thread"""
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
