// Entry point: registers the page modules (loaded on first visit), sets the mode line, draws the background, starts
// the router.
import { start, route, lazy, app, $, isStatic } from './core.js';
import { background } from './background.js';

const PAGES = {
  'home.js': ['home', 'search', 'about'], 'recipes.js': ['recipes', 'recipe'],
  'pantry.js': ['ingredients', 'ingredient', 'equipment', 'tool'], 'cuisines.js': ['cuisines', 'cuisine'],
  'shopping.js': ['shopping'], 'editor.js': ['add', 'edit'],
};
lazy(Object.fromEntries(Object.entries(PAGES).flatMap(([file, names]) => names.map(n => [n, () => import('./' + file)]))));

route('notfound', () => { app().innerHTML = '<h1>Not found</h1><p><a href="#/">Back to the start</a></p>'; });

$('#mode').textContent = isStatic() ? 'static site (adding and editing recipes needs the local app)' : 'local app';
background($('#bg'));
start();
