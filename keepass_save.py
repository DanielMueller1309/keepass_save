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

DOCUMENTATION = '''
---
module: keepass

short_description: This a module to interact with a keepass (kdbx) database.

version_added: "1.0"

description:
    - "This a module to interact with a keepass (kdbx) database. To save informatin into a kdbx file (exept  and icon, comming soon)"

requirements:
    - PyKeePass

options:
    database:
        description:
            - Path of the keepass database.
        required: true
        type: str

    keyfile:
        description:
            - Path of the keepass keyfile. Either this or 'password' (or both) are required.
        required: false
        type: str

    title:
        description:
            - title, will be used for the title of the entry.
        required: true
        type: str

    username:
        description:
            - Username of the entry.
        required: true
        type: str

    db_password:
        description:
            - Path of the keepass keyfile. Either this or 'keyfile' (or both) are required.
        required: false
        type: str
        
    notes:
        description:
            - this param is the most important one (sacasm) he gives us the the space for notes
        defaults:
            - 'This Entry is Ansible Managed'
            
    icon:
        description:
            - to specifi somethin for the eys to see with the default icon which entry is ansible manged
        defaults:
            - '47'
            
    url: 
        description:
        - to fill the url field in kdbx file
        
author:
    - DanielMueller1309 https://github.com/DanielMueller1309
'''

EXAMPLES = '''
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
'''

RETURN = '''
new_username:
    description: the new username who is set by an existing entry
    type: str
add_username:
    description: the added username who is set by a new entry
    type: str

P.S: this return statements are also available by every entry parameter who is changed or created
'''
import traceback

from ansible.module_utils.basic import AnsibleModule,missing_required_lib

PYKEEPASS_IMP_ERR = None
try:
    from pykeepass import PyKeePass
    import pykeepass.exceptions
except ImportError:
    PYKEEPASS_IMP_ERR = traceback.format_exc()
    pykeepass_found = False
else:
    pykeepass_found = True

import subprocess
import argparse

def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        database=dict(type='str', required=True),
        keyfile=dict(type='str', required=False, default=None),
        db_password=dict(type='str', required=False, default=None, no_log=True),
        title=dict(type='str', required=True),
        username=dict(type='str', required=True),
        entry_password=dict(type='str', required=False, default=None, no_log=True),
        notes=dict(type='str', required=False, default='This Entry is Ansible Managed'),
        #expiry_time=dict(type='str', required=False, default=None),
        #tags=dict(type='str', required=False, default=None),
        icon=dict(type='int', required=False, default=47),
        url=dict(type='str', required=False, default=None),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
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
    db_password        = module.params['db_password']
    title         = module.params['title']
    username        = module.params['username']
    entry_password  = module.params['entry_password']
    notes           = module.params['notes']
    #expiry_time     = module.params['expiry_time']
    #tags            = module.params['tags']
    icon            = module.params['icon']
    url             = module.params['url']
    if not db_password and not keyfile:
        module.fail_json(msg="Either 'password' or 'keyfile' (or both) are required.")

    try:
        kp = PyKeePass(database, password=db_password, keyfile=keyfile)
    except IOError as e:
        KEEPASS_OPEN_ERR = traceback.format_exc()
        module.fail_json(msg='Could not open the database or keyfile.')
    except FileNotFoundError:
        KEEPASS_OPEN_ERR = traceback.format_exc()
        module.fail_json(msg='Could not open the database. Credentials are wrong or integrity check failed')

    # try to get the entry from the database
    db_entry = get_entry(module, kp, title)
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
            result['changed'] = False
            if username != db_entry_username:
                set_username(module, kp, title, username)
                result['new_username'] = username
                result['changed'] = True

            if entry_password != db_entry_password:
                set_entry_password(module, kp, title, entry_password)
                result['new_password'] = entry_password
                result['changed'] = True

            if notes != db_entry_notes :
                set_notes(module, kp, title, notes)
                result['new_notes'] = notes
                result['changed'] = True

            if url != db_entry_url:
                set_url(module, kp, title, url)
                result['new_url'] = url
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
                result['new_icon'] = str(icon)
                result['changed'] = True


            module.exit_json(**result)

    # if there is no matching entry, create a new one
    #password = entry_password
    if not module.check_mode:
        try:
            create_entry(module, kp, username, title, entry_password, notes, icon, url)
        except:
            KEEPASS_SAVE_ERR = traceback.format_exc()
            module.fail_json(msg='Could not add the entry or save the database.', exception=KEEPASS_SAVE_ERR)

    result['add_title']             = title
    result['add_username']          = username
    result['add_entry_password']    = entry_password
    result['add_notes']             = notes
    result['add_icon'] = icon
    result['add_url'] = url
    result['changed']           = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def create_entry(module, kp, username, title, password, notes, icon, url):
    kp.add_entry(kp.root_group, title, username, password, icon=str(icon), notes=notes, url=url)
    kp.save()
#set specific stuff (here to change later is the group to a new module param)
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
def get_entry(module, kp, title):

    entry = kp.find_entries(title=title, first=True)

    if (entry):
        return (entry.title, entry.username, entry.password, entry.url, entry.notes, entry.expiry_time, entry.tags,  entry.icon) #
    else:
        return None

# give back specific stuff in list:  (entry.title, entry.parameter)

def get_username(module, kp, title, username):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.username)

def get_password(module, kp, title, password):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.password)

def get_url(module, kp, title, url):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.url)

def get_notes(module, kp, title, notes):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.notes)

def get_expiry_time(module, kp, title, expiry_time):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.expiry_time)

def get_tags(module, kp, title, tags):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.tags)

def get_icon(module, kp, title, icon):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (entry.icon)

def get_param(param, module, kp, title):
    entry = kp.find_entries(title=title, first=True)
    if (entry):
        return (param)

if __name__ == '__main__':
    main()