import pika
import json
from typing import Any, Callable
from ..models.settings import AppSettings

class RabbitMQService:
    def __init__(self, url=None):
        """Initialize RabbitMQ connection"""
        settings = AppSettings.get_settings()
        self.url = url or settings.rabbitmq_url
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            parameters = pika.URLParameters(self.url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def declare_queue(self, queue_name: str):
        """Declare a queue"""
        self.connect()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Any):
        """Publish message to queue"""
        self.connect()
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )

    def consume(self, queue_name: str, callback: Callable):
        """Consume messages from queue"""
        self.connect()
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=lambda ch, method, properties, body: callback(json.loads(body)),
            auto_ack=True
        )
        self.channel.start_consuming()

    def __enter__(self):
        """Context manager enter"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
