from .utils.date_utils import adjust_week, add_days

def register_template_filters(app):
    app.template_filter('sum_list')(sum)
    app.template_filter('adjust_week')(adjust_week_filter)
    app.template_filter('add_days')(add_days_filter)

def adjust_week_filter(week_str, delta_weeks):
    return adjust_week(week_str, delta_weeks)

def add_days_filter(date_str, days):
    return add_days(date_str, days)
