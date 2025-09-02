"""
Logging System Example and Test
Demonstrates the comprehensive logging system for Battle AI.
"""

import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils import get_logger, initialize_logging, Config, config_manager
from src.utils.logging_config import log_function_entry, log_performance


# Initialize logging system
logger = get_logger(__name__)


@log_function_entry
@log_performance
def demonstrate_vector_operations():
    """Demonstrate logging with vector operations."""
    from src.utils import Vector2D
    
    logger.info("🧮 Starting vector operations demonstration")
    
    # Create vectors with logging
    logger.debug("Creating test vectors")
    v1 = Vector2D(3, 4)
    v2 = Vector2D(1, 2)
    
    logger.info(f"Created vectors: v1={v1}, v2={v2}")
    
    # Perform operations
    operations = [
        ("Addition", v1 + v2),
        ("Subtraction", v1 - v2),
        ("Multiplication", v1 * 2),
        ("Magnitude", v1.magnitude()),
        ("Distance", v1.distance_to(v2))
    ]
    
    for op_name, result in operations:
        logger.info(f"  {op_name}: {result}")
    
    logger.info("✅ Vector operations completed")
    return operations


@log_function_entry
def demonstrate_configuration_logging():
    """Demonstrate logging with configuration system."""
    logger.info("⚙️ Loading and displaying configuration")
    
    try:
        config = config_manager.get_config()
        
        # Log configuration details
        logger.info("Configuration loaded successfully:")
        logger.info(f"  🎮 Max agents: {config.simulation.max_agents}")
        logger.info(f"  🗺️ Battlefield: {config.simulation.battlefield_width}x{config.simulation.battlefield_height}")
        logger.info(f"  ⏱️ Time step: {config.simulation.time_step}s")
        logger.info(f"  📊 FPS: {config.simulation.fps}")
        logger.info(f"  💪 Agent health: {config.agents.default_health}")
        logger.info(f"  🏃 Agent speed: {config.agents.default_speed}")
        
        # Log logging configuration
        logger.info("📝 Logging configuration:")
        logger.info(f"  Level: {config.logging.level}")
        logger.info(f"  Console: {config.logging.console}")
        logger.info(f"  Directory: {config.logging.directory}")
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        raise


def demonstrate_different_log_levels():
    """Demonstrate different logging levels."""
    logger.info("📋 Demonstrating different log levels:")
    
    logger.debug("🔍 This is a DEBUG message - detailed development info")
    logger.info("ℹ️ This is an INFO message - general information")
    logger.warning("⚠️ This is a WARNING message - something to watch out for")
    logger.error("❌ This is an ERROR message - something went wrong")
    logger.critical("🚨 This is a CRITICAL message - system failure!")
    
    logger.info("📋 Log level demonstration completed")


def simulate_agent_activity():
    """Simulate some agent activity with logging."""
    logger.info("🤖 Simulating agent activity")
    
    # Simulate agent creation
    for i in range(3):
        logger.info(f"  🔵 Creating agent {i}")
        logger.debug(f"    Agent {i} position: (100, {i * 50})")
        logger.debug(f"    Agent {i} health: 100")
        time.sleep(0.1)  # Small delay to show timing
    
    # Simulate some events
    events = [
        ("Agent 0 attacked Agent 1", "warning"),
        ("Agent 1 health reduced to 75", "info"),
        ("Agent 2 moved to new position", "debug"),
        ("Battle round completed", "info")
    ]
    
    for event, level in events:
        if level == "debug":
            logger.debug(f"    🔍 {event}")
        elif level == "info":
            logger.info(f"    ℹ️ {event}")
        elif level == "warning":
            logger.warning(f"    ⚠️ {event}")
        time.sleep(0.1)
    
    logger.info("🤖 Agent activity simulation completed")


def demonstrate_error_handling():
    """Demonstrate error logging."""
    logger.info("🚨 Demonstrating error handling and logging")
    
    try:
        # Simulate an error condition
        logger.debug("Attempting risky operation...")
        
        # This will cause a division by zero
        result = 1 / 0
        
    except ZeroDivisionError as e:
        logger.error(f"❌ Caught expected error: {e}")
        logger.error("📍 Error occurred in demonstrate_error_handling()")
        logger.info("🔧 Error handled gracefully")
    
    except Exception as e:
        logger.critical(f"🚨 Unexpected error: {e}")
        raise


def main():
    """Main demonstration function."""
    print("🚀 Battle AI Logging System Demonstration")
    print("=" * 60)
    
    # Initialize logging
    logger.info("🎬 Starting logging demonstration")
    logger.info("=" * 50)
    
    try:
        # Demonstrate various features
        demonstrate_different_log_levels()
        print()
        
        vector_ops = demonstrate_vector_operations()
        print()
        
        config = demonstrate_configuration_logging()
        print()
        
        simulate_agent_activity()
        print()
        
        demonstrate_error_handling()
        print()
        
        logger.info("✅ All demonstrations completed successfully!")
        logger.info("🗂️ Check the logs/ directory for detailed log files:")
        logger.info("  📄 battle_ai_*.log - Main log with all messages")
        logger.info("  🚨 battle_ai_errors.log - Error messages only")
        logger.info("  🔍 battle_ai_debug.log - Debug messages")
        
        return {
            'vector_ops': vector_ops,
            'config': config,
            'status': 'success'
        }
        
    except Exception as e:
        logger.critical(f"🚨 Demonstration failed: {e}")
        return {'status': 'failed', 'error': str(e)}


if __name__ == "__main__":
    # Initialize logging system
    initialize_logging()
    
    # Run demonstration
    result = main()
    
    print("\n🏁 Logging demonstration complete!")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print("Check the 'logs/' directory to see the generated log files.")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
