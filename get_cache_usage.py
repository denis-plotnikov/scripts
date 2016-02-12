#!/usr/bin/python
import psycopg2, datetime, time

print "Opened database successfully"

for i in range(1000):
	conn = psycopg2.connect(database="specdb", user="spec", host="dbserver1", port="5432")
	cur = conn.cursor()

	cur.execute('''SELECT 
			sum(heap_blks_read) as heap_read,
			sum(heap_blks_hit)  as heap_hit,
			sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as ratio
			FROM 
			pg_statio_user_tables;''')
	rows = cur.fetchall()
	for row in rows:
		print datetime.datetime.now().strftime("%H:%M:%S"), ": data cached (%) -- ", "%.2f" % row[2]

	time.sleep(5)
	conn.close()

