# ARTEMiS Configuration
## Server
- `listen_address`: IP Address or hostname that the server will listen for connections on. Set to 127.0.0.1 for local only, or 0.0.0.0 for all interfaces. Default `127.0.0.1`
- `hostname`: Hostname that gets sent to clients to tell them where to connect. Games must be able to connect to your server via the hostname or IP you spcify here. Note that most games will reject `localhost` or `127.0.0.1`. Default `localhost`
- `port`: Port that the server will listen for connections on. Default `80`
- `ssl_key`: Location of the ssl server key for the secure title server. Ignored if you don't use SSL. Default `cert/title.key`
- `ssl_cert`: Location of the ssl server certificate for the secure title server. Must not be a self-signed SSL. Ignored if you don't use SSL. Default `cert/title.pem`
- `allow_user_registration`: Allows users to register in-game via the AimeDB `register` function. Disable to be able to control who can use cards on your server. Default `True`
- `allow_unregistered_serials`: Allows games that do not have registered keychips to connect and authenticate. Disable to restrict who can connect to your server. Recomended to disable for production setups. Default `True`
- `name`: Name for the server, used by some games in their default MOTDs. Default `ARTEMiS`
- `is_develop`: Flags that the server is a development instance, and enables some useful development features. Disable for production setups. Default `True`.
- `is_using_proxy`: Flags that you'll be using some other software, such as nginx, to proxy requests, and to send `proxy_port` or `proxy_port_ssl` to games instead of `port`. Default `False`
- `proxy_port`: Which port your front-facing proxy will be listening on. Ignored if `is_using_proxy` is `False` or if set to `0`. Default `0`
- `proxy_port`: Which port your front-facing proxy will be listening for ssl connections on. Ignored if `is_using_proxy` is `False` or if set to `0`. Default `0`
- `log_dir`: Directory to store logs. Server MUST have read and write permissions to this directory or you will have issues. Default `logs`
- `check_arcade_ip`: Checks IPs against the `arcade` table in the database, if one is defined. Default `False`
- `strict_ip_checking`: Rejects clients if there is no IP in the `arcade` table for the respective arcade. Default `False`
## Title
- `loglevel`: Logging level for the title server. Default `info`
- `reboot_start_time`: 24 hour JST time that clients will see as the start of maintenance period, ex `04:00`. A few games or early version will report errors if it is empty, ex maimai DX 1.00
- `reboot_end_time`: 24 hour JST time that clients will see as the end of maintenance period, ex `07:00`. this must be set to 7:00 am for some game, please do not change it.
## Database
- `host`: Host of the database. Default `localhost`
- `username`: Username of the account the server should connect to the database with. Default `aime`
- `password`: Password of the account the server should connect to the database with. Default `aime`
- `name`: Name of the database the server should expect. Default `aime`
- `port`: Port the database server is listening on. Default `3306`
- `protocol`: Protocol used in the connection string, e.i `mysql` would result in `mysql://...`. Default `mysql`
- `ssl_enabled`: Enforce SSL to be used in the connection string. Default `False`
- `sha2_password`: Whether or not the password in the connection string should be hashed via SHA2. Default `False`
- `loglevel`: Logging level for the database. Default `info`
- `memcached_host`: Host of the memcached server. Default `localhost`
## Frontend
- `enable`: Whether or not the frontend servlet should run. Frontend can still be run via `python -m uvicorn core.frontend:app` even if this is set to `False`. Default `False`
- `port`: Port the frontend should listen on. Default `8080`
- `loglevel`: Logging level for the frontend server. Default `info`
- `secret`: Base64-encoded JWT secret for session cookies, generated by you. Default `""`
## Allnet
- `standalone`: Whether allnet should launch it's own servlet on it's own port, or be part of the main servlet on the default port. Disable if you either have something proxying `naominet.jp` requests to port 80, or have port 80 set in `server` -> `port`
- `port`: Port the allnet server should listen for connections on if it's running standalone. Games are hardcoded to ask for port `80` so only change if you have a proxy redirecting properly. Ignored if `standalone` is `False`. Default `80`
- `loglevel`: Logging level for the allnet server. Default `info`
- `allow_online_updates`: Allow allnet to distribute online updates via DownloadOrders. This system is currently non-functional, so leave it disabled. Default `False`
- `update_cfg_folder`: Folder where delivery INI files will be checked for. Ignored if `allow_online_updates` is `False`. Default `""`
## Billing
- `standalone`: Whether the billing server should launch it's own servlet on it's own port, or be part of the main servlet on the default port. Setting this to `True` requires that you have `ssl_key` and `ssl_cert` set. Default `False`
- `loglevel`: Logging level for the billing server. Default `info`
- `port`: Port the billing server should listen for connections on. Games are hardcoded to ask for port `8443` so only change if you have a proxy redirecting properly. Ignored if `standalone` is `False`. Default `8443`
- `ssl_key`: Location of the ssl server key for the billing server. Ignored if `standalone` is `False`. Default `cert/server.key`
- `ssl_cert`: Location of the ssl server certificate for the billing server. Ignored if `standalone` is `False`.  Must match the CA distributed to users or the billing server will not connect. Default `cert/server.pem`
- `signing_key`: Location of the RSA Private key used to sign billing requests. Must match the public key distributed to users or the billing server will not connect. Default `cert/billing.key`
## Aimedb
- `enable`: Whether or not aimedb should run. Default `True`
- `listen_address`: IP Address or hostname that the aimedb server will listen for connections on. Leave this blank to use the listen address under `server`. Default `""`
- `loglevel`: Logging level for the aimedb server. Default `info`
- `port`: Port the aimedb server should listen for connections on. Games are hardcoded to ask for port `22345` so only change if you have a proxy redirecting properly. Default `22345`
- `key`: Key to encrypt/decrypt aimedb requests and responses. MUST be set or the server will not start. If set incorrectly, your server will not properly handle aimedb requests. Default `""`
- `id_secret`: Base64-encoded JWT secret for Sega Auth IDs. Leaving this blank disables this feature. Default `""`
- `id_lifetime_seconds`: Number of secons a JWT generated should be valid for. Default `86400` (1 day)
