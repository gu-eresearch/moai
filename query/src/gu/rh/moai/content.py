from datetime import datetime
from urlparse import urlsplit
from rdflib import URIRef
from gu.rh.moai.utils import Period
from gu.rh.moai.namespace import (ANDS, MARCREL, VIVO, FOR08, SKOS,
                                  CLD, DC, DCES, BIBO, GUHUBEXT, RDFS, FOAF, SEO08, SEO98, RFCD, RDF)

def _uri_to_oai(uri):
    parts = urlsplit(uri)
    return '%s%s' % (parts.netloc, parts.path.replace('/', ':'))


def _uri_to_key(uri):
    parts = urlsplit(uri)
    return 'griffith.edu.au/%s' % (parts.path[1:].replace('/', ':'))

def _get_identifier_list(data, subject):
    idinfo = []
    for idprop, idtype, asUri, uriprefix in ((BIBO.handle, 'handle', False, u'http://hdl.handle.net/%s'),
                                             (BIBO.doi, 'doi', True, u'http://dx.doi.org/%s'),
                                             (BIBO.uri, 'uri', False, None),
                                             (BIBO.isbn, 'isbn', False, None),
                                             (ANDS.nla, 'AU-ANL:PEAU', False, None),
                                             (DCES.identifier, 'uri', True, None),
                                             (VIVO.linkURI, 'uri', False, None)):
        for obj in data.objects(subject, idprop):
            val = unicode(obj)
            if asUri:
                idtype = 'uri'
                if uriprefix:
                    val = uriprefix % val
            idinfo.append({'type': idtype,
                           'value': val})
    if isinstance(subject, URIRef):
        # We 'll add the URI as a local keyword if the subject is a URI ... 
        idinfo.append({'type': 'uri',
                       'value': unicode(subject)})
    return idinfo


def _get_itemtype(data, subject):
    if (subject, RDF.type, FOAF.Person) in data:
        return ('party', 'person')
    if (subject, RDF.type, GUHUBEXT.GrantProject) in data:
        return ('activity', 'project')    
    if (subject, RDF.type, GUHUBEXT.GUOrganisation) in data:
        return ('party', 'group')
    if (subject, RDF.type, ANDS.researchCatalog) in data:
        return ('collection', 'catalogueOrIndex')
    if (subject, RDF.type, ANDS.researchCollection) in data:
        return ('collection', 'collection')
    if (subject, RDF.type, ANDS.researchDataSet) in data:
        return ('collection', 'dataset')
    if (subject, RDF.type, ANDS.researchRegistry) in data:
        return ('collection', 'registry')
    if (subject, RDF.type, ANDS.ResearchData) in data:
        return ('collection', 'collection')
    if (subject, RDF.type, VIVO.Service) in data:
        if (subject, DC.type, ANDS.ServiceCreate) in data: # VIVO.type, 'create'
            return ('service', 'create')
        if (subject, DC.type, ANDS.ServiceCollaboration) in data: # VIVO.type, 'collaboration'
            return ('service', 'collaboration')
        if (subject, DC.type, ANDS.ServiceSyndicateRss) in data: # VIVO.type, 'syndicate-rss'
            return ('service', 'syndicate-rss')
        if (subject, DC.type, ANDS.ServiceTransform) in data: # VIVO.type, 'transform'
            return ('service', 'transform')

        # TODO: get rid of this below and use the new service classes
        oldservicetype = data.value(subject, DC.description)
        #if unicode(oldservicetype) in (u'syndicate-rss', u'syndicate-atom', u'harvest-oaipmh', u'Research Survey Facility'):
        if oldservicetype:
            return ('service', unicode(oldservicetype))


def _extract_identifier(provider, metadata, data, subject):
    '''
    aadd list of
    {'type': '', 'value': '' }
    dictionaries with key 'identifier' into metadata
    '''

    idinfo = _get_identifier_list(data, subject)
    if idinfo:
        metadata['rif_identifier'] = idinfo


