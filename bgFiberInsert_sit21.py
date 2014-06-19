from PyQt4.QtCore import *
from qgis.core import *
import psycopg2
import psycopg2.extras
import qgis.utils
crs = QgsCoordinateReferenceSystem("EPSG:4326 - WGS 84")

conn = psycopg2.connect("host='192.168.106.3' dbname='bg' port = '5432' user='postgres' password='megaprom2014'")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

fiberFields = QgsFields()
fiberFields.append( QgsField('id', QVariant.Int) )
fiberFields.append( QgsField("idCable", QVariant.Int) )
fiberFields.append( QgsField("idColor", QVariant.Int) )
fiberFields.append( QgsField("subscript", QVariant.String) )
fiberFields.append( QgsField("idFiber", QVariant.Int) )
fiberFields.append( QgsField("idLineType", QVariant.Int) )
fiberFields.append( QgsField("idSocket", QVariant.Int) )
fiberFieldsCount = 7

#layer = QgsVectorLayer("D:/GIS/Murmansk City/bgFiber.shx","bgFiber","ogr")
canvas = qgis.utils.iface.mapCanvas()


layerMap = QgsMapLayerRegistry.instance().mapLayers()

for name, layer in layerMap.iteritems():
     if layer.type() == QgsMapLayer.VectorLayer and layer.name() == "bgFiber":
         QgsMapLayerRegistry.instance().removeMapLayer( layer.id() )
         
layer=QgsVectorLayer("D:/GIS/Murmansk City/bgFiber.shx","bgFiber","ogr")
layer.startEditing()

inSocketNumber = 0
it = layer.getFeatures(QgsFeatureRequest().setFilterExpression ( 'id is NULL'))
for feature in it:
     idFeatureFrom= 0
     idFeatureTo= 0
     idSocket= 0
     
     geom = feature.geometry()
     nLine = QgsGeometry(geom)
     X0=QgsPoint(nLine.vertexAt(0))
     lastpointindexN= len(geom.asPolyline()) - 1
     XN=QgsPoint(nLine.vertexAt(lastpointindexN))
     of = layer.getFeatures(QgsFeatureRequest().setFilterExpression ( 'id is NOT NULL'))
     for feat in of:
         if (feat["idColor"] and feat["idColor"]<>-1) :
            geom1 = feat.geometry()
            nLine1 = QgsGeometry(geom1)
            X01=QgsPoint(nLine1.vertexAt(0))
            lastpointindexN1= len(geom1.asPolyline()) - 1
            XN1=QgsPoint(nLine1.vertexAt(lastpointindexN1))
            if (abs(X01.x() - XN.x())<=0.0000001 and abs(X01.y() - XN.y())<=0.0000001) or (abs(XN1.x() - XN.x())<=0.0000001 and abs(XN1.y() - XN.y())<=0.0000001):
                idFeatureTo=feat["idFiber"];
                print str(idFeatureTo)+" to"
            if (abs(XN1.x() - X0.x())<=0.0000001 and abs(XN1.y() - X0.y())<=0.0000001) or (abs(X01.x() - X0.x())<=0.0000001 and abs(X01.y() - X0.y())<=0.0000001):
                idFeatureFrom=feat["idFiber"];
                idSocket = feat["idSocket"];
                print str(idFeatureFrom)+" from"
                print str(idSocket)+" idSocket"
     if (idFeatureFrom<>0 and idFeatureTo<>0):
