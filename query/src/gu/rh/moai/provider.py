from gu.rh.moai.content import RDFContentObject
from gu.rh.moai.namespace import ANDS
from rdflib import URIRef, Graph, Literal
from subprocess import Popen, PIPE
from pkg_resources import resource_string


class JenaHelper(object):

    def __init__(self, config):
        self.jenaroot = config['jenaroot']
        self.jenaconfig = config['jenaconfig']
        self.jdbc = config['sdb_jdbc']

    def graphquery(self, query, g=None):
        env = {'SDBROOT': self.jenaroot,
               'SDB_JDBC': self.jdbc,
               'JVM_ARGS': '-Djava.net.preferIPv4Stack=true'}
        sdb = Popen([self.jenaroot + '/bin/sdbquery', '--sdb=' + self.jenaconfig, '--syntax=ARQ', '--query=-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        (stdout, stderr) = sdb.communicate(query)
        if g is None:
            g = Graph()
        g.parse(data=stdout, format='n3')
        
        return g


    def selectquery(self, query):
        env = {'SDBROOT': self.jenaroot,
               'SDB_JDBC': self.jdbc,
               'JVM_ARGS': '-Djava.net.preferIPv4Stack=true'}
        sdb = Popen([self.jenaroot + '/bin/sdbquery', '--sdb=' + self.jenaconfig, '--results=CSV', '--query=-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        (stdout, stderr) = sdb.communicate(query)
        return stdout.split('\r\n')[1:-1]


class ContentProvider(object):

    #implements(IContentProvider)

    def __init__(self, config):
        self.config = config
        self.jena = JenaHelper(config)
        self.harvester = URIRef(config['harvesteruri'])
        data = self.jena.graphquery("DESCRIBE %s" % self.harvester.n3())
        #import pdb; pdb.set_trace()

        self.originatingSource = data.value(self.harvester, ANDS.originatingSource) or Literal(config['originatingsource'])
        self.groupDescription = data.value(self.harvester, ANDS.groupDescription) or Literal(config['groupdescription'])
        self.item_sparql_query = resource_string(__name__, "item_sparql.sparql")


    def set_logger(self, log):
        """Set the logger instance for this class
        """
        self.log = log

    def update(self, from_date=None):
        """Harvests new content added since from_date
        returns a list of content_ids that were changed/added,
        this should be called before get_contents is called
        """
        query = resource_string(__name__, "items_to_harvest.sparql")
        self._content = self.jena.selectquery(query % {'harvester': self.harvester})

        return self._content

    def count(self):
        """Returns number of content objects in the repository
        returns None if number is unknown, this should not be
        called before update is called
        """
        return len(self._content)

    def get_content_ids(self):
        """returns a list/generator of content_ids
        """
        return self._content

    def get_content_by_id(self, id):
        """Return content of a specific id
        """
        # assume id is URIRef instance
        g = Graph(identifier=URIRef(id))
        #print self.item_sparql_query %{"subject":id, 'harvester': self.harvester}
        data = self.jena.graphquery(self.item_sparql_query %{"subject": id,
                                                             'harvester': self.harvester}, g)
        #print data
        # FIXME: make tese conditional
        data.add((URIRef(id), ANDS.originatingSource, self.originatingSource))
        data.add((URIRef(id), ANDS.groupDescription, self.groupDescription))
        return data

