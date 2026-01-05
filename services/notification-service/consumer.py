import pika
import json
import os
import threading
import asyncio
import time
import logging
from email_utils import (
    send_email,
    get_welcome_email_template,
    get_budget_alert_template,
    get_expense_confirmation_template
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def wait_for_rabbitmq(max_retries=5, initial_delay=2):
    """Wait for RabbitMQ to be available with exponential backoff"""
    for attempt in range(max_retries):
        try:
            credentials = pika.PlainCredentials(
                os.getenv('RABBITMQ_USER', 'guest'),
                os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.getenv('RABBITMQ_HOST', 'localhost'),
                    port=int(os.getenv('RABBITMQ_PORT', '5672')),
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            connection.close()
            logger.info("RabbitMQ connection verified")
            return True
        except Exception as e:
            delay = initial_delay * (2 ** attempt)
            logger.warning(f"RabbitMQ not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Failed to connect to RabbitMQ after all retries")
                return False


def process_user_event(event_type: str, data: dict):
    """Process user events"""
    if event_type == 'user.registered':
        # Send welcome email
        email = data.get('email')
        username = data.get('username', 'User')
        
        logger.info(f"Processing welcome email for user: {username} ({email})")
        
        if email:
            subject = "Welcome to Smart Expense Tracker!"
            body = get_welcome_email_template(username)
            
            try:
                # Run async email sending in event loop
                logger.info(f"Attempting to send welcome email to {email}...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(send_email(email, subject, body, html=True))
                loop.close()
                
                if result:
                    logger.info(f"Welcome email sent successfully to {email}")
                else:
                    logger.warning(f"Failed to send welcome email to {email}")
            except Exception as e:
                logger.error(f"Error sending welcome email to {email}: {e}", exc_info=True)
        else:
            logger.warning(f"No email address provided for user: {username}")


def process_expense_event(event_type: str, data: dict):
    """Process expense events"""
    # In a real application, you would:
    # 1. Fetch user email from User Service
    # 2. Check user notification preferences
    # 3. Send appropriate notifications
    
    print(f"📨 Expense event received: {event_type}")
    # For now, just log the event
    # In production, implement email notifications based on user preferences


def consume_user_events():
    """Consume user events from RabbitMQ"""
    logger.info("Starting user events consumer...")
    
    try:
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER', 'guest'),
            os.getenv('RABBITMQ_PASSWORD', 'guest')
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', '5672')),
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='user_events', durable=True)
        
        logger.info("User events consumer connected to RabbitMQ")
        
        def callback(ch, method, properties, body):
            try:
                logger.info(f"Received user event: {body}")
                message = json.loads(body)
                event_type = message.get('event_type')
                data = message.get('data')
                
                # Handle backward compatibility: data might be double-encoded JSON string
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        logger.error(f"Could not parse data as JSON: {data}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        return
                
                logger.info(f"Processing {event_type} event for user: {data.get('email', 'unknown')}")
                process_user_event(event_type, data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Successfully processed {event_type} event")
                
            except Exception as e:
                logger.error(f"Error processing user event: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='user_events', on_message_callback=callback)
        
        logger.info("User events consumer started - waiting for messages...")
        channel.start_consuming()
        
    except Exception as e:
        logger.error(f"User events consumer error: {e}", exc_info=True)


def consume_expense_events():
    """Consume expense events from RabbitMQ"""
    logger.info("Starting expense events consumer...")
    
    try:
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER', 'guest'),
            os.getenv('RABBITMQ_PASSWORD', 'guest')
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', '5672')),
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='expense_events', durable=True)
        
        logger.info("Expense events consumer connected to RabbitMQ")
        
        def callback(ch, method, properties, body):
            try:
                logger.info(f"Received expense event: {body}")
                message = json.loads(body)
                event_type = message.get('event_type')
                data = message.get('data')
                
                process_expense_event(event_type, data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Successfully processed {event_type} event")
                
            except Exception as e:
                logger.error(f"Error processing expense event: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='expense_events', on_message_callback=callback)
        
        logger.info("Expense events consumer started - waiting for messages...")
        channel.start_consuming()
        
    except Exception as e:
        logger.error(f"Expense events consumer error: {e}", exc_info=True)


def init_consumers():
    """Initialize all consumers in background threads"""
    logger.info("🔧 Initializing notification consumers...")
    
    # Wait for RabbitMQ to be ready
    if not wait_for_rabbitmq():
        logger.error("Cannot start consumers - RabbitMQ is not available")
        return
    
    logger.info("Starting consumer threads...")
    
    user_thread = threading.Thread(target=consume_user_events, daemon=True)
    expense_thread = threading.Thread(target=consume_expense_events, daemon=True)
    
    user_thread.start()
    expense_thread.start()
    
    logger.info("All notification consumers initialized")
    logger.info("Consumers are running in background threads")

