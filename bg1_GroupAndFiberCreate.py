from PyQt4.QtCore import QVariant
from qgis.core import *
import qgis.utils
import shapely.wkt as swkt

import psycopg2
import psycopg2.extras

conn = psycopg2.connect("host='192.168.106.3' dbname='bg' port = '5432' user='postgres' password='megaprom2014'")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

crs = QgsCoordinateReferenceSystem("EPSG:4326 - WGS 84")

fiberFields = QgsFields()
fiberFields.append( QgsField('id', QVariant.Int) )
fiberFields.append( QgsField("idCable", QVariant.Int) )
fiberFields.append( QgsField("idColor", QVariant.Int) )
fiberFields.append( QgsField("subscript", QVariant.String) )
fiberFields.append( QgsField("idFiber", QVariant.Int) )
fiberFields.append( QgsField("idLineType", QVariant.Int) )
fiberFields.append( QgsField("idSocket", QVariant.Int) )
fiberFieldsCount = 7

groupFields = QgsFields()
groupFields.append( QgsField("id", QVariant.Int) )
groupFields.append( QgsField("idCable", QVariant.Int) )
groupFields.append( QgsField("idColor", QVariant.Int) )
groupFields.append( QgsField("subscript", QVariant.String) )
groupFields.append( QgsField("Width", QVariant.Int) )
groupFieldsCount = 5


layerMap = QgsMapLayerRegistry.instance().mapLayers()
for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.VectorLayer and (layer.name() == "bgFiber" or layer.name() == "bgGroup"):
        QgsMapLayerRegistry.instance().removeMapLayer( layer.id() )

crs = QgsCoordinateReferenceSystem("EPSG:4326 - WGS 84")

writer = QgsVectorFileWriter("E:/GIS/Murmansk City/bgFiber.shp", "utf-8", fiberFields, QGis.WKBLineString, crs)
del writer

writer = QgsVectorFileWriter("E:/GIS/Murmansk City/bgGroup.shp", "utf-8", groupFields, QGis.WKBLineString, crs)
del writer

layer_from = QgsVectorLayer("E:/GIS/Murmansk City/bgCablePrepare.shp","","ogr")
layer_to = QgsVectorLayer("E:/GIS/Murmansk City/bgFiber.shp","bgFiber","ogr")
layer_to2 = QgsVectorLayer("E:/GIS/Murmansk City/bgGroup.shp","bgGroup","ogr")

#may be to delete ?
layer_to.setCoordinateSystem()
layer_to2.setCoordinateSystem()

layer_to.startEditing()
layer_to2.startEditing()

iter = layer_from.getFeatures()

for feature in iter:
     geom = feature.geometry()
     print feature["Comment"]
     if int(feature["idLineType"])==1:
         wkt = geom.exportToWkt()
         line = swkt.geom_from_wkt(wkt)
     
     cur.execute('SELECT "InCableN", "idFiber", "idCable", "bgFiber"."idColor", "ColorName" \
                        FROM "bgFiber" INNER JOIN "bgGroup" ON "bgFiber"."idGroup"="bgGroup"."idGroup" \
                        INNER JOIN "bgColor" ON "bgFiber"."idColor"="bgColor"."idColor" \
                        WHERE "bgGroup"."idCable"= %s', [feature["idCable"]])
     rows = cur.fetchall()
     
     for row in rows:
         #print "   ", row
         shift = (int(row['InCableN'])-1)*0.000001
         if feature["idLineType"]==1:
             line2 = line.parallel_offset(shift, feature["left_right"], join_style=2)
             wkt = line2.to_wkt()
             newgeom = QgsGeometry.fromWkt(wkt)
         else:
             pnt0 = geom.vertexAt(0)
             pnt1 = geom.vertexAt(1)
             newPnt0 = QgsPoint(pnt0.x(), pnt0.y()-shift)
             newPnt1 = QgsPoint(pnt1.x(), pnt1.y()-shift)
             newgeom = QgsGeometry.fromPolyline([newPnt0, newPnt1])
         feat = QgsFeature()
         feat.setGeometry(newgeom)
         feat.initAttributes(fiberFieldsCount)
         feat.setFields(fiberFields)
         feat.setAttribute(0, int(row['idFiber'])*100 + int(feature["idLineType"]))
         feat.setAttribute(1, feature['idCable'])
         if  int(feature["idLineType"])==3 or int(feature["idLineType"])==4:
             feat.setAttribute(3, row['ColorName'] + ' ' + str(int(row['InCableN'])))
             feat.setAttribute(6, feature["idSocket"])#idSocket = 1
         feat.setAttribute(2, row['idColor'])
         feat.setAttribute(4, row['idFiber'])
         feat.setAttribute(5, feature['idLineType'])
         (res, outFeats) = layer_to.dataProvider().addFeatures( [ feat ] )
         
     if  int(feature["idLineType"])==2 or int(feature["idLineType"])==5:
         cur.execute('SELECT "Number", "ColorName", "bgGroup"."idGroup", "bgGroup"."idColor", COUNT(*), MIN("InCableN") \
                             FROM "bgFiber" INNER JOIN "bgGroup" ON "bgFiber"."idGroup"="bgGroup"."idGroup" \
                             INNER JOIN "bgColor" ON "bgGroup"."idColor"="bgColor"."idColor" \
                             WHERE "bgGroup"."idCable" = %s \
                             GROUP BY "ColorName", "Number", "bgGroup"."idGroup", "bgGroup"."idColor"', [feature["idCable"]])
         rows = cur.fetchall()
         for row in rows:
             pnt0 = geom.vertexAt(0)
             pnt1 = geom.vertexAt(1)
             shift = (int(row['min'])-1)*0.000001 + (int(row['count'])-1) * 0.0000005
             newPnt0 = QgsPoint(pnt0.x(), pnt0.y()-shift)
             newPnt1 = QgsPoint(pnt1.x(), pnt1.y()-shift)
             newgeom = QgsGeometry.fromPolyline([newPnt0, newPnt1])
             feat = QgsFeature()
             feat.setGeometry(newgeom)
             feat.initAttributes(groupFieldsCount)
             feat.setFields(groupFields)
             feat.setAttribute(0, row['idGroup'])
             feat.setAttribute(1, feature["idCable"])
             feat.setAttribute(2, row['idColor'])
             feat.setAttribute(3, row['ColorName'] + ' ' + str(row['Number']))
             feat.setAttribute(4, int(row['count']))
             (res, outFeats) = layer_to2.dataProvider().addFeatures( [ feat ] )

layer_to2.commitChanges()
layer_to.commitChanges()

layer_to.loadNamedStyle("E:/GIS/Murmansk City/bgFiber-BW-style.qml")
layer_to2.loadNamedStyle("E:/GIS/Murmansk City/bgGroup-BW-style.qml")
QgsMapLayerRegistry.instance().addMapLayer(layer_to)
QgsMapLayerRegistry.instance().addMapLayer(layer_to2)

canvas = qgis.utils.iface.mapCanvas()
canvas.zoomScale(75) 

print 'Processing complete.'