import arcpy

path = arcpy.env.workspace = "C://SyK//01_PORTALES//data//PointAdd_41.mdb"
fc = "PointAdd_41"
fc_layer = fc + "_lyr"
fcCarto = "C://SyK//01_PORTALES//data//41_PORTAL_PK.shp"
nFC = fc + "_empty"
fc_join = fc + "_join0"
geomType = arcpy.Describe(fc).shapeType
sr = arcpy.Describe(fc).spatialReference
exp = "NOMBRE = ''"
srCarto = arcpy.Describe(fcCarto).spatialReference

arcpy.MakeFeatureLayer_management(fc, fc_layer)
selection = arcpy.SelectLayerByAttribute_management(fc_layer, "NEW_SELECTION", exp)
arcpy.CreateFeatureclass_management(path, nFC, geomType, fc, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", sr)
arcpy.Append_management(selection, nFC, "TEST")

arcpy.Project_management(nFC, "nFC_project", srCarto.GCS)
arcpy.SpatialJoin_analysis("nFC_project", fcCarto, "fc_join_aux", "JOIN_ONE_TO_ONE", True,
                           match_option="CLOSEST")
arcpy.Project_management("fc_join_aux", fc_join, sr.GCS)
arcpy.Near_analysis(fc_join, fcCarto)
arcpy.Delete_management("nFC_project")
arcpy.Delete_management("fc_join_aux")

print "Proceso finalizado"