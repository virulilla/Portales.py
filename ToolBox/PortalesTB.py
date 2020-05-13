# coding=utf-8
# ¡Importante!: El interprete debe ser Pyhton 2.7 C:\Python27\ArcGIS10.X\python.exe (entorno x32)

import arcpy, glob, math

arcpy.env.overwriteOutput = True

# Se solicita el directorio donde se encuentran las mdbs de HERE
arcpy.env.workspace = arcpy.GetParameterAsText(0)

# Se solicita el directorio donde se encuentran los datos de CartoCiudad
ruta_Carto = arcpy.GetParameterAsText(1)

# Se solicita la distancia para hacer la intersección espacial
dist = arcpy.GetParameter(2)

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

                    # Se crea el nombre del archivo que almacenará el spatial join en función de la distancia
                    # introducida por el usuario
                    if dist == 0:
                        fc_join = fc + "_join0"
                    elif math.fmod(dist, 1) != 0:
                        fc_join = fc + "_join0" + str(dist).split(".")[1]
                    elif math.fmod(dist, 1) == 0:
                        fc_join = fc + "_join" + str(dist).split(".")[0]

                    # Se comprueba que los sistemas de referencia coincidan y si la distancia se ha introducido como
                    # parametro ya que este valor es opcional
                    # Para mejorar el rendimiento, la proyección se hace al SR que tenga la FC con menos entidades
                    # Después del SpatialJoin se proyecta la FC resultante al SR de nFC
                    srCarto = arcpy.Describe(fcCarto).spatialReference
                    if srCarto.name != sr.name and dist != 0:
                        arcpy.Project_management(nFC, "nFC_project", srCarto.GCS)
                        arcpy.SpatialJoin_analysis("nFC_project", fcCarto, "fc_join_aux", "JOIN_ONE_TO_ONE", True,
                                                   match_option="CLOSEST",
                                                   search_radius=str(dist) + " Meters")
                        arcpy.Project_management("fc_join_aux", fc_join, sr.GCS)
                        arcpy.Near_analysis(fc_join, fcCarto)
                        arcpy.Delete_management("nFC_project")
                        arcpy.Delete_management("fc_join_aux")
                    elif srCarto.name != sr.name and dist == 0:
                        arcpy.Project_management(nFC, "nFC_project", srCarto.GCS)
                        arcpy.SpatialJoin_analysis("nFC_project", fcCarto, "fc_join_aux", "JOIN_ONE_TO_ONE", True,
                                                   match_option="CLOSEST")
                        arcpy.Project_management("fc_join_aux", fc_join, sr.GCS)
                        arcpy.Near_analysis(fc_join, fcCarto)
                        arcpy.Delete_management("nFC_project")
                        arcpy.Delete_management("fc_join_aux")
                    elif srCarto.name == sr.name and dist != 0:
                        arcpy.SpatialJoin_analysis(nFC, fcCarto, fc_join, "JOIN_ONE_TO_ONE", True,
                                                   match_option="CLOSEST",
                                                   search_radius=str(dist) + " Meters")
                        arcpy.Near_analysis(fc_join, fcCarto)
                    elif srCarto.name == sr.name and dist == 0:
                        arcpy.SpatialJoin_analysis(nFC, fcCarto, fc_join, "JOIN_ONE_TO_ONE", True,
                                                   match_option="CLOSEST")
                        arcpy.Near_analysis(fc_join, fcCarto)

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