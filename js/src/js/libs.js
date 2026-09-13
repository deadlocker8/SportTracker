// bootstrap
import '../scss/styles.scss'
import * as bootstrap from 'bootstrap'

window.bootstrap = bootstrap;

// mousetrap
import Mousetrap from 'mousetrap'
window.Mousetrap = Mousetrap;

// autocomplete
import Autocomplete from "bootstrap5-autocomplete/autocomplete.js";
window.Autocomplete = Autocomplete

// sortablejs
import { Sortable, OnSpill } from 'sortablejs/modular/sortable.core.esm.js';
Sortable.mount(OnSpill);
window.Sortable = Sortable