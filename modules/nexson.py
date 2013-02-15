#!/usr/bin/env python
# coding: utf8

#This module implements the export of nexml in JSON syntax.  The json follows the badgerfish () rules for mapping xml to json

#There are two entry points to this module: nexmlStudy (generate nexml for all the trees and otus for a study) and nexmlTree
#(complete nexml but just including a single tree - but currently all the otus for its containing study)

from gluon.storage import Storage
from gluon import *


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
    body["@id"] = studyId
    result = dict()
    result["nexml"] = body
    return result

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
    body["id"] = studyId
    result = dict()
    result["nexml"] = body
    return result

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
    result["cdao"] = "http://www.evolutionaryontology.org/cdao/1.0/cdao.owl#"
    result["xsd"] = "http://www.w3.org/2001/XMLSchema#"
    return result

def metaEltsForNexml(studyid,db):
    'generates nexml meta elements that are children of the root nexml element'
    metaArray = []
    yearMeta = pubYearMetaForStudy(studyid,db)
    if (yearMeta):
        metaArray.append(yearMeta)
    doiMeta = doiMetaForStudy(studyid,db)
    if (doiMeta):
        metaArray.append(doiMeta)
    result = dict()
    result["meta"] = metaArray
    return result


def pubYearMetaForStudy(studyid,db):
    'generates a date meta element'
    mdate = db.study(studyid).year_published
    if (mdate):
        names = metaNSForDCTerm()
        result = dict()
        result["@xmlns"] = names
        result["@xsi:type"] = "ns:LiteralMeta" 
        result["@property"] = "ter:date"
        result["$"] = mdate
        return result
    else:
        return
        
def doiMetaForStudy(studyid,db):
    'generates doi metadata element for a study'
    doi = db.study(studyid).doi
    if (doi):
        names = metaNSForDCTerm()
        result = dict()
        result["@xmlns"] = names
        result["@xsi:type"] = "ns:RssourceMeta"
        result["@property"] = "ter:identifier"
        result["@href"] = doi
        return result
    else:
        return

def metaNSForDCTerm():
    names = dict()
    names["$"] = "http://www.nexml.org/2009"
    names["ns"] = "http://www.nexml.org/2009"
    names["ter"] = "http://purl.org/dc/terms/"
    return names

def otusEltForStudy(studyId,db):
    'Generates an otus block'
    otuList = getOtuIDsForStudy(studyId,db)
    metaElts = metaEltsForOtus(studyId,otuList,db)
    otuElements = [otuElt(otu_id,db) for otu_id in otuList]
    otusElement = dict()
    otusElement["otu"] = otuElements
    otusElement["@id"] = "otus" + str(studyId)
    result = dict()
    result["otus"] = otusElement
    return result
    
def getOtuIDsForStudy(studyid,db):
    'returns a list of otu ids for otu records that link to this study'
    otuStudy = db.otu.study
    s=db(otuStudy==studyid)
    result = [row.id for row in s.select()]
    return result
    
def metaEltsForOtus(studyid,otuList,db):
    'generates nexml meta elements that are children of an otus element'
    result = dict()
    return result
    
def getTreeIDsForStudy(studyid,db):
    'returns a list of the trees associated with the specified study'
    treeStudy = db.stree.study
    s=db(treeStudy==studyid)
    rows = s.select()
    result = [row.id for row in rows]
    return result
    
def otusEltForTree(tree,studyId,db):
    ##get the otus for this tree
    nodeList = getSNodeIdsForTree(tree,db)
    otuList = list([])
    for node_id in nodeList:
        nodeOtu = getOtuForNode(node_id,db)
        if (nodeOtu):
            otuList.append(nodeOtu)
    metaElts = metaEltsForOtus(studyId,otuList,db)
    otuElements = [otuElt(otu_id,db) for otu_id in otuList] 
    otusElement = dict()
    otusElement["otu"] = otuElements
    otusElement["@id"] = "otus" + str(studyId) + "." + str(tree)
    result = dict()
    result["otus"] = otusElement
    return result
       
def getOtuForNode(node_id,db):
    return db.snode(node_id).otu    
    
def otuElt(otu_id,db):
    result = dict()
    result["@id"] = "otu" + str(otu_id)
    ottol_name_id = db.otu(otu_id).ottol_name
    if (ottol_name_id):
        result["@label"]= db.ottol_name(ottol_name_id).name
    return result
    
def taxonSetElt():
    body = dict()
    result = dict()
    result["taxonSet"] = body
    return result
    
def treesElt(study,db):
    idList = getTreeIDsForStudy(study,db)
    if (len(idList) == 1):
        tree = idList[0]
        treeList = [treeElt(tree,db)]
        body=dict()
        body["@otus"] = "otus" + str(study)
        body["tree"] = treeList
        result = dict()
        result["trees"] = body
    else:
        treeElements = [treeElt(tree_id,db) for tree_id in idList]
        treesElement = dict()
        treesElement["tree"] = treeElements
        treesElement["@otus"] = "otus" + str(study)
        treesElement["@id"] = "trees" + str(study)
        result = dict()
        result["trees"] = treesElement
    return result
    
def singletonTreesElt(tree,studyId,db):
    treeList = [treeElt(tree,db)]
    body=dict()
    body["@otus"] = "otus" + str(studyId) + "." + str(tree)
    body["tree"] = treeList
    result = dict()
    result["trees"] = body
    return result
    
def getSingleTreeStudyId(tree,db):
    return db.stree(tree).study
    
def treeElt(tree,db):
    t = db.stree(tree)
    result = dict()
    result["@id"]='tree' + str(t.id)
    result["node"]=treeNodes(tree,db)
    result["edge"]=treeEdges(tree,db)
    return result
    
def treeNodes(tree,db):
    nodeList = getSNodeIdsForTree(tree,db)
    body = [nodeElt(node_id,db) for node_id in nodeList]
    return body
    
def treeEdges(tree,db):
    nodeList = getSNodeIdsForTree(tree,db)
    edgeList = list([])
    for node_id in nodeList:
        parent = getNodeParent(node_id,db)
        child = node_id
        length = getEdgeLength(node_id,db)
        if (parent):
            edgeList.append(edgeElt(parent,child,length))
    return edgeList
    
def getNodeParent(childnode,db):
    return db.snode(childnode).parent

def getEdgeLength(childnode,db):
    return db.snode(childnode).length        
    
def edgeElt(parent, child,length):
    result = dict()
    result["@id"]='edge'+str(child)
    result["@source"]='node'+str(parent)
    result["@target"]='node'+str(child)
    if (length):
        result["@length"]=length
    return result

def getSNodeIdsForTree(treeid,db):
    'returns a list of the nodes associated with the specified study'
    nodeSTree = db.snode.tree
    s=db(nodeSTree==treeid)
    result = [row.id for row in s.select()]
    return result
    
def nodeElt(nodeid,db):
    result = dict()
    otu_id = db.snode(nodeid).otu
    if (otu_id):
        result["@otu"] = 'otu' + str(otu_id)
    result["@id"] = 'node'+str(nodeid)
    return result