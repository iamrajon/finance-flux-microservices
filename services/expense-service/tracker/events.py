import pika
import json
import os


def publish_event(event_type: str, data: dict):
    """Publish event to RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER', 'guest'),
            os.getenv('RABBITMQ_PASSWORD', 'guest')
        )
        host = os.getenv('RABBITMQ_HOST', 'localhost')
        port = int(os.getenv('RABBITMQ_PORT', '5672'))
        
        print(f"🔌 Connecting to RabbitMQ at {host}:{port}...")
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials
            )
        )
        channel = connection.channel()
        channel.confirm_delivery() # Enable publisher confirmations
        
        channel.queue_declare(queue='expense_events', durable=True)
        
        message = {
            'event_type': event_type,
            'data': data
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='expense_events',
            body=json.dumps(message, default=str),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        
        connection.close()
        print(f"✅ Published event to 'expense_events' queue: {event_type}")
    except Exception as e:
        import traceback
        print(f"⚠️ Failed to publish event: {e}")
        traceback.print_exc()