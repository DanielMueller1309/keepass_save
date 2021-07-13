# keepass_save
This reposetory used to develope my keepass_save module for ansible

## Installation

* This Ansible module needs the PyKeePass Module for Python.
  - On Fedora, install it using `dnf install python-pykeepass` for example.
  - On Debian and Ubuntu using `pip install pykeepass` if pip isn´t installed use the suggestet cmd
* Clone the keepass_save Module for Ansible into one of those directories
  - `~/.ansible/plugins/modules/`
  - `/usr/share/ansible/plugins/modules/`


## Create a KeePass Database

Create a new, empty `.kdbx` file using KeePass, [KeeWeb](https://keeweb.info/) or similar. You can either use just a password, or both a password and keyfile.

In this example, we use `/tmp/vault.kdbx` with 'password' as the password and `/tmp/vault.key` as the keyfile. In real life, don't use the `/tmp` directory for this of course. ;-)


## How to use the Module in a Playbook

The next step in using the keepass_save Module for Ansible is to consume it with an Ansible playbook or Role.

* Create a playbook  or a main.yml task in roles/<rolenake>/tasks/main.yml
* Add the following to the new playbook/role task file:

Playbook:
```yaml
- name: Test the KeePass Module
  hosts: localhost
  tasks:
  - name: Add entry or change existung one
    keepass:
      database: /tmp/vault.kdbx
      keyfile: /tmp/vault.key
      title: storage_admin
      username: admin-user
      entry_password: hallowelt
      notes: 'That´s themse to be the the incredibly place, the space for notes '
      icon: 30
      url: 'https://pornhub.com'    
```

role task:
```yaml
- name: Add entry or change existung one
  keepass:
    database: /tmp/vault.kdbx
    keyfile: /tmp/vault.key
    title: storage_admin
    username: admin-user
    entry_password: hallowelt
    notes: 'That´s themse to be the the incredibly place, the space for notes '
    icon: 30
    url: 'https://pornhub.com'    
```


## Full Documentation

You can see the full documentation of the available parameters using

```bash
ansible-doc keepass
```

