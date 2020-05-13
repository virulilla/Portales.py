# coding=utf-8
# ¡Importante!: El interprete debe ser Pyhton 2.7 C:\Python27\ArcGIS10.X\python.exe (entorno x32)

import arcpy, glob

arcpy.env.overwriteOutput = True

# Se solicita el directorio donde se encuentran las mdbs de HERE
arcpy.env.workspace = arcpy.GetParameterAsText(0)

# Se solicita el directorio donde se encuentran los datos de CartoCiudad
ruta_Carto = arcpy.GetParameterAsText(1)

# Se solicita la distancia para hacer la intersección espacial
dist = arcpy.GetParameterAsText(2)

# Se recorren todas las mdbs que se encuentran en la carpeta indicada por el usuario y
# en cada iteración se establece cada una de ellas como workspace
for workspace in arcpy.ListWorkspaces():
    path = arcpy.env.workspace = workspace

    # Se eliminan las FC residuales de ejecuciones anteriores
    for fc in arcpy.ListFeatureClasses():
        if "_empty" in fc:
            arcpy.Delete_management(fc)
        if "_project" in fc:
            arcpy.Delete_management(fc)
        if ("_join" + str(dist)) in fc:
            arcpy.Delete_management(fc)

    # Se recorren todas FC de la mdb, entre las que ya no existe FC residuales
    for fc in arcpy.ListFeatureClasses():
        if not "_join" in fc:
            flag = 0
            nFC = fc + "_empty"
            fc_layer = fc + "_lyr"
            geomType = arcpy.Describe(fc).shapeType
            sr = arcpy.Describe(fc).spatialReference
            exp = "NOMBRE = ''"

            # Se seleccionan aquellos registros en los que el campo NOMBRE está vacío
            # SelectByAttribute no reconoce las FC de las mdbs, por ello se crea un layer (fc_layer)
            arcpy.MakeFeatureLayer_management(fc, fc_layer)
            selection = arcpy.SelectLayerByAttribute_management(fc_layer, "NEW_SELECTION", exp)

            # Si el FIDSet del objeto 'selection' tiene una longitud > 0, existen entidades seleccionadas, entonces:
            # Se crea una nueva FC (*_empty) dentro de la mdb con el mismo esquema que la clase de entidad original
            # Se añade la selección a la nueva FC (nFC)
            # Se hace el spatial_join, creando la nueva FC (fc_join)
            if len(arcpy.Describe(selection).FIDSet) > 0:
                arcpy.CreateFeatureclass_management(path, nFC, geomType, fc, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", sr)
                arcpy.Append_management(selection, nFC, "TEST")
                for fcCarto in glob.glob(ruta_Carto + "//*.shp"):
                    srCarto = arcpy.Describe(fcCarto).spatialReference
                    fc_join = fc + "_join" + str(dist)
                    # Se comprueba que los sistemas de referencia coincidan
                    # Para mejorar el rendimiento, la proyección se hace al SR que tenga la FC con menos entidades
                    # Después del SpatialJoin se proyecta la FC resultante al SR de nFC
                    if srCarto.name != sr.name:
                        arcpy.Project_management(nFC, "fcCarto_project", srCarto.GCS)
                        arcpy.SpatialJoin_analysis("fcCarto_project", fcCarto, "fc_join_aux", "JOIN_ONE_TO_MANY", True,
                                                   match_option="WITHIN_A_DISTANCE",
                                                   search_radius=str(dist) + " Meters")
                        arcpy.Project_management("fc_join_aux", fc_join, sr.GCS)
                        arcpy.Delete_management("fcCarto_project")
                        arcpy.Delete_management("fc_join_aux")
                    else:
                        arcpy.SpatialJoin_analysis(nFC, fcCarto, fc_join, "JOIN_ONE_TO_MANY", True,
                                                   match_option="WITHIN_A_DISTANCE",
                                                   search_radius=str(dist) + " Meters")

                    # Condición de parada del bucle (for fcCarto in glob.glob(ruta_Carto + "//*.shp"))
                    fields = arcpy.ListFields(fc_join)
                    campos = []
                    for field in fields:
                        campos.append(field.name)
                    with arcpy.da.SearchCursor(fc_join, campos) as cursor:
                        for row in cursor:
                            if not row[22] is None:
                                flag = -1
                                break
                        if flag == -1:
                            break

arcpy.AddMessage("Proceso finalizado")