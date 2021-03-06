#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author:  DanielMueller1309

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: keepass

short_description: This a module to interact with a keepass (kdbx) database.

version_added: "1.0"

description:
    - This a module to interact with a keepass (kdbx) database. To save informatin into a kdbx file (exept  and icon, comming soon)
    - If you remove parameter thats are specified in the kdbx file they will be unchanged and you get back a changed:"false", if
      everything who has to change is the same like in your task.
      So you can overwrite specific parameters in an entry without change the others.


requirements:
    - PyKeePass

options:
    database:
        description:
            - Path of the keepass database.
        required: true
        type: str
        defaults: not set

    keyfile:
        description:
            - Path of the keepass keyfile. Either this or 'password' (or both) are required.
        required: false
        type: str
        defaults: not set

    title:
        description:
            - title, will be used for the title of the entry.
            - if not set no entry will be add or modify
        required: false
        type: str
        defaults: not set

    username:
        description:
            - Username of the entry.
        required: false
        type: str
        defaults: not set

    entry_password:
        description:
            - password of the entry.
        required: false
        type: str
        defaults: not set

    db_password:
        description:
            - database password. Either this or 'keyfile' (or both) are required.
        required: false
        type: str
        defaults: not set

    notes:
        description:
            - this param is the most important one (sacasm) it gives us the the space for notes
        required: false
        type: str
        defaults:
            - 'This Entry is Ansible Managed'

    icon:
        description:
            - to specifi something for the eys to see with the default icon which entry is ansible manged
        defaults:
            - '47'
        required: false
        type: str

    url:
        description:
        - to fill the url field in kdbx file
        required: false
        type: str
        defaults: not set

    state:
        description:
        - used to specify if a database have to 'create' or 'modify'
        required: true
        type: str
        default: not set

author:
    - DanielMueller1309 https://github.com/DanielMueller1309
'''

EXAMPLES = r'''
- name: Add entry or change existing one in the database
  keepass:
    database: /home/user/vault.kdbx
    keyfile: /home/user/vault.key
    title: storage_admin
    username: admin-user
    entry_password: hallowelt
    notes: 'That??s themse to be the the incredibly place, the space for notes '
    icon: 30
    url: 'https://pornhub.com'
    state: modify

- name: create new database with keyfile and db_password
  keepass:
    database: /home/user/vault.kdbx
    db_password: 'hallowelt'
    keyfile : /home/user/vault.key
    state: create

- name: create new database without any keyfile and db_password
  keepass:
    database: /home/user/vault.kdbx
    state: create

- name: create new database with his first entry
  keepass:
    database: /home/user/vault.kdbx
    db_password: 'hallowelt'
    username: admin-user
    entry_password: hallowelt
    notes: 'That??s themse to be the the incredibly place, the space for notes '
    icon: 30
    url: 'https://pornhub.com'
    state: create
'''
RETURN = r'''
new_username:
    description: the new username who is set by an existing entry
    type: str
add_username:
    description: the added username who is set by a new entry
    type: str

