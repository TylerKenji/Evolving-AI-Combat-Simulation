"""
Event System for Agent Interactions
Task 1.2.6: Design event system for agent interactions

This module provides a comprehensive event-driven architecture for agent
interactions, combat events, environmental changes, and communication between
agents and the simulation environment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Union
from datetime import datetime
import uuid
import threading
from queue import Queue, PriorityQueue

from src.utils.vector2d import Vector2D


class EventType(Enum):
    """Types of events in the simulation."""
    
    # Combat Events
    AGENT_ATTACKED = "agent_attacked"
    AGENT_DAMAGED = "agent_damaged"
    AGENT_KILLED = "agent_killed"
    AGENT_HEALED = "agent_healed"
    WEAPON_FIRED = "weapon_fired"
    
    # Movement Events
    AGENT_MOVED = "agent_moved"
    AGENT_COLLIDED = "agent_collided"
    AGENT_STUCK = "agent_stuck"
    POSITION_REACHED = "position_reached"
    
    # Perception Events
    ENEMY_SPOTTED = "enemy_spotted"
    ENEMY_LOST = "enemy_lost"
    ALLY_SPOTTED = "ally_spotted"
    THREAT_DETECTED = "threat_detected"
    
    # Communication Events
    HELP_REQUESTED = "help_requested"
    STRATEGY_SHARED = "strategy_shared"
    WARNING_ISSUED = "warning_issued"
    COORDINATION_REQUEST = "coordination_request"
    
    # Environment Events
    TERRAIN_CHANGED = "terrain_changed"
    OBSTACLE_ADDED = "obstacle_added"
    ITEM_SPAWNED = "item_spawned"
    BOUNDARY_HIT = "boundary_hit"
    
    # Simulation Events
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_ENDED = "simulation_ended"
    ROUND_STARTED = "round_started"
    ROUND_ENDED = "round_ended"
    
    # System Events
    ERROR_OCCURRED = "error_occurred"
    DEBUG_INFO = "debug_info"
    PERFORMANCE_METRIC = "performance_metric"


class EventPriority(Enum):
    """Priority levels for event processing."""
    CRITICAL = 0    # Immediate processing required
    HIGH = 1        # Process as soon as possible
    NORMAL = 2      # Standard priority
    LOW = 3         # Process when system has capacity
    BACKGROUND = 4  # Process during idle time


@dataclass
class Event:
    """Base event class for all simulation events."""
    
    # Core event properties
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.DEBUG_INFO
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    
    # Event source and targets
    source_id: Optional[str] = None  # Who/what generated this event
    target_ids: List[str] = field(default_factory=list)  # Who should receive it
    
    # Event data
    data: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Vector2D] = None  # Spatial context if relevant
    
    # Event lifecycle
    processed: bool = False
    processing_time: Optional[datetime] = None
    
    def __lt__(self, other: 'Event') -> bool:
        """Enable priority queue sorting by priority and timestamp."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp
    
    def mark_processed(self) -> None:
        """Mark event as processed."""
        self.processed = True
        self.processing_time = datetime.now()
    
    def get_processing_delay(self) -> float:
        """Get delay between event creation and processing in seconds."""
        if self.processing_time is None:
            return 0.0
        return (self.processing_time - self.timestamp).total_seconds()
    
    def is_targeted_at(self, agent_id: str) -> bool:
        """Check if event is targeted at specific agent."""
        return not self.target_ids or agent_id in self.target_ids
    
    def add_target(self, agent_id: str) -> None:
        """Add target for this event."""
        if agent_id not in self.target_ids:
            self.target_ids.append(agent_id)
    
    def remove_target(self, agent_id: str) -> None:
        """Remove target from this event."""
        if agent_id in self.target_ids:
            self.target_ids.remove(agent_id)


# Specialized Event Classes

@dataclass
class CombatEvent(Event):
    """Event for combat-related interactions."""
    
    def __post_init__(self):
        """Set default event type for combat events."""
        if self.event_type == EventType.DEBUG_INFO:  # Default wasn't changed
            self.event_type = EventType.AGENT_ATTACKED
    
    @property
    def attacker_id(self) -> Optional[str]:
        """Get attacker ID from event data."""
        return self.data.get('attacker_id')
    
    @property
    def victim_id(self) -> Optional[str]:
        """Get victim ID from event data."""
        return self.data.get('victim_id')
    
    @property
    def damage_amount(self) -> float:
        """Get damage amount from event data."""
        return self.data.get('damage_amount', 0.0)
    
    @property
    def weapon_type(self) -> Optional[str]:
        """Get weapon type from event data."""
        return self.data.get('weapon_type')


