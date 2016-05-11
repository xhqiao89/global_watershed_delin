from tethys_sdk.base import TethysAppBase, url_map_maker


class GlobalWatershedDelineationService(TethysAppBase):
    """
    Tethys app class for Global Watershed Delineation Service.
    """

    name = 'Global Watershed Delineation Service'
    index = 'global_watershed_delin:home'
    icon = 'global_watershed_delin/images/app_icon.png'
    package = 'global_watershed_delin'
    root_url = 'global-watershed-delin'
    color = '#3399FF'
    description = 'Place a brief description of your app here.'
    enable_feedback = False
    feedback_emails = []

        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='global-watershed-delin',
                           controller='global_watershed_delin.controllers.home'),
                    UrlMap(name='sample',
                           url='global-watershed-delin/sample',
                           controller='global_watershed_delin.controllers.sample'),
                    UrlMap(name='upload_to_hydroshare_ajax',
                           url='global-watershed-delin/upload-to-hydroshare',
                           controller='global_watershed_delin.controllers.upload_to_hydroshare'),
        )

        return url_maps