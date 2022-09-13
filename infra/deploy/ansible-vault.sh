#!/bin/bash
docker pull bedasoftware/ansible-vault
docker run -e HOST_USER_ID=$HOST_USER_ID -e ANSIBLE_VAULT_PASSWORD=$ANSIBLE_VAULT_PASSWORD -v `pwd`:/data --rm bedasoftware/ansible-vault $@
