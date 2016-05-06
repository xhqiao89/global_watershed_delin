from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button,TextInput
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
                attributes="onclick=app.upload_to_HS()",
                submit=False)

    context = {'btnCompute': btnCompute,
               'btnUpload': btnUpload}


    return render(request, 'global_watershed_delin/home.html', context)

# @csrf_exempt
def upload_to_hydroshare(request):

    return_json = {"status": "success"}
    if request.method == 'POST':
        get_data = request.POST

        watershed_geojson = get_data['geojson_str']
        print watershed_geojson

    return JsonResponse(return_json)


def sample(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'global_watershed_delin/sample.html', context)