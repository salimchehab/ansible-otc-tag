#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: otc_ecs_tag

short_description: This allows tagging of servers (ECS) using the OTC TMS API

version_added: "2.6"

description:
    - "This uses the OTC ECS and TMS APIs to create, delete, or edit tags on the elastic servers."

options:
    name:
        description:
            - The ECS server hostname (unique)
        required: True
        type: str
    cloud:
        description:
            - The cloud region (this is mapped in the cloud.yml file to the project_id and domain_name values)
        required: True
        type: str
    tags:
        description:
            - The key value pair of the tags (max. 10 items can be included)
        required: True
        type: dict
    delete_existing_tags:
        description:
            - Delete the already existing tags if set to True (tags will be replaced instead of being appended)
        required: False
        default: False
        type: bool
    verify_ssl_requests:
        description:
            - Can be set to False in case someone needs to test insecure connections or if no adequate CA is available
        required: False
        default: True
        type: bool
    state:
        description:
            - The desired state of the tags (e.g. present)
        required: False
        choices: [ "present", "absent" ]
        default: present
        type: str

requirements:
    - "ansible>=2.6.0"
    - "openstacksdk>=0.15.0"
    - "requests>=2.22.0"

author:
    - "Salim Chehab (@salimchehab)"
'''

EXAMPLES = '''
# Create new tags for a server 
- name: create tags for my_awesome_server and delete the existing ones
  otc_ecs_tag:
    name: my_awesome_server
    cloud: "dev"
    tags: 
        Environment: "dev"
        Department: "0123"
        PO: "SomeOneVeryImportant"
    delete_existing_tags: True
    state: present

# Append new tags for a server 
- name: append tags for my_awesome_server without deleting the existing ones
  otc_ecs_tag:
    name: my_awesome_server
    cloud: "dev"
    tags: 
        Environment: "dev"
        Department: "0123"
        PO: "SomeOneVeryImportant"
    state: present

# Delete all tags for my_awesome_server
- name: delete test server
  # assuming that ews_api_username and ews_api_password are located in the group vars
  otc_ecs_tag:
    name: my_awesome_server
    state: absent
'''

RETURN = '''
msg:
    description: Any information that is intended for the user (parameter validation, success or failure, etc.) 
    type: str
    returned: always
Response:
    description: The requests API response from the server
    type: str
    returned: changed
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

OPENSTACK_IMP_ERR = None
REQUESTS_IMP_ERR = None

try:
    import openstack

    HAS_OPENSTACK = True
except:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_OPENSTACK = False

try:
    import requests

    HAS_REQUESTS = True
except:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

# constants: API URI paths
API_URIS = {
    "tags_get": "/v1/{project_id}/servers/{server_id}/tags",
    "tags_post": "/v1/{project_id}/servers/{server_id}/tags/action",
}


def run_module():
    module_args = dict(
        name=dict(type="str", required=True),
        cloud=dict(type="str", required=True),
        tags=dict(type="dict", required=True),
        delete_existing_tags=dict(type="bool", required=False, default=False),
        verify_ssl_requests=dict(type="bool", required=False, default=True),
        state=dict(type="str", required=False, choices=["present", "absent"], default="present"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        msg="Initial msg contents - nothing important to share here right now.",
    )

    # fail if one of the openstack or requests libraries is missing
    if not HAS_OPENSTACK:
        module.fail_json(msg=missing_required_lib('openstack'), exception=OPENSTACK_IMP_ERR)
    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib('requests'), exception=REQUESTS_IMP_ERR)

    SERVER_EXISTS = False

    name = module.params.get('name')
    cloud = module.params.get('cloud')
    tags = module.params.get('tags')
    delete_existing_tags = module.params.get('delete_existing_tags')
    verify_ssl_requests = module.params.get('verify_ssl_requests')
    state = module.params.get('state')

    # TODO: get token using openstack: __openstack_connection.auth_token
    otc_iam_token = ''

    # requests session with the token
    requests_session = requests.Session()
    requests_session.headers.update({"Accept": "application/json"})
    requests_session.headers.update({"Content-Type": "application/json"})
    requests_session.headers.update({"X-Auth-Token": otc_iam_token})
    requests_session.verify = verify_ssl_requests
