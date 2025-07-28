#!/bin/bash
# TDD Guard wrapper script with Anthropic API configuration
export MODEL_TYPE=anthropic_api
export TDD_GUARD_ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
exec tdd-guard "$@"
