import os
import shutil

from moai import ConfigurationProfile, name
from moai.update import DatabaseUpdater
from moai.database.sqlite import SQLiteDatabase
from moai.server import Server, FeedConfig
from moai.http.cherry import start_server
from org.ausnc.moai.provider import ORDFContentProvider
from org.ausnc.moai.content import RDFContentObject


class AusNCConfigurationProfile(ConfigurationProfile):
    """Subclass this to create custom profiles.
    use the name directive so it will be automaticly
    registered in the framework:

    class MyConfiguration(ConfigurationProfile):
        name('my_configuration')

    """

    name("ausnc_configuration")

    # log
    # config

    def get_content_provider(self):
        provider = ORDFContentProvider(self.config)
        provider.set_logger(self.log)
        return provider

    def get_content_object(self):
        raise NotImplementedError

    def get_database_updater(self):
        dbnewpath = self.config.get('dbnewpath', '/tmp/ausnc.new.db')
        if os.path.isfile(dbnewpath):
            self.log.warning('removing old %s' % dbnewpath)
            os.remove(dbnewpath)

        return DatabaseUpdater(self.get_content_provider(),
                               RDFContentObject,
                               SQLiteDatabase(dbnewpath, 'w'),
                               self.log)

    def get_database(self):
        dbnewpath = self.config.get('dbnewpath', '/tmp/ausnc.new.db')
        dbpath = self.config.get('dbpath', '/tmp/ausnc.db')
        if os.path.isfile(dbnewpath):
            shutil.move(dbnewpath, dbpath)

        return SQLiteDatabase(dbpath, 'r')

    def get_server(self):
        server_url = 'http://%s:%s/repo' % (self.config['host'],
                                            self.config['port'])
        asset_path = os.path.join(os.path.dirname(__file__),
                                  'example_data',
                                  'assets')

        server = Server(server_url,
                        self.get_database())
        server.add_config(
            FeedConfig('ausnc',
                       'An example OAI Server',
                       '%s/ausnc' % server_url,
                       self.log,
                       base_asset_path=asset_path,
        #sets_allowed=[],
                       metadata_prefixes=['oai_dc', 'rif', 'mods', 'didl']))

        return server

    def start_server(self):
        raise NotImplementedError

    def start_development_server(self):
        start_server('0.0.0.0', self.config['port'], 10,
                     'repo', self.get_server())
