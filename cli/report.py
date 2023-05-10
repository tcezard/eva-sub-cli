import base64
import os.path

from airium import Airium

# Function to generate HTML report from validation results
def generate_html_report_(validation_results):
    file_names = sorted(set([file_name for check_per_file in validation_results.values() for file_name in check_per_file]))
    html = """<html><head>
    <style>ul { list-style: none; } 
    .pass { color: green; } 
    .fail { color: red; } 
    .warn { color: back; }
    </style>
    </head><body>"""
    for file_name in file_names:
        html += f"<h2>Validation results for file {file_name}</h2><ul>"
        for check_type, check_per_file in validation_results.items():
            result = check_per_file.get(file_name, {})
            if check_type == "assembly_check":
                nb_match = result.get("match", 0)
                nb_total = result.get("total", 0)
                match_percentage = f"({nb_match / nb_total * 100:.2f}%)"
                if result.get("nb_mismatch", 0) > 0:
                    icon = "&#10060;"
                    row_class = "fail"
                else:
                    icon = "&#10004;"
                    row_class = "pass"
                html += f"<li class='{row_class}'>{icon} Assembly check: {nb_match}/{nb_total} {match_percentage}</li>"
            elif check_type == "vcf_check":
                critical_count = result.get("critical_count", 0)
                error_count = result.get("error_count", 0)
                warning_count = result.get("warning_count", 0)
                if critical_count > 0:
                    icon = "&#10060;"
                    row_class = "fail"
                elif error_count > 0:
                    icon = "&#10060;"
                    row_class = "warn"
                else:
                    icon = "&#10004;"
                    row_class = "pass"
                html += f"<li class='{row_class}'>{icon} VCF check: {critical_count} critical errors {error_count} non critical error {warning_count} warning </li>"
        html += "</ul>"
    html += "</body></html>"
    return html


current_dir = os.path.dirname(__file__)


def get_logo():
    with open(os.path.join(current_dir, "eva_logo.png"), "rb") as f:
        logo_data = base64.b64encode(f.read()).decode("utf-8")
        return f'<img src="data:image/png;base64,{logo_data}" width="100" height="100">'

def generate_html_report(validation_results):
    file_names = set([file_name for check_per_file in validation_results.values() for file_name in check_per_file])
    html = """<html><head>
    <style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid black; padding: 8px; text-align: left; } 
    th { background-color: lightgrey; } 
    tr.fail { background-color: #FFB6C1; } 
    tr.pass { background-color: #90EE90; } 
    .error-list { display: none; } 
    </style>
    </head><body>"""
    html += get_logo()
    html += f"<h1>Validation </h1>"
    for file_name in file_names:

        html += f"<h2>Validation results for file {file_name}</h2>"
        html += "<ul>"
        for check_type, check_per_file in validation_results.items():
            result = check_per_file.get(file_name, {})
            if check_type == "assembly_check":
                nb_match = result.get("match", 0)
                nb_total = result.get("total", 0)
                match_percentage = f"({nb_match / nb_total * 100:.2f}%)"
                if result.get("nb_mismatch", 0) > 0:
                    icon = "&#10060;"
                    row_class = "fail collapsible"
                else:
                    icon = "&#10004;"
                    row_class = "pass"
                html += f"<li class='{row_class}'>{icon} Assembly check: {nb_match}/{nb_total} {match_percentage}</li>"
                mismatch_list = result.get("mismatch_list")
                if mismatch_list:
                    html += "<div class='error-list'>"
                    html += "<ul>"
                    for error in mismatch_list:
                        html += f"<li><strong>{check_type} error:</strong> {error}</li>"
                    html += "</ul></div>"
                html += "</li>"
            elif check_type == "vcf_check":
                critical_count = result.get("critical_count", 0)
                error_count = result.get("error_count", 0)
                warning_count = result.get("warning_count", 0)
                if critical_count > 0:
                    icon = "&#10060;"
                    row_class = "fail collapsible"
                elif error_count > 0:
                    icon = "&#10060;"
                    row_class = "warn collapsible"
                else:
                    icon = "&#10004;"
                    row_class = "pass"
                html += f"<li class='{row_class}'>{icon} VCF check: {critical_count} critical errors {error_count} non critical error {warning_count} warning </li>"
                critical_list = result.get("critical_list")
                error_list = result.get("error_list")
                if critical_list or error_list:
                    html += "<div class='error-list'>"
                    html += "<ul>"
                    for error in critical_list + error_list:
                        html += f"<li><strong>{check_type} error:</strong> {error}</li>"
                    html += "</ul></div>"
                html += "</li>"
        html += "</ul>"
    html += """<script>
    let collapsibles = document.querySelectorAll('.collapsible'); 
    for (let collapsible of collapsibles) { 
        collapsible.addEventListener('click', function() { 
            this.classList.toggle('active'); 
            let content = this.nextElementSibling; 
            if (content.style.display === 'block') { content.style.display = 'none'; } 
            else { content.style.display = 'block'; } 
        }); 
    }</script></body></html>"""
    return html
