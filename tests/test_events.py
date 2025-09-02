"""
Tests for Event System
Task 1.2.6: Design event system for agent interactions

This module tests the comprehensive event-driven architecture including
event creation, processing, filtering, and agent communication systems.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional

from src.events import (
    EventType, EventPriority, Event, CombatEvent, MovementEvent, CommunicationEvent,
    EventHandler, EventFilter, EventBus, global_event_bus,
    create_combat_event, create_movement_event, create_communication_event
)
from src.utils.vector2d import Vector2D


class TestEventEnums:
    """Test event enumeration types."""
    
    def test_event_type_enum(self):
        """Test EventType enumeration."""
        assert EventType.AGENT_ATTACKED.value == "agent_attacked"
        assert EventType.ENEMY_SPOTTED.value == "enemy_spotted"
        assert EventType.SIMULATION_STARTED.value == "simulation_started"
        # Verify we have events for different categories
        assert len([e for e in EventType if "AGENT" in e.name]) >= 5
        assert len([e for e in EventType if "SIMULATION" in e.name]) >= 3
    
    def test_event_priority_enum(self):
        """Test EventPriority enumeration."""
        assert EventPriority.CRITICAL.value == 0
        assert EventPriority.HIGH.value == 1
        assert EventPriority.NORMAL.value == 2
        assert EventPriority.LOW.value == 3
        assert EventPriority.BACKGROUND.value == 4
        
        # Test priority ordering
        assert EventPriority.CRITICAL.value < EventPriority.NORMAL.value
        assert EventPriority.NORMAL.value < EventPriority.BACKGROUND.value


class TestEvent:
    """Test base Event class."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        position = Vector2D(100, 200)
        data = {"test_key": "test_value"}
        
        event = Event(
            event_type=EventType.AGENT_ATTACKED,
            source_id="agent_123",
            target_ids=["agent_456"],
            data=data,
            position=position,
            priority=EventPriority.HIGH
        )
        
        assert event.event_type == EventType.AGENT_ATTACKED
        assert event.source_id == "agent_123"
        assert event.target_ids == ["agent_456"]
        assert event.data == data
        assert event.position == position
        assert event.priority == EventPriority.HIGH
        assert not event.processed
        assert event.event_id  # Should have auto-generated ID
    
    def test_event_priority_comparison(self):
        """Test event priority comparison for queue sorting."""
        critical_event = Event(priority=EventPriority.CRITICAL)
        normal_event = Event(priority=EventPriority.NORMAL)
        low_event = Event(priority=EventPriority.LOW)
        
        # Critical should be "less than" (higher priority) normal
        assert critical_event < normal_event
        assert normal_event < low_event
        assert not (normal_event < critical_event)
    
    def test_event_targeting(self):
        """Test event targeting functionality."""
        event = Event(target_ids=["agent1", "agent2"])
        
        # Test targeting check
        assert event.is_targeted_at("agent1")
        assert event.is_targeted_at("agent2")
        assert not event.is_targeted_at("agent3")
        
        # Test with no targets (broadcast)
        broadcast_event = Event()
        assert broadcast_event.is_targeted_at("any_agent")
        
        # Test target manipulation
        event.add_target("agent3")
        assert "agent3" in event.target_ids
        assert event.is_targeted_at("agent3")
        
        event.remove_target("agent1")
        assert "agent1" not in event.target_ids
        assert not event.is_targeted_at("agent1")
    
    def test_event_processing(self):
        """Test event processing tracking."""
        event = Event()
        
        assert not event.processed
        assert event.processing_time is None
        
        event.mark_processed()
        
        assert event.processed
        assert event.processing_time is not None
        
        # Test processing delay calculation
        delay = event.get_processing_delay()
        assert delay >= 0.0


