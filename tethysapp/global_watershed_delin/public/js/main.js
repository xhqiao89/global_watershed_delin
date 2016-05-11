require([
        "dojo/dom",
        "dojo/_base/Color",
        "dojo/cookie",
        "dijit/Dialog",
        "dijit/form/Button",
        "dijit/form/TextBox",
          "esri/map",
          "esri/dijit/Search",
          "esri/graphic",
          "esri/graphicsUtils",
          "esri/tasks/Geoprocessor",
          "esri/tasks/FeatureSet",
          "esri/layers/ArcGISTiledMapServiceLayer",
          "esri/layers/GraphicsLayer",
          "esri/symbols/SimpleMarkerSymbol",
          "esri/symbols/SimpleFillSymbol",
          "esri/symbols/CartographicLineSymbol"
    ],
    function(dom, Color, Cookie, Dialog, Button, TextBox, Map, Search, Graphic, graphicsUtils, Geoprocessor, FeatureSet, ArcGISTiledMapServiceLayer, GraphicsLayer, SimpleMarkerSymbol, SimpleFillSymbol, CartographicLineSymbol){

        var map, gp;
        var featureSet = new FeatureSet();

        //Initialize Map
        map = new Map("mapDiv", {
          //basemap: "topo",
          center: [-102, 41],
          zoom: 4
        });

        //Search function
        var search = new Search({
            map: map
         }, "search");

        search.startup();

        var basemap = new ArcGISTiledMapServiceLayer("https://server.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer");
        var tempPoint = new GraphicsLayer();
        var watersheds = new GraphicsLayer();
        map.addLayers([basemap, tempPoint, watersheds]);

        //Set GP Symbology
        var outline = new CartographicLineSymbol(CartographicLineSymbol.STYLE_SOLID, new Color([0,0,0,1]), 2);
        outline.setCap(CartographicLineSymbol.CAP_ROUND);
        outline.setJoin(CartographicLineSymbol.JOIN_ROUND);

        var pointSymbol = new SimpleMarkerSymbol();
        pointSymbol.setStyle(SimpleMarkerSymbol.STYLE_CIRCLE);
        pointSymbol.setSize("10");
        pointSymbol.setColor(new Color([59, 148, 0, 1]));
        pointSymbol.setOutline(outline);

        var snapSymbol = new SimpleMarkerSymbol();
        snapSymbol.setStyle(SimpleMarkerSymbol.STYLE_CIRCLE);
        snapSymbol.setSize("10");
        snapSymbol.setColor(new Color([0, 255, 0, 1]));
        snapSymbol.setOutline(outline);

        var polySymbol = new SimpleFillSymbol();
        polySymbol.setColor(new Color([55,138,73,.25]));
        polySymbol.setOutline(outline);

        //Add Watershed Delineation Geoprocessing Function
        gp = new Geoprocessor("https://hydro.arcgis.com/arcgis/rest/services/Tools/Hydrology/GPServer/Watershed");
        //gp = new Geoprocessor("https://utility.arcgis.com/usrsvcs/appservices/jscdO6XKCTrf3vOM/rest/services/Tools/Hydrology/GPServer/Watershed");

        gp.setOutSpatialReference({wkid: 102100});
        map.on("click", addPoint);

     function addPoint(evt) {
         tempPoint.clear();
         watersheds.clear();
         map.graphics.clear();

         var graphic = new Graphic(evt.mapPoint, pointSymbol);
         tempPoint.add(graphic);

         var features = [];
         features.push(graphic);
         featureSet.features = features;
      }

      function computeWatershed(evt) {

        var params = {
          "InputPoints": featureSet,
          "SnapDistance": "5000",
          "SnapDistanceUnits": "Meters",
          "SourceDatabase": "FINEST",
          "Generalize": "True"
        };
        gp.submitJob(params, completeCallback, statusCallback, function(error){
        console.log("Error", error, params);
        window.alert("Sorry, we do not have data for this region at your requested resolution");
        });
        }

    function statusCallback(jobInfo) {
        console.log(jobInfo.jobStatus);
        if (jobInfo.jobStatus === "esriJobSubmitted") {
          $("#delinstatus").html("<h7 style='color:blue'><b>Job submitted...</b></h7>");
        } else if (jobInfo.jobStatus === "esriJobExecuting") {
            $("#delinstatus").html("<h7 style='color:red;'><b>Calculating...</b></h7>");
        } else if (jobInfo.jobStatus === "esriJobSucceeded") {
            $("#delinstatus").html("<h7 style='color:green;'><b>Succeed!</b></h7>");
        }
      }

      function completeCallback(jobInfo){
        gp.getResultData(jobInfo.jobId, "WatershedArea", drawWatershed);
        gp.getResultData(jobInfo.jobId, "SnappedPoints", drawSnappedPoint);
      }

      function drawWatershed(results) {
        console.log(results);
        var features = results.value.features;
        for (var f=0, fl=features.length; f<fl; f++) {
            var feature = features[f];
            feature.setSymbol(polySymbol);
            watersheds.add(feature);
                    }
          map.setExtent(graphicsUtils.graphicsExtent(watersheds.graphics), true);
          console.log(watersheds.graphics[0].geometry);

          //convert watershed polygon to geojson file
          //var watershed_geojson = Terraformer.ArcGIS.parse(watersheds.graphics[0].geometry);

      }

      function drawSnappedPoint(results) {
        console.log(results);
        var features = results.value.features;
        for (var f=0, fl=features.length; f<fl; f++) {
            var feature = features[f];
            feature.setSymbol(snapSymbol);
            map.graphics.add(feature);
        }
      }
        function requestSucceeded(data) {
              console.log("Data: ", data); // print the data to browser's console
            }

        function requestFailed(error) {
              console.log("Error: ", error.message);
            }

        $('#hydroshare-proceed').on('click', function (){
            //convert watershed polygon to geojson file
            var watershed_geojson = Terraformer.ArcGIS.parse(watersheds.graphics[0].geometry);
            console.log(watershed_geojson);
            // Using dojo.xhrGet, as we simply want to retrieve information
            var resourceTypeSwitch = function(typeSelection) {
                var options = {
                    'Generic': 'GenericResource',
                    'Geographic Feature': 'GeographicFeatureResource'
                };
                return options[typeSelection];
            };

            var resourceAbstract = $('#resource-abstract').val();
            var resourceTitle = $('#resource-title').val();
            var resourceKeywords = $('#resource-keywords').val() ? $('#resource-keywords').val() : "";
            var resourceType = resourceTypeSwitch($('#resource-type').val());

             if (!resourceTitle || !resourceKeywords || !resourceAbstract) {
                displayStatus.removeClass('uploading');
                displayStatus.addClass('error');
                displayStatus.html('<em>You must provide all metadata information.</em>');
                return;
            }

            dojo.xhrPost({
                // The URL of the request
                url: "upload-to-hydroshare/",
                // Handle the result as JSON data
                handleAs: "json",
                content: {
                        "geojson_str": JSON.stringify(watershed_geojson),
                        'r_title': resourceTitle,
                        'r_type': resourceType,
                        'r_abstract': resourceAbstract,
                        'r_keywords': resourceKeywords
                },
                headers: {
                        "X-CSRFToken": Cookie("csrftoken")
                },
                // The success handler
                load: function(jsonData) {
                    alert("Success");
                },
                // The error handler
                error: function() {
                    alert("Error");
                }
            });
        });

        //adds public functions to variable app
        app = {computeWatershed: computeWatershed
        };
});
