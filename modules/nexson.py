#!/usr/bin/env python
# coding: utf8

#This module implements the export of nexml in JSON syntax.  The json follows the badgerfish () rules for mapping xml to json

#There are two entry points to this module: nexmlStudy (generate nexml for all the trees and otus for a study) and nexmlTree
#(complete nexml but just including a single tree - but currently all the otus for its containing study)

#local naming convention: getXXX are DAL queries, generally returning an id or list of ids', everything else is generating
#dicts or lists that correspond to BadgerFish (http://badgerfish.ning.com - original site?) mappings of Elements

#Output has been tested using the translator on http://dropbox.ashlock.us/open311/json-xml/ and validating the resulting
#xml with the validator at nexml.org

from gluon.storage import Storage
from gluon import *

# Note - the nexml root element can have meta elements as direct children; unlike everywhere else, there are no id or about
# attributes as seem to be required for other element types (e.g., otu, node) when they have meta children
def nexmlStudy(studyId,db):
    '''Exports the set of trees associated with a study as JSON Nexml
       study - the study to export
       db - database connection'''
    metaElts = metaEltsForNexml(studyId,db) 
    otus = otusEltForStudy(studyId,db)
    trees = treesElt(studyId,db)
    header = nexmlHeader()
    body = dict()
    body.update(otus)
    body.update(trees)
    body.update(header)
    body.update(metaElts)
    body["@id"] = "study"
    body["@about"] = "#study"
    return dict(nexml = body)

def nexmlTree(tree,db):
    '''Exports one tree from a study (still a complete JSON NeXML with
    headers, otus, and trees blocks)'''
    studyId = getSingleTreeStudyId(tree,db)
    metaElts = metaEltsForNexml(studyId,db)
    otus = otusEltForTree(tree,studyId,db)
    trees = singletonTreesElt(tree,studyId,db)
    header = nexmlHeader()
    body = dict()
    body.update(otus)
    body.update(trees)
    body.update(header)
    body.update(metaElts)
    body["id"] = "study"
    body["@about"] = "#study"
    return dict(nexml = body)

def nexmlHeader():
    'Header for nexml - includes namespaces and version tag (see nexml.org)'
    result = dict()
    result["@xmlns"] = xmlNameSpace()
    result["@version"] = "0.9"
    result["@nexmljson"] = "http://www.somewhere.org"
    result["@generator"] = "Phylografter nexml-json exporter"
    return result
        
