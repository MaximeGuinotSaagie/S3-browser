import os
import dash
from dash import dcc, html, Input as DashInput, Output as DashOutput
from dash.dependencies import Input, Output, State
import boto3
from botocore.exceptions import NoCredentialsError
import base64
import io
from dash_bootstrap_components import themes

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[themes.BOOTSTRAP])

# AWS S3 credentials
s3_access_key = os.environ["AWS_ACCESS_KEY_ID"]
s3_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]

s3 = boto3.client("s3",
                  endpoint_url=os.environ["AWS_S3_ENDPOINT"],
                  region_name=os.environ["AWS_REGION_NAME"],
                  aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])

# Dash layout
app.layout = html.Div([
    html.H1("S3 Browser"),
    dcc.Dropdown(
        id='bucket-dropdown',
        options=[],
        multi=False,
        value='',
        placeholder='Select a bucket'
    ),
    dcc.Loading(
        id="loading",
        type="default",
        children=[
            html.Div(id='file-list'),
            dcc.Upload(
                id='upload-data',
                children=html.Button('Upload File'),
                multiple=False
            ),
        ],
    ),
])

# Callback to update bucket dropdown options
@app.callback(
    Output('bucket-dropdown', 'options'),
    [Input('bucket-dropdown', 'search_value')],
    prevent_initial_call=True
)
def update_bucket_options(search_value):
    try:
        # List all available buckets
        buckets = s3.list_buckets()['Buckets']

        # Create options for the dropdown
        options = [{'label': bucket['Name'], 'value': bucket['Name']} for bucket in buckets]

    except NoCredentialsError:
        return []

    return options

# Callback to update file list based on selected bucket and handle file upload
@app.callback(
    Output('file-list', 'children'),
    [Input('bucket-dropdown', 'value'),
     Input('upload-data', 'contents')],
    prevent_initial_call=True
)
def update_file_list(selected_bucket, contents):
    try:
        if not selected_bucket:
            return []

        # List objects in the specified bucket
        objects = s3.list_objects(Bucket=selected_bucket)['Contents']

        # Create a list of file information as text and boxes around the files
        file_info = []
        for obj in objects:
            file_path = obj['Key']
            # Exclude entries with 0 bytes (folders)
            if obj['Size'] == 0:
                continue

            file_size = format_file_size(obj['Size'])
            # Check if the object is a folder or file
            icon = '📂' if file_path.endswith('/') else '📄'
            file_info.append(html.Div([
                html.Div(icon, style={'marginRight': '5px', 'display': 'inline-block', 'vertical-align': 'middle'}),
                html.Div(f"{file_path}, Size: {file_size}", className='file-box', style={'display': 'inline-block', 'vertical-align': 'middle'}),
                html.A("Download", href=f"/download/{selected_bucket}/{file_path}", className="download-link")
            ], className='file-entry'))

        # Handle file upload
        if contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file_path = "uploaded_file.txt"  # Set a default file name for now, you can extract from contents if needed
            s3.upload_fileobj(io.BytesIO(decoded), selected_bucket, file_path)

    except NoCredentialsError:
        return []

    return file_info

# Callback to handle file download
@app.server.route("/download/<bucket>/<file_path>")
def download_file(bucket, file_path):
    try:
        # Download file
        file_content = s3.get_object(Bucket=bucket, Key=file_path)['Body'].read()
        return dcc.send_data_frame(file_content, filename=file_path)

    except NoCredentialsError:
        return "Credentials not available."

# Function to format file sizes
def format_file_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return "{:.2f} {}".format(size, unit)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
