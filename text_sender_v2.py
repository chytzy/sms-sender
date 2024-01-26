from flask import Flask, render_template, request
from googleapiclient.discovery import build
import os
import os.path
import requests
import json

text_belt_api_key = os.environ["TEXT_BELT_API_KEY"]

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("text_message_form_v2.html")

conversation = {}

@app.route("/text-message", methods=["POST"])
def text():
    template = request.form.get("template")
    csv_data = request.form.get("data")

    keys = []
    data = []
    results = []

    csv_data = csv_data.replace('\r',"")
    rows = csv_data.split("\n")
 
    first_row = 0
    for row in rows:
        values = row.split(",")
        first_row = first_row + 1
        if first_row == 1:
            keys = values
        else:
            data_dictionary = {}
            key_index = 0
            for key in keys:
                data_dictionary[key] = values[key_index]
                key_index = key_index + 1
            data.append(data_dictionary)
    
    for each_message in data:
        print(each_message)
        resp = requests.post('https://textbelt.com/text', {
            "phone" : each_message["phone"],
            "message": template.format(**each_message),
            "key": text_belt_api_key,
            "replyWebhookUrl":"https://ff85-2601-681-5f00-1ac0-30da-a90f-d43b-7005.ngrok-free.app/"
    })
    payload = resp.json()
    #results.append(payload)
    print(resp.json())

    textId = payload.get("textId")
    conversation[textId] = []
    conversation[textId].append({"from": "system", "text": template.format(**each_message)})

    with open ("coversation.json","w") as file:
        json.dump(conversation, file, indent=4)

    
    service = build('sheets', 'v4')

    spreadsheets = service.spreadsheets()
    new_sheet_request = spreadsheets.create(body={"properties": {"title": "new"}})
    new_sheet_response = new_sheet_request.execute()

    spreadsheet_id = new_sheet_response["spreadsheetId"]

    values = [
        [textId,"","",
        "from: system","","",
        "text:",template.format(**each_message),""],
    ]

    body = {
    'values': values
    }
    
    new_sheet_response = new_sheet_request.execute()
    service.close()
    
    if payload["success"] == True:
        id = payload["textId"]
        return render_template("text_confirmation.html", text_id=id)
    else:
        error_message = payload["error"]
        return render_template("text_message_fail.html", error=error_message, results = results)
    
@app.route("/reply", methods=["POST"])
def replies():
    reply = (request.json)
    textId = reply.get("textId")
    conversation.get(textId).append({"from": reply.get("fromNumber"), "text": reply.get("text")})

    with open ("conversation.json", "w") as file:
        json.dump(conversation, file, indent=4)


    service = build('sheets', 'v4')

    spreadsheets = service.spreadsheets()
    new_sheet_request = spreadsheets.create(body={"properties": {"title": "new"}})
    new_sheet_response = new_sheet_request.execute()
    spreadsheet_id = new_sheet_response["spreadsheetId"]

    values = [
        ["from:", reply.get("fromNumber"),"",
        "text:",reply.get("text"),""],
    ],

    body = {
        'values': values
        }

    result = spreadsheets.values().append(
    spreadsheetId=spreadsheet_id,
    body=body
    ).execute()

    service.close()      
    return 


app.run(debug=True)