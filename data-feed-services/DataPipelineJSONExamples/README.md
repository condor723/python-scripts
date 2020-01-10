# data-feed-services - ETL Job Automation via Data Pipeline (Megatron)

## Prerequisites

AWS Nexus Access - Follow "Setup AWS Access" step only.

## Getting Started

Our Data Pipeline jobs live in AWS - Filter pipelines by "megatron".


## Creating a pipeline from example JSONs

1. Grab the JSON pipeline file and replace references to client name
2. Create the S3 folders that correspond to locations in pipeline JSON
3. Create the directories on BV SFTP
   * /data-feed-services
   * /data-feed-services/backup/
4. Create Pipeline
   1. Name: dfs-megatron-{clientname}-{type of feed} (Example:dfs-megatron-marriott-product)
   2. Description: Brief description on the type of feed and the frequency. Also add in the DFS or GSCP JIRA ticket
   3. Set Schedule
   4. Ensure logging is enabled 
   5. Secrity/Access Custom
   6. Add Tags
      * bv:nexus:team
      * bv:nexus:vpc
        * prod
      * bv:nexus:service
        * megatron
   7. Edit in Architect -> check paths are correct
5. Copy runscript-aws.sh & sftpbatch from existing client folder on S3 
   1. Update client specific pieces and update sftp location if SFTP7 needs to be updated