class TestSpecializedEvents:
    """Test specialized event classes."""
    
    def test_combat_event(self):
        """Test CombatEvent functionality."""
        position = Vector2D(50, 75)
        combat_event = CombatEvent(
            source_id="attacker_1",
            target_ids=["victim_1"],
            data={
                'attacker_id': 'attacker_1',
                'victim_id': 'victim_1',
                'damage_amount': 25.0,
                'weapon_type': 'sword'
            },
            position=position
        )
        
        # Test property accessors
        assert combat_event.attacker_id == "attacker_1"
        assert combat_event.victim_id == "victim_1"
        assert combat_event.damage_amount == 25.0
        assert combat_event.weapon_type == "sword"
        
        # Test default event type
        assert combat_event.event_type == EventType.AGENT_ATTACKED
    
    def test_movement_event(self):
        """Test MovementEvent functionality."""
        old_pos = Vector2D(10, 20)
        new_pos = Vector2D(30, 40)
        
        movement_event = MovementEvent(
            source_id="agent_1",
            data={'old_position': {'x': old_pos.x, 'y': old_pos.y}},
            position=new_pos
        )
        
        # Test property accessors
        assert movement_event.old_position == old_pos
        assert movement_event.new_position == new_pos
        
        # Test distance calculation
        expected_distance = old_pos.distance_to(new_pos)
        assert abs(movement_event.distance_moved - expected_distance) < 0.1
        
        # Test default event type
        assert movement_event.event_type == EventType.AGENT_MOVED
    
    def test_communication_event(self):
        """Test CommunicationEvent functionality."""
        comm_event = CommunicationEvent(
            source_id="sender_1",
            target_ids=["receiver_1", "receiver_2"],
            data={
                'message': 'Enemy approaching from north',
                'communication_type': 'warning',
                'broadcast': False
            }
        )
        
        # Test property accessors
        assert comm_event.message == "Enemy approaching from north"
        assert comm_event.communication_type == "warning"
        assert comm_event.sender_id == "sender_1"
        assert not comm_event.is_broadcast
        
        # Test broadcast communication
        broadcast_event = CommunicationEvent(
            source_id="commander",
            data={'message': 'All units retreat', 'broadcast': True}
        )
        assert broadcast_event.is_broadcast


class TestEventFilter:
    """Test EventFilter functionality."""
    
    def test_filter_creation(self):
        """Test basic filter creation."""
        event_filter = EventFilter()
        
        # Empty filter should match everything
        event = Event()
        assert event_filter.matches(event)
    
    def test_event_type_filtering(self):
        """Test filtering by event type."""
        event_filter = EventFilter()
        event_filter.add_event_type(EventType.AGENT_ATTACKED)
        event_filter.add_event_type(EventType.AGENT_DAMAGED)
        
        # Should match combat events
        combat_event = Event(event_type=EventType.AGENT_ATTACKED)
        damage_event = Event(event_type=EventType.AGENT_DAMAGED)
        movement_event = Event(event_type=EventType.AGENT_MOVED)
        
        assert event_filter.matches(combat_event)
        assert event_filter.matches(damage_event)
        assert not event_filter.matches(movement_event)
    
    def test_source_filtering(self):
        """Test filtering by source ID."""
        event_filter = EventFilter()
        event_filter.add_source_id("agent_1")
        event_filter.add_source_id("agent_2")
        
        event1 = Event(source_id="agent_1")
        event2 = Event(source_id="agent_2")
        event3 = Event(source_id="agent_3")
        
        assert event_filter.matches(event1)
        assert event_filter.matches(event2)
        assert not event_filter.matches(event3)
    
    def test_priority_filtering(self):
        """Test filtering by priority level."""
        event_filter = EventFilter()
        event_filter.set_min_priority(EventPriority.NORMAL)
        
        critical_event = Event(priority=EventPriority.CRITICAL)
        high_event = Event(priority=EventPriority.HIGH)
        normal_event = Event(priority=EventPriority.NORMAL)
        low_event = Event(priority=EventPriority.LOW)
        
        assert event_filter.matches(critical_event)
        assert event_filter.matches(high_event)
        assert event_filter.matches(normal_event)
        assert not event_filter.matches(low_event)
    
    def test_age_filtering(self):
        """Test filtering by event age."""
        event_filter = EventFilter()
        event_filter.set_max_age(1.0)  # 1 second max age
        
        # Create old event
        old_event = Event()
        old_event.timestamp = datetime.now() - timedelta(seconds=2)
        
        # Create recent event
        recent_event = Event()
        
        assert not event_filter.matches(old_event)
        assert event_filter.matches(recent_event)


class MockEventHandler(EventHandler):
    """Mock event handler for testing."""
    
    def __init__(self, event_types: Optional[List[EventType]] = None, priority: int = 100):
        self.handled_events: List[Event] = []
        self.event_types = event_types or []
        self.handler_priority = priority
        self.should_fail = False
    
    def can_handle(self, event: Event) -> bool:
        """Check if this handler can process the event."""
        return not self.event_types or event.event_type in self.event_types
    
    def handle_event(self, event: Event) -> bool:
        """Process the event."""
        if self.should_fail:
            raise Exception("Handler intentionally failed")
        
        self.handled_events.append(event)
        return True
    
    def get_priority(self) -> int:
        """Get handler priority."""
        return self.handler_priority


