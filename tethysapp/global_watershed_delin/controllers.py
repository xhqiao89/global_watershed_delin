from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    btnCompute = Button(display_text="Delineate watershed",
                    name="btnCompute",
                    attributes="onclick=app.computeWatershed()",
                    submit=False)

    context = {'btnCompute': btnCompute}

    return render(request, 'global_watershed_delin/home.html', context)

def sample(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'global_watershed_delin/sample.html', context)