import pika
import json
import os
from django.conf import settings


def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        os.getenv('RABBITMQ_USER', 'guest'),
        os.getenv('RABBITMQ_PASSWORD', 'guest')
    )

    parameters = pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST', 'localhost'),
        port=int(os.getenv('RABBITMQ_PORT', '5672')),
        virtual_host=os.getenv('RABBITMQ_VHOST', '/'),
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )

    connection = pika.BlockingConnection(
        parameters
    )
    return connection


def publish_event(event_type:str, user_data: dict):
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        # Declare queue (safe to call multiple times)
        channel.queue_declare(queue='user_events', durable=True)

        message = {
            'event_type': event_type,
            'data': user_data
        }

        channel.basic_publish(
            exchange='',
            routing_key='user_events',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        connection.close()
        print(f"Event published: {event_type}")
    except Exception as e:
        print(f"Failed to publish event: {e}")