P.S: this return statements are also available by every entry parameter who is changed or created except 'new_database'
'''
import traceback

from ansible.module_utils.basic import AnsibleModule,missing_required_lib

PYKEEPASS_IMP_ERR = None
try:
    from pykeepass import PyKeePass, create_database
    import pykeepass.exceptions
    import pykeepass
except ImportError:
    PYKEEPASS_IMP_ERR = traceback.format_exc()
    pykeepass_found = False
else:
    pykeepass_found = True

import subprocess
import argparse

import string
import random

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        database=dict(type='str', required=True),
        keyfile=dict(type='str', required=False, default=None),
        db_password=dict(type='str', required=False, default=None, no_log=True),
        title=dict(type='str', required=False),
        groupname=dict(type='str', required=False, default=None),
        username=dict(type='str', required=False),
        entry_password=dict(type='str', required=False, default=None, no_log=True),
        notes=dict(type='str', required=False, default='This Entry is Ansible Managed'),
        #expiry_time=dict(type='str', required=False, default=None),
        #tags=dict(type='str', required=False, default=None),
        icon=dict(type='int', required=False, default=47),
        url=dict(type='str', required=False, default=None),
        state=dict(type='str', required=True, default=None),

    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not pykeepass_found:
        module.fail_json(msg=missing_required_lib("pykeepass"), exception=PYKEEPASS_IMP_ERR)

    database        = module.params['database']
    keyfile         = module.params['keyfile']
    db_password     = module.params['db_password']
    title           = module.params['title']
    groupname       = module.params['groupname']
    username        = module.params['username']
    entry_password  = module.params['entry_password']
    notes           = module.params['notes']
    #expiry_time     = module.params['expiry_time']
    #tags            = module.params['tags']
    icon            = module.params['icon']
    url             = module.params['url']
    state           = module.params['state']



    #if state is not 'create' and state is not 'modify':
    #    module.fail_json(msg="Could not know what you want as 'state'. Valid states are: 'create','modify'")

    if not db_password and not keyfile:
        KEEPASS_OPEN_ERR = traceback.format_exc()
        module.fail_json(msg="Either 'password' or 'keyfile' (or both) are required. (its for safety)")

    if state == 'create':
        if keyfile is not None:
            try:
                f = open(keyfile)
                f.close()
            except:
                try:
                    create_keyfile(keyfile)
                except:
                    KEEPASS_OPEN_ERR = traceback.format_exc()
                    module.fail_json(msg="Could not create Key File. Please verify that the path is set correct (do not use /tmp path).")
        try:
            f = open(database)
            f.close()

           #kp = PyKeePass(database, password=db_password, keyfile=keyfile)
            if db_password and keyfile is not None:
                try:
                    kp = PyKeePass(database, password=db_password, keyfile=keyfile)
                except:
                    KEEPASS_OPEN_ERR = traceback.format_exc()
                    module.fail_json(
                        msg="cant find keyfile or password")
            if db_password is not None and keyfile is None:
                try:
                    kp = PyKeePass(database, password=db_password)
                except:
                    KEEPASS_OPEN_ERR = traceback.format_exc()
                    module.fail_json(
                        msg="cant find password")
            if db_password is None and keyfile is not None:
                try:
                    kp = PyKeePass(database, keyfile=keyfile)
                except:
                    KEEPASS_OPEN_ERR = traceback.format_exc()
                    module.fail_json(
                        msg="cant find keyfile")
            result['changed'] = False
            result['database'] = database
            result['password'] = db_password
            result['keyfile'] = keyfile
        except:
            try:

                kp = pykeepass.create_database(database, password=db_password, keyfile=keyfile)
                result['changed'] = True
                result['new_database'] = database
                result['new_db_password'] = db_password
                result['keyfile'] = keyfile

            except:
                KEEPASS_OPEN_ERR = traceback.format_exc()
                module.fail_json(msg="Could not create Database File. Please verify that the path is set correctly and set 'db_password'")

    if state == 'modify':
        try:
            kp = PyKeePass(database, password=db_password, keyfile=keyfile)
        except IOError as e:
            KEEPASS_OPEN_ERR = traceback.format_exc()
            module.fail_json(msg='Could not open the database or keyfile.')
        except FileNotFoundError:
            KEEPASS_OPEN_ERR = traceback.format_exc()
            module.fail_json(msg='Could not open the database. Credentials are wrong or integrity check failed')


    # try to get the entry from the database
    if title is not None:
        if groupname is not None:
            create_group(module, kp, groupname)
        db_entry = get_entry(module, kp, title, groupname)
        #user_entry = (title, username, entry_password, url, notes, expiry_time, tags, icon)
        #parameter = ('entry.title', 'entry.username','entry.password', 'entry.url', 'entry.notes', 'entry.expiry_time', 'entry.tags', 'entry.icon')
        #parameter_name = ('title', 'username', 'password', 'url', 'notes', 'expiry_time', 'tags', 'icon')
        if db_entry:
            if db_entry[0] == title:
                #x = range(1, len(db_entry), 1)
                #for i in x:
                #    if user_entry[i] != db_entry[i]:
                #        set_param(parameter[i],parameter_name, module, kp, title, username,entry_password, url, notes, expiry_time, tags, icon)
                db_entry_title, db_entry_username, db_entry_password, db_entry_url, db_entry_notes, db_entry_expiry_time, db_entry_tags, db_entry_icon = db_entry
                #result['changed'] = False
                if username != db_entry_username and username is not None:
                    set_username(module, kp, title, username)
                    result['new_username'] = get_username(module, kp, title)
                    result['changed'] = True

                if entry_password != db_entry_password and entry_password is not None:
                    set_entry_password(module, kp, title, entry_password)
                    result['entry_password'] = get_password(module, kp, title)
                    result['changed'] = True

                if notes != db_entry_notes and notes is not None:
                    set_notes(module, kp, title, notes)
                    result['new_notes'] = get_notes(module, kp, title)
                    result['changed'] = True

                if url != db_entry_url and url is not None:
                    set_url(module, kp, title, url)
                    result['new_url'] = get_url(module, kp, title)
                    result['changed'] = True

                #if expiry_time is not db_entry_expiry_time and str(module_args['icon'].get('default')):
                #    set_expiry_time(module, kp, title, expiry_time)
                #    result['expiry_time'] = expiry_time
                #    result['changed'] = True

                #if str(tags) != str(db_entry_tags):
                #    set_tags(module, kp, title, tags)
                #    result['new_tags'] = tags
                #    result['changed'] = True

                if str(icon) != str(db_entry_icon):
                    set_icon(module, kp, title, icon)
                    result['new_icon'] = str(get_icon(module, kp, title))
                    result['changed'] = True

                database        = module.params['database']
                keyfile         = module.params['keyfile']
                db_password     = module.params['db_password']
                title           = module.params['title']
                groupname       = module.params['groupname']
                username        = module.params['username']
                entry_password  = module.params['entry_password']
                notes           = module.params['notes']
                #expiry_time     = module.params['expiry_time']
                #tags            = module.params['tags']
                icon            = module.params['icon']
                url             = module.params['url']
                state           = module.params['state']
                module.exit_json(**result)

        # if there is no matching entry, create a new one
        #password = entry_password
        if not module.check_mode:
            try:
                create_group(module, kp, groupname)
                groupname = kp.find_groups(name=groupname, first=True)
                create_entry(module, kp, username, title, entry_password, notes, icon, url, groupname)
            except:
                KEEPASS_SAVE_ERR = traceback.format_exc()
                module.fail_json(msg='Could not add the entry or save the database.', exception=KEEPASS_SAVE_ERR)
            result['add_database']          = database
            result['add_title']             = title
            result['add_username']          = username
            result['add_entry_password']    = entry_password
            result['add_notes']             = notes
            result['add_icon']              = icon
            result['add_url']               = url
            result['changed']               = True
    module.exit_json(**result)

def main():
    run_module()
def create_keyfile(keyfile):
    file = open(keyfile, 'w')
    keyfile_text = r'''<?xml version="2.0" encoding="utf-8"?>