def _extract_name_person(provider, metadata, data, subject):
    '''
    insert list of
    {'type': '',
     'lang': '',
     'dateFrom':'',
     'dateTo':'',
     'namePart': [{'type':'',
                   'value':''}]
    }
    with key 'name' into metadata
    '''
    namepartinfo = []
    for nameprop, nametype in ((FOAF.title, 'title'),
                               (FOAF.givenName, 'given'),
                               (FOAF.familyName, 'family')):
        for obj in data.objects(subject, nameprop):
            namepartinfo.append({'type': nametype,
                                 'value': unicode(obj)})
    if namepartinfo:
        metadata['rif_name'] = [{'type': 'primary',
                                  'namePart': namepartinfo}]

def _extract_name(provider, metadata, data, subject):
    '''
    insert list of
    {'type': '',
     'lang': '',
     'dateFrom':'',
     'dateTo':'',
     'namePart': [{'type':'',
                   'value':''}]
    }
    with key 'name' into metadata
    '''
    nameinfo = []
    primaryname = None
    altname = None
    for nameprop, nametype in ((DC.title, 'primary'),
                               (FOAF.name, 'primary'),
                               (DC.alternative, 'alternative')):
        for obj in data.objects(subject, nameprop):
            newname = {'type': nametype,
                       'namePart': [{'value': unicode(obj)}]}
            # Pick the first "primary" and "alternative" name/s we come across
            # (prevents duplication)
            if nametype == 'primary' and primaryname is None:
                primaryname = newname
            elif nametype == 'alternative' and altname is None:
                altname = newname

    if primaryname is not None:
        nameinfo.append(primaryname)
    if altname is not None:
        nameinfo.append(altname)
    if nameinfo:
        metadata['rif_name'] = nameinfo


