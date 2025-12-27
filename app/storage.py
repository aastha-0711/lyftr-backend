from datetime import datetime
from app.models import get_db


def insert_message(message: dict) -> str:
    """
    Insert a message into DB.
    Returns:
      - "created" if inserted
      - "duplicate" if message_id already exists
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO messages (
                message_id,
                from_msisdn,
                to_msisdn,
                ts,
                text,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message["message_id"],
                message["from"],
                message["to"],
                message["ts"],
                message.get("text"),
                datetime.utcnow().isoformat() + "Z",
            ),
        )
        conn.commit()
        return "created"

    except Exception:
        # message_id already exists (idempotent)
        return "duplicate"

    finally:
        conn.close()


def list_messages(
    limit: int,
    offset: int,
    from_msisdn: str | None,
    since: str | None,
    q: str | None,
):
    conn = get_db()
    cursor = conn.cursor()

    filters = []
    params = []

    if from_msisdn:
        filters.append("from_msisdn = ?")
        params.append(from_msisdn)

    if since:
        filters.append("ts >= ?")
        params.append(since)

    # ✅ FIX: handle NULL text safely
    if q:
        filters.append("LOWER(COALESCE(text, '')) LIKE ?")
        params.append(f"%{q.lower()}%")

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    # total count (ignores limit/offset)
    total_query = f"SELECT COUNT(*) FROM messages {where_clause}"
    total = cursor.execute(total_query, params).fetchone()[0]

    # paginated data
    data_query = f"""
        SELECT message_id, from_msisdn, to_msisdn, ts, text
        FROM messages
        {where_clause}
        ORDER BY ts ASC, message_id ASC
        LIMIT ? OFFSET ?
    """
    rows = cursor.execute(
        data_query, params + [limit, offset]
    ).fetchall()

    conn.close()

    messages = [
        {
            "message_id": row["message_id"],
            "from": row["from_msisdn"],
            "to": row["to_msisdn"],
            "ts": row["ts"],
            "text": row["text"],
        }
        for row in rows
    ]

    return messages, total


def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    total_messages = cursor.execute(
        "SELECT COUNT(*) FROM messages"
    ).fetchone()[0]

    senders_count = cursor.execute(
        "SELECT COUNT(DISTINCT from_msisdn) FROM messages"
    ).fetchone()[0]

    rows = cursor.execute("""
        SELECT from_msisdn, COUNT(*) AS count
        FROM messages
        GROUP BY from_msisdn
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()

    messages_per_sender = [
        {"from": row["from_msisdn"], "count": row["count"]}
        for row in rows
    ]

    row = cursor.execute(
        "SELECT MIN(ts), MAX(ts) FROM messages"
    ).fetchone()

    conn.close()

    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": messages_per_sender,
        "first_message_ts": row[0],
        "last_message_ts": row[1],
    }
