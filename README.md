![GitHub language count](https://img.shields.io/github/languages/count/whitelotusapps/table-of-field-values)
![GitHub top language](https://img.shields.io/github/languages/top/whitelotusapps/table-of-field-values)
![GitHub repo size](https://img.shields.io/github/repo-size/whitelotusapps/table-of-field-values)
![GitHub all releases](https://img.shields.io/github/downloads/whitelotusapps/table-of-field-values/total)
![GitHub issues](https://img.shields.io/github/issues-raw/whitelotusapps/table-of-field-values)
![GitHub](https://img.shields.io/github/license/whitelotusapps/table-of-field-values)
![GitHub last commit](https://img.shields.io/github/last-commit/whitelotusapps/table-of-field-values)
# table-of-field-values
Create an internal comment that shows all of the populated field of a form in a concise table of field values.

## Configuration:
You will need to ensure that you edit the .config.yaml file and configure it according to your Zendesk instances.

```
# NOTE: 
# YOU CAN NAME THE INSTANCES WHATEVER YOU WISH.
# IN THIS SAMPLE CONFIG, I HAVE NAMED THE INSTANCES "production" and "sandbox"
# THEY COULD JUST AS EASILY BE NAMED "freelance" and "starlight"
# DO NOT CHANGE THE *NAME* OF THESE VARIABLES: "domain", "auth", or "ignore_fields" UNLESS YOU KNOW WHAT YOU ARE DOING

# BELOW IS A SAMPLE CONFIGURATION FOR A PRODUCTION INSTANCE:
production:
  # I.E: d3v-kairosnature
  domain: <ZENDESK SUBDOMAIN NAME>

  # THE BELOW WILL BE YOUR BASE64 ENCODED STRING
  # https://github.com/whitelotusapps/zendesk-developer-user-group/wiki/2023-05-26-Zendesk-Developer-User-Group-Developer-Tools-Postman#how-to-base64-encode-your-zendesk-api-token
  auth: Basic <API KEY>

  # IF USING OAuth, then use the below line instead, and comment out the above line for the API KEY
  #auth: Bearer <OAuth Secret>

  # YOU WILL NEED TO SET AT LEAST ONE VALUE, OR ELSE THE SCRIPT WILL ERROR OUT
  ignore_fields: 
    #status: <STATUS FIELD ID>
    #group: <GROUP FIELD ID>
    #assignee: <ASSIGNEE FIELD ID>


# BELOW IS A SAMPLE CONFIGURATION FOR A SANBOX INSTANCE:
sandbox:
  domain: <ZENDESK SUBDOMAIN NAME>
  auth: Basic <API KEY>
  ignore_fields: 
    #status: <STATUS FIELD ID>
    #group: <GROUP FIELD ID>
    #assignee: <ASSIGNEE FIELD ID>
```

Inside of the table_of_field_values.py file, you will need to enter in the instance you wish to connect to; from one of the instances that you have defined in the .config.yaml file.

```
# THE BELOW TWO LINES ARE THE MAIN THING TO CHANGE
# WRITE FILES = TRUE WILL WRITE JSON, CSV, AND MACRO FILES
# CSV FILES CONTAIN FORM FIELDS, THEIR ZENDESK AND LIQUID MARKUP PLACE HOLDERS
# JSON FILES CONTAIN WHAT CAN BE USED IN A TRIGGER FOR A JSON PAYLOAD
# MACRO FILES CONTAIN WHAT CAN BE USED IN DYNAMIC CONTENT FOR GENERATING THE TABLE OF FIELD VALUES
# MACRO FILES ARE WHAT ARE NEEDED MOST TO MAINTAIN THE TABLE OF FIELD VALUES
# INSTANCE IS THE ZENDESK INSTANCE YOU WISH TO CONNECT TO, AS DEFINED IN THE .config.yaml FILE
write_files = True
instance = 'production'

domain = config[instance]['domain']
auth = config[instance]['auth']

# WE SET THE FIELDS THAT WE WANT TO EXCLUDE FROM THE TABLE OF FIELD VALUES
# SUCH FIELDS MAY BE THE SUBJECT FIELD, DESCRIPTION, ETC.
ignore_fields = config[instance]['ignore_fields']
```

## Execution

If you open this file in VS Code, you should be able to run it directly from there and have it execute. Otherwise, you can open a terminal and execute it manually:

```
python3 table_of_field_values.py
```

## Output

Sample output from this script can be located in the "Example Output" folder

## Usage of Output

The MACRO folder contains files that can be directly copied and pasted into Dynamic Content and used via triggers or macros to insert an internal comment that generates the table of field values.

Once Dynamic Content has been created that contains the contents of a .macro file, you can create a macro with these settings:
  - Actions: 
    - Comment Mode -> Private
    - Comment/Description:
      - Rich content:
      ```
      \{{<DYNAMIC CONTENT PLACEHOLDER>}}
      ```
NOTE: You must escape the dynamic content placeholder with a backslash slash "\\".