def _extract_location(provider, metadata, data, subject):
    '''
    self.metadata['location'] = {'electronic' :[{'type': '',
                                                 'value': ''}],
                                 'physical': [{'type': '', # addressParts
                                               'value': ''}],
                                }
    '''
    locationinfo = {}
    # the subject uri is one electronic address
    #for locprop, loctype in ((VIVO.primaryEmail, 'email'),
    #                         (VIVO.email, 'email')):
    #    for obj in data.objects(subject, locprop):
    #        if 'electronic' not in locationinfo:
    #            locationinfo['electronic'] = []
    #        locationinfo['electronic'].append({'type': loctype,
    #                                         'value': unicode(obj)
    #                                        })
    for locprop, loctype in ((VIVO.webpage, 'url'),):

        for obj in data.objects(subject, locprop):
            linkType = data.value(obj, VIVO.linkType)
            if linkType not in ("Homepage","Phonebook"):
                continue
            if 'electronic' not in locationinfo:
                locationinfo['electronic'] = []
            locationinfo['electronic'].append({'type': loctype,
                                             'value': data.value(obj, VIVO.linkURI)
                                            })
    #for locprop, loctype in ((VIVO.phoneNumber, 'telephoneNumber'),):
    #    for obj in data.objects(subject, locprop):
    #        if 'physical' not in locationinfo:
    #            locationinfo['physical'] = []
    #        locationinfo['physical'].append({'addressPart': [{'type': loctype,
    #                                                          'value': unicode(obj)}]
    #                                        })
    #for locprop, loctype in ((VIVO.faxNumber, 'faxNumber'),):
    #    for obj in data.objects(subject, locprop):
    #        if 'physical' not in locationinfo:
    #            locationinfo['physical'] = []
    #        locationinfo['physical'].append({'addressPart': [{'type': loctype,
    #                                                          'value': unicode(obj)}]
    #                                        })

    for locprop, loctype in ((VIVO.mailingAddress, 'postalAddress'),):
        
        for obj in data.objects(subject, locprop):
            if data.value(obj, GUHUBEXT.fullAddress) is not None:
                if 'physical' not in locationinfo:
                    locationinfo['physical'] = []
                locationinfo['physical'].append({'type': loctype,
                                                 'addressPart': [{'type': 'text',
                                                                  'value': data.value(obj, GUHUBEXT.fullAddress)}]
                                                })
            elif data.value(obj, GUHUBEXT.partAddress) is not None:
                if 'physical' not in locationinfo:
                    locationinfo['physical'] = []
                locationinfo['physical'].append({'type': loctype,
                                                 'addressPart': [{'type': 'text',
                                                                  'value': data.value(obj, GUHUBEXT.partAddress)}]
                                                })    
            elif data.value(obj, GUHUBEXT.minAddress) is not None:
                if 'physical' not in locationinfo:
                    locationinfo['physical'] = []
                locationinfo['physical'].append({'type': loctype,
                                                 'addressPart': [{'type': 'text',
                                                                  'value': data.value(obj, GUHUBEXT.minAddress)}]
                                                })        

        # for obj in data.objects(subject, locprop):
        #     if data.value(obj, ANDS.addressLabel) is not None:
        #         if 'physical' not in locationinfo:
        #             locationinfo['physical'] = []
        #         locationinfo['physical'].append({'type': loctype,
        #                                          'addressPart': [{'type': 'text',
        #                                                           'value': data.value(obj, ANDS.addressLabel)}]
        #                                         })
        #     else:
        #         addresspart = []
        #         for locprop2, loctype2 in ((VIVO.addressDepartment, 'locationDescriptor'),
        #                                  (VIVO.addressStreet, 'streetName'),
        #                                  (VIVO.addressCity, 'suburbOrPlaceOrLocality'),
        #                                  (VIVO.addressState, 'stateOrTerritory'),
        #                                  (VIVO.addressCountry, 'country'),
        #                                  (VIVO.addressPostalCode, 'postCode')):
        #             for object in data.objects(obj, locprop2):
        #                 addresspart.append({'type': loctype2,
        #                                     'value': unicode(object)})
        #         if addresspart:
        #             if 'physical' not in locationinfo:
        #                 locationinfo['physical'] = []
        #             locationinfo['physical'].append({'type': loctype,
        #                                              'addressPart': addresspart
        #                                              })
            
    #for locprop, loctype in ((ANDS.addressLabel, 'postalAddress'),):
    #    for obj in data.objects(subject, locprop):
    #        if 'physical' not in locationinfo:
    #            locationinfo['physical'] = []
    #        locationinfo['physical'].append({'type': loctype,
    #                                         'addressPart': [{'type': 'text',
    #                                                          'value': unicode(obj)}]
    #                                        })
    if (subject, RDF.type, GUHUBEXT.ResearchHubPerson) in data:
        if 'electronic' not in locationinfo:
            locationinfo['electronic'] = []
        locationinfo['electronic'].append({'type': 'url',
                                             'value': unicode(subject)
                                            })

    if locationinfo:
        metadata['rif_location'] = locationinfo


def _extract_coverage(provider, metadata, data, subject):
    # {'covtype': 'temporal|spatial',
    #  'type': spatial_type,
    #  'value': spatial_value
    #  'date': {'type': '',
    #           'dateFormat': '',
    #           'value': ''},
    # 'text': 'value'}
    covinfo = []
    for covprop, covtype in ((DC.temporal, 'temporal'),):
        for obj in data.objects(subject, covprop):
            if obj.datatype == DC.Period:
                dateinfo = {'covtype': 'temporal',
                            'type': 'W3CDTF'}
                period = Period(unicode(obj))
                if period.start:
                    dateinfo['start'] = period.start
                if period.end:
                    dateinfo['end'] = period.end
                covinfo.append(dateinfo)
            elif obj.datatype == XSD.gYear:
                covinfo.append({'covtype': 'temporal',
                                'type': 'W3CDTF',
                                'start': unicode(obj)})
            else:
                covinfo.append({'covtype': 'temporal',
                                'type': 'text',
                                'value': unicode(obj)})
                
    for covprop, covtype in ((DC.spatial, 'spatial'),):
        for obj in data.objects(subject, covprop):
            # TODO: support additional formats and props form oupdated ands ontology
            if obj.datatype == DC.Box:
                covinfo.append({'covtype': 'spatial',
                                'value': unicode(obj), 'type': 'iso19139dcmiBox'})
            else:
                covinfo.append({'covtype': 'spatial',
                                'value': unicode(obj), 'type': 'text'})
    if covinfo:
        metadata['rif_coverage'] = covinfo


