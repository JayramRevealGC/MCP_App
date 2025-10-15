import psycopg

def get_connection():
    return psycopg.connect(
        host="aies-serverless-clone-cluster.cluster-ro-cjflqg3bd6i9.us-gov-east-1.rds.amazonaws.com",
        port=5432,
        user="postgres",
        password="RootNew123!!",
        dbname="space_ite_4",
    )

conn = get_connection()
with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
    sql = "SELECT * FROM space_product_aies.item_kaus LIMIT 10;"
    cur.execute(sql)
    rows = cur.fetchall()
    print(rows)