class TestEventBus:
    """Test EventBus functionality."""
    
    def test_event_bus_creation(self):
        """Test basic event bus creation."""
        bus = EventBus(max_queue_size=100)
        
        assert bus.get_queue_size() == 0
        assert len(bus.handlers) == 0
        assert not bus.running
    
    def test_handler_registration(self):
        """Test event handler registration."""
        bus = EventBus()
        handler1 = MockEventHandler(priority=50)
        handler2 = MockEventHandler(priority=25)  # Higher priority
        
        bus.register_handler(handler1)
        bus.register_handler(handler2)
        
        assert len(bus.handlers) == 2
        # Should be sorted by priority (lower number = higher priority)
        assert bus.handlers[0] == handler2
        assert bus.handlers[1] == handler1
        
        # Test unregistration
        bus.unregister_handler(handler1)
        assert len(bus.handlers) == 1
        assert bus.handlers[0] == handler2
    
    def test_event_publishing(self):
        """Test event publishing."""
        bus = EventBus()
        
        event = Event(event_type=EventType.AGENT_ATTACKED)
        
        # Should successfully publish
        assert bus.publish_event(event)
        assert bus.get_queue_size() == 1
        assert bus.events_published == 1
    
    def test_event_processing(self):
        """Test event processing."""
        bus = EventBus()
        handler = MockEventHandler([EventType.AGENT_ATTACKED])
        bus.register_handler(handler)
        
        # Publish events
        event1 = Event(event_type=EventType.AGENT_ATTACKED)
        event2 = Event(event_type=EventType.AGENT_MOVED)
        
        bus.publish_event(event1)
        bus.publish_event(event2)
        
        # Process events
        processed = bus.process_events()
        
        assert processed == 2
        assert bus.events_processed == 2
        assert len(handler.handled_events) == 1  # Only handles AGENT_ATTACKED
        assert handler.handled_events[0].event_type == EventType.AGENT_ATTACKED
    
    def test_event_filtering_in_bus(self):
        """Test event filtering in the bus."""
        bus = EventBus()
        event_filter = EventFilter()
        event_filter.add_event_type(EventType.AGENT_ATTACKED)
        bus.add_filter(event_filter)
        
        # Publish filtered and unfiltered events
        combat_event = Event(event_type=EventType.AGENT_ATTACKED)
        movement_event = Event(event_type=EventType.AGENT_MOVED)
        
        assert bus.publish_event(combat_event)  # Should pass filter
        assert not bus.publish_event(movement_event)  # Should be filtered out
        
        assert bus.get_queue_size() == 1
        assert bus.events_published == 1
        assert bus.events_dropped == 1
    
    def test_priority_processing(self):
        """Test priority-based event processing."""
        bus = EventBus()
        handler = MockEventHandler()
        bus.register_handler(handler)
        
        # Publish events in non-priority order
        low_event = Event(event_type=EventType.DEBUG_INFO, priority=EventPriority.LOW)
        critical_event = Event(event_type=EventType.ERROR_OCCURRED, priority=EventPriority.CRITICAL)
        normal_event = Event(event_type=EventType.AGENT_MOVED, priority=EventPriority.NORMAL)
        
        bus.publish_event(low_event)
        bus.publish_event(critical_event)
        bus.publish_event(normal_event)
        
        # Process all events
        bus.process_events()
        
        # Should be processed in priority order
        processed_events = handler.handled_events
        assert len(processed_events) == 3
        assert processed_events[0].priority == EventPriority.CRITICAL
        assert processed_events[1].priority == EventPriority.NORMAL
        assert processed_events[2].priority == EventPriority.LOW
    
    def test_create_and_publish(self):
        """Test create_and_publish convenience method."""
        bus = EventBus()
        
        event_id = bus.create_and_publish(
            event_type=EventType.AGENT_ATTACKED,
            source_id="attacker",
            target_ids=["victim"],
            data={"damage": 10},
            priority=EventPriority.HIGH
        )
        
        assert event_id != ""
        assert bus.get_queue_size() == 1
    
    def test_statistics(self):
        """Test event bus statistics."""
        bus = EventBus()
        handler = MockEventHandler()
        bus.register_handler(handler)
        
        # Publish and process some events
        for i in range(5):
            event = Event(event_type=EventType.AGENT_MOVED)
            bus.publish_event(event)
        
        bus.process_events()
        
        stats = bus.get_statistics()
        assert stats['events_published'] == 5
        assert stats['events_processed'] == 5
        assert stats['queue_size'] == 0
        assert stats['handlers_registered'] == 1
        assert 'average_processing_time_ms' in stats