def _extract_existencedates(provider, metadata, data, subject):
    # {'covtype': 'temporal|spatial',
    #  'type': spatial_type,
    #  'value': spatial_value
    #  'date': {'type': '',
    #           'dateFormat': '',
    #           'value': ''},
    # 'text': 'value'}
    edatesInfo = []
    for covprop, covtype in ((GUHUBEXT.existenceDates, 'existenceDates'),):
        for obj in data.objects(subject, covprop):
            if obj.datatype == DC.Period:
                dateinfo = {'covtype': 'existenceDates',
                            'type': 'W3CDTF'}
                period = Period(unicode(obj))
                if period.start:
                    dateinfo['start'] = period.start
                if period.end:
                    dateinfo['end'] = period.end
                edatesInfo.append(dateinfo)
            elif obj.datatype == XSD.gYear:
                edatesInfo.append({'covtype': 'temporal',
                                'type': 'W3CDTF',
                                'start': unicode(obj)})
            else:
                edatesInfo.append({'covtype': 'temporal',
                                'type': 'text',
                                'value': unicode(obj)})
                
    
    if edatesInfo:
        metadata['rif_existenceDates'] = edatesInfo        
        #print metadata['rif_existenceDates']
    

def _extract_relatedobject(provider, metadata, data, subject):
    # 'key': '',
    # 'relation': {'description': {'lang':'',
    #                              'value': ''},
    #             'url': '',
    #             'type': '' }
    #  }
    relinfo = []
    # TODO: FIXME: should produce reverse links here esp. for isPartOf
    #              and for party records supplied by AusNC
    for relprop, reltype in ((ANDS.isManagedBy, 'isManagedBy'),
                             (ANDS.isManagerOf, 'isManagerOf'),
                             (ANDS.isOwnedBy, 'isOwnedBy'),
                             (ANDS.isOwnerOf, 'isOwnerOf'),
                             (ANDS.isOutputOf, 'isOutputOf'),
                             (ANDS.hasOutput, 'hasOutput'),
                             (ANDS.isParticipantIn, 'isParticipantIn'),
                             (ANDS.hasParticipant, 'hasParticipant'),
                             (ANDS.isPointOfContactFor, 'isPointOfContact'),
                             (ANDS.hasPointOfContact, 'pointOfContact'),
                             (ANDS.isCollectorOf, 'isCollectorOf'),
                             (ANDS.hasCollector, 'hasCollector'),
                             (ANDS.hasAssociationWith, 'hasAssociationWith'),
                             (ANDS.supports, 'supports'),
                             (ANDS.isSupportedBy, 'isSupportedBy'),
                             (VIVO.hasMemberRole, 'isMemberOf'),
                             (VIVO.memberRoleOf, 'hasMember'),
                             (VIVO.hasInvestigatorRole, 'isParticipantIn'),
                             (VIVO.investigatorRoleOf, 'hasParticipant'),
                             (VIVO.hasPrincipalInvestigatorRole, 'isParticipantIn'),
                             (VIVO.principalInvestigatorRoleOf, 'hasParticipant'),
                             (GUHUBEXT.hasPrimaryAffiliationRole, 'hasAssociationWith'),
                             (GUHUBEXT.primaryAffiliationRoleOf, 'hasAssociationWith')):
        for obj in data.objects(subject, relprop):
            if isinstance(obj, URIRef):
                relinfo.append({'key': _uri_to_key(obj),
                                'relation' : {'type': reltype}})
    if relinfo:
        metadata['rif_relatedobject'] = relinfo

