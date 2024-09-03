document.addEventListener('DOMContentLoaded', function()
{
    initMap();
});

function initMap()
{
    let map = initMapBase();

    if(gpxUrl === null)
    {
        return;
    }

    L.tileLayer(tileRenderUrl + '/{z}/{x}/{y}.png', {
        minZoom: 9,
        maxZoom: 16
    }).addTo(map);


    map.on('plugins_loaded', function(e)
    {
        L.Control.Elevation.include({
            _initHotLine: function(layer)
            {
                let prop = typeof this.options.hotline == 'string' ? this.options.hotline : 'elevation';
                return this.options.hotline ? this.import(this.__LHOTLINE)
                                                  .then(() =>
                                                  {
                                                      layer.eachLayer((trkseg) =>
                                                      {
                                                          if(trkseg.feature.geometry.type != "Point")
                                                          {
                                                              // START MODIFICATION: extract speed data for hotline
                                                              let speedData = [];
                                                              for(let i = 0; i < this._data.length; i++)
                                                              {
                                                                  let entry = this._data[i];
                                                                  speedData.push([entry.latlng.lat, entry.latlng.lng, entry.speed]);
                                                              }
                                                              // END MODIFICATION: extract speed data for hotline

                                                              let line = L.hotline(speedData, {
                                                                  min: isFinite(this.track_info[prop + '_min']) ? this.track_info[prop + '_min'] : 0,
                                                                  max: isFinite(this.track_info[prop + '_max']) ? this.track_info[prop + '_max'] : 1,
                                                                  palette: {
                                                                      0.0: '#008800',
                                                                      0.5: '#ffff00',
                                                                      1.0: '#ff0000'
                                                                  },
                                                                  weight: 5,
                                                                  outlineColor: '#000000',
                                                                  outlineWidth: 1
                                                              }).addTo(this._hotline);
                                                              let alpha = trkseg.options.style && trkseg.options.style.opacity || 1;
                                                              trkseg.on('add remove', ({type}) =>
                                                              {
                                                                  trkseg.setStyle({opacity: (type == 'add' ? 0 : alpha)});
                                                                  line[(type == 'add' ? 'addTo' : 'removeFrom')](trkseg._map);
                                                                  if(line._renderer)
                                                                  {
                                                                      line._renderer._container.parentElement.insertBefore(line._renderer._container, line._renderer._container.parentElement.firstChild);
                                                                  }
                                                              });
                                                          }
                                                      });
                                                  }) : Promise.resolve();
            }
        });

        let controlElevation = L.control.elevation(initElevationChartSettings('speed', 'disabled', false)).addTo(map);
        controlElevation.load(gpxUrl);
    });
}