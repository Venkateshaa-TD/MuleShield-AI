"""
MuleShield AI - Message Broker
Kafka-style message broker with topics, producers, and consumers
Implements event-driven architecture for real-time transaction streaming
"""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MessageBroker")


class MessageStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


@dataclass
class Message:
    """
    Kafka-style message with metadata
    Similar to Kafka ProducerRecord
    """
    topic: str
    key: Optional[str]
    value: Any
    partition: int = 0
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    headers: Dict[str, str] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    
    def to_dict(self) -> Dict:
        """Serialize message to dictionary"""
        return {
            "message_id": self.message_id,
            "topic": self.topic,
            "key": self.key,
            "value": self.value,
            "partition": self.partition,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "headers": self.headers,
            "status": self.status.value
        }
    
    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class TopicConfig:
    """Topic configuration similar to Kafka TopicConfig"""
    name: str
    partitions: int = 1
    retention_ms: int = 86400000  # 24 hours
    max_message_size: int = 1048576  # 1MB


class Topic:
    """
    Kafka-style topic with partitions and message retention
    """
    def __init__(self, config: TopicConfig):
        self.config = config
        self.name = config.name
        self.partitions: Dict[int, List[Message]] = {
            i: [] for i in range(config.partitions)
        }
        self.offsets: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
        
    async def publish(self, message: Message) -> int:
        """
        Publish message to topic
        Returns: offset position
        """
        async with self._lock:
            partition = message.partition % self.config.partitions
            offset = len(self.partitions[partition])
            self.partitions[partition].append(message)
            
            # Notify all subscribers
            for queue in self.subscribers:
                await queue.put(message)
            
            return offset
    
    async def consume(self, consumer_group: str, partition: int = 0) -> Optional[Message]:
        """Consume next message from partition"""
        async with self._lock:
            offset = self.offsets[consumer_group][partition]
            messages = self.partitions[partition]
            
            if offset < len(messages):
                message = messages[offset]
                self.offsets[consumer_group][partition] = offset + 1
                return message
            return None
    
    def get_latest_offset(self, partition: int = 0) -> int:
        """Get latest offset for partition"""
        return len(self.partitions.get(partition, []))
    
    def subscribe(self) -> asyncio.Queue:
        """Subscribe to real-time messages"""
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from topic"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)


class Producer:
    """
    Kafka-style producer for publishing messages
    """
    def __init__(self, broker: 'MessageBroker', client_id: str = None):
        self.broker = broker
        self.client_id = client_id or f"producer-{uuid.uuid4().hex[:8]}"
        self.messages_sent = 0
        self.bytes_sent = 0
        
    async def send(
        self, 
        topic: str, 
        value: Any, 
        key: Optional[str] = None,
        partition: int = 0,
        headers: Dict[str, str] = None
    ) -> Message:
        """
        Send message to topic
        Similar to Kafka Producer.send()
        """
        message = Message(
            topic=topic,
            key=key,
            value=value,
            partition=partition,
            headers=headers or {"producer_id": self.client_id}
        )
        
        await self.broker.publish(message)
        self.messages_sent += 1
        self.bytes_sent += len(message.to_json())
        
        logger.debug(f"Producer {self.client_id} sent message to {topic}")
        return message
    
    async def send_batch(self, topic: str, messages: List[Dict]) -> List[Message]:
        """Send batch of messages"""
        sent = []
        for msg_data in messages:
            msg = await self.send(
                topic=topic,
                value=msg_data.get("value"),
                key=msg_data.get("key"),
                partition=msg_data.get("partition", 0)
            )
            sent.append(msg)
        return sent
    
    def get_metrics(self) -> Dict:
        """Get producer metrics"""
        return {
            "client_id": self.client_id,
            "messages_sent": self.messages_sent,
            "bytes_sent": self.bytes_sent
        }