@dataclass
class MovementEvent(Event):
    """Event for movement-related activities."""
    
    def __post_init__(self):
        """Set default event type for movement events."""
        if self.event_type == EventType.DEBUG_INFO:
            self.event_type = EventType.AGENT_MOVED
    
    @property
    def old_position(self) -> Optional[Vector2D]:
        """Get previous position from event data."""
        pos_data = self.data.get('old_position')
        if pos_data and isinstance(pos_data, dict):
            return Vector2D(pos_data['x'], pos_data['y'])
        return None
    
    @property
    def new_position(self) -> Optional[Vector2D]:
        """Get new position (same as position field)."""
        return self.position
    
    @property
    def distance_moved(self) -> float:
        """Calculate distance moved."""
        old_pos = self.old_position
        if old_pos and self.position:
            return old_pos.distance_to(self.position)
        return 0.0


@dataclass
class CommunicationEvent(Event):
    """Event for agent-to-agent communication."""
    
    def __post_init__(self):
        """Set default event type for communication events."""
        if self.event_type == EventType.DEBUG_INFO:
            self.event_type = EventType.STRATEGY_SHARED
    
    @property
    def message(self) -> str:
        """Get message content from event data."""
        return self.data.get('message', '')
    
    @property
    def communication_type(self) -> str:
        """Get type of communication from event data."""
        return self.data.get('communication_type', 'general')
    
    @property
    def sender_id(self) -> Optional[str]:
        """Get sender ID (same as source_id)."""
        return self.source_id
    
    @property
    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return len(self.target_ids) == 0 or self.data.get('broadcast', False)


# Event Handler System

class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """Check if this handler can process the given event."""
        pass
    
    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        """Process the event. Return True if successfully handled."""
        pass
    
    def get_priority(self) -> int:
        """Get handler priority (lower numbers = higher priority)."""
        return 100  # Default priority


class EventFilter:
    """Filters events based on various criteria."""
    
    def __init__(self):
        self.event_types: Set[EventType] = set()
        self.source_ids: Set[str] = set()
        self.target_ids: Set[str] = set()
        self.min_priority: Optional[EventPriority] = None
        self.max_age_seconds: Optional[float] = None
    
    def add_event_type(self, event_type: EventType) -> None:
        """Add event type to filter."""
        self.event_types.add(event_type)
    
    def add_source_id(self, source_id: str) -> None:
        """Add source ID to filter."""
        self.source_ids.add(source_id)
    
    def add_target_id(self, target_id: str) -> None:
        """Add target ID to filter."""
        self.target_ids.add(target_id)
    
    def set_min_priority(self, priority: EventPriority) -> None:
        """Set minimum priority level."""
        self.min_priority = priority
    
    def set_max_age(self, seconds: float) -> None:
        """Set maximum event age in seconds."""
        self.max_age_seconds = seconds
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check source ID
        if self.source_ids and event.source_id not in self.source_ids:
            return False
        
        # Check target ID
        if self.target_ids:
            if not any(target in self.target_ids for target in event.target_ids):
                return False
        
        # Check priority
        if (self.min_priority is not None and 
            event.priority.value > self.min_priority.value):
            return False
        
        # Check age
        if self.max_age_seconds is not None:
            age = (datetime.now() - event.timestamp).total_seconds()
            if age > self.max_age_seconds:
                return False
        
        return True


