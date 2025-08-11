import mysql.connector
from utils.logger import log

try:
    connection = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="test_user",
        password="test_password",
        database="test_db"
    )
    if connection.is_connected():
        print("MySQL 데이터베이스에 성공적으로 연결되었습니다.")
except Exception as e:
    log.error(f"데이터베이스 연결 오류: {e}")
    print(f"오류 발생: {e}")
finally:
    if connection.is_connected():
        connection.close()
