import os
import requests
import json
import time
import yaml
from dateutil import parser


# Function to clear the screen
def clear_screen():
    # Clear screen command based on the operating system
    if os.name == "posix":  # For UNIX, Linux, MacOS
        os.system("clear")
    elif os.name == "nt":  # For Windows
        os.system("cls")


clear_screen()

with open(".config.yaml", encoding="utf-8") as config_data:
    config = yaml.load(config_data, Loader=yaml.FullLoader)

# THE BELOW TWO LINES ARE THE MAIN THING TO CHANGE
# WRITE FILES = TRUE WILL WRITE JSON, CSV, AND MACRO FILES
# CSV FILES CONTAIN FORM FIELDS, THEIR ZENDESK AND LIQUID MARKUP PLACE HOLDERS
# JSON FILES CONTAIN WHAT CAN BE USED IN A TRIGGER FOR A JSON PAYLOAD
# MACRO FILES CONTAIN WHAT CAN BE USED IN DYNAMIC CONTENT FOR GENERATING THE TABLE OF FIELD VALUES
# MACRO FILES ARE WHAT ARE NEEDED MOST TO MAINTAIN THE TABLE OF FIELD VALUES
# INSTANCE IS THE ZENDESK INSTANCE YOU WISH TO CONNECT TO, AS DEFINED IN THE .config.yaml FILE
write_files = True
instance = "production"

domain = config[instance]["domain"]
auth = config[instance]["auth"]

# WE SET THE FIELDS THAT WE WANT TO EXCLUDE FROM THE TABLE OF FIELD VALUES
# SUCH FIELDS MAY BE THE SUBJECT FIELD, DESCRIPTION, ETC.
ignore_fields = config[instance]["ignore_fields"]

######################################################################################################################################
# CREATE FOLDERS IF THEY DO NOT CURRENTLY EXIST
folders = ["CSV", "JSON", "MACRO"]

for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)
######################################################################################################################################

######################################################################################################################################
print(
    f"\n=============================================================================================================\nDOMAIN: {domain}\n\n=============================================================================================================\n"
)

timestr = time.strftime("%Y%m%d-%H%M%S")
######################################################################################################################################

######################################################################################################################################
url = f"https://{domain}.zendesk.com/api/v2/ticket_fields"

payload = {}
headers = {"Authorization": f"{auth}"}

response = requests.request("GET", url, headers=headers, data=payload, timeout=10).text
data = json.loads(response)
ticket_fields = data["ticket_fields"]
######################################################################################################################################


######################################################################################################################################
all_ticket_fields = {}

for ticket_field in ticket_fields:
    ticket_field_active = ticket_field["active"]

    if ticket_field_active is True:
        ticket_field_id = ticket_field["id"]
        ticket_field_name = ticket_field["title"]
        ticket_field_type = ticket_field["type"]
        ticket_field_visible = ticket_field["visible_in_portal"]
        ticket_name_in_portal = ticket_field["title_in_portal"]

        all_ticket_fields[ticket_field_id] = {
            "title": ticket_field_name,
            "type": ticket_field_type,
            "visible_in_portal": ticket_field_visible,
            "title_in_portal": ticket_name_in_portal,
        }
######################################################################################################################################

######################################################################################################################################
url = f"https://{domain}.zendesk.com/api/v2/brands"

payload = {}
headers = {"Authorization": f"{auth}"}

response = requests.request("GET", url, headers=headers, data=payload, timeout=10).text
all_brands_json = json.loads(response)
all_brands = all_brands_json["brands"]
######################################################################################################################################


######################################################################################################################################
all_forms_macro_liquid_markup = ""

