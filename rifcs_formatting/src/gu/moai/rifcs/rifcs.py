# from moai import MetaDataFormat, name
from lxml.builder import ElementMaker
# FIXME: this module is overshadowed by the folder based module
#from moai.metadata import XSI_NS
from moai.metadata.oaidc import XSI_NS


class RIFCSMetadataFormat(object):
    """A metadata prefix implementing the RIF-CS metadata format
    this format is registered under the name "rif"
    Note that this format re-uses oai_dc and mods formats that come with
    MOAI by default
    """
    # name('rif')

    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db
        self.ns = {'xsi': "http://www.w3.org/2001/XMLSchema-instance",
                   None: "http://ands.org.au/standards/rif-cs/registryObjects",
        'rif': "http://ands.org.au/standards/rif-cs/registryObjects",
                   }

        self.schemas = {'rif': "http://services.ands.org.au/home/orca/schemata/registryObjects.xsd"}

    def get_namespace(self):
        return self.ns[self.prefix]

    def get_schema_location(self):
        return self.schemas[self.prefix]

    def gen_attrib(eslf, data, keys):
        return dict((key, data[key]) for key in keys if data.get(key))

    def __call__(self, element, metadata):
        data = metadata.record
        md = data['metadata']

        RIF = ElementMaker(namespace=self.ns[None], nsmap=self.ns)

        rif = RIF.registryObjects(
            {'{%s}schemaLocation' % XSI_NS: '%s %s' % (self.ns[None], self.schemas['rif'])})
        rifregobj = RIF.registryObject(
            RIF.key(md['rif_key']),
            RIF.originatingSource(md['rif_originatingSource']),
            group=md['rif_group'])
        rif.append(rifregobj)

        rifobj = RIF(md['rif_object']['value'], type=md['rif_object']['type'])
        rifregobj.append(rifobj)

        for id in md.get('rif_identifier', []):
            rifobj.append(RIF.identifier(id['value'], type=id['type']))

        for name in md.get('rif_name', []):
            rifname = RIF.name(type=name['type'])
            for namepart in name['namePart']:
                rifname.append(RIF.namePart(namepart['value'],
                                            self.gen_attrib(namepart, ('type',))))
            rifobj.append(rifname)

        if 'rif_location' in md:
            loc = md['rif_location']
            rifaddr = RIF.address()
            for elloc in loc.get('electronic', []):
                rifaddr.append(RIF.electronic(RIF.value(elloc['value']),
                                              type=elloc['type']))
            for phyloc in loc.get('physical', []):
                phyaddr = RIF.physical(self.gen_attrib(phyloc, ('type',)))
                for ap in phyloc.get('addressPart', []):
                    phyaddr.append(RIF.addressPart(ap['value'],
                                                   type=ap['type']))
                rifaddr.append(phyaddr)
            if len(rifaddr) > 0:
                rifobj.append(RIF.location(rifaddr))

        # coverage
        if 'rif_coverage' in md:
            rifcov = RIF.coverage()
            for cov in md.get('rif_coverage', []):
                if cov['covtype'] == 'temporal':
                    riftemp = RIF.temporal()
                    if cov['type'] == 'text':
                        riftemp.append(RIF.text(cov['value']))
                    elif cov['type'] == 'W3CDTF':
                        if 'start' in cov:
                            riftemp.append(RIF.date(cov['start'], type='dateFrom',
                                                    dateFormat='W3CDTF'))
                        if 'end' in cov:
                            riftemp.append(RIF.date(cov['end'], type='dateTo',
                                                    dateFormat='W3CDTF'))
                    rifcov.append(riftemp)
                elif cov['covtype'] == 'spatial':
                    rifcov.append(RIF.spatial(cov['value'], type=cov['type']))
            if len(rifcov) > 0:
                rifobj.append(rifcov)
        
        # existencedates
        if 'rif_existenceDates' in md:
            edates = RIF.existenceDates()
            for cov in md.get('rif_existenceDates', []):
                if cov['type'] == 'W3CDTF':
                    if 'start' in cov:
                        edates.append(RIF.startDate(cov['start'], dateFormat='W3CDTF'))
                    if 'end' in cov:
                        edates.append(RIF.endDate(cov['end'], dateFormat='W3CDTF'))
                
            if len(edates) > 0:
                rifobj.append(edates)



        # relatedobject
        for relob in md.get('rif_relatedobject', []):
            rifrelob = RIF.relatedObject(RIF.key(relob['key']))
            rel = relob['relation']
            rifrelation = RIF.relation(type=rel['type'])
            if 'url' in rel:
                rifrelation.append(RIF.url(rel['url']))
            if 'description' in rel:
                # may have lang
                rifrelation.append(RIF.description(rel['value']))
            rifrelob.append(rifrelation)
            rifobj.append(rifrelob)

        # subject
        for sub in md.get('rif_subject', []):
            rifobj.append(RIF.subject(sub['value'], type=sub['type']))

        # description
        for desc in md.get('rif_description', []):
            # may have lang
            rifobj.append(RIF.description(desc['value'], type=desc['type']))

        # rights
        if 'rif_rights' in md:
            rifrights = RIF.rights()
            rights = md.get('rif_rights')
            if 'rightsStatement' in rights:
                rs = rights['rightsStatement']
                rifrights.append(RIF.rightsStatement(rs['value'],
                                                     self.gen_attrib(rs, ('rightsUri',))))
            if 'licence' in rights:
                rs = rights['licence']
                rifrights.append(RIF.licence(rs['value'],
                                             self.gen_attrib(rs, ('rightsUri', 'type'))))
            if 'accessRights' in rights:
                rs = rights['accessRights']
                rifrights.append(RIF.accessRights(rs['value'],
                                                  self.gen_attrib(rs, ('rightsUri', 'type'))))
            if len(rifrights) > 0:
                rifobj.append(rifrights)

        # relatedinfo
        for relinf in md.get('rif_relatedInfo', []):
            relinfobj = RIF.relatedInfo(self.gen_attrib(relinf, ('type',)))
            for id in relinf.get('identifier', []):
                relinfobj.append(RIF.identifier(id['value'], type=id['type']))
            if 'title' in relinf:
                relinfobj.append(RIF.title(relinf['title']))
            if 'notes' in relinf:
                relinfobj.append(RIF.notes(relinf['notes']))
            rifobj.append(relinfobj)

        # citationinfo
        citinfo = md.get('rif_citationinfo', None)
        if citinfo:
            # may have citationMetadata
            rifcitinfo = RIF.citationInfo()
            for fc in citinfo.get('fullCitation', []):
                rifcitinfo.append(RIF.fullCitation(
                    fc['value'],
                    self.gen_attrib(fc, ('style',))))
            for fc in citinfo.get('citationMetadata',[]):
                rifcitmd = RIF.citationMetadata()
                rifcitmd.append(RIF.identifier(fc['identifier']['value'],
                                               type=fc['identifier']['type']))
                for fcseq, fccontrib in enumerate(fc.get('contributors', [])):
                    rifcontributor = RIF.contributor(seq=str(fcseq+1))
                    for key, value in fccontrib.items():
                        rifcontributor.append(RIF.namePart(value, type=key))
                    rifcitmd.append(rifcontributor)
                rifcitmd.append(RIF.title(fc['title']))
                rifcitmd.append(RIF.edition(fc['edition']))
                rifcitmd.append(RIF.publisher(fc['publisher']))
                rifcitmd.append(RIF.placePublished(fc['placePublished']))
                for fcdate in fc.get('date', []):
                    rifcitmd.append(RIF.date(fcdate['value'], type=fcdate['type']))
                rifcitinfo.append(rifcitmd)
                rifcitmd.append(RIF.url(fc['url']))
                rifcitmd.append(RIF.context(fc['context']))

            # test if not empty
            if len(rifcitinfo) != 0:
                rifobj.append(rifcitinfo)


        element.append(rif)
