# Installation

## Safe install

1. Clone this repository
2. Read `config_aider.py`
3. Make `config_aider.py` executable:

   ```bash
   chmod +x config_aider.py
   ```

4. Create a symlink to make it available as `ca`:

   ```bash
   # might require sudo
   ln -s $(pwd)/config_aider.py /usr/local/bin/ca
   ```

## Baller install

`curl -sSf https://raw.githubusercontent.com/burnettk/config-aider/main/install.sh | bash`
