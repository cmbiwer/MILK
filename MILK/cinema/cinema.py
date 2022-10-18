import sys
import time
import threading
import webbrowser
import functools
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import argparse

def load_json(fname: str):
    with open(fname, 'r') as f:
        data = json.load(f)
    return data

def write_json(fname: str,data: dict):
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False, indent=4)

def start_server(ip,port,serve_path):
    server_address = (ip, port)
    Handler = functools.partial(SimpleHTTPRequestHandler, directory=serve_path)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()

def main(cinema_path: str = os.getenv('CINEMA_PATH'),
         data_path: str = Path.cwd(),
         serve_path: str = Path.home(),
         port: int = 8080,
         ip: str = "127.0.0.1",
         databases_index: int = 0,
         databases_name: str = 'MILK',
         run_server: bool = True,
         open_browser: bool = True
         ):
    """Run cinema instance."""

    cinema_path = Path(cinema_path)
    serve_path = Path(serve_path)
    data_path = Path(data_path)
    
    # Configure the http link
    html_path =  cinema_path / "main.html"
    assert html_path.is_file(), "Please specify a valid cinema path which contains main.html"
    url = f"http://{ip}:{port}/{html_path.relative_to(serve_path)}"

    #configure the database.json used by cinema
    csv_path = data_path / "data.csv"
    assert csv_path.is_file(), "Please specify a data_path with a data.csv file in the directory."
    databases_path = str(cinema_path / "databases.json")
    data = load_json(databases_path)
    data[databases_index]['name'] =  f"{databases_name}"
    data[databases_index]['directory'] =  f"{os.sep}{str(data_path.relative_to(serve_path))}"
    write_json(databases_path,data)

    # Launch server, open browser, and wait
    if run_server:
        threading.Thread(target=start_server,args=(ip,port,str(serve_path))).start()
        print(f"Serving: {url}")
        if open_browser:
            webbrowser.open_new(url)
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                sys.exit(0)

if __name__ == "__main__":
    main()
