import os.path
import flask
import sqlite3

from flask import Flask, render_template, request, redirect, url_for
from os.path import join, relpath
from glob import glob

# インスタンス化
app = Flask(__name__)

# ファイルパス
PATH = "F:\\env1\\HackLog\\static\\logs\\"
FILE_NOT_FOUND_FILE = '/static/logs/404/404.log'

# DB
DATABASE = "matsuno.db"

# 年取得用SQL
YEAR_GET = 'select substr(name, 0, 5) from fileList where name like ? group by substr(name, 0, 5)'
# 月取得用SQL
MONTH_GET = 'select substr(name, 5, 2) from fileList where name like ? group by substr(name, 5, 2)'
# 日取得用SQL
DAY_GET = 'select substr(name, 7, 2) from fileList where name like ? group by substr(name, 7, 2)'
# ファイルリスト取得用SQL
FILELIST_GET = 'select substr(name, 10), size from fileList where name like ? group by substr(name, 10)'
# ファイル取得用SQL
FILE_GET = 'select name from fileList where name = ?'

# index
@app.route('/')
def index():
    title = "HackLog TOPページ"
    return render_template('index.html', title = title)

@app.route('/app/')
def year():
    title = "年選択画面"

    # 接続用カーソルを取得
    cursor = get_request_connection().cursor()
    # 年のみを取得
    cursor.execute(YEAR_GET, ('%.log', ))
    
    yearList = set()
    # 年をsetに入れる
    for row in cursor.fetchall():
        yearList.add(row[0])

    yearList = sorted(yearList)

    if len(yearList) == 0:
        # 404エラーを出す
        return render_template('404.html',
                                title = title,
                                fullFileName = FILE_NOT_FOUND_FILE,), 404

    return render_template('year.html',
                             title = title,
                             yearList = yearList)

@app.route('/app/<year>')
def month(year):
    title = "月選択画面"

    # 接続用カーソルを取得
    cursor = get_request_connection().cursor()
    # 月のみを取得
    cursor.execute(MONTH_GET, ('{}%.log'.format(year), ))
    
    monthList = set()
    
    # 月をsetに入れる
    for row in cursor.fetchall():
        monthList.add(row[0])
    
    monthList = sorted(monthList)
    if len(monthList) == 0:
        # 404エラーを出す
        return render_template('404.html',
                                title = title,
                                fullFileName = FILE_NOT_FOUND_FILE,), 404
    
    return render_template('month.html',
                            title = title,
                            year = year,
                            monthList = monthList)

@app.route('/app/<year>/<month>')
def day(year, month):
    title = "日選択画面"
    
    # 接続用カーソルを取得
    cursor = get_request_connection().cursor()

    # 日のみを取得
    cursor.execute(DAY_GET, ('{}%.log'.format(year + month), ))

    dayList = set()
    
    # 日をsetに入れる
    for row in cursor.fetchall():
        dayList.add(row[0])
    
    dayList = sorted(dayList)
    
    if len(dayList) == 0:
        # 404エラーを出す
        return render_template('404.html',
                                title = title,
                                fullFileName = FILE_NOT_FOUND_FILE,), 404
    
    return render_template('day.html',
                            title = title,
                            year = year,
                            month = month,
                            dayList = dayList)

@app.route('/app/<year>/<month>/<day>')
def fileList(year, month, day):
    title = "ファイル選択画面"
    
    # 接続用カーソルを取得
    cursor = get_request_connection().cursor()
    
    # ファイル名(日付無)を取得
    cursor.execute(FILELIST_GET, ('{}%.log'.format(year + month + day), ))
    
    fileList = set()
    
    # ファイル名をsetに入れる
    for row in cursor.fetchall():
        name = row[0]
        size = row[1]
        fileList.add(MyFile(name, size))
    
    fileList = sorted(fileList, key = lambda x : x.name)
    
    if len(fileList) == 0:
        # 404エラーを出す
        return render_template('404.html',
                                title = title,
                                fullFileName = FILE_NOT_FOUND_FILE,), 404
    
    return render_template('fileList.html',
                            title = title,
                            year = year,
                            month = month,
                            day = day,
                            fileList = fileList)


@app.route('/app/<year>/<month>/<day>/<file>')
def execute(year, month, day, file):
    title = "ログ実行画面"
    
    # 接続用カーソルを取得
    cursor = get_request_connection().cursor()
    
    # ファイル名(日付無)を取得
    cursor.execute(FILE_GET, (year + month + day + '-' + file, ))
    try:
        fileName = cursor.fetchall()[0][0]
        fullFileName = '/static/logs/' + fileName
    except IndexError:
        # 404エラーを出す
        return render_template('404.html',
                                title = title,
                                fullFileName = FILE_NOT_FOUND_FILE,), 404
    
    return render_template('execute.html',
                            title = title,
                            year = year,
                            month = month,
                            day = day,
                            fileName = fileName,
                            fullFileName = fullFileName,)


#これを呼び出すとDBのテーブルをリフレッシュする
@app.route('/refresh')
def matsuno():
    con = get_request_connection()
    cursor = con.cursor()
    
    # DB初期化
    cursor.execute('drop table fileList')
    cursor.execute('create table fileList(name text, size int)')
    
    files = [relpath(x, PATH) for x in glob(join(PATH, "*.log"))]
    fileList = set()
    
    # ファイル名をsetに入れる
    for file in sorted(files):
        name = file
        size = os.path.getsize(PATH + file)
        fileList.add(MyFile(name, size))
    
    for myFile in fileList:
        cursor.execute("insert into fileList values(?, ?)", (myFile.name, myFile.size))
    
    con.commit()
    
    return render_template('404.html',title = 'OK',fullFileName = FILE_NOT_FOUND_FILE,), 200

def request_has_connection():
    return hasattr(flask.g, 'dbconn')


def get_request_connection():
    if not request_has_connection():
        flask.g.dbconn = sqlite3.connect(DATABASE)
    return flask.g.dbconn


@app.teardown_request
def close_db_connection(ex):
    if request_has_connection():
        conn = get_request_connection()
        conn.close()


class MyFile:
    def __init__(self, name, size):
        self.name = name
        self.size = size


if __name__ == "__main__":
    app.run(host = '127.0.0.1')




