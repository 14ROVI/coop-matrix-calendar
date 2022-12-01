import os
from io import BytesIO
import base64
import PyPDF2
from ics import Calendar, Event
from ics.timeline import Timeline
from datetime import date, datetime, timedelta, time
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

os.chdir(os.path.dirname(os.path.abspath(__file__))) # changes directory to this file.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
NAME_REGEX = re.compile(r"([a-zA-Z]+)\s*(?:(?:Off)|(?:Holiday)|(?:Transfer/Training)|(?:Absent)|(?:\d+))")
SCHEDULE_REGEX = re.compile(r"((?:\d{2}:\d{2} - \d{2}:\d{2}(?:\s\[\w\])*)|(?:Off)|(?:Holiday)|(?:Transfer/Training)|(?:Absent))")

calendars = {}
all_shifts = Calendar()

creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)    
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        token.write(creds.to_json())

try:
    service = build("gmail", "v1", credentials=creds)
    threads = service.users().threads().list(userId="me", q="from:noreply@southerncoops.co.uk").execute().get("threads", [])
    for thread in threads:
        tdata = service.users().threads().get(userId="me", id=thread["id"]).execute()
        
        tdata["messages"].sort(key = lambda m: int(m["internalDate"]))
        message = tdata["messages"][-1]
        
        for part in message["payload"]["parts"]:
            if part["filename"]:
                if "data" in part["body"]:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId="me", messageId=message['id'], id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode("UTF-8"))
                
                page_text = PyPDF2.PdfFileReader(BytesIO(file_data)).getPage(0).extractText()
                lines = page_text.splitlines()
                
                week_starting = lines[0].split()[-1]
                sd, sm, sy = week_starting.split("/")
                week_starting = date(int(sy), int(sm), int(sd))
                
                lines = [line for line in lines if ("Holiday" in line or "-" in line or "Off" in line) and ("Co-op" not in line)]
                lines = [" ".join(line.split()[:-1]) for line in lines if line.split()[-1].isdigit()]

                for line in lines:
                    name = NAME_REGEX.match(line).group(1)
                    match = SCHEDULE_REGEX.findall(line)
                
                    for i, shift in enumerate(match):
                        if shift not in {"Off", "Holiday", "Transfer/Training", "Absent"}:
                            shift_day = week_starting + timedelta(days=i)
                            training = "[T]" in shift
                            partial_holiday = "[H]" in shift
                            shift = shift.split("[")[0].split()
                            start = shift[0].split(":")
                            end = shift[-1].split(":")
                            shift_start = datetime.combine(shift_day, time(int(start[0]), int(start[1])))
                            shift_end = datetime.combine(shift_day, time(int(end[0]), int(end[1])))
                            
                            if name not in calendars:
                                calendars[name] = Calendar()
                            calendars[name].events.add(Event(
                                name="Work" + (" (Training)" * training) + (" (Part Holiday)" * partial_holiday),
                                begin=shift_start,
                                end=shift_end,
                                location="The Co-operative Food, 206-208 North St, Bedminster, Bristol BS3 1EN, UK",
                                uid=f"coop-matrix-{name.lower()}-{int(shift_start.timestamp())}",
                                last_modified=datetime.utcnow()
                            ))
                            all_shifts.events.add(Event(
                                name=f"{name}'s shift" + (" (Training)" * training) + (" (Part Holiday)" * partial_holiday),
                                begin=shift_start,
                                end=shift_end,
                                location="The Co-operative Food, 206-208 North St, Bedminster, Bristol BS3 1EN, UK",
                                uid=f"coop-matrix-{name.lower()}-{int(shift_start.timestamp())}",
                                last_modified=datetime.utcnow()
                            ))
except HttpError as error:
    print(f'An error occurred: {error}')

with open(f"calendars/all.ics", "w") as f:
    f.writelines(all_shifts)
    
for name in calendars:
    calendar: Calendar = calendars[name]
    
    for cal_event in calendar.events:
        shift_shared_with = []
        
        for other in calendars:
            if other == name: continue
            other_cal: Calendar = calendars[other]
            for other_cal_event in other_cal.events:
                if cal_event.intersects(other_cal_event):
                    shift_shared_with.append(other)
                    
        if len(shift_shared_with) > 0:
            cal_event.description = "Others on shift: " + ", ".join(shift_shared_with)
        
    with open(f"calendars/{name.lower()}.ics", "w") as f:
        f.writelines(calendar)