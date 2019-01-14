#!/usr/bin/env python3

from urllib import request
import ssl, json, jinja2
import pytz, datetime

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


TIMEZONE_NAME = "Europe/Berlin"


TEMPLATE_FILE = "template.jinja2"
SUBJECT = "Icinga Daily Report"

SERVER = "https://<ICINGA_SERVER>:5665"
SERVICES_URL = "/v1/objects/services?filter=service.state!=ServiceOK"
HTTP_USER = "<API_USER_ACCOUNT>"
HTTP_PASSWORD = "API_USER_PASSWORD"
USERS = ["user@example.com", "user2@benocs.com"]

STATES = ["Ok", "Warning", "CRITICAL"]

# Usefull variables initialized
timezone = pytz.timezone(TIMEZONE_NAME)

# Prepare the urllib for using the authenticator
password_mgr = request.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, SERVER, HTTP_USER, HTTP_PASSWORD)

handler = request.HTTPBasicAuthHandler(password_mgr)
opener = request.build_opener(handler)

ssl._create_default_https_context = ssl._create_unverified_context
# Fetch the data and parse them
raw_data = opener.open(SERVER + SERVICES_URL)

json = json.load(raw_data)

hosts = {}

for service in json["results"]:
    if hosts.get(service["attrs"]["host_name"]) is None:
        hosts[service["attrs"]["host_name"]] = []
    hosts[service["attrs"]["host_name"]].append({
        "name": service["attrs"]["display_name"],
        "system_id" : service["name"],
        "stdout" : service["attrs"]["last_check_result"]["output"]
    })
# Rendering
template_file = open(TEMPLATE_FILE, "r")
template = jinja2.Template(template_file.read())
template_data = {
    "hosts": hosts,
    "datetime": datetime.datetime.now(tz=timezone),
    "STATES": STATES
}
message = template.render(template_data)
print (SUBJECT)
print ("==============================")
print (message)

# Send the e-mail
for address in USERS:
    fromaddr = "monitoring@icinga.benocs.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = address
    msg['Subject'] = SUBJECT

    body = message
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP("mail.benocs.com")
    server.sendmail(fromaddr, address, msg.as_string())
    server.quit()

