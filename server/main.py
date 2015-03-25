import web
import json
import gnsq
import sqlite3

urls = (
    '/', 'FrontPage',
    '/hello/(.*)', 'hello',
    '/terminal/(.*)/(on|off)', "Terminal"
)

myglobals = {
    'PINS_STATE' : {}
}

app = web.application(urls, globals())
render = web.template.render('templates/', globals=myglobals)


def set_pins_state(state):
    global myglobals
    print "set to:", state
    myglobals['PINS_STATE'] = state

def get_pins_state():
    global myglobals
    return myglobals['PINS_STATE']

class FrontPage:
    def GET(self):
        sql_conn = sqlite3.connect("data.db")
        c = sql_conn.cursor()
        c.execute("SELECT * FROM kv WHERE key='pins_state'")
        k, v = c.fetchone()
        sql_conn.close()
        pins_state = json.loads(v)
        return render.index(pins_state,v)


nsqd = gnsq.Nsqd(address='localhost', http_port=4151)


class Terminal:

    def POST(self, name, state):
#        data = web.input()
#        prefix = data.prefix
        nsqd.publish('sinyu', '%s:%s' % (name, state))
        return "OK"


import threading
class Syncher(threading.Thread):

    def run(self):

        reader = gnsq.Reader("sinyu_server","all","localhost:4150")

        @reader.on_message.connect
        def handler(reader, message):
            try:
                msg = message.body.strip()
                set_pins_state(json.loads(msg))
                sql_conn = sqlite3.connect("data.db")
                c = sql_conn.cursor()
#                c.execute("DELETE FROM kv WHERE key='pins_state'")
#                c.execute("INSERT INTO kv VALUES('pins_state',?)", [msg])
                c.execute("UPDATE kv SET value=? WHERE key='pins_state'", [msg])
                sql_conn.commit()
                sql_conn.close()
                print 'got message:', msg
                print "pins state:", get_pins_state()
            except Exception, e:
                print e

        print "syncher started."
        reader.start()


def setup_sqlite():
    sql_conn = sqlite3.connect("data.db")
    c = sql_conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT, value TEXT)")
    sql_conn.commit()
    sql_conn.close()

if __name__ == "__main__":

    setup_sqlite()

    th = Syncher()
    th.daemon = True
    th.start()

    nsqd.publish('sinyu', 'sync')
    app.run()
