"""
Stage 9: Apache Kafka Event-Driven Engine (Producers, Idempotent Consumers, Retries & Dead-Letter Topic).

Supports:
- 10 Domain Kafka Topics + Dead-Letter Topic (`recovery.dlq`):
  * booking.created
  * booking.updated
  * disruption.detected
  * journey.affected
  * recovery.requested
  * recovery.planned
  * action.requested
  * action.completed
  * action.failed
  * notification.requested
  * recovery.dlq
- Partitioned topic log with deterministic correlation_id partitioning & monotonic offsets
- Correlation IDs, Causation IDs, Event IDs, and UTC Timestamps
- Idempotent Consumers (deduplicating by event_id & idempotency_key per consumer group)
- Configurable Retry Handling with exponential backoff simulation
- Automatic Dead-Letter Topic (`recovery.dlq`) routing when max retries are exhausted
- Real-time WebSocket broadcasting via `ws_manager`
"""
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Set
from app.schemas.event_schemas import (
    KafkaTopic,
    ALL_KAFKA_TOPICS,
    KafkaEventEnvelope,
    DeadLetterEventRecord,
)
from app.modules.events.ws_manager import ws_manager
from app.core.config import settings
from app.core.logger import logger


class KafkaConsumerGroup:
    """
    Represents an idempotent Kafka Consumer Group with retry handling and Dead-Letter Queue support.
    """

    def __init__(
        self,
        group_id: str,
        agent_name: str,
        subscribed_topics: List[str],
        handler: Callable[[KafkaEventEnvelope], None],
        default_max_retries: int = 3,
    ):
        self.group_id = group_id
        self.agent_name = agent_name
        self.subscribed_topics = subscribed_topics
        self.handler = handler
        self.default_max_retries = default_max_retries

        # Idempotency state per consumer group
        self.processed_event_ids: Set[str] = set()
        self.processed_idempotency_keys: Dict[str, Dict[str, Any]] = {}
        self.committed_offsets: Dict[str, int] = {}

        # Consumer telemetry metrics
        self.events_received: int = 0
        self.events_processed: int = 0
        self.idempotent_skips: int = 0
        self.retry_attempts: int = 0
        self.dlq_routed: int = 0
        self.processing_log: List[Dict[str, Any]] = []

    def is_duplicate(self, event: KafkaEventEnvelope) -> bool:
        return (
            event.event_id in self.processed_event_ids
            or event.idempotency_key in self.processed_idempotency_keys
        )

    def mark_processed(self, event: KafkaEventEnvelope):
        self.processed_event_ids.add(event.event_id)
        self.processed_idempotency_keys[event.idempotency_key] = {
            "event_id": event.event_id,
            "topic": event.topic,
            "correlation_id": event.correlation_id,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        partition_key = f"{event.topic}:{event.partition}"
        self.committed_offsets[partition_key] = event.offset

    def reset(self):
        self.processed_event_ids.clear()
        self.processed_idempotency_keys.clear()
        self.committed_offsets.clear()
        self.events_received = 0
        self.events_processed = 0
        self.idempotent_skips = 0
        self.retry_attempts = 0
        self.dlq_routed = 0
        self.processing_log.clear()

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "agent_name": self.agent_name,
            "subscribed_topics": self.subscribed_topics,
            "events_received": self.events_received,
            "events_processed": self.events_processed,
            "idempotent_skips": self.idempotent_skips,
            "retry_attempts": self.retry_attempts,
            "dlq_routed": self.dlq_routed,
            "committed_offsets": self.committed_offsets,
            "recent_logs": self.processing_log[-10:],
        }