class TestConvenienceFunctions:
    """Test convenience functions for creating events."""
    
    def test_create_combat_event(self):
        """Test combat event creation function."""
        position = Vector2D(100, 200)
        event = create_combat_event(
            attacker_id="attacker_1",
            victim_id="victim_1",
            damage=25.0,
            weapon_type="sword",
            position=position
        )
        
        assert isinstance(event, CombatEvent)
        assert event.event_type == EventType.AGENT_ATTACKED
        assert event.attacker_id == "attacker_1"
        assert event.victim_id == "victim_1"
        assert event.damage_amount == 25.0
        assert event.weapon_type == "sword"
        assert event.position == position
        assert event.priority == EventPriority.HIGH
    
    def test_create_movement_event(self):
        """Test movement event creation function."""
        old_pos = Vector2D(10, 20)
        new_pos = Vector2D(30, 40)
        
        event = create_movement_event("agent_1", old_pos, new_pos)
        
        assert isinstance(event, MovementEvent)
        assert event.event_type == EventType.AGENT_MOVED
        assert event.source_id == "agent_1"
        assert event.old_position == old_pos
        assert event.new_position == new_pos
        assert event.priority == EventPriority.LOW
    
    def test_create_communication_event(self):
        """Test communication event creation function."""
        # Test targeted communication
        event = create_communication_event(
            sender_id="sender_1",
            message="Help needed at position X",
            targets=["receiver_1", "receiver_2"],
            communication_type="help_request"
        )
        
        assert isinstance(event, CommunicationEvent)
        assert event.sender_id == "sender_1"
        assert event.message == "Help needed at position X"
        assert event.target_ids == ["receiver_1", "receiver_2"]
        assert event.communication_type == "help_request"
        assert not event.is_broadcast
        
        # Test broadcast communication
        broadcast_event = create_communication_event(
            sender_id="commander",
            message="All units retreat"
        )
        
        assert broadcast_event.is_broadcast


class TestEventSystemIntegration:
    """Test complete event system integration."""
    
    def test_full_event_flow(self):
        """Test complete event flow from creation to processing."""
        bus = EventBus()
        
        # Create specialized handlers
        combat_handler = MockEventHandler([EventType.AGENT_ATTACKED, EventType.AGENT_DAMAGED])
        movement_handler = MockEventHandler([EventType.AGENT_MOVED])
        communication_handler = MockEventHandler([EventType.STRATEGY_SHARED, EventType.HELP_REQUESTED])
        
        bus.register_handler(combat_handler)
        bus.register_handler(movement_handler)
        bus.register_handler(communication_handler)
        
        # Create and publish various events
        combat_event = create_combat_event("attacker", "victim", 20.0)
        movement_event = create_movement_event("agent1", Vector2D(0, 0), Vector2D(10, 10))
        comm_event = create_communication_event("leader", "Form up!", ["agent1", "agent2"])
        
        bus.publish_event(combat_event)
        bus.publish_event(movement_event)
        bus.publish_event(comm_event)
        
        # Process all events
        processed = bus.process_events()
        
        assert processed == 3
        assert len(combat_handler.handled_events) == 1
        assert len(movement_handler.handled_events) == 1
        assert len(communication_handler.handled_events) == 1
        
        # Verify events were processed correctly
        assert combat_handler.handled_events[0].event_type == EventType.AGENT_ATTACKED
        assert movement_handler.handled_events[0].event_type == EventType.AGENT_MOVED
        assert communication_handler.handled_events[0].event_type == EventType.STRATEGY_SHARED
    
    def test_global_event_bus(self):
        """Test global event bus instance."""
        # Should be able to access global instance
        assert global_event_bus is not None
        assert isinstance(global_event_bus, EventBus)
        
        # Test basic functionality
        initial_count = global_event_bus.events_published
        event = Event(event_type=EventType.DEBUG_INFO)
        global_event_bus.publish_event(event)
        
        assert global_event_bus.events_published > initial_count


if __name__ == "__main__":
    pytest.main([__file__])
