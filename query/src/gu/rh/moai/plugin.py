from moai import Plugin, name

class AusNCPlugin(Plugin):
    name('ausnc_plugin')

    def __init__(self, database, log, config):
        self.db = database
        self.log = log
        self.config = config

    def run(self, updated_ids):
        self.log.info('Hello %s from AusNCPlugin' % self.config['hello'])
        print 'Hello %s from AusNC plugin -> Updating %s records' % (
                self.config['hello'], len(updated_ids))
