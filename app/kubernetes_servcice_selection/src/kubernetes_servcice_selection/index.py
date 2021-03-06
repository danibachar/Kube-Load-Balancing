import dash_html_components as html

from .app import app
from .utils import DashRouter, DashNavBar
from .pages import kube_sim, page2, page3
from .components import fa


# Ordered iterable of routes: tuples of (route, layout), where 'route' is a
# string corresponding to path of the route (will be prefixed with Dash's
# 'routes_pathname_prefix' and 'layout' is a Dash Component.
urls = (
    ("", kube_sim.get_layout),
    ("kube-sim", kube_sim.get_layout),
    ("page2", page2.layout),
    ("page3", page3.layout),
)

# Ordered iterable of navbar items: tuples of `(route, display)`, where `route`
# is a string corresponding to path of the route (will be prefixed with
# 'routes_pathname_prefix') and 'display' is a valid value for the `children`
# keyword argument for a Dash component (ie a Dash Component or a string).
nav_items = (
    ("kube-sim", html.Div([fa("fas fa-keyboard"), "Simulation Graphs"])),
    ("page2", html.Div([fa("fas fa-chart-area"), "Page 2"])),
    ("page3", html.Div([fa("fas fa-chart-line"), "Page 3"])),
)
print("from index")
router = DashRouter(app, urls)
navbar = DashNavBar(app, nav_items)
