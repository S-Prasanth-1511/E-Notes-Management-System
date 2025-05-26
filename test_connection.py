import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',  # your password if any
        database='enotes'
    )
    print("Connection successful!")
except Exception as e:
    print(e)
