import pymysql.cursors

connect = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='2001',
    db='raz_mobile',
    cursorclass=pymysql.cursors.DictCursor

)

cursor = connect.cursor()