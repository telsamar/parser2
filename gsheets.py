import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def set_permission(drive_service, file_id, email):
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    try:
        drive_service.permissions().create(fileId=file_id, body=permission).execute()
        print(f"Разрешение установлено для {email}")
    except Exception as e:
        print(f"Ошибка разрешения для {email}. Причина: {e}")

def find_or_create_sheet():
    creds = Credentials.from_service_account_file('newtest-401506-8c354a45d760.json',
                                                  scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    title = f"WOMANa-WEAR-{datetime.datetime.now().strftime('%Y-%m')}"

    results = drive_service.files().list(q=f"name='{title}'", fields="files(id, name)").execute()
    items = results.get('files', [])

    if items:
        print(f"Таблица уже существует с ID: {items[0]['id']}")
        file_id = items[0]['id']
        set_permission(drive_service, file_id, "testarmen4@gmail.com")
        return file_id

    else:
        print("Создание новой таблицы.")
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        file_id = spreadsheet.get("spreadsheetId")
        set_permission(drive_service, file_id, "testarmen4@gmail.com")
        return file_id

if __name__ == '__main__':
    find_or_create_sheet()
