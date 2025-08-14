# Prototype fix for KeyboardInterrupt handling in cli/docker_manager.py
# FORGE_TASK_ID: 1161972c-9107-4c83-9aee-a13468eb33f0

"""
KeyboardInterrupt Fix for _interactive_install Method

This is a prototype showing how to properly handle KeyboardInterrupt
exceptions in the _interactive_install method of DockerManager class.

The fix involves wrapping all input() calls in try-catch blocks to
gracefully handle Ctrl+C interruptions.
"""

def fixed_interactive_install_example():
    """
    Example of properly handling KeyboardInterrupt in interactive install.
    
    This demonstrates the pattern that should be applied to all input() calls
    in the _interactive_install method.
    """
    
    def get_user_input(prompt: str, valid_options: list = None, default: str = "") -> str:
        """Helper function to get user input with KeyboardInterrupt handling."""
        while True:
            try:
                user_input = input(prompt).strip().lower()
                if user_input == "" and default:
                    return default
                if valid_options and user_input in valid_options:
                    return user_input
                elif not valid_options:
                    return user_input
                else:
                    print(f"❌ Invalid choice. Please enter one of: {', '.join(valid_options)}")
            except KeyboardInterrupt:
                print("\n👋 Installation cancelled by user")
                return None
    
    print("🚀 Automagik Hive Interactive Installation")
    print("=" * 50)
    
    try:
        # 1. Main Hive installation
        print("\n🏠 Automagik Hive Core (Main Application)")
        print("This includes the workspace server and web interface")
        
        hive_choice = get_user_input(
            "Would you like to install Hive Core? (Y/n): ",
            ["y", "yes", "n", "no", ""],
            "y"
        )
        if hive_choice is None:  # KeyboardInterrupt occurred
            return False
            
        install_hive = hive_choice not in ["n", "no"]
        
        if not install_hive:
            print("👋 Skipping Hive installation")
            return True
        
        # 2. Database setup
        print("\n📦 Database Setup for Hive:")
        print("1. Use our PostgreSQL + pgvector container (recommended)")
        print("2. Use existing PostgreSQL database")
        
        db_choice = get_user_input(
            "\nSelect database option (1-2): ",
            ["1", "2"]
        )
        if db_choice is None:  # KeyboardInterrupt occurred
            return False
        
        if db_choice == "1":
            # Container database setup
            print("✅ Using PostgreSQL + pgvector container")
            
            # Check for existing container and ask for reuse/recreate
            # (simulated check)
            container_exists = True  # This would be actual check
            
            if container_exists:
                print("\n🗄️ Found existing database container")
                db_action = get_user_input(
                    "Do you want to (r)euse existing database or (c)recreate it? (r/c): ",
                    ["r", "reuse", "c", "create", "recreate"]
                )
                if db_action is None:  # KeyboardInterrupt occurred
                    return False
                
                if db_action in ["c", "create", "recreate"]:
                    print("🗑️ Recreating database container...")
                else:
                    print("♻️ Reusing existing database container")
        else:
            # Custom database setup
            print("📝 Custom database setup for Hive")
            print("\nEnter your PostgreSQL connection details:")
            
            # Get credentials with KeyboardInterrupt handling
            try:
                host = input("Host (localhost): ").strip() or "localhost"
                port = input("Port (5432): ").strip() or "5432"  
                database = input("Database name (automagik_hive): ").strip() or "automagik_hive"
                username = input("Username: ").strip()
                password = input("Password: ").strip()
            except KeyboardInterrupt:
                print("\n👋 Installation cancelled by user")
                return False
            
            if not username or not password:
                print("❌ Username and password are required")
                return False
        
        # 3. Additional components
        if install_hive:
            # Genie installation
            print("\n🧞 Genie (AI Agent Assistant)")
            genie_choice = get_user_input(
                "Would you like to install Genie? (y/N): ",
                ["y", "yes", "n", "no", ""],
                "n"
            )
            if genie_choice is None:  # KeyboardInterrupt occurred
                return False
            
            install_genie = genie_choice in ["y", "yes"]
            
            # Agent Workspace installation
            print("\n🤖 Agent Workspace (Optional)")
            print("Separate isolated testing environment for agents")
            agent_choice = get_user_input(
                "Would you like to install Agent Workspace? (y/N): ",
                ["y", "yes", "n", "no", ""],
                "n"
            )
            if agent_choice is None:  # KeyboardInterrupt occurred
                return False
                
            install_agent = agent_choice in ["y", "yes"]
        
        # Proceed with installation based on choices
        print(f"\n✅ Installation configuration complete!")
        print(f"Hive: {install_hive}")
        if install_hive:
            print(f"Genie: {install_genie}")  
            print(f"Agent: {install_agent}")
        
        return True
        
    except KeyboardInterrupt:
        # Catch any KeyboardInterrupt that might escape individual handlers
        print("\n👋 Installation cancelled by user")
        return False


if __name__ == "__main__":
    # Test the fixed implementation
    print("Testing KeyboardInterrupt handling...")
    result = fixed_interactive_install_example()
    print(f"Result: {result}")