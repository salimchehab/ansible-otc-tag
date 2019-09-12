## Ansible OTC Tagging Module `otc_ecs_tag`

The OTC Tag Management Service API will be used for tagging the servers (ECS).

Please make sure you have Python >= `3.5`. This was tested with Python `3.7`. 

## OpenStack and OTC Authentication

In order to accomplish the API requests, we need the following parameters in the `auth` section:

- username
- password
- project_id
- domain_name

There are multiple ways to authenticate and create a [connection in openstack](https://docs.openstack.org/openstacksdk/latest/user/connection.html).
This was tested with the clouds.yml and secure.yml files. 
There are examples here: [cloud.yml](sample_clouds.yml) and [secure.yml](secure.yml). 

## Example Playbook Tasks

Create new tags and delete the existing tags:

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

Append tags and do not delete the existing tags:

    - name: append tags for my_awesome_server in the test environment cloud without deleting the existing tags
      otc_ecs_tag:
        name: my_awesome_server
        cloud: "test"
        tags:
          Environment: "dev"
          Department: "0123"
          POPOPO: "SomeOneEvenMoreImportant"
        state: present

Delete certain tags:

    - name: delete "POPOPO" tags from my_awesome_server
      otc_ecs_tag:
        name: my_awesome_server
        cloud: "dev"
        tags:
          POPOPO: "SomeOneEvenMoreImportant"
        state: absent

The exact log output can be found in the examples folder [here](examples/ansible_output.log).

The playbooks can be run from inside the example directory: `ansible-playbook delete_tags.yml -v`

## Decision Table

Here is a summary on the different parameters and the outcome:

| state   | delete_existing_tags | Outcome                                              |
|---------|----------------------|----------------------------------------------------- |
| present | True                 |  delete all existing tags / add the user-given tags  |
| present | False                |  no tags will be deleted / add the user-given tags   |
| absent  | True                 |  delete all existing tags / no tags will be added    |
| absent  | False                |  delete only user-given tags / no tags will be added |

## How it Works

### API Summary

OTC TMS API calls:

Tag Management Service (TMS): https://tms.otc.t-systems.com

#### Endpoints and Services

Here's a list of services according to the [official website](https://open-telekom-cloud.com/en/products-services/tag-management-service):

- Elastic Cloud Server (ECS): https://ecs.eu-de.otc.t-systems.com
- Image Management Service (IMS): https://ims.otc.t-systems.com
- Auto Scaling (AS): https://as.otc.t-systems.com
- Object Storage Service (OBS): https://obs.otc.t-systems.com
- Elastic Volume Service (EVS): https://evs.eu-de.otc.t-systems.com
- Volume Backup Service (VBS): https://vbs.otc.t-systems.com
- Cloud Server Backup Service (CSBS): https://csbs.otc.t-systems.com
- Virtual Private Cloud (VPC): https://vpc.otc.t-systems.com
- Elastic IP (EIP): https://vpc.otc.t-systems.com
- Virtual Private Network
- Domain Name Service (DNS): https://dns.otc.t-systems.com
- Elastic Load Balancer (ELB): https://elb.otc.t-systems.com
- NAT Gateway: https://nat.otc.t-systems.com
- Distributed Message Service (DMS): https://dms.otc.t-systems.com
- Data Warehouse Service Data Warehouse Service (DWS): https://dws.otc.t-systems.com
- Key Management Service (KMS): https://kms.otc.t-systems.com
- MapReduce Service (MRS): https://mrs.otc.t-systems.com
- Document Database Service
- DeH via API (DeH): https://deh.otc.t-systems.com

This module however only addresse tagging in the ECS domain. The eventual goal is to try and cover the additional services as well. 

#### TMS with ECS

Below summarizes the API calls as written in the [official documentation](https://docs.otc.t-systems.com/en-us/tms_dld/index.html).

##### Adding Tags

- Adding Tags to an ECS in Batches:
    
        POST /v1/{project_id}/servers/{server_id}/tags/action

- Batch Adding Tags for the Specified EVS Disk:
    
        POST /v3/{project_id}/os-vendor-volumes/{volume_id}/tags/action

Example request:

    {
        "action": "create",
        "tags": [
            {
                "key": "key1",
                "value": "value1"
            },
            {
                "key": "key2",
                "value": "value3"
            }
    ] }

##### Deleting Tags

- Deleting Tags from an ECS in Batches:

        POST /v1/{project_id}/servers/{server_id}/tags/action

- Batch Deleting Tags for the Specified EVS Disk:

        POST /v3/{project_id}/os-vendor-volumes/{volume_id}/tags/action

Example request:

    {
        "action": "delete",
        "tags": [
            {
                "key": "key1",
                "value": "value1"
            },
            {
                "key": "key2",
                "value": "value3"
            }
    ] }

##### Querying Tags

- Querying Tags of an ECS:

        GET /v1/{project_id}/servers/{server_id}/tags

- Querying Tags of an EVS Disk:

        GET /v3/{project_id}/os-vendor-volumes/{volume_id}/tags

Example response:

    {
    "tags": [
            {
                "value": "value1",
                "key": "key1"
    }, {
                "key": "key2"
            }
    ] }