#         try:
            #inSocketNumber = inSocketNumber + 1
            
            
            cur.execute('select max("inSocketNumber") from "bgFiberJoin" where "idSocket"=%s' %(str(idSocket)))
            inSocketNumber = int(cur.fetchall()[0][0])+1
            namedict = ({"idFiberFrom":idFeatureFrom, "idFiberTo":idFeatureTo, "idSocket":idSocket, "inSocketNumber":inSocketNumber})       
            cur.execute('INSERT INTO "bgFiberJoin"("idFiberFrom","idFiberTo", "idSocket", "inSocketNumber") VALUES (%(idFiberFrom)s, %(idFiberTo)s, %(idSocket)s, %(inSocketNumber)s)',namedict)
            conn.commit()
            cur.execute('select * from "bgFiberJoin" where "idFiberFrom" = %s and "idFiberTo" = %s' %(str(idFeatureFrom), str(idFeatureTo)))
            row = cur.fetchall()[0]
            print row[0]
            #join
            iter1 = layer.getFeatures( QgsFeatureRequest().setFilterExpression( u'"idFiber" = %s AND idSocket = %s' %(str(idFeatureFrom), str(idSocket))) )
            for fiter1 in iter1:
             geomiter1 = fiter1.geometry()
             if int(fiter1['idLineType']) == 3:
                 pnt1 = geomiter1.vertexAt(1)
                 sign=1.0
             else:
                 pnt1 = geomiter1.vertexAt(0)
                 sign = -1.0
             print str(fiter1['idLineType']) +' ,' + str(fiter1['id'])
             print 'iter2'
             iter2 = layer.getFeatures( QgsFeatureRequest().setFilterExpression( u'"idFiber" = %s AND idSocket = %s' %(str(idFeatureTo), str(idSocket))) )
             for fiter2 in iter2:
                 geomiter2 = fiter2.geometry()
                 if int(fiter2['idLineType']) == 3:
                     pnt2 = geomiter2.vertexAt(1)
                 else:
                     pnt2 = geomiter2.vertexAt(0)
                 print str(fiter2['idLineType']) +' ,' + str(fiter2['id'])
    
                 print pnt1.x()
                 print pnt1.y()

                 NewFeat = QgsFeature()
     
                 if pnt1.y()==pnt2.y():
                     NewFeat.setGeometry(QgsGeometry.fromPolyline([pnt1, pnt2]))
                 else:
                     print 'distance:' + str(pnt2.x()-pnt1.x())
                     if sign == 1:
                         shift = 0.000006 + 0.00006 * int(inSocketNumber)/17.0
                     else:
                         shift = -0.000006 - 0.00006 * (17 - int(inSocketNumber))/17.0
                     print shift
                     pnt3 = QgsPoint(pnt1.x() + shift, pnt1.y())
                     pnt4 = QgsPoint(pnt1.x() + shift, pnt2.y())
                     NewFeat.setGeometry(QgsGeometry.fromPolyline([pnt1, pnt3, pnt4, pnt2]))
                 NewFeat.setFields(fiberFields)
                 #NewFeat.setAttribute(0, 9900+ int(row['idFiberJoin']))
                 NewFeat["id"] = 990000+ int(row['idFiberJoin'])
                 NewFeat["idColor"] = -1
                 NewFeat["idFiber"] = -1
                 NewFeat["idCable"] = -1
                 NewFeat["idLineType"] = 0
                 NewFeat["idSocket"] = idSocket
                 
                 layer.dataProvider().addFeatures( [ NewFeat ] )
                 #layer.dataProvider().deleteFeatures([feature])
                 layer.deleteFeature(feature.id())
                 
#         except:
#            print "Exist  in table: From " + str(idFeatureFrom) + " To: " + str(idFeatureTo)        
         
         
         


#     selectRect=QgsRectangle(X0.x()-0.00001,X0.y()-0.0000005,X0.x()+0.00001,X0.y()+0.0000005)
#     iter=layer.select(selectRect, False);
#     features = layer.selectedFeatures()
#     for feature1 in features:
#         if (feature1["idColor"] and feature1["idColor"]<>-1) :
#             idFeatureFrom=feature1["idFiber"];
#             print str(idFeatureFrom)+" from"
#     layer.removeSelection();
#     selectRect=QgsRectangle(XN.x()-0.00001,XN.y()-0.0000005,XN.x()+0.00001,XN.y()+0.0000005)
#     iter=layer.select(selectRect, True);
#     features = layer.selectedFeatures()
#     for feature1 in features:
#         if (feature1["idColor"] and feature1["idColor"]<>-1) :
#             idFeatureTo=feature1["idFiber"];
#             print str(idFeatureTo)+" to"
             #cur.execute('SELECT * FROM "bgCable" where "idCable" = %s'%str(feature1["idCable"]))
         
#     layer.removeSelection();
#conn.commit()
cur.close()
layer.loadNamedStyle("D:/GIS/Murmansk City/bgFiber-BW-style.qml")
layer.commitChanges()
QgsMapLayerRegistry.instance().addMapLayer(layer)
print "Processing complete"