<KeyFile>
    <Meta>
        <Version>2.00</Version>
    </Meta>
    <Key>
        <Data>key_string</Data>
    </Key>
</KeyFile>
    '''

    keyfile_text = keyfile_text.replace("key_string", random_string(64))
    file.write(keyfile_text)
    file.close()


def random_string(length):
    pool = string.ascii_letters + string.digits
    return ''.join(random.choice(pool) for i in range(length))

def create_entry(module, kp, username, title, entry_password, notes, icon, url, groupname):

    if username is None:
        username = ''
    if entry_password is None:
        entry_password = ''
    if notes is None:
        notes = ''
    if url is None:
        url = ''

    if groupname is not None:

        kp.add_entry(groupname, title, username, entry_password, icon=str(icon), notes=notes, url=url)
    else:
        kp.add_entry(kp.root_group, title, username, entry_password, icon=str(icon), notes=notes, url=url)
    kp.save()

def create_group(module, kp, groupname):
    if not kp.find_groups(name=groupname, first=True):
        kp.add_group(kp.root_group, groupname)
        kp.save()
#set specific stuff (here to change later is the groupname to a new module param)
def set_username(module, kp, title, username):
    entry = kp.find_entries(title=title, first=True)
    entry.username = username
    kp.save()

def set_entry_password(module, kp, title, entry_password):
    entry = kp.find_entries(title=title, first=True)
    entry.password = entry_password
    kp.save()

def set_url(module, kp, title, url):
    entry = kp.find_entries(title=title, first=True)
    entry.url = url
    kp.save()

def set_notes(module, kp, title, notes):
    entry = kp.find_entries(title=title, first=True)
    entry.notes = notes
    kp.save()

def set_expiry_time(module, kp, title, expiry_time):
    entry = kp.find_entries(title=title, first=True)
    entry.expiry_time = expiry_time
    kp.save()

def set_tags(module, kp, title, tags):
    entry = kp.find_entries(title=title, first=True)
    entry.tags = tags
    kp.save()

def set_icon(module, kp, title, icon):
    entry = kp.find_entries(title=title, first=True)
    entry.icon = str(icon)
    kp.save()

def set_param(param, parameter_name, module, kp, title, username,entry_password, url, notes, expiry_time, tags, icon):
    entry = get_param(param, module, kp, title)
    param = parameter_name
    kp.save()

#giveback all entry infos
def get_entry(module, kp, title, groupname):
    if groupname is not None:
        entry = kp.find_entries(groupname, title=title, first=True)
    else:
        entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.title, entry.username, entry.password, entry.url, entry.notes, entry.expiry_time, entry.tags,  entry.icon)
    else:
        return None

# give back specific stuff in list:  (entry.title, entry.parameter)

def get_username(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.username)

def get_password(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.password)

def get_url(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.url)

def get_notes(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.notes)

def get_expiry_time(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.expiry_time)

def get_tags(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.tags)

def get_icon(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.icon)

def get_param(module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (param)

if __name__ == '__main__':
    main()
