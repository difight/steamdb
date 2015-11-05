
import sqlite3

try:
    import steam
except ImportError:
    pass
import msgpack
import traceback
from datetime import datetime
from hashlib import md5

_connection = None
_connection_filename = "steam.db"


def set_database_path(filename):
    """Set the file path of the database you want to operate on."""
    global _connection_filename
    _connection_filename = filename


def get_connection(filename=None):
    """Return an open database connection."""
    global _connection
    
    if _connection:
        return _connection

    _connection = sqlite3.connect(filename or _connection_filename)
    _connection.execute(DB_STATEMENTS['create app id table'])
    _connection.execute(DB_STATEMENTS['create raw appinfo table'])
    _connection.execute(DB_STATEMENTS['create appinfo getter queue table'])
    _connection.commit()
    return _connection
    

def update_app_list():
    """Update the list of app IDs in the database.

    Makes the table if necessary.
    """

    c = get_connection()

    for game in steam.get_steam_apps_list():
        app_id = game['appid']
        name = game['name']

        c.execute(DB_STATEMENTS['insert app id'], (app_id, name))

    c.commit()
        
    return


def queue_app_update(app_id=None):
    """Queue some app_id for an update, to be retrieved later when the getter runs."""

    c = get_connection()
    if app_id is None:
        c.execute(DB_STATEMENTS['insert all app_ids in update queue'])
    else:
        c.execute(
            DB_STATEMENTS['insert app_id in update queue'],
            (app_id, ),
        )
        
    c.commit()

    return


def update_next_app():
    """Get an app_id from the update queue and fetch its details."""

    c = get_connection()
    cursor = c.cursor()
    rowid = None

    while not rowid:

        cursor.execute(
            DB_STATEMENTS['fetch next row from update queue']
        )
        row = cursor.fetchone()
        if not row:
            print("did not find any waiting updates")
            return None
        rowid = row[0]
    
        cursor.execute(
            DB_STATEMENTS['mark next row from update queue'],
            (rowid, ), 
        )
        if cursor.rowcount == 0:
            print("selected row was fetched by someone else")
            rowid = None
        
    cursor.execute(
        DB_STATEMENTS['get row from update queue'],
        (rowid, ), 
    )
    row = cursor.fetchone()
    c.commit()

    app_id = row[0]
    print("{}".format(app_id))

    try:
        res = get_raw_app_details(app_id)
        if res is None:
            res = {'error': True}
    except KeyboardInterrupt as e:
        raise e
    except:
        print("could not get app_id {}".format(app_id))
        traceback.print_exc()
        res = {'error': True}

    cursor.execute(
        DB_STATEMENTS['finish row from update queue'],
        (rowid, ),
    )
    c.commit()

    return res
    
    
def get_raw_app_details(app_id):
    """Retrieve the app details for a single app and put them in the DB (unparsed)."""
    
    app_info = steam.get_app_info(app_id)
    if app_info is None:
        print("  {} returned None".format(app_id))
        return None
    app_info_packed = msgpack.packb(app_info)

    c = get_connection()
    cursor = c.cursor()

    cursor.execute(
        DB_STATEMENTS['insert raw appinfo'],
        (app_id, app_info_packed, md5(app_info_packed).hexdigest(), ),
    )
    rowid = cursor.lastrowid
    c.commit()

    app_info['row_id'] = rowid
    
    return app_info


def load_raw_app_details(row_id):
    """Load the raw app details from the database."""

    c = get_connection()
    row = c.execute(
        DB_STATEMENTS['load raw appinfo row'],
        (row_id, ),
    ).fetchone()

    app_id, details, md5, update_time = row
    app_info = msgpack.unpackb(details)
    return app_id, app_info, update_time


def load_all_raw_app_details():
    """Return all raw app details from the database."""

    c = get_connection()
    rows = c.execute(
        DB_STATEMENTS['load all raw appinfo rows']
    )
    for row in rows:
        app_id, details, md5, update_time = row
        app_info = msgpack.unpackb(details)
        yield app_id, app_info, update_time


def parse_date(datestr):
    """Parse a release date into a python date."""

    formats = (
        '%d %b %Y', '%d %b, %Y',
        '%b %Y',
    )
    def parse_d(val, i=0):
        if i >= len(formats):
            return None
        try:
            return datetime.strptime(val, formats[i]).date()
        except ValueError:
            return parse_d(val, i + 1)

    release_date = parse_d(datestr)

    return release_date


DB_STATEMENTS = {
    'create app id table': """
    CREATE TABLE IF NOT EXISTS app_ids
    (
      app_id varchar NOT NULL UNIQUE,
      name varchar NOT NULL
    );
    """,

    'create raw appinfo table': """
    CREATE TABLE IF NOT EXISTS app_details_raw
    (
      app_id varchar NOT NULL,
      details varchar NOT NULL,
      md5 varchar NOT NULL UNIQUE,
      update_time timestamp NOT NULL
    );
    """,

    'create appinfo getter queue table': """
    CREATE TABLE IF NOT EXISTS app_details_get_queue
    (
      app_id varchar NOT NULL,
      queue_time timestamp NOT NULL,
      start_time timestamp,
      done_time timestamp,
      error_time timestamp
    );
    """,
    
    
    'insert app id': """
    INSERT OR IGNORE INTO app_ids (app_id, name) VALUES (?, ?);
    """,

    'insert raw appinfo': """
    INSERT OR IGNORE INTO app_details_raw (app_id, details, md5, update_time) VALUES (?,?,?, strftime('%s','now'));
    """,

    'load raw appinfo row': """
    SELECT * FROM app_details_raw WHERE rowid = ?;
    """,
    'load all raw appinfo rows': """
    SELECT app_id, details, md5, update_time FROM app_details_raw
    ORDER BY app_id;
    """,

    

    'insert app_id in update queue': """
    INSERT INTO app_details_get_queue (app_id, queue_time)
    VALUES (?, strftime('%s', 'now'))
    """,

    'insert all app_ids in update queue': """
    INSERT INTO app_details_get_queue(app_id, queue_time)
    SELECT app_id, strftime('%s', 'now') FROM app_ids
    """,
    
    'fetch next row from update queue': """
    SELECT rowid FROM app_details_get_queue
    WHERE start_time IS NULL
    ORDER BY queue_time
    LIMIT 1
    """,
    
    'mark next row from update queue': """
    UPDATE app_details_get_queue
    SET start_time = strftime('%s', 'now')
    WHERE rowid = ?
    """,
    
    'get row from update queue': """
    SELECT app_id
    FROM app_details_get_queue
    WHERE rowid = ?
    """,

    'finish row from update queue': """
    UPDATE app_details_get_queue
    SET done_time = strftime('%s', 'now')
    WHERE rowid = ?
    """,
    'finish row from update queue with error': """
    UPDATE app_details_get_queue
    SET error_time = strftime('%s', 'now')
    WHERE rowid = ?
    """,
    
    
}