# PARTY_RELATIONS = {
#     'contributor': (DC.contributor, ),
#     'creator': (DCES.creator, ),
#     'publisher': (MARCREL.OWN, ),
# }


# def _extract_related_party(content, field_name):
#     values = []
#     parties = content.provider.parties
#     for prop in PARTY_RELATIONS[field_name]:
#         for party in content.data.objects(content.data.identifier, prop):
#             key = parties.value(party, ANDS.nla)
#             if key:
#                 values.append(unicode(key))
#     return values


def _extract_subject(provider, metadata, data, subject):
    # 'type': '',
    # 'termIdentifier': '',
    # 'lang': '',
    # 'value': ''}
    subjectinfo = []
    for subjectType in ((VIVO.hasSubjectArea),
                        (VIVO.hasSubjectAreaLabel)):
        for obj in data.objects(subject, subjectType):
            # TODO check if URIRef?
            if obj.startswith(FOR08):
                subjectinfo.append({'type': 'anzsrc-for',
                                    'value': obj.rsplit('/', 1)[-1]})
            elif obj.startswith(RFCD):
                subjectinfo.append({'type': 'anzsrc-rfcd',
                                    'value': obj.rsplit('/', 1)[-1]})
            elif obj.startswith(SEO08):
                subjectinfo.append({'type': 'anzsrc-seo',
                                    'value': obj.rsplit('/', 1)[-1]})
            elif obj.startswith(SEO98):
                subjectinfo.append({'type': 'anzsrc-seo',
                                    'value': obj.rsplit('/', 1)[-1]})
            else:
                subjectinfo.append({'type': 'local',
                                    'value': unicode(obj)})
        if subjectinfo:
            metadata['rif_subject'] = subjectinfo
            #print metadata['rif_subject']

def _extract_description(provider, metadata, data, subject):
    # {'type': '',
    #  'lang': '',
    #  'value': ''}
    descrinfo = []
    for descprop, desctype in ((VIVO.description, 'full'),
                               (DC.description, 'full'),
                               (BIBO.shortDescription, 'brief'),
                               (FOAF.logo, 'logo'),
                               (SKOS.note, 'note'),
                               (VIVO.overview, 'brief')):
        for obj in data.objects(subject, descprop):
            descrinfo.append({'type': desctype,
                              'value': unicode(obj)}),
    if not descrinfo:
        #if no description from rdf, generate generic one
        str_desc = ''
        for descprop1, desctype1 in ((GUHUBEXT.projectstate, 'Project Status:'),
                                     (FOAF.fundedBy, 'Funded By:')):
            for obj1 in data.objects(subject, descprop1):
                str_desc += desctype1 + ' ' + unicode(obj1) + ', ' 

        if str_desc:
            descrinfo.append({'type': 'brief',
                             'value': str_desc}),

    if 'rif_description' in metadata:
        metadata['rif_description'].extend(descrinfo)
    else:
        metadata['rif_description'] = descrinfo

def _extract_itemFormat(provider, metadata, data, subject):
    # {'type': '',
    #  'lang': '',
    #  'value': ''}
    formatInfo = []
    #if no description from rdf, generate generic one
    str_formats = []
    for descprop, desctype in ((CLD.itemFormat, 'Item Format:'),):
        for obj in data.objects(subject, descprop):
            str_formats.append(unicode(obj))

    if str_formats:
        str_formats = desctype + ' ' + ', '.join(str_formats)
        formatInfo.append({'type': 'note',
                         'value': str_formats}),

        #metadata['rif_description'] = formatInfo
        #print metadata['rif_description']      
        if 'rif_description' in metadata:
            metadata['rif_description'].extend(formatInfo)
        else:
            metadata['rif_description'] = formatInfo

