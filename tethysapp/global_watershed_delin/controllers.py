from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button,TextInput


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    btnCompute = Button(display_text="Delineate watershed",
                    name="btnCompute",
                    attributes="onclick=app.computeWatershed()",
                    submit=False)
    btnDownload = Button(display_text="Download results",
                name="btnDownload",
                attributes="onclick=app.run_download_results()",
                submit=False)

    context = {'btnCompute': btnCompute,
               'btnDownload': btnDownload}


    return render(request, 'global_watershed_delin/home.html', context)

def sample(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'global_watershed_delin/sample.html', context)