for brand in all_brands:
    brand_name = brand["name"]
    brand_form_ids = brand["ticket_form_ids"]
    brand_forms = ",".join(map(str, brand_form_ids))

    if len(brand_form_ids) > 0:
        if write_files is True:
            csv_output = f"./CSV/{timestr} - {domain} - {brand_name}.csv"
            json_output = f"./JSON/{timestr} - {domain} - {brand_name}.json"
            macro_output = f"./MACRO/{timestr} - {domain} - {brand_name}.macro"

        form_counter = 0
        brand_forms_macro_liquid_markup = ""
        brand_forms_complete_json = '''{"ticket":{"comment":{"html_body": "'''

        print(
            f"\n=============================================================================================================\nDOMAIN: {domain}\nBRAND : {brand_name}\n\n=============================================================================================================\n"
        )

        ######################################################################################################################################

        url = f"https://{domain}.zendesk.com/api/v2/ticket_forms/show_many?ids={brand_forms}"

        payload = {}
        headers = {"Authorization": f"{auth}"}

        response = requests.request(
            "GET", url, headers=headers, data=payload, timeout=10
        ).text
        all_forms = json.loads(response)
        current_set_of_forms = all_forms["ticket_forms"]

        ######################################################################################################################################
        for form in current_set_of_forms:
            form_name = form["name"]
            form_id = form["id"]
            form_active = form["active"]

            if form_name and form_active is True:
                form_counter += 1
                print(
                    "\n=============================================================================================================\n"
                )
                # print(f"{form_counter} - Brand: {brand_name}\t\tForm Name: {form_name}\t\tForm ID: {form_id}\t\n\nForm Field IDs:\n")
                print(
                    f"{form_counter} - Brand: {brand_name}\t\tForm Name: {form_name}\t\tForm ID: {form_id}\t\n"
                )

                html_comment = (
                    """<style>table {"""
                    + "width: 800px;"
                    + "}"
                    + "th, td"
                    + "{"
                    + "width: 50%;"
                    + "}"
                    + "table.fixed "
                    + "{"
                    + "table-layout: fixed;"
                    + "}"
                    + f"</style><h2><center>{form_name}"
                    + "</h2></center><br><center><table><tbody><tr bgcolor="
                    + """'#ddd"""
                    """'><td><strong>Field Name</strong></td><td><strong>Field Value</strong></td></tr>"""
                )

                current_form_macro_liquid_markup = ""
                current_form_macro_liquid_markup = (
                    "{% if ticket.ticket_form == "
                    + "'"
                    + f"{form_name}"
                    + "'"
                    + " %}"
                    + html_comment
                )

                ######################################################################################################################################
                if write_files == True:
                    with open(csv_output, "a") as csv_output_file:
                        csv_output_file.write(f"{form_name}, {form_id}\n")
                ######################################################################################################################################

                form_field_ids = form["ticket_field_ids"]

                whole_form_html = ""
                whole_form_html += html_comment
                macro_form_html = ""
                macro_form_html += current_form_macro_liquid_markup

                ######################################################################################################################################
                for form_field_id in form_field_ids:
                    if form_field_id in all_ticket_fields:
                        raw_ticket_field_name = all_ticket_fields[form_field_id][
                            "title"
                        ]
                        ticket_field_name_in_portal = all_ticket_fields[form_field_id][
                            "title_in_portal"
                        ]
                        ticket_field_type = all_ticket_fields[form_field_id]["type"]

                        if form_field_id not in ignore_fields.values():
                            matched_field = 0
                            match ticket_field_type:
                                case "multiselect" | "tagger" | "integer":
                                    if ":" in raw_ticket_field_name:
                                        ticket_field_name = (
                                            raw_ticket_field_name.partition(":")[
                                                2
                                            ].strip()
                                        )
                                    else:
                                        ticket_field_name = raw_ticket_field_name

                                    if (
                                        ticket_field_type == "multiselect"
                                        and matched_field == 0
                                    ):
                                        ticket_field_placeholder = (
                                            "{{"
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + "}}"
                                        )
                                        ticket_field_placeholder_plain = f"ticket.ticket_field_option_title_{form_field_id}"
                                        ticket_html_combo = (
                                            "{% if "
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + " != "
                                            """'' and ticket.ticket_field_option_title_{}""".format(
                                                form_field_id
                                            )
                                            + " != "
                                            """'-"""
                                            """'  %}"""
                                            + """<tr><td><strong>{}""".format(
                                                ticket_field_name
                                            )
                                            + """</strong></td><td><ul><li>"""
                                            + "{{"
                                            + "ticket.ticket_field_option_title_{}".format(
                                                form_field_id
                                            )
                                            + " | replace: "
                                            + "', '"
                                            + " , "
                                            + "'</li><li>'"
                                            + "}}</li></ul></td></tr>"
                                            + "{% endif %}"
                                        )
                                        whole_form_html += ticket_html_combo
                                        macro_form_html += ticket_html_combo

                                    if (
                                        ticket_field_type != "multiselect"
                                        and matched_field == 0
                                    ):
                                        ticket_field_placeholder = (
                                            "{{"
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + "}}"
                                        )
                                        ticket_field_placeholder_plain = f"ticket.ticket_field_option_title_{form_field_id}"
                                        ticket_html_combo = (
                                            "{% if "
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + " != "
                                            """'' and ticket.ticket_field_option_title_{}""".format(
                                                form_field_id
                                            )
                                            + " != "
                                            """'-"""
                                            """'  %}"""
                                            + """<tr><td><strong>{}""".format(
                                                ticket_field_name
                                            )
                                            + """</strong></td><td>"""
                                            + "{{"
                                            + "ticket.ticket_field_option_title_{}".format(
                                                form_field_id
                                            )
                                            + " | capitalize }}</td></tr>"
                                            + "{% endif %}"
                                        )
                                        whole_form_html += ticket_html_combo
                                        macro_form_html += ticket_html_combo

                                case "checkbox":
                                    if ":" in raw_ticket_field_name:
                                        ticket_field_name = (
                                            raw_ticket_field_name.partition(":")[
                                                2
                                            ].strip()
                                        )
                                    else:
                                        ticket_field_name = raw_ticket_field_name

                                    ticket_field_placeholder = (
                                        "{{"
                                        + f"ticket.ticket_field_{form_field_id}"
                                        + "}}"
                                    )
                                    ticket_field_placeholder_plain = (
                                        f"ticket.ticket_field_{form_field_id}"
                                    )
                                    ticket_html_combo = (
                                        "{% if "
                                        + f"ticket.ticket_field_{form_field_id}"
                                        + " == "
                                        """'1"""
                                        """' %}"""
                                        + """<tr><td><strong>{}""".format(
                                            ticket_field_name
                                        )
                                        + """</strong></td><td>"""
                                        + "Confirmed</td></tr>"
                                        + "{% endif %}"
                                    )
                                    whole_form_html += ticket_html_combo
                                    macro_form_html += ticket_html_combo

                                case "textarea":
                                    if ":" in raw_ticket_field_name:
                                        ticket_field_name = (
                                            raw_ticket_field_name.partition(":")[
                                                2
                                            ].strip()
                                        )
                                    else:
                                        ticket_field_name = raw_ticket_field_name

                                case "date":
                                    if ":" in raw_ticket_field_name:
                                        ticket_field_name = (
                                            raw_ticket_field_name.partition(":")[
                                                2
                                            ].strip()
                                        )
                                        ticket_field_placeholder = (
                                            "{{"
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + "}}"
                                        )
                                        ticket_field_placeholder_plain = f"ticket.ticket_field_option_title_{form_field_id}"
                                        ticket_html_combo = (
                                            "{% if "
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + " != "
                                            """'' and ticket.ticket_field_option_title_{}""".format(
                                                form_field_id
                                            )
                                            + " != "
                                            """'-"""
                                            """'  %}"""
                                            + """<tr><td><strong>{}""".format(
                                                ticket_field_name
                                            )
                                            + """</strong></td><td>"""
                                            + "{{"
                                            + "ticket.ticket_field_option_title_{}".format(
                                                form_field_id
                                            )
                                            + "}}</td></tr>"
                                            + "{% endif %}"
                                        )
                                        whole_form_html += ticket_html_combo
                                        macro_form_html += ticket_html_combo
                                    else:
                                        ticket_field_name = raw_ticket_field_name
                                        ticket_field_placeholder = (
                                            "{{"
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + "}}"
                                        )
                                        ticket_field_placeholder_plain = f"ticket.ticket_field_option_title_{form_field_id}"
                                        ticket_html_combo = (
                                            "{% if "
                                            + f"ticket.ticket_field_option_title_{form_field_id}"
                                            + " != "
                                            """'' and ticket.ticket_field_option_title_{}""".format(
                                                form_field_id
                                            )
                                            + " != "
                                            """'-"""
                                            """'  %}"""
                                            + """<tr><td><strong>{}""".format(
                                                ticket_field_name
                                            )
                                            + """</strong></td><td>"""
                                            + "{{"
                                            + "ticket.ticket_field_option_title_{}".format(
                                                form_field_id
                                            )
                                            + "}}</td></tr>"
                                            + "{% endif %}"
                                        )
                                        whole_form_html += ticket_html_combo
                                        macro_form_html += ticket_html_combo

                                case _:
                                    if matched_field == 0:
                                        if ":" in raw_ticket_field_name:
                                            ticket_field_name = (
                                                raw_ticket_field_name.partition(":")[
                                                    2
                                                ].strip()
                                            )
                                            ticket_field_placeholder = (
                                                "{{"
                                                + f"ticket.ticket_field_option_title_{form_field_id}"
                                                + "}}"
                                            )
                                            ticket_field_placeholder_plain = f"ticket.ticket_field_option_title_{form_field_id}"
                                            ticket_html_combo = (
                                                "{% if "
                                                + f"ticket.ticket_field_option_title_{form_field_id}"
                                                + " != "
                                                """'' and ticket.ticket_field_option_title_{}""".format(
                                                    form_field_id
                                                )
                                                + " != "
                                                """'-"""
                                                """'  %}"""
                                                + """<tr><td><strong>{}""".format(
                                                    ticket_field_name
                                                )
                                                + """</strong></td><td>"""
                                                + "{{"
                                                + "ticket.ticket_field_option_title_{}".format(
                                                    form_field_id
                                                )
                                                + "}}</td></tr>"
                                                + "{% endif %}"
                                            )
                                            whole_form_html += ticket_html_combo
                                            macro_form_html += ticket_html_combo
                                        else:
                                            ticket_field_name = raw_ticket_field_name
                                            ticket_field_name = raw_ticket_field_name
                                            ticket_field_placeholder = (
                                                "{{"
                                                + f"ticket.ticket_field_option_title_{form_field_id}"
                                                + "}}"
                                            )
                                            ticket_field_placeholder_plain = f"ticket.ticket_field_option_title_{form_field_id}"
                                            ticket_html_combo = (
                                                "{% if "
                                                + f"ticket.ticket_field_option_title_{form_field_id}"
                                                + " != "
                                                """'' and ticket.ticket_field_option_title_{}""".format(
                                                    form_field_id
                                                )
                                                + " != "
                                                """'-"""
                                                """'  %}"""
                                                + """<tr><td><strong>{}""".format(
                                                    ticket_field_name
                                                )
                                                + """</strong></td><td>"""
                                                + "{{"
                                                + "ticket.ticket_field_option_title_{}".format(
                                                    form_field_id
                                                )
                                                + "}}</td></tr>"
                                                + "{% endif %}"
                                            )
                                            whole_form_html += ticket_html_combo
                                            macro_form_html += ticket_html_combo

                            if write_files == True:
                                with open(csv_output, "a") as csv_output_file:
                                    csv_output_file.write(
                                        f",,{form_field_id},{ticket_field_name},{ticket_field_type},{ticket_field_placeholder},{ticket_field_placeholder_plain}\n"
                                    )

                #                           print("{: >30} ({: >30}) ({: >30}) ({: >30})\t{: >30}\t{: >30}".format(form_field_id, ticket_field_name,ticket_field_name_in_portal, ticket_field_type, ticket_field_placeholder, ticket_field_placeholder_plain))

                ######################################################################################################################################

                html_comment = (
                    '''{"ticket":{"comment":{"html_body": "'''
                    + whole_form_html
                    + """</tbody></table></center>","public": false,"type": "comment"}}}"""
                )

                current_form_macro_liquid_markup = (
                    macro_form_html + "</tbody></table></center>{% endif %}"
                )

                #                print(f"\n\nDOMAIN: {domain}\tBRAND: {brand_name}\tFORM: {form_name}\tJSON:")
                #                print(f'\n\n{html_comment}\n\n')
                #                print(f"DOMAIN: {domain}\tBRAND: {brand_name}\tFORM: {form_name}\tMACRO:")
                #                print(f'\n\n{current_form_macro_liquid_markup}')

                all_forms_macro_liquid_markup += current_form_macro_liquid_markup
                brand_forms_macro_liquid_markup += current_form_macro_liquid_markup

            ticket_html_combo = ""
            html_comment = ""
            whole_form_html = ""
            current_form_macro_liquid_markup = ""

        brand_forms_complete_json += (
            brand_forms_macro_liquid_markup + '", "public": False,"type": "comment"}}}'
            ""
        )

        #        print("\n=============================================================================================================\n")
        #        print('\nALL {} FORMS JSON:\n\n{}'.format(brand_name, brand_forms_complete_json))

        #        print("\n=============================================================================================================\n")
        #        print('\nALL {} FORMS MACRO LIQUID MARKUP:\n\n{}'.format(brand_name, brand_forms_macro_liquid_markup))

        if write_files == True:
            with open(json_output, "a") as json_output_file:
                json_output_file.write(f"{brand_forms_complete_json}")

            with open(macro_output, "a") as macro_output_file:
                macro_output_file.write(f"{brand_forms_macro_liquid_markup}")

print("Run complete; and files have been generated!\n")
# print("\n=============================================================================================================\n")
# print('\nALL FORMS MACRO LIQUID MARKUP:\n\n{}'.format(all_forms_macro_liquid_markup))
