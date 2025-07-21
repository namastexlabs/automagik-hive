#!/usr/bin/env python3

from agno.agent import Agent
import inspect

sig = inspect.signature(Agent.__init__)
print('Agent.__init__ parameters:')
for name, param in sig.parameters.items():
    if name != 'self':
        print(f'  {name}: {param.annotation}')

print('\nParameters with defaults:')
for name, param in sig.parameters.items():
    if name != 'self' and param.default != param.empty:
        print(f'  {name} = {param.default}')

# Check specifically for context-related parameters
context_params = [name for name in sig.parameters.keys() if 'context' in name.lower()]
print(f'\nContext-related parameters: {context_params}')