#!/usr/bin/env python3
"""
Test script to verify CLI functionality
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_system_initialization():
    """Test that the system can be initialized"""
    try:
        from src.workflows.research_workflow import HierarchicalResearchSystem
        
        print("Testing HierarchicalResearchSystem initialization...")
        
        # Test non-CLI mode
        system = HierarchicalResearchSystem(cli_mode=False)
        print("✅ Non-CLI mode initialization: SUCCESS")
        
        # Test CLI mode initialization
        system = HierarchicalResearchSystem(cli_mode=True)
        print("✅ CLI mode initialization: SUCCESS")
        
        # Test that CLI controller exists
        if hasattr(system, 'cli_controller'):
            print("✅ CLI controller exists: SUCCESS")
        else:
            print("❌ CLI controller missing: FAILED")
        
        # Test model configuration
        if hasattr(system, 'model_config'):
            print("✅ Model config exists: SUCCESS")
            print(f"   Privacy mode: {system.model_config.privacy_mode}")
            print(f"   CLI mode: {system.model_config.cli_mode}")
        else:
            print("❌ Model config missing: FAILED")
        
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_imports():
    """Test that all required modules can be imported"""
    modules_to_test = [
        'src.config.models',
        'src.config.costs', 
        'src.cli.conversation_controller',
        'src.cli.state_manager',
        'src.cli.question_generator',
        'src.cli.response_parser',
        'src.tools.source_manager',
        'src.utils.session_manager',
        'src.utils.memory_management',
        'src.workflows.research_workflow'
    ]
    
    print("Testing module imports...")
    all_success = True
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: SUCCESS")
        except Exception as e:
            print(f"❌ {module}: FAILED - {e}")
            all_success = False
    
    return all_success

async def test_structlog():
    """Test structlog functionality"""
    try:
        import structlog
        logger = structlog.get_logger()
        logger.info("Testing structlog functionality")
        print("✅ structlog: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ structlog: FAILED - {e}")
        return False

async def main():
    """Run all tests"""
    print("="*60)
    print("HierarchicalResearchAI System Tests")
    print("="*60)
    
    test_results = []
    
    # Test imports
    imports_ok = await test_imports()
    test_results.append(("Module Imports", imports_ok))
    
    # Test structlog
    structlog_ok = await test_structlog()
    test_results.append(("Structlog", structlog_ok))
    
    # Test system initialization
    init_ok = await test_system_initialization()
    test_results.append(("System Initialization", init_ok))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    print("="*60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\nTo use the CLI interactively, run:")
        print("python -m src.cli.interface research")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())