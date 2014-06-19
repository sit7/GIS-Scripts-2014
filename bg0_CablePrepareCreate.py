from PyQt4.QtCore import *
from qgis.core import *
import psycopg2
import psycopg2.extras

def copyAttribute(featureFrom, featureTo, idLineType, idSocket):
     "comment"
     fields = QgsFields()
     fields.append( QgsField("id", QVariant.Int) )
     fields.append( QgsField("left_right", QVariant.String) )
     fields.append( QgsField("Comment", QVariant.String) )
     fields.append( QgsField("idCable", QVariant.Int) )
     fields.append( QgsField("idLineType", QVariant.Int) )
     fields.append( QgsField("idSocket", QVariant.Int) )
     fieldCount = 6
     featureTo.setFields(fields)
     featureTo.initAttributes(fieldCount)
     featureTo.setAttribute(0, featureFrom["id"]*10+idLineType)
     featureTo.setAttribute(1, featureFrom["left_right"])
     featureTo.setAttribute(2,  featureFrom["Comment"])
     featureTo.setAttribute(3, featureFrom["idCable"])
     featureTo.setAttribute(4,  idLineType)
     featureTo.setAttribute(5,  idSocket)

shiftX=0.0001

crs = QgsCoordinateReferenceSystem("EPSG:4326 - WGS 84")

layer_from = QgsVectorLayer("E:/GIS/Murmansk City/bgCableBase.shp","bgCableBase","ogr")

layerMap = QgsMapLayerRegistry.instance().mapLayers()

for name, layer in layerMap.iteritems():
     if layer.type() == QgsMapLayer.VectorLayer and layer.name() == "bgCablePrepare":
         QgsMapLayerRegistry.instance().removeMapLayer( layer.id() )

QgsVectorFileWriter.writeAsVectorFormat(layer_from, "E:/GIS/Murmansk City/bgCablePrepare.shp",  "System", crs )

layer_to = QgsVectorLayer("E:/GIS/Murmansk City/bgCablePrepare.shp","bgCablePrepare","ogr")

conn = psycopg2.connect("host='192.168.106.3' dbname='bg' port = '5432' user='postgres' password='megaprom2014'")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cur.execute('SELECT * FROM "bgSocket"')
sockets = cur.fetchall()
layer_to.startEditing()

