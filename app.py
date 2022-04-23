import os
import re
from datetime import datetime
# google sheet使用套件
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

from flask import Flask, abort, request
import time

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, TemplateSendMessage\
    ,StickerSendMessage, URIAction, PostbackAction, ButtonsTemplate, PostbackEvent, DatetimePickerTemplateAction, ConfirmTemplate

# 試算表金鑰與網址
Json = 'informatics-and-social-service-4075fdd59a29.json'  # Json 的單引號內容請改成妳剛剛下載的那個金鑰
Url = ['https://spreadsheets.google.com/feeds']
# 連結至資料表
Connect = SAC.from_json_keyfile_name(Json, Url)
GoogleSheets = gspread.authorize(Connect)
# 開啟資料表及工作表
SheetCode = '1sXOLCHiH0n-HnmdiJzLVVDE5TjhoAPI3yN4Ku-4JUM4' # 這裡請輸入妳自己的試算表代號
Sheet = GoogleSheets.open_by_key(SheetCode)  
SheetUrl = f"https://docs.google.com/spreadsheets/d/{SheetCode}/edit?usp=sharing"
Sheets = Sheet.sheet1

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))

ini_y, ini_m, ini_d = '2022', '06', '30'
def get_now_time():
    global ini_y, ini_m, ini_d
    now_time = time.localtime(time.time())
    ini_m = str(now_time.tm_mon)
    ini_d = str(now_time.tm_mday)
    ini_y = str(now_time.tm_year)
    if len(ini_m) == 1:
        ini_m = "0"+str(ini_m)
    if len(ini_d) == 1:
        ini_d = "0"+str(ini_d)

dataTitle = ["日期", "類別" "項目", "金額", 'reset=false']

function_label = TemplateSendMessage(
            alt_text='功能選項',
            template=ButtonsTemplate(
                title='功能選項',
                text='請選擇要使用的功能',
                actions=[
                    PostbackAction(
                        label='記帳',
                        display_text='我要記帳',
                        data='record'
                    ),
                    PostbackAction(
                        label='查詢',
                        display_text='我要查詢',
                        data='inquire'
                    ),
                    PostbackAction(
                        label='重置',
                        display_text='我要重置',
                        data='reset'
                    ),
                    URIAction(
                        label='查看表單',
                        uri='SheetUrl')
                ]
            )
        )

category_picker = TemplateSendMessage(
            alt_text='類別選擇中',
            template=ButtonsTemplate(
                title='請選擇消費類別',
                text='今天又在哪裡投資了',
                actions=[
                    PostbackAction(
                        label='飲食',
                        display_text='民以食為天^_^',
                        data='category_eat'
                    ),
                    PostbackAction(
                        label='交通',
                        display_text='停車坐愛楓林晚(　ﾟ∀ﾟ) ﾉ♡\n今天騎什麼車',
                        data='category_traffic'
                    ),
                    PostbackAction(
                        label='娛樂',
                        display_text='火山孝子｡:.ﾟヽ(*´∀`)ﾉﾟ.:｡',
                        data='category_entertain'
                    ),
                    PostbackAction(
                        label='其他',
                        display_text='別...別的地方啦',
                        data='category_others'
                    )

                ]
            )
        )

income_expense_picker = TemplateSendMessage(
            alt_text='選擇中...',
            template=ConfirmTemplate(
                text='收入/支出',
                title='請選擇收入或支出',
                actions=[
                    PostbackAction(
                        label='收入',
                        display_text='輸入中(收入)...',
                        data='record_income'
                    ),
                    PostbackAction(
                        label='支出',
                        display_text='輸入中(支出)...',
                        data='record_expense'
                    )
                ]
            )
        )

picker = TemplateSendMessage(
            alt_text='選擇中...',
            template=ConfirmTemplate(
                text='之前的資料都會不見喔!!',
                title='確定要重置所有紀錄嗎?',
                actions=[
                    PostbackAction(
                        label='是',
                        display_text='是',
                        data='reset_true'
                    ),
                    PostbackAction(
                        label='否',
                        display_text='否',
                        data='reset_false'
                    )
                ]
            )
        )


@app.route("/", methods=["GET", "POST"])
def callback():
    if request.method == "GET":
        return '<html><head><h1>Hello Heroku</h1><p>This is get method</p><a href="https://github.com/NCULineBot/Flask-LINE-Bot-Heroku/">Press me to view sourcecode</a></head></html>'
    if request.method == "POST":
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        # 寫入
        if Sheets.get_all_values() == []:
            Sheets.append_row(dataTitle)
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)

        return "OK"


@handler.add(MessageEvent)
def handle_message(event):
    return_message = []
    if event.message.type == "text":
        get_message = event.message.text
        try:
            item, money = str(get_message).split('=')
            money = int(money)
            datas = Sheets.get_all_values()
            if money <= 0:
                return_message.append(TextSendMessage(text="請輸入有效的金額:("))
            elif Sheets.cell(len(datas), 3).value == '*待輸入支出':
                Sheets.update_cell(len(datas), 3, item)
                Sheets.update_cell(len(datas), 4, str(-money))
                data = Sheets.get_all_values()[-1]
                return_message.append(TextSendMessage(text=f"成功紀錄:\n{data[0]}在{data[1]}的{data[2]}花費了{-int(data[3])}元"))
            elif Sheets.cell(len(datas), 3).value == '*待輸入收入':
                Sheets.update_cell(len(datas), 3, item)
                Sheets.update_cell(len(datas), 4, str(money))
                data = Sheets.get_all_values()[-1]
                return_message.append(TextSendMessage(text=f"成功紀錄:\n{data[0]}在{data[1]}的{data[2]}獲得了{int(data[3])}元"))
            elif Sheets.cell(len(datas), 3).value == '*待輸入':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先選擇 收入/支出:("))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先選擇時間:("))
        except ValueError:
            return_message.append(TextSendMessage(text="我聽不懂你在說什麼...\n要不要試試看下面這些功能~"))
        # Send To Line
        return_message.append(function_label)
        line_bot_api.reply_message(event.reply_token, return_message)
    else:
        print(event.message.type, type(event.message.type))
        if re.match(str(event.message.type), "sticker"):
            sticker = StickerSendMessage(package_id=f"{event.message.package_id}", sticker_id=f"{event.message.sticker_id}")
        else:
            sticker = StickerSendMessage(package_id="11537",sticker_id="52002738")
        line_bot_api.reply_message(event.reply_token,[sticker, function_label])