def xmlNameSpace():
    '''namespace definitions for nexml; will be value of xmlns attribute in header (per badgerfish 
    treatment of namespaces)'''
    result = dict()
    result["$"] = "http://www.nexml.org/2009"
    result["nex"] = "http://www.nexml.org/2009"
    result["xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
    result["ot"] = "http://purl.org/opentree-terms#"
    result["xsd"] = "http://www.w3.org/2001/XMLSchema#"
    return result

def metaEltsForNexml(study_id,db):
    'generates nexml meta elements that are children of the root nexml element'
    metaArray = []
    studyRow = db.study(study_id)
    studyPublicationMeta = studyPublicationMetaElt(studyRow)
    if studyPublicationMeta:
        metaArray.append(studyPublicationMeta)
    doiMeta = doiMetaForStudy(studyRow)
    if doiMeta:
        metaArray.append(doiMeta)
    curatorMeta = curatorMetaForStudy(studyRow)
    if curatorMeta:
        metaArray.append(curatorMeta)
    treeBaseDepositMeta = treeBaseDepositMetaForStudy(studyRow)
    if treeBaseDepositMeta:
        metaArray.append(treeBaseDepositMeta)
    phylografterIdMeta = phylografterIdMetaForStudy(studyRow)
    if phylografterIdMeta:
        metaArray.append(phylografterIdMeta)
    return dict(meta = metaArray)

def curatorMetaForStudy(studyRow):
    'generates curator metadata element for a study'
    curator = studyRow.contributor
    if (curator):
        #names = metaNSForDCTerm()
        result = dict()
        result["@xsi:type"] = "nex:LiteralMeta"
        result["@property"] = "ot:curatorName"
        result["$"] = curator
        return result
    else:
        return

def treeBaseDepositMetaForStudy(studyRow):
    'generates text citation metadata element for a study'
    treebaseId = studyRow.treebase_id
    if (treebaseId):
        #names = metaNSForDCTerm()
        result = dict()
        result["@xsi:type"] = "nex:ResourceMeta"
        result["@property"] = "ot:dataDeposit"
        result["@href"] = "http://purl.org/phylo/treebase/phylows/study/TB2:S" + str(treebaseId)
        return result
    else:
        return


#returns an ot:studyPublication metadata element if a (possibly incomplete) doi or a 
#suitable URI is available, else nothing
def doiMetaForStudy(studyRow):
    'generates ot:studyPublication metadata element for a study'
    doi = studyRow.doi
    if (doi):
        if (doi.startswith('http://dx.doi.org/')):
            pass  #fine, leave as is
        elif (doi.startswith('http://www.')): #not a doi, but an identifier of some sort
            pass
        elif (doi.startswith('doi:')):    #splice the http prefix on
           doi = 'http://dx.doi.org/' + doi[4:]
        elif not(doi.startswith('10.')):  #not a doi, or corrupted, treat as blank
            return
        else:
           doi = 'http://dx.doi.org/' + doi
        result = dict()
        result["@xsi:type"] = "nex:ResourceMeta"
        result["@property"] = "ot:studyPublication"
        result["@href"] = doi
        return result
    else:
        return

def studyPublicationMetaElt(studyRow):
    'generates text citation metadata element for a study'
    cite = studyRow.citation
    if (cite):
        result = dict()
        result["@xsi:type"] = "nex:LiteralMeta"
        result["@property"] = "ot:studyPublicationReference"
        result["$"] = cite
        return result
    else:
        return

def phylografterIdMetaForStudy(studyRow):
    'generates phylografter study id metadata element for a study'
    result = dict()
    result["@xsi:type"] = "nex:LiteralMeta"
    result["@property"] = "ot:studyid"
    result["$"] = studyRow.id
    return result

def otusEltForStudy(studyId,db):
    'Generates an otus block'
    otuRows = getOtuRowsForStudy(studyId,db)
    metaElts = metaEltsForOtus(studyId,otuRows,db)
    otuElements = [otuElt(otuRow,db) for otuRow in otuRows]
    otusElement = dict()
    otusElement["otu"] = otuElements
    otusElement["@id"] = "otus" + str(studyId)
    return dict(otus = otusElement)
    
def getOtuRowsForStudy(studyid,db):
    'returns a list of otu ids for otu records that link to this study'
    otuStudy = db.otu.study
    s=db(otuStudy==studyid)
    rows = s.select()
    return rows
    
def metaEltsForOtus(studyid,otuRows,db):
    'generates nexml meta elements that are children of an otus element'
    result = dict()
    return result
    
def getTreeRowsForStudy(studyid,db):
    'returns a list of the trees associated with the specified study'
    treeStudy = db.stree.study
    s=db(treeStudy==studyid)
    rows = s.select()
    return rows
    
def otusEltForTree(tree,studyId,db):
    ##get the otus for this tree
    nodeList = getSNodeIdsForTree(tree,db)
    otuRows = list([])
    for node_id in nodeList:
        otuRow = getOtuRowForNode(node_id,db)
        if (otuRow):
            otuRows.append(otuRow)
    metaElts = metaEltsForOtus(studyId,otuRows,db)
    otuElements = [otuElt(otuRow,db) for otuRow in otuRows] 
    otusElement = dict()
    otusElement["otu"] = otuElements
    otusElement["@id"] = "otus" + str(studyId) + "." + str(tree)
    result = dict()
    result["otus"] = otusElement
    return result
       
def getOtuRowForNode(node_id,db):
    return db.otu(db.snode(node_id).otu) #this may need more attention   

#Generates an otu Element             
def otuElt(otuRow,db):
    ottolNameRow = db.ottol_name(otuRow.ottol_name)
    metaElts = metaEltsForOtuElt(ottolNameRow)
    result = dict()
    result["@id"] = "otu" + str(otuRow.id)
    if (ottolNameRow):
        result["@label"]= ottolNameRow.name
    else:
        result["@label"]= otuRow.label
    if metaElts:
        result["@about"] = "#otu" + str(otuRow.id)
        result.update(metaElts)
    return result
    
#Name suggests more than one meta element; expect more than current ot:ottolid
#will be added in the future.    
def metaEltsForOtuElt(ottolNameRow):
    'generates meta elements for an otu element'
    if ottolNameRow:
        idElt = dict()
        idElt["@xsi:type"] = "nex:LiteralMeta"
        idElt["@property"] = "ot:ottolid"
        idElt["$"] = ottolNameRow.accepted_uid
        return dict(meta = idElt)    
    else:
        return
    
def treesElt(study,db):
    'generate trees element'
    rowList = getTreeRowsForStudy(study,db)
    if (len(rowList) == 1):
        treeList = [treeElt(rowList[0],db)]
        body=dict()
        body["@otus"] = "otus" + str(study)
        body["tree"] = treeList
        result = dict()
        result["trees"] = body
    else:
        treeElements = [treeElt(treeRow,db) for treeRow in rowList]
        treesElement = dict()
        treesElement["tree"] = treeElements
        treesElement["@otus"] = "otus" + str(study)
        treesElement["@id"] = "trees" + str(study)
        result = dict()
        result["trees"] = treesElement
    return result
    
def metaEltsForTreesElt(study,db):
    return dict()    

def singletonTreesElt(tree,studyId,db):
    'generate the singleton tree element for a tree request'
    treeRow=db.stree(tree)
    treeList = [treeElt(treeRow,db)]
    body=dict()
    body["@otus"] = "otus" + str(studyId) + "." + str(treeRow.id)
    body["tree"] = treeList
    result = dict()
    result["trees"] = body
    return result
    
def getSingleTreeStudyId(tree,db):
    return db.stree(tree).study
    
def treeElt(treeRow,db):
    'generates a tree element'
    metaElts = metaEltsForTreeElt(treeRow)
    result = dict()
    result["@id"]='tree' + str(treeRow.id)
    result["node"]=treeNodes(treeRow,db)
    result["edge"]=treeEdges(treeRow,db)
    if metaElts:
    	result["@about"] = "#tree" + str(treeRow.id)
    	result.update(metaElts)
    return result
    
#Name suggests more than one meta element; expect more than current ot:branchLengthMode
#will be added in the future.    
def metaEltsForTreeElt(treeRow):
    'returns meta elements for a tree element'
    blRep = treeRow.branch_lengths_represent
    if blRep:
        lengthsElt = dict()
        lengthsElt["@xsi:type"] = "nex:LiteralMeta"
        lengthsElt["@property"] = "ot:branchLengthMode"
        if (blRep == "substitutions per site"):
        	lengthsElt["$"] = "ot:substitutionCount"
        elif (blRep == "character changes"):
            lengthsElt["$"] = "ot:changesCount"
        elif (blRep == "time (Myr)"):
            lengthsElt["$"] = "ot:years"
        elif (blRep == "bootstrap values"):
            lengthsElt["$"] = "ot:bootstrapValues"                            
        elif (blRep == "posterior support"):
            lengthsElt["$"] = "ot:posteriorSupport"
        else:
        	return   #this is a silent fail, maybe better to return 'unknown'?
        return dict(meta=lengthsElt)
    else:
        return    
    
def treeNodes(treeRow,db):
    nodeRows = getSNodeRowsForTree(treeRow,db)
    body = [nodeElt(nodeRow) for nodeRow in nodeRows]
    return body
    
def treeEdges(tree,db):
    nodeRows = getSNodeRowsForTree(tree,db)
    edgeList = list([])
    for nodeRow in nodeRows:
        parent = getNodeParent(nodeRow)
        child = nodeRow.id
        length = getEdgeLength(nodeRow)
        if (parent):
            edgeList.append(edgeElt(parent,child,length))
    return edgeList
    
def getNodeParent(childNodeRow):
    return childNodeRow.parent

def getEdgeLength(nodeRow):
    return nodeRow.length        
    
def edgeElt(parent, child,length):
    result = dict()
    result["@id"]='edge'+str(child)
    result["@source"]='node'+str(parent)
    result["@target"]='node'+str(child)
    if (length):
        result["@length"]=length
    return result

def getSNodeRowsForTree(treeRow,db):
    'returns a list of the nodes associated with the specified study'
    nodeSTree = db.snode.tree
    s=db(nodeSTree==treeRow.id)
    return s.select()
    
def nodeElt(nodeRow):
    result = dict()
    otu_id = nodeRow.otu
    if (otu_id):
        result["@otu"] = 'otu' + str(otu_id)
    if getNodeParent(nodeRow):
        pass
    else:
        result["@root"] = 'true'
    result["@id"] = 'node'+str(nodeRow.id)
    return result