class EventBus:
    """Central event distribution system."""
    
    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self.event_queue = PriorityQueue(maxsize=max_queue_size)
        self.handlers: List[EventHandler] = []
        self.filters: List[EventFilter] = []
        
        # Event statistics
        self.events_published = 0
        self.events_processed = 0
        self.events_dropped = 0
        self.processing_times: List[float] = []
        
        # Threading
        self.processing_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()
    
    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        with self.lock:
            self.handlers.append(handler)
            # Sort handlers by priority
            self.handlers.sort(key=lambda h: h.get_priority())
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler."""
        with self.lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
    
    def add_filter(self, event_filter: EventFilter) -> None:
        """Add an event filter."""
        with self.lock:
            self.filters.append(event_filter)
    
    def remove_filter(self, event_filter: EventFilter) -> None:
        """Remove an event filter."""
        with self.lock:
            if event_filter in self.filters:
                self.filters.remove(event_filter)
    
    def publish_event(self, event: Event) -> bool:
        """Publish an event to the bus."""
        try:
            # Apply filters
            for event_filter in self.filters:
                if not event_filter.matches(event):
                    self.events_dropped += 1
                    return False
            
            # Add to queue
            self.event_queue.put_nowait(event)
            self.events_published += 1
            return True
            
        except Exception:
            self.events_dropped += 1
            return False
    
    def create_and_publish(self, event_type: EventType, source_id: Optional[str] = None,
                          target_ids: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None,
                          position: Optional[Vector2D] = None, priority: EventPriority = EventPriority.NORMAL) -> str:
        """Create and publish an event in one call."""
        event = Event(
            event_type=event_type,
            source_id=source_id,
            target_ids=target_ids or [],
            data=data or {},
            position=position,
            priority=priority
        )
        
        if self.publish_event(event):
            return event.event_id
        return ""
    
    def process_events(self, max_events: int = 100) -> int:
        """Process events from the queue."""
        processed_count = 0
        
        while processed_count < max_events and not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                start_time = datetime.now()
                
                # Find handlers for this event
                handled = False
                for handler in self.handlers:
                    if handler.can_handle(event):
                        try:
                            if handler.handle_event(event):
                                handled = True
                                break
                        except Exception as e:
                            # Log handler error but continue processing
                            print(f"Handler error: {e}")
                
                # Mark event as processed
                event.mark_processed()
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                self.processing_times.append(processing_time)
                
                self.events_processed += 1
                processed_count += 1
                
                # Limit processing time history
                if len(self.processing_times) > 1000:
                    self.processing_times = self.processing_times[-500:]
                
            except Exception:
                break
        
        return processed_count
    
    def start_processing(self) -> None:
        """Start background event processing."""
        if self.running:
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self) -> None:
        """Stop background event processing."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
    
    def _processing_loop(self) -> None:
        """Background processing loop."""
        import time
        while self.running:
            self.process_events(50)
            time.sleep(0.001)  # 1ms sleep to prevent busy waiting
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.event_queue.qsize()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event processing statistics."""
        avg_processing_time = 0.0
        if self.processing_times:
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        return {
            'events_published': self.events_published,
            'events_processed': self.events_processed,
            'events_dropped': self.events_dropped,
            'queue_size': self.get_queue_size(),
            'average_processing_time_ms': avg_processing_time,
            'handlers_registered': len(self.handlers),
            'filters_active': len(self.filters)
        }
    
    def clear_queue(self) -> int:
        """Clear all events from queue. Returns number of events cleared."""
        cleared = 0
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
                cleared += 1
            except:
                break
        return cleared


# Convenience Functions

def create_combat_event(attacker_id: str, victim_id: str, damage: float,
                       weapon_type: str = "unknown", position: Optional[Vector2D] = None) -> CombatEvent:
    """Create a combat event."""
    return CombatEvent(
        event_type=EventType.AGENT_ATTACKED,
        source_id=attacker_id,
        target_ids=[victim_id],
        data={
            'attacker_id': attacker_id,
            'victim_id': victim_id,
            'damage_amount': damage,
            'weapon_type': weapon_type
        },
        position=position,
        priority=EventPriority.HIGH
    )


def create_movement_event(agent_id: str, old_pos: Vector2D, new_pos: Vector2D) -> MovementEvent:
    """Create a movement event."""
    return MovementEvent(
        event_type=EventType.AGENT_MOVED,
        source_id=agent_id,
        data={
            'old_position': {'x': old_pos.x, 'y': old_pos.y}
        },
        position=new_pos,
        priority=EventPriority.LOW
    )


def create_communication_event(sender_id: str, message: str, targets: Optional[List[str]] = None,
                              communication_type: str = "general") -> CommunicationEvent:
    """Create a communication event."""
    return CommunicationEvent(
        event_type=EventType.STRATEGY_SHARED,
        source_id=sender_id,
        target_ids=targets or [],
        data={
            'message': message,
            'communication_type': communication_type,
            'broadcast': not targets
        },
        priority=EventPriority.NORMAL
    )


# Global Event Bus Instance
global_event_bus = EventBus()