def _extract_rights(provider, metadata, data, subject):
    # {'rightsStatemnt': {'rightsUri': '',
    #                    'value': ''},
    # 'licence': {'type': '',
    #             'rightsUri': '',
    #             'value': ''},
    # 'accessRights', {'type': '',
    #                  'rightsUri': '',
    #                  'value': ''}
    # }
    rightinfo = {}
    for rightprop, righttype in ((DC.accessRights, 'accessRights'),
                                 (DC.rights, 'rights')):
        for obj in data.objects(subject, rightprop):
            rightinfo[righttype] = {'value': unicode(obj)}
    if rightinfo:
        metadata['rif_rights'] = rightinfo


def _extract_relatedinfo(provider, metadata, data, subject):
    # {'identifier': {'type': '',
    #                 'value': ''},
    #  'title': '',
    #  'notes': '',
    #  'type': ''}
    relinfo = []
    for relprop, reltype in ((VIVO.webpage, 'url'),):

        for obj in data.objects(subject, relprop):
            linkType = data.value(obj, VIVO.linkType)
            if linkType not in (None, "Homepage","Phonebook"):
                continue
            idinfo = _get_identifier_list(data, obj)
            title = data.value(obj, VIVO.linkType)

            # TODO: check in more detail for complete data
            if title not in ("Homepage","Phonebook"):
                info = {}
                if title and title not in ('uri',):
                    info['title'] = title
                if title in (None,"Website"):
                    info['type'] = 'website'    
                    linkText = data.value(obj, VIVO.linkAnchorText)
                    if linkText:
                        info['title'] = linkText
                if idinfo:
                    info['identifier'] = idinfo[0:1]
                if info:
                    relinfo.append(info)

    if relinfo:
        metadata['rif_relatedInfo'] = relinfo
        print relinfo

    # Add <relatedInfo type="publication"/> for party, if applicable
    _extract_relatedinfo_publication(provider, metadata, data, subject)


def _extract_relatedinfo_publication(provider, metadata, data, subject):
    # {'identifier': {'type': '',
    #                 'value': ''},
    #  'title': '',
    #  'notes': '',
    #  'type': ''}

    # If party is a ResearchHubPerson, add a link to their publications page
    if (subject, RDF.type, GUHUBEXT.ResearchHubPerson) in data:
        pubinfo = {}
        # Note: If URI scheme or publications endpoint changes, update generated URI
        pubinfo['identifier'] = [{'type': 'uri', 
                                 'value': unicode(subject) + '#publications'}]
        pubinfo['title'] = 'Publications in the Griffith Research Hub'
        pubinfo['type'] = 'publication'

        if 'rif_relatedInfo' in metadata:
            metadata['rif_relatedInfo'].append(pubinfo)
        else:
            metadata['rif_relatedInfo'] = [pubinfo]







