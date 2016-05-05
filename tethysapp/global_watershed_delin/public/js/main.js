
require(["dojo/dom",
          "dojo/_base/Color",

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
          "esri/symbols/CartographicLineSymbol",
          "esri/IdentityManager"
          ],
    function(dom, Color, Map, Search, Graphic, graphicsUtils, Geoprocessor, FeatureSet, ArcGISTiledMapServiceLayer, GraphicsLayer, SimpleMarkerSymbol, SimpleFillSymbol, CartographicLineSymbol){

        var map, gp;
        var featureSet = new FeatureSet();


        //Initialize Map
        map = new Map("mapDiv", {
          //basemap: "topo",
          center: [-102, 41],
          zoom: 4
        });

        var search = new Search({
            map: map
         }, "search");

        search.startup();

        var basemap = new ArcGISTiledMapServiceLayer("http://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer");
        var overlay = new ArcGISTiledMapServiceLayer("http://hydrology.esri.com/arcgis/rest/services/WorldHydroReferenceOverlay/MapServer");
        var tempPoint = new GraphicsLayer();
        var watersheds = new GraphicsLayer();
        map.addLayers([basemap, overlay, tempPoint, watersheds]);

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
        snapSymbol.setStyle(SimpleMarkerSymbol.STYLE_CIRCLE)
        snapSymbol.setSize("10");
        snapSymbol.setColor(new Color([0, 255, 0, 1]));
        snapSymbol.setOutline(outline);

        var polySymbol = new SimpleFillSymbol();
        polySymbol.setColor(new Color([55,138,73,.25]));
        polySymbol.setOutline(outline);

        //Add Watershed Delineation Geoprocessing Function
        gp = new Geoprocessor("http://hydro.arcgis.com/arcgis/rest/services/Tools/Hydrology/GPServer/Watershed");
        gp.setOutSpatialReference({wkid: 102100});
        map.on("click", addPoint);

        //kml_gp = new Geoprocessor("http://geoserver.byu.edu/arcgis/rest/services/GWD/FeaturesToKML/GPServer/FeaturesToKML");
        //kml_gp.setOutSpatialReference({wkid: 102100});

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

        //adds public functions to variable app
        app = {computeWatershed: computeWatershed
        };
});
