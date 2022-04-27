# os套件用於取得環境變數
import os
# google sheet使用套件
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC
# flask套件
from flask import Flask, abort, request
# python內建時間模組
import time
# linebot相關套件
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# 試算表金鑰與網址
Json = 'informatics-and-social-service-4075fdd59a29.json'  # Json 的單引號內容請改成妳剛剛下載的那個金鑰
Url = ['https://spreadsheets.google.com/feeds'] # 這是goole sheet api 伺服器網址
# 連結至資料表
Connect = SAC.from_json_keyfile_name(Json, Url)
GoogleSheets = gspread.authorize(Connect)
# 開啟資料表及工作表
SheetCode = '1sXOLCHiH0n-HnmdiJzLVVDE5TjhoAPI3yN4Ku-4JUM4' # 這裡請輸入妳自己的試算表代號
Sheet = GoogleSheets.open_by_key(SheetCode)
SheetUrl = f"https://docs.google.com/spreadsheets/d/{SheetCode}/edit?usp=sharing"
Sheets = Sheet.sheet1

app = Flask(__name__)

# 從環境變數取得存取代幣(CHANNEL_ACCESS_TOKEN)以及秘鑰(CHANNEL_SECRET)
# 環境變數的設置已在其他檔案做完，用的會是在heroku部屬時輸入的變數
line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))

# 初始化時間的函數
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
# 宣告物件區
dataTitle = ["日期", "類別", "項目", "金額", 'reset=false']

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
                        uri=SheetUrl)
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

inquire_picker = TemplateSendMessage(
            alt_text='查詢形式選擇中',
            template=ButtonsTemplate(
                title='請選擇查詢形式',
                text='試問一個人手頭是有多緊才會回顧自已的帳本?',
                actions=[
                    PostbackAction(
                        label='按照月',
                        display_text='讓我看看(#`皿´)',
                        data='inquire_month'
                    ),
                    PostbackAction(
                        label='按照日期',
                        display_text='讓我看看(#`Д´)ﾉ',
                        data='inquire_date'
                    )
                ]
            )
        )

reset_picker = TemplateSendMessage(
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
                        display_text='不要!',
                        data='reset_false'
                    )
                ]
            )
        )


@app.route("/", methods=["GET", "POST"])
def callback():
    if request.method == "GET":
        return '<html><head><h1>Hello Heroku</h1></head></html>'
    if request.method == "POST":
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
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
        # 若輸入文字符合格式(項目=金額)則將資料寫入
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
                return_message.append(TextSendMessage(text=f"成功紀錄:\n{data[0]}在{data[2]}獲得了{int(data[3])}元"))
            elif Sheets.cell(len(datas), 3).value == '*待輸入':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先選擇 收入/支出:("))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先選擇時間:("))
        # 其他情況回傳訊息
        except ValueError:
            return_message.append(TextSendMessage(text="我聽不懂你在說什麼...\n要不要試試看下面這些功能~"))
        return_message.append(function_label)
        line_bot_api.reply_message(event.reply_token, return_message)
    else:
        print(event.message.type, type(event.message.type))
        if event.message.type == "sticker":
            sticker = StickerSendMessage(package_id=f"{event.message.package_id}", sticker_id=f"{event.message.sticker_id}")
        else:
            sticker = StickerSendMessage(package_id="11537",sticker_id="52002738")
        line_bot_api.reply_message(event.reply_token,[sticker, function_label])