def _extract_citationinfo(provider, metadata, data, subject):
    # {'fullCitation': {'style': '',
    #                   'value': ''},
    #  # 'citationMetadata': {'identifier': ..]
    #  }
    citinfo = {}
    for citprop, citstyle in ((ANDS.citHarvard, 'Harvard'),
                             (ANDS.citAPA, 'APA'),
                             (ANDS.citMLA, 'MLA'),
                             (ANDS.citVancouver, 'Vancouver'),
                             (ANDS.citIEEE, 'IEEE'),
                             (ANDS.citCSE, 'CSE'),
                             (ANDS.citChicago, 'Chicago'),
                             (ANDS.citAMA, 'AMA'),
                             (ANDS.citAgpsAGIMO, 'AGPS-AGIMO'),
                             (ANDS.citAGLC, 'AGLC'),
                             (ANDS.citACS, 'ACS'),
                             (ANDS.citDatacite, 'Datacite'),
                             ):
        for obj in data.objects(subject, citprop):
            if 'fullCitation' not in citinfo:
                citinfo['fullCitation'] = []
            citinfo['fullCitation'].append({'style': citstyle,
                                            'value': unicode(obj)})
    # FIXME: not sure how citationMetadat is mapped in ontology... has to be a separate individual with all props attached to it, or autogenerated from available info?
    str_doi, str_issued, str_publisher, str_title, contrib = (data.value(subject, BIBO.doi),
                     data.value(subject, DC.issued),
                     data.value(subject, DC.publisher),
                     data.value(subject, DC.title),
                     data.value(subject, ANDS.hasCollector))
    if all((str_doi, str_issued, str_publisher, str_title, contrib)):
        citMetadata = {}
        # Note: If URI scheme or publications endpoint changes, update generated URI        
        citMetadata['identifier'] = {'type': 'doi', 
                                 'value': str_doi}                         
        
        citMetadata['title'] = unicode(str_title)
        citMetadata['edition'] = unicode(str_issued)
        citMetadata['publisher'] = unicode(str_publisher)
        citMetadata['placePublished'] = 'Brisbane, Australia'

        citMetadata['date'] = [{'type': 'publicationDate',
                                'value': unicode(str_issued)}]

        citMetadata['url'] = unicode('http://dx.doi.org/' + str_doi)
        citMetadata['context'] = 'Griffith Research Data Repository'

        citContributors = []
        for obj in data.objects(subject, ANDS.hasCollector):
            lname, fname, title = (data.value(obj, FOAF.familyName),
                                 data.value(obj, FOAF.firstName),
                                 data.value(obj, RDFS.label))
                     
            contributor = None
            if all((fname, lname)):
                #if it is a person, we include familyname and initials as nameparts
                contributor = {'family': unicode(lname),
                               'given': unicode(fname)}
            else:
                #if it is a group etc, we only include title as namepart for the contributor
                contributor = {'title': unicode(title)}
            #add nameparts to the contributor
            if contributor:
                citContributors.append(contributor)

        #add all contributors to citation metadata object
        if citContributors:
            citMetadata['contributors'] = citContributors
        if citMetadata:
            if 'citationMetadata' not in citinfo:
                citinfo['citationMetadata'] = []
            citinfo['citationMetadata'].append(citMetadata)


    if citinfo:
        metadata['rif_citationinfo'] = citinfo
        #debug
        #print metadata['rif_citationinfo']
        
    
    


