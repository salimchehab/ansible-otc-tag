#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
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
    - "openstacksdk>=0.35.0"
    - "requests>=2.22.0"

author:
    - "Salim Chehab (@salimchehab)"
"""

EXAMPLES = """
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
- name: append tags for my_awesome_server in the test environment cloud without deleting the existing tags
  otc_ecs_tag:
    name: my_awesome_server
    cloud: "test"
    tags: 
      Environment: "test"
      Department: "007"
      Manager: "SomeOneEvenMoreImportant"
    state: present

# Delete certain tags for a server
- name: delete "Environment" tags from my_awesome_server
  # assuming that ews_api_username and ews_api_password are located in the group vars
  otc_ecs_tag:
    name: my_awesome_server
    tags: 
      Environment: "test"
    state: absent
"""

RETURN = """
msg:
    description: Any information that is intended for the user (parameter validation, success or failure, etc.) 
    type: str
    returned: always
Tags_before:
    description: The existing tags on the server
    type: list
    returned: always
Tags_after:
    description: The new tags on the server
    type: list
    returned: changed
Response:
    description: The response from the server in case of failure / success otherwise
    type: str
    returned: always
"""

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

# Endpoints and URIs to be used in the requests
ECS_ENDPOINT_URL = "https://ecs.eu-de.otc.t-systems.com"
ECS_API_URIS = {
    'tags_get': '/v1/{project_id}/servers/{server_id}/tags',
    'tags_post': '/v1/{project_id}/servers/{server_id}/tags/action',
}


def get_tags(requests_session: object, project_id: str, server_id: str) -> tuple:
    """ returns a list of the tags that are attached to a certain server along with the API call status code
    GET /v1/{project_id}/servers/{server_id}/tags
    example returned value: ([{"value": "value1", "key": "key1"}, {"key": "key2"}], 200, "success")

    :param requests_session: requests session object containing the token and necessary headers
    :param server_id: server id
    :param project_id: project id
    """

    tags_response = requests_session.get(
        ECS_ENDPOINT_URL + ECS_API_URIS.get('tags_get').format(project_id=project_id, server_id=server_id))
    status_code = tags_response.status_code
    tags = []
    if status_code == 200:
        tags = tags_response.json()['tags']
        message = "success"
    else:
        message = tags_response.content
    return tags, status_code, message


def generate_otc_format_tags(tags: dict) -> list:
    """ returns a list of dictionaries containing the key value pairs of the tags e.g. [{"value": "value1", "key": "key1"}, {"key": "key2"}]

    :param tags: a hash map of the tags e.g. {"key1": "value1", "key2": ""} or {"env": " dev", "team": "one"}
    """

    otc_format_tags = []
    otc_format_tags_template = {
        'key': '',
        'value': ''
    }
    for key, value in tags.items():
        otc_format_tags_template['key'] = key
        otc_format_tags_template['value'] = value
        # deep copy to prevent duplicate key errors
        otc_format_tags.append(otc_format_tags_template.copy())
    return otc_format_tags


def post_tags(requests_session: requests.Session, project_id: str, server_id: str, otc_format_tags: list,
              action: str) -> tuple:
    """ used to send a post in  the requests session to to create or delete tags
    POST /v1/{project_id}/servers/{server_id}/tags/action
    returns the status code and a message
    example returned value: (204, "success")

    :param requests_session: requests session object containing the token and necessary headers
    :param server_id: server id
    :param project_id: project id
    :param otc_format_tags: a list of hash maps of the tags e.g. [{"value": "value1", "key": "key1"}, {"key": "key2"}]
    :param action: can be 'create' or 'delete'
    """

    post_tags_payload = {
        'action': action,
        'tags': otc_format_tags
    }
    tags_post_response = requests_session.post(
        ECS_ENDPOINT_URL + ECS_API_URIS.get('tags_post').format(project_id=project_id, server_id=server_id),
        json=post_tags_payload)

    status_code = tags_post_response.status_code
    # create and delete tags return a 204 status code when successful
    if status_code == 204:
        message = "success"
    else:
        message = tags_post_response.content
    return status_code, message


# NOTE: formatting of tags
# Tags as entered by the user (dict): {"key1": "value1", "key2": ""}
# Tags in OTC format (list of dict): [{"value": "value1", "key": "key1"}, {"key": "key2"}]

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        cloud=dict(type='str', required=True),
        tags=dict(type='dict', required=True),
        delete_existing_tags=dict(type='bool', required=False, default=False),
        verify_ssl_requests=dict(type='bool', required=False, default=True),
        state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        msg='Initial empty msg contents - nothing important to share here right now.',
        Response='Initial empty response contents - nothing important to share here right now.',
    )

    # fail if one of the required openstack or requests libraries is missing
    if not HAS_OPENSTACK:
        module.fail_json(msg=missing_required_lib('openstack'), exception=OPENSTACK_IMP_ERR)
    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib('requests'), exception=REQUESTS_IMP_ERR)

    name = module.params.get('name')
    cloud = module.params.get('cloud')
    tags = module.params.get('tags')
    delete_existing_tags = module.params.get('delete_existing_tags')
    verify_ssl_requests = module.params.get('verify_ssl_requests')
    state = module.params.get('state')

    # use openstack to get the auth token instead of using the OTC IAM "https://iam.eu-de.otc.t-systems.com" endpoint
    openstack_connection = openstack.connect(cloud=cloud)
    openstack_connection_auth_token = openstack_connection.auth_token

    # requests session updated headers with the token
    requests_session = requests.Session()
    requests_session.headers.update({'Accept': 'application/json'})
    requests_session.headers.update({'Content-Type': 'application/json'})
    requests_session.headers.update({'X-Auth-Token': openstack_connection_auth_token})
    requests_session.verify = verify_ssl_requests

    SERVER_EXISTS = False
    # returns a list of server ``munch.Munch``
    servers = openstack_connection.list_servers()
    for server in servers:
        if server.name == name:
            SERVER_EXISTS = True
            server_id = server.id
            # do not know why we need to provide the project id if it can be identified from the server id response
            # another way to get the project id would be from _get_openstack_connection_auth()['project_id']
            # project_id is provided in the auth dict param in one of the clouds.yml or secure.yml files
            project_id = server.location.project.id
            break

    existing_tags_otc_format, status_code, message = get_tags(requests_session, project_id, server_id)
    result['Tags_before'] = existing_tags_otc_format
    result['Response'] = message
    if message != "success":
        result['msg'] = 'Failed to get tags!'
        module.fail_json(**result)

    if module.check_mode:
        result['msg'] = 'Running in check mode..'
        module.exit_json(**result)

    if not SERVER_EXISTS:
        result['msg'] = f"The provided hostname: {name} could not be found!"
        module.fail_json(**result)

    if (state == 'absent' and not existing_tags_otc_format) or (
            state == 'present' and delete_existing_tags and not existing_tags_otc_format):
        result['msg'] = f"{name} does not have any tags. Cannot delete Tags! (state might be set to absent or " \
                        f"delete_existing_tags to true). "
        module.fail_json(**result)

    # the post requests take a list with specific key value names
    user_provided_tags_otc_format = generate_otc_format_tags(tags)

    # Tag deletion and creation decision table:
    # | state   | delete_existing_tags | Outcome                                              |
    # |---------|----------------------|----------------------------------------------------- |
    # | present | True                 |  delete all existing tags / add the user-given tags  |
    # | present | False                |  no tags will be deleted / add the user-given tags   |
    # | absent  | True                 |  delete all existing tags / no tags will be added    |
    # | absent  | False                |  delete only user-given tags / no tags will be added |

    if delete_existing_tags:
        delete_tags_status_code, delete_existing_tags_message = post_tags(requests_session, project_id, server_id,
                                                                          existing_tags_otc_format,
                                                                          "delete")
        if delete_tags_status_code != 204:
            result['msg'] = f"Could not delete tags. Response code: {delete_tags_status_code}."
            result['Response'] = f"{delete_existing_tags_message}"
            module.fail_json(**result)
        result['msg'] = 'Successfully deleted existing tags.'

    if state == 'present':
        post_tags_status_code, post_tags_message = post_tags(requests_session, project_id, server_id,
                                                             user_provided_tags_otc_format,
                                                             "create")
        if post_tags_status_code != 204:
            result['msg'] = f"Could not add tags. Response code: {post_tags_status_code}."
            result['Response'] = f"{post_tags_message}"
            module.fail_json(**result)
        result['msg'] = 'Successfully added new tags.'

    elif state == 'absent':
        # TODO: see if can be combined with the above "delete_existing_tags" since it is almost the same and only
        #  differs in the tags variable
        delete_tags_status_code, delete_existing_tags_message = post_tags(requests_session, project_id, server_id,
                                                                          user_provided_tags_otc_format,
                                                                          "delete")
        if delete_tags_status_code != 204:
            result['msg'] = f"Could not delete tags. Response code: {delete_tags_status_code}."
            result['Response'] = f"{delete_existing_tags_message}"
            module.fail_json(**result)
        result['msg'] = 'Successfully deleted existing tags.'

    new_tags_otc_format, status_code, message = get_tags(requests_session, project_id, server_id)
    result['Tags_after'] = new_tags_otc_format

    if existing_tags_otc_format != new_tags_otc_format:
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
