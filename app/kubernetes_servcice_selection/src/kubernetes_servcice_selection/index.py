import dash_html_components as html

from .app import app
from .utils import DashRouter, DashNavBar
from .pages import main_dashboard, analysis_pivot_table, deep_research_analysis
from .components import fa


# Ordered iterable of routes: tuples of (route, layout), where 'route' is a
# string corresponding to path of the route (will be prefixed with Dash's
# 'routes_pathname_prefix' and 'layout' is a Dash Component.
urls = (
    ("", main_dashboard.get_layout),
    ("main_dashboard", main_dashboard.get_layout),
    ("analysis_pivot_table", analysis_pivot_table.get_layout),
    ("deep_research_analysis", deep_research_analysis.get_layout),
)

# Ordered iterable of navbar items: tuples of `(route, display)`, where `route`
# is a string corresponding to path of the route (will be prefixed with
# 'routes_pathname_prefix') and 'display' is a valid value for the `children`
# keyword argument for a Dash component (ie a Dash Component or a string).
nav_items = (
    ("main_dashboard", html.Div([fa("fas fa-keyboard"), "Dashboard"])),
    ("analysis_pivot_table", html.Div([fa("fas fa-chart-area"), "Analysis Pivot Table"])),
    ("deep_research_analysis", html.Div([fa("fas fa-chart-line"), "Research Analysis"])),
)

router = DashRouter(app, urls)
navbar = DashNavBar(app, nav_items)