@handler.add(PostbackEvent)
def Postback01(event):
    return_messages = []
    get_now_time()
    get_postback_data = event.postback.data

    date_picker = TemplateSendMessage(
        alt_text='選擇中...',
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
        # 指定date_picker的標題
        date_picker.template.title = '請選擇要紀錄的日期'
        # 指定date_picker回傳內容，將傳到下方record_date區塊
        date_picker.template.actions[0].data= "record_date"
        line_bot_api.reply_message(event.reply_token,date_picker)
    elif get_postback_data == 'record_date':
        # 取得日期並傳換格式
        date = str(event.postback.params['date'])
        date = date.replace('-', '/')
        datas = Sheets.get_all_values()
        if datas[-1][2][0] != '*' and datas[-1][3][0] != '*':
            # 一般情況將以得到的日期新增一行待輸入資料
            Sheets.append_row([date, '*待輸入', "*待輸入", '0'])
        else:
            # 其他情況將複寫一行待輸入資料
            Sheets.update_cell(len(datas), 1, date)
            Sheets.update_cell(len(datas), 2, '*待輸入')
            Sheets.update_cell(len(datas), 3, '*待輸入')
            Sheets.update_cell(len(datas), 4, '0')
        line_bot_api.reply_message(event.reply_token, income_expense_picker)
    # 接收上方income_expense_picker中的兩種回傳
    elif get_postback_data == 'record_expense' or get_postback_data == 'record_income':
        datas = Sheets.get_all_values()
        if datas[-1][3] == '0':
            # 確認有待輸入的資料，於是分別將試算表更新成兩種待輸入狀態
            if get_postback_data == 'record_expense':
                Sheets.update_cell(len(datas), 2, '*待輸入')
                Sheets.update_cell(len(datas), 3, '*待輸入支出')
                Sheets.update_cell(len(datas), 4, '0')
                # 傳送支出類別選擇選項
                line_bot_api.reply_message(event.reply_token, category_picker)
            else:
                Sheets.update_cell(len(datas), 2, '收入')
                Sheets.update_cell(len(datas), 3, '*待輸入收入')
                Sheets.update_cell(len(datas), 4, '0')
                # 直接請使用者寫入項目及金額(跳回@handler.add(MessageEvent)區塊)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=f'請輸入收入項目與金額。\n(ex:撿到一百塊=100)'))
        else:
            # 無待輸入的資料
            date_picker.template.title = '請選擇要紀錄的日期'
            date_picker.template.actions[0].data = "record_date"
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇日期"), date_picker])
    # 接收來自不同支出類別的回傳
    elif get_postback_data[:9] == "category_":
        datas = Sheets.get_all_values()
        if datas[-1][3] == '0' and datas[-1][2] == "*待輸入支出":
            # 確認過選擇了支出後，將對應的類別寫入google sheet
            category_mapping = {"eat":"飲食", "traffic":"交通", "entertain":"娛樂", "others":"其他"}
            Sheets.update_cell(len(datas), 2, f'{category_mapping[get_postback_data[9:]]}')
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text=f'請輸入支出項目與金額。\n(ex:我的豆花=30)'))
        elif datas[-1][3] == '0':
            # 沒有選擇收入/支出
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=f'請重新選擇支出/收入'), income_expense_picker])
        else:
            # 無待輸入的資料
            date_picker.template.title = '請選擇要紀錄的日期'
            date_picker.template.actions[0].data = "record_date"
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=f'請重新選擇日期'), date_picker])
    # 查詢資料
    elif get_postback_data == 'inquire':
        # 詢問使用者要用日期/月份查詢
        line_bot_api.reply_message(event.reply_token, inquire_picker)
    elif get_postback_data == "inquire_date" or get_postback_data == "inquire_month":
        # 接著詢問確切日期
        inquire_time_mapping = {"inquire_date":"日期", "inquire_month":"月份"}
        date_picker.template.title = f'請選擇要查詢的{inquire_time_mapping[get_postback_data]}'
        date_picker.template.actions[0].data = f"find_{get_postback_data[8:]}"
        line_bot_api.reply_message(event.reply_token, date_picker)
    elif get_postback_data == 'find_date' or get_postback_data == "find_month":
        # 做出對應的搜尋
        date = str(event.postback.params['date'])
        date = date.replace('-', '/')
        month = date[:7]
        time_mapping = {'find_date':date, "find_month":month}
        datas = Sheets.get_all_values()
        if get_postback_data == 'find_date':
            result = [data for data in datas if data[0] == date]
        else:
            result = [data for data in datas if data[0][:7] == month]
        if not result:
            return_messages.append(TextSendMessage(text=f"找不到{time_mapping[get_postback_data]}的資料"))
        else:
            sums = {"收支結算":0, "飲食":0, "交通":0, "娛樂":0, "其他":0, "收入":0}
            inquire_text = ""
            for bill in result:
                if bill[1][0] == '*' or bill[2][0] == '*':
                    continue
                for key in sums:
                    if bill[1] == key:
                        sums[key] += int(bill[3])
                sums["收支結算"] += int(bill[3])
                if int(bill[3]) < 0:
                    inquire_text += f"{bill[0]}在{bill[2]}花費了{-int(bill[3])}元({bill[1]})\n"
                else:
                    inquire_text += f"{bill[0]}在{bill[2]}存到了{bill[3]}元\n"
            return_messages.append(TextSendMessage(text=inquire_text))
            sum_text = ""
            for key, value in sums.items():
                sum_text += f"{time_mapping[get_postback_data]}的{key} : {value}\n"
            return_messages.append(TextSendMessage(text=sum_text))
    # 重置資料
    elif get_postback_data == 'reset':
        # 以表單中的(1, 5)作為重置表單的緩衝
        Sheets.update_cell(1, 5, 'reset=true')
        line_bot_api.reply_message(event.reply_token, reset_picker)
    elif get_postback_data == 'reset_true':
        # 收到"是"的選項時，只有在表單(1, 5)為'reset=true'才重置
        if str(Sheets.cell(1,5).value) == 'reset=true':
            Sheets.clear()
            Sheets.append_row(dataTitle)
            return_messages.append(TextSendMessage(text='重置成功'))
    elif get_postback_data == 'reset_false':
        # 將表單中的(1, 5)改回'reset=false'
        Sheets.update_cell(1,5,'reset=false')
        return_messages.append(TextSendMessage(text='看來你只是想試試看這個功能...'))
    else:
        # 未知的 postback事件
        return_messages.append(TextSendMessage(text='可以不要玩我的後台嗎?'))
    # 若前面沒有傳送過訊息，將訊息陣列補上"功能選項"並傳送給使用者(因為每個reply_token只能使用一次)
    return_messages.append(function_label)
    line_bot_api.reply_message(event.reply_token, return_messages)
