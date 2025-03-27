// bootstrap
import '../scss/styles.scss'
import * as bootstrap from 'bootstrap'

window.bootstrap = bootstrap;

// leaflet
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// leaflet-ui
import 'leaflet-ui/dist/leaflet-ui.css';
import 'leaflet-ui/dist/leaflet-ui.js';

// leaflet-elevation
import '@raruto/leaflet-elevation/dist/leaflet-elevation.css'
import '@raruto/leaflet-elevation/dist/leaflet-elevation.js'

// leaflet-easybutton
import 'leaflet-easybutton/src/easy-button.css'
import 'leaflet-easybutton/src/easy-button.js'

// mousetrap
import Mousetrap from 'mousetrap'
window.Mousetrap = Mousetrap;

// plotly
import Plotly from 'plotly.js-basic-dist-min'

// autocomplete
import Autocomplete from "bootstrap5-autocomplete/autocomplete.js";
window.Autocomplete = Autocomplete