from pathlib import Path

# Workspace name: only used for naming cloud resources
WS_NAME = "pagbank-multiagents"

# Path to the workspace root
WS_ROOT = Path(__file__).parent.parent.resolve()

# Environment names
DEV_ENV = "dev"
PRD_ENV = "prd"

# Dev key is used for naming development resources
DEV_KEY = f"{WS_NAME}-{DEV_ENV}"
# Production key is used for naming production resources
PRD_KEY = f"{WS_NAME}-{PRD_ENV}"

# AWS settings
# Region for AWS resources (Brazilian region preferred for PagBank)
AWS_REGION = "sa-east-1"
# AWS profile for PagBank account
AWS_PROFILE = "pagbank"

# Availability Zones for AWS resources
AWS_AZ1 = "sa-east-1a"
AWS_AZ2 = "sa-east-1c"

# Subnet IDs in the aws_region (to be configured)
SUBNET_IDS = []

# Image Settings
# Repository for images
IMAGE_REPO = "pagbank"

# Build images locally
BUILD_IMAGES = True