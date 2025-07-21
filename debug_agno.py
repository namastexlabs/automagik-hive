#!/usr/bin/env python3

from agno.agent import Agent
import inspect
from lib.logging import logger

sig = inspect.signature(Agent.__init__)
logger.info('🤖 Agent.__init__ parameters:')
for name, param in sig.parameters.items():
    if name != 'self':
        logger.info(f'🔧   {name}: {param.annotation}')

logger.info('🔧 Parameters with defaults:')
for name, param in sig.parameters.items():
    if name != 'self' and param.default != param.empty:
        logger.info(f'🔧   {name} = {param.default}')

# Check specifically for context-related parameters
context_params = [name for name in sig.parameters.keys() if 'context' in name.lower()]
logger.info(f'🔧 Context-related parameters: {context_params}')