class Consumer:
    """
    Kafka-style consumer for subscribing to topics
    """
    def __init__(
        self, 
        broker: 'MessageBroker',
        group_id: str,
        topics: List[str] = None,
        auto_offset_reset: str = "latest"
    ):
        self.broker = broker
        self.group_id = group_id
        self.client_id = f"consumer-{uuid.uuid4().hex[:8]}"
        self.topics = topics or []
        self.auto_offset_reset = auto_offset_reset
        self.subscriptions: Dict[str, asyncio.Queue] = {}
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.messages_received = 0
        self.running = False
        self._poll_task: Optional[asyncio.Task] = None
        
    async def subscribe(self, topics: List[str]):
        """Subscribe to topics"""
        for topic_name in topics:
            if topic_name not in self.topics:
                self.topics.append(topic_name)
                topic = self.broker.get_topic(topic_name)
                if topic:
                    self.subscriptions[topic_name] = topic.subscribe()
                    
    async def unsubscribe(self, topics: List[str] = None):
        """Unsubscribe from topics"""
        topics = topics or list(self.subscriptions.keys())
        for topic_name in topics:
            if topic_name in self.subscriptions:
                topic = self.broker.get_topic(topic_name)
                if topic:
                    topic.unsubscribe(self.subscriptions[topic_name])
                del self.subscriptions[topic_name]
                if topic_name in self.topics:
                    self.topics.remove(topic_name)
    
    def on_message(self, topic: str, callback: Callable):
        """Register callback for topic messages"""
        self.callbacks[topic].append(callback)
    
    async def poll(self, timeout_ms: int = 1000) -> List[Message]:
        """
        Poll for new messages
        Similar to Kafka Consumer.poll()
        """
        messages = []
        timeout = timeout_ms / 1000
        
        for topic_name, queue in self.subscriptions.items():
            try:
                while True:
                    try:
                        message = queue.get_nowait()
                        messages.append(message)
                        self.messages_received += 1
                        
                        # Execute callbacks
                        for callback in self.callbacks.get(topic_name, []):
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(message)
                                else:
                                    callback(message)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                                
                    except asyncio.QueueEmpty:
                        break
            except Exception as e:
                logger.error(f"Poll error for {topic_name}: {e}")
        
        if not messages:
            await asyncio.sleep(timeout)
            
        return messages
    
    async def start(self):
        """Start continuous polling"""
        self.running = True
        while self.running:
            await self.poll()
            await asyncio.sleep(0.1)
    
    async def stop(self):
        """Stop consumer"""
        self.running = False
        await self.unsubscribe()
        
    def get_metrics(self) -> Dict:
        """Get consumer metrics"""
        return {
            "client_id": self.client_id,
            "group_id": self.group_id,
            "topics": self.topics,
            "messages_received": self.messages_received
        }


class MessageBroker:
    """
    Central message broker - Kafka-style
    Manages topics, producers, and consumers
    """
    
    # Singleton instance
    _instance: Optional['MessageBroker'] = None
    
    # Standard topics for banking
    TOPICS = {
        "transactions": TopicConfig("transactions", partitions=4),
        "transactions.raw": TopicConfig("transactions.raw", partitions=2),
        "transactions.enriched": TopicConfig("transactions.enriched", partitions=2),
        "alerts": TopicConfig("alerts", partitions=2),
        "alerts.high-priority": TopicConfig("alerts.high-priority", partitions=1),
        "accounts": TopicConfig("accounts", partitions=2),
        "risk-scores": TopicConfig("risk-scores", partitions=2),
        "aml-detections": TopicConfig("aml-detections", partitions=1),
        "audit-log": TopicConfig("audit-log", partitions=1),
    }
    
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
        self.producers: Dict[str, Producer] = {}
        self.consumers: Dict[str, Consumer] = {}
        self._running = False
        self._stats = {
            "messages_total": 0,
            "bytes_total": 0,
            "started_at": None
        }
        
        # Initialize standard topics
        for name, config in self.TOPICS.items():
            self.create_topic(config)
    
    @classmethod
    def get_instance(cls) -> 'MessageBroker':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = MessageBroker()
        return cls._instance
    
    def create_topic(self, config: TopicConfig) -> Topic:
        """Create a new topic"""
        if config.name not in self.topics:
            self.topics[config.name] = Topic(config)
            logger.info(f"Created topic: {config.name} ({config.partitions} partitions)")
        return self.topics[config.name]
    
    def delete_topic(self, name: str):
        """Delete a topic"""
        if name in self.topics:
            del self.topics[name]
            logger.info(f"Deleted topic: {name}")
    
    def get_topic(self, name: str) -> Optional[Topic]:
        """Get topic by name"""
        return self.topics.get(name)
    
    def list_topics(self) -> List[str]:
        """List all topic names"""
        return list(self.topics.keys())
    
    def create_producer(self, client_id: str = None) -> Producer:
        """Create a new producer"""
        producer = Producer(self, client_id)
        self.producers[producer.client_id] = producer
        return producer
    
    def create_consumer(
        self, 
        group_id: str, 
        topics: List[str] = None
    ) -> Consumer:
        """Create a new consumer"""
        consumer = Consumer(self, group_id, topics)
        self.consumers[consumer.client_id] = consumer
        return consumer
    
    async def publish(self, message: Message):
        """Publish message to topic"""
        topic = self.get_topic(message.topic)
        if topic:
            await topic.publish(message)
            self._stats["messages_total"] += 1
            self._stats["bytes_total"] += len(message.to_json())
        else:
            raise ValueError(f"Topic not found: {message.topic}")
    
    async def start(self):
        """Start the message broker"""
        self._running = True
        self._stats["started_at"] = datetime.now().isoformat()
        logger.info("Message broker started")
    
    async def stop(self):
        """Stop the message broker"""
        self._running = False
        
        # Stop all consumers
        for consumer in self.consumers.values():
            await consumer.stop()
            
        logger.info("Message broker stopped")
    
    def get_stats(self) -> Dict:
        """Get broker statistics"""
        return {
            **self._stats,
            "topics": len(self.topics),
            "producers": len(self.producers),
            "consumers": len(self.consumers),
            "topic_details": {
                name: {
                    "partitions": topic.config.partitions,
                    "messages": sum(len(p) for p in topic.partitions.values())
                }
                for name, topic in self.topics.items()
            }
        }


# Global broker instance
def get_broker() -> MessageBroker:
    """Get the global message broker instance"""
    return MessageBroker.get_instance()
