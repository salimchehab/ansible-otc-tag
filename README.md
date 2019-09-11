## Ansible OTC Tagging Module `otc_ecs_tag`

The OTC Tag Management Service API will be used for tagging the servers (ECS).

## Examples

TODO

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
