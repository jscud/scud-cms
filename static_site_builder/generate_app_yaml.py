# This script generates an app.yaml file which configures a static site
# served by Google App Engine.
#
# To generate the configuration file for the static site, run this script
# with the name of the directory containing the website contents as the
# first argument. The website directory must contain an index.html file
# which will be served as the root file at the website (visting the domain
# with a path of /).
#
# Example:
# python generate_app_yaml.py example_site
#
# This will create an app.yaml file in the example_site directory.
#
# To deploy the application to Google App Engine, you can then run the
# gcloud command to upload the app, pointing to the app.yaml file that
# this script created.
#
# Example
# gcloud app deploy example_site/app.yaml --project=<your-project-id>
#
# After deploying, you will be able to see your website at 
# <your-project-id>.appspot.com

import os
import sys


APP_YAML_PREAMBLE = '''runtime: python27
api_version: 1
threadsafe: true

handlers:
- url: /
  static_files: index.html
  upload: index\.html
'''


def write_app_yaml(files, directories):
  new_app_yaml = open('%s/app.yaml' % sys.argv[1], 'w')
  new_app_yaml.write(APP_YAML_PREAMBLE)
  new_app_yaml.close()


def main():
    if len(sys.argv) < 2:
        print('Provide a directory which contains the website files.')
        print('For example, run %s example_site' % sys.argv[0])
        return 1

    found_index_html = False
    files = []
    directories = []
    filenames = os.listdir(sys.argv[1])
    for filename in filenames:
        print('Filename: %s' % filename)
        if filename == 'index.html':
            found_index_html = True
        elif os.path.isdir(filename):
            directories.append(filename)
        elif filename != 'app.yaml':
            files.append(filename)

    if found_index_html:
        write_app_yaml(files, directories)
    else:
        print('The directory %s must contain an index.html file.' % (
            sys.argv[1],))
        return 1


if __name__ == '__main__':
    main()