class KafkaEventBroker:
    """
    Production-style Kafka Event Broker & Producer/Consumer Coordinator.
    Provides partitioned topics, consumer group subscriptions, idempotent message processing,
    configurable retry policies, and Dead-Letter Queue (`recovery.dlq`) routing.
    """

    NUM_PARTITIONS = 3

    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS or "localhost:9092"
        self.topics: Dict[str, List[Dict[str, Any]]] = {topic: [] for topic in ALL_KAFKA_TOPICS}
        self.partition_offsets: Dict[str, Dict[int, int]] = {
            topic: {p: 0 for p in range(self.NUM_PARTITIONS)} for topic in ALL_KAFKA_TOPICS
        }
        self.consumer_groups: Dict[str, KafkaConsumerGroup] = {}
        self.dlq_records: List[DeadLetterEventRecord] = []
        self.all_events_chronological: List[Dict[str, Any]] = []
        self.idempotent_skip_records: List[Dict[str, Any]] = []

    def ensure_topic(self, topic: str):
        if topic not in self.topics:
            self.topics[topic] = []
            self.partition_offsets[topic] = {p: 0 for p in range(self.NUM_PARTITIONS)}

    def register_consumer_group(self, consumer_group: KafkaConsumerGroup):
        for topic in consumer_group.subscribed_topics:
            self.ensure_topic(topic)
        self.consumer_groups[consumer_group.group_id] = consumer_group
        logger.info(
            f"Registered Kafka Consumer Group '{consumer_group.group_id}' ({consumer_group.agent_name}) "
            f"for topics: {consumer_group.subscribed_topics}"
        )

    @staticmethod
    def compute_idempotency_key(
        correlation_id: str,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        explicit_key: Optional[str] = None,
    ) -> str:
        if explicit_key:
            return explicit_key
        discriminator = {
            "correlation_id": correlation_id,
            "topic": topic,
            "event_type": event_type,
            "booking_ref": payload.get("booking_ref") or payload.get("booking_id"),
            "action_type": payload.get("action_type"),
            "step_tag": payload.get("step_tag"),
        }
        digest = hashlib.sha256(json.dumps(discriminator, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
        return f"KAFKA-IDEM-{digest.upper()}"

    def _select_partition(self, correlation_id: str) -> int:
        digest = int(hashlib.md5(correlation_id.encode("utf-8")).hexdigest(), 16)
        return digest % self.NUM_PARTITIONS

    def publish_event(
        self,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        producer: str = "system-producer",
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        ui_message: str = "",
        max_retries: int = 3,
        step_delay_ms: int = 0,
    ) -> KafkaEventEnvelope:
        """
        Publishes a structured KafkaEventEnvelope to the target topic, broadcasts it over WebSocket,
        and dispatches it to all subscribed consumer groups with idempotency and retry handling.
        """
        self.ensure_topic(topic)

        corr_id = correlation_id or f"corr-{uuid.uuid4().hex[:10]}"
        evt_id = event_id or f"evt-{uuid.uuid4().hex[:12]}"
        idem_key = self.compute_idempotency_key(
            correlation_id=corr_id,
            topic=topic,
            event_type=event_type,
            payload=payload,
            explicit_key=idempotency_key,
        )

        partition = self._select_partition(corr_id)
        offset = self.partition_offsets[topic][partition]
        self.partition_offsets[topic][partition] += 1

        envelope = KafkaEventEnvelope(
            event_id=evt_id,
            correlation_id=corr_id,
            causation_id=causation_id,
            topic=topic,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            producer=producer,
            idempotency_key=idem_key,
            partition=partition,
            offset=offset,
            retry_count=0,
            max_retries=max_retries,
            ui_message=ui_message,
            payload=payload,
        )

        event_dict = envelope.model_dump()
        self.topics[topic].append(event_dict)
        self.all_events_chronological.append(event_dict)

        # Broadcast live event over WebSocket
        ws_manager.broadcast_event(event_dict)

        if step_delay_ms and step_delay_ms > 0:
            time.sleep(min(step_delay_ms, 1000) / 1000.0)

        # Deliver to subscribed consumer groups
        self._dispatch_to_consumers(envelope, step_delay_ms=step_delay_ms)

        return envelope

    def _dispatch_to_consumers(self, envelope: KafkaEventEnvelope, step_delay_ms: int = 0):
        for group_id, consumer in list(self.consumer_groups.items()):
            if envelope.topic not in consumer.subscribed_topics:
                continue

            consumer.events_received += 1

            # 1. Idempotent Consumer Deduplication Check
            if consumer.is_duplicate(envelope):
                consumer.idempotent_skips += 1
                skip_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "consumer_group": group_id,
                    "agent_name": consumer.agent_name,
                    "event_id": envelope.event_id,
                    "idempotency_key": envelope.idempotency_key,
                    "topic": envelope.topic,
                    "correlation_id": envelope.correlation_id,
                    "status": "IDEMPOTENT_DUPLICATE_SKIPPED",
                    "reason": f"Consumer group '{group_id}' already processed key '{envelope.idempotency_key}'",
                }
                consumer.processing_log.append(skip_entry)
                self.idempotent_skip_records.append(skip_entry)
                ws_manager.broadcast_event({
                    "event_id": envelope.event_id,
                    "correlation_id": envelope.correlation_id,
                    "causation_id": envelope.causation_id,
                    "topic": envelope.topic,
                    "event_type": "IDEMPOTENT_CONSUMER_SKIP",
                    "producer": consumer.agent_name,
                    "timestamp": skip_entry["timestamp"],
                    "partition": envelope.partition,
                    "offset": envelope.offset,
                    "retry_count": 0,
                    "ui_message": f"Idempotent consumer ({consumer.agent_name}) skipped duplicate event {envelope.event_id}",
                    "payload": skip_entry,
                })
                continue

            # 2. Execute Consumer Handler with Retry Policy
            max_retries = envelope.max_retries if envelope.max_retries is not None else consumer.default_max_retries
            retry_history: List[Dict[str, Any]] = []
            succeeded = False

            for attempt in range(1, max_retries + 2):
                try:
                    envelope.retry_count = attempt - 1
                    # Update stored dict retry_count as well
                    if self.topics[envelope.topic]:
                        self.topics[envelope.topic][-1]["retry_count"] = envelope.retry_count

                    consumer.handler(envelope)
                    succeeded = True
                    consumer.mark_processed(envelope)
                    consumer.events_processed += 1
                    consumer.processing_log.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "consumer_group": group_id,
                        "event_id": envelope.event_id,
                        "topic": envelope.topic,
                        "correlation_id": envelope.correlation_id,
                        "status": "PROCESSED" if attempt == 1 else f"PROCESSED_AFTER_RETRY_{attempt - 1}",
                        "attempts": attempt,
                    })
                    break
                except Exception as exc:
                    error_msg = str(exc)
                    retry_history.append({
                        "attempt": attempt,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": error_msg,
                    })
                    if attempt <= max_retries:
                        consumer.retry_attempts += 1
                        ws_manager.broadcast_event({
                            "event_id": envelope.event_id,
                            "correlation_id": envelope.correlation_id,
                            "causation_id": envelope.causation_id,
                            "topic": envelope.topic,
                            "event_type": "CONSUMER_RETRY_ATTEMPT",
                            "producer": consumer.agent_name,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "partition": envelope.partition,
                            "offset": envelope.offset,
                            "retry_count": attempt,
                            "ui_message": f"Retry #{attempt}/{max_retries} in {consumer.agent_name}: {error_msg}",
                            "payload": {"attempt": attempt, "max_retries": max_retries, "error": error_msg},
                        })
                        if step_delay_ms and step_delay_ms > 0:
                            time.sleep(0.05)
                    else:
                        # Exhausted all retries -> Route to Dead-Letter Topic (`recovery.dlq`)
                        consumer.dlq_routed += 1
                        self._route_to_dlq(
                            original_event=envelope,
                            failed_consumer=consumer,
                            error_message=error_msg,
                            retry_history=retry_history,
                        )

    def _route_to_dlq(
        self,
        original_event: KafkaEventEnvelope,
        failed_consumer: KafkaConsumerGroup,
        error_message: str,
        retry_history: List[Dict[str, Any]],
    ):
        dlq_id = f"dlq-{uuid.uuid4().hex[:10]}"
        failed_at = datetime.now(timezone.utc).isoformat()
        dlq_record = DeadLetterEventRecord(
            dlq_id=dlq_id,
            original_event=original_event,
            failed_topic=original_event.topic,
            failed_consumer_group=failed_consumer.group_id,
            error_message=error_message,
            retry_attempts=len(retry_history),
            retry_history=retry_history,
            failed_at=failed_at,
            replayed=False,
        )
        self.dlq_records.append(dlq_record)
        failed_consumer.processing_log.append({
            "timestamp": failed_at,
            "consumer_group": failed_consumer.group_id,
            "event_id": original_event.event_id,
            "topic": original_event.topic,
            "correlation_id": original_event.correlation_id,
            "status": "ROUTED_TO_DLQ",
            "dlq_id": dlq_id,
            "error": error_message,
            "attempts": len(retry_history),
        })

        # Publish to `recovery.dlq` topic
        dlq_topic = KafkaTopic.DEAD_LETTER_TOPIC.value
        partition = self._select_partition(original_event.correlation_id)
        offset = self.partition_offsets[dlq_topic][partition]
        self.partition_offsets[dlq_topic][partition] += 1

        dlq_envelope = KafkaEventEnvelope(
            event_id=f"evt-dlq-{uuid.uuid4().hex[:8]}",
            correlation_id=original_event.correlation_id,
            causation_id=original_event.event_id,
            topic=dlq_topic,
            event_type="EVENT_ROUTED_TO_DLQ",
            timestamp=failed_at,
            producer=failed_consumer.agent_name,
            idempotency_key=f"DLQ-{original_event.idempotency_key}",
            partition=partition,
            offset=offset,
            retry_count=original_event.retry_count,
            max_retries=original_event.max_retries,
            ui_message=f"Dead-Letter Topic ({dlq_topic}): {failed_consumer.agent_name} exhausted {original_event.max_retries} retries",
            payload=dlq_record.model_dump(),
        )
        dlq_dict = dlq_envelope.model_dump()
        self.topics[dlq_topic].append(dlq_dict)
        self.all_events_chronological.append(dlq_dict)
        ws_manager.broadcast_event(dlq_dict)

        # If the failure happened during `action.requested`, also emit `action.failed`
        if original_event.topic == KafkaTopic.ACTION_REQUESTED.value:
            self.publish_event(
                topic=KafkaTopic.ACTION_FAILED.value,
                event_type="RECOVERY_ACTION_FAILED",
                producer=failed_consumer.agent_name,
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,
                ui_message="Recovery action failed — routed to Dead-Letter Queue & human escalation",
                payload={
                    "failed_event_id": original_event.event_id,
                    "dlq_id": dlq_id,
                    "error_message": error_message,
                    "retry_attempts": len(retry_history),
                    "journey_id": original_event.payload.get("journey_id"),
                },
            )

    def replay_dlq_event(self, dlq_id: str) -> Dict[str, Any]:
        """
        Replays a Dead-Letter Queue event by clearing any simulated poison-pill flags
        and re-publishing the original event to its target topic.
        """
        target: Optional[DeadLetterEventRecord] = None
        for rec in self.dlq_records:
            if rec.dlq_id == dlq_id or rec.original_event.event_id == dlq_id:
                target = rec
                break

        if not target:
            raise ValueError(f"DLQ event '{dlq_id}' not found.")

        target.replayed = True
        orig = target.original_event
        cleaned_payload = dict(orig.payload)
        # Clear simulated failure flags so replay succeeds
        cleaned_payload["inject_consumer_failure"] = None
        cleaned_payload["replayed_from_dlq"] = target.dlq_id

        replayed_envelope = self.publish_event(
            topic=orig.topic,
            event_type=orig.event_type,
            payload=cleaned_payload,
            producer=f"dlq-replay-service ({orig.producer})",
            correlation_id=orig.correlation_id,
            causation_id=orig.event_id,
            idempotency_key=f"{orig.idempotency_key}-REPLAY-{uuid.uuid4().hex[:6]}",
            ui_message=f"Replaying event {orig.event_id} from Dead-Letter Queue ({target.dlq_id})",
            max_retries=orig.max_retries,
        )
        return {
            "status": "REPLAYED_SUCCESSFULLY",
            "dlq_id": target.dlq_id,
            "replayed_event_id": replayed_envelope.event_id,
            "correlation_id": replayed_envelope.correlation_id,
            "topic": replayed_envelope.topic,
        }

    def get_topics_summary(self) -> List[Dict[str, Any]]:
        summaries = []
        for topic in ALL_KAFKA_TOPICS:
            events = self.topics.get(topic, [])
            subscribed_groups = [
                g.group_id for g in self.consumer_groups.values() if topic in g.subscribed_topics
            ]
            summaries.append({
                "topic": topic,
                "partitions": self.NUM_PARTITIONS,
                "message_count": len(events),
                "partition_offsets": self.partition_offsets.get(topic, {}),
                "subscribed_consumer_groups": subscribed_groups,
                "latest_event": events[-1] if events else None,
            })
        return summaries

    def reset_broker(self):
        for topic in ALL_KAFKA_TOPICS:
            self.topics[topic] = []
            self.partition_offsets[topic] = {p: 0 for p in range(self.NUM_PARTITIONS)}
        for group in self.consumer_groups.values():
            group.reset()
        self.dlq_records.clear()
        self.all_events_chronological.clear()
        self.idempotent_skip_records.clear()
        ws_manager.clear_milestones()


kafka_broker = KafkaEventBroker()
