import web
import json
import gnsq
import sqlite3

urls = (
    '/', 'FrontPage',
    '/hello/(.*)', 'hello',
    '/terminal/(.*)/(on|off)', "Terminal"
)

CURRENT_STATE_FILE_PATH = "current_state.json"

app = web.application(urls, globals())
render = web.template.render('templates/')


def set_pins_state(state):
    print "set to:", state
    _csjson = json.dumps(state)
    text_file = open(CURRENT_STATE_FILE_PATH, "w")
    text_file.write(_csjson)
    text_file.close()

def get_pins_state():
    if os.path.exists(CURRENT_STATE_FILE_PATH):
        with open(CURRENT_STATE_FILE_PATH, "r") as text_file:
            _csjson = text_file.read().strip()
            if len(_csjson) > 0:
                return json.loads(_csjson)
    return "{}"



class FrontPage:
    def GET(self):
        #sql_conn = sqlite3.connect("data.db")
        #c = sql_conn.cursor()
        #c.execute("SELECT * FROM kv WHERE key='pins_state'")
        #k, v = c.fetchone()
        #sql_conn.close()
        #pins_state = json.loads(v)
        pins_state = get_pins_state()
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
                #sql_conn = sqlite3.connect("data.db")
                #c = sql_conn.cursor()
                #c.execute("UPDATE kv SET value=? WHERE key='pins_state'", [msg])
                #sql_conn.commit()
                #sql_conn.close()

                print 'got message:', msg
                print "pins state:", get_pins_state()
            except Exception, e:
                print e

        print "syncher started."
        reader.start()


#def setup_sqlite():
#    sql_conn = sqlite3.connect("data.db")
#    c = sql_conn.cursor()
#    c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT, value TEXT)")
#    sql_conn.commit()
#    sql_conn.close()


if __name__ == "__main__":

#    setup_sqlite()

    th = Syncher()
    th.daemon = True
    th.start()

    nsqd.publish('sinyu', 'sync')
    app.run()
