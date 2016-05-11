import tempfile
import shutil
import os
import traceback
import osgeo.osr as osr
import osgeo.ogr as ogr
import zipfile

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button,TextInput
from django.http import JsonResponse,FileResponse
from django.views.decorators.csrf import csrf_exempt
from hs_restclient import HydroShare, HydroShareAuthBasic
from oauthlib.oauth2 import TokenExpiredError
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
#from osgeo import ogr

hs_hostname = "www.hydroshare.org"

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    btnCompute = Button(display_text="Delineate watershed",
                    name="btnCompute",
                    attributes="onclick=app.computeWatershed()",
                    submit=False)
    btnUpload = Button(display_text="Upload to HydroShare",
                name="btnUpload",
                attributes="",
                submit=False)

    context = {'btnCompute': btnCompute,
               'btnUpload': btnUpload}


    return render(request, 'global_watershed_delin/home.html', context)

def getOAuthHS(request):

    client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", "None")
    client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", "None")

    # this line will throw out from django.core.exceptions.ObjectDoesNotExist if current user is not signed in via HydroShare OAuth
    token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']
    auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
    hs = HydroShare(auth=auth, hostname=hs_hostname)

    return hs


def upload_to_hydroshare(request):

    temp_dir = None
    try:
        return_json = {}
        if request.method == 'POST':
            get_data = request.POST

            watershed_geojson_str = str(get_data['geojson_str'])

            r_title = str(get_data['r_title'])
            r_type = str(get_data['r_type'])
            r_abstract = str(get_data['r_abstract'])
            r_keywords_raw = str(get_data['r_keywords'])
            r_keywords = r_keywords_raw.split(',')

            hs = getOAuthHS(request)

            #create a temp directory to save all files
            temp_dir = tempfile.mkdtemp()

            #generate geojson file
            watershed_geojson_path = os.path.join(temp_dir, "watershed.geojson")

            with open(watershed_geojson_path, 'w') as fd:
                fd.write(watershed_geojson_str)

            #generate kml file
            watershed_kml_path = os.path.join(temp_dir, "watershed.kml")

            #extract geometry
            watershed_geometry =ogr.CreateGeometryFromJson(watershed_geojson_str)
            # print watershed_geometry

            watershed_kml_body = watershed_geometry.ExportToKML()
            watershed_kml_header = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Placemark>'
            watershed_kml_foot = '</Placemark></kml>'
            watershed_kml = watershed_kml_header + watershed_kml_body + watershed_kml_foot

            with open(watershed_kml_path, 'w') as fd:
                fd.write(watershed_kml)

            shpfile_name = "watershed"
            #generate shapefile
            watershed_shpfile_path = os.path.join(temp_dir, shpfile_name)
            print watershed_shpfile_path

            driver = ogr.GetDriverByName("ESRI Shapefile")
            # create the data source
            data_source = driver.CreateDataSource(watershed_shpfile_path)
            # create the spatial reference, WGS84
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            # create the layer
            layer = data_source.CreateLayer("watershed", srs, ogr.wkbPolygon)
            layer.CreateField(ogr.FieldDefn("Latitude", ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn("Longitude", ogr.OFTReal))
            feature = ogr.Feature(layer.GetLayerDefn())
            # Export geometry to WKT
            # watershed_wkt = watershed_geometry.ExportToWkt()
            # Set the feature geometry using the point
            feature.SetGeometry(watershed_geometry)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)

            # Destroy the feature to free resources
            feature.Destroy()
            # Destroy the data source to free resources
            data_source.Destroy()

            watershed_shp_path = watershed_shpfile_path + "/" + shpfile_name + ".shp"
            watershed_shx_path = watershed_shpfile_path + "/" + shpfile_name + ".shx"
            watershed_dbf_path = watershed_shpfile_path + "/" + shpfile_name + ".dbf"
            watershed_prj_path = watershed_shpfile_path + "/" + shpfile_name + ".prj"

            if os.path.exists(watershed_geojson_path):
                geojson_resource_id = hs.createResource(r_type, r_title, resource_file=watershed_geojson_path,
                                                      keywords=r_keywords, abstract=r_abstract)
                resource_id = hs.addResourceFile(geojson_resource_id, watershed_kml_path)
                resource_id = hs.addResourceFile(geojson_resource_id, watershed_shp_path)
                resource_id = hs.addResourceFile(geojson_resource_id, watershed_shx_path)
                resource_id = hs.addResourceFile(geojson_resource_id, watershed_dbf_path)
                resource_id = hs.addResourceFile(geojson_resource_id, watershed_prj_path)
                return_json['success'] = 'File uploaded successfully!'
                return_json['newResource'] = resource_id
            else:
                raise

    except ObjectDoesNotExist as e:
        print str(e)
        return_json['error'] = 'Login timed out! Please re-sign in with your HydroShare account.'
    except TokenExpiredError as e:
        print str(e)
        return_json['error'] = 'Login timed out! Please re-sign in with your HydroShare account.'
    except Exception, err:
        if "401 Unauthorized" in str(err):
            return_json['error'] = 'Username or password invalid.'
        elif "400 Bad Request" in str(err):
            return_json['error'] = 'File uploaded successfully despite 400 Bad Request Error.'
        else:
            traceback.print_exc()
            return_json['error'] = 'HydroShare rejected the upload for some reason.'

    finally:
        if temp_dir != None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    return JsonResponse(return_json)

