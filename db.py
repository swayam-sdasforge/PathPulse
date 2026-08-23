import os
import pyexasol

def get_connection():
    """
    Creates and returns a connection to the Exasol database using
    credentials from environment variables.
    """
    dsn = os.environ.get('EXA_DSN', '127.0.0.1:8563')
    user = os.environ.get('EXA_USER')
    password = os.environ.get('EXA_PASSWORD')
    
    if not user or not password:
        raise ValueError("EXA_USER and EXA_PASSWORD environment variables must be set.")
        
    import ssl
    return pyexasol.connect(dsn=dsn, user=user, password=password, websocket_sslopt={'cert_reqs': ssl.CERT_NONE})

def insert_incident(incident_date, description, location, damage_type, priority_score):
    """
    Inserts a new incident into the CIVIC.ROAD_INCIDENTS table.
    """
    query = """
        INSERT INTO CIVIC.ROAD_INCIDENTS 
        (incident_date, description, location, damage_type, priority_score)
        VALUES ({incident_date}, {description}, {location}, {damage_type}, {priority_score})
    """
    
    with get_connection() as conn:
        conn.execute(query, {
            'incident_date': incident_date,
            'description': description,
            'location': location,
            'damage_type': damage_type,
            'priority_score': priority_score
        })
def insert_incidents_batch(incidents):
    """
    Inserts a list of incidents in bulk.
    incidents should be an iterable of tuples matching the column order:
    (incident_date, description, location, damage_type, priority_score)
    """
    if not incidents:
        return
        
    query_base = "INSERT INTO CIVIC.ROAD_INCIDENTS (incident_date, description, location, damage_type, priority_score) VALUES "
    
    # We will construct the VALUES part and flatten parameters
    placeholders = []
    params = {}
    
    for i, inc in enumerate(incidents):
        placeholders.append(f"({{d{i}}}, {{desc{i}}}, {{loc{i}}}, {{dt{i}}}, {{ps{i}}})")
        params[f"d{i}"] = inc[0]
        params[f"desc{i}"] = inc[1]
        params[f"loc{i}"] = inc[2]
        params[f"dt{i}"] = inc[3]
        params[f"ps{i}"] = inc[4]
        
    query = query_base + ", ".join(placeholders)
    
    with get_connection() as conn:
        conn.execute(query, params)

def get_summary_stats():
    """
    Aggregates total incidents by damage type and priority score.
    Returns the results as a pandas DataFrame.
    """
    query = """
        SELECT damage_type, priority_score, COUNT(*) as total_incidents
        FROM CIVIC.ROAD_INCIDENTS
        GROUP BY damage_type, priority_score
        ORDER BY total_incidents DESC
    """
    
    with get_connection() as conn:
        stmt = conn.execute(query)
        data = stmt.fetchall()
        import pandas as pd
        return pd.DataFrame(data, columns=['damage_type', 'priority_score', 'total_incidents'])

def get_kpis():
    """
    Fetches high-level KPIs: total incidents and critical anomalies (priority >= 4).
    """
    query = """
        SELECT 
            COUNT(*) as total_incidents,
            SUM(CASE WHEN priority_score >= 4 THEN 1 ELSE 0 END) as critical_anomalies
        FROM CIVIC.ROAD_INCIDENTS
    """
    with get_connection() as conn:
        stmt = conn.execute(query)
        row = stmt.fetchone()
        return {
            'total_incidents': row[0] or 0,
            'critical_anomalies': row[1] or 0
        }

def get_recent_incidents(limit=100):
    """
    Fetches the most recent raw entries from the database.
    """
    query = f"""
        SELECT incident_date, description, location, damage_type, priority_score
        FROM CIVIC.ROAD_INCIDENTS
        ORDER BY id DESC
        LIMIT {limit}
    """
    with get_connection() as conn:
        stmt = conn.execute(query)
        data = stmt.fetchall()
        import pandas as pd
        return pd.DataFrame(data, columns=['Incident Date', 'Description', 'Location', 'Damage Type', 'Priority Score'])
