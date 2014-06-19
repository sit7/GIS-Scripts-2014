from PyQt4.QtCore import QVariant
from qgis.core import *
import qgis.utils
import shapely.wkt as swkt

import psycopg2
import psycopg2.extras

conn = psycopg2.connect("host='192.168.106.3' dbname='bg' port = '5432' user='postgres' password='megaprom2014'")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

layer = QgsVectorLayer("E:/GIS/Murmansk City/bgFiber.shp","bgFiber","ogr")

fiberFields = QgsFields()
fiberFields.append( QgsField('id', QVariant.Int) )
fiberFields.append( QgsField("idCable", QVariant.Int) )
fiberFields.append( QgsField("idColor", QVariant.Int) )
fiberFields.append( QgsField("subscript", QVariant.String) )
fiberFields.append( QgsField("idFiber", QVariant.Int) )
fiberFields.append( QgsField("idLineType", QVariant.Int) )
fiberFields.append( QgsField("idSocket", QVariant.Int) )
fiberFieldsCount = 7

cur.execute('SELECT * FROM "bgSocket"')

sockets = cur.fetchall()

for socket in sockets:
     idSocket = socket["idSocket"]
     cur.execute('SELECT * FROM "bgFiberJoin" WHERE "idSocket" = %s' %str(idSocket))
     rows = cur.fetchall()

     for row in rows:
         print row['idFiberJoin']
         iter1 = layer.getFeatures( QgsFeatureRequest().setFilterExpression( u'"idFiber" = %s AND idSocket = %s' %(str(row['idFiberFrom']), str(idSocket))) )
         for feature in iter1:
             geom = feature.geometry()
             if int(feature['idLineType']) == 3:
                 pnt1 = geom.vertexAt(1)
                 sign=1.0
             else:
                 pnt1 = geom.vertexAt(0)
                 sign = -1.0
             print str(feature['idLineType']) +' ,' + str(feature['id'])
             print 'iter2'
             iter2 = layer.getFeatures( QgsFeatureRequest().setFilterExpression( u'"idFiber" = %s AND idSocket = %s' %(str(row['idFiberTo']), str(idSocket))) )
             for feature in iter2:
                 geom = feature.geometry()
                 if int(feature['idLineType']) == 3:
                     pnt2 = geom.vertexAt(1)
                 else:
                     pnt2 = geom.vertexAt(0)
                 print str(feature['idLineType']) +' ,' + str(feature['id'])
    
                 print pnt1.x()
                 print pnt1.y()

                 feat = QgsFeature()
         
                 if abs(pnt1.y()-pnt2.y())<0.0000000001:
                     feat.setGeometry(QgsGeometry.fromPolyline([pnt1, pnt2]))
                 else:
                     print 'distance:' + str(pnt2.x()-pnt1.x())
                     print pnt1.y()
                     print pnt2.y()
                     if sign == 1:
                         shift = 0.000006 + 0.00006 * int(row['inSocketNumber'])/17.0
                     else:
                         shift = -0.000006 - 0.00006 * (17 - int(row['inSocketNumber']))/17.0
                     print shift
                     pnt3 = QgsPoint(pnt1.x() + shift, pnt1.y())
                     pnt4 = QgsPoint(pnt1.x() + shift, pnt2.y())
                     feat.setGeometry(QgsGeometry.fromPolyline([pnt1, pnt3, pnt4, pnt2]))
                 feat.setFields(fiberFields)
                 feat.setAttribute(0, 9900+ int(row['idFiberJoin']))
                 feat["idColor"] = -1

                 (res, outFeats) = layer.dataProvider().addFeatures( [ feat ] )


print 'Processing complete'