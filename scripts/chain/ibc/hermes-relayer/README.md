# Hermes relayer setup for umee app 

## Deps 
 1. Install hermes 1.1.0 
```bash
$ cargo install ibc-relayer-cli@1.1.0 --bin hermes --locked 
 ```

## Init the two chains 
```bash
$ bash ./noob/hermes-relayer/init_chains.sh ./build/umeed
```

## Start the chains 
```bash
$ bash noob/hermes-relayer/start_chains.sh  ./build/umeed
```

## Setup hermes relayer and create connections 
```bash
$ bash noob/hermes-relayer/hermes/restore_keys.sh

$ bash noob/hermes-relayer/hermes/create_conn.sh 
```
## 

## Start the hermes relayer
```bash
$ bash noob/hermes-relayer/hermes/start_relayer.sh 
```