@handler.add(PostbackEvent)
def Postback01(event):
    return_messanges = []
    get_now_time()
    get_postback_data = event.postback.data

    date_picker = TemplateSendMessage(
        alt_text='紀錄中...',
        template=ButtonsTemplate(
            text='西元年/月/日',
            title='請選擇日期',
            actions=[
                DatetimePickerTemplateAction(
                    label='按我選擇日期',
                    data='record_date',
                    mode='date',
                    initial=f'{ini_y}-{ini_m}-{ini_d}',
                    min='2020-01-01',
                    max='2099-12-31'
                )
            ]
        )
    )
    # 紀錄資料
    if get_postback_data == 'record':
        date_picker.template.title = '請選擇要紀錄的日期'
        date_picker.template.actions[0].data= "record_date"
        line_bot_api.reply_message(event.reply_token,date_picker)
    elif get_postback_data == 'record_date':
        date = str(event.postback.params['date'])
        date = date.replace('-', '/')
        datas = Sheets.get_all_values()
        if datas[-1][2][0] != '*' and datas[-1][3][0] != '*':
            Sheets.append_row([date, '*待輸入', "*待輸入", '0'])
        else:
            Sheets.update_cell(len(datas), 1, date)
            Sheets.update_cell(len(datas), 2, '*待輸入')
            Sheets.update_cell(len(datas), 3, '*待輸入')
            Sheets.update_cell(len(datas), 4, '0')
        line_bot_api.reply_message(event.reply_token, category_picker)
        #line_bot_api.reply_message(event.reply_token, income_expense_picker)
    elif get_postback_data[:9] == "category_":
        datas = Sheets.get_all_values()
        if datas[-1][4] == '0':
            Sheets.update_cell(len(datas), 2, f'{get_postback_data[9:]}')
            Sheets.update_cell(len(datas), 3, '*待輸入')
            Sheets.update_cell(len(datas), 4, '0')
            line_bot_api.reply_message(event.reply_token, income_expense_picker)
        else:
            date_picker.template.title = '請選擇要紀錄的日期'
            date_picker.template.actions[0].data = "record_date"
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇日期"), date_picker])
    elif get_postback_data == 'record_income' or get_postback_data == 'record_expense':
        mapping = {'record_income':("收入", "(ex:撿到一百塊=100)"), 'record_expense':("支出", "(ex:我的豆花=30)")}
        datas = Sheets.get_all_values()
        if datas[-1][4] == '0' and datas[-1][1][0] != "*":
            Sheets.update_cell(len(datas), 3, f'*待輸入{mapping[get_postback_data[0]]}')
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請輸入{mapping[get_postback_data[0]]}項目與金額。\n{mapping[get_postback_data[1]]}'))
        elif datas[-1][4] == '0':
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=f'請重新選擇類別'), category_picker])
        else:
            date_picker.template.title = '請選擇要紀錄的日期'
            date_picker.template.actions[0].data = "record_date"
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=f'請重新選擇日期'), date_picker])
    # 查詢資料
    elif get_postback_data == 'inquire':
        date_picker.template.title = '請選擇要查詢的日期'
        date_picker.template.actions[0].data = "inquire_date"
        line_bot_api.reply_message(event.reply_token,date_picker)
    elif get_postback_data == 'inquire_date':
        date = str(event.postback.params['date'])
        date = date.replace('-', '/')
        datas = Sheets.get_all_values()
        result = []
        for data in datas:
            if data[0] == date:
                result.append(data)
        if not result:
            return_messanges.append(TextSendMessage(text=f"找不到{date}的資料"))
        else:
            s = 0
            for re in result:
                s += int(re[2])
                if re[1][0] == '*':
                    continue
                if int(re[2]) < 0:

                    return_messanges.append(TextSendMessage(text=f"{re[0]}在{re[1]}項目中花費了{-int(re[2])}元"))
                else:
                    return_messanges.append(TextSendMessage(text=f"{re[0]}在{re[1]}項目中存到了{re[2]}元"))
            if s >= 0:
                return_messanges.append(TextSendMessage(text=f"{re[0]}的收支結算:+{s}"))
            else:
                return_messanges.append(TextSendMessage(text=f"{re[0]}的收支結算:{s}"))
    # 重置資料
    elif get_postback_data == 'reset':
        Sheets.update_cell(1, 5, 'reset=true')
        line_bot_api.reply_message(event.reply_token, reset_picker)
    elif get_postback_data == 'reset_true':
        if str(Sheets.cell(1,5).value) == 'reset=true':
            Sheets.clear()
            Sheets.append_row(dataTitle)
            return_messanges.append(TextSendMessage(text='重置成功'))
    elif get_postback_data == 'reset_false':
        Sheets.update_cell(1,5,'reset=false')
        return_messanges.append(TextSendMessage(text='看來你只是想試試看這個功能...'))
    else:
        print("Unexpect PostbackEvent!!!")
    return_messanges.append(function_label)
    line_bot_api.reply_message(event.reply_token, return_messanges)
