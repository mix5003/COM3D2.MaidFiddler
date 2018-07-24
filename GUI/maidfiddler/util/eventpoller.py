import gevent
import zerorpc
import maidfiddler.util.util as util

class EventPoller(object):
    def __init__(self, port):
        self.port = port
        self.event_handlers = dict()
        self.server = None
        self.ge_server = None
        self.job_stack = []

    def event_loop(self):
        while util.APP_RUNNING:
            if len(self.job_stack) != 0:
                for event_name, args in self.job_stack:
                    for handler in self.event_handlers[event_name]:
                        handler(args)
                self.job_stack.clear()
            gevent.sleep(0.1)

    def start(self, client, group):
        print("Initializing event poller")
        self.server = zerorpc.Server(self)
        self.server.bind(f"tcp://{util.CLIENT_ADDRESS}:{self.port}")
        self.ge_server = group.spawn(self.server.run)
        group.spawn(self.event_loop)
        client.SubscribeToEventHandler(f"tcp://{util.CLIENT_ADDRESS}:{self.port}")
    
    def dispose_handler(self):
        # TODO: When called from COM, add disconnected message
        self.stop()

    def stop(self):
        try:
            gevent.kill(self.ge_server)
        except Exception:
            print("Closed gevent!")
        finally:
            self.server.close()

    def on(self, event_name, handler):
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)

    def emit(self, events):
        for event in events:
            if event["event_name"] in self.event_handlers:
                self.job_stack.append((event["event_name"], event["args"]))