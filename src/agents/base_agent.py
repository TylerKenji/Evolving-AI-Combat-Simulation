"""
Agent Base Class Interface

This module defines the abstract base class for all AI agents in the Battle AI system.
The Agent class provides the core interface that all agent implementations must follow,
supporting combat abilities, decision making, evolution, and cooperation.

Key Features:
- Health and damage systems
- Movement and positioning
- Combat abilities (attack, dodge, defend)
- AI decision making framework
- Genetic algorithm support
- Team cooperation mechanics
- Weapon and equipment systems
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set, Union, Sequence
from dataclasses import dataclass, field
import time
import uuid
import logging
from datetime import datetime

from src.utils.vector2d import Vector2D
from src.utils.logging_config import get_logger
from src.agents.agent_state import (
    CombatState, MovementState, SensorData, 
    CombatStatus, MovementStatus
)


class AgentState(Enum):
    """Possible states for an agent."""
    ALIVE = "alive"
    DEAD = "dead"
    STUNNED = "stunned"
    DEFENDING = "defending"
    ATTACKING = "attacking"
    MOVING = "moving"
    IDLE = "idle"


class AgentRole(Enum):
    """Specialized roles for agents."""
    TANK = "tank"           # High health, defensive focus
    DPS = "dps"            # High damage, offensive focus
    SUPPORT = "support"     # Healing, buffs, team utility
    SCOUT = "scout"        # High speed, reconnaissance
    BALANCED = "balanced"   # Balanced stats and abilities


class CombatAction(Enum):
    """Types of combat actions an agent can perform."""
    ATTACK_MELEE = "attack_melee"
    ATTACK_RANGED = "attack_ranged"
    DODGE = "dodge"
    DEFEND = "defend"
    MOVE = "move"
    USE_SPECIAL = "use_special"
    RETREAT = "retreat"
    COOPERATE = "cooperate"


@dataclass
class AgentStats:
    """Core statistics for an agent."""
    max_health: float = 100.0
    current_health: float = field(default=0.0)
    speed: float = 50.0
    attack_damage: float = 20.0
    defense: float = 5.0
    accuracy: float = 0.8
    dodge_chance: float = 0.1
    vision_range: float = 150.0
    attack_range: float = 30.0
    attack_cooldown: float = 1.0  # seconds
    
    def __post_init__(self):
        """Set current_health to max_health if not explicitly set."""
        if self.current_health == 0.0:
            self.current_health = self.max_health


@dataclass
class AgentGenome:
    """Genetic representation for evolutionary algorithms."""
    
    # Movement behavior weights
    movement_aggression: float = 0.5      # 0=defensive, 1=aggressive positioning
    movement_cooperation: float = 0.5     # 0=individualistic, 1=team-oriented
    positioning_preference: float = 0.5   # 0=close combat, 1=ranged combat
    
    # Combat behavior weights
    attack_aggression: float = 0.5        # 0=cautious, 1=aggressive attacking
    defense_priority: float = 0.5         # 0=offense focused, 1=defense focused
    target_selection: float = 0.5         # 0=nearest, 1=strategic targeting
    
    # Special abilities and tactics
    dodge_tendency: float = 0.5           # Likelihood to attempt dodges
    retreat_threshold: float = 0.3        # Health % to trigger retreat
    cooperation_willingness: float = 0.5  # Tendency to help teammates
    risk_tolerance: float = 0.5           # 0=risk averse, 1=risk seeking
    
    # Weapon and equipment preferences
    weapon_preferences: Dict[str, float] = field(default_factory=dict)
    
    # Mutation parameters
    mutation_rate: float = 0.1
    mutation_strength: float = 0.1
    
    def mutate(self) -> 'AgentGenome':
        """Create a mutated copy of this genome."""
        import random
        
        # Create a copy
        new_genome = AgentGenome(
            movement_aggression=self.movement_aggression,
            movement_cooperation=self.movement_cooperation,
            positioning_preference=self.positioning_preference,
            attack_aggression=self.attack_aggression,
            defense_priority=self.defense_priority,
            target_selection=self.target_selection,
            dodge_tendency=self.dodge_tendency,
            retreat_threshold=self.retreat_threshold,
            cooperation_willingness=self.cooperation_willingness,
            risk_tolerance=self.risk_tolerance,
            weapon_preferences=self.weapon_preferences.copy(),
            mutation_rate=self.mutation_rate,
            mutation_strength=self.mutation_strength
        )
        
        # Apply mutations to each gene
        genes = [
            'movement_aggression', 'movement_cooperation', 'positioning_preference',
            'attack_aggression', 'defense_priority', 'target_selection',
            'dodge_tendency', 'retreat_threshold', 'cooperation_willingness',
            'risk_tolerance'
        ]
        
        for gene in genes:
            if random.random() < self.mutation_rate:
                current_value = getattr(new_genome, gene)
                mutation = random.gauss(0, self.mutation_strength)
                new_value = max(0.0, min(1.0, current_value + mutation))
                setattr(new_genome, gene, new_value)
        
        return new_genome
    
    def crossover(self, other: 'AgentGenome') -> 'AgentGenome':
        """Create offspring through crossover with another genome."""
        import random
        
        child = AgentGenome()
        
        # Simple single-point crossover for each gene
        genes = [
            'movement_aggression', 'movement_cooperation', 'positioning_preference',
            'attack_aggression', 'defense_priority', 'target_selection',
            'dodge_tendency', 'retreat_threshold', 'cooperation_willingness',
            'risk_tolerance'
        ]
        
        for gene in genes:
            parent_value = getattr(self, gene) if random.random() < 0.5 else getattr(other, gene)
            setattr(child, gene, parent_value)
        
        # Crossover weapon preferences
        all_weapons = set(self.weapon_preferences.keys()) | set(other.weapon_preferences.keys())
        for weapon in all_weapons:
            self_pref = self.weapon_preferences.get(weapon, 0.5)
            other_pref = other.weapon_preferences.get(weapon, 0.5)
            child.weapon_preferences[weapon] = self_pref if random.random() < 0.5 else other_pref
        
        return child


@dataclass
class AgentMemory:
    """Memory system for learning and adaptation."""
    
    # Experience tracking
    battles_fought: int = 0
    victories: int = 0
    defeats: int = 0
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    
    # Opponent tracking
    enemy_encounters: Dict[str, int] = field(default_factory=dict)
    successful_strategies: List[str] = field(default_factory=list)
    failed_strategies: List[str] = field(default_factory=list)
    
    # Learning metrics
    fitness_history: List[float] = field(default_factory=list)
    generation: int = 0
    
    def calculate_fitness(self) -> float:
        """Calculate current fitness score for evolution."""
        if self.battles_fought == 0:
            return 0.0
        
        # Base fitness from win rate
        win_rate = self.victories / self.battles_fought
        
        # Damage efficiency bonus
        damage_ratio = self.damage_dealt / max(self.damage_taken, 1.0)
        
        # Survival bonus
        survival_rate = (self.battles_fought - self.defeats) / self.battles_fought
        
        # Combine metrics with weights
        fitness = (
            win_rate * 0.4 +
            min(damage_ratio / 5.0, 1.0) * 0.3 +  # Cap damage ratio influence
            survival_rate * 0.3
        )
        
        return max(0.0, min(1.0, fitness))


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the Battle AI system.
    
    This class defines the core interface that all agent implementations must follow,
    providing standard methods for movement, combat, decision making, and evolution.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        position: Optional[Vector2D] = None,
        stats: Optional[AgentStats] = None,
        genome: Optional[AgentGenome] = None,
        role: AgentRole = AgentRole.BALANCED,
        team_id: Optional[str] = None
    ):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for this agent
            position: Starting position on the battlefield
            stats: Agent statistics and capabilities
            genome: Genetic representation for evolution
            role: Specialized role/class for this agent
            team_id: Team membership identifier
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.position = position or Vector2D(0, 0)
        self.stats = stats or AgentStats()
        self.genome = genome or AgentGenome()
        self.role = role
        self.team_id = team_id
        
        # Current state
        self.state = AgentState.ALIVE
        self.velocity = Vector2D(0, 0)
        self.facing_direction = Vector2D(1, 0)
        
        # Combat tracking
        self.last_attack_time = 0.0
        self.target_agent = None
        self.is_defending = False
        
        # Memory and learning
        self.memory = AgentMemory()
        
        # Logger
        self.logger = get_logger(f"Agent_{self.agent_id[:8]}")
        
        # Advanced status management
        self.combat_state = CombatState()
        self.movement_state = MovementState()
        self.sensor_data = SensorData()
        
        # Status effects and timers
        self.status_effects = {}  # Dict to store active status effects
        self.status_timers = {}   # Dict to store status effect timers
        
        # Collision detection properties
        self.collision_radius = 10.0  # Default collision radius
        self.collision_events = []    # Recent collision events for this agent
        
        self.logger.debug(f"🤖 Agent {self.agent_id[:8]} initialized with role {role.value}")
    
    # === Core Properties ===
    
    @property
    def is_alive(self) -> bool:
        """Check if agent is alive."""
        return self.state != AgentState.DEAD and self.stats.current_health > 0
    
    @property
    def health_percentage(self) -> float:
        """Get current health as percentage of max health."""
        return self.stats.current_health / self.stats.max_health
    
    @property
    def can_attack(self) -> bool:
        """Check if agent can perform an attack."""
        current_time = time.time()
        basic_can_attack = (self.is_alive and 
                           current_time - self.last_attack_time >= self.stats.attack_cooldown)
        
        # Additional status checks using advanced combat state
        advanced_can_attack = self.combat_state.can_attack()
        
        return basic_can_attack and advanced_can_attack
    
    # === Abstract Methods (Must be implemented by subclasses) ===
    
    @abstractmethod
    def update(self, dt: float, battlefield_info: Dict[str, Any]) -> None:
        """
        Update agent state for one simulation step.
        
        Args:
            dt: Time step in seconds
            battlefield_info: Information about the current battlefield state
        """
        pass
    
    @abstractmethod
    def decide_action(self, visible_agents: Sequence['BaseAgent'], 
                     battlefield_info: Dict[str, Any]) -> CombatAction:
        """
        Decide what action to take based on current situation.
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            The action this agent wants to perform
        """
        pass
    
    @abstractmethod
    def select_target(self, visible_enemies: Sequence['BaseAgent']) -> Optional['BaseAgent']:
        """
        Select a target from visible enemies.
        
        Args:
            visible_enemies: List of enemy agents within vision range
            
        Returns:
            Selected target agent, or None if no valid target
        """
        pass
    
    @abstractmethod
    def calculate_movement(self, visible_agents: Sequence['BaseAgent'], 
                         battlefield_info: Dict[str, Any]) -> Vector2D:
        """
        Calculate desired movement direction and speed.
        
        Args:
            visible_agents: List of agents visible to this agent
            battlefield_info: Current battlefield state information
            
        Returns:
            Desired velocity vector
        """
        pass
    
    # === Core Combat Methods ===
    
    def take_damage(self, damage: float, attacker: Optional['BaseAgent'] = None) -> bool:
        """
        Apply damage to this agent.
        
        Args:
            damage: Amount of damage to apply
            attacker: Agent that caused the damage
            
        Returns:
            True if agent died from this damage
        """
        if not self.is_alive or self.is_stunned():
            return False
        
        # Apply defense reduction
        actual_damage = max(0, damage - self.stats.defense)
        
        # Apply status effect modifiers
        if self.has_status_effect('shield'):
            shield_intensity = self.get_status_effect_intensity('shield')
            actual_damage *= (1.0 - shield_intensity * 0.5)  # Shield reduces damage by up to 50%
        
        # Apply dodge chance
        import random
        dodge_success = random.random() < self.stats.dodge_chance
        if dodge_success:
            self.update_combat_statistics('dodge', success=True)
            self.logger.debug(f"💨 Agent {self.agent_id[:8]} dodged attack!")
            self.log_decision_making({"action": "dodge", "damage": damage, "chance": self.stats.dodge_chance}, "Successfully dodged attack")
            return False
        else:
            self.update_combat_statistics('dodge', success=False)
        
        # Apply damage
        self.stats.current_health -= actual_damage
        self.memory.damage_taken += actual_damage
        self.combat_state.total_damage_taken += actual_damage
        self.combat_state.last_damage_time = datetime.now()
        
        self.logger.debug(f"💥 Agent {self.agent_id[:8]} took {actual_damage:.1f} damage "
                         f"({self.stats.current_health:.1f}/{self.stats.max_health} HP)")
        
        # Check if agent died
        if self.stats.current_health <= 0:
            self.state = AgentState.DEAD
            self.combat_state.status = CombatStatus.NOT_IN_COMBAT  # Dead agents are no longer in combat
            self.logger.info(f"☠️ Agent {self.agent_id[:8]} died")
            self.log_performance_metrics({"death_damage": actual_damage, "total_damage_taken": self.combat_state.total_damage_taken})
            return True
        
        return False
    
    def attack(self, target: 'BaseAgent') -> bool:
        """
        Attempt to attack a target agent.
        
        Args:
            target: Agent to attack
            
        Returns:
            True if attack was successful
        """
        if not self.can_attack or not target.is_alive:
            return False
        
        # Check range
        distance = self.position.distance_to(target.position)
        if distance > self.stats.attack_range:
            return False
        
        # Apply accuracy
        import random
        attack_success = random.random() <= self.stats.accuracy
        self.update_combat_statistics('attack', success=attack_success)
        
        if not attack_success:
            self.logger.debug(f"⚡ Agent {self.agent_id[:8]} missed attack on {target.agent_id[:8]}")
            self.log_decision_making({"action": "attack", "target": target.agent_id[:8], "accuracy": self.stats.accuracy}, "Attack missed")
            return False
        
        # Perform attack
        self.last_attack_time = time.time()
        self.combat_state.last_attack_time = datetime.now()
        self.state = AgentState.ATTACKING
        self.combat_state.status = CombatStatus.ENGAGING
        self.combat_state.current_target_id = target.agent_id
        
        # Calculate damage with some randomness and status effects
        base_damage = self.stats.attack_damage
        
        # Apply damage boost status effect
        if self.has_status_effect('damage_boost'):
            boost_intensity = self.get_status_effect_intensity('damage_boost')
            base_damage *= (1.0 + boost_intensity * 0.5)  # Up to 50% damage boost
        
        damage_variance = base_damage * 0.2  # ±20% variance
        actual_damage = base_damage + random.uniform(-damage_variance, damage_variance)
        
        # Apply damage to target
        target_died = target.take_damage(actual_damage, self)
        self.memory.damage_dealt += actual_damage
        self.combat_state.total_damage_dealt += actual_damage
        
        self.logger.debug(f"⚔️ Agent {self.agent_id[:8]} attacked {target.agent_id[:8]} "
                         f"for {actual_damage:.1f} damage")
        
        # Log attack decision and performance
        self.log_decision_making(
            {"action": "attack", "target": target.agent_id[:8], "damage": actual_damage, "distance": distance},
            "Successful attack"
        )
        self.log_performance_metrics({"damage_dealt": actual_damage, "total_damage_dealt": self.combat_state.total_damage_dealt})
        
        # Update memory
        if target_died:
            self.memory.victories += 1
            self.log_performance_metrics({"victory": True, "total_victories": self.memory.victories})
        
        return True
    
    def heal(self, amount: float) -> None:
        """
        Heal this agent by the specified amount.
        
        Args:
            amount: Amount of health to restore
        """
        if not self.is_alive:
            return
        
        old_health = self.stats.current_health
        self.stats.current_health = min(
            self.stats.max_health,
            self.stats.current_health + amount
        )
        
        healed = self.stats.current_health - old_health
        if healed > 0:
            self.logger.debug(f"💚 Agent {self.agent_id[:8]} healed {healed:.1f} HP")
    
    # === Status Effect Management ===
    
    def apply_status_effect(self, effect_name: str, duration: float, intensity: float = 1.0) -> None:
        """
        Apply a status effect to this agent.
        
        Args:
            effect_name: Name of the status effect (e.g., 'stun', 'poison', 'shield')
            duration: Duration in seconds
            intensity: Intensity/strength of the effect (0.0 to 1.0+)
        """
        self.status_effects[effect_name] = intensity
        self.status_timers[effect_name] = duration
        
        # Apply immediate effects based on status type
        if effect_name == 'stun':
            self.state = AgentState.STUNNED
            self.combat_state.stun_remaining = duration
        elif effect_name == 'speed_boost':
            # Speed boost is handled in movement calculations
            pass
        elif effect_name == 'damage_boost':
            # Damage boost is handled in attack calculations
            pass
        
        self.logger.debug(f"✨ Agent {self.agent_id[:8]} affected by {effect_name} "
                         f"(intensity: {intensity:.1f}, duration: {duration:.1f}s)")
        
        # Use new logging method for status effect changes
        self.log_status_effect_change(effect_name, "applied", intensity, duration)
    
    def remove_status_effect(self, effect_name: str) -> bool:
        """
        Remove a specific status effect.
        
        Args:
            effect_name: Name of the effect to remove
            
        Returns:
            True if effect was removed, False if it wasn't present
        """
        if effect_name in self.status_effects:
            del self.status_effects[effect_name]
            del self.status_timers[effect_name]
            
            # Handle effect removal
            if effect_name == 'stun' and self.state == AgentState.STUNNED:
                self.state = AgentState.ALIVE
                self.combat_state.stun_remaining = 0.0
                
            self.logger.debug(f"🚫 Agent {self.agent_id[:8]} recovered from {effect_name}")
            self.log_status_effect_change(effect_name, "removed")
            return True
        return False
    
    def update_status_effects(self, dt: float) -> None:
        """
        Update all active status effects and remove expired ones.
        
        Args:
            dt: Time step in seconds
        """
        expired_effects = []
        
        for effect_name, timer in self.status_timers.items():
            new_timer = timer - dt
            if new_timer <= 0:
                expired_effects.append(effect_name)
            else:
                self.status_timers[effect_name] = new_timer
        
        # Remove expired effects
        for effect_name in expired_effects:
            self.remove_status_effect(effect_name)
        
        # Update combat state timers
        self.combat_state.attack_cooldown_remaining = max(0.0, 
            self.combat_state.attack_cooldown_remaining - dt)
        self.combat_state.special_ability_cooldown = max(0.0, 
            self.combat_state.special_ability_cooldown - dt)
        self.combat_state.stun_remaining = max(0.0, 
            self.combat_state.stun_remaining - dt)
    
    def has_status_effect(self, effect_name: str) -> bool:
        """Check if agent has a specific status effect."""
        return effect_name in self.status_effects
    
    def get_status_effect_intensity(self, effect_name: str) -> float:
        """Get the intensity of a specific status effect."""
        return self.status_effects.get(effect_name, 0.0)
    
    def get_active_status_effects(self) -> Dict[str, Tuple[float, float]]:
        """
        Get all active status effects.
        
        Returns:
            Dictionary mapping effect names to (intensity, remaining_time) tuples
        """
        return {
            effect: (self.status_effects[effect], self.status_timers[effect])
            for effect in self.status_effects.keys()
        }
    
    def is_stunned(self) -> bool:
        """Check if agent is currently stunned."""
        return self.has_status_effect('stun') or self.state == AgentState.STUNNED
    
    def update_combat_statistics(self, action_type: str, success: bool = True) -> None:
        """
        Update combat statistics based on actions taken.
        
        Args:
            action_type: Type of action ('attack', 'dodge', 'defend')
            success: Whether the action was successful
        """
        if action_type == 'attack':
            self.combat_state.attacks_attempted += 1
            if success:
                self.combat_state.attacks_hit += 1
        elif action_type == 'dodge':
            self.combat_state.dodges_attempted += 1
            if success:
                self.combat_state.dodges_successful += 1
    
    # === Utility Methods ===
    
    def get_visible_agents(self, all_agents: Sequence['BaseAgent']) -> List['BaseAgent']:
        """
        Get list of agents visible to this agent.
        
        Args:
            all_agents: List of all agents in the simulation
            
        Returns:
            List of visible agents (excluding self)
        """
        visible = []
        for agent in all_agents:
            if agent == self or not agent.is_alive:
                continue
            
            distance = self.position.distance_to(agent.position)
            if distance <= self.stats.vision_range:
                visible.append(agent)
        
        return visible
    
    def get_enemies(self, visible_agents: Sequence['BaseAgent']) -> List['BaseAgent']:
        """
        Filter visible agents to get only enemies.
        
        Args:
            visible_agents: List of visible agents
            
        Returns:
            List of enemy agents
        """
        return [agent for agent in visible_agents 
                if agent.team_id != self.team_id]
    
    def get_allies(self, visible_agents: Sequence['BaseAgent']) -> List['BaseAgent']:
        """
        Filter visible agents to get only allies.
        
        Args:
            visible_agents: List of visible agents
            
        Returns:
            List of allied agents
        """
        return [agent for agent in visible_agents 
                if agent.team_id == self.team_id and agent != self]
    
    def distance_to(self, other: 'BaseAgent') -> float:
        """
        Calculate distance to another agent.
        
        Args:
            other: Other agent
            
        Returns:
            Distance in pixels
        """
        return self.position.distance_to(other.position)
    
    def move(self, dt: float, velocity: Vector2D, battlefield_bounds: Tuple[float, float]) -> None:
        """
        Move the agent by the specified velocity, respecting battlefield bounds.
        
        Args:
            dt: Time step in seconds
            velocity: Desired velocity vector
            battlefield_bounds: (width, height) of battlefield
        """
        if not self.is_alive:
            return
        
        # Apply status effects to movement
        effective_velocity = self._apply_movement_modifiers(velocity)
        
        # Limit velocity to agent's maximum speed
        max_speed = self._get_effective_speed()
        if effective_velocity.magnitude() > max_speed:
            effective_velocity = effective_velocity.normalize() * max_speed
        
        # Store old position for distance tracking
        old_position = Vector2D(self.position.x, self.position.y)
        
        # Update position
        new_position = self.position + effective_velocity * dt
        
        # Clamp to battlefield bounds
        width, height = battlefield_bounds
        new_position.x = max(0, min(width, new_position.x))
        new_position.y = max(0, min(height, new_position.y))
        
        # Update movement tracking
        distance_moved = old_position.distance_to(new_position)
        self.movement_state.total_distance_moved += distance_moved
        self.movement_state.current_velocity = effective_velocity
        
        # Update position and state
        self.position = new_position
        self.velocity = effective_velocity
        
        # Update facing direction if moving
        if effective_velocity.magnitude() > 0:
            self.facing_direction = effective_velocity.normalize()
            self.movement_state.status = MovementStatus.MOVING
            self.movement_state.last_position_change = datetime.now()
        else:
            self.movement_state.status = MovementStatus.STATIONARY
        
        self.state = AgentState.MOVING if effective_velocity.magnitude() > 0 else AgentState.IDLE
        
        # Log movement decision and performance
        if distance_moved > 0:
            self.log_decision_making(
                {"action": "move", "velocity": effective_velocity.magnitude(), "distance": distance_moved, "position": [new_position.x, new_position.y]},
                f"Moved {distance_moved:.2f} units"
            )
            self.log_performance_metrics({"distance_moved": distance_moved, "total_distance": self.movement_state.total_distance_moved})
        
        self.logger.debug(f"🏃 Agent {self.agent_id[:8]} moved to {self.position} with velocity {effective_velocity}")
    
    def _apply_movement_modifiers(self, velocity: Vector2D) -> Vector2D:
        """Apply status effects and other modifiers to movement velocity."""
        modified_velocity = Vector2D(velocity.x, velocity.y)
        
        # Apply speed boost effect
        if self.has_status_effect('speed_boost'):
            boost_intensity = self.get_status_effect_intensity('speed_boost')
            speed_multiplier = 1.0 + boost_intensity * 0.5  # Up to 50% speed boost
            modified_velocity = modified_velocity * speed_multiplier
        
        # Apply stun effect (prevent movement)
        if self.is_stunned():
            modified_velocity = Vector2D(0, 0)
        
        return modified_velocity
    
    def _get_effective_speed(self) -> float:
        """Get the effective maximum speed considering status effects."""
        base_speed = self.stats.speed
        
        # Apply speed boost effect to max speed
        if self.has_status_effect('speed_boost'):
            boost_intensity = self.get_status_effect_intensity('speed_boost')
            return base_speed * (1.0 + boost_intensity * 0.5)
        
        return base_speed
    
    # === Advanced Movement Methods ===
    
    def seek(self, target_position: Vector2D, max_force: float = 1.0) -> Vector2D:
        """
        Calculate steering force to seek toward a target position.
        
        Args:
            target_position: Position to move toward
            max_force: Maximum steering force
            
        Returns:
            Steering force vector
        """
        desired_velocity = (target_position - self.position).normalize() * self._get_effective_speed()
        steering_force = desired_velocity - self.velocity
        
        # Limit steering force
        if steering_force.magnitude() > max_force:
            steering_force = steering_force.normalize() * max_force
        
        return steering_force
    
    def flee(self, threat_position: Vector2D, max_force: float = 1.0) -> Vector2D:
        """
        Calculate steering force to flee from a threat position.
        
        Args:
            threat_position: Position to move away from
            max_force: Maximum steering force
            
        Returns:
            Steering force vector
        """
        desired_velocity = (self.position - threat_position).normalize() * self._get_effective_speed()
        steering_force = desired_velocity - self.velocity
        
        # Limit steering force
        if steering_force.magnitude() > max_force:
            steering_force = steering_force.normalize() * max_force
        
        return steering_force
    
    def wander(self, wander_strength: float = 0.1) -> Vector2D:
        """
        Calculate random wandering movement.
        
        Args:
            wander_strength: Strength of wandering behavior
            
        Returns:
            Wandering force vector
        """
        import random
        
        # Generate random angle change
        angle_change = (random.random() - 0.5) * 2 * wander_strength
        
        # Get current direction or random if not moving
        if self.velocity.magnitude() > 0:
            current_angle = self.velocity.angle()
        else:
            current_angle = random.random() * 2 * 3.14159
        
        new_angle = current_angle + angle_change
        wander_force = Vector2D.from_angle(new_angle) * self._get_effective_speed() * 0.5
        
        return wander_force
    
    def avoid_obstacles(self, obstacles: List[Vector2D], avoidance_radius: float = 50.0, 
                       max_force: float = 1.0) -> Vector2D:
        """
        Calculate steering force to avoid obstacles.
        
        Args:
            obstacles: List of obstacle positions
            avoidance_radius: Distance to start avoiding obstacles
            max_force: Maximum avoidance force
            
        Returns:
            Avoidance force vector
        """
        total_force = Vector2D(0, 0)
        
        for obstacle in obstacles:
            distance = self.position.distance_to(obstacle)
            if distance < avoidance_radius and distance > 0:
                # Calculate avoidance force (stronger when closer)
                avoid_direction = (self.position - obstacle).normalize()
                force_magnitude = (avoidance_radius - distance) / avoidance_radius * max_force
                total_force = total_force + avoid_direction * force_magnitude
        
        return total_force
    
    def follow_path(self, path: List[Vector2D], path_radius: float = 10.0) -> Vector2D:
        """
        Calculate steering force to follow a path.
        
        Args:
            path: List of waypoints to follow
            path_radius: Distance to consider a waypoint reached
            
        Returns:
            Path following force vector
        """
        if not path:
            return Vector2D(0, 0)
        
        # Update movement state path
        self.movement_state.path = path
        
        # Get current target waypoint
        current_waypoint = self.movement_state.get_next_waypoint()
        if current_waypoint is None:
            if self.movement_state.path:
                current_waypoint = self.movement_state.path[0]
                self.movement_state.current_path_index = 0
            else:
                return Vector2D(0, 0)
        
        # Check if we've reached the current waypoint
        distance_to_waypoint = self.position.distance_to(current_waypoint)
        if distance_to_waypoint < path_radius:
            # Move to next waypoint
            if not self.movement_state.advance_path():
                # Reached end of path
                return Vector2D(0, 0)
            current_waypoint = self.movement_state.get_next_waypoint()
            if current_waypoint is None:
                return Vector2D(0, 0)
        
        # Seek toward current waypoint
        return self.seek(current_waypoint)
    
    def set_movement_target(self, target: Vector2D) -> None:
        """
        Set a movement target for the agent.
        
        Args:
            target: Target position to move toward
        """
        self.movement_state.target_position = target
        self.movement_state.status = MovementStatus.MOVING
        self.logger.debug(f"🎯 Agent {self.agent_id[:8]} set movement target to {target}")
    
    def clear_movement_target(self) -> None:
        """Clear the current movement target."""
        self.movement_state.target_position = None
        self.movement_state.status = MovementStatus.STATIONARY
        self.movement_state.path.clear()
        self.movement_state.current_path_index = 0
    
    def is_near_target(self, tolerance: float = 10.0) -> bool:
        """
        Check if agent is near its movement target.
        
        Args:
            tolerance: Distance tolerance for "near"
            
        Returns:
            True if near target or no target set
        """
        if not self.movement_state.has_target() or self.movement_state.target_position is None:
            return True
        
        return self.position.distance_to(self.movement_state.target_position) <= tolerance
    
    def calculate_separation(self, nearby_agents: List['BaseAgent'], 
                           separation_radius: float = 30.0, max_force: float = 1.0) -> Vector2D:
        """
        Calculate separation force to avoid crowding with other agents.
        
        Args:
            nearby_agents: List of nearby agents to separate from
            separation_radius: Distance to maintain from other agents
            max_force: Maximum separation force
            
        Returns:
            Separation force vector
        """
        separation_force = Vector2D(0, 0)
        count = 0
        
        for agent in nearby_agents:
            if agent != self and agent.is_alive:
                distance = self.position.distance_to(agent.position)
                if 0 < distance < separation_radius:
                    # Calculate separation direction (away from other agent)
                    diff = (self.position - agent.position).normalize()
                    # Weight by distance (closer = stronger force)
                    diff = diff * (separation_radius - distance) / separation_radius
                    separation_force = separation_force + diff
                    count += 1
        
        if count > 0:
            separation_force = separation_force / count  # Average
            if separation_force.magnitude() > max_force:
                separation_force = separation_force.normalize() * max_force
        
        return separation_force
    
    def calculate_alignment(self, nearby_agents: List['BaseAgent'], 
                          alignment_radius: float = 50.0, max_force: float = 0.5) -> Vector2D:
        """
        Calculate alignment force to match velocity with nearby agents.
        
        Args:
            nearby_agents: List of nearby agents to align with
            alignment_radius: Distance to consider for alignment
            max_force: Maximum alignment force
            
        Returns:
            Alignment force vector
        """
        average_velocity = Vector2D(0, 0)
        count = 0
        
        for agent in nearby_agents:
            if agent != self and agent.is_alive:
                distance = self.position.distance_to(agent.position)
                if 0 < distance < alignment_radius:
                    average_velocity = average_velocity + agent.velocity
                    count += 1
        
        if count > 0:
            average_velocity = average_velocity / count
            alignment_force = average_velocity - self.velocity
            if alignment_force.magnitude() > max_force:
                alignment_force = alignment_force.normalize() * max_force
            return alignment_force
        
        return Vector2D(0, 0)
    
    def calculate_cohesion(self, nearby_agents: List['BaseAgent'], 
                         cohesion_radius: float = 100.0, max_force: float = 0.3) -> Vector2D:
        """
        Calculate cohesion force to move toward center of nearby agents.
        
        Args:
            nearby_agents: List of nearby agents to move toward
            cohesion_radius: Distance to consider for cohesion
            max_force: Maximum cohesion force
            
        Returns:
            Cohesion force vector
        """
        center_of_mass = Vector2D(0, 0)
        count = 0
        
        for agent in nearby_agents:
            if agent != self and agent.is_alive:
                distance = self.position.distance_to(agent.position)
                if 0 < distance < cohesion_radius:
                    center_of_mass = center_of_mass + agent.position
                    count += 1
        
        if count > 0:
            center_of_mass = center_of_mass / count
            return self.seek(center_of_mass, max_force)
        
        return Vector2D(0, 0)
    
    # === Collision Detection Methods ===
    
    def check_collision_with_agent(self, other: 'BaseAgent') -> bool:
        """
        Check if this agent is colliding with another agent.
        
        Args:
            other: The other agent to check collision with
            
        Returns:
            True if agents are colliding
        """
        if not other.is_alive or other == self:
            return False
        
        distance = self.position.distance_to(other.position)
        collision_distance = self.collision_radius + other.collision_radius
        
        return distance < collision_distance
    
    def check_collision_with_point(self, point: Vector2D, radius: float = 0.0) -> bool:
        """
        Check if this agent is colliding with a point or circular object.
        
        Args:
            point: Position to check collision with
            radius: Radius of the object at the point
            
        Returns:
            True if agent is colliding with the point/object
        """
        distance = self.position.distance_to(point)
        collision_distance = self.collision_radius + radius
        
        return distance < collision_distance
    
    def check_collision_with_bounds(self, battlefield_bounds: Tuple[float, float]) -> bool:
        """
        Check if this agent is colliding with battlefield boundaries.
        
        Args:
            battlefield_bounds: (width, height) of the battlefield
            
        Returns:
            True if agent is colliding with any boundary
        """
        width, height = battlefield_bounds
        
        return (
            self.position.x <= self.collision_radius or
            self.position.x >= width - self.collision_radius or
            self.position.y <= self.collision_radius or
            self.position.y >= height - self.collision_radius
        )
    
    def get_collision_boundary_normal(self, battlefield_bounds: Tuple[float, float]) -> Optional[Vector2D]:
        """
        Get the normal vector of the boundary this agent is colliding with.
        
        Args:
            battlefield_bounds: (width, height) of the battlefield
            
        Returns:
            Normal vector pointing inward from the boundary, or None if no collision
        """
        width, height = battlefield_bounds
        
        if self.position.x <= self.collision_radius:
            return Vector2D(1, 0)  # Left boundary - normal points right
        elif self.position.x >= width - self.collision_radius:
            return Vector2D(-1, 0)  # Right boundary - normal points left
        elif self.position.y <= self.collision_radius:
            return Vector2D(0, 1)  # Top boundary - normal points down
        elif self.position.y >= height - self.collision_radius:
            return Vector2D(0, -1)  # Bottom boundary - normal points up
        
        return None
    
    def resolve_collision_with_agent(self, other: 'BaseAgent', separation_force: float = 1.0) -> None:
        """
        Resolve collision with another agent by pushing them apart.
        
        Args:
            other: The other agent in collision
            separation_force: Strength of the separation force
        """
        if not self.check_collision_with_agent(other):
            return
        
        # Calculate separation direction
        direction = (self.position - other.position)
        distance = direction.magnitude()
        
        if distance == 0:
            # If exactly on top of each other, use random direction
            import random
            direction = Vector2D(random.uniform(-1, 1), random.uniform(-1, 1))
        
        direction = direction.normalize()
        
        # Calculate overlap amount
        collision_distance = self.collision_radius + other.collision_radius
        overlap = collision_distance - distance
        
        # Move agents apart by half the overlap each
        separation = direction * (overlap * 0.5 * separation_force)
        
        # Only move if agent is alive and not stunned
        if self.is_alive and not self.has_status_effect('stun'):
            self.position = self.position + separation
        if other.is_alive and not other.has_status_effect('stun'):
            other.position = other.position - separation
    
    def resolve_boundary_collision(self, battlefield_bounds: Tuple[float, float]) -> None:
        """
        Resolve collision with battlefield boundaries by clamping position.
        
        Args:
            battlefield_bounds: (width, height) of the battlefield
        """
        width, height = battlefield_bounds
        
        # Clamp position to stay within bounds accounting for collision radius
        self.position.x = max(self.collision_radius, 
                              min(width - self.collision_radius, self.position.x))
        self.position.y = max(self.collision_radius, 
                              min(height - self.collision_radius, self.position.y))
    
    def get_nearby_agents_for_collision(self, all_agents: List['BaseAgent'], 
                                      check_radius: Optional[float] = None) -> List['BaseAgent']:
        """
        Get agents within collision checking distance.
        
        Args:
            all_agents: List of all agents to check
            check_radius: Radius to check for nearby agents (defaults to 3x collision radius)
            
        Returns:
            List of agents within checking radius
        """
        if check_radius is None:
            check_radius = self.collision_radius * 3.0
        
        nearby = []
        for agent in all_agents:
            if agent != self and agent.is_alive:
                distance = self.position.distance_to(agent.position)
                if distance <= check_radius:
                    nearby.append(agent)
        
        return nearby
    
    def update_collision_state(self, dt: float, all_agents: List['BaseAgent'], 
                             battlefield_bounds: Tuple[float, float]) -> None:
        """
        Update collision state and resolve any collisions.
        
        Args:
            dt: Time step in seconds
            all_agents: List of all agents in the environment
            battlefield_bounds: (width, height) of the battlefield
        """
        # Clear previous collision events
        self.collision_events.clear()
        
        # Check and resolve boundary collisions
        if self.check_collision_with_bounds(battlefield_bounds):
            self.resolve_boundary_collision(battlefield_bounds)
            
            # Record boundary collision event
            boundary_normal = self.get_collision_boundary_normal(battlefield_bounds)
            if boundary_normal:
                collision_event = {
                    'type': 'boundary',
                    'normal': boundary_normal,
                    'timestamp': time.time(),
                    'position': Vector2D(self.position.x, self.position.y)
                }
                self.collision_events.append(collision_event)
                
                # Log boundary collision with details
                self.log_collision_event('boundary', {
                    'normal': boundary_normal,
                    'old_position': f"({self.position.x:.1f}, {self.position.y:.1f})",
                    'bounds': f"{battlefield_bounds[0]}x{battlefield_bounds[1]}"
                })
        
        # Check and resolve agent collisions
        nearby_agents = self.get_nearby_agents_for_collision(all_agents)
        for other_agent in nearby_agents:
            if self.check_collision_with_agent(other_agent):
                self.resolve_collision_with_agent(other_agent)
                
                # Record agent collision event
                collision_event = {
                    'type': 'agent',
                    'other_agent': other_agent,
                    'timestamp': time.time(),
                    'position': Vector2D(self.position.x, self.position.y)
                }
                self.collision_events.append(collision_event)
                
                # Log agent collision with details
                self.log_collision_event('agent', {
                    'other_agent_id': other_agent.agent_id[:8],
                    'other_agent_role': other_agent.role.value,
                    'distance': f"{self.position.distance_to(other_agent.position):.1f}",
                    'combined_radius': f"{self.collision_radius + other_agent.collision_radius:.1f}"
                })
    
    def has_recent_collision(self, collision_type: Optional[str] = None, 
                           time_window: float = 1.0) -> bool:
        """
        Check if agent has had a recent collision.
        
        Args:
            collision_type: Type of collision to check for ('boundary', 'agent', or None for any)
            time_window: Time window in seconds to check for recent collisions
            
        Returns:
            True if agent has had a recent collision of the specified type
        """
        current_time = time.time()
        
        for event in self.collision_events:
            if current_time - event['timestamp'] <= time_window:
                if collision_type is None or event['type'] == collision_type:
                    return True
        
        return False
    
    def update_movement_state(self, dt: float) -> None:
        """
        Update movement state and statistics.
        
        Args:
            dt: Time step in seconds
        """
        # Update movement efficiency if we have a target
        if self.movement_state.has_target() and self.movement_state.target_position is not None:
            direct_distance = self.position.distance_to(self.movement_state.target_position)
            if self.movement_state.total_distance_moved > 0:
                self.movement_state.movement_efficiency = direct_distance / self.movement_state.total_distance_moved
        
        # Check if agent is stuck (not moving when it should be)
        if self.movement_state.current_velocity.magnitude() < 0.1 and self.movement_state.has_target():
            self.movement_state.stuck_counter += 1
        else:
            self.movement_state.stuck_counter = 0
        
        # Update movement status based on velocity
        if self.movement_state.current_velocity.magnitude() > self._get_effective_speed() * 0.8:
            self.movement_state.status = MovementStatus.RUNNING
        elif self.movement_state.current_velocity.magnitude() > 0.1:
            self.movement_state.status = MovementStatus.MOVING
        else:
            self.movement_state.status = MovementStatus.STATIONARY
    
    def should_retreat(self) -> bool:
        """
        Check if agent should retreat based on health and strategy.
        
        Returns:
            True if agent should retreat
        """
        health_threshold = self.genome.retreat_threshold
        return self.health_percentage <= health_threshold
    
    # === Evolution Methods ===
    
    def update_fitness(self) -> None:
        """Update fitness score based on current performance."""
        fitness = self.memory.calculate_fitness()
        self.memory.fitness_history.append(fitness)
        
        # Keep only recent fitness history
        if len(self.memory.fitness_history) > 100:
            self.memory.fitness_history.pop(0)
    
    def get_fitness(self) -> float:
        """Get current fitness score."""
        return self.memory.calculate_fitness()
    
    def clone(self, mutate: bool = True) -> 'BaseAgent':
        """
        Create a clone of this agent for evolution.
        
        Args:
            mutate: Whether to apply mutations to the clone
            
        Returns:
            New agent instance with similar properties
        """
        new_genome = self.genome.mutate() if mutate else self.genome
        
        # Create new agent of the same type
        clone = self.__class__(
            position=Vector2D(0, 0),  # Will be set by environment
            stats=AgentStats(
                max_health=self.stats.max_health,
                speed=self.stats.speed,
                attack_damage=self.stats.attack_damage,
                defense=self.stats.defense,
                accuracy=self.stats.accuracy,
                dodge_chance=self.stats.dodge_chance,
                vision_range=self.stats.vision_range,
                attack_range=self.stats.attack_range,
                attack_cooldown=self.stats.attack_cooldown
            ),
            genome=new_genome,
            role=self.role,
            team_id=self.team_id
        )
        
        clone.memory.generation = self.memory.generation + 1
        
        return clone
    
    # === Serialization Methods ===
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize agent state to dictionary.
        
        Returns:
            Dictionary containing all agent state data
        """
        return {
            'agent_id': self.agent_id,
            'position': {'x': self.position.x, 'y': self.position.y},
            'stats': {
                'max_health': self.stats.max_health,
                'current_health': self.stats.current_health,
                'speed': self.stats.speed,
                'attack_damage': self.stats.attack_damage,
                'attack_range': self.stats.attack_range,
                'attack_cooldown': self.stats.attack_cooldown,
                'defense': self.stats.defense,
                'vision_range': self.stats.vision_range,
                'dodge_chance': self.stats.dodge_chance,
                'accuracy': self.stats.accuracy
            },
            'genome': {
                'movement_aggression': self.genome.movement_aggression,
                'movement_cooperation': self.genome.movement_cooperation,
                'positioning_preference': self.genome.positioning_preference,
                'attack_aggression': self.genome.attack_aggression,
                'defense_priority': self.genome.defense_priority,
                'target_selection': self.genome.target_selection,
                'dodge_tendency': self.genome.dodge_tendency,
                'retreat_threshold': self.genome.retreat_threshold,
                'cooperation_willingness': self.genome.cooperation_willingness,
                'risk_tolerance': self.genome.risk_tolerance,
                'mutation_rate': self.genome.mutation_rate,
                'mutation_strength': self.genome.mutation_strength,
                'weapon_preferences': self.genome.weapon_preferences
            },
            'role': self.role.value,
            'team_id': self.team_id,
            'state': self.state.value,
            'velocity': {'x': self.velocity.x, 'y': self.velocity.y},
            'facing_direction': {'x': self.facing_direction.x, 'y': self.facing_direction.y},
            'last_attack_time': self.last_attack_time,
            'is_defending': self.is_defending,
            'memory': {
                'battles_fought': self.memory.battles_fought,
                'victories': self.memory.victories,
                'defeats': self.memory.defeats,
                'damage_dealt': self.memory.damage_dealt,
                'damage_taken': self.memory.damage_taken,
                'generation': self.memory.generation,
                'enemy_encounters': self.memory.enemy_encounters,
                'successful_strategies': self.memory.successful_strategies,
                'failed_strategies': self.memory.failed_strategies,
                'fitness_history': self.memory.fitness_history
            },
            'combat_state': {
                'status': self.combat_state.status.value,
                'last_attack_time': self.combat_state.last_attack_time.isoformat() if self.combat_state.last_attack_time else None,
                'last_damage_time': self.combat_state.last_damage_time.isoformat() if self.combat_state.last_damage_time else None,
                'current_target_id': self.combat_state.current_target_id,
                'threat_level': self.combat_state.threat_level,
                'total_damage_dealt': self.combat_state.total_damage_dealt,
                'total_damage_taken': self.combat_state.total_damage_taken,
                'attacks_attempted': self.combat_state.attacks_attempted,
                'attacks_hit': self.combat_state.attacks_hit,
                'dodges_attempted': self.combat_state.dodges_attempted,
                'dodges_successful': self.combat_state.dodges_successful,
                'attack_cooldown_remaining': self.combat_state.attack_cooldown_remaining,
                'special_ability_cooldown': self.combat_state.special_ability_cooldown,
                'stun_remaining': self.combat_state.stun_remaining
            },
            'movement_state': {
                'status': self.movement_state.status.value,
                'target_position': {
                    'x': self.movement_state.target_position.x,
                    'y': self.movement_state.target_position.y
                } if self.movement_state.target_position else None,
                'path': [{'x': p.x, 'y': p.y} for p in self.movement_state.path],
                'current_path_index': self.movement_state.current_path_index,
                'current_velocity': {'x': self.movement_state.current_velocity.x, 'y': self.movement_state.current_velocity.y},
                'total_distance_moved': self.movement_state.total_distance_moved,
                'movement_efficiency': self.movement_state.movement_efficiency,
                'stuck_counter': self.movement_state.stuck_counter,
                'last_position_change': self.movement_state.last_position_change.isoformat() if self.movement_state.last_position_change else None
            },
            'status_effects': {
                effect_name: {
                    'intensity': self.status_effects[effect_name],
                    'remaining_time': self.status_timers.get(effect_name, 0.0)
                }
                for effect_name in self.status_effects.keys()
            },
            'collision_radius': self.collision_radius,
            'collision_events': [
                {
                    'type': event['type'],
                    'timestamp': event['timestamp'],
                    'position': {'x': event['position'].x, 'y': event['position'].y},
                    'normal': {'x': event['normal'].x, 'y': event['normal'].y} if 'normal' in event else None,
                    'other_agent_id': event.get('other_agent').agent_id if 'other_agent' in event else None
                }
                for event in self.collision_events
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseAgent':
        """
        Deserialize agent state from dictionary.
        
        Args:
            data: Dictionary containing agent state data
            
        Returns:
            BaseAgent instance with restored state
            
        Note:
            This creates a partially restored agent. Subclasses should override
            this method to properly restore their specific implementations.
        """
        # Create stats from serialized data
        stats_data = data['stats']
        stats = AgentStats(
            max_health=stats_data['max_health'],
            current_health=stats_data['current_health'],
            speed=stats_data['speed'],
            attack_damage=stats_data['attack_damage'],
            attack_range=stats_data['attack_range'],
            attack_cooldown=stats_data['attack_cooldown'],
            defense=stats_data['defense'],
            vision_range=stats_data['vision_range'],
            dodge_chance=stats_data['dodge_chance'],
            accuracy=stats_data['accuracy']
        )
        
        # Create genome from serialized data
        genome_data = data['genome']
        genome = AgentGenome(
            movement_aggression=genome_data['movement_aggression'],
            movement_cooperation=genome_data['movement_cooperation'],
            positioning_preference=genome_data['positioning_preference'],
            attack_aggression=genome_data['attack_aggression'],
            defense_priority=genome_data['defense_priority'],
            target_selection=genome_data['target_selection'],
            dodge_tendency=genome_data['dodge_tendency'],
            retreat_threshold=genome_data['retreat_threshold'],
            cooperation_willingness=genome_data['cooperation_willingness'],
            risk_tolerance=genome_data['risk_tolerance'],
            mutation_rate=genome_data['mutation_rate'],
            mutation_strength=genome_data['mutation_strength'],
            weapon_preferences=genome_data['weapon_preferences']
        )
        
        # Create memory from serialized data
        memory_data = data['memory']
        memory = AgentMemory()
        memory.battles_fought = memory_data['battles_fought']
        memory.victories = memory_data['victories']
        memory.defeats = memory_data['defeats']
        memory.damage_dealt = memory_data['damage_dealt']
        memory.damage_taken = memory_data['damage_taken']
        memory.generation = memory_data['generation']
        memory.enemy_encounters = memory_data['enemy_encounters']
        memory.successful_strategies = memory_data['successful_strategies']
        memory.failed_strategies = memory_data['failed_strategies']
        memory.fitness_history = memory_data['fitness_history']
        
        # Note: This creates a base agent instance that cannot be directly instantiated
        # Subclasses should override this method to create their specific type
        raise NotImplementedError(
            "BaseAgent.from_dict() must be implemented by concrete subclasses. "
            "Use a specific agent class (e.g., RandomAgent.from_dict()) instead."
        )
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save agent state to JSON file.
        
        Args:
            filepath: Path to save the agent state
        """
        import json
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'BaseAgent':
        """
        Load agent state from JSON file.
        
        Args:
            filepath: Path to the saved agent state file
            
        Returns:
            BaseAgent instance with loaded state
        """
        import json
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    # === Debug Information and Logging Methods ===
    
    def get_debug_info(self, include_detailed: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive debug information about the agent.
        
        Args:
            include_detailed: Include detailed state information
            
        Returns:
            Dictionary containing debug information
        """
        debug_info = {
            'agent_id': self.agent_id,
            'short_id': self.agent_id[:8],
            'role': self.role.value,
            'team_id': self.team_id,
            'state': self.state.value,
            'is_alive': self.is_alive,
            'health': {
                'current': self.stats.current_health,
                'max': self.stats.max_health,
                'percentage': self.health_percentage
            },
            'position': {
                'x': self.position.x,
                'y': self.position.y,
                'facing': {'x': self.facing_direction.x, 'y': self.facing_direction.y}
            },
            'velocity': {
                'x': self.velocity.x,
                'y': self.velocity.y,
                'magnitude': self.velocity.magnitude()
            },
            'combat': {
                'status': self.combat_state.status.value,
                'last_attack_time': self.last_attack_time,
                'attack_cooldown_remaining': self.combat_state.attack_cooldown_remaining,
                'is_defending': self.is_defending,
                'current_target_id': self.combat_state.current_target_id,
                'threat_level': self.combat_state.threat_level
            },
            'movement': {
                'status': self.movement_state.status.value,
                'has_target': self.movement_state.has_target(),
                'total_distance': self.movement_state.total_distance_moved,
                'efficiency': self.movement_state.movement_efficiency,
                'stuck_counter': self.movement_state.stuck_counter
            },
            'status_effects': {
                effect: {
                    'intensity': intensity,
                    'remaining_time': self.status_timers.get(effect, 0.0)
                }
                for effect, intensity in self.status_effects.items()
            },
            'collision': {
                'radius': self.collision_radius,
                'recent_events_count': len(self.collision_events),
                'has_recent_collision': self.has_recent_collision()
            },
            'fitness': self.get_fitness(),
            'memory': {
                'battles_fought': self.memory.battles_fought,
                'victories': self.memory.victories,
                'defeats': self.memory.defeats,
                'win_rate': self.memory.victories / max(1, self.memory.battles_fought),
                'damage_dealt': self.memory.damage_dealt,
                'damage_taken': self.memory.damage_taken,
                'generation': self.memory.generation
            }
        }
        
        if include_detailed:
            debug_info.update({
                'stats': {
                    'speed': self.stats.speed,
                    'attack_damage': self.stats.attack_damage,
                    'attack_range': self.stats.attack_range,
                    'attack_cooldown': self.stats.attack_cooldown,
                    'defense': self.stats.defense,
                    'vision_range': self.stats.vision_range,
                    'dodge_chance': self.stats.dodge_chance,
                    'accuracy': self.stats.accuracy
                },
                'genome': {
                    'movement_aggression': self.genome.movement_aggression,
                    'attack_aggression': self.genome.attack_aggression,
                    'defense_priority': self.genome.defense_priority,
                    'retreat_threshold': self.genome.retreat_threshold,
                    'cooperation_willingness': self.genome.cooperation_willingness,
                    'risk_tolerance': self.genome.risk_tolerance
                },
                'combat_stats': {
                    'attacks_attempted': self.combat_state.attacks_attempted,
                    'attacks_hit': self.combat_state.attacks_hit,
                    'accuracy_rate': self.combat_state.get_accuracy_rate(),
                    'dodges_attempted': self.combat_state.dodges_attempted,
                    'dodges_successful': self.combat_state.dodges_successful,
                    'dodge_rate': self.combat_state.get_dodge_rate(),
                    'total_damage_dealt': self.combat_state.total_damage_dealt,
                    'total_damage_taken': self.combat_state.total_damage_taken
                },
                'movement_target': {
                    'x': self.movement_state.target_position.x,
                    'y': self.movement_state.target_position.y
                } if self.movement_state.target_position else None,
                'recent_collision_events': [
                    {
                        'type': event['type'],
                        'timestamp': event['timestamp'],
                        'position': {'x': event['position'].x, 'y': event['position'].y}
                    }
                    for event in self.collision_events[-5:]  # Last 5 events
                ]
            })
        
        return debug_info
    
    def log_state_summary(self, log_level: str = 'DEBUG') -> None:
        """
        Log a comprehensive summary of the agent's current state.
        
        Args:
            log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        level = getattr(self.logger, log_level.lower())
        
        # Basic state
        level(f"🤖 Agent {self.agent_id[:8]} State Summary:")
        level(f"  📊 Health: {self.stats.current_health:.1f}/{self.stats.max_health} "
              f"({self.health_percentage:.1f}%)")
        level(f"  📍 Position: {self.position} | Facing: {self.facing_direction}")
        level(f"  🏃 Velocity: {self.velocity} (mag: {self.velocity.magnitude():.2f})")
        level(f"  🎯 Role: {self.role.value} | State: {self.state.value}")
        level(f"  👥 Team: {self.team_id or 'None'}")
        
        # Combat state
        if self.combat_state.current_target_id:
            level(f"  ⚔️ Combat: Targeting {self.combat_state.current_target_id[:8]} "
                  f"(threat: {self.combat_state.threat_level:.2f})")
        else:
            level(f"  ⚔️ Combat: No target | Status: {self.combat_state.status.value}")
        
        # Movement state
        if self.movement_state.has_target():
            target = self.movement_state.target_position
            level(f"  🚶 Movement: Target {target} | Status: {self.movement_state.status.value}")
        else:
            level(f"  🚶 Movement: No target | Status: {self.movement_state.status.value}")
        
        # Status effects
        if self.status_effects:
            effects_str = ", ".join([
                f"{effect}({intensity:.1f}, {self.status_timers.get(effect, 0):.1f}s)"
                for effect, intensity in self.status_effects.items()
            ])
            level(f"  ✨ Effects: {effects_str}")
        
        # Performance metrics
        if self.memory.battles_fought > 0:
            win_rate = self.memory.victories / self.memory.battles_fought * 100
            level(f"  🏆 Performance: {win_rate:.1f}% wins ({self.memory.victories}/"
                  f"{self.memory.battles_fought}) | Fitness: {self.get_fitness():.3f}")
    
    def log_decision_making(self, decision_context: Dict[str, Any], 
                          decision_made: str, reasoning: str = "") -> None:
        """
        Log agent decision-making process for debugging.
        
        Args:
            decision_context: Context information used for decision
            decision_made: The decision that was made
            reasoning: Optional reasoning for the decision
        """
        self.logger.debug(f"🧠 Agent {self.agent_id[:8]} Decision:")
        self.logger.debug(f"  📋 Context: {decision_context}")
        self.logger.debug(f"  ✅ Decision: {decision_made}")
        if reasoning:
            self.logger.debug(f"  💭 Reasoning: {reasoning}")
    
    def log_performance_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Log performance metrics for analysis.
        
        Args:
            metrics: Dictionary of metric name to value
        """
        self.logger.info(f"📈 Agent {self.agent_id[:8]} Performance Metrics:")
        for metric_name, value in metrics.items():
            if isinstance(value, float):
                self.logger.info(f"  {metric_name}: {value:.3f}")
            else:
                self.logger.info(f"  {metric_name}: {value}")
    
    def log_collision_event(self, collision_type: str, details: Dict[str, Any]) -> None:
        """
        Log collision events with detailed information.
        
        Args:
            collision_type: Type of collision ('agent', 'boundary', 'obstacle')
            details: Additional collision details
        """
        self.logger.debug(f"💥 Agent {self.agent_id[:8]} Collision:")
        self.logger.debug(f"  🔍 Type: {collision_type}")
        self.logger.debug(f"  📍 Position: {self.position}")
        for key, value in details.items():
            self.logger.debug(f"  {key}: {value}")
    
    def log_status_effect_change(self, effect_name: str, action: str, 
                               intensity: float = 0.0, duration: float = 0.0) -> None:
        """
        Log status effect changes.
        
        Args:
            effect_name: Name of the status effect
            action: Action performed ('applied', 'removed', 'expired')
            intensity: Effect intensity (for applied effects)
            duration: Effect duration (for applied effects)
        """
        if action == "applied":
            self.logger.debug(f"✨ Agent {self.agent_id[:8]} Status Effect Applied:")
            self.logger.debug(f"  🔮 Effect: {effect_name} (intensity: {intensity:.2f})")
            self.logger.debug(f"  ⏱️ Duration: {duration:.1f}s")
        elif action == "removed":
            self.logger.debug(f"🚫 Agent {self.agent_id[:8]} Status Effect Removed: {effect_name}")
        elif action == "expired":
            self.logger.debug(f"⏰ Agent {self.agent_id[:8]} Status Effect Expired: {effect_name}")
    
    def debug_assert(self, condition: bool, message: str) -> None:
        """
        Debug assertion with logging.
        
        Args:
            condition: Condition to check
            message: Message to log if condition fails
        """
        if not condition:
            self.logger.error(f"🚨 Agent {self.agent_id[:8]} Debug Assertion Failed: {message}")
            self.log_state_summary('ERROR')
            raise AssertionError(f"Agent {self.agent_id[:8]}: {message}")
    
    def get_debug_string(self, compact: bool = True) -> str:
        """
        Get a debug string representation of the agent.
        
        Args:
            compact: Whether to use compact format
            
        Returns:
            Debug string representation
        """
        if compact:
            effects = f"+{len(self.status_effects)}" if self.status_effects else ""
            target = f"→{self.combat_state.current_target_id[:8]}" if self.combat_state.current_target_id else ""
            return (f"{self.agent_id[:8]}|{self.role.value[:3]}|"
                   f"HP:{self.stats.current_health:.0f}|"
                   f"@{self.position.x:.0f},{self.position.y:.0f}|"
                   f"{self.state.value[:3]}{effects}{target}")
        else:
            debug_info = self.get_debug_info(include_detailed=False)
            lines = [f"Agent {self.agent_id[:8]} Debug Info:"]
            for key, value in debug_info.items():
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for subkey, subvalue in value.items():
                        lines.append(f"    {subkey}: {subvalue}")
                else:
                    lines.append(f"  {key}: {value}")
            return "\n".join(lines)
    
    def enable_detailed_logging(self, enable: bool = True) -> None:
        """
        Enable or disable detailed logging for this agent.
        
        Args:
            enable: Whether to enable detailed logging
        """
        if enable:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info(f"🔍 Agent {self.agent_id[:8]} detailed logging enabled")
        else:
            self.logger.setLevel(logging.INFO)
            self.logger.info(f"🔇 Agent {self.agent_id[:8]} detailed logging disabled")
    
    def log_startup_info(self) -> None:
        """Log agent startup information."""
        self.logger.info(f"🚀 Agent {self.agent_id[:8]} starting up:")
        self.logger.info(f"  🎭 Role: {self.role.value}")
        self.logger.info(f"  💪 Health: {self.stats.max_health}")
        self.logger.info(f"  🏃 Speed: {self.stats.speed}")
        self.logger.info(f"  ⚔️ Attack: {self.stats.attack_damage}")
        self.logger.info(f"  🛡️ Defense: {self.stats.defense}")
        self.logger.info(f"  👁️ Vision: {self.stats.vision_range}")
        self.logger.info(f"  👥 Team: {self.team_id or 'None'}")
        if self.genome.cooperation_willingness > 0.7:
            self.logger.info(f"  🤝 Highly cooperative agent")
        if self.genome.attack_aggression > 0.7:
            self.logger.info(f"  🔥 Highly aggressive agent")
    
    # === String Representation ===
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return (f"Agent({self.agent_id[:8]}, {self.role.value}, "
                f"HP:{self.stats.current_health:.1f}/{self.stats.max_health}, "
                f"Pos:{self.position}, Team:{self.team_id})")
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return str(self)