class RDFContentObject(object):

    #implements(IContentObject)

    #dc-fields:
    # 'title', 'creator', 'subject', 'description',
    # 'publisher', 'contributor', 'type', 'format',
    # 'identifier', 'source', 'language', 'date',
    # 'relation', 'coverage', 'rights']:

    #rif-fields:
    # rif_type .... RIF-CS Object type
    # rif_subtype ... Sub type within RIF-CS object

    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.deleted = None
        self.data = None
        self.sets = None

    def update(self, data):
        """Called by IContentProvider, to fill the object with data
        """
        self.data = data
        # extract data
        subject = data.identifier
        self.id = _uri_to_oai(subject)
        self.modified = datetime.utcnow()
        self.deleted = False

        itemtype, subtype = _get_itemtype(data, subject)

        self.metadata = {}

        # fixed fields:
        self.metadata['rif_key'] = _uri_to_key(subject)
        self.metadata['rif_group'] = self.provider.groupDescription
        self.metadata['rif_originatingSource'] = self.provider.originatingSource
        self.metadata['rif_object'] = {'value': itemtype,
                                       'type': subtype,
                                       #'dateModified': '',
                                       }

        if itemtype == 'collection':
            self.updateCollection(data, subject)
        elif itemtype == 'party':
            if subtype == 'person':
                self.updatePartyPerson(data, subject)
            else:
                self.updateParty(data, subject)
        elif itemtype == 'activity':
            self.updateActivity(data, subject)
        elif itemtype == 'service':
            self.updateService(data, subject)

    def updateCollection(self, data, subject):
        self.sets = {u'Collections': {'name': u'Collections',
                                      'description': u'All Collections'}}

        # collection specific part
        _extract_identifier(self.provider, self.metadata, data, subject)
        _extract_name(self.provider, self.metadata, data, subject)
        _extract_existencedates(self.provider, self.metadata, data, subject)
        # this should become location/address
        _extract_location(self.provider, self.metadata, data, subject)
        _extract_coverage(self.provider, self.metadata, data, subject)
        _extract_relatedobject(self.provider, self.metadata, data, subject)
        _extract_subject(self.provider, self.metadata, data, subject)
        _extract_description(self.provider, self.metadata, data, subject)
        _extract_itemFormat(self.provider, self.metadata, data, subject)
        _extract_rights(self.provider, self.metadata, data, subject)
        _extract_relatedinfo(self.provider, self.metadata, data, subject)
        _extract_citationinfo(self.provider, self.metadata, data, subject)

    def updateParty(self, data, subject):
        self.sets = {u'Party': {'name': u'Party',
                                      'description': u'All Parties'}}
        _extract_identifier(self.provider, self.metadata, data, subject)
        _extract_name(self.provider, self.metadata, data, subject)
        _extract_existencedates(self.provider, self.metadata, data, subject)

        # this should become location/address
        _extract_location(self.provider, self.metadata, data, subject)
        _extract_coverage(self.provider, self.metadata, data, subject)
        _extract_relatedobject(self.provider, self.metadata, data, subject)
        _extract_subject(self.provider, self.metadata, data, subject)
        _extract_description(self.provider, self.metadata, data, subject)
        _extract_rights(self.provider, self.metadata, data, subject)
        _extract_relatedinfo(self.provider, self.metadata, data, subject)

    def updatePartyPerson(self, data, subject):
        self.sets = {u'Party': {'name': u'Party',
                                      'description': u'All Parties'}}
        _extract_identifier(self.provider, self.metadata, data, subject)
        _extract_name_person(self.provider, self.metadata, data, subject)
        _extract_existencedates(self.provider, self.metadata, data, subject)

        # this should become location/address
        _extract_location(self.provider, self.metadata, data, subject)
        _extract_coverage(self.provider, self.metadata, data, subject)
        _extract_relatedobject(self.provider, self.metadata, data, subject)
        _extract_subject(self.provider, self.metadata, data, subject)
        _extract_description(self.provider, self.metadata, data, subject)
        _extract_rights(self.provider, self.metadata, data, subject)
        _extract_relatedinfo(self.provider, self.metadata, data, subject)

    def updateActivity(self, data, subject):
        self.sets = {u'Activity': {'name': u'Activity',
                                      'description': u'All Activities'}}
        _extract_identifier(self.provider, self.metadata, data, subject)
        _extract_name(self.provider, self.metadata, data, subject)
        _extract_existencedates(self.provider, self.metadata, data, subject)

        # this should become location/address
        _extract_location(self.provider, self.metadata, data, subject)
        _extract_coverage(self.provider, self.metadata, data, subject)
        _extract_relatedobject(self.provider, self.metadata, data, subject)
        _extract_subject(self.provider, self.metadata, data, subject)
        _extract_description(self.provider, self.metadata, data, subject)
        _extract_rights(self.provider, self.metadata, data, subject)
        _extract_relatedinfo(self.provider, self.metadata, data, subject)

    def updateService(self, data, subject):
        self.sets = {u'Service': {'name': u'Service',
                                      'description': u'All Services'}}
        _extract_identifier(self.provider, self.metadata, data, subject)
        _extract_name(self.provider, self.metadata, data, subject)
        _extract_existencedates(self.provider, self.metadata, data, subject)

        # this should become location/address
        _extract_location(self.provider, self.metadata, data, subject)
        _extract_coverage(self.provider, self.metadata, data, subject)
        _extract_relatedobject(self.provider, self.metadata, data, subject)
        _extract_subject(self.provider, self.metadata, data, subject)
        _extract_description(self.provider, self.metadata, data, subject)
        _extract_rights(self.provider, self.metadata, data, subject)
        _extract_relatedinfo(self.provider, self.metadata, data, subject)

    def _uri_to_oai(self, uri):
        parts = urlsplit(uri)
        return '%s%s' % (parts.netloc, parts.path.replace('/', ':'))

    def _uri_to_key(self, uri):
        parts = urlsplit(uri)
        return 'ausnc.org.au/%s' % (parts.path.replace('/', ':'))
