# Minimal Factory Pattern

## 🎯 **Why Minimal Factories?**

Instead of empty `agent.py` files, use **minimal factory functions**:
- ✅ Always return a configured agent
- ✅ Leverage version_factory abstraction 
- ✅ Only add custom logic when actually needed
- ✅ Keep agent.py files clean and focused

## 🏭 **Minimal Pattern**

```python
# ai/agents/{agent_name}/agent.py
from lib.utils.version_factory import create_agent

def get_{agent_name}_agent(**kwargs):
    """Agent factory - add custom logic here if needed"""
    
    # Custom logic only when needed:
    # if kwargs.get("user_context", {}).get("subscription") == "pro":
    #     kwargs["model_override"] = "claude-opus-3-20240229"
    
    return create_agent("{agent_name}", **kwargs)
```

## 🛠️ **Custom Logic Examples**

### **Subscription-Based Models**
```python
if kwargs.get("user_context", {}).get("subscription") == "pro":
    kwargs["model_override"] = "claude-opus-3-20240229"
```

### **Risk-Based Adjustments**  
```python
if kwargs.get("transaction_amount", 0) > 50000:
    kwargs["temperature_override"] = 0.01
    kwargs["instructions_append"] = "\nATENÇÃO: Alto valor"
```

### **Geographic Compliance**
```python
user_state = kwargs.get("user_context", {}).get("state")
if user_state == "SP":
    kwargs["instructions_append"] = "\nAplique regras ICMS-SP"
```

### **Time-Based Behavior**
```python
from datetime import datetime
current_hour = datetime.now().hour
if 18 <= current_hour or current_hour <= 6:
    kwargs["temperature_override"] = 0.3
```

## 📝 **Implementation**

### **1. Create Factory Function**
```python
# ai/agents/new_agent/agent.py
from lib.utils.version_factory import create_agent

def get_new_agent(**kwargs):
    # Add custom logic here if needed
    return create_agent("new_agent", **kwargs)
```

### **2. Use Template**
- Copy `ai/agents/template/` for examples
- Uncomment only the custom logic you need
- Keep it minimal

## 🎯 **Key Benefits**

- **Minimal Code**: Only custom logic in agent.py
- **Maximum Abstraction**: Leverage version_factory  
- **Clean Separation**: YAML for config, Python only for custom logic
- **Easy Maintenance**: Less code = fewer bugs

## 📋 **Template Available**

- **`ai/agents/template/agent.py`** - Commented examples
- **`ai/agents/adquirencia/agent.py`** - Clean implementation
- Start with template, remove what you don't need!