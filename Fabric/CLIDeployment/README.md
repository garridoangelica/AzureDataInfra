Using the Fabric CLI

Here's an example on how to run this Fabric CLI deployment: 
./fabric-deploy.sh deploy DataEngineeringWSDevCICD FabricCLI-DEDev fsku2eastus SilverLakehouse GoldWarehouse SilverToGoldNotebook env
In this example we're creating a workspace, a lakehouse, a data warehouse with tables, importing a ntoebook and supporting 2 authentication methods service principal and interactive. 

The idea is to show how to leverage the Fabric CLI for Microsfot Fabric workspaec management, it's advantages and limitiations. In this example, I tried to make the code as functional as possible. Separated into modules so that others can leverage similar functionality and understand how to approach a scalable deployment solution with the CLI

- Lots of flexibility to create items the way you want
- For example, you can create code that would look at an existing workspace git repo and create code to go through each item and deploy. But it requires extra work to make this happen. 
- Errors are not very detailed, for example when trying to create a workspace with an existing capacity, the error I was getting was: 
fab mkdir 'FabricCLI-DEDev'.Workspace -P capacityname=fsku2eastus
x mkdir: [NotFound] The Capacity 'fsku2eastus.Capacity' could not be found
This is not very descriptive. When I went to the Fabric Rest API documentation (https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace?tabs=HTTP) It states that SPN or caller need extra permissions on capacity and Fabric tenant. After permissions to SPN were provided then I was able to continue with workspace creation. This is not a stopper per say, but it can't cause a bit of delay in troubleshooting. If I were to call this command from the rest api this is the message I get: The calling principal has no sufficient permissions over the target capacity" and error code "InsufficientPermissionsOverCapacity". To fix this I had to go to capacity settings in admin portal, select Fabric capacity and add the security group where the service principal belongs to Contributor permissions. Recommendation is to leverage the Fabric Rest API docs to validate permissions/requirements for the respective CLI command and further help you with troubleshooting. At the end of the day, the CLI is a wrapper on top of the APIs for faster development.

Yet some other errors are very direct, like I was unable to create lakehouse because of special characters in name:
[INFO] Creating lakehouse 'FabricCLI-BronzeLK' in workspace 'FabricCLI-DEDev'...
x create: [Special caracters not supported for this item type] Lakehouse name 'FabricCLI-BronzeLK' contains unsupported special characters
[ERROR] Failed to create lakehouse 'FabricCLI-BronzeLK'

The CLI is used for creating higher level objects. When trying to create a warehouse table, there wasn't an option. A workaround would be connecting directly to the SQL endpoint and executing the DDL commands. For this, you will have to obtain the connection string of the warehouse created and then leverage CLI API 

To run this: 
You need this installed: for executing SQL scripts in warehouse
https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-download-install?view=sql-server-ver17&tabs=windows

And the Fabric CLI
You need to create an .env file with service principal secrets, client id and tenant If you would like to use SPN to authenticate. Otherwise use interactive mode for authentication. 
in your .env put the following parameters: Note: do not enclose parameters in quotes.
FABRIC_CLIENT_ID=<clientid>
FABRIC_CLIENT_SECRET=<secret>
FABRIC_TENANT_ID=<tenantid>

Another thing I've encountered is for when importing notebooks into a workspace you need to keep in mind that you're importing all of the metadata information, meaning if a notebook has a defaulted lakehouse, environment, warehouse... You will have to change this either before import or if done after import which is in this case, you need to do a post-processing of finding the respective ids of the lakehouses and workspaces and changing the properties of the notebook.
Now in this case I imported a notebook but there might be scenarios where we will need to do more advance automations. For example, you might want to create a data pipeline or an event stream with already defined activities. These type of operations can be done by levearing the API functionality within the CLI. It allows you to do post requests with the same authentication. 

Let's say for example I have a pipeline that I would like to deploy. I would first have to convert the pipeline json definition to base64 and create a body like this: 

body = {
  "displayName": "DataPipeline 1",
  "description": "A data pipeline description",
  "definition": {
    "parts": [
      {
        "path": "pipeline-content.json",
        "payload": "ewogICAgInByb3***A==",
        "payloadType": "InlineBase64"
      },
      {
        "path": ".platform",
        "payload": "ZG90UGx****Jpbmc=",
        "payloadType": "InlineBase64"
      }
    ]
  }
}

Then you can call the Fabric CLI API function like this:fab api workspaces
fab api workspaces/<workspaceid>/items -X post -H "content-type=application/json" -i '$body'