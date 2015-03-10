import web
import json
import gnsq

urls = (
    '/', 'FrontPage',
    '/hello/(.*)', 'hello',
    '/lampu_teras/(\\d+)/(on|off)', "LampuTeras"
)

app = web.application(urls, globals())
render = web.template.render('templates/')

class hello:        
    def GET(self, name):
        if not name: 
            name = 'world'
        return 'Hello, ' + name + '!'

class FrontPage:
    def GET(self):
        return render.index()

class LampuTeras:
    conn = gnsq.Nsqd(address='localhost', http_port=4151)

    def POST(self, pos, state):
        self.conn.publish('sinyu', 'lampu_teras_%s_%s' % (pos, state))
        return "OK"
        

if __name__ == "__main__":
    app.run()