for socket in sockets:
    print str(socket["idSocket"])+" socket"
    #cur.execute('SELECT * FROM "bgCable" where "idSocketTo" = %s'%str(socket["idSocket"]))
    cur.execute('SELECT "bgCable"."idCable",  "bgCable"."NumFrom", "bgCable"."NumTo", COUNT("idFiber") as "FiberCount", "HasInverseGeometry"\
                         FROM "bgCable" INNER JOIN "bgGroup" on "bgGroup"."idCable"="bgCable"."idCable"\
                         INNER JOIN "bgFiber" on "bgFiber"."idGroup"="bgGroup"."idGroup"\
                         WHERE "idSocketTo"=%s\
                         GROUP BY "bgCable"."idCable",  "bgCable"."NumFrom", "bgCable"."NumTo", "HasInverseGeometry"\
                         ORDER BY  "bgCable"."NumTo"'%str(socket["idSocket"]))
    cables = cur.fetchall()
    prevFiberCount=0
    for cable in cables:
         print cable
         it = layer_to.getFeatures(QgsFeatureRequest().setFilterExpression ( u'"id" = %s' %str(cable["idCable"])))
        
         for feature in it:
             geom = feature.geometry()
             nLine = QgsGeometry(geom)
             if cable["HasInverseGeometry"] ==True:
                 XN=QgsPoint(nLine.vertexAt(0))
                 lastpointindexN=0
             else:
                 lastpointindexN= len(geom.asPolyline()) - 1
                 XN=QgsPoint(nLine.vertexAt(lastpointindexN))

                 #create line2
             shiftY=prevFiberCount*0.000001
             line2_start = QgsPoint(XN.x()-shiftX*1.5,XN.y()-shiftY)
             line2_end = QgsPoint(XN.x()-shiftX,XN.y()-shiftY)
             line2 = QgsGeometry.fromPolyline([line2_start,line2_end])
             feat = QgsFeature()
             feat.setGeometry(line2)
             copyAttribute(feature, feat, 2, socket["idSocket"])
             (res, outFeats) = layer_to.dataProvider().addFeatures([ feat ])
                #create line3
             line3_start = QgsPoint(XN.x()-shiftX,XN.y() - shiftY)
             line3_end = QgsPoint(XN.x()-shiftX*0.5,XN.y() - shiftY)
             line3 = QgsGeometry.fromPolyline([line3_start,line3_end])
             feat1 = QgsFeature()
             feat1.setGeometry(line3)
             copyAttribute(feature, feat1, 3, socket["idSocket"])
             (res, outFeats) = layer_to.dataProvider().addFeatures([ feat1 ])
             if cable["HasInverseGeometry"] ==False:
                nLine.moveVertex(XN.x()-shiftX*1.5, XN.y() - shiftY, lastpointindexN)
                layer_to.editBuffer().changeGeometry( feature.id(), nLine );
                nLine.insertVertex(XN.x()-shiftX*2, XN.y() - shiftY, lastpointindexN)
                layer_to.editBuffer().changeGeometry( feature.id(), nLine );
             else:
                 nLine.moveVertex(XN.x()-shiftX*1.5, XN.y() - shiftY, lastpointindexN)
                 layer_to.editBuffer().changeGeometry( feature.id(), nLine );
                 nLine.insertVertex(XN.x()-shiftX*2, XN.y() - shiftY, lastpointindexN+1)
                 layer_to.editBuffer().changeGeometry( feature.id(), nLine );
             prevFiberCount=prevFiberCount+cable["FiberCount"]+1
     
    cur.execute('SELECT "bgCable"."idCable",  "bgCable"."NumFrom", "bgCable"."NumTo", COUNT("idFiber") as "FiberCount", "HasInverseGeometry" \
                        FROM "bgCable" \
                        INNER JOIN "bgGroup" on "bgGroup"."idCable"="bgCable"."idCable"\
                        INNER JOIN "bgFiber" on "bgFiber"."idGroup"="bgGroup"."idGroup"\
                        WHERE "idSocketFrom"=%s\
                        GROUP BY "bgCable"."idCable",  "bgCable"."NumFrom", "bgCable"."NumTo", "HasInverseGeometry" ORDER BY  "bgCable"."NumFrom"'%str(socket["idSocket"]))

    cables = cur.fetchall()
    prevFiberCount=0
    for cable in cables:
         print cable
         it = layer_to.getFeatures(QgsFeatureRequest().setFilterExpression ( u'"id" = %s' %str(cable["idCable"])))
        
         for feature in it:
             geom = feature.geometry()
             nLine = QgsGeometry(geom)
             if cable["HasInverseGeometry"] ==True:
                 lastpointindexN= len(geom.asPolyline()) - 1
                 XN=QgsPoint(nLine.vertexAt(lastpointindexN))
             else:
                 XN=QgsPoint(nLine.vertexAt(0))
                 lastpointindexN=0

                 #create line4
             shiftY=prevFiberCount*0.000001    
             line2_start = QgsPoint(XN.x()+shiftX*0.5,XN.y()-shiftY)
             line2_end = QgsPoint(XN.x()+shiftX,XN.y()-shiftY)
             line2 = QgsGeometry.fromPolyline([line2_start,line2_end])
             feat = QgsFeature()
             feat.setGeometry(line2)
             copyAttribute(feature, feat, 4, socket["idSocket"])
             (res, outFeats) = layer_to.dataProvider().addFeatures([ feat ])
                #create line5
             line3_start = QgsPoint(XN.x()+shiftX,XN.y() - shiftY)
             line3_end = QgsPoint(XN.x()+shiftX*1.5,XN.y() - shiftY)
             line3 = QgsGeometry.fromPolyline([line3_start,line3_end])
             feat1 = QgsFeature()
             feat1.setGeometry(line3)
             copyAttribute(feature, feat1, 5, socket["idSocket"])
             (res, outFeats) = layer_to.dataProvider().addFeatures([ feat1 ])
             
             if cable["HasInverseGeometry"] ==False:
                 nLine.insertVertex(XN.x()+shiftX*2, XN.y() - shiftY, lastpointindexN+1)
                 layer_to.editBuffer().changeGeometry( feature.id(), nLine );
                 nLine.moveVertex(XN.x()+shiftX*1.5, XN.y() - shiftY, lastpointindexN)
                 layer_to.editBuffer().changeGeometry( feature.id(), nLine );
             else:
                 nLine.moveVertex(XN.x()+shiftX*1.5, XN.y() - shiftY, lastpointindexN)
                 layer_to.editBuffer().changeGeometry( feature.id(), nLine );
                 nLine.insertVertex(XN.x()+shiftX*2, XN.y() - shiftY, lastpointindexN)
                 layer_to.editBuffer().changeGeometry( feature.id(), nLine );
             prevFiberCount=prevFiberCount+cable["FiberCount"]+1
             
layer_to.commitChanges()
QgsMapLayerRegistry.instance().addMapLayer(layer_to)

canvas = qgis.utils.iface.mapCanvas()
canvas.zoomScale(75) 

print 'Processing complete'        