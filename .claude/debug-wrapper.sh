#\!/bin/bash
# Debug wrapper to capture what TDD Guard is doing
echo "TDD Guard Debug Log - $(date)" >> /tmp/tdd-debug.log
echo "Environment vars:" >> /tmp/tdd-debug.log
env | grep -E "(CLAUDE|TDD|MODEL|USE_SYSTEM)" >> /tmp/tdd-debug.log
echo "Command args: $@" >> /tmp/tdd-debug.log
echo "Input:" >> /tmp/tdd-debug.log
tee -a /tmp/tdd-debug.log | tdd-guard
echo "---" >> /tmp/tdd-debug.log