def download_results(request):

    temp_dir = None
    try:
        return_json = {}
        if request.method == 'POST':
            get_data = request.POST

            watershed_geojson_str = str(get_data['geojson_str'])

            #create a temp directory to save all files
            temp_dir = tempfile.mkdtemp()

            #generate geojson file
            watershed_geojson_path = os.path.join(temp_dir, "watershed.geojson")

            with open(watershed_geojson_path, 'w') as fd:
                fd.write(watershed_geojson_str)

            #generate kml file
            watershed_kml_path = os.path.join(temp_dir, "watershed.kml")

            #extract geometry
            watershed_geometry =ogr.CreateGeometryFromJson(watershed_geojson_str)
            # print watershed_geometry

            watershed_kml_body = watershed_geometry.ExportToKML()
            watershed_kml_header = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Placemark>'
            watershed_kml_foot = '</Placemark></kml>'
            watershed_kml = watershed_kml_header + watershed_kml_body + watershed_kml_foot

            with open(watershed_kml_path, 'w') as fd:
                fd.write(watershed_kml)

            shpfile_name = "watershed"
            #generate shapefile
            watershed_shpfile_path = os.path.join(temp_dir, shpfile_name)

            driver = ogr.GetDriverByName("ESRI Shapefile")
            # create the data source
            data_source = driver.CreateDataSource(watershed_shpfile_path)
            # create the spatial reference, WGS84
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            # create the layer
            layer = data_source.CreateLayer("watershed", srs, ogr.wkbPolygon)
            layer.CreateField(ogr.FieldDefn("Latitude", ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn("Longitude", ogr.OFTReal))
            feature = ogr.Feature(layer.GetLayerDefn())
            # Export geometry to WKT
            # watershed_wkt = watershed_geometry.ExportToWkt()
            # Set the feature geometry using the point
            feature.SetGeometry(watershed_geometry)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)

            # Destroy the feature to free resources
            feature.Destroy()
            # Destroy the data source to free resources
            data_source.Destroy()

            watershed_shp_path = watershed_shpfile_path + "/" + shpfile_name + ".shp"
            watershed_shx_path = watershed_shpfile_path + "/" + shpfile_name + ".shx"
            watershed_dbf_path = watershed_shpfile_path + "/" + shpfile_name + ".dbf"
            watershed_prj_path = watershed_shpfile_path + "/" + shpfile_name + ".prj"

            watershed_zip_path = os.path.join(temp_dir, "watershed.zip")
            items = [watershed_geojson_path, watershed_shp_path, watershed_prj_path, watershed_shx_path, watershed_dbf_path, watershed_kml_path]
            watershed_zip_file = zipfile.ZipFile(watershed_zip_path, "w")

            for item in items:
                watershed_zip_file.write(item)

            watershed_zip_file.close()
            print watershed_zip_file

            return_json['success'] = 'Success'

            response = FileResponse(open(watershed_zip_path, 'rb'), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="' + shpfile_name + '.zip"'
            response['Content-Length'] = os.path.getsize(watershed_zip_path)

            return response
    except:
        return_json['error'] = 'Error'


    finally:
        if temp_dir != None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

