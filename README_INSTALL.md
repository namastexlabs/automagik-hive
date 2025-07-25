# Automagik Hive Installation

## Single Command Install

Run this command to install Automagik Hive and enter the directory:

```bash
bash -c "$(curl -sSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh)" && cd automagik-hive
```

This will:
1. Download and run the installer
2. Clone the repository
3. Install dependencies
4. Ask about Docker setup
5. Leave you in the `automagik-hive` directory

## Alternative: Clone and Install

```bash
git clone https://github.com/namastexlabs/automagik-hive.git && cd automagik-hive && make install
```