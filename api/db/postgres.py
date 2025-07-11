import psycopg2

PG_CONN_STR = "postgresql://neondb_owner:npg_YarpRPv27KLc@ep-cool-bonus-ab2dfy4h-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_pg_conn():
    return psycopg2.connect(PG_CONN_STR)